"""Generator for notebooks/improve_program.ipynb — the method-improvement program.

ONE merged Run-All notebook (per CLAUDE.md Colab rules) covering the levers
locked on 2026-06-10: freeze-A LoRA, semantic head init, Fisher / count-head
num-denom aggregation, λ grid + client-vote selection, client-side flags
(SWA / prox / logit calibration), rank compensation, and the CIFAR-100/ViT
vision arm. Every results cell prints paste-ready CSV.

The library cell is the TOP of jobs/finetune_improve.py (everything above the
"# ===== CLI (VALAR) =====" marker), embedded verbatim at build time so the
Colab path and the VALAR path cannot drift.

Run: python notebooks/build_improve_nb.py -> notebooks/improve_program.ipynb
"""
import ast
import json
from pathlib import Path

JOB = Path(__file__).parent.parent / "jobs" / "finetune_improve.py"
MARKER = "# ===== CLI (VALAR) ====="
library_src = JOB.read_text().split(MARKER)[0].rstrip() + "\n"
# Drop the shebang + module docstring (the notebook has its own intro cell).
tree = ast.parse(library_src)
first_real = tree.body[1] if (isinstance(tree.body[0], ast.Expr)
                              and isinstance(tree.body[0].value, ast.Constant)) else tree.body[0]
library_src = "\n".join(library_src.splitlines()[first_real.lineno - 1:])

CELLS = []


def md(src):
    CELLS.append(("markdown", src))


def code(src):
    ast.parse(src)
    CELLS.append(("code", src))


# ---------------------------------------------------------------------------
md(r"""# HE-IFD: method-improvement program (freeze-A era)

The improvement levers locked on 2026-06-10, all HE-legal (server = depth-1
linear combiner; client-side work is pre-encryption, candidate selection is
post-decryption among clients, which our threat model permits):

| Section | Lever | Question it answers |
|---|---|---|
| S1 | **freeze-A LoRA** (FFA) | does exact task arithmetic kill the seed collapses? |
| S2 | **semantic head init** | does a zero-shot public θ₀ close the coverage gap? |
| S3 | client-side flags (SWA / prox / calib) | residual variance after S1? |
| S4 | K × lr mini-grid | re-tune the trajectory for the freeze-A config |
| S5 | rank compensation | does r=16/32 recover the capacity frozen with A? |
| S6 | **vision arm** (CIFAR-100 / ViT-B/16) | does the story hold off-text? |

Every cell of S1–S5 also reports, for free, the **aggregation candidates**:
plain λ∈{0.25,…,1}, **Fisher** and **count-head** num/denom merges, and the
**client-vote selected** model — so the aggregation comparison rides along with
whatever else is being measured.

Run-all per section; per-cell JSONs under `results/finetune_improve/` make every
section resumable. Paste each CSV block into
`results/finetune_improve/<section>.csv`. Use a GPU runtime.""")

# ---------------------------------------------------------------------------
code(r"""# ===== Setup =====
import importlib, subprocess, sys
for pkg in ["transformers", "peft", "datasets"]:
    if importlib.util.find_spec(pkg) is None:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", pkg], check=True)
if importlib.util.find_spec("torchao") is not None:        # Colab's old torchao breaks new peft
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "-q", "torchao"], check=False)
    importlib.invalidate_caches()
print("setup ok")""")

# ---------------------------------------------------------------------------
md(r"""## Library

Embedded verbatim from `jobs/finetune_improve.py` (everything above the CLI
marker) — the VALAR job runs the same code.""")

code(library_src)

# ---------------------------------------------------------------------------
md(r"""## VERIFY (run first, ~10 min)

One fast cell (TREC, freeze-A, semantic init). Expect: `A0` **above chance**
(semantic init is zero-shot informative), `A*` well above `A0`, candidates and
the client-vote selection printed.""")

code(r"""v = run_cell("trec", "roberta_base", N=10, alpha=0.1, seed=42, K=200, r=8,
             freeze_a=True, sem_init=True)
print("A0 (zero-shot theta0):  %.3f  (chance 0.167)" % v["A0"])
print("A* (plain lam=1):       %.3f" % v["Astar"])
print("fisher / count_head:    %.3f / %.3f" % (v["acc_fisher"], v["acc_counthead"]))
print("selected by client vote:", v["selected"], "->", v["acc_selected"])
print("A_central (ceiling):    %.3f" % v["A_central"])
print("trainable params:", v["n_trainable"])""")

