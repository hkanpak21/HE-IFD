#!/usr/bin/env python
"""DP comparator (PI comment, 2026-06): centralized DP-SGD logistic head on the
SAME frozen features HE-IFD uses, at several epsilons. This is the privacy-utility
ceiling for differential privacy on frozen features (Mehta et al. 2211.13403,
Tramer-Boneh 2011.11660 style) -- centralized DP is the *best case* for DP, so if
it cannot reach our accuracy at a given epsilon, no federated DP one-shot method can.

Output point: for each (task, epsilon) the DP test accuracy; the non-private (eps=inf)
head is the ceiling. The paper then shows the HE-IFD released-model accuracy sitting
above the whole DP curve at zero privacy cost.

Reuses the frozen RoBERTa feature path from jobs/finetune_improve.py (same backbone,
same mean-pool, same tasks), then trains a linear head with Opacus DP-SGD on the
POOLED data (centralized). CSV schema:
  task,backbone,n_classes,eps,delta,acc,acc_nonprivate
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "jobs"))

import finetune_improve as FI  # noqa: E402  (load_text, tokenize, mean_pool, BACKBONES)
from transformers import AutoModel  # noqa: E402

CASE = "dp_baseline"
OUTDIR = REPO / "results" / CASE
OUTDIR.mkdir(parents=True, exist_ok=True)

TASKS = ["ag_news", "trec", "dbpedia_14", "banking77"]
EPS_GRID = [1.0, 2.0, 4.0, 8.0]


@torch.no_grad()
def extract_features(task, backbone="roberta_base", seed=42, bs=64):
    """Frozen mean-pooled features for the full train/test split (cached)."""
    cache = OUTDIR / f"feat_{task}_{backbone}_s{seed}.pt"
    if cache.exists():
        d = torch.load(cache)
        return d["Xtr"], d["ytr"], d["Xte"], d["yte"], d["C"]
    Xtr_txt, ytr, Xte_txt, yte, C = FI.load_text(task, seed=seed)
    model = AutoModel.from_pretrained(FI.BACKBONES[backbone]["hf"]).to(FI.DEVICE).eval()

    def feats(texts):
        ids, mask = FI.tokenize(backbone, texts)
        out = []
        for i in range(0, len(ids), bs):
            o = model(input_ids=ids[i:i + bs].to(FI.DEVICE),
                      attention_mask=mask[i:i + bs].to(FI.DEVICE)).last_hidden_state
            out.append(FI.mean_pool(o, mask[i:i + bs].to(FI.DEVICE)).cpu())
        return torch.cat(out)

    Xtr, Xte = feats(Xtr_txt), feats(Xte_txt)
    ytr_t = torch.as_tensor(ytr, dtype=torch.long)
    yte_t = torch.as_tensor(yte, dtype=torch.long)
    torch.save({"Xtr": Xtr, "ytr": ytr_t, "Xte": Xte, "yte": yte_t, "C": C}, cache)
    del model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return Xtr, ytr_t, Xte, yte_t, C


def train_head(Xtr, ytr, Xte, yte, C, eps=None, epochs=20, lr=0.5, bs=256,
               delta=1e-5, max_grad_norm=1.0):
    """Train a linear head; if eps is not None, with Opacus DP-SGD (target eps)."""
    dev = FI.DEVICE
    head = nn.Linear(Xtr.shape[1], C).to(dev)
    opt = torch.optim.SGD(head.parameters(), lr=lr, momentum=0.0)
    loader = DataLoader(TensorDataset(Xtr, ytr), batch_size=bs, shuffle=True)

    if eps is not None:
        from opacus import PrivacyEngine
        pe = PrivacyEngine()
        head, opt, loader = pe.make_private_with_epsilon(
            module=head, optimizer=opt, data_loader=loader,
            target_epsilon=eps, target_delta=delta, epochs=epochs,
            max_grad_norm=max_grad_norm)

    lossf = nn.CrossEntropyLoss()
    head.train()
    for _ in range(epochs):
        for xb, yb in loader:
            opt.zero_grad()
            loss = lossf(head(xb.to(dev)), yb.to(dev))
            loss.backward(); opt.step()

    head.eval()
    with torch.no_grad():
        pred = head(Xte.to(dev)).argmax(1).cpu()
    return (pred == yte).float().mean().item()


def run_task(task, backbone="roberta_base", epochs=20):
    cell = OUTDIR / f"cell_{task}_{backbone}.json"
    if cell.exists():
        row = json.loads(cell.read_text())
        print(f"skip (done): {cell.name}", flush=True)
        return row
    t = time.time()
    Xtr, ytr, Xte, yte, C = extract_features(task, backbone)
    # standardize features (matters a lot for DP-SGD on features; arXiv:2307.11106)
    mu, sd = Xtr.mean(0, keepdim=True), Xtr.std(0, keepdim=True).clamp_min(1e-6)
    Xtr, Xte = (Xtr - mu) / sd, (Xte - mu) / sd

    acc_np = train_head(Xtr, ytr, Xte, yte, C, eps=None, epochs=epochs)
    accs = {}
    for eps in EPS_GRID:
        accs[eps] = train_head(Xtr, ytr, Xte, yte, C, eps=eps, epochs=epochs)
        print(f"  {task} eps={eps}: acc={accs[eps]:.4f}", flush=True)

    row = dict(task=task, backbone=backbone, n_classes=C, delta=1e-5,
               acc_nonprivate=round(acc_np, 4),
               acc_by_eps={str(k): round(v, 4) for k, v in accs.items()},
               wall=round(time.time() - t, 1))
    cell.write_text(json.dumps(row))
    print(f"ok {task} | nonpriv={acc_np:.3f} "
          + " ".join(f"e{int(k)}={v:.3f}" for k, v in accs.items())
          + f" ({row['wall']}s)", flush=True)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=20)
    args = ap.parse_args()
    print(f"[dp_baseline] device={FI.DEVICE}", flush=True)
    rows = []
    for task in TASKS:
        try:
            rows.append(run_task(task, epochs=args.epochs))
        except Exception as e:  # noqa: BLE001
            import traceback
            (OUTDIR / f"FAIL_{task}.txt").write_text(traceback.format_exc())
            print(f"FAIL {task}: {e}", flush=True)

    print("\n===== BEGIN results.csv =====", flush=True)
    print("task,backbone,n_classes,eps,delta,acc,acc_nonprivate")
    for r in rows:
        for eps, acc in r["acc_by_eps"].items():
            print(f"{r['task']},{r['backbone']},{r['n_classes']},{eps},"
                  f"{r['delta']},{acc},{r['acc_nonprivate']}")
    print("===== END results.csv =====\n", flush=True)


if __name__ == "__main__":
    main()
