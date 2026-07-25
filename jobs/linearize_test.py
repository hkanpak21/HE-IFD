#!/usr/bin/env python
"""Linearization test: does a first-order approximation of the INTERNAL LoRA
preserve accuracy?

WHY
---
The Serve protocol (aggregate stays encrypted, never decrypted) needs the client
to run the backbone in PLAINTEXT. An internal-layer LoRA makes the features
depend on the secret adapter, so the exact forward is impossible under
encryption. The only way to keep internal LoRA is:

    client feeds BASE-model activations at every LoRA site
    -> server computes each site's LoRA contribution against Enc(B)
    -> all contributions accumulated and added ONCE at the logits

That is a FIRST-ORDER (linearized) approximation of the true model: it ignores
that the LoRA at layer 3 changes what layer 4 sees. This script measures, in
plaintext, what that approximation costs in accuracy.

    logits_lin = L0 + (L_eps - L0) / eps            (finite-difference JVP)

  L0    = forward with the LoRA displacement OFF, trained head kept
  L_eps = forward with the LoRA displacement scaled by eps

The head is NOT linearized -- it is the final linear map and is applied exactly
(that part is servable at depth 1 either way).

At eps = 1.0 the formula collapses to the true model, so that row is a built-in
self-test: acc_lin MUST equal acc_true there.

DECISION RULE
-------------
  acc_lin ~= acc_true  -> internal LoRA is rescuable under Serve; the
                          0.93 -> 0.78 head-only cliff is avoided.
  acc_lin collapses    -> internal LoRA is dead under Serve; the servable
                          architecture is head-side and we take the cliff.

Usage:  python -m jobs.linearize_test [task ...]
"""
import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import finetune_improve as fi  # noqa: E402

OUTDIR = Path("results") / "linearize_test"
OUTDIR.mkdir(parents=True, exist_ok=True)

TASKS = ["ag_news", "dbpedia_14", "banking77"]
BACKBONE = "roberta_base"
N, ALPHA, SEED, K, LR, BS, R = 10, 0.1, 42, 200, 5e-4, 32, 8
EPS_GRID = [1.0, 0.1, 0.01]          # 1.0 is the exactness self-test
CENTRAL_STEPS = 600


@torch.no_grad()
def logits_of(model, ids, mask, bs=256):
    model.eval()
    out = []
    for s in range(0, len(ids), bs):
        out.append(model(ids[s:s + bs].to(fi.DEVICE),
                         mask[s:s + bs].to(fi.DEVICE)).float().cpu())
    return torch.cat(out)


def scaled_state(state, theta0, eps):
    """Scale the LoRA displacement by eps; keep the head at its trained value."""
    out = {}
    for k, v in state.items():
        if "lora_" in k:
            out[k] = theta0[k] + eps * (v - theta0[k])
        else:
            out[k] = v
    return out


def acc(logits, y):
    return (logits.argmax(1).numpy() == np.asarray(y)).mean().item()


def probe(model, state, theta0, ids, mask, y, tag, task, C, rows):
    """Compare the true forward against the first-order approximation."""
    fi.load_trainable(model, state)
    L_true = logits_of(model, ids, mask)

    fi.load_trainable(model, scaled_state(state, theta0, 0.0))
    L0 = logits_of(model, ids, mask)

    a_true, a_base = acc(L_true, y), acc(L0, y)
    for eps in EPS_GRID:
        fi.load_trainable(model, scaled_state(state, theta0, eps))
        L_eps = logits_of(model, ids, mask)
        L_lin = L0 + (L_eps - L0) / eps
        rel = (L_lin - L_true).norm().item() / max(L_true.norm().item(), 1e-12)
        rows.append(dict(task=task, C=C, model=tag, eps=eps,
                         acc_base=round(a_base, 4), acc_true=round(a_true, 4),
                         acc_lin=round(acc(L_lin, y), 4),
                         rel_logit_err=round(rel, 5),
                         acc_drop=round(a_true - acc(L_lin, y), 4)))
        print(f"  [{tag}] eps={eps:<5} acc_true={a_true:.4f} "
              f"acc_lin={rows[-1]['acc_lin']:.4f} "
              f"drop={rows[-1]['acc_drop']:+.4f} rel_err={rel:.4f}", flush=True)


def run_task(task, rows):
    print(f"\n=== {task} ===", flush=True)
    ids_tr, mask_tr, ytr, ids_te, mask_te, yte, C = fi._data(task, BACKBONE, SEED)

    fi.set_seed(SEED)
    model = fi.TextLoRA(BACKBONE, C, r=R, freeze_a=True).to(fi.DEVICE)
    theta0 = fi.trainable_state(model)

    # --- centralized: the strongest LoRA, hardest case for linearization ---
    fi.load_trainable(model, theta0)
    fi.train_steps(model, ids_tr, mask_tr, ytr, CENTRAL_STEPS, LR, BS)
    probe(model, fi.trainable_state(model), theta0,
          ids_te, mask_te, yte, "central", task, C, rows)

    # --- the one-shot aggregate: what Serve would actually answer from ---
    parts = fi.dirichlet_partition(ytr, N, ALPHA, C, SEED)
    deltas, ws, counts = [], [], []
    for j, idx in enumerate(parts):
        idx = torch.as_tensor(np.asarray(idx), dtype=torch.long)
        fi.load_trainable(model, theta0)
        fi.train_steps(model, ids_tr[idx], mask_tr[idx],
                       np.asarray(ytr)[idx.numpy()], K, LR, BS)
        st = fi.trainable_state(model)
        deltas.append({k: st[k] - theta0[k] for k in st})
        ws.append(len(idx))
        counts.append(np.bincount(np.asarray(ytr)[idx.numpy()], minlength=C))
        print(f"  client {j+1}/{len(parts)} done", flush=True)
    ws = np.asarray(ws, dtype=float)
    ws /= ws.sum()
    agg = fi.agg_count_head(theta0, deltas, ws, counts)
    probe(model, agg, theta0, ids_te, mask_te, yte, "aggregate", task, C, rows)


def main():
    tasks = sys.argv[1:] or TASKS
    rows = []
    for t in tasks:
        try:
            run_task(t, rows)
        except Exception as e:  # keep going; one task failing shouldn't kill the run
            print(f"[FAIL] {t}: {type(e).__name__}: {e}", flush=True)
        (OUTDIR / "linearize.json").write_text(json.dumps(rows, indent=2))

    cols = ["task", "C", "model", "eps", "acc_base", "acc_true", "acc_lin",
            "rel_logit_err", "acc_drop"]
    print("\n" + ",".join(cols))
    for r in rows:
        print(",".join(str(r[c]) for c in cols))


if __name__ == "__main__":
    main()
