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
  sel_perclient    per-client vote        BIASED (local holdout follows local skew)
  sel_federated    federation-wide vote   one winner for all, sample-weighted
  sel_fed_balanced federation-wide vote   + per-class balanced holdout scoring

Also writes results/personal_adapter_vision/artifacts/<ds>_s<seed>.pt with
theta0, per-client states (r=8/r=0), counts, weights, holdout indices, and the
LOGITS of every candidate on the global test set and each client's holdout, so
blind/HE selection rules can be developed offline with no GPU.

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
ARTDIR = OUTDIR / "artifacts"
OUTDIR.mkdir(parents=True, exist_ok=True)
ARTDIR.mkdir(parents=True, exist_ok=True)

DATASETS = ["cifar100"]
N, ALPHA, K, LR, BS, R = 10, 0.1, 200, 5e-4, 32, 8
SEEDS = [42, 43, 44]
VAL_FRAC = 0.1
HEAD_KEYS = ("head.weight", "head.bias")


def is_head(k):
    return k in HEAD_KEYS


MIN_SHARD = 20        # a client needs enough data to split into train + holdout


def usable(parts):
    """Drop clients whose Dirichlet shard is too small to train on.

    At small alpha on a small dataset the partition can hand a client zero (or
    a handful of) samples, which crashes the sampler. Such a client cannot
    meaningfully participate anyway, so we drop it and report the effective N
    rather than silently reshaping the partition.
    """
    keep = [p for p in parts if len(p) >= MIN_SHARD]
    if len(keep) != len(parts):
        print(f"  [partition] dropped {len(parts) - len(keep)}/{len(parts)} "
              f"clients with <{MIN_SHARD} samples -> effective N={len(keep)}",
              flush=True)
    return keep


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


@torch.no_grad()
def logits_of(model, X, bs=64):
    model.eval()
    out = []
    for s in range(0, len(X), bs):
        out.append(model(vm.prep(X[s:s + bs])).float().cpu())
    return torch.cat(out)


def acc_of(logits, y):
    return float((logits.argmax(1).numpy() == np.asarray(y)).mean())


def balanced_acc_of(logits, y, C):
    """Per-class accuracy averaged over classes present; removes the local prior."""
    p = logits.argmax(1).numpy(); y = np.asarray(y)
    per = [(p[y == c] == c).mean() for c in range(C) if (y == c).sum() > 0]
    return float(np.mean(per)) if per else 0.0


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
    parts = usable(fi.dirichlet_partition(ytr, N, ALPHA, C, seed))
    tr_parts, va_parts = split_parts(parts, seed)

    def val_of(j):
        v = np.asarray(va_parts[j])
        return Xtr[v], ytr[v]

    art = dict(dataset=ds, seed=seed, C=C, N=N, alpha=ALPHA, K=K, r=R,
               va_parts=[np.asarray(v) for v in va_parts], yte=np.asarray(yte))

    # ---------- pass 1: r=8, each client trains its OWN adapter + head -------
    fi.set_seed(seed)
    model = vm.ViTLoRA(C, r=R, freeze_a=True).to(fi.DEVICE)
    theta0 = fi.trainable_state(model)
    states, w, counts = train_clients(model, theta0, tr_parts, Xtr, ytr, C)

    deltas = [{k: s[k] - theta0[k] for k in s} for s in states]
    agg = fi.agg_count_head(theta0, deltas, w, counts)
    art.update(theta0_r8={k: v.cpu() for k, v in theta0.items()},
               states_r8=[{k: v.cpu() for k, v in st.items()} for st in states],
               w=w, counts=np.stack(counts))

    fi.load_trainable(model, agg)                       # reference only
    art["logits_current_test"] = logits_of(model, Xte)
    record(rows, ds, C, seed, "current",
           [acc_of(art["logits_current_test"], yte)], "agg adapter + agg head")

    accs = []
    for st in states:
        fi.load_trainable(model, st)
        accs.append(vm.v_eval(model, Xte, yte))
    record(rows, ds, C, seed, "local", accs, "own adapter + own head")

    B_test, B_val, B_bal = [], [], []
    art["logits_B_test"], art["logits_B_val"] = [], []
    for j, st in enumerate(states):
        fi.load_trainable(model, {k: (agg[k] if is_head(k) else st[k]) for k in st})
        lt = logits_of(model, Xte)
        vX, vy = val_of(j)
        lv = logits_of(model, vX)
        art["logits_B_test"].append(lt); art["logits_B_val"].append(lv)
        B_test.append(acc_of(lt, yte))
        B_val.append(acc_of(lv, vy))
        B_bal.append(balanced_acc_of(lv, vy, C))
    record(rows, ds, C, seed, "B_personal", B_test, "own adapter + agg head")

    del model, states, deltas
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # ---------- pass 2: r=0 floor -------------------------------------------
    fi.set_seed(seed)
    m0 = vm.ViTLoRA(C, r=0, freeze_a=True).to(fi.DEVICE)
    t0 = fi.trainable_state(m0)
    s0, w0, c0 = train_clients(m0, t0, tr_parts, Xtr, ytr, C)
    d0 = [{k: st[k] - t0[k] for k in st} for st in s0]
    fi.load_trainable(m0, fi.agg_count_head(t0, d0, w0, c0))
    art.update(theta0_r0={k: v.cpu() for k, v in t0.items()},
               states_r0=[{k: v.cpu() for k, v in st.items()} for st in s0])

    art["logits_A_test"] = logits_of(m0, Xte)
    A_test = acc_of(art["logits_A_test"], yte)
    A_val, A_bal, art["logits_A_val"] = [], [], []
    for j in range(len(parts)):
        vX, vy = val_of(j)
        lv = logits_of(m0, vX)
        art["logits_A_val"].append(lv)
        A_val.append(acc_of(lv, vy))
        A_bal.append(balanced_acc_of(lv, vy, C))
    record(rows, ds, C, seed, "A_headonly", [A_test], "r=0, head only, federated")

    # ---------- selection variants ------------------------------------------
    sel = [B_test[j] if B_val[j] >= A_val[j] else A_test for j in range(len(parts))]
    n_B = sum(1 for j in range(len(parts)) if B_val[j] >= A_val[j])
    record(rows, ds, C, seed, "sel_perclient", sel,
           f"per-client vote (biased), {n_B}/{len(parts)} chose B")

    for tag, vB, vA in (("sel_federated", B_val, A_val),
                        ("sel_fed_balanced", B_bal, A_bal)):
        sB = float(np.dot(w, vB)); sA = float(np.dot(w, vA))
        pick_B = sB >= sA
        out = B_test if pick_B else [A_test] * len(parts)
        record(rows, ds, C, seed, tag, out,
               f"federation picked {'B' if pick_B else 'A'} (B={sB:.4f} A={sA:.4f})")

    art.update(B_test=B_test, B_val=B_val, B_bal=B_bal,
               A_test=A_test, A_val=A_val, A_bal=A_bal)
    ap = ARTDIR / f"{ds}_s{seed}.pt"
    torch.save(art, ap)
    print(f"  artifacts -> {ap} ({ap.stat().st_size/1e6:.1f} MB)", flush=True)

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
