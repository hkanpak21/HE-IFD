"""Aggregation-coherence ablation (issue 006): *why* the design works.

This module produces the empirical evidence for HE-IFD's central design choice
and preempts the "isn't this just FedAvg-averaging?" reviewer reflex (PRD user
story 17, the "basin coherence" argument).

The thesis (CLAUDE.md "The current method"; ``aggregate.py`` telescoping note):
the single sample-weighted linear combine ``θ₀ + Σ_i w_i·Δ_i`` lands inside ONE
loss basin **only because** every client departs from the SAME Phase-0-aligned
init ``θ₀`` and moves a BOUNDED distance (K KL-distillation steps). It is *not*
"encrypt and average final weights" — naive averaging of independently-converged
/ unbounded / different-init students drifts across basins and the linear combine
collapses. This ablation measures exactly that, on a shared cell, holding ``θ₀``,
the partition, and the per-client teachers FIXED so the only thing that varies is
**how far, and from where, each client's student travelled.**

Regimes (all on the SAME θ₀ / partition / teachers within a cell):

  1. ``heifd``                    — HE-IFD (ours). Bounded ``K``-step KL distillation
                                    from the shared aligned ``θ₀`` against each
                                    client's teacher; sample-weighted linear
                                    aggregate ``θ₀ + Σ_i w_i·Δ_i``. This is exactly
                                    what ``protocol.run_cell`` does for ``raw_union``
                                    — here it is reassembled from the same library
                                    primitives (``distill.distill_all_clients`` +
                                    ``aggregate.aggregate``) so it shares one θ₀
                                    with the naive regimes (a fair control).
  2. ``converged_shared_init``    — each client SUPERVISED-trains a student to
                                    convergence (``--converge-epochs``, e.g. 40) on
                                    its own ``D_i`` STARTING FROM the shared ``θ₀``;
                                    average the finals (sample-weighted). Large
                                    displacement from the SAME init.
  3. ``converged_diff_init``      — each client supervised-trains to convergence on
                                    ``D_i`` from a DIFFERENT random init (seed-keyed
                                    per client); average the finals (sample-weighted).
                                    The classic permutation / different-basin failure.
  4. ``unbounded_distill_shared`` — (optional, default on) the SAME KL distillation
                                    as regime 1 from the SAME ``θ₀``, but UNBOUNDED
                                    (``--unbounded-K`` ≫ ``K``, e.g. 3000 steps);
                                    average the finals. Isolates *boundedness* from
                                    the supervised/distil axis: same init, same
                                    objective, only the displacement magnitude
                                    differs (the "full-FT / large-displacement"
                                    variant of PRD story 17).

The aggregate in every regime is computed through ``aggregate.aggregate`` over a
per-client cumulative displacement ``Δ_i = θ_i_final − θ_ref``:
  * regimes 1/2/4 use ``θ_ref = θ₀`` (the shared aligned init) — so the combine is
    literally ``θ₀ + Σ_i w_i·(θ_i − θ₀)``;
  * regime 3 has no shared init, so ``θ_ref = 0`` (a zero param-dict) and the
    combine reduces to the plain sample-weighted average of finals
    ``Σ_i w_i·θ_i`` — the genuine "average the final weights" baseline.
Both are linear (PT×CT + CT+CT only), so ``aggregate`` is reused unchanged.

REUSE map (nothing in src/ is modified):
  data.reserve_probe_and_pool / partition_pool / per_client_per_class_counts
  phase0.build_probe (raw_union) + warmup_init        -> the shared aligned θ₀
  teacher.train_supervised_model                       -> teachers + converged students
  distill.local_distill_trajectory / distill_all_clients -> bounded + unbounded trajectories
  aggregate.sample_weights / aggregate                 -> the one server op (all regimes)
  evaluate.accuracy_on                                 -> IID test accuracy
  backbones.get_params + the protocol BACKBONES/_load_features registry

Hard boundaries honoured: this is a NEW module with its own entrypoint
(``python -m src.ablation``); it edits none of protocol/aggregate/distill and
adds no helper to them. Compute runs only under sbatch on VALAR.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

# Reused, side-effect-free imports (no torch pulled in at module import time — the
# protocol registry is pure dataclasses; every heavy import is deferred into
# run_cell_ablation, mirroring the rest of src/). Keeps login-node ast/CLI checks
# clean (CLAUDE.md GOLDEN RULE).
from .protocol import BACKBONES, BackboneSpec, _TAU, _STUDENT_LR, _TEACHER_MOMENTUM, _load_features


# Regime identifiers (stable strings used in JSON / CSV / README).
REGIME_HEIFD = "heifd"
REGIME_CONVERGED_SHARED = "converged_shared_init"
REGIME_CONVERGED_DIFF = "converged_diff_init"
REGIME_UNBOUNDED = "unbounded_distill_shared"

ALL_REGIMES = [
    REGIME_HEIFD,
    REGIME_CONVERGED_SHARED,
    REGIME_CONVERGED_DIFF,
    REGIME_UNBOUNDED,
]

REGIME_BLURB = {
    REGIME_HEIFD: "HE-IFD (ours): bounded K-step KL distillation from shared aligned θ₀; θ₀+Σ w_i·Δ_i.",
    REGIME_CONVERGED_SHARED: "naive avg of students supervised-trained to convergence on D_i from the SAME θ₀.",
    REGIME_CONVERGED_DIFF: "naive avg of students supervised-trained to convergence on D_i from DIFFERENT random inits.",
    REGIME_UNBOUNDED: "naive avg of UNBOUNDED (long-K) distillation students from the SAME θ₀ (large displacement).",
}


@dataclass
class AblationCellResult:
    """One (backbone, N, α, seed) ablation cell: a row per regime + shared refs.

    Serialised to ``results/<case>/cell_*.json``. The headline field is
    ``regime_acc`` — the IID test accuracy of each regime's aggregated model on
    the SAME θ₀ / partition / teachers, so the gap between ``heifd`` and the naive
    regimes is the coherence signal. ``displacement_l2`` reports the mean
    per-client ‖Δ_i‖ relative to the regime's reference, the quantitative "how far
    did each client travel" knob the basin argument turns on.
    """
    # identity (shared across regimes)
    backbone: str
    dataset: str
    N: int
    alpha: float
    seed: int
    K: int
    unbounded_K: int
    converge_epochs: int
    tau: float
    student_lr: float
    K_per_class: int
    probe_size_actual: int
    # shared references (regime-independent)
    theta0_acc: Optional[float] = None      # standalone acc of the shared aligned θ₀
    mean_teacher: Optional[float] = None
    best_teacher: Optional[float] = None
    per_teacher_acc: List[float] = field(default_factory=list)
    # per-regime headline metric: regime -> IID test accuracy of its aggregate
    regime_acc: Dict[str, Optional[float]] = field(default_factory=dict)
    # per-regime mean per-client displacement ‖Δ_i‖_2 (relative to its θ_ref)
    regime_mean_displacement: Dict[str, Optional[float]] = field(default_factory=dict)
    # partition diagnostics
    per_client_total: List[int] = field(default_factory=list)
    per_client_per_class: List[List[int]] = field(default_factory=list)
    sample_weights: List[float] = field(default_factory=list)
    # timing / provenance
    wall_clock_sec: float = 0.0
    job_id: Optional[str] = None
    node: Optional[str] = None
    status: str = "success"
    error: Optional[str] = None
    notes: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Small helpers (kept INSIDE this module per the issue's "add a helper here" rule)
# ---------------------------------------------------------------------------
def _zeros_like_params(params: Dict) -> Dict:
    """A zero param-dict matching ``params`` (the θ_ref=0 baseline for regime 3).

    Used so ``aggregate(theta0=0, deltas=finals, weights)`` reduces to the plain
    sample-weighted average of final weights Σ_i w_i·θ_i — the genuine
    "average the final models" baseline for the different-init regime, computed
    through the SAME linear ``aggregate`` op as every other regime.
    """
    import torch

    return {k: torch.zeros_like(v) for k, v in params.items()}


def _params_diff(p1: Dict, p0: Dict) -> Dict:
    return {k: p1[k] - p0[k] for k in p1}


def _mean_displacement_l2(deltas: List[Dict], weights) -> float:
    """Sample-weighted mean of per-client total displacement ‖Δ_i‖_2 (flattened).

    A scalar summary of "how far each client's student travelled from its
    reference" — the magnitude the basin-coherence argument predicts is small for
    HE-IFD (bounded K) and large for the converged / unbounded regimes.
    """
    import torch

    total = 0.0
    for w, d in zip(weights, deltas):
        sq = sum(float(torch.sum(v.double() * v.double()).item()) for v in d.values())
        total += float(w) * (sq ** 0.5)
    return total


# ---------------------------------------------------------------------------
# The ablation cell: build the shared setup ONCE, then run every regime on it
# ---------------------------------------------------------------------------
def run_cell_ablation(
    *,
    backbone: str,
    N: int,
    alpha: float,
    seed: int,
    K: int = 300,
    unbounded_K: int = 3000,
    converge_epochs: int = 40,
    K_per_class: int = 20,
    tau: float = _TAU,
    student_lr: float = _STUDENT_LR,
    probe_size: Optional[int] = None,
    include_unbounded: bool = True,
    data_root: str = "data",
    cache_root: str = "cache",
    job_id: Optional[str] = None,
    node: Optional[str] = None,
) -> AblationCellResult:
    """Run the coherence ablation for one (backbone, N, α, seed) cell.

    Builds ONE shared setup (data → partition → teachers → raw_union Phase-0
    ``θ₀``) reusing the same library primitives ``protocol.run_cell`` uses, then
    derives every regime's aggregate from that single shared state. Holding θ₀,
    the partition and the teachers fixed is what makes the regime-to-regime
    accuracy gap a clean measurement of displacement/basin effects rather than of
    re-randomised teachers or a different aligned init.
    """
    import numpy as np
    import torch

    from . import aggregate as agg
    from . import phase0 as p0
    from .backbones import get_params
    from .data import (
        partition_pool,
        per_client_per_class_counts,
        reserve_probe_and_pool,
    )
    from .distill import distill_all_clients
    from .evaluate import accuracy_on
    from .teacher import train_supervised_model

    spec: BackboneSpec = BACKBONES[backbone]
    probe_size = spec.labelled_probe_default if probe_size is None else probe_size
    momentum = _TEACHER_MOMENTUM
    nc = spec.num_classes
    _loader_prefix = spec.feature_loader.split(":")[0]
    dataset = {
        "mnist": "MNIST",
        "fmnist": "FashionMNIST",
        "cifar10_raw": "CIFAR10",
        "cifar10": "CIFAR10",
    }.get(_loader_prefix, "CIFAR10" if "cifar" in spec.feature_loader else "AGNews")

    res = AblationCellResult(
        backbone=backbone, dataset=dataset, N=N, alpha=alpha, seed=seed,
        K=K, unbounded_K=unbounded_K, converge_epochs=converge_epochs,
        tau=tau, student_lr=student_lr, K_per_class=K_per_class,
        probe_size_actual=0, job_id=job_id, node=node,
        notes=("Aggregation-coherence ablation (issue 006): regimes share one "
               "raw_union θ₀, partition and teacher set; only the per-client "
               "trajectory (bounded distil vs converged-supervised vs unbounded "
               "distil vs different-init) varies. Server op is the same linear "
               "θ_ref+Σ w_i·Δ_i (PT×CT+CT+CT) in every regime."),
    )
    t_start = time.time()
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"

        # --- shared data: reserve probe, Dirichlet-partition the pool ---
        Xtr, ytr, Xte, yte, in_dim, model_fn_src = _load_features(spec, data_root, cache_root)
        Xte_dev = Xte.to(device)
        yte_dev = yte.to(device)
        make_model_fn = model_fn_src() if spec.kind == "scratch" else model_fn_src(in_dim, nc)

        probe_X, probe_y, pool_X, pool_y = reserve_probe_and_pool(Xtr, ytr, probe_size, seed)
        client_X_list, client_y_list, sample_sizes = partition_pool(
            pool_X, pool_y, N, alpha, seed, nc)
        res.per_client_total = [int(s) for s in sample_sizes]
        res.per_client_per_class = per_client_per_class_counts(client_y_list, nc)
        weights = agg.sample_weights(sample_sizes)
        res.sample_weights = weights

        def eval_params(params: Dict) -> float:
            m = make_model_fn()
            m.load_state_dict(params)
            return float(accuracy_on(m, Xte_dev, yte_dev))

        # --- shared teachers (one per client), seeded exactly as run_cell ---
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
            t_accs.append(float(accuracy_on(t, Xte_dev, yte_dev)))
        res.per_teacher_acc = [float(a) for a in t_accs]
        res.mean_teacher = float(np.mean(t_accs))
        res.best_teacher = float(np.max(t_accs))

        # --- shared aligned θ₀ via raw_union Phase-0 (same path as run_cell) ---
        torch.manual_seed(seed)
        init_params = get_params(make_model_fn())  # fresh random init (pre-warmup)
        probe_seed = seed * 100003
        align_X, align_y, info = p0.build_probe(
            "raw_union", client_X_list=client_X_list, client_y_list=client_y_list,
            num_classes=nc, K_per_class=K_per_class, seed=probe_seed)
        theta0 = p0.warmup_init(
            make_model_fn, align_X, align_y, init_params,
            epochs=spec.warmup_epochs, lr=spec.teacher_lr,
            momentum=momentum, bs=spec.bs)
        res.probe_size_actual = int(info["probe_size"])
        res.theta0_acc = eval_params(theta0)

        zero_ref = _zeros_like_params(theta0)

        # =================================================================
        # Regime 1 — HE-IFD (ours): bounded K-step distillation from θ₀.
        # Reuses distill_all_clients + aggregate, i.e. the exact run_cell path.
        # =================================================================
        deltas_heifd = distill_all_clients(
            teachers, theta0, make_model_fn, client_X_list,
            K_steps=K, lr=student_lr, momentum=0.0, tau=tau, bs=spec.bs)
        theta_heifd = agg.aggregate(theta0, deltas_heifd, weights)
        res.regime_acc[REGIME_HEIFD] = eval_params(theta_heifd)
        res.regime_mean_displacement[REGIME_HEIFD] = _mean_displacement_l2(deltas_heifd, weights)

        # =================================================================
        # Regime 2 — converged students from the SHARED θ₀ (supervised, many
        # epochs). Δ_i = θ_i_converged − θ₀; aggregate θ₀ + Σ w_i·Δ_i.
        # Each client's supervised trainer is seeded distinctly (matches the
        # teacher-seed convention so finals are reproducible) but ALL start from
        # the identical θ₀ via init_params.
        # =================================================================
        conv_shared_deltas: List[Dict] = []
        for i in range(N):
            if sample_sizes[i] == 0:
                conv_shared_deltas.append(_zeros_like_params(theta0))
                continue
            m = train_supervised_model(
                make_model_fn, client_X_list[i], client_y_list[i],
                epochs=converge_epochs, lr=spec.teacher_lr, momentum=momentum,
                bs=spec.bs, seed=seed * 1000 + i, init_params=theta0)
            conv_shared_deltas.append(_params_diff(get_params(m), theta0))
        theta_conv_shared = agg.aggregate(theta0, conv_shared_deltas, weights)
        res.regime_acc[REGIME_CONVERGED_SHARED] = eval_params(theta_conv_shared)
        res.regime_mean_displacement[REGIME_CONVERGED_SHARED] = _mean_displacement_l2(
            conv_shared_deltas, weights)

        # =================================================================
        # Regime 3 — converged students from DIFFERENT random inits, averaged.
        # No shared init → θ_ref = 0, so aggregate(0, finals, w) = Σ w_i·θ_i, the
        # genuine "average the final weights of independently-initialised models"
        # baseline (the permutation / different-basin failure). Each client's
        # init is reseeded distinctly via train_supervised_model's
        # torch.manual_seed(seed) BEFORE the model is built (init_params=None).
        # =================================================================
        conv_diff_finals: List[Dict] = []
        for i in range(N):
            if sample_sizes[i] == 0:
                # A zero-sample client with no shared init: contribute a fresh
                # random init (seed-keyed) so the average is well-defined and the
                # client still "votes" with a divergent model.
                torch.manual_seed(seed * 1000 + i)
                conv_diff_finals.append(get_params(make_model_fn()))
                continue
            m = train_supervised_model(
                make_model_fn, client_X_list[i], client_y_list[i],
                epochs=converge_epochs, lr=spec.teacher_lr, momentum=momentum,
                bs=spec.bs, seed=seed * 1000 + i, init_params=None)
            conv_diff_finals.append(get_params(m))
        theta_conv_diff = agg.aggregate(zero_ref, conv_diff_finals, weights)
        res.regime_acc[REGIME_CONVERGED_DIFF] = eval_params(theta_conv_diff)
        # Displacement here is measured from θ₀ for a comparable scale (how far the
        # different-init finals sit from where HE-IFD started).
        diff_deltas_vs_theta0 = [_params_diff(f, theta0) for f in conv_diff_finals]
        res.regime_mean_displacement[REGIME_CONVERGED_DIFF] = _mean_displacement_l2(
            diff_deltas_vs_theta0, weights)

        # =================================================================
        # Regime 4 — UNBOUNDED distillation from the SHARED θ₀ (optional).
        # Same KL objective and same θ₀ as regime 1, only unbounded_K ≫ K, so the
        # ONLY difference from HE-IFD is displacement magnitude. Aggregate as
        # θ₀ + Σ w_i·Δ_i.
        # =================================================================
        if include_unbounded:
            deltas_unbounded = distill_all_clients(
                teachers, theta0, make_model_fn, client_X_list,
                K_steps=unbounded_K, lr=student_lr, momentum=0.0, tau=tau, bs=spec.bs)
            theta_unbounded = agg.aggregate(theta0, deltas_unbounded, weights)
            res.regime_acc[REGIME_UNBOUNDED] = eval_params(theta_unbounded)
            res.regime_mean_displacement[REGIME_UNBOUNDED] = _mean_displacement_l2(
                deltas_unbounded, weights)

        res.status = "success"
    except Exception as exc:  # noqa: BLE001 — record failure, keep the sweep alive
        import traceback

        res.status = "FAIL"
        res.error = "".join(traceback.format_exception_only(type(exc), exc)).strip()
        res.notes += f" | traceback: {traceback.format_exc()[-800:]}"
    res.wall_clock_sec = time.time() - t_start
    return res


# ---------------------------------------------------------------------------
# Results writer (small, dedicated — the protocol report.py is keyed to the
# protocol CellResult/M3/M4 schema, which does not fit per-regime rows; the issue
# explicitly permits a small writer in this module). Pure stdlib -> login-node safe.
# ---------------------------------------------------------------------------
ABLATION_BLURB = (
    "Aggregation-coherence ablation (issue 006 / PRD user story 17): empirical "
    "evidence for *why* HE-IFD's single sample-weighted linear aggregate works. "
    "On each shared cell the partition, the per-client teachers, and the raw_union "
    "Phase-0-aligned init θ₀ are held FIXED; the only thing that varies across "
    "regimes is how each client's student travelled from θ₀. HE-IFD (bounded K-step "
    "distillation from the shared θ₀) is expected to dominate the naive-average "
    "regimes — converged-from-shared-init, unbounded-distillation-from-shared-init, "
    "and converged-from-different-inits — most clearly at low α, which is the "
    "basin-coherence claim: bounded departures from one aligned init stay in one "
    "loss basin, naive averaging of diverged / different-basin models does not."
)

_REGIME_ORDER = ALL_REGIMES


def _fmt(x, nd: int = 4) -> str:
    return f"{x:.{nd}f}" if isinstance(x, (int, float)) else "n/a"


def write_ablation_csv(path: Path, cells: List[AblationCellResult]) -> None:
    """Long-form CSV: one row per (cell, regime). Pure stdlib csv."""
    import csv

    fields = [
        "backbone", "dataset", "N", "alpha", "seed", "regime",
        "acc", "mean_displacement_l2",
        "theta0_acc", "mean_teacher", "best_teacher",
        "K", "unbounded_K", "converge_epochs", "K_per_class",
        "probe_size_actual", "tau", "student_lr",
        "wall_clock_sec", "job_id", "node", "status", "error",
    ]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for c in cells:
            for regime in _REGIME_ORDER:
                if regime not in c.regime_acc:
                    continue
                w.writerow({
                    "backbone": c.backbone, "dataset": c.dataset, "N": c.N,
                    "alpha": c.alpha, "seed": c.seed, "regime": regime,
                    "acc": c.regime_acc.get(regime),
                    "mean_displacement_l2": c.regime_mean_displacement.get(regime),
                    "theta0_acc": c.theta0_acc, "mean_teacher": c.mean_teacher,
                    "best_teacher": c.best_teacher, "K": c.K,
                    "unbounded_K": c.unbounded_K, "converge_epochs": c.converge_epochs,
                    "K_per_class": c.K_per_class,
                    "probe_size_actual": c.probe_size_actual, "tau": c.tau,
                    "student_lr": c.student_lr, "wall_clock_sec": c.wall_clock_sec,
                    "job_id": c.job_id, "node": c.node, "status": c.status,
                    "error": c.error,
                })


def write_partition_jsonl(path: Path, cells: List[AblationCellResult]) -> None:
    with open(path, "w") as f:
        for c in cells:
            f.write(json.dumps({
                "backbone": c.backbone, "N": c.N, "alpha": c.alpha, "seed": c.seed,
                "per_client_total": c.per_client_total,
                "per_client_per_class": c.per_client_per_class,
                "sample_weights": c.sample_weights,
            }) + "\n")


def _aggregate_seed_mean(cells: List[AblationCellResult]):
    """Group cells by (backbone, N, α) and average each regime's acc over seeds.

    Returns a sorted list of
    ``(backbone, dataset, N, α, n_seeds, {regime: (mean_acc, std_acc, mean_disp)},
      theta0_acc_mean, mean_teacher_mean, best_teacher_mean)``.
    """
    import math
    from collections import defaultdict

    groups: Dict[tuple, List[AblationCellResult]] = defaultdict(list)
    for c in cells:
        groups[(c.backbone, c.dataset, c.N, c.alpha)].append(c)

    out = []
    for (bb, ds, N, a), cs in groups.items():
        per_regime = {}
        for regime in _REGIME_ORDER:
            accs = [c.regime_acc[regime] for c in cs
                    if regime in c.regime_acc and c.regime_acc[regime] is not None]
            disps = [c.regime_mean_displacement.get(regime) for c in cs
                     if c.regime_mean_displacement.get(regime) is not None]
            if not accs:
                continue
            mean = sum(accs) / len(accs)
            var = sum((x - mean) ** 2 for x in accs) / len(accs)
            mean_disp = (sum(disps) / len(disps)) if disps else None
            per_regime[regime] = (mean, math.sqrt(var), mean_disp)

        def _avg(vals):
            v = [x for x in vals if isinstance(x, (int, float))]
            return (sum(v) / len(v)) if v else None

        out.append((
            bb, ds, N, a, len(cs), per_regime,
            _avg([c.theta0_acc for c in cs]),
            _avg([c.mean_teacher for c in cs]),
            _avg([c.best_teacher for c in cs]),
        ))
    out.sort(key=lambda r: (str(r[0]), r[2], r[3]))
    return out


def render_table(cells: List[AblationCellResult]) -> str:
    """Markdown: one row per (backbone, N, α), regime accuracies side by side
    (mean ± std over seeds), plus the coherence margin Δ = heifd − max(naive).

    A positive Δ at low α is the headline finding (HE-IFD ≫ naive averages)."""
    grouped = _aggregate_seed_mean(cells)
    head = (
        "| backbone | N | α | seeds | θ₀_acc | mean_teacher | "
        "HE-IFD (ours) | converged@θ₀ | unbounded@θ₀ | converged@diff-init | "
        "Δ(ours − best-naive) |\n"
        "|---|---|---|---|--------|--------------|------------|------------|------------|------------|------|"
    )
    body = []
    for (bb, ds, N, a, n_seeds, per_regime, t0, mt, bt) in grouped:
        def cell(regime):
            if regime not in per_regime:
                return "n/a"
            mean, std, _ = per_regime[regime]
            return f"{mean:.4f}±{std:.4f}"

        heifd_mean = per_regime.get(REGIME_HEIFD, (None,))[0]
        naive_means = [per_regime[r][0] for r in
                       (REGIME_CONVERGED_SHARED, REGIME_UNBOUNDED, REGIME_CONVERGED_DIFF)
                       if r in per_regime]
        margin = (f"{heifd_mean - max(naive_means):+.4f}"
                  if (heifd_mean is not None and naive_means) else "n/a")
        body.append(
            f"| {bb} | {N} | {a} | {n_seeds} | {_fmt(t0)} | {_fmt(mt)} | "
            f"{cell(REGIME_HEIFD)} | {cell(REGIME_CONVERGED_SHARED)} | "
            f"{cell(REGIME_UNBOUNDED)} | {cell(REGIME_CONVERGED_DIFF)} | {margin} |")
    table = head + "\n" + ("\n".join(body) if body else "| _(no cells yet)_ |")

    disp = ["", "### Mean per-client displacement ‖Δ_i‖₂ (sample-weighted)",
            "", "Boundedness made quantitative: HE-IFD's bounded K-step trajectory "
            "should show the smallest displacement; converged/unbounded the largest.",
            "",
            "| backbone | N | α | HE-IFD | converged@θ₀ | unbounded@θ₀ | converged@diff-init |",
            "|---|---|---|--------|------------|------------|------------|"]
    for (bb, ds, N, a, n_seeds, per_regime, t0, mt, bt) in grouped:
        def dcell(regime):
            if regime not in per_regime or per_regime[regime][2] is None:
                return "n/a"
            return f"{per_regime[regime][2]:.2f}"
        disp.append(
            f"| {bb} | {N} | {a} | {dcell(REGIME_HEIFD)} | "
            f"{dcell(REGIME_CONVERGED_SHARED)} | {dcell(REGIME_UNBOUNDED)} | "
            f"{dcell(REGIME_CONVERGED_DIFF)} |")
    return table + "\n" + "\n".join(disp)


def write_report(results_dir: str, cells: List[AblationCellResult], args: Dict) -> None:
    root = Path(results_dir)
    root.mkdir(parents=True, exist_ok=True)
    (root / "runs").mkdir(exist_ok=True)
    write_ablation_csv(root / "results.csv", cells)
    write_partition_jsonl(root / "partition_diagnostic.jsonl", cells)

    config_block = (
        "## Ablation configuration\n\n"
        f"- Backbones: `{args.get('backbones')}`\n"
        f"- N values: `{args.get('Ns')}`\n"
        f"- Dirichlet α: `{args.get('alphas')}`\n"
        f"- Seeds: `{args.get('seeds')}`\n"
        f"- K (HE-IFD bounded trajectory): `{args.get('K')}`\n"
        f"- unbounded_K (regime 4 long trajectory): `{args.get('unbounded_K')}`\n"
        f"- converge_epochs (regimes 2/3 supervised): `{args.get('converge_epochs')}`\n"
        f"- K_per_class (raw_union probe → θ₀): `{args.get('K_per_class')}`\n"
        f"- τ (distill temperature): `{args.get('tau')}`\n"
        f"- Student LR: `{args.get('student_lr')}`\n"
        f"- include_unbounded (regime 4): `{args.get('include_unbounded')}`\n"
    )

    regimes_block = "## Regimes\n\n" + "\n".join(
        f"- **{r}** — {REGIME_BLURB[r]}" for r in _REGIME_ORDER)

    case = root.name
    (root / "README.md").write_text(
        f"# {case}\n\n"
        f"{ABLATION_BLURB}\n\n"
        f"{regimes_block}\n\n"
        f"{config_block}\n"
        f"## Results\n\n"
        f"{render_table(cells)}\n\n"
        f"Raw per-cell JSONs live here as "
        f"`cell_<backbone>_N<n>_a<α>_s<seed>_<hash>.json` (one cell = all regimes "
        f"on one shared θ₀/partition/teacher set). Long-form rows (one per "
        f"cell×regime) at `results.csv`; per-client per-class counts at "
        f"`partition_diagnostic.jsonl`; Slurm logs at `runs/`.\n"
    )


# ---------------------------------------------------------------------------
# Resumable / chunkable CLI (mirrors src/sweep.py conventions)
# ---------------------------------------------------------------------------
def cell_descriptor(backbone: str, N: int, alpha: float, seed: int) -> Dict:
    return {"backbone": backbone, "N": N, "alpha": alpha, "seed": seed}


def descriptor_hash(desc: Dict) -> str:
    import hashlib

    canon = json.dumps(desc, sort_keys=True, default=str)
    return hashlib.sha256(canon.encode()).hexdigest()[:12]


def cell_filename(desc: Dict) -> str:
    stem = f"cell_{desc['backbone']}_N{desc['N']}_a{desc['alpha']}_s{desc['seed']}"
    return f"{stem}_{descriptor_hash(desc)}.json"


def write_cell_json(results_dir: Path, res: AblationCellResult, desc: Dict) -> Path:
    path = results_dir / cell_filename(desc)
    payload = res.to_dict()
    payload["_descriptor"] = desc
    path.write_text(json.dumps(payload, indent=2))
    return path


def load_cells(results_dir: Path) -> List[AblationCellResult]:
    cells: List[AblationCellResult] = []
    for p in sorted(results_dir.glob("cell_*.json")):
        try:
            d = json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        d.pop("_descriptor", None)
        valid = {f: d[f] for f in AblationCellResult.__dataclass_fields__ if f in d}
        cells.append(AblationCellResult(**valid))
    return cells


def parse_float_list(s: str) -> List[float]:
    out = []
    for x in s.split(","):
        x = x.strip()
        if not x:
            continue
        out.append(float("inf") if x in ("inf", "Inf") else float(x))
    return out


def parse_int_list(s: str) -> List[int]:
    return [int(x) for x in s.split(",") if x.strip()]


def parse_str_list(s: str) -> List[str]:
    return [x.strip() for x in s.split(",") if x.strip()]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Resumable, chunkable HE-IFD aggregation-coherence ablation "
                    "(issue 006): HE-IFD vs naive-average regimes on a shared cell.")
    p.add_argument("--backbones", type=str, default="mlp_mnist,cnn5_cifar10",
                   help=f"Comma list from {sorted(BACKBONES)}.")
    p.add_argument("--Ns", type=str, default="10", help="Client counts, e.g. 10.")
    p.add_argument("--alphas", type=str, default="0.05,0.3",
                   help="Dirichlet alphas (low + mid), e.g. 0.05,0.3.")
    p.add_argument("--seeds", type=str, default="42,43,44", help="Seeds, e.g. 42,43,44.")
    p.add_argument("--K", type=int, default=300,
                   help="HE-IFD bounded distillation trajectory length (regime 1).")
    p.add_argument("--unbounded-K", type=int, default=3000,
                   help="Unbounded distillation length for regime 4 (≫ K).")
    p.add_argument("--converge-epochs", type=int, default=40,
                   help="Supervised epochs to convergence for regimes 2/3.")
    p.add_argument("--K-per-class", type=int, default=20,
                   help="raw_union samples/class/client used to warm the shared θ₀.")
    p.add_argument("--tau", type=float, default=4.0)
    p.add_argument("--student-lr", type=float, default=0.01)
    p.add_argument("--probe-size", type=int, default=None,
                   help="Labelled-probe size P (default: backbone-specific).")
    p.add_argument("--no-unbounded", action="store_true",
                   help="Skip regime 4 (the unbounded-distillation variant).")
    p.add_argument("--case", type=str, default="heifd_coherence_ablation",
                   help="Case slug -> results/<case>/.")
    p.add_argument("--results-root", type=str, default="results")
    p.add_argument("--data-root", type=str, default="data")
    p.add_argument("--cache-root", type=str, default="cache")
    p.add_argument("--num-chunks", type=int,
                   default=int(os.environ.get("NUM_CHUNKS", "1")),
                   help="Split the grid into this many contiguous chunks.")
    p.add_argument("--chunk-index", type=int,
                   default=int(os.environ.get("CHUNK_INDEX", "0")),
                   help="Which chunk (0-based) this job runs.")
    p.add_argument("--force", action="store_true",
                   help="Recompute even if a cell JSON already exists.")
    return p.parse_args()


def build_grid(args) -> List[Dict]:
    grid: List[Dict] = []
    for backbone in parse_str_list(args.backbones):
        for N in parse_int_list(args.Ns):
            for alpha in parse_float_list(args.alphas):
                for seed in parse_int_list(args.seeds):
                    grid.append(cell_descriptor(backbone, N, alpha, seed))
    return grid


def select_chunk(grid: List[Dict], num_chunks: int, chunk_index: int) -> List[Dict]:
    if num_chunks <= 1:
        return grid
    if not (0 <= chunk_index < num_chunks):
        raise ValueError(f"chunk_index {chunk_index} out of range [0,{num_chunks})")
    return [d for i, d in enumerate(grid) if i % num_chunks == chunk_index]


def main() -> None:
    args = parse_args()
    job_id = os.environ.get("SLURM_JOB_ID")
    node = os.environ.get("SLURMD_NODENAME") or os.environ.get("HOSTNAME")
    include_unbounded = not args.no_unbounded

    results_dir = Path(args.results_root) / args.case
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "runs").mkdir(exist_ok=True)

    grid = build_grid(args)
    my_cells = select_chunk(grid, args.num_chunks, args.chunk_index)
    print(f"[ablation] grid={len(grid)} cells; chunk {args.chunk_index}/{args.num_chunks} "
          f"-> {len(my_cells)} cells; case={args.case}", flush=True)

    n_run = n_skip = n_fail = 0
    for desc in my_cells:
        out_path = results_dir / cell_filename(desc)
        if out_path.exists() and not args.force:
            prior_ok = False
            try:
                prior_ok = json.loads(out_path.read_text()).get("status") == "success"
            except (json.JSONDecodeError, OSError):
                prior_ok = False
            if prior_ok:
                n_skip += 1
                print(f"[ablation] skip  {out_path.name} (success exists)", flush=True)
                continue
            print(f"[ablation] retry {out_path.name} (prior status != success)", flush=True)
        print(f"[ablation] start {desc['backbone']} N={desc['N']} a={desc['alpha']} "
              f"s={desc['seed']}", flush=True)
        res = run_cell_ablation(
            backbone=desc["backbone"], N=desc["N"], alpha=desc["alpha"],
            seed=desc["seed"], K=args.K, unbounded_K=args.unbounded_K,
            converge_epochs=args.converge_epochs, K_per_class=args.K_per_class,
            tau=args.tau, student_lr=args.student_lr, probe_size=args.probe_size,
            include_unbounded=include_unbounded,
            data_root=args.data_root, cache_root=args.cache_root,
            job_id=job_id, node=node,
        )
        write_cell_json(results_dir, res, desc)
        tag = "ok" if res.status == "success" else "FAIL"
        if res.status != "success":
            n_fail += 1
        else:
            n_run += 1
        accs = " ".join(
            f"{r}={res.regime_acc[r]:.4f}" for r in ALL_REGIMES
            if r in res.regime_acc and res.regime_acc[r] is not None)
        print(f"[ablation] {tag}   {accs} wall={res.wall_clock_sec:.1f}s "
              f"err={res.error}", flush=True)

    all_cells = load_cells(results_dir)
    write_report(results_dir=str(results_dir), cells=all_cells,
                 args={**vars(args), "include_unbounded": include_unbounded})
    print(f"[ablation] done. ran={n_run} skipped={n_skip} failed={n_fail}. "
          f"report at {results_dir / 'README.md'}", flush=True)


if __name__ == "__main__":
    main()
