"""Generator for notebooks/finetune_increment.ipynb.

We build the notebook from clean Python strings (one per cell) and ast-parse
every code cell before emitting, so the shipped .ipynb is syntactically valid
even though it is authored here rather than in Colab. Run:

    python notebooks/build_increment_nb.py

It writes notebooks/finetune_increment.ipynb.

The notebook implements the fine-tuning-pivot method the PRD now describes:
a public base split pretrains a task model M0 (backbone + LoRA on its own
pretrained layers + head); clients fine-tune M0's LoRA on their private data for
a bounded K steps; the server forms the depth-1 weighted sum of the LoRA+head
displacements (the plaintext equivalent of the multiparty-CKKS op, whose real
cost is measured separately in fhe/); the headline is the increment A* - A0 over
the public model, with the centralized fine-tune A_central as ceiling. No new
head from scratch, no alignment, no name-grounding.
"""
import ast
import json
from pathlib import Path

CELLS = []


def md(src: str):
    CELLS.append(("markdown", src))


def code(src: str):
    ast.parse(src)  # fail loudly here if a cell has a syntax error
    CELLS.append(("code", src))


# ---------------------------------------------------------------------------
md(r"""# HE-IFD — One-shot federated fine-tuning: the **increment** experiments

**No public data is assumed.** Method (one `run_increment` call per cell):

1. **Shared start, no public data.** θ0 = the public pretrained backbone (frozen)
   with **zero-init LoRA** + a deterministic head init — the standard adapter
   initialization, identical for every client. No public labelled set, no
   alignment, no name-grounding. A0 (θ0 alone) is therefore ~chance.
2. **Federated fine-tuning.** Each client fine-tunes θ0's **LoRA (on the backbone's
   own pretrained layers) + head** on its OWN private data for K steps, producing
   Δ = θ_K − θ0 (LoRA + head only — a few thousand scalars).
3. **Encrypted aggregation (plaintext here).** θ\* = θ0 + Σ w_i·Δ_i, the depth-1
   weighted sum the multiparty-CKKS op computes (real CKKS cost is in `fhe/`).
4. **What we measure:** the **increment from fine-tuning the pretrained parts** =
   acc(LoRA, r>0) − acc(frozen-feature head, r=0); the centralized fine-tune
   **A_central** is the ceiling and **gap = A_central − A\***.

**E5 alone** adds a small *public base* split to ask whether public data helps —
an ablation, **not** assumed anywhere else.

LoRA is what makes "fine-tune the pretrained parts" cheap to encrypt: low rank ⇒
a few-thousand-scalar payload even though we adapt the backbone's own layers.

**MIA is a discussion in the paper, not an experiment** — the server sees only
ciphertexts and the released model is inspectable only by the clients; there is
no separate experimental MIA stage here.

**How to run:** Runtime → Run all. Run the **VERIFY** cell first (~5 min), check
the increment is real, then run the program. Every stage prints paste-ready CSV.
Resumable: re-running skips finished cells.""")

# ---------------------------------------------------------------------------
code(r"""# ===== Setup =====
# Colab has torch + datasets; transformers/peft may need installing.
import importlib, subprocess, sys
for pkg in ["transformers", "peft", "datasets"]:
    if importlib.util.find_spec(pkg) is None:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", pkg], check=True)

import os, json, math, time, random
import numpy as np
import torch, torch.nn as nn, torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
from peft import LoraConfig, get_peft_model
from datasets import load_dataset

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print("device:", DEVICE, "| torch:", torch.__version__)

def set_seed(s):
    random.seed(s); np.random.seed(s); torch.manual_seed(s)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(s)""")

