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
  sel_globalprior  GLOBAL-prior estimator A pools evidence, B's unseen classes -> 0
  sel_gp_rarefill  same, unseen filled from the client's <=2-example classes

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
STRAT_PER_CLASS = 1   # holdout examples reserved from EVERY class a client holds
RARE_Q = 2            # 'rare' = <=q TRAINING examples (absolute, not relative)
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


def split_parts(parts, seed, y=None):
    """Coverage-STRATIFIED holdout carve.

    A uniform 10% carve almost never lands a class with 1-2 training examples in
    the holdout, so the client can never measure how it does on classes it barely
    knows -- which is the only local proxy for classes it has never seen, and the
    exact quantity that decides A vs B.

    So: reserve >=STRAT_PER_CLASS example from EVERY class the client holds, then
    top up to VAL_FRAC at random. A client holding a single example of class c
    donates it, so its adapter never trains on c -- precisely the
    leave-one-class-out probe the selector needs, at negligible training cost.
    """
    rng = np.random.default_rng(seed + 7)
    tr, va = [], []
    for idx in parts:
        idx = np.asarray(idx)
        keep = np.zeros(len(idx), dtype=bool)
        if y is not None:
            lab = np.asarray(y)[idx]
            for c in np.unique(lab):
                pos = np.where(lab == c)[0]
                keep[rng.choice(pos, min(STRAT_PER_CLASS, len(pos)),
                                replace=False)] = True
        deficit = max(1, int(round(VAL_FRAC * len(idx)))) - int(keep.sum())
        if deficit > 0:
            rest = np.where(~keep)[0]
            if len(rest):
                keep[rng.choice(rest, min(deficit, len(rest)), replace=False)] = True
        if (~keep).sum() == 0:          # degenerate: keep at least something to train on
            keep[rng.choice(np.where(keep)[0], 1, replace=False)] = False
        va.append(idx[keep])
        tr.append(idx[~keep])
    return tr, va


def global_prior(counts):
    """p(c) over the federation, from the already-disclosed count matrix."""
    tot = np.asarray(counts).sum(0).astype(float)
    return tot / max(tot.sum(), 1e-12)


def per_class_nk(logits, y, C):
    """(#holdout examples, #correct) per class -- the only thing a client reports."""
    p = logits.argmax(1).numpy()
    y = np.asarray(y)
    n = np.array([(y == c).sum() for c in range(C)], dtype=float)
    k = np.array([((y == c) & (p == c)).sum() for c in range(C)], dtype=float)
    return n, k


def rare_fill(train_counts_j, n, k, q=RARE_Q):
    """Accuracy on classes with <=q TRAINING examples: the local stand-in for
    'classes I have never seen'. Rarity must be ABSOLUTE, not relative -- at C=4
    a client's relatively-rarest class still has hundreds of examples."""
    rare = (np.asarray(train_counts_j) <= q) & (n > 0)
    return float(k[rare].sum() / max(n[rare].sum(), 1.0)) if rare.any() else 0.0


def estimate(pg, nk_list, w, counts, pooled, fill="zero"):
    """Expected accuracy on a GLOBAL-prior example.

    pooled=True (A): one shared model, so per-class evidence combines across
    clients and every class is covered by someone.
    pooled=False (B): N models; client j only has evidence for its own classes,
    and the rest take a fill. fill='zero' makes the estimate a LOWER BOUND.
    """
    if pooled:
        n = sum(nk[0] for nk in nk_list)
        k = sum(nk[1] for nk in nk_list)
        acc = np.where(n > 0, k / np.maximum(n, 1.0), 0.0)
        return float(np.dot(pg, acc))
    per = []
    for j, (n, k) in enumerate(nk_list):
        f = 0.0 if fill == "zero" else rare_fill(counts[j], n, k)
        acc = np.where(n > 0, k / np.maximum(n, 1.0), f)
        per.append(float(np.dot(pg, acc)))
    return float(np.dot(w, per))


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
    tr_parts, va_parts = split_parts(parts, seed, ytr)

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

    B_test, B_val, B_bal, val_y = [], [], [], []
    art["logits_B_test"], art["logits_B_val"] = [], []
    for j, st in enumerate(states):
        fi.load_trainable(model, {k: (agg[k] if is_head(k) else st[k]) for k in st})
        lt = logits_of(model, Xte)
        vX, vy = val_of(j)
        lv = logits_of(model, vX)
        art["logits_B_test"].append(lt); art["logits_B_val"].append(lv)
        val_y.append(vy)
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

    pg = global_prior(counts)
    nkA = [per_class_nk(art["logits_A_val"][j], val_y[j], C) for j in range(len(parts))]
    nkB = [per_class_nk(art["logits_B_val"][j], val_y[j], C) for j in range(len(parts))]
    eA = estimate(pg, nkA, w, counts, pooled=True)
    for tag, fill in (("sel_globalprior", "zero"), ("sel_gp_rarefill", "rare")):
        eB = estimate(pg, nkB, w, counts, pooled=False, fill=fill)
        pick_B = eB >= eA
        out = B_test if pick_B else [A_test] * len(parts)
        record(rows, ds, C, seed, tag, out,
               f"picked {'B' if pick_B else 'A'} (E_B={eB:.4f} E_A={eA:.4f}; "
               f"true B={np.mean(B_test):.4f} A={A_test:.4f})")
    art.update(pg=pg, E_A=eA,
               E_B_zero=estimate(pg, nkB, w, counts, pooled=False, fill="zero"),
               E_B_rare=estimate(pg, nkB, w, counts, pooled=False, fill="rare"),
               nkA=np.array(nkA), nkB=np.array(nkB),
               val_y=[np.asarray(v) for v in val_y])
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
