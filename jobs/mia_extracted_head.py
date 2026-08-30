#!/usr/bin/env python
"""How much membership signal survives extraction of the served head.

WHY
---
Proposition 2 of the security section caps what a client coalition learns about
an honest client at delta_wb, the advantage of an adversary handed the shared
head in plaintext. The cap has never been measured, so it is a symbol with no
number, and it is the only such quantity in that section.

The coalition cannot read the head. It is a ciphertext throughout, and reading it
would mean breaking IND-CPA. What the coalition can do is extract a copy from
label-only answers, which results/extraction_budget already measures, and then
attack the copy. That two-stage chain is what this job measures end to end.

The literature does not report it. Jagielski et al. (NeurIPS 2023) measure
membership inference against a soft-label distilled student, which is the closest
published result; every other work that claims extracted models leak membership
either reads the victim's own confidence vector, or reports balanced accuracy,
which Carlini et al. (S&P 2022) argue is not a meaningful metric.

THE ADVERSARY
-------------
A coalition of clients. It holds the public backbone, its own clients' data and
adapters, and a query allowance. It receives one label per query and nothing
else. It never sees a score, a logit or a confidence.

WHAT IT ATTACKS
---------------
Whether a given example was in an honest client's training set.

SURFACES, in increasing weakness
--------------------------------
  truehead    the attacker is handed the head in plaintext and reads real
              logits. This is delta_wb itself and it is the ceiling: by the
              data-processing inequality no attack on a copy can beat it.
  extracted   the attacker holds a copy fitted from Q label-only queries.
              Swept over Q. This is what the protocol actually admits.
  gap         predict member iff the head classifies the example correctly.
              Free, no queries, no shadow models. The floor any attack must
              beat to be worth reporting (Choquette-Choo et al., ICML 2021,
              report the gap attack reaching 83.5 of the 89.2 the best
              label-only attack achieves on CIFAR-100).

METHOD
------
LiRA (Carlini et al., IEEE S&P 2022). For each candidate example the attacker
fits Gaussians to its statistic over shadow federations that did and did not
train on it, and thresholds the likelihood ratio. Shadow federations are cheap
here because the backbone is frozen and public: a shadow is N clients each
taking K gradient steps on cached 768-dimensional features, then the
coverage-weighted merge. No backbone forward pass is repeated.

Members are the clients' training examples and non-members their own held-out
examples, so both sides come from the same clients' data and the test measures
membership rather than distribution shift. The holdout is stratified by class and
is small per client, so the default pools every client; MIA_TARGET restricts it
to one.

REPORTED
--------
  tpr_at_0.1pct, tpr_at_1pct   the convention Carlini et al. require
  auc                          for completeness only, per their Table I caption

Usage:  python jobs/mia_extracted_head.py [task ...] [seed ...]
Env:    MIA_SHADOWS (default 64), MIA_NCAND (default 1000),
        MIA_TARGET (client index; the default -1 pools every client)
"""
import os
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import finetune_improve as fi  # noqa: E402
import personal_adapter_test as pa  # noqa: E402
from extraction_budget import Oracle, fit_linear, head_of, query_random  # noqa: E402

OUTDIR = Path("results") / "mia_extracted"
ARTDIR = Path("results") / "personal_adapter" / "artifacts"
OUTDIR.mkdir(parents=True, exist_ok=True)

TASKS = ["ag_news", "dbpedia_14", "banking77"]
SEEDS = [42, 43, 44]
BUDGETS = [2000, 20000, 200000]
SHADOWS = int(os.environ.get("MIA_SHADOWS", 64))
TARGET = int(os.environ.get("MIA_TARGET", -1))   # -1 pools every client
N_CAND = int(os.environ.get("MIA_NCAND", 1000))
K_STEPS, LR = 200, 5e-4


