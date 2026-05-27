"""Single-cell driver: (N, seed) -> CellResult JSON.

A "cell" is one experimental condition: one N value, one seed. Produces:
    student_acc, mean_teacher_acc, per_client_per_class_holdings,
    wall_clock_sec, per-phase timing, JSON written to results_dir.
"""
from __future__ import annotations

import json
import os
import socket
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import torch
import torch.nn as nn

from .aggregate import linear_aggregate
from .data import (
    client_subsets,
    dirichlet_partition,
    load_mnist,
    materialize_probe_tensor,
    probe_and_local_union_dataset,
    split_probe_from_test,
)
from .distill import local_distill
from .evaluation import evaluate_state, mean_teacher_acc
from .model import build_mlp, state_dict_named
from .teacher import train_all_teachers


@dataclass
class CellResult:
    method: str
    dataset: str
    N: int
    alpha: float
    seed: int
    K: int
    tau: float
    probe_size: int
    use_probe: bool
    student_acc: Optional[float]
    mean_teacher_acc: Optional[float]
    best_teacher_acc: Optional[float]
    worst_teacher_acc: Optional[float]
    per_teacher_acc: List[float]
    per_client_total: List[int]
    per_client_per_class: List[List[int]]
    wall_clock_sec: float
    phase_teacher_sec: float
    phase_distill_sec: float
    phase_aggregate_sec: float
    phase_eval_sec: float
    job_id: str
    node: str
    status: str
    error: Optional[str] = None
    notes: str = ""

    def dump(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(asdict(self), f, indent=2)


def shared_theta0(seed: int, device: str) -> Dict[str, torch.Tensor]:
    torch.manual_seed(seed)
    model = build_mlp().to(device)
    return state_dict_named(model)


def run_cell(
    *,
    N: int,
    seed: int,
    alpha: float = 0.1,
    K: int = 5,
    tau: float = 4.0,
    probe_size: int = 5000,
    use_probe: bool = False,
    teacher_epochs: int = 30,
    distill_lr: float = 1e-2,
    distill_batch_size: int = 64,
    cache_root: str = "cache",
    results_dir: str = "results/v1_he-ifd_mlp_mnist_n-sweep",
    device: str = "cuda" if torch.cuda.is_available() else "cpu",
) -> CellResult:
    job_id = os.environ.get("SLURM_JOB_ID", "local")
    node = socket.gethostname()
    t_start = time.time()

    effective_probe_size = probe_size if use_probe else 0
    distill_inputs_label = "P∪D_i" if use_probe else "D_i"
    result = CellResult(
        method="he-ifd-v1",
        dataset="MNIST",
        N=N, alpha=alpha, seed=seed, K=K, tau=tau,
        probe_size=effective_probe_size, use_probe=use_probe,
        student_acc=None, mean_teacher_acc=None,
        best_teacher_acc=None, worst_teacher_acc=None,
        per_teacher_acc=[], per_client_total=[], per_client_per_class=[],
        wall_clock_sec=0.0, phase_teacher_sec=0.0, phase_distill_sec=0.0,
        phase_aggregate_sec=0.0, phase_eval_sec=0.0,
        job_id=job_id, node=node, status="failed",
        error=None,
        notes=(f"v1 simulation: plaintext, server linear-only. "
               f"loss=KL(tau={tau}), inputs={distill_inputs_label}, alpha_i=1/N, "
               f"end-of-K cumulative deltas, CKS-decrypt deferred."),
    )

    try:
        # Data.
        train_ds, test_ds = load_mnist()
        if use_probe:
            probe_ds, eval_ds = split_probe_from_test(test_ds, probe_size=probe_size, seed=seed)
        else:
            probe_ds = None
            eval_ds = test_ds
        idx_per_client, per_class_holdings = dirichlet_partition(
            train_ds, n_clients=N, alpha=alpha, seed=seed,
        )
        subsets = client_subsets(train_ds, idx_per_client)
        result.per_client_total = [len(s) for s in subsets]
        result.per_client_per_class = per_class_holdings.tolist()

        # Teachers (cached).
        t0 = time.time()
        teachers = train_all_teachers(
            client_subsets=subsets, cache_root=cache_root,
            dataset="MNIST", N=N, alpha=alpha, seed=seed,
            n_classes=10, device=device, epochs=teacher_epochs,
        )
        result.phase_teacher_sec = time.time() - t0

        # Shared init.
        theta0 = shared_theta0(seed=seed, device=device)

        # Local distillation per client -> per-layer deltas.
        t0 = time.time()
        client_deltas: List[Dict[str, torch.Tensor]] = []
        for i, (teacher, local_subset) in enumerate(zip(teachers, subsets)):
            distill_ds = (
                probe_and_local_union_dataset(probe_ds, local_subset)
                if use_probe else local_subset
            )
            delta = local_distill(
                teacher=teacher, union_ds=distill_ds, theta0=theta0,
                epochs=K, batch_size=distill_batch_size, lr=distill_lr,
                momentum=0.9, tau=tau, device=device, seed=2000 + i,
            )
            client_deltas.append(delta)
        result.phase_distill_sec = time.time() - t0

        # Server aggregation (linear-only).
        t0 = time.time()
        W_E = linear_aggregate(theta0=theta0, client_deltas=client_deltas)
        result.phase_aggregate_sec = time.time() - t0

        # Evaluate.
        t0 = time.time()
        student_acc = evaluate_state(W_E, eval_ds=eval_ds, device=device)
        mt_acc, per_teacher = mean_teacher_acc(teachers, eval_ds=eval_ds, device=device)
        result.phase_eval_sec = time.time() - t0
        result.student_acc = student_acc
        result.mean_teacher_acc = mt_acc
        result.per_teacher_acc = per_teacher
        result.best_teacher_acc = max(per_teacher) if per_teacher else None
        result.worst_teacher_acc = min(per_teacher) if per_teacher else None
        result.status = "success"

    except Exception as exc:  # pragma: no cover - defensive
        import traceback
        result.error = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
        result.status = "failed"

    result.wall_clock_sec = time.time() - t_start
    out_path = Path(results_dir) / f"cell_N{N}_s{seed}_{job_id}.json"
    result.dump(str(out_path))
    return result
