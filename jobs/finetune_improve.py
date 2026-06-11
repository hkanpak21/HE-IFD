#!/usr/bin/env python
"""Improvement program for the one-shot federated fine-tuning method (2026-06-10).

Implements the levers locked in the grilling session, all HE-legal (server stays
a depth-1 linear combiner; everything else is client-side pre-encryption or
post-decryption among clients, which our threat model permits):

  * freeze_a   — FFA-LoRA: A is frozen at the shared public init, only B (+head)
                 is trained. Makes Σ wⱼ·Bⱼ·A₀ = Σ wⱼ·ΔWⱼ EXACT task arithmetic
                 (both-A-B is bilinear and breaks the linearity claim).
  * sem_init   — semantic head init: head row c = centered+normalized embedding
                 of class c's NAME under the same frozen backbone. Public (no
                 client data), gives unseen-class rows a zero-shot starting
                 point — targets the coverage gap (banking77).
  * Fisher / count-head aggregation at depth 1 via the num/denom trick: clients
                 send Enc(Fⱼ⊙Δⱼ) and Enc(Fⱼ); server adds both (CT+CT only);
                 clients decrypt two aggregates and divide elementwise.
                 count_head is the special case Fⱼ = local class counts on the
                 head rows (plain wⱼ elsewhere).
  * λ grid + client-vote selection: server emits several depth-1 candidates;
                 every client scores each on a local 10% holdout; sample-weighted
                 vote picks the released model. Post-decryption, client-side.
  * swa / prox_mu / calib_tau — client-side trajectory smoothing (SWA over the
                 second half of the local trajectory), FedProx proximal pull to
                 θ₀, and FedLC-style logit calibration by the local log-prior.

Self-contained (no src/ import), per-cell JSON resumable, one --stage per
invocation. The Colab notebook builder (notebooks/build_improve_nb.py) embeds
everything above the CLI marker verbatim, so job and notebook cannot drift.
"""
import argparse
import json
import random
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
from peft import LoraConfig, get_peft_model
from datasets import load_dataset

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
CASE = "finetune_improve"
OUTDIR = Path("results") / CASE
OUTDIR.mkdir(parents=True, exist_ok=True)


def set_seed(s):
    random.seed(s); np.random.seed(s); torch.manual_seed(s)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(s)


TEXT_TASKS = {
    "ag_news":    dict(hf="fancyzhx/ag_news",    text="text",    label="label",        C=4),
    "dbpedia_14": dict(hf="fancyzhx/dbpedia_14", text="content", label="label",        C=14),
    "trec":       dict(hf="CogComp/trec",        text="text",    label="coarse_label", C=6),
    "banking77":  dict(hf="PolyAI/banking77",    text="text",    label="label",        C=77),
}
# Readable class names for the semantic head init. Taken from the HF label
# feature when its names are real words; overridden where they are codes.
LABEL_NAME_OVERRIDES = {
    "trec": ["abbreviation", "entity", "description and abstract concept",
             "human being", "location", "numeric value"],
    "ag_news": ["world news", "sports", "business", "science and technology"],
}
BACKBONES = {
    "roberta_base": dict(hf="roberta-base", targets=["query", "value"]),
    "mpnet_st":     dict(hf="sentence-transformers/all-mpnet-base-v2", targets=["q", "v"]),
}
VIT = "google/vit-base-patch16-224-in21k"
VIT_TARGETS = ["query", "value"]


def _load_any(hf_id):
    last = None
    for kw in ({}, {"revision": "refs/convert/parquet"}):
        try:
            return load_dataset(hf_id, **kw)
        except Exception as e:  # noqa: BLE001
            last = e
    raise last


def class_names(task):
    """Human-readable class-name strings for the semantic head init (public)."""
    if task in LABEL_NAME_OVERRIDES:
        return LABEL_NAME_OVERRIDES[task]
    cfg = TEXT_TASKS[task]
    feat = _load_any(cfg["hf"])["train"].features[cfg["label"]]
    return [n.replace("_", " ") for n in feat.names]


