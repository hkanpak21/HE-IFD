"""Client-side local distillation. Plaintext, runs entirely at the client.

Output: per-layer end-of-K cumulative deltas DeltaW_{i,l} that get uploaded
(in production: encrypted under collective pk) to the server.
"""
from __future__ import annotations

from typing import Dict

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset

from .model import build_mlp, deltas_against, load_named_state, state_dict_named


def kl_distillation_loss(student_logits: torch.Tensor, teacher_logits: torch.Tensor, tau: float) -> torch.Tensor:
    """KL(softmax(s/tau) || softmax(T/tau)) * tau^2 (Hinton 2015 scale-correction)."""
    s = F.log_softmax(student_logits / tau, dim=1)
    t = F.softmax(teacher_logits / tau, dim=1)
    return F.kl_div(s, t, reduction="batchmean") * (tau ** 2)


def local_distill(
    teacher: nn.Module,
    union_ds: Dataset,
    theta0: Dict[str, torch.Tensor],
    *,
    epochs: int = 5,
    batch_size: int = 64,
    lr: float = 1e-2,
    momentum: float = 0.9,
    tau: float = 4.0,
    device: str = "cpu",
    seed: int | None = None,
) -> Dict[str, torch.Tensor]:
    """One client's local distillation. Returns per-layer DeltaW_{i,l}.

    Inputs
    ------
    teacher : the client's trained teacher T_i.
    union_ds : the inputs the client distils over (P union D_i in v1 spec).
    theta0 : the shared random init (six parameter blocks).
    """
    if seed is not None:
        torch.manual_seed(seed)
    student = build_mlp().to(device)
    load_named_state(student, theta0)
    teacher = teacher.to(device).eval()

    if len(union_ds) == 0:
        # Empty client -- no update.
        final_state = state_dict_named(student)
        return deltas_against(theta0, final_state)

    loader = DataLoader(union_ds, batch_size=batch_size, shuffle=True, num_workers=0)
    opt = optim.SGD(student.parameters(), lr=lr, momentum=momentum)
    student.train()
    for _ in range(epochs):
        for xb, _ in loader:
            xb = xb.to(device)
            with torch.no_grad():
                t_logits = teacher(xb)
            s_logits = student(xb)
            loss = kl_distillation_loss(s_logits, t_logits, tau=tau)
            opt.zero_grad()
            loss.backward()
            opt.step()
    final_state = state_dict_named(student)
    return deltas_against(theta0, final_state)
