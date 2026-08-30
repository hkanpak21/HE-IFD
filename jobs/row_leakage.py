#!/usr/bin/env python
"""What a shared head's row carries about the client that decided it.

WHY
---
The merge is coverage weighted. Row c of the shared head is the n_{j,c}-weighted
average of the row-c displacements of the clients holding class c, so a class
held by one client has a row equal to that client's displacement alone, with no
dilution over the federation. Every measured dilution law in the literature
varies the total client count with uniform contribution, and none of them
applies row-wise, so the question is open and it is ours to answer.

The mechanism that would turn that into a leak is old and exact. For a linear
layer with a bias trained under cross-entropy, the gradient of row c is xi_c
times the feature and the gradient of the bias is xi_c, so their ratio is the
feature itself (Phong et al., IEEE TIFS 2018, observation O1). Accumulated over
a client's local training the ratio becomes a xi-weighted mean over that client's
examples, dominated by its class-c examples but not equal to any one of them.

WHAT THIS MEASURES
------------------
Whether that ratio points anywhere useful, as a function of how many clients
hold the class and how many examples the holder has. Two quantities per class:

  cos_mean   cosine between the recovered ratio and the mean feature of the
             class-c training examples of the clients holding c. High means the
             row identifies what that class looked like to its holders.
  hit_at_1   whether the single nearest training feature under cosine to the
             ratio is an example of class c belonging to a holder. This is the
             record-level question, and a low value is a negative result worth
             reporting: the row would then carry a class direction and not a
             record.

The adversary is assumed to hold the row already, which is the strongest case:
it is what Proposition 2 hands its reduction. Whether extraction from label-only
queries recovers a row to the precision this needs is a separate question that
`jobs/mia_extracted_head.py` bounds.

REPORTED, one row per (task, seed, arrangement, class)
------------------------------------------------------
  holders    clients holding the class, the coverage that decides the row
  n_holder   training examples of that class across its holders
  cos_mean, cos_rand, hit_at_1

`cos_rand` is the same cosine against a random feature direction, so `cos_mean`
can be read against a baseline rather than against zero.

Usage:  python jobs/row_leakage.py [task ...] [seed ...]
"""
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import finetune_improve as fi  # noqa: E402
import personal_adapter_test as pa  # noqa: E402
from extraction_budget import head_of  # noqa: E402
from mia_extracted_head import features_of  # noqa: E402

OUTDIR = Path("results") / "row_leakage"
ARTDIR = Path("results") / "personal_adapter" / "artifacts"
OUTDIR.mkdir(parents=True, exist_ok=True)

TASKS = ["ag_news", "dbpedia_14", "banking77"]
SEEDS = [42, 43, 44]


def cosine(a, B):
    a = a / (np.linalg.norm(a) + 1e-12)
    Bn = B / (np.linalg.norm(B, axis=1, keepdims=True) + 1e-12)
    return Bn @ a


def run(task, seed, rows):
    cands = sorted(ARTDIR.glob(f"{task}_N10_a0.1_K200_s{seed}.pt")) or \
            sorted(ARTDIR.glob(f"{task}_s{seed}.pt"))
    if not cands:
        print(f"  [skip] no artifact for {task} s{seed}", flush=True)
        return
    art = torch.load(cands[0], map_location="cpu", weights_only=False)
    C = int(art["C"])
    N, ALPHA = int(art.get("N", 10)), float(art.get("alpha", 0.1))

    ids_tr, mask_tr, ytr, *_ = fi._data(task, pa.BACKBONE, seed)
    y = np.asarray(ytr)
    parts = pa.usable(fi.dirichlet_partition(y, N, ALPHA, C, seed))
    tr_parts, _ = pa.split_parts(parts, seed, y)
    counts = np.asarray(art["counts"], dtype=np.float64)
    rng = np.random.default_rng(seed)

    for arrangement in ("A", "B"):
        tag = "r0" if arrangement == "A" else "r8"
        r = 0 if arrangement == "A" else pa.R
        fi.set_seed(seed)
        model = fi.TextLoRA(pa.BACKBONE, C, r=r, freeze_a=True).to(fi.DEVICE)
        F = features_of(model, ids_tr, mask_tr)
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        W, b = head_of(art, arrangement)
        theta0 = art[f"theta0_{tag}"]
        hk = [k for k in theta0 if "head" in k]
        wk = [k for k in hk if theta0[k].ndim == 2][0]
        bk = [k for k in hk if theta0[k].ndim == 1][0]
        dW = W - theta0[wk].double().numpy()
        db = b - theta0[bk].double().numpy()

        # which training rows belong to a client that holds class c
        owner = np.full(len(y), -1, dtype=int)
        for j, p in enumerate(tr_parts):
            owner[np.asarray(p)] = j

        for c in range(C):
            holders = np.flatnonzero(counts[:, c] > 0)
            if len(holders) == 0 or abs(db[c]) < 1e-9:
                continue
            mine = np.flatnonzero((y == c) & np.isin(owner, holders))
            if len(mine) < 2:
                continue
            ratio = dW[c] / db[c]
            cm = float(cosine(ratio, F[mine].mean(0, keepdims=True))[0])
            cr = float(np.abs(cosine(ratio, rng.normal(size=(64, F.shape[1])))).mean())
            sims = cosine(ratio, F)
            nn = int(np.argmax(sims))
            hit = int(y[nn] == c and owner[nn] in holders)
            rows.append(dict(task=task, C=C, seed=seed, arrangement=arrangement,
                             cls=c, holders=int(len(holders)),
                             n_holder=int(len(mine)),
                             cos_mean=round(cm, 4), cos_rand=round(cr, 4),
                             hit_at_1=hit))
        got = [r_ for r_ in rows if r_["seed"] == seed and r_["task"] == task
               and r_["arrangement"] == arrangement]
        if got:
            sing = [r_ for r_ in got if r_["holders"] == 1]
            print(f"  {task} s{seed} {arrangement}: {len(got)} classes, "
                  f"{len(sing)} held by one client, "
                  f"mean cos {np.mean([r_['cos_mean'] for r_ in got]):.4f} "
                  f"against baseline {np.mean([r_['cos_rand'] for r_ in got]):.4f}, "
                  f"hit@1 {np.mean([r_['hit_at_1'] for r_ in got]):.3f}", flush=True)


def main():
    args = sys.argv[1:]
    tasks = [a for a in args if not a.isdigit()] or TASKS
    seeds = [int(a) for a in args if a.isdigit()] or SEEDS
    rows = []
    for t in tasks:
        for s in seeds:
            run(t, s, rows)
    if not rows:
        raise SystemExit("no rows produced")

    cols = ["task", "C", "seed", "arrangement", "cls", "holders", "n_holder",
            "cos_mean", "cos_rand", "hit_at_1"]
    out = OUTDIR / "results.csv"
    with out.open("w") as f:
        f.write(",".join(cols) + "\n")
        for r in rows:
            f.write(",".join(str(r[c]) for c in cols) + "\n")
    print(f"\nwrote {out} ({len(rows)} rows)\n", flush=True)
    print(",".join(cols))
    for r in rows:
        print(",".join(str(r[c]) for c in cols))


if __name__ == "__main__":
    main()
