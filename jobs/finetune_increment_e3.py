#!/usr/bin/env python
"""E3 (multi-client robustness) for the one-shot federated fine-tuning increment
study — standalone, for VALAR. Ported verbatim from
notebooks/finetune_increment.ipynb (both LoRA matrices trained, so it stays
comparable to the Colab E1/E2 run; freeze-A is a separate pending decision).

One ``--N`` per invocation (driven by a Slurm job array), loops the 3 seeds,
writes one JSON per (N, seed) cell (resumable: existing cells are skipped) and
prints a paste-ready CSV block. Runs fully offline — roberta-base and dbpedia_14
are pre-cached on VALAR; the sbatch wrapper sets HF_HUB_OFFLINE=1.
"""
import argparse
import json
import os
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
CASE = "finetune_increment_e3"
OUTDIR = Path("results") / CASE
OUTDIR.mkdir(parents=True, exist_ok=True)


def set_seed(s):
    random.seed(s); np.random.seed(s); torch.manual_seed(s)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(s)


TEXT_TASKS = {
    "dbpedia_14": dict(hf="fancyzhx/dbpedia_14", text="content", label="label", C=14),
}
BACKBONES = {
    "roberta_base": dict(hf="roberta-base", targets=["query", "value"]),
}


def _load_any(hf_id):
    last = None
    for kw in ({}, {"revision": "refs/convert/parquet"}):
        try:
            return load_dataset(hf_id, **kw)
        except Exception as e:  # noqa: BLE001
            last = e
    raise last


def load_text(task, max_train=20000, max_test=5000, seed=0):
    cfg = TEXT_TASKS[task]
    ds = _load_any(cfg["hf"])
    tr, te = ds["train"], ds["test"]
    rng = np.random.default_rng(seed)
    def take(split, n):
        n = min(n, len(split))
        idx = rng.choice(len(split), n, replace=False)
        sub = split.select(idx.tolist())
        return list(sub[cfg["text"]]), np.array(sub[cfg["label"]], dtype=np.int64)
    Xtr, ytr = take(tr, max_train)
    Xte, yte = take(te, max_test)
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
    def __init__(self, backbone, C, r=8):
        super().__init__()
        base = AutoModel.from_pretrained(BACKBONES[backbone]["hf"])
        hidden = base.config.hidden_size
        for p in base.parameters():
            p.requires_grad = False
        if r > 0:
            lcfg = LoraConfig(r=r, lora_alpha=2 * r, lora_dropout=0.0, bias="none",
                              target_modules=BACKBONES[backbone]["targets"])
            base = get_peft_model(base, lcfg)
        self.backbone = base
        self.head = nn.Linear(hidden, C)
    def forward(self, ids, mask):
        out = self.backbone(input_ids=ids, attention_mask=mask).last_hidden_state
        return self.head(mean_pool(out, mask))


def trainable_state(model):
    return {n: p.detach().clone() for n, p in model.named_parameters() if p.requires_grad}

def load_trainable(model, state):
    with torch.no_grad():
        for n, p in model.named_parameters():
            if n in state:
                p.copy_(state[n].to(p.device))

def n_trainable(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def train_steps(model, ids, mask, y, steps, lr, bs):
    model.train()
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=lr)
    n = len(y); yt = torch.as_tensor(y, device=DEVICE)
    g = torch.Generator().manual_seed(0)
    for _ in range(max(1, steps)):
        idx = torch.randint(0, n, (min(bs, n),), generator=g)
        lo = model(ids[idx].to(DEVICE), mask[idx].to(DEVICE))
        loss = F.cross_entropy(lo, yt[idx])
        opt.zero_grad(); loss.backward(); opt.step()
    return model


@torch.no_grad()
def evaluate(model, ids, mask, y, bs=256):
    model.eval()
    n = len(y); yt = torch.as_tensor(y); correct = 0
    for s in range(0, n, bs):
        lo = model(ids[s:s + bs].to(DEVICE), mask[s:s + bs].to(DEVICE))
        correct += (lo.argmax(1).cpu() == yt[s:s + bs]).sum().item()
    return correct / n


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


_DATA = {}
_CENTRAL = {}
def _data(task, backbone, seed):
    key = (task, backbone, seed)
    if key not in _DATA:
        Xtr, ytr, Xte, yte, C = load_text(task, seed=seed)
        ids_tr, mask_tr = tokenize(backbone, Xtr)
        ids_te, mask_te = tokenize(backbone, Xte)
        _DATA[key] = (ids_tr, mask_tr, ytr, ids_te, mask_te, yte, C)
    return _DATA[key]


