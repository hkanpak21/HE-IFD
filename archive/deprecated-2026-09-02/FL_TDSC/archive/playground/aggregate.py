"""Server-side linear aggregate.

Two regimes:

    weight_mode = "uniform"  ->  W_E = theta0 + (1/N) Σ ΔW_i  (FedAvg-uniform)
    weight_mode = "samples"  ->  W_E = theta0 + Σ w_i · ΔW_i
                                  where w_i = |D_i| / Σ |D_j|   (FedAvg-classic)

Both are FHE-compatible: plaintext-scalar × ciphertext (depth +1).
"""
from __future__ import annotations
import torch


def linear_aggregate(theta0: dict, client_deltas: list[dict],
                     client_sizes: list[int] | None = None,
                     weight_mode: str = "uniform") -> dict:
    N = len(client_deltas)
    layer_names = list(theta0.keys())
    if weight_mode == "uniform":
        weights = [1.0 / N] * N
    elif weight_mode == "samples":
        assert client_sizes is not None and len(client_sizes) == N
        total = float(sum(client_sizes))
        assert total > 0
        weights = [n / total for n in client_sizes]
    else:
        raise ValueError(f"unknown weight_mode: {weight_mode}")

    out: dict = {}
    for name in layer_names:
        acc = weights[0] * client_deltas[0][name]
        for w, d in zip(weights[1:], client_deltas[1:]):
            acc = acc + w * d[name]
        out[name] = acc
    return {name: theta0[name] + out[name] for name in layer_names}