# ---------------------------------------------------------------------------
md(r"""## S1 — freeze-A vs both-A-B (the linearity fix)

The two seed-unstable tasks (`ag_news`, `trec`), 3 seeds each, both LoRA
configs. The hypothesis: both-A-B collapses (ag_news s44, trec s43) because the
bilinear merge is not task arithmetic; freeze-A is exact and should be stable.
~12 cells. Paste the CSV into `results/finetune_improve/s1_freeze_a.csv`.""")

code(r"""S1 = []
for task in ["ag_news", "trec"]:
    for fa in [True, False]:
        for s in [42, 43, 44]:
            run_resumable(S1, task=task, backbone="roberta_base", N=10, alpha=0.1,
                          seed=s, K=200, r=8, freeze_a=fa)""")

code(r"""print_csv(S1)""")

# ---------------------------------------------------------------------------
md(r"""## S2 — semantic head init (the coverage-gap fix)

All four tasks, freeze-A, 3 seeds, `sem_init=True`. Compare against the
`sem_init=0` rows of S1 / the old E1. The key cell is **banking77** (77 classes,
the 52pp coverage chasm): watch `A0` (zero-shot floor) and `acc_counthead`.
~12 cells. Paste into `results/finetune_improve/s2_sem_init.csv`.""")

code(r"""S2 = []
for task in ["ag_news", "trec", "dbpedia_14", "banking77"]:
    for s in [42, 43, 44]:
        run_resumable(S2, task=task, backbone="roberta_base", N=10, alpha=0.1,
                      seed=s, K=200, r=8, freeze_a=True, sem_init=True)""")

code(r"""print_csv(S2)""")

# ---------------------------------------------------------------------------
md(r"""## S3 — client-side flags (run ONLY if S1 still shows instability)

SWA / proximal pull / logit calibration on `ag_news`, freeze-A, 3 seeds each.
~9 cells. Paste into `results/finetune_improve/s3_flags.csv`.""")

code(r"""S3 = []
for kv in [dict(swa=True), dict(prox_mu=0.01), dict(calib_tau=1.0)]:
    for s in [42, 43, 44]:
        run_resumable(S3, task="ag_news", backbone="roberta_base", N=10, alpha=0.1,
                      seed=s, K=200, r=8, freeze_a=True, **kv)""")

code(r"""print_csv(S3)""")

# ---------------------------------------------------------------------------
md(r"""## S4 — K × lr mini-grid for the freeze-A config

The K=200 / lr=5e-4 defaults were tuned on both-A-B. 6 cells, seed 42 only
(decision cell, not a reporting cell). Paste into
`results/finetune_improve/s4_k_lr.csv`.""")

code(r"""S4 = []
for K in [100, 200, 400]:
    for lr in [5e-4, 1e-3]:
        run_resumable(S4, task="dbpedia_14", backbone="roberta_base", N=10,
                      alpha=0.1, seed=42, K=K, lr=lr, r=8, freeze_a=True)""")

code(r"""print_csv(S4)""")

# ---------------------------------------------------------------------------
md(r"""## S5 — rank compensation on banking77

Freezing A halves trainable capacity; r=16/32 (with semantic init) checks
whether capacity was the binding constraint on the hardest task. Payload at
r=32 freeze-A is still below both-A-B r=16. ~9 cells. Paste into
`results/finetune_improve/s5_rank.csv`.""")

code(r"""S5 = []
for r in [8, 16, 32]:
    for s in [42, 43, 44]:
        run_resumable(S5, task="banking77", backbone="roberta_base", N=10,
                      alpha=0.1, seed=s, K=200, r=r, freeze_a=True, sem_init=True)""")

code(r"""print_csv(S5)""")

