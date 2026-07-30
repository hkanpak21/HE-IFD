#!/usr/bin/env python
"""Does the extraction cost really track the size of the shared map?

WHY
---
Section 5.6 measures three label spaces and reports that fidelity 0.90 costs
three to five queries per parameter of the C x d head. If that law holds as C
grows, then the cost for a vocabulary projection follows by arithmetic and needs
no language model. If it does not hold, the generation claim needs its own
measurement.

THE TEST
--------
Spend a budget proportional to the parameter count, q = m * C * d, and vary m.
If the law holds, fidelity depends on m alone and the curves for different C
fall on top of each other. This tests the law directly instead of fitting it.

The head is synthetic. Extraction attacks the map, not the task, so a trained
head is not needed here. Section 5.6 already covers trained heads.

Usage:  python jobs/extraction_scale.py
"""
import sys
from pathlib import Path

import numpy as np
import torch

OUTDIR = Path("results") / "extraction_scale"
OUTDIR.mkdir(parents=True, exist_ok=True)

D = 768
CLASSES = [4, 16, 64, 256]
MULTS = [0.25, 0.5, 1.0, 2.0, 4.0]
N_EVAL = 20000
SEEDS = [42, 43]


def make_head(C, d, rng):
    """A linear map with the row-norm spread a trained head shows."""
    W = rng.normal(0, 1.0 / np.sqrt(d), size=(C, d))
    W *= rng.uniform(0.7, 1.3, size=(C, 1))     # unequal row norms
    b = rng.normal(0, 0.05, size=C)
    return W, b


def fit_linear(X, y, C, steps=300):
    Xt = torch.as_tensor(X, dtype=torch.float32)
    yt = torch.as_tensor(y, dtype=torch.long)
    lin = torch.nn.Linear(Xt.shape[1], C)
    opt = torch.optim.LBFGS(lin.parameters(), lr=0.5, max_iter=steps,
                            history_size=10, line_search_fn="strong_wolfe")
    lossf = torch.nn.CrossEntropyLoss()

    def closure():
        opt.zero_grad()
        loss = lossf(lin(Xt), yt)
        loss.backward()
        return loss

    try:
        opt.step(closure)
    except Exception:                                            # noqa: BLE001
        pass
    return (lin.weight.detach().numpy().astype(np.float64),
            lin.bias.detach().numpy().astype(np.float64))


def run(C, seed, rows):
    rng = np.random.default_rng(seed * 1000 + C)
    W, b = make_head(C, D, rng)
    scale = 1.0 / np.sqrt(D)
    Xe = rng.normal(0, scale, size=(N_EVAL, D))
    ytrue = np.argmax(Xe @ W.T + b, axis=1)
    majority = float(np.bincount(ytrue, minlength=C).max() / len(ytrue))

    for m in MULTS:
        nq = int(m * C * D)
        if nq < 50:
            continue
        X = rng.normal(0, scale, size=(nq, D))
        y = np.argmax(X @ W.T + b, axis=1)
        if len(np.unique(y)) < 2:
            continue
        Wh, bh = fit_linear(X, y, C)
        fid = float((np.argmax(Xe @ Wh.T + bh, axis=1) == ytrue).mean())
        rows.append(dict(C=C, d=D, seed=seed, params=C * D, mult=m,
                         queries=nq, fidelity=round(fid, 4),
                         majority=round(majority, 4)))
        print(f"  C={C:<5} m={m:<5} q={nq:<9} fid={fid:.4f} "
              f"(majority {majority:.3f})", flush=True)
        del X, y


def main():
    rows = []
    for C in CLASSES:
        for s in SEEDS:
            run(C, s, rows)

    cols = ["C", "d", "seed", "params", "mult", "queries", "fidelity", "majority"]
    out = OUTDIR / "results.csv"
    with out.open("w") as f:
        f.write(",".join(cols) + "\n")
        for r in rows:
            f.write(",".join(str(r[c]) for c in cols) + "\n")
    print(f"\nwrote {out} ({len(rows)} rows)\n", flush=True)

    # collapse test: fidelity against m, one column per C
    print("COLLAPSE TEST: fidelity against queries per parameter")
    hdr = "m".ljust(7)
    for C in CLASSES:
        hdr += ("C=" + str(C)).rjust(10)
    print(hdr)
    for m in MULTS:
        line = str(m).ljust(7)
        for C in CLASSES:
            v = [r["fidelity"] for r in rows if r["C"] == C and r["mult"] == m]
            line += (("%.3f" % np.mean(v)) if v else "-").rjust(10)
        print(line)
    print("\nIf the columns agree, cost tracks the parameter count.")


if __name__ == "__main__":
    main()
