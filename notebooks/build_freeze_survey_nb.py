"""Generator for notebooks/lora_freeze_survey.ipynb.

Surveys the freeze-A question for the HE-IFD LoRA aggregation:

  Part 1 (instant, no GPU): the algebraic fact. The server averages the LoRA
    FACTORS (A_i, B_i) linearly, but the effective update is B@A. For both-A-B,
    (Sum w_i B_i)(Sum w_i A_i) != Sum w_i (B_i A_i): cross terms + rank collapse.
    Freezing A (A_i = A0) makes B_i -> B_i A0 linear, so factor-averaging EQUALS
    task arithmetic exactly. Shown as a relative-error + rank table on random
    adapters.

  Part 2: the same fidelity measured on REAL fine-tuned adapters.

  Part 3: accuracy + stability. head-only / both-A-B / freeze-A across tasks x
    seeds; freeze-A should match-or-beat both-A-B and kill the seed-collapse
    variance.

Run: python notebooks/build_freeze_survey_nb.py  ->  notebooks/lora_freeze_survey.ipynb
"""
import ast
import json
from pathlib import Path

CELLS = []


def md(src):
    CELLS.append(("markdown", src))


def code(src):
    ast.parse(src)
    CELLS.append(("code", src))


# ---------------------------------------------------------------------------
md(r"""# LoRA aggregation survey: does freezing $A$ make the merge linear?

The HE server averages the uploaded LoRA **factors** $A_i,B_i$ linearly (depth-1).
But a LoRA layer's effective update is the **product** $\frac{\alpha}{r}B A$. So the
merged update the protocol produces is
$$\Delta W^\star=\Big(\textstyle\sum_i w_i B_i\Big)\Big(\sum_i w_i A_i\Big),$$
while "task arithmetic / averaging the models" means
$$\Delta W_{\mathrm{TA}}=\textstyle\sum_i w_i\,(B_i A_i).$$
These differ (product of sums $\neq$ sum of products) unless $A$ is shared/frozen,
in which case $A_i=A_0$ and $\big(\sum_i w_i B_i\big)A_0=\sum_i w_i(B_i A_0)$ exactly.

This notebook measures both the **aggregation fidelity** (how far $\Delta W^\star$ is
from $\Delta W_{\mathrm{TA}}$) and the **accuracy/stability** of three configs:
head-only ($r{=}0$), both-$A$-$B$ LoRA, and freeze-$A$ LoRA (FFA-LoRA). Run-all;
Part 1 is instant and needs no GPU.""")

# ---------------------------------------------------------------------------
code(r"""# ===== Setup =====
import importlib, subprocess, sys
for pkg in ["transformers", "peft", "datasets"]:
    if importlib.util.find_spec(pkg) is None:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", pkg], check=True)
if importlib.util.find_spec("torchao") is not None:   # Colab's old torchao breaks new peft
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "-q", "torchao"], check=False)
    importlib.invalidate_caches()

import os, json, time, random
import numpy as np
import torch, torch.nn as nn, torch.nn.functional as F
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print("device:", DEVICE)

def set_seed(s):
    random.seed(s); np.random.seed(s); torch.manual_seed(s)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(s)""")

# ---------------------------------------------------------------------------
md(r"""## Part 1 — the algebraic fact (instant, no GPU)

Random rank-$r$ adapters for $N$ clients. We report, per config, the **relative
error** $\lVert\Delta W^\star-\Delta W_{\mathrm{TA}}\rVert/\lVert\Delta W_{\mathrm{TA}}\rVert$
and the **rank** of each merge. Expect: both-$A$-$B$ has large error and collapses
to rank $\le r$; freeze-$A$ is exact (error $\sim$ machine epsilon) and keeps the
full rank.""")