# ---------------------------------------------------------------------------
md(r"""## S6 — vision arm: CIFAR-100 with frozen ViT-B/16

Freeze-A LoRA on the attention q,v projections + head, per-batch 32→224 resize.
Plain + count-head candidates (no text-side semantic init for a pure-vision
backbone — noted as the CLIP extension in the paper). ViT at 224 is heavy:
~15–25 min/cell on a T4; r∈{0,8} × 3 seeds ≈ 2h. Paste into
`results/finetune_improve/s6_vision.csv`.""")

code(r'''# ===== Vision library (CIFAR-100 + ViT-LoRA), reuses the agg/candidate code =====
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
        imgs = np.stack([np.array(im.convert("RGB")) for im in sub[img_col]])
        x = torch.from_numpy(imgs).permute(0, 3, 1, 2).contiguous()
        return x, np.array(sub[lbl_col], dtype=np.int64)
    Xtr, ytr = take(ds["train"], max_train)
    Xte, yte = take(ds["test"], max_test)
    return Xtr, ytr, Xte, yte, 100

def prep(x_uint8):
    x = x_uint8.to(DEVICE).float().div_(255.0)
    x = F.interpolate(x, size=224, mode="bilinear", align_corners=False)
    return (x - MEAN.to(DEVICE)) / STD.to(DEVICE)

class ViTLoRA(nn.Module):
    def __init__(self, C, r=8, freeze_a=True):
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
    def forward(self, x):
        out = self.backbone(pixel_values=x).last_hidden_state
        return self.head(out[:, 0])

def v_train(m, X, y, steps, lr, bs):
    m.train(); opt = torch.optim.AdamW([p for p in m.parameters() if p.requires_grad], lr=lr)
    n = len(y); yt = torch.as_tensor(y, device=DEVICE); g = torch.Generator().manual_seed(0)
    for _ in range(max(1, steps)):
        idx = torch.randint(0, n, (min(bs, n),), generator=g)
        loss = F.cross_entropy(m(prep(X[idx])), yt[idx])
        opt.zero_grad(); loss.backward(); opt.step()
    return m

@torch.no_grad()
def v_eval(m, X, y, bs=64):
    m.eval(); n = len(y); yt = torch.as_tensor(y); c = 0
    for s in range(0, n, bs):
        c += (m(prep(X[s:s+bs])).argmax(1).cpu() == yt[s:s+bs]).sum().item()
    return c / max(n, 1)

_VDATA, _VCENTRAL = {}, {}
def run_vision_cell(N=10, alpha=0.1, seed=42, K=200, lr=5e-4, bs=32, r=8,
                    freeze_a=True, lambdas=(0.25, 0.5, 0.75, 1.0)):
    if seed not in _VDATA:
        _VDATA[seed] = load_cifar100(seed=seed)
    Xtr, ytr, Xte, yte, C = _VDATA[seed]
    set_seed(seed); model = ViTLoRA(C, r=r, freeze_a=freeze_a).to(DEVICE)
    theta0 = trainable_state(model)
    A0 = v_eval(model, Xte, yte); ntr = n_trainable(model)
    parts = dirichlet_partition(ytr, N, alpha, C, seed)
    deltas, sizes, cnts = [], [], []
    for ci in parts:
        if not len(ci):
            deltas.append({k: torch.zeros_like(v) for k, v in theta0.items()})
            cnts.append(np.zeros(C)); sizes.append(0); continue
        load_trainable(model, theta0)
        v_train(model, Xtr[ci], ytr[ci], K, lr, bs)
        st = trainable_state(model)
        deltas.append({k: st[k] - theta0[k] for k in theta0})
        cnts.append(np.bincount(ytr[ci], minlength=C).astype(np.float64))
        sizes.append(len(ci))
    tot = max(sum(sizes), 1); w = [s / tot for s in sizes]
    cands = {f"plain_l{lam:g}": agg_plain(theta0, deltas, w, lam=float(lam)) for lam in lambdas}
    cands["count_head"] = agg_count_head(theta0, deltas, w, cnts)
    acc = {}
    for name, st in cands.items():
        load_trainable(model, st); acc[name] = v_eval(model, Xte, yte)
    ck = (seed, K, r, freeze_a, lr)
    if ck not in _VCENTRAL:
        load_trainable(model, theta0)
        v_train(model, Xtr, ytr, max(K, N * K // 4), lr, bs)
        _VCENTRAL[ck] = v_eval(model, Xte, yte)
    Ac = _VCENTRAL[ck]
    lam_best = max((nme for nme in acc if nme.startswith("plain_l")), key=lambda nme: acc[nme])
    Astar = acc["plain_l1"]
    return dict(task="cifar100", backbone="vit_b16", N=N, alpha=alpha, seed=seed,
                K=K, r=r, freeze_a=int(freeze_a), sem_init=0, swa=0, prox_mu=0.0,
                calib_tau=0.0, n_trainable=ntr, A0=round(A0, 4), Astar=round(Astar, 4),
                acc_fisher=float("nan"), acc_counthead=round(acc["count_head"], 4),
                lam_best=float(lam_best.split("plain_l")[1]),
                acc_lam_best=round(acc[lam_best], 4), selected="n/a",
                acc_selected=float("nan"), A_central=round(Ac, 4),
                increment=round(Astar - A0, 4), gap=round(Ac - Astar, 4))''')

