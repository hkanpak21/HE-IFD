"""Anchor ablation sweep.

Axes:
  anchors_per_class K_a in {1, 5, 20}
  anchor_lambda     lam in {1.0, 5.0, 10.0}
  N                 in {4, 8, 16, 32}

Runs M1 only for each (K_a, lam, N). Method M0 / M3 baselines are loaded
from previous grid runs for comparison.
"""
from __future__ import annotations
import argparse, json, time
from pathlib import Path

import torch

from .run import pick_device, run_one


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--Ns", type=str, default="4,8,16,32")
    ap.add_argument("--Kas", type=str, default="1,5,20")
    ap.add_argument("--lams", type=str, default="1.0,5.0,10.0")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--alpha", type=float, default=0.1)
    ap.add_argument("--K", type=int, default=5)
    ap.add_argument("--teacher-epochs", type=int, default=10)
    ap.add_argument("--anchor-scale", type=float, default=3.0)
    ap.add_argument("--cache-root", type=str, default="playground/cache")
    ap.add_argument("--out", type=str, default="playground/results/ablate.json")
    args = ap.parse_args()

    device = pick_device()
    print(f"[ablate] device={device}")

    Ns   = [int(x) for x in args.Ns.split(",")]
    Kas  = [int(x) for x in args.Kas.split(",")]
    lams = [float(x) for x in args.lams.split(",")]

    rows = []
    n_total = len(Ns) * len(Kas) * len(lams)
    n_done = 0
    for N in Ns:
        for Ka in Kas:
            for lam in lams:
                n_done += 1
                tag = f"N={N} K_a={Ka} lam={lam}"
                print(f"[ablate {n_done}/{n_total}] start  {tag}")
                tic = time.time()
                r = run_one("M1", N=N, seed=args.seed, alpha=args.alpha,
                            device=device, K=args.K,
                            teacher_epochs=args.teacher_epochs,
                            probe_size=0,
                            anchor_scale=args.anchor_scale,
                            anchor_lambda=lam, anchors_per_class=Ka,
                            cache_root=args.cache_root)
                r["wall_sec"] = time.time() - tic
                print(f"[ablate {n_done}/{n_total}] ok     {tag}  "
                      f"student={r['student_acc']:.4f}  "
                      f"best_t={r['best_teacher']:.4f}  "
                      f"wall={r['wall_sec']:.1f}s")
                rows.append(r)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(rows, open(args.out, "w"), indent=2)
    print(f"[ablate] done. wrote {args.out}")


if __name__ == "__main__":
    main()