# ---------------------------------------------------------------------------
code(r'''# ===== Library: data, model, train/eval, the federated increment loop =====

# Task registry. (hf id, text field, label field, #classes). Namespaced ids for
# current `datasets`. Subsample for tractable real-fine-tuning wall-clock.
TEXT_TASKS = {
    "ag_news":    dict(hf="fancyzhx/ag_news",    text="text",    label="label",        C=4),
    "dbpedia_14": dict(hf="fancyzhx/dbpedia_14", text="content", label="label",        C=14),
    "trec":       dict(hf="CogComp/trec",        text="text",    label="coarse_label", C=6),
    "banking77":  dict(hf="PolyAI/banking77",    text="text",    label="label",        C=77),
}
BACKBONES = {
    "roberta_base": dict(hf="roberta-base", targets=["query", "value"]),
    "mpnet_st":     dict(hf="sentence-transformers/all-mpnet-base-v2",
                         targets=["q", "v"]),  # MPNet attention proj names
}

def _load_any(hf_id):
    # Version-independent: try normally, then the parquet-export revision that
    # bypasses removed dataset scripts on datasets>=3.
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

# Tokenize once per (backbone, task, seed); cache the tensors.
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
    """Frozen backbone + LoRA on its pretrained attention layers + linear head.

    Only the LoRA matrices and the head are trainable; they are the few-thousand-
    scalar payload that gets aggregated/encrypted. r=0 means head-only (the
    linear-probe ablation: no LoRA, frozen backbone)."""
    def __init__(self, backbone, C, r=8):
        super().__init__()
        base = AutoModel.from_pretrained(BACKBONES[backbone]["hf"])
        hidden = base.config.hidden_size           # capture BEFORE peft wraps it
        for p in base.parameters():
            p.requires_grad = False
        if r > 0:
            lcfg = LoraConfig(r=r, lora_alpha=2 * r, lora_dropout=0.0, bias="none",
                              target_modules=BACKBONES[backbone]["targets"])
            base = get_peft_model(base, lcfg)      # r=0 => frozen backbone, head-only probe
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
    return [np.array(c, dtype=np.int64) for c in client]''')

# ---------------------------------------------------------------------------
code(r'''# ===== The federated increment experiment =====
# Caches so a sweep over (N, alpha) does not retokenize / refit M0 / refit the
# centralized ceiling, which depend only on (task, backbone, seed, base_frac, K, r).
_DATA = {}    # (task, backbone, seed) -> tensors
_M0    = {}   # (task, backbone, seed, base_frac, r, steps) -> (theta0, A0)
_CENTRAL = {} # (task, backbone, seed, base_frac, K, r, lr) -> A_central

def _data(task, backbone, seed):
    key = (task, backbone, seed)
    if key not in _DATA:
        Xtr, ytr, Xte, yte, C = load_text(task, seed=seed)
        ids_tr, mask_tr = tokenize(backbone, Xtr)
        ids_te, mask_te = tokenize(backbone, Xte)
        _DATA[key] = (ids_tr, mask_tr, ytr, ids_te, mask_te, yte, C)
    return _DATA[key]

def _new_model(task, backbone, seed, r):
    set_seed(seed)
    _, _, _, _, _, _, C = _data(task, backbone, seed)
    return TextLoRA(backbone, C, r=r).to(DEVICE)

def run_increment(task, backbone="roberta_base", N=10, alpha=0.1, seed=42,
                  base_frac=0.0, K=200, base_steps=600, lr=5e-4, bs=32, r=8,
                  lambdas=(0.0, 0.25, 0.5, 0.75, 1.0)):
    """One cell -> dict with A0 / Astar / A_central / increment / gap (+ lambda curve).

    base_frac=0.0 (DEFAULT): NO public data. theta0 is the public pretrained
    backbone with zero-init LoRA + the deterministic head init; A0 ~ chance.
    base_frac>0 (E5 only): theta0 is pretrained on a public base split first."""
    ids_tr, mask_tr, ytr, ids_te, mask_te, yte, C = _data(task, backbone, seed)
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(ytr))
    nb = int(base_frac * len(ytr))
    base_idx, priv_idx = perm[:nb], perm[nb:]   # base empty when base_frac=0 => all data private

    model = _new_model(task, backbone, seed, r)

    # ---- theta0: the shared public starting model (cached) ----
    m0key = (task, backbone, seed, base_frac, r, base_steps)
    if m0key not in _M0:
        # `model` is already the fresh, seed-deterministic shared init from _new_model.
        if nb > 0:                                # public base (E5) — otherwise skip: no public data
            train_steps(model, ids_tr[base_idx], mask_tr[base_idx], ytr[base_idx],
                        steps=base_steps, lr=lr, bs=bs)
        theta0 = trainable_state(model)
        A0 = evaluate(model, ids_te, mask_te, yte)
        _M0[m0key] = (theta0, A0, n_trainable(model))
    theta0, A0, ntrain = _M0[m0key]

    # ---- private partition + per-client bounded fine-tuning from M0 ----
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

    # ---- depth-1 weighted aggregate (the CKKS op, in plaintext) + lambda sweep ----
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

    # ---- centralized ceiling: fine-tune M0 on ALL private data (cached) ----
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

# Results accumulator (resumable: a config key maps to its row).
RESULTS = {}
CSV_COLS = ["task", "backbone", "N", "alpha", "seed", "base_frac", "K", "r",
            "n_trainable", "A0", "Astar", "A_central", "increment", "gap"]
def _key(**c):
    return tuple(c[k] for k in ["task", "backbone", "N", "alpha", "seed", "base_frac", "K", "r"])
def do(**cfg):
    k = _key(**cfg)
    if k in RESULTS:
        return RESULTS[k]
    t = time.time()
    row = run_increment(**cfg)
    row["wall"] = round(time.time() - t, 1)
    RESULTS[k] = row
    print(f"  {cfg.get('task'):11s} N={cfg.get('N'):>3} a={cfg.get('alpha'):<4} "
          f"r={cfg.get('r')} base={cfg.get('base_frac')} | A0={row['A0']:.3f} "
          f"A*={row['Astar']:.3f} Ac={row['A_central']:.3f} "
          f"inc={row['increment']:+.3f} ({row['wall']}s)", flush=True)
    return row
def print_csv(rows=None):
    rows = rows if rows is not None else list(RESULTS.values())
    print("\n===== BEGIN results.csv =====")
    print(",".join(CSV_COLS))
    for r in rows:
        print(",".join(str(r[c]) for c in CSV_COLS))
    print("===== END results.csv =====\n")''')

