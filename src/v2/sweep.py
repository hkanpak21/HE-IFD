"""v2 sweep: ViT + LoRA on CIFAR.

Usage:
    python -m src.v2.sweep --methods M0,M1 --Ns 4,8 --seeds 42 --dataset cifar10
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from .cell import run_cell


def parse_int_list(s: str) -> List[int]:
    return [int(x) for x in s.split(",") if x.strip()]


def parse_str_list(s: str) -> List[str]:
    return [x.strip() for x in s.split(",") if x.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--methods", default="M0,M1")
    ap.add_argument("--dataset", default="cifar10", choices=["cifar10", "cifar100"])
    ap.add_argument("--Ns", default="4,8")
    ap.add_argument("--seeds", default="42")
    ap.add_argument("--alpha", type=float, default=0.1)
    ap.add_argument("--K", type=int, default=3)
    ap.add_argument("--tau", type=float, default=4.0)
    ap.add_argument("--rank", type=int, default=8)
    ap.add_argument("--lora-alpha", type=int, default=16)
    ap.add_argument("--weight-mode", default="samples")
    ap.add_argument("--teacher-epochs", type=int, default=3)
    ap.add_argument("--teacher-lr", type=float, default=5e-4)
    ap.add_argument("--teacher-batch-size", type=int, default=128)
    ap.add_argument("--distill-lr", type=float, default=5e-4)
    ap.add_argument("--distill-batch-size", type=int, default=128)
    ap.add_argument("--results-dir", default="results/v2_he-ifd_vit_cifar10")
    ap.add_argument("--cache-root", default="cache/v2")
    args = ap.parse_args()

    methods = parse_str_list(args.methods)
    Ns = parse_int_list(args.Ns)
    seeds = parse_int_list(args.seeds)
    results_dir = Path(args.results_dir)
    (results_dir / "runs").mkdir(parents=True, exist_ok=True)

    summary = []
    for method in methods:
        for N in Ns:
            for seed in seeds:
                print(f"[v2 sweep] start  method={method} dataset={args.dataset} "
                      f"N={N} seed={seed}", flush=True)
                r = run_cell(
                    method=method, dataset=args.dataset,
                    N=N, seed=seed, alpha=args.alpha,
                    K=args.K, tau=args.tau, rank=args.rank,
                    lora_alpha=args.lora_alpha, weight_mode=args.weight_mode,
                    teacher_epochs=args.teacher_epochs,
                    teacher_lr=args.teacher_lr,
                    teacher_batch_size=args.teacher_batch_size,
                    distill_lr=args.distill_lr,
                    distill_batch_size=args.distill_batch_size,
                    cache_root=args.cache_root,
                    results_dir=str(results_dir),
                )
                tag = "ok" if r.status == "success" else "FAIL"
                sa = f"{r.student_acc:.4f}" if r.student_acc is not None else "n/a"
                bt = f"{r.best_teacher_acc:.4f}" if r.best_teacher_acc is not None else "n/a"
                mt = f"{r.mean_teacher_acc:.4f}" if r.mean_teacher_acc is not None else "n/a"
                print(f"[v2 sweep] {tag}    method={method} N={N} seed={seed}  "
                      f"student={sa}  best_t={bt}  mean_t={mt}  "
                      f"wall={r.wall_clock_sec:.1f}s", flush=True)
                summary.append({
                    "method": method, "dataset": args.dataset,
                    "N": N, "seed": seed,
                    "student_acc": r.student_acc,
                    "best_teacher_acc": r.best_teacher_acc,
                    "mean_teacher_acc": r.mean_teacher_acc,
                    "worst_teacher_acc": r.worst_teacher_acc,
                    "wall_clock_sec": r.wall_clock_sec,
                    "trainable_params_per_client": r.trainable_params_per_client,
                    "status": r.status,
                })

    (results_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"[v2 sweep] done. summary at {results_dir}/summary.json", flush=True)


if __name__ == "__main__":
    main()
