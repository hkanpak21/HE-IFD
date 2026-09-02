"""Eval: top-1 acc + per-class acc + per-teacher acc."""
from __future__ import annotations
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

from .model import build_model, load_named


@torch.no_grad()
def evaluate_state(state: dict, eval_ds: Dataset, device,
                   arch: str = "mlp",
                   batch_size: int = 512) -> tuple[float, dict[int, float]]:
    m = build_model(arch).to(device); load_named(m, state); m.eval()
    loader = DataLoader(eval_ds, batch_size=batch_size, shuffle=False, num_workers=0)
    correct = 0; total = 0
    pc_correct = {}; pc_total = {}
    for xb, yb in loader:
        xb = xb.to(device); yb = yb.to(device)
        pred = m(xb).argmax(dim=1)
        correct += (pred == yb).sum().item(); total += yb.size(0)
        for c in range(10):
            mask = (yb == c)
            pc_total[c] = pc_total.get(c, 0) + mask.sum().item()
            pc_correct[c] = pc_correct.get(c, 0) + ((pred == yb) & mask).sum().item()
    per_class = {c: (pc_correct[c] / pc_total[c] if pc_total[c] > 0 else 0.0)
                 for c in pc_total}
    return correct / total, per_class


@torch.no_grad()
def evaluate_module(m: nn.Module, eval_ds, device, batch_size: int = 512) -> float:
    m = m.to(device).eval()
    loader = DataLoader(eval_ds, batch_size=batch_size, shuffle=False)
    correct = 0; total = 0
    for xb, yb in loader:
        xb = xb.to(device); yb = yb.to(device)
        pred = m(xb).argmax(dim=1)
        correct += (pred == yb).sum().item(); total += yb.size(0)
    return correct / total
