#!/usr/bin/env python
"""One-shot label-only membership inference, against the serving interface.

WHY
---
`jobs/mia_extracted_head.py` shows that a coalition which extracts a copy of the
head and attacks it learns nothing, and that a coalition simply handed the head
in plaintext learns nothing either. Both attacks read a statistic off a model.

OSLO (Peng et al., 2024) does not. It crafts one query per candidate so that the
label alone separates members from non-members, and it is the strongest
label-only attack at a low false-positive rate that we found in the literature,
reporting 6.7 per cent true positives at 0.1 per cent false positives on
CIFAR-100 where the best previous label-only attack reports 0.3 per cent.

Our serving interface is unusually exposed to it. The client encrypts its own
feature vector and uploads that, so a coalition may submit ANY point in R^768
rather than only vectors the backbone can produce from a real input. OSLO
elsewhere must craft an input and push it through a fixed feature map; here the
crafted point goes in directly. And it costs one query per candidate rather than
the thousands a boundary-distance attack needs, so it is the most efficient use
of a query allowance that exists.

THE ADVERSARY
-------------
A coalition holding some of the clients. It has their data, their adapters, the
public backbone, and label-only answers. It does not have the head.

THE ATTACK
----------
1. Train surrogate heads on the coalition's own data alone. This is what the
   coalition can build without any query.
2. For a candidate (x, y), take the direction that most reduces the margin of
   class y on the surrogates, which for a linear head is the difference between
   the row of y and the row of its nearest competitor.
3. Choose one step size on the coalition's OWN data, where it knows for each
   surrogate which examples that surrogate trained on. Pick the step that best
   separates held-in survival from held-out survival. Calibrating on the
   candidates instead would need the answer the attack is looking for.
4. Submit ONE query at the perturbed point. Predict member if the label is
   still y.

A member sits further from the boundary than a non-member if and only if the
head fitted it more tightly, so the single label carries the membership signal
the attack needs, and nothing else leaves the protocol.

REPORTED
--------
  tpr_at_0.1pct, tpr_at_1pct, auc, and the queries spent, which is one per
  candidate by construction.

Usage:  python jobs/oslo_serving.py [task ...] [seed ...]
Env:    OSLO_SURROGATES (default 32), OSLO_NCAND (default 1000),
        OSLO_COALITION (clients the coalition holds, default 3)
"""
import os
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import finetune_improve as fi  # noqa: E402
import personal_adapter_test as pa  # noqa: E402
from extraction_budget import head_of  # noqa: E402
from mia_extracted_head import (features_of, roc_points, train_head)  # noqa: E402

OUTDIR = Path("results") / "oslo_serving"
ARTDIR = Path("results") / "personal_adapter" / "artifacts"
OUTDIR.mkdir(parents=True, exist_ok=True)

TASKS = ["ag_news", "dbpedia_14", "banking77"]
SEEDS = [42, 43, 44]
SURR = int(os.environ.get("OSLO_SURROGATES", 32))
N_CAND = int(os.environ.get("OSLO_NCAND", 1000))
COALITION = int(os.environ.get("OSLO_COALITION", 3))
STEPS = np.linspace(0.0, 6.0, 25)


