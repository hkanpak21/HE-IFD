"""End-to-end protocol composition: one (dataset, backbone, N, α, K, method, seed)
cell -> CellResult.

``run_cell`` is the deep-module that wires the whole pipeline:

    data        reserve labelled probe + Dirichlet-partition the pool
      -> teacher    train one teacher per client (+ a centralised oracle reference)
      -> phase0     build the alignment probe and warm θ₀ for the chosen strategy
      -> distill    each client runs the bounded K-step trajectory -> Δ_i
      -> aggregate  server computes θ = θ₀ + Σ_i w_i·Δ_i  (linear, sample-weighted)
      -> evaluate   IID test accuracy of the aggregated student
      (-> report    handled by the caller / sweep)

It faithfully reproduces the notebook's two task runners — ``run_section_A_task``
(from-scratch MNIST/MLP) and ``run_pretrained_protocol_task`` (linear head on
cached pretrained features) — behind one signature parameterised by ``backbone``.
All seeding matches the notebook so a ported cell reproduces the colab logic
(numeric bit-match is NOT a goal — the notebook carries the GPT-2 bug fixed in
issue 002; the gate is the qualitative sanity check in 001).

Method panel (``method`` -> (phase0 strategy)):
  no_phase0             -> none        (distil from fresh random init θ₀)
  warmup_only_labelled  -> warmup_only (warm on labelled probe, NO distillation)
  labelled_probe_warmup -> labelled    (warm θ₀ on labelled probe, then distil)
  raw_union_K{K}        -> raw_union   (K_per_class kwarg)
  dp_avg_eps{E}_K{K}    -> dp_avg      (K_per_class + eps kwargs)
"""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Backbone registry: maps a backbone label to its loader + per-role hyperparams.
# From-scratch backbones train on raw inputs; "head" backbones train a linear
# head on cached pretrained features. Hyperparameters mirror notebook Section 0.2.
# ---------------------------------------------------------------------------
@dataclass
class BackboneSpec:
    label: str
    kind: str                 # "scratch" | "head"
    num_classes: int
    labelled_probe_default: int
    teacher_epochs: int
    teacher_lr: float
    oracle_epochs: int
    warmup_epochs: int
    bs: int
    feature_loader: str       # which backbones.* loader to call ("mnist"/cifar/text)


# Notebook Section 0.2 constants
_TEACHER_MOMENTUM = 0.9
_STUDENT_LR = 0.01
_TAU = 4.0
_WARMUP_EPOCHS = 5

