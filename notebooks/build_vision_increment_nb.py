"""Generator for notebooks/vision_increment.ipynb.

The increment study on vision: CIFAR-100 with a frozen ViT-B/16 backbone, LoRA on
its attention layers + a linear head. Identical method and metrics to the text
notebook (no public data, theta0 = bare backbone + zero LoRA + head; clients
fine-tune K steps; depth-1 weighted-sum aggregate; A0 / A* / A_central). Fills
the CIFAR-100 row of the headline table.

Data path differs from text: 224^2 pixel tensors are too big to precompute, so we
keep CIFAR at 32^2 uint8 (tiny) and resize->normalize per batch on the GPU.

Run: python notebooks/build_vision_increment_nb.py -> notebooks/vision_increment.ipynb
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
md(r"""# HE-IFD vision: the increment on CIFAR-100 (ViT)

Same method as the text notebook, image backbone. $\theta_0$ is the frozen ViT-B/16
with a zero-init LoRA + untrained head (no public data, classifies at chance). Each
client fine-tunes the adapter+head on its private CIFAR-100 shard for $K$ steps; the
server forms $\theta^\star=\theta_0+\sum_j w_j\Delta_j$ (depth-1). We report A0 /
A\* / A_central and the head-vs-LoRA increment, to fill the CIFAR-100 row of the
headline table.

Run-all. VERIFY first (~10 min on a fresh GPU); the program is ~1.5--2 h. Use a GPU
runtime (Runtime -> Change runtime type -> GPU).""")

# ---------------------------------------------------------------------------
code(r"""# ===== Setup =====
import importlib, subprocess, sys
for pkg in ["transformers", "peft", "datasets"]:
    if importlib.util.find_spec(pkg) is None:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", pkg], check=True)
if importlib.util.find_spec("torchao") is not None:        # Colab's old torchao breaks new peft
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "-q", "torchao"], check=False)
    importlib.invalidate_caches()

import os, json, time, random
import numpy as np
import torch, torch.nn as nn, torch.nn.functional as F
from transformers import AutoModel
from peft import LoraConfig, get_peft_model
from datasets import load_dataset

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print("device:", DEVICE)