code(r'''# Pure-algebra demo: no training, no GPU. Shows the identity holds iff A is frozen.
def rand_fidelity(N=10, r=8, d=256, k=256, seed=0):
    g = torch.Generator().manual_seed(seed)
    w = torch.softmax(torch.randn(N, generator=g), 0)            # sample weights
    A = [torch.randn(r, k, generator=g) for _ in range(N)]       # per-client A_i
    B = [torch.randn(d, r, generator=g) * 0.1 for _ in range(N)] # per-client B_i (B0=0)
    A0 = torch.randn(r, k, generator=g)                          # shared frozen A

    def rel_and_ranks(A_list):
        Astar = sum(w[i] * A_list[i] for i in range(N))
        Bstar = sum(w[i] * B[i] for i in range(N))
        dW_proto = Bstar @ Astar                                 # protocol merge
        dW_ta = sum(w[i] * (B[i] @ A_list[i]) for i in range(N)) # task arithmetic
        rel = (dW_proto - dW_ta).norm() / dW_ta.norm()
        return rel.item(), torch.linalg.matrix_rank(dW_proto).item(), torch.linalg.matrix_rank(dW_ta).item()

    rel_ab, rk_proto_ab, rk_ta_ab = rel_and_ranks(A)             # both A,B trained
    rel_fz, rk_proto_fz, rk_ta_fz = rel_and_ranks([A0] * N)      # A frozen = A0
    return dict(rel_bothAB=rel_ab, rank_proto_bothAB=rk_proto_ab, rank_TA_bothAB=rk_ta_ab,
                rel_freezeA=rel_fz, rank_proto_freezeA=rk_proto_fz, rank_TA_freezeA=rk_ta_fz)

print(f"{'seed':>4} | {'relerr both-AB':>14} {'rank p/TA':>10} | {'relerr freeze-A':>15} {'rank p/TA':>10}")
for s in range(5):
    d = rand_fidelity(N=10, r=8, seed=s)
    rk_ab = f"{d['rank_proto_bothAB']}/{d['rank_TA_bothAB']}"
    rk_fz = f"{d['rank_proto_freezeA']}/{d['rank_TA_freezeA']}"
    print(f"{s:>4} | {d['rel_bothAB']:>14.3f} {rk_ab:>10} | {d['rel_freezeA']:>15.2e} {rk_fz:>10}")
print("\nboth-A-B: large error, merge collapses to rank<=r.  freeze-A: exact (~1e-7), full rank.")''')

# ---------------------------------------------------------------------------
md(r"""## Library (real-training parts)""")

