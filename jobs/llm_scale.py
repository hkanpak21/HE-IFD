#!/usr/bin/env python
"""fa03 — LLM-scale feasibility cell: one-shot freeze-A LoRA federation on a
sub-billion/billion-class causal LM (default Qwen2.5-0.5B; TinyLlama-1.1B via
--backbone if memory allows).

Feasibility demonstration, not a grid: does the one-shot merge hold when the
frozen backbone is a causal LM at 0.5–1B parameters? Mirrors the
finetune_improve cell (same partition, K-step trajectories, depth-1 candidate
set, client-vote selection) with the two causal-LM specifics:

  * LEFT padding + last-token pooling (a causal token only sees its past — the
    repo's GPT-2 lesson; mean-pooling a right-padded causal LM pins at chance).
  * fp32 LoRA(+head) on a frozen fp32 backbone with gradient checkpointing —
    slow but numerically boring on a T4.

Imports the federated core from jobs/finetune_improve.py so aggregation and
candidates are byte-identical to the headline method.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "jobs"))

import finetune_improve as FI  # noqa: E402
from transformers import AutoModel, AutoTokenizer  # noqa: E402
from peft import LoraConfig, get_peft_model  # noqa: E402

CASE = "llm_scale"
OUTDIR = REPO / "results" / CASE
OUTDIR.mkdir(parents=True, exist_ok=True)

LLM_BACKBONES = {
    "qwen25_05b":  dict(hf="Qwen/Qwen2.5-0.5B", targets=["q_proj", "v_proj"]),
    "tinyllama":   dict(hf="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                        targets=["q_proj", "v_proj"]),
}

_TOK = {}
def tok_left(backbone, texts, max_len=128):
    """Causal-LM tokenization: LEFT padding so position -1 is a real token."""
    if backbone not in _TOK:
        t = AutoTokenizer.from_pretrained(LLM_BACKBONES[backbone]["hf"])
        if t.pad_token is None:
            t.pad_token = t.eos_token
        t.padding_side = "left"
        _TOK[backbone] = t
    enc = _TOK[backbone](texts, padding="max_length", truncation=True,
                         max_length=max_len, return_tensors="pt")
    return enc["input_ids"], enc["attention_mask"]


class CausalLoRA(nn.Module):
    """Frozen causal LM + freeze-A LoRA on q/v projections + linear head on the
    last real token's hidden state. Trainable tensors: lora_B.* + head.*, so
    the displacement/aggregation path is identical to TextLoRA's."""
    def __init__(self, backbone, C, r=8, freeze_a=True):
        super().__init__()
        cfg = LLM_BACKBONES[backbone]
        base = AutoModel.from_pretrained(cfg["hf"])
        base.gradient_checkpointing_enable()
        hidden = base.config.hidden_size
        for p in base.parameters():
            p.requires_grad = False
        if r > 0:
            base = get_peft_model(base, LoraConfig(
                r=r, lora_alpha=2 * r, lora_dropout=0.0, bias="none",
                target_modules=cfg["targets"]))
            if freeze_a:
                for n, p in base.named_parameters():
                    if "lora_A" in n:
                        p.requires_grad = False
        self.backbone = base
        self.head = nn.Linear(hidden, C)

    def forward(self, ids, mask):
        out = self.backbone(input_ids=ids, attention_mask=mask).last_hidden_state
        return self.head(out[:, -1, :])    # left-pad ⇒ -1 is the last real token


