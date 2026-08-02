#!/usr/bin/env python
"""How many label-only queries buy a functional copy of the served head.

WHY
---
The threat model bounds what a querying client learns by a per-client query
allowance Q, and says Q must sit below the extraction cost of the deployment's
label space. That sentence is empty until the extraction cost is measured.

THE ADVERSARY
-------------
A participating client, which is the strongest label-only adversary the
protocol admits: it computes query features itself, so it may submit an
ARBITRARY vector in feature space rather than only real inputs. It receives one
label per query and nothing else.

WHAT IT ATTACKS
---------------
The served head is linear in the features, y = argmax_c (W phi + b)_c, so
extraction is the problem of learning a linear classifier from membership
queries.

THE ATTACK
----------
Fit a multinomial linear model to the (query, label) pairs by convex
optimisation. This is deliberately the straightforward attack rather than a
clever one. An earlier version of this experiment used per-boundary bisection
and reported far lower fidelity, but that attack is broken: with more than two
classes the segment between two points can cross a third class's region, so the
collected points do not lie on a single hyperplane, and each hyperplane is
recovered only up to an independent scale, which the argmax does not preserve.
Reporting its numbers would have overstated the protocol's security. Fitting a
model to labelled queries has neither defect.

Two query strategies are measured, because they bracket the adversary:
  random     points drawn from the feature distribution; the cheap attack
  boundary   half the budget spent bisecting toward the current estimate's
             decision boundary, where labels are most informative; the
             stronger attack, and the one a bound should be set against

REPORTED
--------
  fidelity   agreement with the served model on held-out feature vectors
  majority   the share of the largest class, so fidelity can be read against
             the trivial baseline rather than against zero
Plus two reference points: logit access, which needs no search and recovers the
head by linear solve in d+1 queries, and the disclosed model, exact at zero.

Usage:  python jobs/extraction_budget.py [task ...] [seed ...]
"""
import sys
from pathlib import Path

import numpy as np
import torch

OUTDIR = Path("results") / "extraction_budget"
ARTDIR = Path("results") / "personal_adapter" / "artifacts"
OUTDIR.mkdir(parents=True, exist_ok=True)

BUDGETS = [200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000]
N_EVAL = 20000
BISECT = 12          # halvings per boundary probe under the 'boundary' strategy
SEEDS = [42, 43, 44]
TASKS = ["ag_news", "dbpedia_14", "banking77"]


def head_of(art, arrangement):
    """Rebuild the served head (W, b): the coverage-weighted combination of eq. (1)."""
    tag = "r0" if arrangement == "A" else "r8"
    theta0, states = art[f"theta0_{tag}"], art[f"states_{tag}"]
    counts = np.asarray(art["counts"], dtype=np.float64)

    hk = [k for k in theta0 if "head" in k or "classifier" in k or "score" in k]
    wk = [k for k in hk if theta0[k].ndim == 2]
    bk = [k for k in hk if theta0[k].ndim == 1]
    if not wk:
        raise SystemExit(f"no head weight among {list(theta0)}")
    wk, bk = wk[0], (bk[0] if bk else None)

    den = torch.as_tensor(np.where(counts.sum(0) > 0, counts.sum(0), 1.0))
    W = theta0[wk].double().clone()
    num = torch.zeros_like(W)
    for j, s in enumerate(states):
        g = torch.as_tensor(counts[j], dtype=torch.float64).unsqueeze(1)
        num += g * (s[wk].double() - theta0[wk].double())
    W = W + num / den.unsqueeze(1)

    if bk is None:
        b = torch.zeros(W.shape[0], dtype=torch.float64)
    else:
        b = theta0[bk].double().clone()
        nb = torch.zeros_like(b)
        for j, s in enumerate(states):
            nb += torch.as_tensor(counts[j], dtype=torch.float64) * \
                  (s[bk].double() - theta0[bk].double())
        b = b + nb / den
    return W.numpy(), b.numpy()


class Oracle:
    """The served model: returns a label, nothing else, and counts queries."""

    def __init__(self, W, b):
        self.W, self.b, self.n = W, b, 0

    def __call__(self, X):
        X = np.atleast_2d(X)
        self.n += len(X)
        return np.argmax(X @ self.W.T + self.b, axis=1)