def load_text(task, max_train=20000, max_test=5000, seed=0):
    cfg = TEXT_TASKS[task]
    ds = _load_any(cfg["hf"])
    rng = np.random.default_rng(seed)
    def take(split, n):
        n = min(n, len(split))
        idx = rng.choice(len(split), n, replace=False)
        sub = split.select(idx.tolist())
        return list(sub[cfg["text"]]), np.array(sub[cfg["label"]], dtype=np.int64)
    Xtr, ytr = take(ds["train"], max_train)
    Xte, yte = take(ds["test"], max_test)
    return Xtr, ytr, Xte, yte, cfg["C"]


_TOK_CACHE = {}
def tokenize(backbone, texts, max_len=128):
    tok = _TOK_CACHE.setdefault("tok:" + backbone,
                                AutoTokenizer.from_pretrained(BACKBONES[backbone]["hf"]))
    enc = tok(texts, padding="max_length", truncation=True,
              max_length=max_len, return_tensors="pt")
    return enc["input_ids"], enc["attention_mask"]


def mean_pool(last_hidden, mask):
    m = mask.unsqueeze(-1).float()
    return (last_hidden * m).sum(1) / m.sum(1).clamp_min(1e-6)


class TextLoRA(nn.Module):
    def __init__(self, backbone, C, r=8, freeze_a=False, head_init=None):
        super().__init__()
        base = AutoModel.from_pretrained(BACKBONES[backbone]["hf"])
        hidden = base.config.hidden_size
        for p in base.parameters():
            p.requires_grad = False
        if r > 0:
            lcfg = LoraConfig(r=r, lora_alpha=2 * r, lora_dropout=0.0, bias="none",
                              target_modules=BACKBONES[backbone]["targets"])
            base = get_peft_model(base, lcfg)
            if freeze_a:
                # FFA-LoRA: A stays at its (seed-keyed, public) random init.
                for n, p in base.named_parameters():
                    if "lora_A" in n:
                        p.requires_grad = False
        self.backbone = base
        self.head = nn.Linear(hidden, C)
        if head_init is not None:
            with torch.no_grad():
                self.head.weight.copy_(head_init)
                self.head.bias.zero_()
    def forward(self, ids, mask):
        out = self.backbone(input_ids=ids, attention_mask=mask).last_hidden_state
        return self.head(mean_pool(out, mask))


@torch.no_grad()
def semantic_head_init(backbone, task):
    """Head rows from class-NAME embeddings under the same frozen backbone.

    Public by construction (label names only, no client data). Rows are
    centered across classes then L2-normalized, so θ₀'s head encodes class
    semantics at a uniform scale; the zero-init LoRA keeps the backbone output
    identical to the bare pretrained model at step 0.
    """
    names = class_names(task)
    base = AutoModel.from_pretrained(BACKBONES[backbone]["hf"]).to(DEVICE).eval()
    ids, mask = tokenize(backbone, names, max_len=16)
    out = base(input_ids=ids.to(DEVICE), attention_mask=mask.to(DEVICE)).last_hidden_state
    e = mean_pool(out, mask.to(DEVICE)).cpu()
    del base
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    e = e - e.mean(0, keepdim=True)
    return e / e.norm(dim=1, keepdim=True).clamp_min(1e-6)


def trainable_state(model):
    return {n: p.detach().clone() for n, p in model.named_parameters() if p.requires_grad}

def load_trainable(model, state):
    with torch.no_grad():
        for n, p in model.named_parameters():
            if n in state:
                p.copy_(state[n].to(p.device))