def margin_direction(W, y):
    """For a linear head, the direction that most reduces class y's margin.

    The boundary between y and a competitor c is where (w_y - w_c) . z + (b_y -
    b_c) is zero, so moving against w_y - w_c is the shortest way out of y's
    cell. Averaging over surrogates gives the coalition's best guess at it
    without ever seeing the served head.
    """
    d = W[y][None, :] - W                     # (C, dim)
    n = np.linalg.norm(d, axis=1)
    n[y] = np.inf
    c = int(np.argmin(n))                     # nearest competitor
    v = d[c]
    return v / (np.linalg.norm(v) + 1e-12), c


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
    tr_parts, va_parts = pa.split_parts(parts, seed, y)
    n_cl = len(parts)
    if n_cl <= COALITION + 1:
        print(f"  [skip] {task} s{seed}: {n_cl} clients, too few to split",
              flush=True)
        return
    coal = list(range(COALITION))
    honest = list(range(COALITION, n_cl))

    # candidates come from the honest clients only: that is what the coalition
    # does not hold and Proposition 2 is about
    members = np.concatenate([np.asarray(tr_parts[j]) for j in honest])
    nonmembers = np.concatenate([np.asarray(va_parts[j]) for j in honest])
    n = min(len(members), len(nonmembers), N_CAND)
    if n < 50:
        print(f"  [skip] {task} s{seed}: only {n} candidates", flush=True)
        return
    rng = np.random.default_rng(seed)
    members = rng.choice(members, n, replace=False)
    nonmembers = rng.choice(nonmembers, n, replace=False)
    cand = np.concatenate([members, nonmembers])
    label = np.concatenate([np.ones(n, bool), np.zeros(n, bool)])
    print(f"  {task} s{seed}: coalition holds {len(coal)} of {n_cl} clients, "
          f"{n} members and {n} non-members from the other {len(honest)}",
          flush=True)

    for arrangement in ("A", "B"):
        tag = "r0" if arrangement == "A" else "r8"
        r = 0 if arrangement == "A" else pa.R
        fi.set_seed(seed)
        model = fi.TextLoRA(pa.BACKBONE, C, r=r, freeze_a=True).to(fi.DEVICE)
        if arrangement == "B":
            fi.load_trainable(model, art[f"states_{tag}"][coal[0]])
        F = features_of(model, ids_tr, mask_tr)
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        W, b = head_of(art, arrangement)                 # the served head
        theta0 = art[f"theta0_{tag}"]
        hk = [k for k in theta0 if "head" in k]
        wk = [k for k in hk if theta0[k].ndim == 2][0]
        bk = [k for k in hk if theta0[k].ndim == 1][0]
        t0W = theta0[wk].double().numpy()
        t0b = theta0[bk].double().numpy()

        # step 1: surrogates from the coalition's own data, no queries spent
        srng = np.random.default_rng(seed * 31 + 5)
        pool = np.concatenate([np.concatenate([np.asarray(tr_parts[j]),
                                               np.asarray(va_parts[j])])
                               for j in coal])
        surr, surr_in = [], []
        for _ in range(SURR):
            idx = srng.choice(pool, max(32, len(pool) // 2), replace=False)
            surr.append(train_head(F[idx], y[idx], C, t0W, t0b))
            surr_in.append(np.isin(pool, idx))
        surr_in = np.array(surr_in)                     # (SURR, len(pool))
        print(f"    {task} s{seed} {arrangement}: {SURR} surrogates from "
              f"{len(pool)} coalition examples", flush=True)

        # step 2 and 3: one direction and one step size per candidate, chosen
        # on the surrogates alone
        Fc, yc = F[cand], y[cand]
        dirs = np.zeros_like(Fc)
        for i in range(len(cand)):
            v = np.zeros(Fc.shape[1])
            for Ws, _ in surr:
                d, _ = margin_direction(Ws, int(yc[i]))
                v += d
            dirs[i] = v / (np.linalg.norm(v) + 1e-12)

        # the step size is common and the coalition calibrates it on its own
        # data, where it knows for every surrogate which examples that surrogate
        # trained on. Calibrating on the candidates would need the answer the
        # attack is trying to find.
        cal = srng.choice(len(pool), min(600, len(pool)), replace=False)
        Fcal, ycal, incal = F[pool[cal]], y[pool[cal]], surr_in[:, cal]
        dcal = np.zeros_like(Fcal)
        for i in range(len(cal)):
            v = np.zeros(Fcal.shape[1])
            for Ws, _ in surr:
                d, _ = margin_direction(Ws, int(ycal[i]))
                v += d
            dcal[i] = v / (np.linalg.norm(v) + 1e-12)
        best_t, best_sep = STEPS[1], -np.inf
        for t in STEPS[1:]:
            surv = np.array([((Fcal + t * dcal) @ Ws.T + bsv).argmax(1) == ycal
                             for Ws, bsv in surr])          # (SURR, len(cal))
            num_in = (surv & incal).sum(); den_in = incal.sum()
            num_out = (surv & ~incal).sum(); den_out = (~incal).sum()
            if den_in == 0 or den_out == 0:
                continue
            sep = float(num_in / den_in - num_out / den_out)
            if sep > best_sep:
                best_sep, best_t = sep, t
        if not np.isfinite(best_sep):
            print(f"  [skip] {task} s{seed} {arrangement}: no calibration signal",
                  flush=True)
            continue

        # step 4: ONE query per candidate against the served head
        z = (Fc + best_t * dirs) @ W.T + b
        still = (np.argmax(z, axis=1) == yc).astype(np.float64)
        # break ties with the surrogate-averaged survival, which costs no query
        aux = np.mean([((Fc + best_t * dirs) @ Ws.T + bsv).argmax(1) == yc
                       for Ws, bsv in surr], axis=0)
        score = still + 1e-3 * aux
        t1, t2, auc = roc_points(score, label)
        rows.append(dict(task=task, C=C, seed=seed, arrangement=arrangement,
                         coalition=len(coal), surrogates=SURR,
                         n_candidates=int(len(cand)), queries=int(len(cand)),
                         step=round(float(best_t), 3),
                         surrogate_sep=round(float(best_sep), 4),
                         tpr_at_0_1pct=round(t1, 5), tpr_at_1pct=round(t2, 5),
                         auc=round(auc, 4)))
        print(f"  {task} s{seed} {arrangement} OSLO step={best_t:.2f} "
              f"(surrogate separation {best_sep:+.4f}) "
              f"TPR@0.1%={t1:.4f} TPR@1%={t2:.4f} AUC={auc:.4f}", flush=True)


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
    cols = ["task", "C", "seed", "arrangement", "coalition", "surrogates",
            "n_candidates", "queries", "step", "surrogate_sep",
            "tpr_at_0_1pct", "tpr_at_1pct", "auc"]
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