def fit_linear(X, y, C, steps=400, lr=0.5):
    """Multinomial logistic regression, the adversary's surrogate."""
    Xt = torch.as_tensor(X, dtype=torch.float32)
    yt = torch.as_tensor(y, dtype=torch.long)
    lin = torch.nn.Linear(Xt.shape[1], C)
    opt = torch.optim.LBFGS(lin.parameters(), lr=lr, max_iter=steps,
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


def query_random(orc, n, d, rng, scale):
    X = rng.normal(0, scale, size=(n, d))
    return X, orc(X)


def query_boundary(orc, n, d, rng, scale, C):
    """Half the budget on random probes, half bisecting toward the boundary.

    Points close to a decision boundary carry the most information about a
    linear model, so this is the stronger attack of the two.
    """
    half = max(2, n // 2)
    X0, y0 = query_random(orc, half, d, rng, scale)
    Xs, ys = [X0], [y0]

    spent, budget = 0, n - half
    order = rng.permutation(len(X0))
    i = 0
    while spent < budget and i + 1 < len(order):
        a, bnd = X0[order[i]], None
        ya = int(y0[order[i]])
        for j in range(i + 1, min(i + 40, len(order))):
            if int(y0[order[j]]) != ya:
                bnd = X0[order[j]]
                break
        i += 1
        if bnd is None:
            continue
        xa, xb = a.copy(), bnd.copy()
        for _ in range(min(BISECT, budget - spent)):
            xm = 0.5 * (xa + xb)
            ym = int(orc(xm)[0])          # one query, used both to steer and to keep
            spent += 1
            if ym == ya:
                xa = xm
            else:
                xb = xm
            Xs.append(xm[None, :])
            ys.append(np.array([ym]))
            if spent >= budget:
                break
    return np.vstack(Xs), np.concatenate(ys)


def run(task, seed, rows):
    cands = sorted(ARTDIR.glob(f"{task}_N10_a0.1_K200_s{seed}.pt")) or \
            sorted(ARTDIR.glob(f"{task}_s{seed}.pt"))
    if not cands:
        print(f"  [skip] no artifact for {task} s{seed}", flush=True)
        return
    art = torch.load(cands[0], map_location="cpu", weights_only=False)
    C = int(art["C"])
    rng = np.random.default_rng(seed)

    for arrangement in ("A", "B"):
        try:
            W, b = head_of(art, arrangement)
        except Exception as e:                                   # noqa: BLE001
            print(f"  [skip] {task} s{seed} {arrangement}: {e}", flush=True)
            continue
        d = W.shape[1]
        scale = 1.0 / np.sqrt(d)
        Xe = rng.normal(0, scale, size=(N_EVAL, d))
        ytrue = np.argmax(Xe @ W.T + b, axis=1)
        majority = float(np.bincount(ytrue, minlength=C).max() / len(ytrue))

        for access, q in (("disclosed", 0), ("logits", d + 1)):
            rows.append(dict(task=task, C=C, d=d, seed=seed,
                             arrangement=arrangement, strategy=access,
                             queries=q, fidelity=1.0, majority=round(majority, 4)))

        for strategy in ("random", "boundary"):
            for nq in BUDGETS:
                orc = Oracle(W, b)
                if strategy == "random":
                    X, y = query_random(orc, nq, d, rng, scale)
                else:
                    X, y = query_boundary(orc, nq, d, rng, scale, C)
                if len(np.unique(y)) < 2:
                    continue
                Wh, bh = fit_linear(X, y, C)
                fid = float((np.argmax(Xe @ Wh.T + bh, axis=1) == ytrue).mean())
                rows.append(dict(task=task, C=C, d=d, seed=seed,
                                 arrangement=arrangement, strategy=strategy,
                                 queries=int(orc.n), fidelity=round(fid, 4),
                                 majority=round(majority, 4)))
                print(f"  {task} s{seed} {arrangement} {strategy:<8} "
                      f"q={orc.n:<7} fid={fid:.4f} (majority {majority:.3f})",
                      flush=True)


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

    cols = ["task", "C", "d", "seed", "arrangement", "strategy", "queries",
            "fidelity", "majority"]
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