def n_trainable(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def train_steps(model, ids, mask, y, steps, lr, bs, theta0=None,
                prox_mu=0.0, calib_logp=None, swa=False):
    """Bounded local trajectory with the client-side levers.

    prox_mu    — FedProx pull (μ/2)·‖θ−θ₀‖² over the trainable unit.
    calib_logp — FedLC-style: train on logits + log(local prior); removes the
                 local-prior bias from the decision boundary. Eval is untouched.
    swa        — average trainable params over the 2nd half of the trajectory
                 (every 10 steps); the averaged point is loaded back at the end.
    """
    model.train()
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=lr)
    n = len(y); yt = torch.as_tensor(y, device=DEVICE)
    g = torch.Generator().manual_seed(0)
    if calib_logp is not None:
        calib_logp = calib_logp.to(DEVICE)
    swa_acc, swa_n = None, 0
    steps = max(1, steps)
    for k in range(steps):
        idx = torch.randint(0, n, (min(bs, n),), generator=g)
        lo = model(ids[idx].to(DEVICE), mask[idx].to(DEVICE))
        if calib_logp is not None:
            lo = lo + calib_logp
        loss = F.cross_entropy(lo, yt[idx])
        if prox_mu > 0 and theta0 is not None:
            reg = sum(((p - theta0[nme].to(p.device)) ** 2).sum()
                      for nme, p in model.named_parameters() if nme in theta0)
            loss = loss + 0.5 * prox_mu * reg
        opt.zero_grad(); loss.backward(); opt.step()
        if swa and k >= steps // 2 and (k - steps // 2) % 10 == 0:
            st = trainable_state(model)
            if swa_acc is None:
                swa_acc = st
            else:
                for kk in swa_acc:
                    swa_acc[kk] += st[kk]
            swa_n += 1
    if swa and swa_acc is not None:
        load_trainable(model, {k: v / swa_n for k, v in swa_acc.items()})
    return model


@torch.no_grad()
def evaluate(model, ids, mask, y, bs=256):
    model.eval()
    n = len(y); yt = torch.as_tensor(y); correct = 0
    for s in range(0, n, bs):
        lo = model(ids[s:s + bs].to(DEVICE), mask[s:s + bs].to(DEVICE))
        correct += (lo.argmax(1).cpu() == yt[s:s + bs]).sum().item()
    return correct / max(n, 1)


def diag_fisher(model, ids, mask, y, bs, batches=8):
    """Client-side diagonal Fisher of the trainable unit at the end of the
    trajectory (mean squared gradient over a few local batches), normalized to
    mean 1 per client so scale differences don't dominate the merge."""
    model.train()
    n = len(y); yt = torch.as_tensor(y, device=DEVICE)
    g = torch.Generator().manual_seed(1)
    fis = {nme: torch.zeros_like(p) for nme, p in model.named_parameters() if p.requires_grad}
    for _ in range(batches):
        idx = torch.randint(0, n, (min(bs, n),), generator=g)
        lo = model(ids[idx].to(DEVICE), mask[idx].to(DEVICE))
        loss = F.cross_entropy(lo, yt[idx])
        model.zero_grad(); loss.backward()
        for nme, p in model.named_parameters():
            if p.requires_grad and p.grad is not None:
                fis[nme] += p.grad.detach() ** 2
    model.zero_grad()
    tot = sum(f.sum().item() for f in fis.values())
    cnt = sum(f.numel() for f in fis.values())
    scale = tot / max(cnt, 1)
    return {k: v / max(scale, 1e-12) for k, v in fis.items()}


def dirichlet_partition(y, N, alpha, C, seed):
    rng = np.random.default_rng(seed)
    client = [[] for _ in range(N)]
    for c in range(C):
        idx = np.where(y == c)[0]; rng.shuffle(idx)
        if len(idx) == 0:
            continue
        props = rng.dirichlet([alpha] * N)
        cuts = (np.cumsum(props) * len(idx)).astype(int)[:-1]
        for i, part in enumerate(np.split(idx, cuts)):
            client[i].extend(part.tolist())
    return [np.array(c, dtype=np.int64) for c in client]


