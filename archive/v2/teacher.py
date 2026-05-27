"""Per-client teacher = ViT fine-tune on D_i.

Two modes (selected by `use_lora`):
  - Full-FT: every param of the ViT is updated on D_i.
  - LoRA: only adapter + head updated; backbone frozen at pretrained init.

Teacher state cached on disk and reused across runs.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Subset

from .model import (build_student, trainable_state, trainable_load,
                    trainable_param_count)


def teacher_cache_path(cache_root: str, dataset: str, num_classes: int,
                       N: int, alpha: float, seed: int, ci: int,
                       teacher_epochs: int, mode_tag: str) -> Path:
    name = (f"vit_{dataset}_C{num_classes}_N{N}_a{alpha}_s{seed}_c{ci}"
            f"_{mode_tag}_e{teacher_epochs}.pt")
    return Path(cache_root) / name


def train_one_teacher(subset: Subset, *, num_classes: int, epochs: int,
                      lr: float, batch_size: int, device, seed: int,
                      use_lora: bool, rank: int, lora_alpha: int
                      ) -> Dict[str, torch.Tensor]:
    torch.manual_seed(seed)
    m = build_student(num_classes=num_classes, use_lora=use_lora,
                      rank=rank, lora_alpha=lora_alpha).to(device)
    if len(subset) == 0:
        return trainable_state(m)

    loader = DataLoader(subset, batch_size=batch_size, shuffle=True,
                        num_workers=2, pin_memory=True)
    opt = optim.AdamW([p for p in m.parameters() if p.requires_grad],
                      lr=lr, weight_decay=0.01)
    crit = nn.CrossEntropyLoss()
    m.train()
    for _ in range(epochs):
        for xb, yb in loader:
            xb = xb.to(device, non_blocking=True)
            yb = yb.to(device, non_blocking=True)
            opt.zero_grad()
            crit(m(xb), yb).backward()
            opt.step()
    m.eval()
    return trainable_state(m)


def train_all_teachers(client_subsets: List[Subset], *, dataset: str,
                       num_classes: int, N: int, alpha: float, seed: int,
                       cache_root: str, epochs: int, lr: float, batch_size: int,
                       use_lora: bool, rank: int, lora_alpha: int,
                       device) -> List[Dict[str, torch.Tensor]]:
    """Train (or load from cache) one teacher state per client.

    Returns a list of N dicts of trainable-parameter tensors. In LoRA mode
    that's adapter + head; in full-FT mode that's the full ViT.
    """
    mode_tag = f"lora{rank}" if use_lora else "fullft"
    Path(cache_root).mkdir(parents=True, exist_ok=True)
    teachers: List[Dict[str, torch.Tensor]] = []
    for ci, sub in enumerate(client_subsets):
        path = teacher_cache_path(cache_root, dataset, num_classes,
                                  N, alpha, seed, ci, epochs, mode_tag)
        if path.exists():
            state = torch.load(path, map_location=device)
        else:
            state = train_one_teacher(
                sub, num_classes=num_classes, epochs=epochs, lr=lr,
                batch_size=batch_size, device=device, seed=1000 + ci,
                use_lora=use_lora, rank=rank, lora_alpha=lora_alpha,
            )
            # Save to CPU for portability
            torch.save({k: v.cpu() for k, v in state.items()}, path)
        teachers.append({k: v.to(device) for k, v in state.items()})
    return teachers


def build_teacher_model(teacher_state: Dict[str, torch.Tensor], *,
                        num_classes: int, use_lora: bool,
                        rank: int, lora_alpha: int, device) -> nn.Module:
    """Reconstruct an inference-ready model from a teacher state."""
    m = build_student(num_classes=num_classes, use_lora=use_lora,
                      rank=rank, lora_alpha=lora_alpha).to(device)
    trainable_load(m, teacher_state)
    m.eval()
    return m
