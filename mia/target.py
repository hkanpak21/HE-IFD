"""Target / shadow global-model construction by reusing ``src/`` (NOT a reimpl).

LiRA (and GLiRA) need many models trained on overlapping data splits so the
attacker can, for each example, compare confidences from models that DID vs DID
NOT train on it. In the HE-IFD setting the "model" under attack is the released
global student θ⋆, which the protocol produces by

    teacher (per client) → phase0 (build θ₀) → distill (bounded K-step Δ_i)
      → aggregate (θ₀ + Σ_i w_i·Δ_i).

This module composes exactly those ``src/`` primitives — ``src.teacher``,
``src.phase0``, ``src.distill``, ``src.aggregate`` — to produce one global model
on a *designated* training subset of a fixed data pool. It deliberately does NOT
call ``src.protocol.run_cell`` (which re-loads features and computes the headline
/ M3 / M4 metrics every time, work we do not need per shadow model) but it uses
the same functions ``run_cell`` uses, in the same order, so a shadow model is a
faithful instance of the protocol's released model. Nothing about training or
aggregation semantics is changed.

The fixed-pool / random-subset construction is the standard LiRA shadow-model
recipe (Carlini et al. 2022, ``mi_lira_2021``): a global "attack pool" of D
examples is fixed; each shadow model trains on a random half of it; for every
example we record the IN/OUT mask (which shadow models trained on it). The
target model is just one more model on the pool, with a known IN/OUT split, and
the *members* we attack are the examples in its training subset.

Feature loading is delegated to ``src.protocol._load_features`` so each backbone
(``mlp_mnist`` from-scratch, ``vit_b32_cifar100`` head-on-cached-features)
produces the same per-example representation the protocol's models consume — the
single read-only reuse hook (no ``src/`` edit required; ``_load_features`` is an
existing module-level function).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np


# ---------------------------------------------------------------------------
# Defaults — chosen to keep a shadow model cheap (we train ~64 per target).
# ---------------------------------------------------------------------------
# These mirror the protocol's pretrained-head KD defaults (issue 010/012:
# K=100, τ=1, lr=1e-3 for head backbones) and the notebook from-scratch defaults
# for the MLP. The MIA harness exposes them as knobs so a chunked job can dial K
# down if a node is slow, but the defaults match the protocol so leakage is
# measured on a realistic θ⋆.
DEFAULT_KD = {
    "mlp_mnist": {"K": 300, "tau": 4.0, "student_lr": 0.01},
    "vit_b32_cifar100": {"K": 100, "tau": 1.0, "student_lr": 0.001},
}


@dataclass
class TargetConfig:
    """One MIA cell's protocol configuration (mirrors a sweep cell descriptor)."""
    backbone: str
    N: int = 10
    alpha: float = 1.0
    method: str = "raw_union_K20"       # Phase-0 strategy under attack
    K: int = 100
    tau: float = 1.0
    student_lr: float = 0.01
    probe_size: Optional[int] = None
    data_root: str = "data"
    cache_root: str = "cache"
    # Size of the fixed LiRA attack pool (examples whose membership we test).
    # Drawn once from the training set; each model trains on a random half.
    attack_pool_size: int = 5000
    # Number of shadow models per target. Issue 021 asks for ~64.
    n_shadows: int = 64

    @classmethod
    def with_kd_defaults(cls, backbone: str, **kw) -> "TargetConfig":
        """Build a config, filling K / τ / student_lr from the backbone's
        protocol defaults when the caller passes them as ``None``.

        Any explicit (non-None) value in ``kw`` overrides the default; non-KD
        kwargs (N, alpha, method, ...) pass straight through. This is the only
        place the protocol's KD hyperparameters enter the MIA harness so the
        attacked θ⋆ is configured exactly as the headline sweep configures it.
        """
        kd = dict(DEFAULT_KD.get(backbone, {"K": 100, "tau": 1.0, "student_lr": 0.01}))
        fields: Dict = {"backbone": backbone}
        # Start from KD defaults for the three KD keys, override if provided.
        for key in ("K", "tau", "student_lr"):
            if kw.get(key) is not None:
                fields[key] = kw[key]
            elif key in kd:
                fields[key] = kd[key]
        # Pass through every other non-None kwarg (N, alpha, method, ...).
        for key, val in kw.items():
            if key in ("K", "tau", "student_lr"):
                continue
            if val is not None:
                fields[key] = val
        return cls(**fields)