# --------------------------------------------------------------------------
# Aggregation candidates — every one is depth-1 under multiparty CKKS.
# fisher/count_head use the num/denom trick: the server only ever ADDS
# ciphertexts (the per-client products are formed client-side, pre-encryption);
# clients decrypt numerator and denominator and divide in plaintext.
# --------------------------------------------------------------------------
def agg_plain(theta0, deltas, w, lam=1.0):
    out = {}
    for k in theta0:
        acc = torch.zeros_like(theta0[k])
        for i in range(len(deltas)):
            acc += w[i] * deltas[i][k]
        out[k] = theta0[k] + lam * acc
    return out


def agg_fisher(theta0, deltas, w, fishers, eps=1e-8):
    out = {}
    for k in theta0:
        num = torch.zeros_like(theta0[k])
        den = torch.zeros_like(theta0[k])
        for i in range(len(deltas)):
            num += w[i] * fishers[i][k] * deltas[i][k]
            den += w[i] * fishers[i][k]
        out[k] = theta0[k] + num / (den + eps)
    return out


def agg_count_head(theta0, deltas, w, class_counts, head_keys=("head.weight", "head.bias")):
    """Coverage-aware: head row c is the n_{j,c}-weighted average of the clients'
    row-c displacements (clients that saw class c decide its row); every other
    tensor keeps the plain sample-weighted combine. Rows nobody covers stay θ₀."""
    out = agg_plain(theta0, deltas, w, lam=1.0)
    counts = torch.as_tensor(np.stack(class_counts), dtype=torch.float32)  # (N, C)
    den = counts.sum(0).clamp_min(1e-9)                                    # (C,)
    for k in head_keys:
        if k not in theta0:
            continue
        num = torch.zeros_like(theta0[k])
        for i in range(len(deltas)):
            ci = counts[i].to(theta0[k].device)
            num += (ci.unsqueeze(-1) if theta0[k].dim() == 2 else ci) * deltas[i][k]
        d = den.to(theta0[k].device)
        out[k] = theta0[k] + num / (d.unsqueeze(-1) if theta0[k].dim() == 2 else d)
    return out


_DATA = {}
_CENTRAL = {}
_SEMHEAD = {}
def _data(task, backbone, seed):
    key = (task, backbone, seed)
    if key not in _DATA:
        Xtr, ytr, Xte, yte, C = load_text(task, seed=seed)
        ids_tr, mask_tr = tokenize(backbone, Xtr)
        ids_te, mask_te = tokenize(backbone, Xte)
        _DATA[key] = (ids_tr, mask_tr, ytr, ids_te, mask_te, yte, C)
    return _DATA[key]