# ---------------------------------------------------------------------------
md(r"""## VERIFY — run this first (~5 min)

One config, **no public data**. Check that **A\*** is well above chance and close
to **A_central** (one-shot ≈ centralized fine-tune). A0 is ~chance here by design
(θ0 is the bare backbone, no task head). If A\* is healthy, start the program.""")

code(r"""# VERIFY: DBpedia, N=10, alpha=0.1, LoRA r=8, NO public base (base_frac=0).
v = run_increment(task="dbpedia_14", backbone="roberta_base", N=10, alpha=0.1,
                  seed=42, base_frac=0.0, K=200, r=8)
print("A0 (theta0, no public base): %.3f   (~chance 1/14 = %.3f)" % (v["A0"], 1 / 14))
print("A* (federated LoRA):         %.3f" % v["Astar"])
print("A_central (ceiling):         %.3f" % v["A_central"])
print("gap A_central - A*:          %+.3f" % v["gap"])
print("trainable params (LoRA+head):", v["n_trainable"])
print("lambda curve:", [(l, round(a, 3)) for l, a in v["lambda_curve"]])
print("\\n(E1 measures the real headline: acc at r=8 minus acc at r=0 = the lift")
print(" from fine-tuning the pretrained layers vs a frozen-feature head.)")""")

# ---------------------------------------------------------------------------
md(r"""## The program

Each stage appends to `RESULTS` and prints paste-ready CSV. Comment out stages
you do not want. Real LoRA fine-tuning is minutes per cell, so the heavier stages
(E3 N=100, E7 vision) are last; the run is resumable if the runtime drops.""")

code(r'''# ===== E1  The increment from fine-tuning the pretrained parts (HEADLINE) =====
# r=0 = frozen backbone, head-only linear probe.  r>0 = LoRA on the backbone's own
# pretrained layers.  The increment is acc(r>0) - acc(r=0).  NO public data.
SEEDS = [42, 43, 44]
for task in ["ag_news", "dbpedia_14", "trec", "banking77"]:
    for r in [0, 8, 16]:
        for s in SEEDS:
            do(task=task, backbone="roberta_base", N=10, alpha=0.1, seed=s, base_frac=0.0, K=200, r=r)
print_csv()''')