def run_llm_cell(task, backbone, N=10, alpha=0.1, seed=42, K=200, lr=5e-4,
                 bs=8, r=8, freeze_a=True, lambdas=(0.5, 0.75, 1.0),
                 val_frac=0.1, max_train=8000, max_test=2000):
    cell = OUTDIR / (f"cell_{task}_{backbone}_N{N}_a{alpha}_s{seed}"
                     f"_K{K}_r{r}_fa{int(freeze_a)}.json")
    if cell.exists():
        row = json.loads(cell.read_text())
        print(f"skip (done): {cell.name}", flush=True)
        return row

    Xtr, ytr, Xte, yte, C = FI.load_text(task, max_train=max_train,
                                         max_test=max_test, seed=seed)
    ids_tr, mask_tr = tok_left(backbone, Xtr)
    ids_te, mask_te = tok_left(backbone, Xte)

    t0 = time.time()
    FI.set_seed(seed)
    model = CausalLoRA(backbone, C, r=r, freeze_a=freeze_a).to(FI.DEVICE)
    theta0 = FI.trainable_state(model)
    A0 = FI.evaluate(model, ids_te, mask_te, yte)
    ntrain = FI.n_trainable(model)

    parts = FI.dirichlet_partition(ytr, N, alpha, C, seed)
    rng = np.random.default_rng(seed + 1)
    deltas, sizes, counts, vals, client_wall = [], [], [], [], []
    for ci in parts:
        if len(ci) == 0:
            deltas.append({k: torch.zeros_like(v) for k, v in theta0.items()})
            counts.append(np.zeros(C)); sizes.append(0)
            vals.append(np.array([], dtype=np.int64)); continue
        ci = rng.permutation(ci)
        nv = int(val_frac * len(ci)) if len(ci) >= 20 else 0
        val_idx, tr_idx = ci[:nv], ci[nv:]
        tc = time.time()
        FI.load_trainable(model, theta0)
        FI.train_steps(model, ids_tr[tr_idx], mask_tr[tr_idx], ytr[tr_idx],
                       steps=K, lr=lr, bs=bs)
        client_wall.append(round(time.time() - tc, 1))
        st = FI.trainable_state(model)
        deltas.append({k: st[k] - theta0[k] for k in theta0})
        counts.append(np.bincount(ytr[tr_idx], minlength=C).astype(np.float64))
        sizes.append(int(len(tr_idx))); vals.append(val_idx)

    tot = max(sum(sizes), 1); w = [s / tot for s in sizes]
    cands = {f"plain_l{lam:g}": FI.agg_plain(theta0, deltas, w, lam=float(lam))
             for lam in lambdas}
    cands["count_head"] = FI.agg_count_head(theta0, deltas, w, counts)

    test_acc = {}
    for name, st in cands.items():
        FI.load_trainable(model, st)
        test_acc[name] = FI.evaluate(model, ids_te, mask_te, yte)

    votes = {name: 0.0 for name in cands}
    vtot = 0.0
    for i, vi in enumerate(vals):
        if len(vi) == 0:
            continue
        for name, st in cands.items():
            FI.load_trainable(model, st)
            votes[name] += sizes[i] * FI.evaluate(model, ids_tr[vi],
                                                  mask_tr[vi], ytr[vi])
        vtot += sizes[i]
    selected = max(votes, key=lambda nme: votes[nme]) if vtot > 0 else "plain_l1"

    FI.load_trainable(model, theta0)
    FI.train_steps(model, ids_tr, mask_tr, ytr, steps=max(K, N * K // 4),
                   lr=lr, bs=bs)
    A_central = FI.evaluate(model, ids_te, mask_te, yte)

    n_ct = int(np.ceil(ntrain / 8192))      # CKKS ring 2^14 → 8192 slots/ct
    row = dict(task=task, backbone=backbone, N=N, alpha=alpha, seed=seed,
               K=K, r=r, freeze_a=int(freeze_a), n_trainable=ntrain,
               ciphertexts=n_ct, A0=round(A0, 4),
               Astar=round(test_acc["plain_l1"], 4),
               acc_counthead=round(test_acc["count_head"], 4),
               selected=selected, acc_selected=round(test_acc[selected], 4),
               A_central=round(A_central, 4),
               increment=round(test_acc["plain_l1"] - A0, 4),
               gap=round(A_central - test_acc[selected], 4),
               client_wall_s=client_wall, wall=round(time.time() - t0, 1),
               test_acc_all={k: round(v, 4) for k, v in test_acc.items()})
    cell.write_text(json.dumps(row))
    print(f"ok {task} {backbone} s={seed} | A0={A0:.3f} A*={row['Astar']:.3f} "
          f"cnt={row['acc_counthead']:.3f} sel={selected}:{row['acc_selected']:.3f} "
          f"Ac={A_central:.3f} | {ntrain} params = {n_ct} cts "
          f"({row['wall']}s)", flush=True)
    return row


CSV_COLS = ["task", "backbone", "N", "alpha", "seed", "K", "r", "freeze_a",
            "n_trainable", "ciphertexts", "A0", "Astar", "acc_counthead",
            "selected", "acc_selected", "A_central", "increment", "gap", "wall"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backbone", default="qwen25_05b",
                    choices=list(LLM_BACKBONES))
    ap.add_argument("--bs", type=int, default=8)
    args = ap.parse_args()

    print(f"[llm_scale] device={FI.DEVICE} backbone={args.backbone}", flush=True)
    rows = []
    for task in ["ag_news", "dbpedia_14"]:
        for seed in [42, 43]:
            try:
                rows.append(run_llm_cell(task, args.backbone, seed=seed,
                                         bs=args.bs))
            except Exception as e:  # noqa: BLE001
                import traceback
                (OUTDIR / f"FAIL_{task}_{args.backbone}_s{seed}.txt").write_text(
                    traceback.format_exc())
                print(f"FAIL {task} s{seed}: {e}", flush=True)

    print("\n===== BEGIN results.csv =====", flush=True)
    print(",".join(CSV_COLS))
    for r in rows:
        print(",".join(str(r[c]) for c in CSV_COLS))
    print("===== END results.csv =====\n", flush=True)


if __name__ == "__main__":
    main()