BACKBONES: Dict[str, BackboneSpec] = {
    # From-scratch MNIST MLP (Section A): teacher_epochs=5, lr=0.05, oracle=10, bs=64.
    "mlp_mnist": BackboneSpec(
        label="mlp_mnist", kind="scratch", num_classes=10,
        labelled_probe_default=100, teacher_epochs=5, teacher_lr=0.05,
        oracle_epochs=10, warmup_epochs=_WARMUP_EPOCHS, bs=64, feature_loader="mnist",
    ),
    # From-scratch FashionMNIST LeNet-5 (issue 007): same from-scratch training
    # regime as mlp_mnist (teacher_epochs=5, lr=0.05, oracle=10, warmup=5, bs=64),
    # the notebook Section-0.2 from-scratch convention. Conv net on 1x28x28 raw
    # images — Co-Boosting/FedLPA "LeNet-5 for FMNIST" peer setup.
    "lenet_fmnist": BackboneSpec(
        label="lenet_fmnist", kind="scratch", num_classes=10,
        labelled_probe_default=100, teacher_epochs=5, teacher_lr=0.05,
        oracle_epochs=10, warmup_epochs=_WARMUP_EPOCHS, bs=64, feature_loader="fmnist",
    ),
    # From-scratch CIFAR-10 CNN-5 (issue 007): CIFAR-10 is harder, so give the
    # teacher/oracle a few more epochs (teacher 10 / oracle 20) and the slightly
    # smaller LR conv nets prefer (0.01), batch 64 — Co-Boosting/FedLPA "CNN-5 for
    # CIFAR-10" peer setup. Conv net on RAW 3x32x32 images (NOT pretrained feats).
    "cnn5_cifar10": BackboneSpec(
        label="cnn5_cifar10", kind="scratch", num_classes=10,
        labelled_probe_default=100, teacher_epochs=10, teacher_lr=0.01,
        oracle_epochs=20, warmup_epochs=_WARMUP_EPOCHS, bs=64, feature_loader="cifar10_raw",
    ),
    # Pretrained vision heads (Section B): head training is faster/smaller-LR.
    "resnet18_cifar10": BackboneSpec(
        label="resnet18_cifar10", kind="head", num_classes=10,
        labelled_probe_default=100, teacher_epochs=3, teacher_lr=0.01,
        oracle_epochs=5, warmup_epochs=_WARMUP_EPOCHS, bs=128, feature_loader="cifar10:resnet18",
    ),
    "vit_b32_cifar10": BackboneSpec(
        label="vit_b32_cifar10", kind="head", num_classes=10,
        labelled_probe_default=100, teacher_epochs=3, teacher_lr=0.01,
        oracle_epochs=5, warmup_epochs=_WARMUP_EPOCHS, bs=128, feature_loader="cifar10:vit_b32",
    ),
    # Pretrained text heads (Section C) on AG News (4 classes).
    "distilbert_agnews": BackboneSpec(
        label="distilbert_agnews", kind="head", num_classes=4,
        labelled_probe_default=100, teacher_epochs=3, teacher_lr=0.01,
        oracle_epochs=5, warmup_epochs=_WARMUP_EPOCHS, bs=128, feature_loader="text:distilbert",
    ),
    "gpt2_agnews": BackboneSpec(
        label="gpt2_agnews", kind="head", num_classes=4,
        labelled_probe_default=100, teacher_epochs=3, teacher_lr=0.01,
        oracle_epochs=5, warmup_epochs=_WARMUP_EPOCHS, bs=128, feature_loader="text:gpt2_small",
    ),
}


@dataclass
class CellResult:
    """One protocol cell's outcome (serialised to results/<case>/cell_*.json)."""
    # identity
    backbone: str
    dataset: str
    N: int
    alpha: float
    seed: int
    K: int
    tau: float
    method: str
    phase0_kind: str
    probe_size_actual: int
    sigma: float
    # headline metric + references
    acc: Optional[float] = None
    mean_teacher: Optional[float] = None
    best_teacher: Optional[float] = None
    oracle: Optional[float] = None
    per_teacher_acc: List[float] = field(default_factory=list)
    # standalone θ₀: test accuracy of the aligned init clients receive, BEFORE
    # any local distillation (for no_phase0 this is the fresh random init).
    theta0_acc: Optional[float] = None
    # M3 — per-client teacher-vs-aggregate gap on each client's own data D_i:
    #   acc(final_student, D_i) − acc(teacher_i, D_i). Positive ⇒ federation
    #   helped client i. (See evaluate.per_client_gap.)
    m3_student_acc_on_Di: List[Optional[float]] = field(default_factory=list)
    m3_teacher_acc_on_Di: List[Optional[float]] = field(default_factory=list)
    m3_gap: List[Optional[float]] = field(default_factory=list)
    m3_mean_gap: Optional[float] = None
    m3_clients_helped: Optional[int] = None
    m3_clients_evaluated: Optional[int] = None
    # M4 — per-client OOD-class accuracy: final student's accuracy on TEST
    #   examples from classes client i held ZERO local examples of. All-None /
    #   m4_mean=None when vacuous (every client saw every class, e.g. α=1.0).
    m4_ood_acc: List[Optional[float]] = field(default_factory=list)
    m4_mean: Optional[float] = None
    m4_clients_evaluated: Optional[int] = None
    # partition diagnostics
    per_client_total: List[int] = field(default_factory=list)
    per_client_per_class: List[List[int]] = field(default_factory=list)
    sample_weights: List[float] = field(default_factory=list)
    # timing
    wall_clock_sec: float = 0.0
    phase_teacher_sec: float = 0.0
    phase_phase0_sec: float = 0.0
    phase_distill_sec: float = 0.0
    phase_aggregate_sec: float = 0.0
    phase_eval_sec: float = 0.0
    # provenance
    job_id: Optional[str] = None
    node: Optional[str] = None
    status: str = "success"
    error: Optional[str] = None
    notes: str = ""
    # KD-dynamics diagnostics (issue 013). ``None`` (the default) means this
    # cell was run WITHOUT diagnostics — the default for every sweep — and the
    # field is simply absent from the JSON's information content (still
    # serialised so the schema is stable). When populated, this dict carries
    # teacher entropy / per-step Δ norms / pairwise cosine / per-class θ₀-vs-
    # final accuracy. JSON-serialisable plain types only. See src.diagnostics.
    diagnostics: Optional[Dict] = None

    def to_dict(self) -> Dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Method-name parsing (notebook panel) -> (phase0_kind, kwargs)
