#!/usr/bin/env python
"""Experiment B: personal adapter + federated encrypted head.

WHY
---
Serve needs the client to run its backbone in PLAINTEXT, which forbids a
*shared* internal adapter (its aggregate would have to be decrypted, and an
(N-1) coalition could then subtract its own contributions and recover the last
honest client's displacement exactly).

The way out: never aggregate the adapter at all.

  * each client trains its OWN adapter locally and never shares it
    -> no adapter aggregate exists -> nothing to subtract -> collusion-safe
  * only the HEAD is federated, aggregated under HE, and kept encrypted
  * at query time the client runs its own backbone+adapter in plaintext,
    sends phi_j(x) and fc(phi_j(x)) encrypted, server applies the encrypted
    head -> argmax. Depth 1-2. Exactly the intended protocol.

Rationale: the adapter improves the REPRESENTATION, which a client can do alone
for free. The HEAD is where coverage bites (a client cannot classify classes it
never saw), so that is the part that actually needs federating.

RISK BEING TESTED
-----------------
Each client's features drift apart, so a shared head may not transfer. All
clients start from the same theta0 and take only K bounded steps, which is the
paper's own "shared frame" argument -- but it is an assumption, not a fact.

MODES (all evaluated on the GLOBAL test set)
--------------------------------------------
  local        adapter_j + head_j          what client j gets alone
  B_personal   adapter_j + agg_head        <-- the proposed design
  current      agg_adapter + agg_head      current HE-OFT (not servable)
  A_headonly   no adapter + agg_head       floor: clients train r=0, head only

Usage:  python -m jobs.personal_adapter_test [task ...]
"""
import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import finetune_improve as fi  # noqa: E402

OUTDIR = Path("results") / "personal_adapter"
OUTDIR.mkdir(parents=True, exist_ok=True)

TASKS = ["ag_news", "dbpedia_14", "banking77"]
BACKBONE = "roberta_base"
N, ALPHA, SEED, K, LR, BS, R = 10, 0.1, 42, 200, 5e-4, 32, 8
HEAD_KEYS = ("head.weight", "head.bias")


def is_head(k):
    return k in HEAD_KEYS


def train_clients(model, theta0, parts, ids_tr, mask_tr, ytr, C):
    """Each client runs its own bounded trajectory from the shared theta0."""
    states, ws, counts = [], [], []
    y = np.asarray(ytr)
    for j, idx in enumerate(parts):
        idx = torch.as_tensor(np.asarray(idx), dtype=torch.long)
        fi.load_trainable(model, theta0)
        fi.train_steps(model, ids_tr[idx], mask_tr[idx], y[idx.numpy()], K, LR, BS)
        states.append(fi.trainable_state(model))
        ws.append(len(idx))
        counts.append(np.bincount(y[idx.numpy()], minlength=C))
        print(f"  client {j+1}/{len(parts)} done", flush=True)
    ws = np.asarray(ws, dtype=float)
    return states, ws / ws.sum(), counts


def record(rows, task, C, mode, accs, note=""):
    a = np.asarray(accs, dtype=float)
    rows.append(dict(task=task, C=C, mode=mode, n=len(a),
                     acc_mean=round(a.mean(), 4), acc_min=round(a.min(), 4),
                     acc_max=round(a.max(), 4), note=note))
    print(f"  >> {mode:<12} mean={a.mean():.4f} "
          f"[{a.min():.4f}, {a.max():.4f}]  n={len(a)}", flush=True)


def run_task(task, rows):
    print(f"\n=== {task} ===", flush=True)
    ids_tr, mask_tr, ytr, ids_te, mask_te, yte, C = fi._data(task, BACKBONE, SEED)
    parts = fi.dirichlet_partition(ytr, N, ALPHA, C, SEED)

    # ---------- pass 1: r=8, clients train their own adapter + head ----------
    fi.set_seed(SEED)
    model = fi.TextLoRA(BACKBONE, C, r=R, freeze_a=True).to(fi.DEVICE)
    theta0 = fi.trainable_state(model)
    states, w, counts = train_clients(model, theta0, parts, ids_tr, mask_tr, ytr, C)

    deltas = [{k: s[k] - theta0[k] for k in s} for s in states]
    agg = fi.agg_count_head(theta0, deltas, w, counts)   # current HE-OFT

    # current HE-OFT: everything aggregated (not servable, reference only)
    fi.load_trainable(model, agg)
    record(rows, task, C, "current", [fi.evaluate(model, ids_te, mask_te, yte)],
           "agg adapter + agg head")

    # local: client j alone
    accs = []
    for s in states:
        fi.load_trainable(model, s)
        accs.append(fi.evaluate(model, ids_te, mask_te, yte))
    record(rows, task, C, "local", accs, "own adapter + own head")

    # B: client j's own adapter + the federated head
    accs = []
    for s in states:
        mixed = {k: (agg[k] if is_head(k) else s[k]) for k in s}
        fi.load_trainable(model, mixed)
        accs.append(fi.evaluate(model, ids_te, mask_te, yte))
    record(rows, task, C, "B_personal", accs, "own adapter + agg head")

    # adapter switched off, federated head kept (head trained WITH an adapter)
    accs = []
    mixed = {k: (agg[k] if is_head(k) else theta0[k]) for k in theta0}
    fi.load_trainable(model, mixed)
    record(rows, task, C, "no_adapter", [fi.evaluate(model, ids_te, mask_te, yte)],
           "theta0 adapter + agg head")

    del model, states, deltas
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # ---------- pass 2: r=0 floor — clients train a head only ----------
    fi.set_seed(SEED)
    m0 = fi.TextLoRA(BACKBONE, C, r=0, freeze_a=True).to(fi.DEVICE)
    t0 = fi.trainable_state(m0)
    s0, w0, c0 = train_clients(m0, t0, parts, ids_tr, mask_tr, ytr, C)
    d0 = [{k: s[k] - t0[k] for k in s} for s in s0]
    fi.load_trainable(m0, fi.agg_count_head(t0, d0, w0, c0))
    record(rows, task, C, "A_headonly", [fi.evaluate(m0, ids_te, mask_te, yte)],
           "r=0, head only, federated")
    del m0, s0, d0
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def main():
    rows = []
    for t in (sys.argv[1:] or TASKS):
        try:
            run_task(t, rows)
        except Exception as e:
            print(f"[FAIL] {t}: {type(e).__name__}: {e}", flush=True)
        (OUTDIR / "personal_adapter.json").write_text(json.dumps(rows, indent=2))

    cols = ["task", "C", "mode", "n", "acc_mean", "acc_min", "acc_max", "note"]
    print("\n" + ",".join(cols))
    for r in rows:
        print(",".join(str(r[c]) for c in cols))


if __name__ == "__main__":
    main()