def run_increment(task, backbone, N, alpha, seed, base_frac, K, lr, bs, r,
                  lambdas=(0.0, 0.25, 0.5, 0.75, 1.0)):
    ids_tr, mask_tr, ytr, ids_te, mask_te, yte, C = _data(task, backbone, seed)
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(ytr))
    nb = int(base_frac * len(ytr))
    priv_idx = perm[nb:]

    set_seed(seed)
    model = TextLoRA(backbone, C, r=r).to(DEVICE)
    theta0 = trainable_state(model)            # base_frac=0 -> bare backbone, zero LoRA + head init
    A0 = evaluate(model, ids_te, mask_te, yte)
    ntrain = n_trainable(model)

    parts_local = dirichlet_partition(ytr[priv_idx], N, alpha, C, seed)
    parts = [priv_idx[p] if len(p) else p for p in parts_local]
    deltas, sizes = [], []
    for ci in parts:
        if len(ci) == 0:
            deltas.append({k: torch.zeros_like(v) for k, v in theta0.items()}); sizes.append(0); continue
        load_trainable(model, theta0)
        train_steps(model, ids_tr[ci], mask_tr[ci], ytr[ci], steps=K, lr=lr, bs=bs)
        st = trainable_state(model)
        deltas.append({k: st[k] - theta0[k] for k in theta0}); sizes.append(int(len(ci)))

    tot = max(sum(sizes), 1); w = [s / tot for s in sizes]
    def agg_at(lam):
        out = {}
        for k in theta0:
            acc = torch.zeros_like(theta0[k])
            for i in range(N):
                acc += w[i] * deltas[i][k]
            out[k] = theta0[k] + lam * acc
        return out
    load_trainable(model, agg_at(1.0))
    Astar = evaluate(model, ids_te, mask_te, yte)
    lam_curve = []
    for lam in lambdas:
        load_trainable(model, agg_at(float(lam)))
        lam_curve.append((float(lam), evaluate(model, ids_te, mask_te, yte)))

    ckey = (task, backbone, seed, base_frac, K, r, lr)
    if ckey not in _CENTRAL:
        load_trainable(model, theta0)
        train_steps(model, ids_tr[priv_idx], mask_tr[priv_idx], ytr[priv_idx],
                    steps=max(K, N * K // 4), lr=lr, bs=bs)
        _CENTRAL[ckey] = evaluate(model, ids_te, mask_te, yte)
    A_central = _CENTRAL[ckey]

    return dict(task=task, backbone=backbone, N=N, alpha=alpha, seed=seed,
                base_frac=base_frac, K=K, r=r, n_trainable=ntrain,
                A0=round(A0, 4), Astar=round(Astar, 4), A_central=round(A_central, 4),
                increment=round(Astar - A0, 4), gap=round(A_central - Astar, 4),
                lambda_curve=lam_curve)


CSV_COLS = ["task", "backbone", "N", "alpha", "seed", "base_frac", "K", "r",
            "n_trainable", "A0", "Astar", "A_central", "increment", "gap"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--N", type=int, required=True)
    ap.add_argument("--task", default="dbpedia_14")
    ap.add_argument("--backbone", default="roberta_base")
    ap.add_argument("--alpha", type=float, default=0.1)
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--base_frac", type=float, default=0.0)
    ap.add_argument("--K", type=int, default=200)
    ap.add_argument("--lr", type=float, default=5e-4)
    ap.add_argument("--bs", type=int, default=32)
    ap.add_argument("--r", type=int, default=8)
    args = ap.parse_args()

    print(f"[e3] device={DEVICE} N={args.N} task={args.task} seeds={args.seeds}", flush=True)
    rows = []
    for s in args.seeds:
        cell = OUTDIR / f"cell_N{args.N}_a{args.alpha}_s{s}_K{args.K}_r{args.r}.json"
        if cell.exists():
            row = json.loads(cell.read_text())
            print(f"[e3] skip (done): {cell.name}", flush=True)
        else:
            t = time.time()
            row = run_increment(args.task, args.backbone, args.N, args.alpha, s,
                                args.base_frac, args.K, args.lr, args.bs, args.r)
            row["wall"] = round(time.time() - t, 1)
            cell.write_text(json.dumps(row))
            print(f"[e3] ok N={args.N} s={s} A0={row['A0']:.3f} A*={row['Astar']:.3f} "
                  f"Ac={row['A_central']:.3f} inc={row['increment']:+.3f} ({row['wall']}s)",
                  flush=True)
        rows.append(row)

    print("\n===== BEGIN results.csv (N=%d) =====" % args.N, flush=True)
    print(",".join(CSV_COLS))
    for r in rows:
        print(",".join(str(r[c]) for c in CSV_COLS))
    print("===== END results.csv =====\n", flush=True)


if __name__ == "__main__":
    main()
