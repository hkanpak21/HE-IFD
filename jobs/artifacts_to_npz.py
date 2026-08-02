#!/usr/bin/env python
"""Convert the personal-adapter .pt artifacts to plain .npz for offline analysis.

The selection work needs logits, LABELS, counts and weights -- but no torch and
no GPU. This flattens each artifact into a numpy archive so the analysis runs
anywhere.

The artifacts store holdout *indices* into the train set, not labels, so we
reload each (task, seed) dataset -- deterministic given the seed -- to recover
the holdout labels. Only the label loader is used (no tokenisation).

Usage:  python jobs/artifacts_to_npz.py <artifact_dir> [<artifact_dir> ...]
"""
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import finetune_improve as fi          # noqa: E402
import vision_matched as vm            # noqa: E402

_YTR = {}


def train_labels(task, seed):
    """ytr for a (task, seed), cached. Deterministic given the seed."""
    key = (task, seed)
    if key not in _YTR:
        if task in vm.VDATASETS:
            _, ytr, _, _, _ = vm.load_vision(task, seed=seed)
        else:
            _, ytr, _, _, _ = fi.load_text(task, seed=seed)
        _YTR[key] = np.asarray(ytr)
    return _YTR[key]


def convert(src):
    a = torch.load(src, map_location="cpu", weights_only=False)
    task = str(a.get("task", a.get("dataset")))
    seed = int(a["seed"])
    ytr = train_labels(task, seed)

    out = dict(
        task=task, seed=seed, C=a["C"], N=a["N"], alpha=a["alpha"],
        K=a["K"], r=a["r"],
        counts=np.asarray(a["counts"]), w=np.asarray(a["w"]),
        yte=np.asarray(a["yte"]),
        logits_A_test=a["logits_A_test"].numpy(),
        logits_current_test=a["logits_current_test"].numpy(),
        logits_B_test=np.stack([t.numpy() for t in a["logits_B_test"]]),
        A_test=a["A_test"], B_test=np.asarray(a["B_test"]),
        A_val=np.asarray(a["A_val"]), B_val=np.asarray(a["B_val"]),
        A_bal=np.asarray(a["A_bal"]), B_bal=np.asarray(a["B_bal"]),
        n_clients=len(a["va_parts"]),
    )
    # per-client holdouts are ragged -> one entry each, WITH labels
    for j, (la, lb, vi) in enumerate(zip(a["logits_A_val"], a["logits_B_val"],
                                         a["va_parts"])):
        vi = np.asarray(vi)
        out[f"val_A_{j}"] = la.numpy()
        out[f"val_B_{j}"] = lb.numpy()
        out[f"val_y_{j}"] = ytr[vi]                 # <- actual labels
        out[f"val_idx_{j}"] = vi
    dst = src.with_suffix(".npz")
    np.savez_compressed(dst, **out)
    print(f"{src.name} -> {dst.name}  {dst.stat().st_size/1e6:.1f} MB "
          f"(C={a['C']}, clients={out['n_clients']})", flush=True)


if __name__ == "__main__":
    for d in sys.argv[1:]:
        for src in sorted(Path(d).glob("*.pt")):
            try:
                convert(src)
            except Exception as e:  # noqa: BLE001
                print(f"[FAIL] {src.name}: {type(e).__name__}: {e}", flush=True)
