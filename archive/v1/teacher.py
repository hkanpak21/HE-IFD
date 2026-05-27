"""Client teacher training + cache.

Cache key: (dataset, N, alpha, seed, client_i). Reused across methods so
Co-Boosting / FedMD baselines (later) start from byte-identical teachers.
"""
from __future__ import annotations

from pathlib import Path
from typing import List

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Subset

from .model import build_mlp


def teacher_cache_path(cache_root: str, dataset: str, N: int, alpha: float, seed: int, client_i: int) -> Path:
    return Path(cache_root) / "teachers" / f"{dataset}_N{N}_a{alpha}_s{seed}" / f"client_{client_i}.pt"


def train_teacher(
    client_subset: Subset,
    n_classes: int,
    *,
    epochs: int = 30,
    batch_size: int = 64,
    lr: float = 1e-2,
    momentum: float = 0.9,
    device: str = "cpu",
    seed: int | None = None,
) -> nn.Module:
    if seed is not None:
        torch.manual_seed(seed)
    model = build_mlp(input_dim=784, num_classes=n_classes).to(device)
    if len(client_subset) == 0:
        # Pathological partition: client got zero samples. Return the untrained
        # init; downstream code records the diagnostic.
        return model
    loader = DataLoader(client_subset, batch_size=batch_size, shuffle=True, num_workers=0)
    opt = optim.SGD(model.parameters(), lr=lr, momentum=momentum)
    crit = nn.CrossEntropyLoss()
    model.train()
    for _ in range(epochs):
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad()
            loss = crit(model(xb), yb)
            loss.backward()
            opt.step()
    return model


def get_or_train_teacher(
    cache_root: str,
    dataset: str,
    N: int,
    alpha: float,
    seed: int,
    client_i: int,
    client_subset: Subset,
    n_classes: int,
    device: str,
    epochs: int,
    train_seed: int,
) -> nn.Module:
    """Cache-friendly teacher training. Returns a model in eval mode on `device`."""
    path = teacher_cache_path(cache_root, dataset, N, alpha, seed, client_i)
    model = build_mlp(input_dim=784, num_classes=n_classes).to(device)
    if path.exists():
        model.load_state_dict(torch.load(path, map_location=device))
        model.eval()
        return model
    model = train_teacher(
        client_subset,
        n_classes=n_classes,
        epochs=epochs,
        device=device,
        seed=train_seed,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), path)
    model.eval()
    return model


@torch.no_grad()
def evaluate_teacher(model: nn.Module, eval_ds, device: str, batch_size: int = 256) -> float:
    model.eval()
    loader = DataLoader(eval_ds, batch_size=batch_size, shuffle=False, num_workers=0)
    correct, total = 0, 0
    for xb, yb in loader:
        xb, yb = xb.to(device), yb.to(device)
        pred = model(xb).argmax(dim=1)
        correct += (pred == yb).sum().item()
        total += yb.size(0)
    return correct / max(total, 1)


def train_all_teachers(
    client_subsets: List[Subset],
    cache_root: str,
    dataset: str,
    N: int,
    alpha: float,
    seed: int,
    n_classes: int,
    device: str,
    epochs: int,
) -> List[nn.Module]:
    teachers = []
    for i, subset in enumerate(client_subsets):
        t = get_or_train_teacher(
            cache_root=cache_root, dataset=dataset, N=N, alpha=alpha, seed=seed,
            client_i=i, client_subset=subset, n_classes=n_classes, device=device,
            epochs=epochs, train_seed=1000 + i,
        )
        teachers.append(t)
    return teachers