code(r'''from transformers import AutoTokenizer, AutoModel
from peft import LoraConfig, get_peft_model
from datasets import load_dataset

TEXT_TASKS = {
    "ag_news":    dict(hf="fancyzhx/ag_news",    text="text",    label="label",        C=4),
    "dbpedia_14": dict(hf="fancyzhx/dbpedia_14", text="content", label="label",        C=14),
}
BACKBONES = {"roberta_base": dict(hf="roberta-base", targets=["query", "value"])}

def _load_any(hf_id):
    last = None
    for kw in ({}, {"revision": "refs/convert/parquet"}):
        try:
            return load_dataset(hf_id, **kw)
        except Exception as e:  # noqa: BLE001
            last = e
    raise last

def load_text(task, max_train=20000, max_test=5000, seed=0):
    cfg = TEXT_TASKS[task]; ds = _load_any(cfg["hf"]); rng = np.random.default_rng(seed)
    def take(split, n):
        n = min(n, len(split)); idx = rng.choice(len(split), n, replace=False)
        sub = split.select(idx.tolist())
        return list(sub[cfg["text"]]), np.array(sub[cfg["label"]], dtype=np.int64)
    Xtr, ytr = take(ds["train"], max_train); Xte, yte = take(ds["test"], max_test)
    return Xtr, ytr, Xte, yte, cfg["C"]

_TOK = {}
def tokenize(backbone, texts, max_len=128):
    tok = _TOK.setdefault(backbone, AutoTokenizer.from_pretrained(BACKBONES[backbone]["hf"]))
    enc = tok(texts, padding="max_length", truncation=True, max_length=max_len, return_tensors="pt")
    return enc["input_ids"], enc["attention_mask"]

def mean_pool(h, mask):
    m = mask.unsqueeze(-1).float(); return (h * m).sum(1) / m.sum(1).clamp_min(1e-6)

class TextLoRA(nn.Module):
    def __init__(self, backbone, C, r=8, freeze_a=False):
        super().__init__()
        base = AutoModel.from_pretrained(BACKBONES[backbone]["hf"])
        hidden = base.config.hidden_size
        for p in base.parameters():
            p.requires_grad = False
        if r > 0:
            base = get_peft_model(base, LoraConfig(r=r, lora_alpha=2 * r, lora_dropout=0.0,
                                  bias="none", target_modules=BACKBONES[backbone]["targets"]))
            if freeze_a:                                   # FFA-LoRA: train only B
                for n, p in base.named_parameters():
                    if "lora_A" in n:
                        p.requires_grad = False
        self.backbone = base
        self.head = nn.Linear(hidden, C)
    def forward(self, ids, mask):
        out = self.backbone(input_ids=ids, attention_mask=mask).last_hidden_state
        return self.head(mean_pool(out, mask))

def trainable_state(m):
    return {n: p.detach().clone() for n, p in m.named_parameters() if p.requires_grad}
def load_trainable(m, st):
    with torch.no_grad():
        for n, p in m.named_parameters():
            if n in st: p.copy_(st[n].to(p.device))
def n_trainable(m):
    return sum(p.numel() for p in m.parameters() if p.requires_grad)

def train_steps(m, ids, mask, y, steps, lr, bs):
    m.train(); opt = torch.optim.AdamW([p for p in m.parameters() if p.requires_grad], lr=lr)
    n = len(y); yt = torch.as_tensor(y, device=DEVICE); g = torch.Generator().manual_seed(0)
    for _ in range(max(1, steps)):
        idx = torch.randint(0, n, (min(bs, n),), generator=g)
        loss = F.cross_entropy(m(ids[idx].to(DEVICE), mask[idx].to(DEVICE)), yt[idx])
        opt.zero_grad(); loss.backward(); opt.step()
    return m

@torch.no_grad()
def evaluate(m, ids, mask, y, bs=256):
    m.eval(); n = len(y); yt = torch.as_tensor(y); c = 0
    for s in range(0, n, bs):
        c += (m(ids[s:s+bs].to(DEVICE), mask[s:s+bs].to(DEVICE)).argmax(1).cpu() == yt[s:s+bs]).sum().item()
    return c / n

def dirichlet_partition(y, N, alpha, C, seed):
    rng = np.random.default_rng(seed); client = [[] for _ in range(N)]
    for c in range(C):
        idx = np.where(y == c)[0]; rng.shuffle(idx)
        if not len(idx): continue
        cuts = (np.cumsum(rng.dirichlet([alpha]*N)) * len(idx)).astype(int)[:-1]
        for i, part in enumerate(np.split(idx, cuts)): client[i].extend(part.tolist())
    return [np.array(c, dtype=np.int64) for c in client]

_DATA = {}
def _data(task, backbone, seed):
    k = (task, backbone, seed)
    if k not in _DATA:
        Xtr, ytr, Xte, yte, C = load_text(task, seed=seed)
        idtr, mtr = tokenize(backbone, Xtr); idte, mte = tokenize(backbone, Xte)
        _DATA[k] = (idtr, mtr, ytr, idte, mte, yte, C)
    return _DATA[k]''')