code(r'''# ===== E2  Heterogeneity: does the increment survive label skew =====
for a in [0.05, 0.1, 0.3, 1.0]:
    for s in SEEDS:
        do(task="dbpedia_14", backbone="roberta_base", N=10, alpha=a, seed=s, base_frac=0.0, K=200, r=8)
print_csv()''')

code(r'''# ===== E3  Multi-client robustness =====
for N in [10, 20, 50, 100]:
    for s in SEEDS:
        do(task="dbpedia_14", backbone="roberta_base", N=N, alpha=0.1, seed=s, base_frac=0.0, K=200, r=8)
print_csv()''')

code(r'''# ===== E4  Trajectory length K (bounded steps) =====
for K in [100, 200, 400]:
    for s in SEEDS:
        do(task="dbpedia_14", backbone="roberta_base", N=10, alpha=0.1, seed=s, base_frac=0.0, K=K, r=8)
print_csv()''')

code(r'''# ===== E5  PUBLIC BASE ablation (the ONLY stage that uses public data) =====
# base_frac=0.0 is the no-public-data method; >0 pretrains theta0 on that public
# slice first. Asks whether a little public data would help — not assumed elsewhere.
for bf in [0.0, 0.1, 0.2, 0.3, 0.5]:
    for s in SEEDS:
        do(task="dbpedia_14", backbone="roberta_base", N=10, alpha=0.1, seed=s, base_frac=bf, K=200, r=8)
print_csv()''')

code(r'''# ===== E6  lambda drift curves (eval-only; no extra training) =====
# Reuses the E2 alpha=0.05 cells. lambda<1 pulls theta* back toward theta0 along
# theta*(lambda) = theta0 + lambda * sum_i w_i Delta_i.
for s in SEEDS:
    k = _key(task="dbpedia_14", backbone="roberta_base", N=10, alpha=0.05, seed=s, base_frac=0.0, K=200, r=8)
    if k in RESULTS:
        print("lambda @ alpha=0.05 seed", s, RESULTS[k]["lambda_curve"])''')

code(r'''# ===== E1b  MPNet backbone (confirm the method is not RoBERTa-specific) =====
# If this errors on LoRA target_modules, print the module names and set them:
#   print(_new_model("trec","mpnet_st",42,8).backbone)
for task in ["dbpedia_14", "trec"]:
    for r in [0, 8]:
        for s in SEEDS:
            do(task=task, backbone="mpnet_st", N=10, alpha=0.1, seed=s, base_frac=0.0, K=200, r=r)
print_csv()''')

code(r'''# ===== Full dump (paste into results/<case>/results.csv) =====
print_csv()''')

# ---------------------------------------------------------------------------
md(r"""## Vision (E7) and what stays in the paper as discussion

**E7 vision** (ImageNet ViT-B/16 on CIFAR-100) follows the identical recipe with
an image backbone; it is heavier, so add it once the text program is confirmed.
Ask and I will drop in the vision cell.

**Not experiments — paper discussion only:**
- **MIA / reconstruction.** The server sees only ciphertexts (no leakage beyond
  the released model); the released model is inspectable only by the clients
  after threshold decryption. We argue the residual channel is the released model
  alone, the inherent floor of any protocol that hands parties a shared model.
- **CKKS cost / correctness.** Measured separately in `fhe/` (the depth-1 weighted
  sum above is exactly that op); the numbers are already in the cost section.""")

# ---------------------------------------------------------------------------
nb = {
    "cells": [
        {"cell_type": t, "metadata": {},
         **({"source": s.splitlines(keepends=True)} if t == "markdown"
            else {"source": s.splitlines(keepends=True), "outputs": [], "execution_count": None})}
        for (t, s) in CELLS
    ],
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
        "accelerator": "GPU", "colab": {"provenance": []},
    },
    "nbformat": 4, "nbformat_minor": 5,
}
out = Path(__file__).parent / "finetune_increment.ipynb"
out.write_text(json.dumps(nb, indent=1))
print("wrote", out, "with", len(CELLS), "cells")
