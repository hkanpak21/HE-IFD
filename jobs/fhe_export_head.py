#!/usr/bin/env python
"""Export a trained served head, real query features and their plaintext labels.

WHY
---
Every cryptographic benchmark in results/fhe_serve/ runs on synthetic vectors.
The head is a random matrix, the logits are uniform draws, and the top-1/top-2
gap is whatever the seed produced. None of that says the encrypted serving path
answers a real query the way the plaintext model does. This job produces the
input that makes one real query possible: the served head (W, b) rebuilt from a
recorded artifact, a sample of real test features under the same frozen
backbone, and the plaintext argmax the encrypted path has to reproduce.

WHAT IS EXPORTED
----------------
  W, b        the coverage-weighted served head of eq. (1), from head_of()
  features    phi(x) for a random sample of test examples, under the SAME
              backbone the arrangement serves: the bare public backbone for
              arrangement A, client j's own adapter for arrangement B
  logits      W phi(x) + b in float64, and its argmax
  margin      the top-1/top-2 logit gap, which is what the encrypted argmax
              has to resolve
  logit_abs_max  the largest |logit| over the exported queries. The serving
              party's sign circuit is a minimax approximation on [-1,1], so a
              public scale must map the logits into that interval; this is the
              quantity that scale is set from. It is reported, not hidden.

Nothing here is decrypted, encrypted or homomorphic. It is the plaintext half
of the comparison, written as JSON so fhe/serve_real.go can read it with the Go
standard library.

Computing phi(x) needs the backbone, so this is a GPU job.

Usage:  python jobs/fhe_export_head.py [task ...] [seed ...]
Env:    FHE_EXPORT_Q (queries per export, default 16)
        FHE_EXPORT_ARR (arrangements, default "A,B")
        FHE_EXPORT_CLIENT (client whose adapter serves arrangement B, default 0)
"""
import json
import os
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import finetune_improve as fi  # noqa: E402
import personal_adapter_test as pa  # noqa: E402
from extraction_budget import head_of  # noqa: E402
from mia_extracted_head import features_of  # noqa: E402

OUTDIR = Path("results") / "fhe_serve" / "real_query"
ARTDIR = Path("results") / "personal_adapter" / "artifacts"
OUTDIR.mkdir(parents=True, exist_ok=True)

TASKS = ["ag_news"]
SEEDS = [42]
NQ = int(os.environ.get("FHE_EXPORT_Q", 16))
ARRS = [a.strip() for a in os.environ.get("FHE_EXPORT_ARR", "A,B").split(",") if a.strip()]
CLIENT = int(os.environ.get("FHE_EXPORT_CLIENT", 0))


def export(task, seed, arrangement):
    cands = sorted(ARTDIR.glob(f"{task}_N10_a0.1_K200_s{seed}.pt")) or \
            sorted(ARTDIR.glob(f"{task}_s{seed}.pt"))
    if not cands:
        print(f"  [skip] no artifact for {task} s{seed}", flush=True)
        return
    art = torch.load(cands[0], map_location="cpu", weights_only=False)
    C = int(art["C"])

    ids_tr, mask_tr, ytr, ids_te, mask_te, yte, C2 = fi._data(task, pa.BACKBONE, seed)
    assert C2 == C, (C2, C)
    yte = np.asarray(yte)

    tag = "r0" if arrangement == "A" else "r8"
    r = 0 if arrangement == "A" else pa.R
    fi.set_seed(seed)
    model = fi.TextLoRA(pa.BACKBONE, C, r=r, freeze_a=True).to(fi.DEVICE)
    if arrangement == "B":
        fi.load_trainable(model, art[f"states_{tag}"][CLIENT])

    rng = np.random.default_rng(seed * 100 + 1)
    q = rng.choice(len(yte), size=min(NQ, len(yte)), replace=False)
    q = np.sort(q)
    F = features_of(model, ids_te[torch.as_tensor(q, dtype=torch.long)],
                    mask_te[torch.as_tensor(q, dtype=torch.long)])
    del model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    W, b = head_of(art, arrangement)
    logits = F @ W.T + b
    pred = np.argmax(logits, axis=1)
    srt = np.sort(logits, axis=1)
    margin = srt[:, -1] - srt[:, -2]

    queries = []
    for i in range(len(q)):
        queries.append(dict(
            test_index=int(q[i]),
            true_label=int(yte[q[i]]),
            plain_label=int(pred[i]),
            margin=float(margin[i]),
            features=[float(v) for v in F[i]],
            logits=[float(v) for v in logits[i]],
        ))

    out = dict(
        task=task, seed=seed, arrangement=arrangement, backbone=pa.BACKBONE,
        artifact=cands[0].name, client=(CLIENT if arrangement == "B" else -1),
        N=int(art.get("N", 10)), alpha=float(art.get("alpha", 0.1)),
        K=int(art.get("K", 200)), r=r, C=C, d=int(W.shape[1]),
        W=[[float(v) for v in row] for row in W],
        b=[float(v) for v in b],
        logit_abs_max=float(np.abs(logits).max()),
        min_margin=float(margin.min()),
        plain_accuracy=float((pred == yte[q]).mean()),
        queries=queries,
    )
    dst = OUTDIR / f"{task}_s{seed}_{arrangement}.json"
    dst.write_text(json.dumps(out))
    print(f"  {task} s{seed} {arrangement}: C={C} d={W.shape[1]} "
          f"{len(queries)} queries, |logit|max={out['logit_abs_max']:.4f}, "
          f"min margin={out['min_margin']:.4f}, plaintext acc "
          f"{out['plain_accuracy']:.3f} -> {dst} "
          f"({dst.stat().st_size/1e6:.2f} MB)", flush=True)


def main():
    args = sys.argv[1:]
    tasks = [a for a in args if not a.isdigit()] or TASKS
    seeds = [int(a) for a in args if a.isdigit()] or SEEDS
    for task in tasks:
        for seed in seeds:
            for arrangement in ARRS:
                export(task, seed, arrangement)


if __name__ == "__main__":
    main()