code(r'''# --- LoRA fidelity helpers: pair lora_A/lora_B by module, compute effective dW ---
def lora_modules(model):
    mods = {}
    for n, _ in model.named_parameters():
        if "lora_A" in n: mods.setdefault(n.replace("lora_A", ""), {})["A"] = n
        elif "lora_B" in n: mods.setdefault(n.replace("lora_B", ""), {})["B"] = n
    return {k: v for k, v in mods.items() if "A" in v and "B" in v}

def lora_weights(model):
    return {n: p.detach().float().cpu().clone() for n, p in model.named_parameters() if "lora_" in n}

def aggregation_fidelity(task, backbone, N, alpha, seed, K, r, freeze_a, lr=5e-4, bs=32):
    """Run one federated round; return mean relative error between the protocol
    merge (B*@A*) and task arithmetic (sum w_i B_i@A_i) over LoRA modules."""
    idtr, mtr, ytr, idte, mte, yte, C = _data(task, backbone, seed)
    set_seed(seed); model = TextLoRA(backbone, C, r=r, freeze_a=freeze_a).to(DEVICE)
    mods = lora_modules(model)
    theta0_tr = trainable_state(model); w0 = lora_weights(model)
    perm = np.random.default_rng(seed).permutation(len(ytr))
    parts = dirichlet_partition(ytr[perm], N, alpha, C, seed)
    parts = [perm[p] for p in parts]
    sizes, client_w = [], []
    for ci in parts:
        if not len(ci): client_w.append(None); sizes.append(0); continue
        load_trainable(model, theta0_tr)
        train_steps(model, idtr[ci], mtr[ci], ytr[ci], K, lr, bs)
        client_w.append(lora_weights(model)); sizes.append(len(ci))
    tot = max(sum(sizes), 1); w = [s / tot for s in sizes]
    rels = []
    for m, names in mods.items():
        An, Bn = names["A"], names["B"]
        A_i = [(cw[An] if cw is not None else w0[An]) for cw in client_w]
        B_i = [(cw[Bn] if cw is not None else w0[Bn]) for cw in client_w]
        Astar = sum(w[i] * A_i[i] for i in range(N))
        Bstar = sum(w[i] * B_i[i] for i in range(N))
        dW_proto = Bstar @ Astar
        dW_ta = sum(w[i] * (B_i[i] @ A_i[i]) for i in range(N))
        rels.append(((dW_proto - dW_ta).norm() / dW_ta.norm().clamp_min(1e-12)).item())
    return float(np.mean(rels))''')

code(r'''# --- run_increment with the freeze_a switch (no public data, base_frac=0) ---
_CENTRAL = {}
def run_increment(task, backbone="roberta_base", N=10, alpha=0.1, seed=42, K=200,
                  lr=5e-4, bs=32, r=8, freeze_a=False):
    idtr, mtr, ytr, idte, mte, yte, C = _data(task, backbone, seed)
    set_seed(seed); model = TextLoRA(backbone, C, r=r, freeze_a=freeze_a).to(DEVICE)
    theta0 = trainable_state(model)
    A0 = evaluate(model, idte, mte, yte); ntr = n_trainable(model)
    perm = np.random.default_rng(seed).permutation(len(ytr))
    parts = [perm[p] for p in dirichlet_partition(ytr[perm], N, alpha, C, seed)]
    deltas, sizes = [], []
    for ci in parts:
        if not len(ci):
            deltas.append({k: torch.zeros_like(v) for k, v in theta0.items()}); sizes.append(0); continue
        load_trainable(model, theta0)
        train_steps(model, idtr[ci], mtr[ci], ytr[ci], K, lr, bs)
        st = trainable_state(model)
        deltas.append({k: st[k] - theta0[k] for k in theta0}); sizes.append(len(ci))
    tot = max(sum(sizes), 1); w = [s / tot for s in sizes]
    agg = {k: theta0[k] + sum(w[i] * deltas[i][k] for i in range(N)) for k in theta0}
    load_trainable(model, agg); Astar = evaluate(model, idte, mte, yte)
    ck = (task, backbone, seed, K, r, freeze_a, lr)
    if ck not in _CENTRAL:
        load_trainable(model, theta0)
        train_steps(model, idtr[perm], mtr[perm], ytr[perm], max(K, N * K // 4), lr, bs)
        _CENTRAL[ck] = evaluate(model, idte, mte, yte)
    Ac = _CENTRAL[ck]
    return dict(A0=round(A0, 4), Astar=round(Astar, 4), A_central=round(Ac, 4),
                gap=round(Ac - Astar, 4), n_trainable=ntr)''')

