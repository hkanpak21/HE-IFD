#!/usr/bin/env python
"""Experiment B, vision arm: personal adapter + federated encrypted head.

Same protocol as jobs/personal_adapter_test.py, on a frozen ViT-B/16:

  * each client trains its OWN LoRA adapter locally and never shares it
    -> no adapter aggregate exists -> nothing for an (N-1) coalition to subtract
  * only the HEAD is federated, merged under HE, and kept encrypted
  * at query time the client runs its own backbone+adapter in plaintext and
    sends Enc(phi_j(x)); the server applies the encrypted head and the
    encrypted argmax, and only the label is threshold-decrypted

MODES (all evaluated on the GLOBAL test set)
  current      agg adapter + agg head     current HE-OFT (NOT servable)
  local        adapter_j + head_j         client alone
  B_personal   adapter_j + agg head       <-- the proposed design
  A_headonly   r=0, head only, federated  the floor
  selected     per-client vote A vs B     each client picks on its own holdout

Usage:  python jobs/personal_adapter_vision.py [dataset ...] [seed ...]
"""
import json
import sys
from pathlib import Path

import numpy as np
import torch

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import finetune_improve as fi           # noqa: E402
import vision_matched as vm             # noqa: E402

OUTDIR = REPO / "results" / "personal_adapter_vision"
OUTDIR.mkdir(parents=True, exist_ok=True)

DATASETS = ["cifar100"]
N, ALPHA, K, LR, BS, R = 10, 0.1, 200, 5e-4, 32, 8
SEEDS = [42, 43, 44]
VAL_FRAC = 0.1
HEAD_KEYS = ("head.weight", "head.bias")


def is_head(k):
    return k in HEAD_KEYS


def split_parts(parts, seed):
    rng = np.random.default_rng(seed + 7)
    tr, va = [], []
    for idx in parts:
        idx = np.asarray(idx)
        perm = rng.permutation(len(idx))
        nv = max(1, int(round(VAL_FRAC * len(idx))))
        va.append(idx[perm[:nv]])
        tr.append(idx[perm[nv:]] if len(idx) - nv > 0 else idx[perm[:nv]])
    return tr, va


def train_clients(model, theta0, parts, X, y, C):
    states, ws, counts = [], [], []
    for j, idx in enumerate(parts):
        idx = np.asarray(idx)
        fi.load_trainable(model, theta0)
        vm.v_train(model, X[idx], y[idx], K, LR, BS)
        states.append(fi.trainable_state(model))
        ws.append(len(idx))
        counts.append(np.bincount(y[idx], minlength=C))
        print(f"  client {j+1}/{len(parts)} done", flush=True)
    ws = np.asarray(ws, dtype=float)
    return states, ws / ws.sum(), counts


def record(rows, ds, C, seed, mode, accs, note=""):
    a = np.asarray(accs, dtype=float)
    rows.append(dict(dataset=ds, C=C, seed=seed, mode=mode, n=len(a),
                     acc_mean=round(a.mean(), 4), acc_min=round(a.min(), 4),
                     acc_max=round(a.max(), 4), note=note))
    print(f"  >> {mode:<12} mean={a.mean():.4f} "
          f"[{a.min():.4f}, {a.max():.4f}]  n={len(a)}  {note}", flush=True)


def run_ds(ds, seed, rows):
    print(f"\n=== {ds} seed={seed} ===", flush=True)
    Xtr, ytr, Xte, yte, C = vm.load_vision(ds, seed=seed)
    parts = fi.dirichlet_partition(ytr, N, ALPHA, C, seed)
    tr_parts, va_parts = split_parts(parts, seed)

    def on_val(model, j):
        v = np.asarray(va_parts[j])
        return vm.v_eval(model, Xtr[v], ytr[v])

    # ---------- pass 1: r=8, each client trains its OWN adapter + head -------
    fi.set_seed(seed)
    model = vm.ViTLoRA(C, r=R, freeze_a=True).to(fi.DEVICE)
    theta0 = fi.trainable_state(model)
    states, w, counts = train_clients(model, theta0, tr_parts, Xtr, ytr, C)

    deltas = [{k: s[k] - theta0[k] for k in s} for s in states]
    agg = fi.agg_count_head(theta0, deltas, w, counts)

    fi.load_trainable(model, agg)                       # reference only
    record(rows, ds, C, seed, "current", [vm.v_eval(model, Xte, yte)],
           "agg adapter + agg head")

    accs = []
    for s in states:
        fi.load_trainable(model, s)
        accs.append(vm.v_eval(model, Xte, yte))
    record(rows, ds, C, seed, "local", accs, "own adapter + own head")

    B_test, B_val = [], []
    for j, s in enumerate(states):
        fi.load_trainable(model, {k: (agg[k] if is_head(k) else s[k]) for k in s})
        B_test.append(vm.v_eval(model, Xte, yte))
        B_val.append(on_val(model, j))
    record(rows, ds, C, seed, "B_personal", B_test, "own adapter + agg head")

    del model, states, deltas
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # ---------- pass 2: r=0 floor -------------------------------------------
    fi.set_seed(seed)
    m0 = vm.ViTLoRA(C, r=0, freeze_a=True).to(fi.DEVICE)
    t0 = fi.trainable_state(m0)
    s0, w0, c0 = train_clients(m0, t0, tr_parts, Xtr, ytr, C)
    d0 = [{k: s[k] - t0[k] for k in s} for s in s0]
    fi.load_trainable(m0, fi.agg_count_head(t0, d0, w0, c0))
    A_test = vm.v_eval(m0, Xte, yte)
    A_val = [on_val(m0, j) for j in range(len(parts))]
    record(rows, ds, C, seed, "A_headonly", [A_test], "r=0, head only, federated")

    sel = [B_test[j] if B_val[j] >= A_val[j] else A_test for j in range(len(parts))]
    n_B = sum(1 for j in range(len(parts)) if B_val[j] >= A_val[j])
    record(rows, ds, C, seed, "selected", sel,
           f"client vote, {n_B}/{len(parts)} chose B")

    del m0, s0, d0
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def main():
    args = sys.argv[1:]
    dss = [a for a in args if not a.isdigit()] or DATASETS
    seeds = [int(a) for a in args if a.isdigit()] or SEEDS
    rows = []
    for ds in dss:
        for sd in seeds:
            try:
                run_ds(ds, sd, rows)
            except Exception as e:
                print(f"[FAIL] {ds} s{sd}: {type(e).__name__}: {e}", flush=True)
            (OUTDIR / f"personal_adapter_{'_'.join(dss)}.json").write_text(
                json.dumps(rows, indent=2))

    cols = ["dataset", "C", "seed", "mode", "n", "acc_mean", "acc_min",
            "acc_max", "note"]
    print("\n" + ",".join(cols))
    for r in rows:
        print(",".join(str(r[c]) for c in cols))


if __name__ == "__main__":
    main()
