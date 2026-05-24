"""Server-side LoRA-parameter aggregation. Linear-only, FHE-compatible.

Each client uploads a dict of trainable-param tensors (LoRA A/B + head).
Server computes a sample-weighted (or uniform) linear sum and adds to the
shared init. All operations are CT+CT (depth 0) and PT*CT (depth +1) under
multiparty CKKS.
"""
from __future__ import annotations

from typing import Dict, List

import torch


def linear_aggregate(initial: Dict[str, torch.Tensor],
                     client_deltas: List[Dict[str, torch.Tensor]],
                     client_sizes: List[int] | None = None,
                     weight_mode: str = "samples") -> Dict[str, torch.Tensor]:
    """W_E[k] = initial[k] + sum_i w_i * delta_i[k] for each tensor k.

    weight_mode:
        "uniform" -> w_i = 1/N
        "samples" -> w_i = |D_i| / sum_j |D_j|
    """
    N = len(client_deltas)
    if N == 0:
        raise ValueError("linear_aggregate requires at least one delta")

    if weight_mode == "uniform":
        weights = [1.0 / N] * N
    elif weight_mode == "samples":
        assert client_sizes is not None and len(client_sizes) == N
        total = float(sum(client_sizes))
        assert total > 0
        weights = [n / total for n in client_sizes]
    else:
        raise ValueError(f"unknown weight_mode: {weight_mode}")

    keys = list(initial.keys())
    out: Dict[str, torch.Tensor] = {}
    for k in keys:
        # depth audit: w_i * delta_i is PT*CT (+1), sum_i is CT+CT (0)
        acc = weights[0] * client_deltas[0][k]
        for wi, d in zip(weights[1:], client_deltas[1:]):
            acc = acc + wi * d[k]
        out[k] = initial[k] + acc        # PT+CT = CT (no depth growth)
    return out