# ---------------------------------------------------------------- features ---
def features_of(model, ids, mask, bs=64):
    """phi(x) for every row: the backbone output the head consumes.

    For the r=0 model this is the bare public backbone. For the r=8 model the
    adapter is inside the backbone, so this is client j's own feature map.
    """
    model.eval()
    out = []
    with torch.no_grad():
        for s in range(0, len(ids), bs):
            i = ids[s:s + bs].to(fi.DEVICE)
            m = mask[s:s + bs].to(fi.DEVICE)
            h = model.backbone(input_ids=i, attention_mask=m).last_hidden_state
            out.append(fi.mean_pool(h, m).float().cpu())
    return torch.cat(out).numpy().astype(np.float64)


# ------------------------------------------------------------- the shadows ---
def train_head(F, y, C, theta0_W, theta0_b, steps=K_STEPS, lr=LR):
    """One client's local head training, on cached features."""
    W = torch.as_tensor(theta0_W, dtype=torch.float32).clone().requires_grad_(True)
    b = torch.as_tensor(theta0_b, dtype=torch.float32).clone().requires_grad_(True)
    Xt = torch.as_tensor(F, dtype=torch.float32)
    yt = torch.as_tensor(y, dtype=torch.long)
    opt = torch.optim.AdamW([W, b], lr=lr)
    lossf = torch.nn.CrossEntropyLoss()
    n = len(Xt)
    g = torch.Generator().manual_seed(0)
    for _ in range(steps):
        idx = torch.randint(0, n, (min(32, n),), generator=g)
        opt.zero_grad()
        lossf(Xt[idx] @ W.T + b, yt[idx]).backward()
        opt.step()
    return W.detach().numpy().astype(np.float64), b.detach().numpy().astype(np.float64)


def merge(theta0_W, theta0_b, heads, counts):
    """The coverage-weighted merge of eq. (1): clients holding a class decide it."""
    counts = np.asarray(counts, dtype=np.float64)
    den = np.where(counts.sum(0) > 0, counts.sum(0), 1.0)
    numW = np.zeros_like(theta0_W)
    numb = np.zeros_like(theta0_b)
    for j, (Wj, bj) in enumerate(heads):
        numW += counts[j][:, None] * (Wj - theta0_W)
        numb += counts[j] * (bj - theta0_b)
    return theta0_W + numW / den[:, None], theta0_b + numb / den


