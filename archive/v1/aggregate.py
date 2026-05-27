"""Server-side aggregation. Linear only -- no non-linearities, no losses,
no gradient computation. FHE-compatible by construction.

In v1 simulation everything is plaintext torch tensors, but every operation
in this module is one of:
    (a) element-wise tensor addition (FHE CT+CT, depth 0),
    (b) plaintext-scalar * tensor (FHE PT*CT, depth +1).
No activations, no softmax, no losses, no `forward`/`backward` calls.
"""
from __future__ import annotations

from typing import Dict, List

import torch


def linear_aggregate(
    theta0: Dict[str, torch.Tensor],
    client_deltas: List[Dict[str, torch.Tensor]],
) -> Dict[str, torch.Tensor]:
    """W_l^E = theta_0,l + (1/N) * sum_i DeltaW_{i,l}.

    FHE depth audit:
        sum_i DeltaW_{i,l}              -- (N-1) ct+ct, depth 0
        scalar (1/N) * (sum)            -- pt*ct, depth +1
        theta_0,l + scaled              -- ct+ct (with theta_0 either pt or
                                           ct depending on whether theta_0 is
                                           public-plaintext or encrypted in
                                           production); in v1 we keep theta_0
                                           public plaintext per user spec.
    Net per-layer depth: +1. Well within the depth-<=-3 budget.
    """
    if len(client_deltas) == 0:
        raise ValueError("linear_aggregate requires at least one client delta")
    layer_names = list(theta0.keys())
    inv_N = 1.0 / len(client_deltas)
    aggregate: Dict[str, torch.Tensor] = {}
    for name in layer_names:
        acc = client_deltas[0][name].clone()
        for delta in client_deltas[1:]:
            acc = acc + delta[name]
        scaled = acc * inv_N
        aggregate[name] = scaled
    # Final composition: theta_0 + aggregate.
    return {name: theta0[name] + aggregate[name] for name in layer_names}
