"""Single-cell driver for v2: (dataset, N, seed, method) -> CellResult JSON.

Methods supported in this first build:
    M0  -- "FedAvg-LoRA": each client fine-tunes a LoRA on D_i, ships the
           LoRA params themselves (no distillation, no student). Server
           averages. Strong, widely-used baseline.
    M1  -- "HE-IFD-LoRA": each client fine-tunes a teacher LoRA, then distils
           it into a fresh student LoRA via KL on D_i, ships student LoRA
           delta. Server averages.

Both are strict 1-shot. The 1.5-shot variant lives in src/v2/oneshot_ensemble.py
(to be added later).
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
from .data import (client_subsets, dirichlet_partition, load_cifar10,
                   load_cifar100, split_probe_from_test)
from .distill import local_distill, fresh_student
from .evaluation import evaluate_module
from .model import (build_vit, wrap_with_lora, lora_trainable_state,
                    lora_trainable_load, trainable_param_count)
from .teacher import build_teacher_model, train_all_teachers


@dataclass
class CellResult:
    method: str
    dataset: str
    num_classes: int
    N: int
    alpha: float
    seed: int
    K: int
    tau: float
    rank: int
    lora_alpha: int
    weight_mode: str
    teacher_epochs: int
    teacher_lr: float
    distill_lr: float
    distill_batch_size: int
    student_acc: Optional[float]
    student_per_class: Optional[Dict[int, float]]
    per_teacher_acc: List[float]
    best_teacher_acc: Optional[float]
    mean_teacher_acc: Optional[float]
    worst_teacher_acc: Optional[float]
    per_client_total: List[int]
    per_client_per_class: List[List[int]]
    trainable_params_per_client: int
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


def load_dataset(name: str):
    if name == "cifar10":
        train, test = load_cifar10()
        return train, test, 10
    if name == "cifar100":
        train, test = load_cifar100()
        return train, test, 100
    raise ValueError(f"unknown dataset: {name}")


def run_cell(*, method: str, dataset: str, N: int, seed: int,
             alpha: float = 0.1,
             K: int = 3, tau: float = 4.0,
             rank: int = 8, lora_alpha: int = 16,
             weight_mode: str = "samples",
             teacher_epochs: int = 3, teacher_lr: float = 5e-4,
             distill_lr: float = 5e-4, distill_batch_size: int = 128,
             teacher_batch_size: int = 128,
             cache_root: str = "cache",
             results_dir: str = "results/v2_he-ifd_vit_cifar10",
             device: str = "cuda" if torch.cuda.is_available() else "cpu",
             ) -> CellResult:
    job_id = os.environ.get("SLURM_JOB_ID", "local")
    node = socket.gethostname()
    t_start = time.time()

    train_ds, test_ds, num_classes = load_dataset(dataset)

    result = CellResult(
        method=method, dataset=dataset, num_classes=num_classes,
        N=N, alpha=alpha, seed=seed, K=K, tau=tau,
        rank=rank, lora_alpha=lora_alpha, weight_mode=weight_mode,
        teacher_epochs=teacher_epochs, teacher_lr=teacher_lr,
        distill_lr=distill_lr, distill_batch_size=distill_batch_size,
        student_acc=None, student_per_class=None,
        per_teacher_acc=[], best_teacher_acc=None, mean_teacher_acc=None,
        worst_teacher_acc=None,
        per_client_total=[], per_client_per_class=[],
        trainable_params_per_client=0,
        wall_clock_sec=0.0, phase_teacher_sec=0.0, phase_distill_sec=0.0,
        phase_aggregate_sec=0.0, phase_eval_sec=0.0,
        job_id=job_id, node=node, status="failed",
        error=None,
        notes=(f"v2 ViT-B/16 + LoRA fine-tune, dataset={dataset}, "
               f"weight_mode={weight_mode}, method={method}"),
    )

    try:
        idx_per, holdings = dirichlet_partition(train_ds, N, alpha, seed)
        subs = client_subsets(train_ds, idx_per)
        client_sizes = [len(s) for s in subs]
        result.per_client_total = client_sizes
        result.per_client_per_class = holdings.tolist()

        # ---- Phase 1: teacher LoRA per client ----
        t0 = time.time()
        teacher_states = train_all_teachers(
            subs, dataset=dataset, num_classes=num_classes,
            N=N, alpha=alpha, seed=seed, cache_root=cache_root,
            epochs=teacher_epochs, lr=teacher_lr,
            batch_size=teacher_batch_size,
            rank=rank, lora_alpha=lora_alpha, device=device,
        )
        result.phase_teacher_sec = time.time() - t0

        # Materialize teachers for distillation / eval
        teachers = [build_teacher_model(s, num_classes=num_classes,
                                        rank=rank, alpha=lora_alpha,
                                        device=device)
                    for s in teacher_states]

        # ---- Shared student init (deterministic) ----
        student_init_seed = seed + 7
        ref_student = fresh_student(num_classes, rank, lora_alpha,
                                    student_init_seed, device)
        initial = lora_trainable_state(ref_student)
        result.trainable_params_per_client = trainable_param_count(ref_student)
        del ref_student

        # ---- Phase 2: build per-client deltas ----
        t0 = time.time()
        client_deltas: List[Dict[str, torch.Tensor]] = []
        if method == "M0":
            # FedAvg-LoRA: the teacher LoRA *is* the delta (since the shared
            # init for the teacher is the same as the student's init).
            for ts in teacher_states:
                client_deltas.append({k: ts[k] - initial[k] for k in initial})
        elif method == "M1":
            # HE-IFD-LoRA: distill teacher into a fresh student via KL on D_i.
            for ci, (teacher, sub) in enumerate(zip(teachers, subs)):
                d = local_distill(
                    teacher, sub, num_classes=num_classes,
                    rank=rank, alpha=lora_alpha, init_seed=student_init_seed,
                    K=K, lr=distill_lr, batch_size=distill_batch_size,
                    tau=tau, device=device, run_seed=2000 + ci,
                )
                client_deltas.append(d)
        else:
            raise ValueError(f"unknown method: {method}")
        result.phase_distill_sec = time.time() - t0

        # ---- Phase 3: server-side linear aggregation ----
        t0 = time.time()
        W_E = linear_aggregate(initial, client_deltas,
                               client_sizes=client_sizes,
                               weight_mode=weight_mode)
        result.phase_aggregate_sec = time.time() - t0

        # ---- Phase 4: eval ----
        t0 = time.time()
        student_for_eval = fresh_student(num_classes, rank, lora_alpha,
                                         student_init_seed, device)
        lora_trainable_load(student_for_eval, W_E)
        s_acc, s_per_class = evaluate_module(student_for_eval, test_ds, device)

        per_teacher = []
        for tm in teachers:
            ta, _ = evaluate_module(tm, test_ds, device)
            per_teacher.append(ta)
        result.phase_eval_sec = time.time() - t0

        result.student_acc = s_acc
        result.student_per_class = s_per_class
        result.per_teacher_acc = per_teacher
        result.best_teacher_acc = max(per_teacher) if per_teacher else None
        result.mean_teacher_acc = sum(per_teacher) / len(per_teacher) if per_teacher else None
        result.worst_teacher_acc = min(per_teacher) if per_teacher else None
        result.status = "success"

    except Exception as exc:
        import traceback
        result.error = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
        result.status = "failed"

    result.wall_clock_sec = time.time() - t_start
    out_path = Path(results_dir) / f"cell_{method}_{dataset}_N{N}_s{seed}_{job_id}.json"
    result.dump(str(out_path))
    return result