def set_seed(s):
    random.seed(s); np.random.seed(s); torch.manual_seed(s)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(s)""")

# ---------------------------------------------------------------------------
code(r'''# ===== Library: CIFAR-100 + ViT-LoRA + per-batch image prep =====
VIT = "google/vit-base-patch16-224-in21k"   # ImageNet-21k pretrained ViT-B/16
VIT_TARGETS = ["query", "value"]            # LoRA on the attention q,v projections
MEAN = torch.tensor([0.5, 0.5, 0.5]).view(1, 3, 1, 1)
STD  = torch.tensor([0.5, 0.5, 0.5]).view(1, 3, 1, 1)

def _load_cifar():
    last = None
    for hf in ("uoft-cs/cifar100", "cifar100"):
        try:
            return load_dataset(hf)
        except Exception as e:  # noqa: BLE001
            last = e
    raise last

def load_cifar100(max_train=10000, max_test=2000, seed=0):
    ds = _load_cifar(); rng = np.random.default_rng(seed)
    img_col = "img" if "img" in ds["train"].column_names else "image"
    lbl_col = "fine_label" if "fine_label" in ds["train"].column_names else "label"
    def take(split, n):
        n = min(n, len(split)); idx = rng.choice(len(split), n, replace=False)
        sub = split.select(idx.tolist())
        imgs = np.stack([np.array(im.convert("RGB")) for im in sub[img_col]])  # (n,32,32,3) uint8
        x = torch.from_numpy(imgs).permute(0, 3, 1, 2).contiguous()            # (n,3,32,32) uint8
        return x, np.array(sub[lbl_col], dtype=np.int64)
    Xtr, ytr = take(ds["train"], max_train)
    Xte, yte = take(ds["test"], max_test)
    return Xtr, ytr, Xte, yte, 100

def prep(x_uint8):
    # (B,3,32,32) uint8 -> (B,3,224,224) normalized float, on DEVICE
    x = x_uint8.to(DEVICE).float().div_(255.0)
    x = F.interpolate(x, size=224, mode="bilinear", align_corners=False)
    return (x - MEAN.to(DEVICE)) / STD.to(DEVICE)

class ViTLoRA(nn.Module):
    def __init__(self, C, r=8, freeze_a=False):
        super().__init__()
        base = AutoModel.from_pretrained(VIT)
        hidden = base.config.hidden_size
        for p in base.parameters():
            p.requires_grad = False
        if r > 0:
            base = get_peft_model(base, LoraConfig(r=r, lora_alpha=2 * r, lora_dropout=0.0,
                                  bias="none", target_modules=VIT_TARGETS))
            if freeze_a:
                for n, p in base.named_parameters():
                    if "lora_A" in n:
                        p.requires_grad = False
        self.backbone = base
        self.head = nn.Linear(hidden, C)
    def forward(self, pixel_values):
        out = self.backbone(pixel_values=pixel_values).last_hidden_state
        return self.head(out[:, 0])         # CLS token

def trainable_state(m):
    return {n: p.detach().clone() for n, p in m.named_parameters() if p.requires_grad}
def load_trainable(m, st):
    with torch.no_grad():
        for n, p in m.named_parameters():
            if n in st: p.copy_(st[n].to(p.device))
def n_trainable(m):
    return sum(p.numel() for p in m.parameters() if p.requires_grad)

def train_steps(m, X, y, steps, lr, bs):
    m.train(); opt = torch.optim.AdamW([p for p in m.parameters() if p.requires_grad], lr=lr)
    n = len(y); yt = torch.as_tensor(y, device=DEVICE); g = torch.Generator().manual_seed(0)
    for _ in range(max(1, steps)):
        idx = torch.randint(0, n, (min(bs, n),), generator=g)
        loss = F.cross_entropy(m(prep(X[idx])), yt[idx])
        opt.zero_grad(); loss.backward(); opt.step()
    return m

@torch.no_grad()
def evaluate(m, X, y, bs=64):
    m.eval(); n = len(y); yt = torch.as_tensor(y); c = 0
    for s in range(0, n, bs):
        c += (m(prep(X[s:s+bs])).argmax(1).cpu() == yt[s:s+bs]).sum().item()
    return c / n

def dirichlet_partition(y, N, alpha, C, seed):
    rng = np.random.default_rng(seed); client = [[] for _ in range(N)]
    for c in range(C):
        idx = np.where(y == c)[0]; rng.shuffle(idx)
        if not len(idx): continue
        cuts = (np.cumsum(rng.dirichlet([alpha]*N)) * len(idx)).astype(int)[:-1]
        for i, part in enumerate(np.split(idx, cuts)): client[i].extend(part.tolist())
    return [np.array(c, dtype=np.int64) for c in client]''')

# ---------------------------------------------------------------------------
code(r'''# ===== The federated increment (CIFAR-100), with the freeze_a switch =====
_DATA, _CENTRAL = {}, {}
def _data(seed):
    if seed not in _DATA:
        _DATA[seed] = load_cifar100(seed=seed)
    return _DATA[seed]

def run_increment(N=10, alpha=0.1, seed=42, K=200, lr=5e-4, bs=32, r=8, freeze_a=False):
    Xtr, ytr, Xte, yte, C = _data(seed)
    set_seed(seed); model = ViTLoRA(C, r=r, freeze_a=freeze_a).to(DEVICE)
    theta0 = trainable_state(model)
    A0 = evaluate(model, Xte, yte); ntr = n_trainable(model)
    perm = np.random.default_rng(seed).permutation(len(ytr))
    parts = [perm[p] for p in dirichlet_partition(ytr[perm], N, alpha, C, seed)]
    deltas, sizes = [], []
    for ci in parts:
        if not len(ci):
            deltas.append({k: torch.zeros_like(v) for k, v in theta0.items()}); sizes.append(0); continue
        load_trainable(model, theta0)
        train_steps(model, Xtr[ci], ytr[ci], K, lr, bs)
        st = trainable_state(model)
        deltas.append({k: st[k] - theta0[k] for k in theta0}); sizes.append(len(ci))
    tot = max(sum(sizes), 1); w = [s / tot for s in sizes]
    agg = {k: theta0[k] + sum(w[i] * deltas[i][k] for i in range(N)) for k in theta0}
    load_trainable(model, agg); Astar = evaluate(model, Xte, yte)
    ck = (seed, K, r, freeze_a, lr)
    if ck not in _CENTRAL:
        load_trainable(model, theta0)
        train_steps(model, Xtr[perm], ytr[perm], max(K, N * K // 4), lr, bs)
        _CENTRAL[ck] = evaluate(model, Xte, yte)
    Ac = _CENTRAL[ck]
    return dict(task="cifar100", backbone="vit_b16", N=N, alpha=alpha, seed=seed,
                base_frac=0.0, K=K, r=r, n_trainable=ntr,
                A0=round(A0, 4), Astar=round(Astar, 4), A_central=round(Ac, 4),
                increment=round(Astar - A0, 4), gap=round(Ac - Astar, 4))

RESULTS = {}
CSV_COLS = ["task", "backbone", "N", "alpha", "seed", "base_frac", "K", "r",
            "n_trainable", "A0", "Astar", "A_central", "increment", "gap"]
def do(**c):
    k = (c["N"], c["alpha"], c["seed"], c["K"], c["r"], c.get("freeze_a", False))
    if k in RESULTS: return RESULTS[k]
    t = time.time(); row = run_increment(**c); row["wall"] = round(time.time() - t, 1)
    RESULTS[k] = row
    print(f"  r={c['r']} fa={c.get('freeze_a', False)} seed={c['seed']} | "
          f"A0={row['A0']:.3f} A*={row['Astar']:.3f} Ac={row['A_central']:.3f} "
          f"inc={row['increment']:+.3f} ({row['wall']}s)", flush=True)
    return row
def print_csv():
    print("\n===== BEGIN results.csv =====")
    print(",".join(CSV_COLS))
    for r in RESULTS.values():
        print(",".join(str(r[c]) for c in CSV_COLS))
    print("===== END results.csv =====")''')

# ---------------------------------------------------------------------------
md(r"""## VERIFY (run first, ~10 min)