def run_cell(task, backbone, N, alpha, seed, K=200, lr=5e-4, bs=32, r=8,
             freeze_a=True, sem_init=False, swa=False, prox_mu=0.0,
             calib_tau=0.0, lambdas=(0.25, 0.5, 0.75, 1.0), val_frac=0.1):
    ids_tr, mask_tr, ytr, ids_te, mask_te, yte, C = _data(task, backbone, seed)

    head_init = None
    if sem_init:
        hk = (task, backbone)
        if hk not in _SEMHEAD:
            _SEMHEAD[hk] = semantic_head_init(backbone, task)
        head_init = _SEMHEAD[hk]

    set_seed(seed)
    model = TextLoRA(backbone, C, r=r, freeze_a=freeze_a, head_init=head_init).to(DEVICE)
    theta0 = trainable_state(model)
    A0 = evaluate(model, ids_te, mask_te, yte)
    ntrain = n_trainable(model)

    parts = dirichlet_partition(ytr, N, alpha, C, seed)
    rng = np.random.default_rng(seed + 1)
    deltas, sizes, fishers, counts, vals = [], [], [], [], []
    for ci in parts:
        if len(ci) == 0:
            deltas.append({k: torch.zeros_like(v) for k, v in theta0.items()})
            fishers.append({k: torch.zeros_like(v) for k, v in theta0.items()})
            counts.append(np.zeros(C)); sizes.append(0); vals.append(np.array([], dtype=np.int64))
            continue
        ci = rng.permutation(ci)
        nv = int(val_frac * len(ci)) if len(ci) >= 20 else 0
        val_idx, tr_idx = ci[:nv], ci[nv:]
        load_trainable(model, theta0)
        logp = None
        if calib_tau > 0:
            pr = np.bincount(ytr[tr_idx], minlength=C).astype(np.float64)
            logp = calib_tau * torch.log(torch.as_tensor(
                (pr + 1.0) / (pr.sum() + C), dtype=torch.float32))
        train_steps(model, ids_tr[tr_idx], mask_tr[tr_idx], ytr[tr_idx],
                    steps=K, lr=lr, bs=bs, theta0=theta0,
                    prox_mu=prox_mu, calib_logp=logp, swa=swa)
        st = trainable_state(model)
        deltas.append({k: st[k] - theta0[k] for k in theta0})
        fishers.append(diag_fisher(model, ids_tr[tr_idx], mask_tr[tr_idx],
                                   ytr[tr_idx], bs=bs))
        counts.append(np.bincount(ytr[tr_idx], minlength=C).astype(np.float64))
        sizes.append(int(len(tr_idx))); vals.append(val_idx)

    tot = max(sum(sizes), 1); w = [s / tot for s in sizes]

    # --- candidate set (all depth-1) ---
    cands = {}
    for lam in lambdas:
        cands[f"plain_l{lam:g}"] = agg_plain(theta0, deltas, w, lam=float(lam))
    cands["fisher"] = agg_fisher(theta0, deltas, w, fishers)
    cands["count_head"] = agg_count_head(theta0, deltas, w, counts)

    test_acc = {}
    for name, st in cands.items():
        load_trainable(model, st)
        test_acc[name] = evaluate(model, ids_te, mask_te, yte)

    # --- client-vote selection on local holdouts (post-decryption, free) ---
    votes = {name: 0.0 for name in cands}
    vtot = 0.0
    for i, vi in enumerate(vals):
        if len(vi) == 0:
            continue
        for name, st in cands.items():
            load_trainable(model, st)
            votes[name] += sizes[i] * evaluate(model, ids_tr[vi], mask_tr[vi], ytr[vi])
        vtot += sizes[i]
    if vtot > 0:
        selected = max(votes, key=lambda nme: votes[nme])
    else:
        selected = "plain_l1"
    Astar = test_acc.get("plain_l1", test_acc[max(test_acc, key=test_acc.get)])
    lam_best = max((nme for nme in test_acc if nme.startswith("plain_l")),
                   key=lambda nme: test_acc[nme])

    ckey = (task, backbone, seed, K, r, freeze_a, sem_init, lr)
    if ckey not in _CENTRAL:
        load_trainable(model, theta0)
        train_steps(model, ids_tr, mask_tr, ytr, steps=max(K, N * K // 4), lr=lr, bs=bs)
        _CENTRAL[ckey] = evaluate(model, ids_te, mask_te, yte)
    A_central = _CENTRAL[ckey]

    return dict(task=task, backbone=backbone, N=N, alpha=alpha, seed=seed,
                K=K, r=r, freeze_a=int(freeze_a), sem_init=int(sem_init),
                swa=int(swa), prox_mu=prox_mu, calib_tau=calib_tau,
                n_trainable=ntrain, A0=round(A0, 4),
                Astar=round(Astar, 4),
                acc_fisher=round(test_acc["fisher"], 4),
                acc_counthead=round(test_acc["count_head"], 4),
                lam_best=float(lam_best.split("plain_l")[1]),
                acc_lam_best=round(test_acc[lam_best], 4),
                selected=selected,
                acc_selected=round(test_acc[selected], 4),
                A_central=round(A_central, 4),
                increment=round(Astar - A0, 4),
                gap=round(A_central - Astar, 4),
                test_acc_all={k: round(v, 4) for k, v in test_acc.items()})


CSV_COLS = ["task", "backbone", "N", "alpha", "seed", "K", "r", "freeze_a",
            "sem_init", "swa", "prox_mu", "calib_tau", "n_trainable", "A0",
            "Astar", "acc_fisher", "acc_counthead", "lam_best", "acc_lam_best",
            "selected", "acc_selected", "A_central", "increment", "gap"]


def cell_name(c):
    return ("cell_%s_%s_N%d_a%s_s%d_K%d_r%d_fa%d_si%d_sw%d_pm%s_ct%s_lr%s.json"
            % (c["task"], c["backbone"], c["N"], c["alpha"], c["seed"], c["K"],
               c["r"], int(c.get("freeze_a", True)), int(c.get("sem_init", False)),
               int(c.get("swa", False)), c.get("prox_mu", 0.0),
               c.get("calib_tau", 0.0), c.get("lr", 5e-4)))


def run_resumable(rows, **c):
    """Run one cell with per-cell JSON resume; append the row to ``rows``."""
    f = OUTDIR / cell_name(c)
    if f.exists():
        row = json.loads(f.read_text())
        rows.append(row)
        print(f"skip (done): {f.name}", flush=True)
        return row
    t = time.time()
    row = run_cell(**c)
    row["wall"] = round(time.time() - t, 1)
    f.write_text(json.dumps(row))
    rows.append(row)
    print(f"ok {row['task']} fa={row['freeze_a']} si={row['sem_init']} "
          f"s={row['seed']} | A0={row['A0']:.3f} A*={row['Astar']:.3f} "
          f"fis={row['acc_fisher']:.3f} cnt={row['acc_counthead']:.3f} "
          f"sel={row['selected']}:{row['acc_selected']:.3f} "
          f"Ac={row['A_central']:.3f} ({row['wall']}s)", flush=True)
    return row


def print_csv(rows):
    """Paste-ready CSV block: one header line, one row per cell, nothing else."""
    print(",".join(CSV_COLS))
    for r in rows:
        print(",".join(str(r[c]) for c in CSV_COLS))


# --------------------------------------------------------------------------
# S7 (issue fa04) — Byzantine-lite robustness via leave-one-out candidates.
# The server forms the plain aggregate plus all N leave-one-out aggregates —
# every one a depth-1 linear combine with public renormalized weights — and
# the clients threshold-decrypt all N+1 candidates and vote on local holdouts.
# A poisoned contribution shows up as the LOO candidate whose exclusion wins.
# --------------------------------------------------------------------------
def craft_attack(delta_honest, attack, all_deltas, rng):
    """Replace the attacker's honest delta with a crafted one (client-side)."""
    if attack == "sign_flip":
        return {k: -5.0 * v for k, v in delta_honest.items()}
    if attack == "gauss":
        out = {}
        for k, v in delta_honest.items():
            rms = float(torch.stack([d[k] for d in all_deltas]).pow(2).mean().sqrt())
            out[k] = torch.randn_like(v) * 5.0 * max(rms, 1e-8)
        return out
    raise ValueError(attack)


def run_robust_cell(task, backbone, N, alpha, seed, K=200, lr=5e-4, bs=32, r=8,
                    attack="sign_flip", freeze_a=True, val_frac=0.1):
    ids_tr, mask_tr, ytr, ids_te, mask_te, yte, C = _data(task, backbone, seed)
    set_seed(seed)
    model = TextLoRA(backbone, C, r=r, freeze_a=freeze_a).to(DEVICE)
    theta0 = trainable_state(model)

    parts = dirichlet_partition(ytr, N, alpha, C, seed)
    rng = np.random.default_rng(seed + 1)
    deltas, sizes, vals = [], [], []
    for ci in parts:
        if len(ci) == 0:
            deltas.append({k: torch.zeros_like(v) for k, v in theta0.items()})
            sizes.append(0); vals.append(np.array([], dtype=np.int64)); continue
        ci = rng.permutation(ci)
        nv = int(val_frac * len(ci)) if len(ci) >= 20 else 0
        val_idx, tr_idx = ci[:nv], ci[nv:]
        load_trainable(model, theta0)
        train_steps(model, ids_tr[tr_idx], mask_tr[tr_idx], ytr[tr_idx], steps=K, lr=lr, bs=bs)
        st = trainable_state(model)
        deltas.append({k: st[k] - theta0[k] for k in theta0})
        sizes.append(int(len(tr_idx))); vals.append(val_idx)

    # Attacker = the largest shard (worst case for sample weighting).
    atk = int(np.argmax(sizes))
    if attack == "label_flip":
        ci = parts[atk]
        ci = rng.permutation(ci)
        nv = int(val_frac * len(ci)) if len(ci) >= 20 else 0
        tr_idx = ci[nv:]
        load_trainable(model, theta0)
        y_flip = (ytr[tr_idx] + 1) % C
        train_steps(model, ids_tr[tr_idx], mask_tr[tr_idx], y_flip, steps=K, lr=lr, bs=bs)
        st = trainable_state(model)
        deltas[atk] = {k: st[k] - theta0[k] for k in theta0}
    else:
        deltas[atk] = craft_attack(deltas[atk], attack, deltas, rng)

    tot = max(sum(sizes), 1); w = [s / tot for s in sizes]
    cands = {"plain": agg_plain(theta0, deltas, w, lam=1.0)}
    for i in range(N):
        wi = [w[j] for j in range(N) if j != i]
        s = sum(wi)
        wloo = [(w[j] / s if s > 0 else 0.0) for j in range(N) if j != i]
        dloo = [deltas[j] for j in range(N) if j != i]
        cands[f"loo_{i}"] = agg_plain(theta0, dloo, wloo, lam=1.0)

    test_acc = {}
    for name, st in cands.items():
        load_trainable(model, st)
        test_acc[name] = evaluate(model, ids_te, mask_te, yte)

    votes = {name: 0.0 for name in cands}
    vtot = 0.0
    for i, vi in enumerate(vals):
        if len(vi) == 0:
            continue
        for name, st in cands.items():
            load_trainable(model, st)
            votes[name] += sizes[i] * evaluate(model, ids_tr[vi], mask_tr[vi], ytr[vi])
        vtot += sizes[i]
    selected = max(votes, key=lambda nme: votes[nme]) if vtot > 0 else "plain"

    return dict(task=task, backbone=backbone, N=N, alpha=alpha, seed=seed,
                K=K, r=r, freeze_a=int(freeze_a), attack=attack,
                attacker=atk, attacker_w=round(w[atk], 4),
                acc_poisoned_plain=round(test_acc["plain"], 4),
                acc_selected=round(test_acc[selected], 4),
                selected=selected,
                attacker_excluded=int(selected == f"loo_{atk}"),
                acc_oracle=round(test_acc[f"loo_{atk}"], 4))


CSV_COLS_ROBUST = ["task", "backbone", "N", "alpha", "seed", "K", "r", "freeze_a",
                   "attack", "attacker", "attacker_w", "acc_poisoned_plain",
                   "acc_selected", "selected", "attacker_excluded", "acc_oracle"]


def run_robust_resumable(rows, **c):
    f = OUTDIR / ("robust_" + cell_name(c).replace(".json", "") +
                  "_atk%s.json" % c.get("attack", "sign_flip"))
    if f.exists():
        rows.append(json.loads(f.read_text()))
        print(f"skip (done): {f.name}", flush=True)
        return rows[-1]
    t = time.time()
    row = run_robust_cell(**c)
    row["wall"] = round(time.time() - t, 1)
    f.write_text(json.dumps(row))
    rows.append(row)
    print(f"ok {row['task']} atk={row['attack']} s={row['seed']} | "
          f"poisoned={row['acc_poisoned_plain']:.3f} sel={row['selected']}:"
          f"{row['acc_selected']:.3f} oracle={row['acc_oracle']:.3f} "
          f"excluded={row['attacker_excluded']} ({row['wall']}s)", flush=True)
    return row


def print_csv_robust(rows):
    print(",".join(CSV_COLS_ROBUST))
    for r in rows:
        print(",".join(str(r[c]) for c in CSV_COLS_ROBUST))


# ===== CLI (VALAR) =====
# Everything below this marker is VALAR-only; the notebook builder drops it.

def grid(stage):
    base = dict(task="ag_news", backbone="roberta_base", N=10, alpha=0.1,
                K=200, r=8, freeze_a=True)
    seeds = [42, 43, 44]
    cells = []
    if stage == "s1":            # freeze-A vs both-A-B on the unstable tasks
        for task in ["ag_news", "trec"]:
            for fa in [True, False]:
                for s in seeds:
                    cells.append({**base, "task": task, "freeze_a": fa, "seed": s})
    elif stage == "s2":          # semantic head init across all four tasks
        for task in ["ag_news", "trec", "dbpedia_14", "banking77"]:
            for s in seeds:
                cells.append({**base, "task": task, "sem_init": True, "seed": s})
        # Attribution baseline: banking77 WITHOUT semantic init (freeze-A,
        # r=8) — s1 covers only ag_news/trec, so without these three cells the
        # banking77 jump cannot be split between freeze-A+candidates and the
        # semantic init.
        for s in seeds:
            cells.append({**base, "task": "banking77", "seed": s})
    elif stage == "s3":          # client-side levers on the unstable task
        for kv in [dict(swa=True), dict(prox_mu=0.01), dict(calib_tau=1.0)]:
            for s in seeds:
                cells.append({**base, **kv, "seed": s})
    elif stage == "s4":          # K x lr mini-grid, freeze-A
        for K in [100, 200, 400]:
            for lr_t in [5e-4, 1e-3]:
                cells.append({**base, "task": "dbpedia_14", "K": K,
                              "lr": lr_t, "seed": 42})
    elif stage == "s5":          # rank compensation for the frozen A
        for r in [8, 16, 32]:
            for s in seeds:
                cells.append({**base, "task": "banking77", "r": r,
                              "sem_init": True, "seed": s})
    elif stage == "s7":          # Byzantine-lite LOO robustness (issue fa04)
        for task in ["dbpedia_14", "ag_news"]:
            for attack in ["sign_flip", "gauss", "label_flip"]:
                for s in seeds:
                    cells.append(dict(task=task, backbone="roberta_base", N=10,
                                      alpha=0.1, K=200, r=8, freeze_a=True,
                                      attack=attack, seed=s))
    else:
        raise SystemExit(f"unknown stage {stage!r}")
    return cells


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True,
                    choices=["s1", "s2", "s3", "s4", "s5", "s7"])
    ap.add_argument("--bs", type=int, default=32)
    args = ap.parse_args()

    robust = args.stage == "s7"
    runner = run_robust_resumable if robust else run_resumable
    cells = grid(args.stage)
    print(f"[{args.stage}] device={DEVICE} cells={len(cells)}", flush=True)
    rows = []
    for c in cells:
        try:
            runner(rows, bs=args.bs, **c)
        except Exception as e:  # noqa: BLE001 — keep the stage alive on a bad cell
            import traceback
            (OUTDIR / (cell_name(c).replace(".json", ".FAIL"))).write_text(
                traceback.format_exc())
            print(f"[{args.stage}] FAIL {cell_name(c)}: {e}", flush=True)

    print(f"\n===== BEGIN results.csv ({args.stage}) =====", flush=True)
    (print_csv_robust if robust else print_csv)(rows)
    print("===== END results.csv =====\n", flush=True)


if __name__ == "__main__":
    main()
