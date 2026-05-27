"""MLP 784 -> 128 -> 32 -> 10 with ReLU between hidden layers.

Same architecture for client teachers and the server student per the v1 spec.
"""
from __future__ import annotations

from typing import Iterable

import torch
import torch.nn as nn


def build_mlp(input_dim: int = 784, num_classes: int = 10) -> nn.Sequential:
    return nn.Sequential(
        nn.Flatten(),
        nn.Linear(input_dim, 128),
        nn.ReLU(),
        nn.Linear(128, 32),
        nn.ReLU(),
        nn.Linear(32, num_classes),
    )


LAYER_NAMES: tuple[str, ...] = (
    "linear1.weight", "linear1.bias",
    "linear2.weight", "linear2.bias",
    "linear3.weight", "linear3.bias",
)


def state_dict_named(model: nn.Module) -> dict[str, torch.Tensor]:
    """Return a state dict keyed by LAYER_NAMES (six parameter blocks)."""
    linears = [m for m in model.modules() if isinstance(m, nn.Linear)]
    assert len(linears) == 3, "v1 architecture expects exactly three linear layers"
    return {
        "linear1.weight": linears[0].weight.detach().clone(),
        "linear1.bias":   linears[0].bias.detach().clone(),
        "linear2.weight": linears[1].weight.detach().clone(),
        "linear2.bias":   linears[1].bias.detach().clone(),
        "linear3.weight": linears[2].weight.detach().clone(),
        "linear3.bias":   linears[2].bias.detach().clone(),
    }


def load_named_state(model: nn.Module, state: dict[str, torch.Tensor]) -> None:
    linears = [m for m in model.modules() if isinstance(m, nn.Linear)]
    assert len(linears) == 3
    with torch.no_grad():
        linears[0].weight.copy_(state["linear1.weight"])
        linears[0].bias.copy_(state["linear1.bias"])
        linears[1].weight.copy_(state["linear2.weight"])
        linears[1].bias.copy_(state["linear2.bias"])
        linears[2].weight.copy_(state["linear3.weight"])
        linears[2].bias.copy_(state["linear3.bias"])


def deltas_against(initial: dict[str, torch.Tensor], final_state: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
    """Per-layer end-of-K cumulative delta DeltaW_{i,l} = S_K[l] - theta_0[l]."""
    return {k: (final_state[k] - initial[k]) for k in initial.keys()}


def apply_aggregate(theta0: dict[str, torch.Tensor], aggregate: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
    """theta_0 + aggregate. Pure linear; FHE-compatible at depth 0."""
    return {k: theta0[k] + aggregate[k] for k in theta0.keys()}