# ---------------------------------------------------------------------------
def parse_method(method: str) -> tuple:
    """Map a method name to (phase0_kind, kwargs) following the notebook panel."""
    if method in ("no_phase0",):
        return "none", {}
    if method in ("warmup_only_labelled", "warmup_only"):
        return "warmup_only", {}
    if method in ("labelled_probe_warmup", "labelled"):
        return "labelled", {}
    if method.startswith("raw_union"):
        # raw_union_K20 -> K_per_class=20 ; bare raw_union -> default 20
        k = _extract_int_after(method, "K", default=20)
        return "raw_union", {"K_per_class": k}
    if method.startswith("dp_avg"):
        # dp_avg_eps2_K20 / dp_avg_epsinf_K5
        k = _extract_int_after(method, "K", default=20)
        eps = _extract_eps(method)
        return "dp_avg", {"K_per_class": k, "eps": eps}
    raise ValueError(f"unknown method {method!r}")


def _extract_int_after(s: str, marker: str, default: int) -> int:
    import re

    m = re.search(rf"{marker}(\d+)", s)
    return int(m.group(1)) if m else default


def _extract_eps(s: str) -> float:
    import re

    m = re.search(r"eps([0-9.]+|inf)", s)
    if not m:
        return float("inf")
    tok = m.group(1)
    return float("inf") if tok == "inf" else float(tok)


# ---------------------------------------------------------------------------
# Feature loading per backbone
# ---------------------------------------------------------------------------
def _load_features(spec: BackboneSpec, data_root: str, cache_root: str):
    """Return (X_train, y_train, X_test, y_test, in_dim_or_None, make_model_fn_factory).

    For "scratch" backbones in_dim is None and make_model_fn is parameter-free.
    For "head" backbones in_dim is the feature dim and make_model_fn is built
    from (in_dim, num_classes).
    """
    from . import backbones as bk
    from . import data as dt

    if spec.feature_loader == "mnist":
        Xtr, ytr, Xte, yte = dt.load_mnist_tensors(data_root, cache_root)
        return Xtr, ytr, Xte, yte, None, bk.make_mnist_mlp
    if spec.feature_loader == "fmnist":
        # From-scratch LeNet-5 on raw 1x28x28 FashionMNIST images.
        Xtr, ytr, Xte, yte = dt.load_fmnist_tensors(data_root, cache_root)
        return Xtr, ytr, Xte, yte, None, bk.make_fmnist_lenet5
    if spec.feature_loader == "cifar10_raw":
        # From-scratch CNN-5 on RAW 3x32x32 CIFAR-10 images (pixel space — NOT the
        # pretrained-feature "cifar10:<backbone>" path below).
        Xtr, ytr, Xte, yte = dt.load_cifar10_raw_tensors(data_root, cache_root)
        return Xtr, ytr, Xte, yte, None, bk.make_cifar10_cnn5
    if spec.feature_loader.startswith("cifar10:"):
        name = spec.feature_loader.split(":", 1)[1]
        Xtr, ytr, Xte, yte, in_dim = bk.extract_cifar10_features(name, data_root, cache_root)
        return Xtr, ytr, Xte, yte, in_dim, bk.make_head
    if spec.feature_loader.startswith("text:"):
        name = spec.feature_loader.split(":", 1)[1]
        Xtr, ytr, Xte, yte, in_dim = bk.extract_text_features(name, "ag_news", data_root, cache_root)
        return Xtr, ytr, Xte, yte, in_dim, bk.make_head
    raise ValueError(spec.feature_loader)


