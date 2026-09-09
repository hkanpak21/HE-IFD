#!/usr/bin/env python
"""How many head rows a federation actually covers.

WHY
---
The shared head collapses to $0.206$ on Banking77 while a client alone reaches
$0.249$, and the paper attributes that to coverage: with 77 classes each row is
decided by few clients or none. The claim is stated and never counted. This
counts it.

Row $c$ of the shared head is the coverage-weighted average of the row-$c$
displacements of the clients holding class $c$. A class no client holds keeps
the public initializer, which is a random row, so it still competes in the
argmax. A class one client holds takes that client's displacement with no
dilution.

WHAT IT REPORTS, one line per (task, seed)
------------------------------------------
  holders_0   classes no usable client holds
  holders_1   classes exactly one usable client holds
  holders_2   classes exactly two hold
  holders_3p  classes three or more hold
  n_clients   usable clients after the minimum-size rule

No GPU and no model. It loads labels, replays the same Dirichlet partition the
runs used, and counts. The partition is deterministic in (labels, N, alpha, C,
seed), so these are the partitions the accuracy numbers were measured on.

Usage:  python jobs/coverage_histogram.py [task ...] [seed ...]
"""
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import finetune_improve as fi        # noqa: E402
import personal_adapter_test as pa   # noqa: E402

OUTDIR = REPO / "results" / "coverage"
OUTDIR.mkdir(parents=True, exist_ok=True)

TASKS = ["ag_news", "trec", "dbpedia_14", "banking77"]
SEEDS = [42, 43, 44]
N, ALPHA = 10, 0.1


def run(task, seed, rows):
    *_, ytr = fi._data(task, pa.BACKBONE, seed)[:3]
    y = np.asarray(ytr)
    C = int(y.max()) + 1
    parts = pa.usable(fi.dirichlet_partition(y, N, ALPHA, C, seed))
    holders = np.zeros(C, dtype=int)
    for p_ in parts:
        holders += (np.bincount(y[np.asarray(p_)], minlength=C) > 0).astype(int)
    r = dict(task=task, C=C, seed=seed, n_clients=len(parts),
             holders_0=int((holders == 0).sum()),
             holders_1=int((holders == 1).sum()),
             holders_2=int((holders == 2).sum()),
             holders_3p=int((holders >= 3).sum()))
    rows.append(r)
    print(f"  {task} s{seed}: {len(parts)} clients, {C} classes. "
          f"0 holders {r['holders_0']}, 1 holder {r['holders_1']}, "
          f"2 holders {r['holders_2']}, 3+ {r['holders_3p']}", flush=True)


def main():
    args = sys.argv[1:]
    tasks = [a for a in args if not a.isdigit()] or TASKS
    seeds = [int(a) for a in args if a.isdigit()] or SEEDS
    rows = []
    for t in tasks:
        for s in seeds:
            run(t, s, rows)
    cols = ["task", "C", "seed", "n_clients", "holders_0", "holders_1",
            "holders_2", "holders_3p"]
    out = OUTDIR / "results.csv"
    with out.open("w") as f:
        f.write(",".join(cols) + "\n")
        for r in rows:
            f.write(",".join(str(r[c]) for c in cols) + "\n")
    print(f"\nwrote {out}\n", flush=True)
    print(",".join(cols))
    for r in rows:
        print(",".join(str(r[c]) for c in cols))
    print("\nmean over seeds")
    for t in tasks:
        v = [r for r in rows if r["task"] == t]
        if v:
            print(f"  {t:<12} C={v[0]['C']:<4} "
                  f"0 holders {np.mean([r['holders_0'] for r in v]):.1f}, "
                  f"1 holder {np.mean([r['holders_1'] for r in v]):.1f}, "
                  f"2 holders {np.mean([r['holders_2'] for r in v]):.1f}")


if __name__ == "__main__":
    main()
