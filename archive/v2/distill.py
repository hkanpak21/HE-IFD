"""Client-side local distillation. Supports full-FT and LoRA modes.

Each client:
  - Builds a fresh student from a deterministic shared init.
  - KL-distills against its teacher on D_i.
  - Returns the trainable-parameter delta {student_final - student_init}.

Full-FT: every ViT parameter moves; delta is ~86M floats per layer-key.
LoRA: only adapter + head move; delta is ~hundreds of K floats.
"""
from __future__ import annotations

from typing import Dict

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset

from .model import build_student, trainable_state, model_deltas


def kl_distillation_loss(student_logits: torch.Tensor,
                         teacher_logits: torch.Tensor,
                         tau: float) -> torch.Tensor:
    """KL(softmax(s/tau) || softmax(T/tau)) * tau^2."""
    s = F.log_softmax(student_logits / tau, dim=1)
    t = F.softmax(teacher_logits / tau, dim=1)
    return F.kl_div(s, t, reduction="batchmean") * (tau ** 2)


def fresh_student(num_classes: int, *, use_lora: bool, rank: int,
                  lora_alpha: int, init_seed: int, device) -> nn.Module:
    """Build a student from a deterministic init (same on every client).

    Pretrained backbone weights are public/deterministic. In LoRA mode the
    A matrix is Kaiming-init (seeded), B is zero. In full-FT mode the
    "init" is the pretrained weights themselves.
    """
    torch.manual_seed(init_seed)
    m = build_student(num_classes=num_classes, use_lora=use_lora,
                      rank=rank, lora_alpha=lora_alpha).to(device)
    return m


def local_distill(teacher: nn.Module, distill_ds: Dataset, *,
                  num_classes: int, use_lora: bool, rank: int, lora_alpha: int,
                  init_seed: int, K: int, lr: float, batch_size: int,
                  tau: float, device, run_seed: int) -> Dict[str, torch.Tensor]:
    """One client's local KL distillation of a teacher into a fresh student.

    Returns the trainable-param delta from the deterministic shared init.
    """
    torch.manual_seed(run_seed)
    s = fresh_student(num_classes, use_lora=use_lora, rank=rank,
                      lora_alpha=lora_alpha, init_seed=init_seed, device=device)
    initial = trainable_state(s)
    teacher = teacher.to(device).eval()

    if len(distill_ds) == 0:
        return model_deltas(initial, initial)

    loader = DataLoader(distill_ds, batch_size=batch_size, shuffle=True,
                        num_workers=2, pin_memory=True)
    opt = optim.AdamW([p for p in s.parameters() if p.requires_grad],
                      lr=lr, weight_decay=0.01)
    s.train()
    for _ in range(K):
        for xb, _ in loader:
            xb = xb.to(device, non_blocking=True)
            with torch.no_grad():
                t_logits = teacher(xb)
            s_logits = s(xb)
            loss = kl_distillation_loss(s_logits, t_logits, tau)
            opt.zero_grad()
            loss.backward()
            opt.step()
    final = trainable_state(s)
    return model_deltas(initial, final)
