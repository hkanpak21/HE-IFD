"""Client-side local distillation in the LoRA fine-tuning regime.

Each client:
  - Builds a fresh student LoRA from the shared init (teacher LoRA, freshly
    constructed each call from the same seed -> deterministic shared init).
  - KL-distills against its teacher T_i (the per-client LoRA model) on D_i.
  - Returns the trainable-parameter delta {student_final - student_init}.

Backbone weights NEVER move. Only the LoRA A/B matrices and the classification
head receive updates. The "delta" is therefore much smaller than full-model
FL (typically a few hundred K parameters per client vs 86M).
"""
from __future__ import annotations

from typing import Dict

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset

from .model import (build_vit, wrap_with_lora, lora_trainable_state,
                    lora_deltas)


def kl_distillation_loss(student_logits: torch.Tensor,
                         teacher_logits: torch.Tensor,
                         tau: float) -> torch.Tensor:
    """KL(softmax(s/tau) || softmax(T/tau)) * tau^2."""
    s = F.log_softmax(student_logits / tau, dim=1)
    t = F.softmax(teacher_logits / tau, dim=1)
    return F.kl_div(s, t, reduction="batchmean") * (tau ** 2)


def fresh_student(num_classes: int, rank: int, alpha: int,
                  init_seed: int, device) -> nn.Module:
    """Build a student LoRA from a deterministic init (same on every client).

    The pretrained backbone + classification head init are deterministic across
    clients because pretrained weights are public. The LoRA A/B init is
    Kaiming/zero (deterministic from the torch seed we set here).
    """
    torch.manual_seed(init_seed)
    base = build_vit(num_classes=num_classes, pretrained=True)
    m = wrap_with_lora(base, rank=rank, alpha=alpha).to(device)
    return m


def local_distill(teacher: nn.Module, distill_ds: Dataset, *,
                  num_classes: int, rank: int, alpha: int, init_seed: int,
                  K: int, lr: float, batch_size: int, tau: float,
                  device, run_seed: int) -> Dict[str, torch.Tensor]:
    """One client's local KL distillation of a teacher into a fresh student LoRA.

    Returns the trainable-param delta from the deterministic shared init.
    """
    torch.manual_seed(run_seed)
    s = fresh_student(num_classes, rank, alpha, init_seed, device)
    initial = lora_trainable_state(s)
    teacher = teacher.to(device).eval()

    if len(distill_ds) == 0:
        return lora_deltas(initial, initial)

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
    final = lora_trainable_state(s)
    return lora_deltas(initial, final)
