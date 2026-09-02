"""Pre-alignment: train the shared θ₀ on the synthetic anchors only,
producing a deterministic θ_pre that every client agrees on.

This locks in the class-slot assignment BEFORE local-data distillation starts,
so the clients' deltas measure deviation from a model that already knows
"anchor z_k → logit slot k".

Deterministic: same (seed, anchors, epochs, lr) -> same θ_pre on every client.
"""
from __future__ import annotations
from typing import Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

from .model import build_model, load_named, state_named


def pre_align(theta0: dict[str, torch.Tensor],
              anchors: Tuple[torch.Tensor, torch.Tensor],
              *, arch: str, epochs: int, lr: float = 0.05,
              batch_size: int = 64, seed: int = 0,
              device) -> dict[str, torch.Tensor]:
    """Train θ₀ on (Z, y) for `epochs` epochs.

    Deterministic across clients given the same inputs.
    For conv archs (lenet5), reshapes Z from (N, 784) to (N, 1, 28, 28).
    """
    if epochs <= 0:
        return theta0
    Z, y = anchors
    if arch == "lenet5" and Z.dim() == 2:
        Z = Z.view(Z.size(0), 1, 28, 28)
    torch.manual_seed(seed)
    m = build_model(arch).to(device); load_named(m, theta0); m.train()
    opt = optim.SGD(m.parameters(), lr=lr, momentum=0.9)
    n = Z.size(0)
    for _ in range(epochs):
        perm = torch.randperm(n, generator=torch.Generator().manual_seed(seed))
        for s in range(0, n, batch_size):
            idx = perm[s:s + batch_size]
            xb = Z[idx]; yb = y[idx]
            loss = F.cross_entropy(m(xb), yb)
            opt.zero_grad(); loss.backward(); opt.step()
    return state_named(m)