def shadow_federation(F, y, pools, C, theta0_W, theta0_b, rng):
    """One shadow: every client trains on a random half of its own pool.

    The pool is that client's training AND held-out examples together. Sampling
    from the training split alone would leave every non-member OUT of every
    shadow, so its IN distribution would be empty and LiRA would have nothing to
    compare against. Randomising over the whole pool is what makes a candidate a
    member in about half the shadows, which is the condition the attack needs.
    """
    heads, counts, inmask = [], [], np.zeros(len(y), dtype=bool)
    for p in pools:
        take = rng.random(len(p)) < 0.5
        idx = p[take]
        if len(idx) < 4:
            idx = p[:max(4, len(p) // 2)]
        inmask[idx] = True
        heads.append(train_head(F[idx], y[idx], C, theta0_W, theta0_b))
        counts.append(np.bincount(y[idx], minlength=C).astype(np.float64))
    W, b = merge(theta0_W, theta0_b, heads, counts)
    return W, b, inmask


# -------------------------------------------------------------- statistics ---
def logit_stat(W, b, F, y):
    """Carlini's rescaled logit: log p_y - log(1 - p_y), stable form."""
    z = F @ W.T + b
    z = z - z.max(1, keepdims=True)
    e = np.exp(z)
    p = e / e.sum(1, keepdims=True)
    py = np.clip(p[np.arange(len(y)), y], 1e-12, 1 - 1e-12)
    return np.log(py) - np.log1p(-py)


def roc_points(score, label):
    """TPR at 0.1 and 1 per cent FPR, plus AUC. Higher score means member."""
    o = np.argsort(-score)
    lab = label[o]
    tp = np.cumsum(lab)
    fp = np.cumsum(~lab)
    P, N = lab.sum(), (~lab).sum()
    if P == 0 or N == 0:
        return 0.0, 0.0, 0.5
    tpr, fpr = tp / P, fp / N
    def at(t):
        k = np.searchsorted(fpr, t, side="right") - 1
        return float(tpr[k]) if k >= 0 else 0.0
    auc = float(np.trapz(tpr, fpr))
    return at(0.001), at(0.01), auc


def lira(stat_target, stat_in, stat_out):
    """Offline-and-online LiRA: Gaussian likelihood ratio per example."""
    mu_i, sd_i = stat_in.mean(0), stat_in.std(0) + 1e-6
    mu_o, sd_o = stat_out.mean(0), stat_out.std(0) + 1e-6
    ll_i = -0.5 * ((stat_target - mu_i) / sd_i) ** 2 - np.log(sd_i)
    ll_o = -0.5 * ((stat_target - mu_o) / sd_o) ** 2 - np.log(sd_o)
    return ll_i - ll_o


# --------------------------------------------------------------------- run ---
def run(task, seed, rows):
    cands = sorted(ARTDIR.glob(f"{task}_N10_a0.1_K200_s{seed}.pt")) or \
            sorted(ARTDIR.glob(f"{task}_s{seed}.pt"))
    if not cands:
        print(f"  [skip] no artifact for {task} s{seed}", flush=True)
        return
    art = torch.load(cands[0], map_location="cpu", weights_only=False)
    C = int(art["C"])
    N, ALPHA = int(art.get("N", 10)), float(art.get("alpha", 0.1))

    ids_tr, mask_tr, ytr, ids_te, mask_te, yte, C2 = fi._data(task, pa.BACKBONE, seed)
    assert C2 == C, (C2, C)
    y = np.asarray(ytr)
    parts = pa.usable(fi.dirichlet_partition(y, N, ALPHA, C, seed))
    tr_parts, va_parts = pa.split_parts(parts, seed, y)
    # TARGET < 0 pools every client, which is the quantity Proposition 2 caps:
    # what a coalition learns about the training set it does not hold. A single
    # client's stratified holdout is a handful of examples, too few for a
    # low-false-positive-rate measurement.
    if TARGET < 0:
        members = np.concatenate([np.asarray(p) for p in tr_parts])
        nonmembers = np.concatenate([np.asarray(p) for p in va_parts])
    else:
        if TARGET >= len(parts):
            print(f"  [skip] {task} s{seed}: target {TARGET} beyond {len(parts)}",
                  flush=True)
            return
        members = np.asarray(tr_parts[TARGET])
        nonmembers = np.asarray(va_parts[TARGET])
    n = min(len(members), len(nonmembers), N_CAND)
    if n < 50:
        print(f"  [skip] {task} s{seed}: only {n} usable candidates "
              f"({len(members)} members, {len(nonmembers)} non-members)", flush=True)
        return
    # the shadow world randomises membership over each client's whole pool
    pools = [np.concatenate([np.asarray(a), np.asarray(v)])
             for a, v in zip(tr_parts, va_parts)]
    rng = np.random.default_rng(seed)
    members = rng.choice(members, n, replace=False)
    nonmembers = rng.choice(nonmembers, n, replace=False)
    cand = np.concatenate([members, nonmembers])
    label = np.concatenate([np.ones(n, bool), np.zeros(n, bool)])
    print(f"  {task} s{seed}: {n} members and {n} non-members over "
          f"{len(parts)} clients", flush=True)

    for arrangement in ("A", "B"):
        tag = "r0" if arrangement == "A" else "r8"
        r = 0 if arrangement == "A" else pa.R
        fi.set_seed(seed)
        model = fi.TextLoRA(pa.BACKBONE, C, r=r, freeze_a=True).to(fi.DEVICE)
        if arrangement == "B":
            fi.load_trainable(model, art[f"states_{tag}"][TARGET])
        F_cand = features_of(model, ids_tr[cand], mask_tr[cand])
        F_all = features_of(model, ids_tr, mask_tr)
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        W, b = head_of(art, arrangement)
        d = W.shape[1]
        theta0 = art[f"theta0_{tag}"]
        hk = [k for k in theta0 if "head" in k]
        wk = [k for k in hk if theta0[k].ndim == 2][0]
        bk = [k for k in hk if theta0[k].ndim == 1][0]
        t0W = theta0[wk].double().numpy()
        t0b = theta0[bk].double().numpy()

        # shadow federations, recording IN/OUT per candidate
        srng = np.random.default_rng(seed * 1000 + 7)
        s_in = [[] for _ in range(len(cand))]
        s_out = [[] for _ in range(len(cand))]
        for s in range(SHADOWS):
            Ws, bs_, inmask = shadow_federation(F_all, y, pools, C, t0W, t0b, srng)
            st = logit_stat(Ws, bs_, F_cand, y[cand])
            for i, c in enumerate(cand):
                (s_in if inmask[c] else s_out)[i].append(st[i])
            if (s + 1) % 16 == 0:
                print(f"    {task} s{seed} {arrangement}: {s+1}/{SHADOWS} shadows",
                      flush=True)
        keep = np.array([len(a) >= 2 and len(o) >= 2
                         for a, o in zip(s_in, s_out)])
        if keep.sum() < 20:
            print(f"  [skip] {task} s{seed} {arrangement}: "
                  f"only {keep.sum()} candidates with both sides", flush=True)
            continue
        SI = np.array([np.mean(a) for a in s_in])
        SO = np.array([np.mean(o) for o in s_out])
        SIs = np.array([np.std(a) + 1e-6 for a in s_in])
        SOs = np.array([np.std(o) + 1e-6 for o in s_out])

        def report(surface, queries, Wa, ba):
            st = logit_stat(Wa, ba, F_cand, y[cand])
            sc = (-0.5 * ((st - SI) / SIs) ** 2 - np.log(SIs)) - \
                 (-0.5 * ((st - SO) / SOs) ** 2 - np.log(SOs))
            t1, t2, auc = roc_points(sc[keep], label[keep])
            rows.append(dict(task=task, C=C, d=d, seed=seed, target=TARGET,
                             arrangement=arrangement, surface=surface,
                             queries=queries, shadows=SHADOWS,
                             n_candidates=int(keep.sum()),
                             tpr_at_0_1pct=round(t1, 5),
                             tpr_at_1pct=round(t2, 5), auc=round(auc, 4)))
            print(f"  {task} s{seed} {arrangement} {surface:<14} q={queries:<7} "
                  f"TPR@0.1%={t1:.4f} TPR@1%={t2:.4f} AUC={auc:.4f}", flush=True)

        report("truehead", 0, W, b)

        scale = 1.0 / np.sqrt(d)
        for nq in BUDGETS:
            orc = Oracle(W, b)
            X, yq = query_random(orc, nq, d, rng, scale)
            if len(np.unique(yq)) < 2:
                continue
            Wh, bh = fit_linear(X, yq, C)
            report("extracted", int(orc.n), Wh, bh)

        # the free baseline: member iff the served head is right
        pred = np.argmax(F_cand @ W.T + b, axis=1)
        sc = (pred == y[cand]).astype(np.float64)
        t1, t2, auc = roc_points(sc[keep], label[keep])
        rows.append(dict(task=task, C=C, d=d, seed=seed, target=TARGET,
                         arrangement=arrangement, surface="gap", queries=1,
                         shadows=0, n_candidates=int(keep.sum()),
                         tpr_at_0_1pct=round(t1, 5), tpr_at_1pct=round(t2, 5),
                         auc=round(auc, 4)))
        print(f"  {task} s{seed} {arrangement} {'gap':<14} q=1       "
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

    cols = ["task", "C", "d", "seed", "target", "arrangement", "surface",
            "queries", "shadows", "n_candidates", "tpr_at_0_1pct",
            "tpr_at_1pct", "auc"]
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