@dataclass
class Features:
    """Cached per-backbone feature tensors + the model factory (loaded once)."""
    Xtr: object
    ytr: object
    Xte: object
    yte: object
    in_dim: Optional[int]
    make_model_fn: Callable
    num_classes: int
    kind: str          # "scratch" | "head"


@dataclass
class GlobalModel:
    """A trained global model θ⋆ plus the protocol intermediates an adversary
    on each surface may legitimately see.

    ``params`` is the aggregated student state_dict (what every party holds after
    decryption). ``theta0`` is the public shared init. ``prototypes`` is the
    Phase-0 release (X, y, info) the P2P channel exposed — used by the fellow and
    prototype surfaces. ``in_idx`` are positions (into the attack pool) this
    model trained on (its members)."""
    params: Dict
    theta0: Dict
    prototypes: Optional[Tuple]
    in_idx: np.ndarray
    sample_sizes: List[int]


def load_features(cfg: TargetConfig) -> Features:
    """Load (and cache) the per-backbone features via ``src.protocol``.

    Reuses the protocol's own ``_load_features`` and ``BACKBONES`` registry so
    the MIA target/shadow models consume the IDENTICAL representation the
    protocol's released model does — no separate feature pipeline.
    """
    from src import protocol as P

    spec = P.BACKBONES[cfg.backbone]
    Xtr, ytr, Xte, yte, in_dim, model_fn_src = P._load_features(
        spec, cfg.data_root, cfg.cache_root, trainable_scope="head_only",
    )
    make_model_fn = model_fn_src() if spec.kind == "scratch" else model_fn_src(
        in_dim, spec.num_classes)
    return Features(
        Xtr=Xtr, ytr=ytr, Xte=Xte, yte=yte, in_dim=in_dim,
        make_model_fn=make_model_fn, num_classes=spec.num_classes, kind=spec.kind,
    )


def make_attack_pool(feats: Features, cfg: TargetConfig, seed: int = 0):
    """Fix the LiRA attack pool: a deterministic random subset of the train set.

    Returns ``(pool_X, pool_y, pool_idx)`` where ``pool_idx`` are positions into
    ``feats.Xtr``. The pool is fixed across all shadow models of a target so the
    IN/OUT bookkeeping is over a common example set (the LiRA recipe). Determined
    by ``seed`` (the *cell* seed, distinct from per-model seeds) so a resumed job
    rebuilds the identical pool.
    """
    rng = np.random.default_rng(seed * 9973 + 1)
    n = int(feats.Xtr.shape[0])
    size = min(cfg.attack_pool_size, n)
    pool_idx = rng.choice(n, size=size, replace=False)
    pool_X = feats.Xtr[pool_idx]
    pool_y = feats.ytr[pool_idx]
    return pool_X, pool_y, pool_idx


def in_out_mask(pool_size: int, model_seed: int) -> np.ndarray:
    """Boolean IN mask over the attack pool for one model (random half IN).

    Each shadow / target model trains on a fresh random half of the fixed pool;
    the per-model seed makes the split deterministic and reproducible (so a
    resumed job regenerates the exact same membership). This is precisely the
    LiRA shadow-model membership randomisation.
    """
    rng = np.random.default_rng(model_seed * 131 + 7)
    keep = rng.random(pool_size) < 0.5
    if not keep.any():        # guard the degenerate all-OUT draw
        keep[rng.integers(pool_size)] = True
    return keep


