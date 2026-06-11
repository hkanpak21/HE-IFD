#!/usr/bin/env python
"""fa05 + s6 — vision arm and matched-setup comparator cells (ViT-B/16).

Runs the freeze-A method (frozen ViT-B/16 + freeze-A LoRA r=8 + head, K-step
trajectories, depth-1 candidates {plain λ, fisher, count_head} + client-vote
selection) at the PUBLISHED setups of the comparator papers, so the comparison
table can place our number beside theirs at THEIR partition (repo rule: never
re-run vendor code).

Stages (array index):
  0  s6        CIFAR-100, N=10, α=0.1            (the fa01 vision arm)
  1  dense     CIFAR-10,  N=5,  α∈{0.1, 0.3}     (DENSE NeurIPS'22 Table 1;
                                                   α=0.1 row also ~ Co-Boosting)
  2  fedaux    CIFAR-10,  N=20, α∈{0.04, 0.16}   (FedAUXfdp IJCAI-W'22 grid)
  3  fedsd2c   Tiny-ImageNet, N=10, α∈{0.1, 0.3} (FedSD2C NeurIPS'24)

Documented deviation (per fa05 brief): the model class is ours (frozen
pretrained ViT + adapter), not theirs (ResNet-18 / ShuffleNet from scratch) —
the controlled axes are dataset, client count, and the Dirichlet partition.
The published numbers quoted beside ours come verbatim from
comparators/REPORTED_RESULTS.md.

Imports the aggregation/candidate core from jobs/finetune_improve.py so the
combine path is byte-identical to the text headline.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "jobs"))

import finetune_improve as FI  # noqa: E402
from transformers import AutoModel  # noqa: E402
from peft import LoraConfig, get_peft_model  # noqa: E402
from datasets import load_dataset  # noqa: E402

CASE = "vision_matched"
OUTDIR = REPO / "results" / CASE
OUTDIR.mkdir(parents=True, exist_ok=True)

VIT = "google/vit-base-patch16-224-in21k"
VIT_TARGETS = ["query", "value"]
MEAN = torch.tensor([0.5, 0.5, 0.5]).view(1, 3, 1, 1)
STD = torch.tensor([0.5, 0.5, 0.5]).view(1, 3, 1, 1)

VDATASETS = {
    "cifar10":  dict(hf=("uoft-cs/cifar10", "cifar10"), C=10),
    "cifar100": dict(hf=("uoft-cs/cifar100", "cifar100"), C=100),
    "tiny_imagenet": dict(hf=("zh-plus/tiny-imagenet",), C=200),
}


def load_vision(slug, max_train=10000, max_test=2000, seed=0):
    cfg = VDATASETS[slug]
    last = None
    for hf in cfg["hf"]:
        try:
            ds = load_dataset(hf); break
        except Exception as e:  # noqa: BLE001
            last = e
    else:
        raise last
    test_split = "test" if "test" in ds else "valid"
    rng = np.random.default_rng(seed)
    cols = ds["train"].column_names
    img_col = "img" if "img" in cols else "image"
    lbl_col = ("fine_label" if "fine_label" in cols
               else "label" if "label" in cols else "labels")

    def take(split, n):
        n = min(n, len(split))
        idx = rng.choice(len(split), n, replace=False)
        sub = split.select(idx.tolist())
        imgs = np.stack([np.array(im.convert("RGB")) for im in sub[img_col]])
        x = torch.from_numpy(imgs).permute(0, 3, 1, 2).contiguous()  # uint8
        return x, np.array(sub[lbl_col], dtype=np.int64)

    Xtr, ytr = take(ds["train"], max_train)
    Xte, yte = take(ds[test_split], max_test)
    return Xtr, ytr, Xte, yte, cfg["C"]


def prep(x_uint8):
    x = x_uint8.to(FI.DEVICE).float().div_(255.0)
    x = F.interpolate(x, size=224, mode="bilinear", align_corners=False)
    return (x - MEAN.to(FI.DEVICE)) / STD.to(FI.DEVICE)


class ViTLoRA(nn.Module):
    def __init__(self, C, r=8, freeze_a=True):
        super().__init__()
        base = AutoModel.from_pretrained(VIT)
        hidden = base.config.hidden_size
        for p in base.parameters():
            p.requires_grad = False
        if r > 0:
            base = get_peft_model(base, LoraConfig(
                r=r, lora_alpha=2 * r, lora_dropout=0.0, bias="none",
                target_modules=VIT_TARGETS))
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
    m.train()
    opt = torch.optim.AdamW([p for p in m.parameters() if p.requires_grad], lr=lr)
    n = len(y); yt = torch.as_tensor(y, device=FI.DEVICE)
    g = torch.Generator().manual_seed(0)
    for _ in range(max(1, steps)):
        idx = torch.randint(0, n, (min(bs, n),), generator=g)
        loss = F.cross_entropy(m(prep(X[idx])), yt[idx])
        opt.zero_grad(); loss.backward(); opt.step()
    return m


@torch.no_grad()
def v_eval(m, X, y, bs=64):
    m.eval()
    n = len(y); yt = torch.as_tensor(y); c = 0
    for s in range(0, n, bs):
        c += (m(prep(X[s:s + bs])).argmax(1).cpu() == yt[s:s + bs]).sum().item()
    return c / max(n, 1)


def v_fisher(m, X, y, bs, batches=8):
    m.train()
    n = len(y); yt = torch.as_tensor(y, device=FI.DEVICE)
    g = torch.Generator().manual_seed(1)
    fis = {nme: torch.zeros_like(p) for nme, p in m.named_parameters()
           if p.requires_grad}
    for _ in range(batches):
        idx = torch.randint(0, n, (min(bs, n),), generator=g)
        loss = F.cross_entropy(m(prep(X[idx])), yt[idx])
        m.zero_grad(); loss.backward()
        for nme, p in m.named_parameters():
            if p.requires_grad and p.grad is not None:
                fis[nme] += p.grad.detach() ** 2
    m.zero_grad()
    tot = sum(f.sum().item() for f in fis.values())
    cnt = sum(f.numel() for f in fis.values())
    scale = tot / max(cnt, 1)
    return {k: v / max(scale, 1e-12) for k, v in fis.items()}


_VDATA, _VCENTRAL = {}, {}
def run_vcell(dataset, match, N, alpha, seed, K=200, lr=5e-4, bs=32, r=8,
              freeze_a=True, lambdas=(0.5, 0.75, 1.0), val_frac=0.1):
    cell = OUTDIR / (f"cell_{dataset}_{match}_N{N}_a{alpha}_s{seed}"
                     f"_K{K}_r{r}_fa{int(freeze_a)}.json")
    if cell.exists():
        row = json.loads(cell.read_text())
        print(f"skip (done): {cell.name}", flush=True)
        return row

    dk = (dataset, seed)
    if dk not in _VDATA:
        _VDATA[dk] = load_vision(dataset, seed=seed)
    Xtr, ytr, Xte, yte, C = _VDATA[dk]

    t0 = time.time()
    FI.set_seed(seed)
    model = ViTLoRA(C, r=r, freeze_a=freeze_a).to(FI.DEVICE)
    theta0 = FI.trainable_state(model)
    A0 = v_eval(model, Xte, yte)
    ntrain = FI.n_trainable(model)

    parts = FI.dirichlet_partition(ytr, N, alpha, C, seed)
    rng = np.random.default_rng(seed + 1)
    deltas, sizes, fishers, counts, vals = [], [], [], [], []
    for ci in parts:
        if len(ci) == 0:
            deltas.append({k: torch.zeros_like(v) for k, v in theta0.items()})
            fishers.append({k: torch.zeros_like(v) for k, v in theta0.items()})
            counts.append(np.zeros(C)); sizes.append(0)
            vals.append(np.array([], dtype=np.int64)); continue
        ci = rng.permutation(ci)
        nv = int(val_frac * len(ci)) if len(ci) >= 20 else 0
        val_idx, tr_idx = ci[:nv], ci[nv:]
        FI.load_trainable(model, theta0)
        v_train(model, Xtr[tr_idx], ytr[tr_idx], K, lr, bs)
        st = FI.trainable_state(model)
        deltas.append({k: st[k] - theta0[k] for k in theta0})
        fishers.append(v_fisher(model, Xtr[tr_idx], ytr[tr_idx], bs))
        counts.append(np.bincount(ytr[tr_idx], minlength=C).astype(np.float64))
        sizes.append(int(len(tr_idx))); vals.append(val_idx)

    tot = max(sum(sizes), 1); w = [s / tot for s in sizes]
    cands = {f"plain_l{lam:g}": FI.agg_plain(theta0, deltas, w, lam=float(lam))
             for lam in lambdas}
    cands["fisher"] = FI.agg_fisher(theta0, deltas, w, fishers)
    cands["count_head"] = FI.agg_count_head(theta0, deltas, w, counts)

    test_acc = {}
    for name, st in cands.items():
        FI.load_trainable(model, st)
        test_acc[name] = v_eval(model, Xte, yte)

    votes = {name: 0.0 for name in cands}
    vtot = 0.0
    for i, vi in enumerate(vals):
        if len(vi) == 0:
            continue
        for name, st in cands.items():
            FI.load_trainable(model, st)
            votes[name] += sizes[i] * v_eval(model, Xtr[vi], ytr[vi])
        vtot += sizes[i]
    selected = max(votes, key=lambda nme: votes[nme]) if vtot > 0 else "plain_l1"

    ck = (dataset, seed, K, r, freeze_a)
    if ck not in _VCENTRAL:
        FI.load_trainable(model, theta0)
        v_train(model, Xtr, ytr, max(K, N * K // 4), lr, bs)
        _VCENTRAL[ck] = v_eval(model, Xte, yte)
    Ac = _VCENTRAL[ck]

    row = dict(dataset=dataset, match=match, backbone="vit_b16", N=N,
               alpha=alpha, seed=seed, K=K, r=r, freeze_a=int(freeze_a),
               n_trainable=ntrain, A0=round(A0, 4),
               Astar=round(test_acc["plain_l1"], 4),
               acc_fisher=round(test_acc["fisher"], 4),
               acc_counthead=round(test_acc["count_head"], 4),
               selected=selected, acc_selected=round(test_acc[selected], 4),
               A_central=round(Ac, 4),
               gap=round(Ac - test_acc[selected], 4),
               wall=round(time.time() - t0, 1),
               test_acc_all={k: round(v, 4) for k, v in test_acc.items()})
    cell.write_text(json.dumps(row))
    print(f"ok {dataset} {match} N={N} a={alpha} s={seed} | A0={A0:.3f} "
          f"A*={row['Astar']:.3f} fis={row['acc_fisher']:.3f} "
          f"cnt={row['acc_counthead']:.3f} sel={selected}:{row['acc_selected']:.3f} "
          f"Ac={Ac:.3f} ({row['wall']}s)", flush=True)
    return row


CSV_COLS = ["dataset", "match", "backbone", "N", "alpha", "seed", "K", "r",
            "freeze_a", "n_trainable", "A0", "Astar", "acc_fisher",
            "acc_counthead", "selected", "acc_selected", "A_central", "gap"]

STAGES = {
    "s6":      [("cifar100", "s6_vision_arm", 10, a, s)
                for a in [0.1] for s in [42, 43, 44]],
    "dense":   [("cifar10", "dense_n5", 5, a, s)
                for a in [0.1, 0.3] for s in [42, 43, 44]],
    "fedaux":  [("cifar10", "fedauxfdp_n20", 20, a, s)
                for a in [0.04, 0.16] for s in [42, 43, 44]],
    "fedsd2c": [("tiny_imagenet", "fedsd2c_n10", 10, a, s)
                for a in [0.1, 0.3] for s in [42, 43, 44]],
}
STAGE_ORDER = ["s6", "dense", "fedaux", "fedsd2c"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True,
                    help="s6|dense|fedaux|fedsd2c or an integer array index")
    ap.add_argument("--bs", type=int, default=32)
    args = ap.parse_args()
    stage = (STAGE_ORDER[int(args.stage)] if args.stage.isdigit()
             else args.stage)

    cells = STAGES[stage]
    print(f"[vision_matched:{stage}] device={FI.DEVICE} cells={len(cells)}",
          flush=True)
    rows = []
    for dataset, match, N, alpha, seed in cells:
        try:
            rows.append(run_vcell(dataset, match, N, alpha, seed, bs=args.bs))
        except Exception as e:  # noqa: BLE001
            import traceback
            (OUTDIR / f"FAIL_{dataset}_{match}_a{alpha}_s{seed}.txt").write_text(
                traceback.format_exc())
            print(f"FAIL {dataset} {match} a={alpha} s={seed}: {e}", flush=True)

    print(f"\n===== BEGIN results.csv ({stage}) =====", flush=True)
    print(",".join(CSV_COLS))
    for r in rows:
        print(",".join(str(r[c]) for c in CSV_COLS))
    print("===== END results.csv =====\n", flush=True)


if __name__ == "__main__":
    main()
