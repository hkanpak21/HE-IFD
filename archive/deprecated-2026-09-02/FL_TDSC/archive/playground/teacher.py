"""Per-client teacher training, with disk cache keyed by (N, seed, alpha, client_idx)."""
from __future__ import annotations
import os
from pathlib import Path
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Subset

from .model import build_model


def teacher_cache_path(cache_root: str, arch: str, N: int, alpha: float,
                       seed: int, ci: int, teacher_epochs: int) -> Path:
    name = f"{arch}_N{N}_a{alpha}_s{seed}_c{ci}_e{teacher_epochs}.pt"
    return Path(cache_root) / name


def train_one_teacher(subset: Subset, arch: str, epochs: int, lr: float,
                      batch_size: int, device, seed: int) -> nn.Module:
    torch.manual_seed(seed)
    m = build_model(arch).to(device)
    if len(subset) == 0:
        return m
    loader = DataLoader(subset, batch_size=batch_size, shuffle=True, num_workers=0)
    opt = optim.SGD(m.parameters(), lr=lr, momentum=0.9)
    crit = nn.CrossEntropyLoss()
    m.train()
    for _ in range(epochs):
        for xb, yb in loader:
            xb = xb.to(device); yb = yb.to(device)
            opt.zero_grad()
            crit(m(xb), yb).backward()
            opt.step()
    m.eval()
    return m


def train_all_teachers(client_subsets, *, arch: str, N: int, alpha: float,
                       seed: int, cache_root: str, epochs: int = 10,
                       lr: float = 0.05, batch_size: int = 128,
                       device) -> list[nn.Module]:
    Path(cache_root).mkdir(parents=True, exist_ok=True)
    teachers = []
    for ci, sub in enumerate(client_subsets):
        path = teacher_cache_path(cache_root, arch, N, alpha, seed, ci, epochs)
        if path.exists():
            m = build_model(arch).to(device)
            m.load_state_dict(torch.load(path, map_location=device))
            m.eval()
        else:
            m = train_one_teacher(sub, arch, epochs, lr, batch_size, device,
                                  seed=1000 + ci)
            torch.save(m.state_dict(), path)
        teachers.append(m)
    return teachers