def train_global_model(
    feats: Features,
    cfg: TargetConfig,
    pool_X,
    pool_y,
    in_mask: np.ndarray,
    model_seed: int,
) -> GlobalModel:
    """Train ONE protocol global model θ⋆ on the IN half of the attack pool.

    Composes ``src`` exactly as ``run_cell`` does, on the designated training
    subset ``pool_X[in_mask]``:

      1. Dirichlet-partition the IN subset across ``cfg.N`` clients.
      2. Train one teacher per client (``src.teacher.train_supervised_model``).
      3. Build θ₀ for ``cfg.method`` (``src.phase0`` builders + ``warmup_init``).
      4. Bounded K-step distillation per client (``src.distill``).
      5. Sample-weighted linear aggregate (``src.aggregate``).

    Returns a ``GlobalModel`` carrying θ⋆, θ₀, the Phase-0 prototype release, and
    the IN indices (members). For the ``labelled`` method the warmup probe is a
    small cell-fixed public sample (``_disjoint_probe``); since the attack pool
    is a small subset of the full train set, probe/pool overlap is negligible
    and the probe is held fixed across a cell's target + shadows. The headline
    MIA method is ``raw_union`` (no labelled probe), so this caveat is
    secondary.
    """
    import torch

    from src import aggregate as agg
    from src import phase0 as p0
    from src.backbones import get_params
    from src.data import dirichlet_partition
    from src.distill import distill_all_clients
    from src.teacher import train_supervised_model
    from src import protocol as P

    spec = P.BACKBONES[cfg.backbone]
    nc = feats.num_classes
    make_model_fn = feats.make_model_fn

    in_idx = np.where(in_mask)[0]
    train_X = pool_X[in_idx]
    train_y = pool_y[in_idx]
    phase0_kind, kwargs = P.parse_method(cfg.method)

    # --- partition the IN subset across clients (Dirichlet, like the protocol) ---
    y_np = train_y.cpu().numpy() if hasattr(train_y, "cpu") else np.asarray(train_y)
    client_idx = dirichlet_partition(y_np, cfg.N, cfg.alpha, model_seed, nc)
    client_X_list = [train_X[ci] for ci in client_idx]
    client_y_list = [train_y[ci] for ci in client_idx]
    sample_sizes = [len(ci) for ci in client_idx]

    # --- teachers ---
    teachers = []
    for i in range(cfg.N):
        if sample_sizes[i] == 0:
            teachers.append(make_model_fn())
            continue
        t = train_supervised_model(
            make_model_fn, client_X_list[i], client_y_list[i],
            epochs=spec.teacher_epochs, lr=spec.teacher_lr, momentum=0.9,
            bs=spec.bs, seed=model_seed * 1000 + i,
            lr_schedule=spec.teacher_lr_schedule)
        teachers.append(t)

    # --- θ₀ via Phase-0 (raw_union default; labelled uses a public probe) ---
    torch.manual_seed(model_seed)
    init_params = get_params(make_model_fn())
    sample_shape = tuple(feats.Xtr.shape[1:])
    is_image = len(sample_shape) > 1
    flat_dim = int(np.prod(sample_shape))

    def _flatten(xs):
        return [x.reshape(x.shape[0], flat_dim) for x in xs]

    def _reshape_probe(pX):
        if pX.shape[0] == 0:
            return torch.empty((0, *sample_shape), dtype=pX.dtype, device=pX.device)
        return pX.reshape(pX.shape[0], *sample_shape)

    prototypes = None
    clip = None
    if phase0_kind in ("dp_avg", "synthetic_dp", "noprobe_dp_avg"):
        clip = p0.compute_feature_norms_percentile(
            train_X.reshape(train_X.shape[0], -1) if is_image else train_X)

    if phase0_kind == "none":
        theta0 = init_params
    elif phase0_kind == "labelled":
        probe_X, probe_y = _disjoint_probe(feats, cfg=cfg)
        theta0 = p0.warmup_init(
            make_model_fn, probe_X, probe_y, init_params,
            epochs=spec.warmup_epochs, lr=spec.teacher_lr, momentum=0.9,
            bs=spec.bs, lr_schedule=spec.teacher_lr_schedule)
    elif phase0_kind in ("raw_union", "dp_avg", "noprobe_raw_union", "noprobe_dp_avg"):
        flat_image = is_image and phase0_kind in ("dp_avg", "noprobe_dp_avg",
                                                  "noprobe_raw_union")
        probe_clients = _flatten(client_X_list) if flat_image else client_X_list
        align_X, align_y, info = p0.build_probe(
            phase0_kind, client_X_list=probe_clients, client_y_list=client_y_list,
            num_classes=nc, K_per_class=kwargs.get("K_per_class"),
            eps=kwargs.get("eps"), clip=clip, seed=model_seed * 100003)
        if flat_image:
            align_X = _reshape_probe(align_X)
        prototypes = (align_X, align_y, info)
        theta0 = p0.warmup_init(
            make_model_fn, align_X, align_y, init_params,
            epochs=spec.warmup_epochs, lr=spec.teacher_lr, momentum=0.9,
            bs=spec.bs, lr_schedule=spec.teacher_lr_schedule)
    else:
        raise ValueError(
            f"MIA target does not support phase0_kind={phase0_kind!r} "
            f"(method={cfg.method!r}); use no_phase0 / labelled / raw_union / "
            f"dp_avg / noprobe_* .")

    # --- distillation + aggregation (sample-weighted, linear) ---
    deltas = distill_all_clients(
        teachers, theta0, make_model_fn, client_X_list,
        K_steps=cfg.K, lr=cfg.student_lr, momentum=0.0, tau=cfg.tau, bs=spec.bs)
    weights = agg.sample_weights(sample_sizes)
    final_params = agg.aggregate(theta0, deltas, weights)

    return GlobalModel(
        params=final_params, theta0=theta0, prototypes=prototypes,
        in_idx=in_idx, sample_sizes=sample_sizes,
    )