One config. Expect A\* well above chance (1/100 = 0.01) and below the centralized
ceiling.""")

code(r"""v = run_increment(N=10, alpha=0.1, seed=42, K=200, r=8, freeze_a=False)
print("A0 (theta0, ~chance 0.01): %.3f" % v["A0"])
print("A* (federated LoRA):       %.3f" % v["Astar"])
print("A_central (ceiling):       %.3f" % v["A_central"])
print("trainable params (LoRA+head):", v["n_trainable"])""")

# ---------------------------------------------------------------------------
md(r"""## Headline: head vs LoRA on CIFAR-100

`FREEZE_A=False` matches the current (both-A-B) text headline. Flip it to `True`
once the freeze-A switch is committed across the paper, and re-run.""")

code(r'''FREEZE_A = False          # set True when the paper switches to freeze-A
SEEDS = [42, 43, 44]
for r in [0, 8]:          # head-only vs rank-8 LoRA
    for s in SEEDS:
        do(N=10, alpha=0.1, seed=s, K=200, r=r, freeze_a=FREEZE_A)
print_csv()''')

# ---------------------------------------------------------------------------
md(r"""## Notes

- Paste the CSV into `results/finetune_increment/results.csv` (same schema as the
  text rows) — that fills the CIFAR-100 row of the headline table.
- ViT-B/16 at 224 is heavier than RoBERTa: ~15--25 min/cell on a T4. If memory is
  tight, lower the training `bs` (32) or `max_train` (10000) in the loaders.
- The recipe is identical to text, so the freeze-A argument applies unchanged: with
  both-A-B the LoRA merge is not task arithmetic; set `FREEZE_A=True` for the
  correct, stable version when the rest of the paper switches.""")

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
out = Path(__file__).parent / "vision_increment.ipynb"
out.write_text(json.dumps(nb, indent=1))
print("wrote", out, "with", len(CELLS), "cells")