# ---------------------------------------------------------------------------
md(r"""## Part 2 — fidelity on real fine-tuned adapters

Same relative error, now on adapters produced by actual local fine-tuning
(DBpedia, $N{=}10$, short $K$). both-$A$-$B$ should be far from task arithmetic;
freeze-$A$ should be exact.""")

code(r'''for fa in [False, True]:
    rel = aggregation_fidelity("dbpedia_14", "roberta_base", N=10, alpha=0.1, seed=42,
                               K=100, r=8, freeze_a=fa)
    tag = "freeze-A " if fa else "both-A-B"
    print(f"{tag}: mean relative error  ||dW_proto - dW_TA|| / ||dW_TA|| = {rel:.4f}"
          + ("   <- exact (task arithmetic)" if fa else "   <- NOT task arithmetic"))''')

# ---------------------------------------------------------------------------
md(r"""## Part 3 — accuracy and stability

Three configs across two tasks and three seeds. Watch the **per-config std of
$A^\star$**: both-$A$-$B$ carries the seed-collapse variance; freeze-$A$ should be
tighter and match-or-beat it, while being the only LoRA config whose merge is
provably task arithmetic.""")

code(r'''SEEDS = [42, 43, 44]
CONFIGS = [("head", 0, False), ("lora_AB", 8, False), ("lora_freezeA", 8, True)]
TASKS = ["ag_news", "dbpedia_14"]

rows = []
print("config        task        seed |   A0    A*    Ac    gap")
for task in TASKS:
    for label, r, fa in CONFIGS:
        for s in SEEDS:
            t = time.time()
            o = run_increment(task=task, N=10, alpha=0.1, seed=s, K=200, r=r, freeze_a=fa)
            o.update(config=label, task=task, seed=s, r=r, freeze_a=fa)
            rows.append(o)
            print(f"{label:13s} {task:11s} {s:>4} | {o['A0']:.3f} {o['Astar']:.3f} "
                  f"{o['A_central']:.3f} {o['gap']:.3f}  ({time.time()-t:.0f}s)", flush=True)

print("\n===== per-config summary (mean +/- std of A*) =====")
print("task        config        mean_A*   std_A*   mean_gap")
for task in TASKS:
    for label, r, fa in CONFIGS:
        a = [x["Astar"] for x in rows if x["task"] == task and x["config"] == label]
        g = [x["gap"] for x in rows if x["task"] == task and x["config"] == label]
        print(f"{task:11s} {label:13s} {np.mean(a):.3f}    {np.std(a):.3f}    {np.mean(g):.3f}")

print("\n===== BEGIN results.csv =====")
cols = ["task", "config", "r", "freeze_a", "seed", "A0", "Astar", "A_central", "gap", "n_trainable"]
print(",".join(cols))
for x in rows:
    print(",".join(str(x[c]) for c in cols))
print("===== END results.csv =====")''')

# ---------------------------------------------------------------------------
md(r"""## How to read it

- **Part 1 / Part 2** are the claim, measured: the protocol's factor-averaging
  equals task arithmetic ($\Delta W^\star=\Delta W_{\mathrm{TA}}$) only with
  freeze-$A$ (relative error $\sim 10^{-7}$); both-$A$-$B$ is a different,
  rank-collapsing operation (error $O(1)$).
- **Part 3** is the consequence: if freeze-$A$ matches-or-beats both-$A$-$B$ on
  $A^\star$ with lower seed variance, switch the headline runs to freeze-$A$ — it
  makes the paper's "depth-1 linear $=$ task arithmetic" claim true *and* steadier,
  at half the encrypted payload (only $B$ + head).""")

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
out = Path(__file__).parent / "lora_freeze_survey.ipynb"
out.write_text(json.dumps(nb, indent=1))
print("wrote", out, "with", len(CELLS), "cells")
