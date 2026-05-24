"""Eval helpers: accuracy + per-class accuracy."""
from __future__ import annotations

from typing import Dict, Tuple

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset


@torch.no_grad()
def evaluate_module(m: nn.Module, eval_ds: Dataset, device,
                    batch_size: int = 256) -> Tuple[float, Dict[int, float]]:
    m = m.to(device).eval()
    loader = DataLoader(eval_ds, batch_size=batch_size, shuffle=False,
                        num_workers=2, pin_memory=True)
    correct = 0; total = 0
    pc_correct: Dict[int, int] = {}
    pc_total: Dict[int, int] = {}
    for xb, yb in loader:
        xb = xb.to(device, non_blocking=True)
        yb = yb.to(device, non_blocking=True)
        pred = m(xb).argmax(dim=1)
        correct += (pred == yb).sum().item()
        total += yb.size(0)
        unique_classes = yb.unique().tolist()
        for c in unique_classes:
            mask = (yb == c)
            pc_total[c] = pc_total.get(c, 0) + mask.sum().item()
            pc_correct[c] = pc_correct.get(c, 0) + ((pred == yb) & mask).sum().item()
    per_class = {c: (pc_correct[c] / pc_total[c]) if pc_total[c] > 0 else 0.0
                 for c in pc_total}
    return correct / total, per_class
