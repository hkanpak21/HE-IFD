#!/usr/bin/env python
"""The pooled ceiling: what the same recipe reaches when the data can be pooled.

WHY
---
The headline table's rightmost column is the disclosed model, and a reader can
mistake it for the best achievable number. It is not. It is what one-shot
federated aggregation reaches under this partition; pooling the data outright
reaches more. Without that reference point the accuracy figures cannot be read,
because there is no way to tell how much of the shortfall is the label skew and
how much is the protocol.

WHAT IS HELD FIXED
------------------
Everything except the partition: the same frozen backbone, the same rank-8
adapter with its down-projection frozen, the same head, the same learning rate
and batch size. The only change is that the optimiser sees the union of the
clients' shards instead of one shard.

BUDGETS
-------
Two, because either alone invites an objection.
  matched-per-client   K steps, what one client spends
  matched-total        N*K steps, what the federation spends in aggregate
The second is the honest ceiling for a same-compute comparison.

Usage:  python jobs/centralised_ceiling.py [task ...] [seed ...]
"""
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import finetune_improve as fi  # noqa: E402

OUTDIR = Path("results") / "centralised_ceiling"
OUTDIR.mkdir(parents=True, exist_ok=True)

BACKBONE = "roberta_base"
TASKS = ["ag_news", "trec", "dbpedia_14", "banking77"]
SEEDS = [42, 43, 44]
N, K, R = 10, 200, 8
LR, BS = 5e-4, 32


def run(task, seed, rows):
    print(f"\n=== {task} seed={seed} ===", flush=True)
    ids_tr, mask_tr, ytr, ids_te, mask_te, yte, C = fi._data(task, BACKBONE, seed)

    for tag, steps in (("matched_per_client", K), ("matched_total", N * K)):
        fi.set_seed(seed)
        model = fi.TextLoRA(BACKBONE, C, r=R, freeze_a=True).to(fi.DEVICE)
        theta0 = fi.trainable_state(model)
        fi.train_steps(model, ids_tr, mask_tr, ytr, steps=steps, lr=LR, bs=BS,
                       theta0=theta0)
        acc = float(fi.evaluate(model, ids_te, mask_te, yte))
        rows.append(dict(task=task, C=C, seed=seed, mode=tag, steps=steps,
                         acc=round(acc, 4)))
        print(f"  >> {tag:<20} steps={steps:<5} acc={acc:.4f}", flush=True)
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


def main():
    args = sys.argv[1:]
    tasks = [a for a in args if not a.isdigit()] or TASKS
    seeds = [int(a) for a in args if a.isdigit()] or SEEDS
    rows = []
    for t in tasks:
        for s in seeds:
            run(t, s, rows)

    cols = ["task", "C", "seed", "mode", "steps", "acc"]
    out = OUTDIR / "results.csv"
    hdr = not out.exists()
    with out.open("a") as f:
        if hdr:
            f.write(",".join(cols) + "\n")
        for r in rows:
            f.write(",".join(str(r[c]) for c in cols) + "\n")
    print(f"\nwrote {out}", flush=True)

    print("\n" + ",".join(cols))
    for r in rows:
        print(",".join(str(r[c]) for c in cols))

    # per-task mean over seeds, the form the paper's table needs
    print("\ntask,mode,acc_mean")
    for t in sorted({r["task"] for r in rows}):
        for m in ("matched_per_client", "matched_total"):
            a = [r["acc"] for r in rows if r["task"] == t and r["mode"] == m]
            if a:
                print(f"{t},{m},{np.mean(a):.4f}")


if __name__ == "__main__":
    main()
