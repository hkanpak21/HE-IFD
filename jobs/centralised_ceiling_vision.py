#!/usr/bin/env python
"""The pooled ceiling on the vision task, the cell Table I leaves blank.

WHY
---
`jobs/centralised_ceiling.py` measures the pooled reference on the four text
tasks and cannot take a vision task: it is hardcoded to RoBERTa and builds a
TextLoRA over token ids. CIFAR-100's pooled cell was therefore never run, and
Table I carries a dash there. This job fills it.

WHAT IS HELD FIXED
------------------
Everything the text version holds fixed, on the vision pipeline: the same frozen
ViT-B/16, the same rank-8 adapter with its down-projection frozen, the same
head, the same learning rate and batch size, and the same two budgets. The only
change from the federated runs is that the optimiser sees the whole training
pool rather than one Dirichlet shard.

BUDGETS
-------
  matched_per_client   K steps, what one client spends
  matched_total        N*K steps, what the federation spends in aggregate
The second is the pooled reference Table I wants.

TEST SET
--------
`vision_matched.load_vision` draws its test subset with rng.choice, so the
2000-image set is NOT a prefix of the 10000-image set. Table I's CIFAR-100 row
was produced at the default of 2000 and no wrapper overrides it, but rather than
rest the comparison on that, we evaluate every trained model on both and report
both. The training pool is identical across the two loads, because max_train is
the same and the training draw precedes the test draw in the same rng stream.

Usage:  python jobs/centralised_ceiling_vision.py [dataset ...] [seed ...]
"""
import sys
from pathlib import Path

import numpy as np
import torch

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import finetune_improve as fi   # noqa: E402
import vision_matched as vm     # noqa: E402

OUTDIR = REPO / "results" / "centralised_ceiling"
OUTDIR.mkdir(parents=True, exist_ok=True)

DATASETS = ["cifar100"]
SEEDS = [42, 43, 44]
N, K, R = 10, 200, 8
LR, BS = 5e-4, 32
TEST_SIZES = (2000, 10000)


def run(ds, seed, rows):
    print(f"\n=== {ds} seed={seed} ===", flush=True)
    Xtr, ytr, Xte_s, yte_s, C = vm.load_vision(ds, max_test=TEST_SIZES[0], seed=seed)
    Xtr2, ytr2, Xte_f, yte_f, _ = vm.load_vision(ds, max_test=TEST_SIZES[1], seed=seed)
    assert np.array_equal(ytr, ytr2), "training pool differs between the two loads"
    print(f"  train {len(ytr)}, test {len(yte_s)} and {len(yte_f)}, C={C}", flush=True)

    for tag, steps in (("matched_per_client", K), ("matched_total", N * K)):
        fi.set_seed(seed)
        model = vm.ViTLoRA(C, r=R, freeze_a=True).to(fi.DEVICE)
        vm.v_train(model, Xtr, ytr, steps, LR, BS)
        for X, y in ((Xte_s, yte_s), (Xte_f, yte_f)):
            acc = float(vm.v_eval(model, X, y))
            rows.append(dict(task=ds, C=C, seed=seed, mode=tag, steps=steps,
                             n_test=len(y), acc=round(acc, 4)))
            print(f"  >> {tag:<20} steps={steps:<5} n_test={len(y):<6} "
                  f"acc={acc:.4f}", flush=True)
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


def main():
    args = sys.argv[1:]
    tasks = [a for a in args if not a.isdigit()] or DATASETS
    seeds = [int(a) for a in args if a.isdigit()] or SEEDS
    rows = []
    for t in tasks:
        for s in seeds:
            run(t, s, rows)

    cols = ["task", "C", "seed", "mode", "steps", "n_test", "acc"]
    out = OUTDIR / "vision_results.csv"
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

    print("\nper-task mean over seeds, the form Table I needs")
    for t in tasks:
        for tag in ("matched_per_client", "matched_total"):
            for n in TEST_SIZES:
                v = [r["acc"] for r in rows if r["task"] == t and r["mode"] == tag
                     and r["n_test"] == n]
                if v:
                    print(f"  {t:<10} {tag:<20} n_test={n:<6} "
                          f"mean={np.mean(v):.4f} over {len(v)} seeds")


if __name__ == "__main__":
    main()
