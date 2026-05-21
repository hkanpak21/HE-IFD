"""Drive a sweep over N values and seeds. CLI entrypoint for the sbatch wrapper.

Usage:
    python -m src.v1.sweep --Ns 1,2,4,8,16,32 --seeds 42 --K 5
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from .cell import run_cell
from .report import write_report


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--Ns", type=str, default="1,2,4,8,16,32",
                   help="Comma-separated N values to sweep.")
    p.add_argument("--seeds", type=str, default="42",
                   help="Comma-separated seeds.")
    p.add_argument("--alpha", type=float, default=0.1)
    p.add_argument("--K", type=int, default=5,
                   help="Client-side distillation epochs.")
    p.add_argument("--tau", type=float, default=4.0)
    p.add_argument("--probe-size", type=int, default=5000)
    p.add_argument("--use-probe", action="store_true",
                   help="Include public probe P in distillation set (P ∪ D_i). "
                        "Default: False (D_i only).")
    p.add_argument("--teacher-epochs", type=int, default=30)
    p.add_argument("--results-dir", default="results/v1_he-ifd_mlp_mnist_n-sweep")
    p.add_argument("--cache-root", default="cache")
    return p.parse_args()


def parse_int_list(s: str) -> List[int]:
    return [int(x) for x in s.split(",") if x.strip()]


def main() -> None:
    args = parse_args()
    Ns = parse_int_list(args.Ns)
    seeds = parse_int_list(args.seeds)
    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "runs").mkdir(exist_ok=True)

    cells = []
    for N in Ns:
        for seed in seeds:
            print(f"[sweep] start  N={N} seed={seed} alpha={args.alpha} K={args.K}", flush=True)
            res = run_cell(
                N=N, seed=seed, alpha=args.alpha, K=args.K, tau=args.tau,
                probe_size=args.probe_size, use_probe=args.use_probe,
                teacher_epochs=args.teacher_epochs,
                cache_root=args.cache_root, results_dir=str(results_dir),
            )
            cells.append(res)
            tag = "ok" if res.status == "success" else "FAIL"
            sa = f"{res.student_acc:.4f}" if res.student_acc is not None else "n/a"
            mt = f"{res.mean_teacher_acc:.4f}" if res.mean_teacher_acc is not None else "n/a"
            print(f"[sweep] {tag}    N={N} seed={seed}  student={sa}  mean_teacher={mt}  "
                  f"wall={res.wall_clock_sec:.1f}s", flush=True)

    write_report(results_dir=str(results_dir), cells=cells, args=vars(args))
    print(f"[sweep] done. report at {results_dir / 'README.md'}", flush=True)


if __name__ == "__main__":
    main()