code(r"""S6 = []
for r in [0, 8]:
    for s in [42, 43, 44]:
        c = dict(task="cifar100_vit", backbone="vit_b16", N=10, alpha=0.1,
                 seed=s, K=200, r=r, freeze_a=True)
        f = OUTDIR / cell_name(c)
        if f.exists():
            S6.append(json.loads(f.read_text())); print("skip (done):", f.name); continue
        t = time.time()
        row = run_vision_cell(N=10, alpha=0.1, seed=s, K=200, r=r, freeze_a=True)
        row["wall"] = round(time.time() - t, 1)
        f.write_text(json.dumps(row)); S6.append(row)
        print(f"ok cifar100 r={r} s={s} | A0={row['A0']:.3f} A*={row['Astar']:.3f} "
              f"cnt={row['acc_counthead']:.3f} Ac={row['A_central']:.3f} ({row['wall']}s)",
              flush=True)""")

code(r"""print_csv(S6)""")

# ---------------------------------------------------------------------------
md(r"""## S7 — Byzantine-lite robustness via leave-one-out candidates (issue fa04)

One client (the largest shard) submits a crafted displacement (sign-flip / large
Gaussian / label-flip training). The server forms the plain aggregate + all N
leave-one-out aggregates (every one depth-1, public renormalized weights);
clients decrypt all N+1 candidates and vote on local holdouts. Success = the
vote excludes the attacker (`attacker_excluded=1`) and `acc_selected` recovers
toward `acc_oracle` (the attacker-free aggregate). ~18 cells. Paste into
`results/finetune_improve/s7_robust.csv`.""")

code(r"""S7 = []
for task in ["dbpedia_14", "ag_news"]:
    for attack in ["sign_flip", "gauss", "label_flip"]:
        for s in [42, 43, 44]:
            run_robust_resumable(S7, task=task, backbone="roberta_base", N=10,
                                 alpha=0.1, seed=s, K=200, r=8, freeze_a=True,
                                 attack=attack)""")

code(r"""print_csv_robust(S7)""")

# ---------------------------------------------------------------------------
md(r"""## Notes

- **Decision flow**: S1 decides the LoRA config (expect freeze-A). S2 decides
  whether semantic init joins the headline method. The candidate columns decide
  the aggregation rule (expect plain λ=1 near-IID, count-head/λ<1 under skew —
  if plain wins everywhere, that's the measured ablation justifying depth-1
  averaging). S4/S5 set the final hyperparameters; then the full headline grid
  re-runs in the existing sweep with the winning config.
- All candidates are depth-1: fisher/count_head are formed client-side
  pre-encryption (Enc(F⊙Δ), Enc(F)), the server only adds, clients decrypt
  numerator and denominator and divide in plaintext. Client-vote selection is
  post-decryption among clients — admissible because every client receives the
  model anyway under our threat model.
- Clients hold out 10% of their shard for the vote (`val_frac=0.1`), so per-client
  training data is 90% of the E1 runs — internally consistent within this program.
- Paste each section's CSV into `results/finetune_improve/<section>.csv`.""")

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
out = Path(__file__).parent / "improve_program.ipynb"
out.write_text(json.dumps(nb, indent=1))
print("wrote", out, "with", len(CELLS), "cells")