# ---------------------------------------------------------------------------
# The deep module: run_cell
# ---------------------------------------------------------------------------
def run_cell(
    *,
    backbone: str,
    N: int,
    alpha: float,
    seed: int,
    method: str,
    K: int = 300,
    tau: float = _TAU,
    student_lr: float = _STUDENT_LR,
    probe_size: Optional[int] = None,
    data_root: str = "data",
    cache_root: str = "cache",
    job_id: Optional[str] = None,
    node: Optional[str] = None,
    diagnose: bool = False,
) -> CellResult:
    """Run one protocol cell end-to-end and return a CellResult.

    Faithful composition of the notebook task runners. ``K`` is the bounded
    trajectory length (swept hyperparameter; notebook default 300). Aggregation
    is always sample-weighted. ``warmup_only`` short-circuits before distillation
    (its "result" is the warmed model, not a protocol output) — this is the
    probe-only baseline used to isolate what the K-step trajectory adds.

    ``diagnose`` (default ``False``) — when ``False`` this function is
    byte-identical to its pre-issue-013 behaviour (no new code paths execute).
    When ``True`` the distill loop additionally retains per-step deltas, and
    after aggregation the issue-013 diagnostics (teacher entropy / Δ-norm
    profile / pairwise cosine / per-class θ₀-vs-final acc) are computed once
    and stuffed into ``res.diagnostics``. The flag is opt-in and reserved for
    diagnostic cells; sweeps that omit it see zero behaviour change.
    """
    import numpy as np
    import torch

    from . import aggregate as agg
    from . import phase0 as p0
    from .backbones import get_params
    from .data import partition_pool, per_client_per_class_counts, reserve_probe_and_pool
    from .distill import distill_all_clients
    from .evaluate import accuracy_on, ood_accuracy, per_client_gap
    from .teacher import train_supervised_model

    spec = BACKBONES[backbone]
    phase0_kind, kwargs = parse_method(method)
    probe_size = spec.labelled_probe_default if probe_size is None else probe_size
    momentum = _TEACHER_MOMENTUM
    nc = spec.num_classes
    # Human-readable dataset label from the feature_loader. Keyed on the prefix
    # so both the from-scratch loaders ("mnist"/"fmnist"/"cifar10_raw") and the
    # pretrained ones ("cifar10:<bb>"/"text:<bb>") resolve correctly.
    _loader_prefix = spec.feature_loader.split(":")[0]
    dataset = {
        "mnist": "MNIST",
        "fmnist": "FashionMNIST",
        "cifar10_raw": "CIFAR10",
        "cifar10": "CIFAR10",
    }.get(_loader_prefix, "CIFAR10" if "cifar" in spec.feature_loader else "AGNews")

    res = CellResult(
        backbone=backbone, dataset=dataset, N=N, alpha=alpha, seed=seed,
        K=K, tau=tau, method=method, phase0_kind=phase0_kind,
        probe_size_actual=0, sigma=0.0, job_id=job_id, node=node,
        notes=("HE-IFD plaintext simulation: sample-weighted linear aggregate "
               "θ₀+Σ w_i·Δ_i of bounded K-step cumulative displacements; "
               "server op is PT×CT + CT+CT only (FHE-compatible)."),
    )
    t_start = time.time()
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"

        # --- data: load features, reserve labelled probe, partition the pool ---
        Xtr, ytr, Xte, yte, in_dim, model_fn_src = _load_features(spec, data_root, cache_root)
        Xte_dev = Xte.to(device)
        yte_dev = yte.to(device)

        make_model_fn = model_fn_src() if spec.kind == "scratch" else model_fn_src(in_dim, nc)

        # Per-sample shape (everything after dim 0). For the MLP / pretrained
        # heads this is (D,) — already flat. For the conv backbones it is
        # (C, H, W). The dp_avg Phase-0 mechanism is defined in FLAT feature
        # space (it L2-clips, averages and Gaussian-noises per-feature), so for
        # image-shaped data we flatten into it and reshape its probe back to the
        # image shape before warmup. raw_union/none/labelled/warmup_only need no
        # such bridge — they index/concat along dim 0 only and so flow with the
        # native shape straight into the conv net. (See data.py shape contract.)
        sample_shape = tuple(Xtr.shape[1:])
        is_image = len(sample_shape) > 1

        def _flatten_clients(xs):
            """Flatten a list of per-client tensors to (n_i, prod(sample_shape))."""
            return [x.reshape(x.shape[0], -1) for x in xs]

        def _reshape_probe_to_image(probe_X_flat):
            """Reshape a flat dp_avg probe (P, prod(sample_shape)) back to images
            (P, C, H, W) so the conv warmup consumes the same shape as training."""
            return probe_X_flat.reshape(probe_X_flat.shape[0], *sample_shape)

        probe_X, probe_y, pool_X, pool_y = reserve_probe_and_pool(Xtr, ytr, probe_size, seed)
        client_X_list, client_y_list, sample_sizes = partition_pool(
            pool_X, pool_y, N, alpha, seed, nc)
        res.per_client_total = [int(s) for s in sample_sizes]
        res.per_client_per_class = per_client_per_class_counts(client_y_list, nc)

        def eval_model(m):
            return accuracy_on(m, Xte_dev, yte_dev)

        def theta0_test_acc(params):
            """Standalone θ₀ accuracy: build a model from the aligned init params
            and evaluate it on the test set, BEFORE any local distillation."""
            m = make_model_fn()
            m.load_state_dict(params)
            return float(eval_model(m))

        def populate_incentive_ood(final_student):
            """Populate M3 (per-client gap on D_i) and M4 (OOD-class acc) on the
            CellResult. Reuses the already-trained ``teachers`` and the
            per-client partition tensors — trains nothing, decodes nothing."""
            m3 = per_client_gap(final_student, teachers, client_X_list, client_y_list)
            res.m3_student_acc_on_Di = m3["student_acc"]
            res.m3_teacher_acc_on_Di = m3["teacher_acc"]
            res.m3_gap = m3["gap"]
            res.m3_mean_gap = m3["mean_gap"]
            res.m3_clients_helped = m3["n_clients_helped"]
            res.m3_clients_evaluated = m3["n_clients_evaluated"]
            m4 = ood_accuracy(final_student, Xte_dev, yte_dev, res.per_client_per_class)
            res.m4_ood_acc = m4["per_client"]
            res.m4_mean = m4["mean"]
            res.m4_clients_evaluated = m4["n_clients_evaluated"]

        # --- teachers (one per client) + oracle reference ---
        t0 = time.time()
        teachers, t_accs = [], []
        for i in range(N):
            if sample_sizes[i] == 0:
                teachers.append(make_model_fn())
                t_accs.append(1.0 / nc)
                continue
            t = train_supervised_model(
                make_model_fn, client_X_list[i], client_y_list[i],
                epochs=spec.teacher_epochs, lr=spec.teacher_lr,
                momentum=momentum, bs=spec.bs, seed=seed * 1000 + i)
            teachers.append(t)
            t_accs.append(eval_model(t))
        res.per_teacher_acc = [float(a) for a in t_accs]
        res.mean_teacher = float(np.mean(t_accs))
        res.best_teacher = float(np.max(t_accs))

        oracle_m = train_supervised_model(
            make_model_fn, pool_X, pool_y, epochs=spec.oracle_epochs,
            lr=spec.teacher_lr, momentum=momentum, bs=spec.bs, seed=seed * 7919)
        res.oracle = float(eval_model(oracle_m))
        res.phase_teacher_sec = time.time() - t0

        # --- Phase 0: build θ₀ for the chosen strategy ---
        t0 = time.time()
        torch.manual_seed(seed)
        init_params = get_params(make_model_fn())  # fresh random init

        # The augmented-probe tensors the warmup actually consumes. Tracked
        # purely so issue-013 diagnostics (when ``diagnose=True``) can compute
        # teacher entropy on the same tensor that warmed θ₀. ``None`` for
        # ``no_phase0`` and ``warmup_only`` (the latter returns before
        # distillation anyway). Not used unless ``diagnose=True``.
        align_X = None

        clip = None
        if phase0_kind == "dp_avg":
            # Percentile feature-norm clip in flat space (image data -> flatten).
            clip = p0.compute_feature_norms_percentile(
                pool_X.reshape(pool_X.shape[0], -1) if is_image else pool_X)

        if phase0_kind == "none":
            theta0 = init_params  # no alignment: θ₀ is the fresh random init
            res.probe_size_actual = 0
            res.sigma = 0.0
            res.theta0_acc = theta0_test_acc(theta0)

        elif phase0_kind == "warmup_only":
            # Probe-only baseline: warm on the labelled probe, NO distillation.
            theta0 = p0.warmup_init(
                make_model_fn, probe_X, probe_y, init_params,
                epochs=spec.warmup_epochs, lr=spec.teacher_lr,
                momentum=momentum, bs=spec.bs)
            res.phase_phase0_sec = time.time() - t0
            warmed = make_model_fn()
            warmed.load_state_dict(theta0)
            t0e = time.time()
            res.acc = float(eval_model(warmed))
            # θ₀ IS the output here (no distillation), so standalone-θ₀ acc == acc;
            # M3/M4 are reported against the warmed model so the probe-only
            # baseline row is complete rather than empty.
            res.theta0_acc = res.acc
            populate_incentive_ood(warmed)
            res.phase_eval_sec = time.time() - t0e
            res.probe_size_actual = int(probe_size)
            res.sigma = 0.0
            res.sample_weights = agg.sample_weights(sample_sizes)
            res.wall_clock_sec = time.time() - t_start
            res.status = "success"
            return res

        elif phase0_kind == "labelled":
            theta0 = p0.warmup_init(
                make_model_fn, probe_X, probe_y, init_params,
                epochs=spec.warmup_epochs, lr=spec.teacher_lr,
                momentum=momentum, bs=spec.bs)
            align_X = probe_X       # for issue-013 entropy (no-op unless diagnose=True)
            res.probe_size_actual = int(probe_size)
            res.sigma = 0.0
            res.theta0_acc = theta0_test_acc(theta0)

        elif phase0_kind in ("raw_union", "dp_avg"):
            probe_seed = seed * 100003
            # raw_union selects raw samples (preserves the native image shape).
            # dp_avg works in flat feature space, so for image data we flatten the
            # per-client tensors going in and reshape its (P, C*H*W) probe back to
            # (P, C, H, W) coming out — keeping phase0.py and the conv warmup
            # input shape-consistent without touching aggregation/distill.
            dp_image = is_image and phase0_kind == "dp_avg"
            probe_clients = _flatten_clients(client_X_list) if dp_image else client_X_list
            align_X, align_y, info = p0.build_probe(
                phase0_kind, client_X_list=probe_clients, client_y_list=client_y_list,
                num_classes=nc, K_per_class=kwargs.get("K_per_class"),
                eps=kwargs.get("eps"), clip=clip, seed=probe_seed)
            if dp_image:
                align_X = _reshape_probe_to_image(align_X)
            theta0 = p0.warmup_init(
                make_model_fn, align_X, align_y, init_params,
                epochs=spec.warmup_epochs, lr=spec.teacher_lr,
                momentum=momentum, bs=spec.bs)
            res.probe_size_actual = int(info["probe_size"])
            res.sigma = float(info["sigma"])
            res.theta0_acc = theta0_test_acc(theta0)
        else:
            raise ValueError(phase0_kind)
        res.phase_phase0_sec = time.time() - t0

        # --- distillation: each client runs the bounded K-step trajectory -> Δ_i ---
        # ``diagnose=False`` (the sweep default) takes the byte-identical path
        # — distill_all_clients returns only the cumulative Δ list. With
        # ``diagnose=True`` the per-step trajectories are additionally collected
        # so src.diagnostics can compute the per-step ‖Δ⁽ᵏ⁾‖₂ profile (issue 013).
        t0 = time.time()
        if diagnose:
            deltas, step_deltas_per_client = distill_all_clients(
                teachers, theta0, make_model_fn, client_X_list,
                K_steps=K, lr=student_lr, momentum=0.0, tau=tau, bs=spec.bs,
                diagnose=True,
            )
        else:
            deltas = distill_all_clients(
                teachers, theta0, make_model_fn, client_X_list,
                K_steps=K, lr=student_lr, momentum=0.0, tau=tau, bs=spec.bs)
            step_deltas_per_client = None
        res.phase_distill_sec = time.time() - t0

        # --- aggregate: θ = θ₀ + Σ_i w_i·Δ_i (sample-weighted, linear-only) ---
        t0 = time.time()
        weights = agg.sample_weights(sample_sizes)
        res.sample_weights = weights
        final_params = agg.aggregate(theta0, deltas, weights)
        res.phase_aggregate_sec = time.time() - t0

        # --- evaluate: IID acc + M3 (per-client gap) + M4 (OOD-class acc) ---
        # θ₀_acc was recorded above right after warmup (before distill); M3/M4
        # reuse the trained teachers + per-client tensors, so no retraining here.
        t0 = time.time()
        model = make_model_fn()
        model.load_state_dict(final_params)
        res.acc = float(eval_model(model))
        populate_incentive_ood(model)
        res.phase_eval_sec = time.time() - t0

        # --- (optional) issue-013 KD-dynamics diagnostics ---
        # Strictly opt-in. When ``diagnose=False`` this block does not run and
        # ``res.diagnostics`` stays ``None`` (the default) — so the produced
        # CellResult is unchanged from the pre-issue-013 sweep behaviour.
        if diagnose:
            from .diagnostics import build_diagnostics

            res.diagnostics = build_diagnostics(
                teachers=teachers,
                align_X=align_X,
                align_y=None,
                client_X_list=client_X_list,
                deltas=deltas,
                step_deltas_per_client=step_deltas_per_client,
                theta0_params=theta0,
                final_params=final_params,
                make_model_fn=make_model_fn,
                X_test=Xte_dev,
                y_test=yte_dev,
                num_classes=nc,
                bs=spec.bs,
            )

        res.status = "success"
    except Exception as exc:  # noqa: BLE001 — record failure, keep sweep alive
        import traceback

        res.status = "FAIL"
        res.error = "".join(traceback.format_exception_only(type(exc), exc)).strip()
        res.notes += f" | traceback: {traceback.format_exc()[-800:]}"
    res.wall_clock_sec = time.time() - t_start
    return res
