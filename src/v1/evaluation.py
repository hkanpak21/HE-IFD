"""Evaluation helpers for v1: student accuracy, mean-teacher accuracy."""
from __future__ import annotations

from typing import Dict, List

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

from .model import build_mlp, load_named_state


@torch.no_grad()
def evaluate_state(state: Dict[str, torch.Tensor], eval_ds: Dataset, device: str, batch_size: int = 256) -> float:
    model = build_mlp().to(device)
    load_named_state(model, state)
    model.eval()
    loader = DataLoader(eval_ds, batch_size=batch_size, shuffle=False, num_workers=0)
    correct, total = 0, 0
    for xb, yb in loader:
        xb, yb = xb.to(device), yb.to(device)
        pred = model(xb).argmax(dim=1)
        correct += (pred == yb).sum().item()
        total += yb.size(0)
    return correct / max(total, 1)


@torch.no_grad()
def evaluate_model(model: nn.Module, eval_ds: Dataset, device: str, batch_size: int = 256) -> float:
    model.eval()
    loader = DataLoader(eval_ds, batch_size=batch_size, shuffle=False, num_workers=0)
    correct, total = 0, 0
    for xb, yb in loader:
        xb, yb = xb.to(device), yb.to(device)
        pred = model(xb).argmax(dim=1)
        correct += (pred == yb).sum().item()
        total += yb.size(0)
    return correct / max(total, 1)


def mean_teacher_acc(teachers: List[nn.Module], eval_ds: Dataset, device: str) -> tuple[float, List[float]]:
    accs = [evaluate_model(t, eval_ds, device) for t in teachers]
    return (sum(accs) / max(len(accs), 1)), accs