def _disjoint_probe(feats: Features, cfg: TargetConfig):
    """A small labelled warmup probe drawn from the train set.

    For the ``labelled`` Phase-0 method. Drawn with a cell-fixed (not per-model)
    RNG; in the MIA harness the attack pool is small relative to the full train
    set so the chance of probe/pool overlap is negligible, and the probe is held
    fixed across the target + shadows of a cell (a public-data probe). Kept
    minimal because ``raw_union`` (no labelled probe) is the headline MIA method.
    """
    import torch  # noqa: F401  (kept local for login-node import hygiene)

    probe_size = cfg.probe_size or 100
    rng = np.random.default_rng(cfg.N * 777 + 13)  # cell-fixed, not per-model
    n = int(feats.Xtr.shape[0])
    idx = rng.choice(n, size=min(probe_size, n), replace=False)
    return feats.Xtr[idx], feats.ytr[idx]


def model_confidences(model_params: Dict, make_model_fn: Callable, X, y, bs: int = 512):
    """Per-example logits, softmax confidence on the true class, and CE loss.

    The raw signal every attack consumes. Returns a dict of NumPy arrays:
      * ``logits``      (n, C)
      * ``conf``        (n,)   softmax probability of the true class
      * ``loss``        (n,)   cross-entropy (−log conf)
      * ``logit_scaled``(n,)   the LiRA logit-scaling transform φ of ``conf``
                               (Carlini §IV-B): log(p/(1−p)), stabilised.

    Evaluated under ``no_grad`` in eval mode, batched, device-aware — mirroring
    ``src.evaluate.accuracy_on``'s evaluation regime.
    """
    import torch
    import torch.nn.functional as F

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = make_model_fn()
    model.load_state_dict(model_params)
    model.eval()
    n = int(X.shape[0])
    logits_all = np.empty((n, 0))
    conf = np.empty(n, dtype=np.float64)
    loss = np.empty(n, dtype=np.float64)
    with torch.no_grad():
        out_chunks = []
        for i in range(0, n, bs):
            xb = X[i:i + bs].to(device) if X.device.type == "cpu" else X[i:i + bs]
            yb = y[i:i + bs].to(device) if y.device.type == "cpu" else y[i:i + bs]
            lo = model(xb)
            p = F.softmax(lo, dim=1)
            true_p = p.gather(1, yb.view(-1, 1)).squeeze(1).clamp_min(1e-12)
            ce = F.cross_entropy(lo, yb, reduction="none")
            out_chunks.append(lo.cpu().numpy())
            conf[i:i + bs] = true_p.cpu().numpy()
            loss[i:i + bs] = ce.cpu().numpy()
    logits_all = np.concatenate(out_chunks, axis=0) if out_chunks else logits_all
    # LiRA logit-scaling φ(p) = log(p / (1 − p)) on the true-class confidence;
    # the membership signal is approximately Gaussian in this transformed space.
    p = np.clip(conf, 1e-12, 1.0 - 1e-12)
    logit_scaled = np.log(p / (1.0 - p))
    return {"logits": logits_all, "conf": conf, "loss": loss,
            "logit_scaled": logit_scaled}
