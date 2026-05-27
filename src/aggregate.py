"""Server-side aggregation — the ONLY cryptographic operation, FHE-compatible.

The server computes exactly

        θ = θ₀ + Σ_i  w_i · Δ_i ,        w_i = n_i / Σ_j n_j

over the encrypted per-client cumulative displacements Δ_i. It is

  * **sample-weighted** — w_i is client i's share of the total training samples
    (NOT uniform 1/N; that was the deprecated ``src/v1`` behaviour);
  * **linear by construction** — the only tensor operations are
        ciphertext + ciphertext        (accumulating weighted Δ's, and + θ₀)
        plaintext_scalar × ciphertext  (the w_i scaling)
    No multiplication of two ciphertexts, no division, no non-linear activation.
    Multiplicative depth ≈ 1. This is what lets the plaintext simulation here be
    taken as the encrypted result (validated to ≤1e-3 in M2) and what frees the
    student to use any architecture (ReLU/GELU/softmax) with no polynomial
    approximation.

Telescoping identity (the basin-coherence argument, made precise):
    θ = θ₀ + Σ_i w_i·(θ_i^(K) − θ₀)
because each Δ_i = θ_i^(K) − θ₀ is itself the sum of client i's K per-step
deltas, ``aggregate`` over cumulative Δ's equals the notebook's
``server_aggregate`` over per-step deltas. Both are provided so the equality is
testable (issue 003) and the coherence ablation (issue 006) can feed either form.

THE LINEARITY INVARIANT IS LOAD-BEARING: do not introduce any non-linear op
into this module. The aggregate must remain expressible as PT×CT and CT+CT only.
"""
from __future__ import annotations

from typing import Dict, List, Sequence


def sample_weights(sample_sizes: Sequence[int]) -> List[float]:
    """w_i = n_i / Σ_j n_j. The sample-weighted combination weights.

    If every client has zero samples (degenerate), falls back to uniform 1/N so
    the aggregate is still well-defined.
    """
    total = float(sum(sample_sizes))
    n = len(sample_sizes)
    if total <= 0:
        return [1.0 / n] * n
    return [float(s) / total for s in sample_sizes]


def aggregate(theta0: Dict, deltas: List[Dict], weights: Sequence[float]) -> Dict:
    """Server aggregation: θ = θ₀ + Σ_i w_i·Δ_i (linear, sample-weighted).

    Parameters
    ----------
    theta0 : dict
        The shared aligned init θ₀ (the download baseline; known to the server).
    deltas : list of dict
        Per-client cumulative displacements Δ_i (the encrypted uploads).
    weights : sequence of float
        Sample weights w_i (use ``sample_weights(sample_sizes)``). Need not be
        re-normalised here — they are passed pre-normalised by the protocol.

    Returns
    -------
    theta : dict
        The aggregated final-student parameters.

    Implementation uses ONLY ``+`` (CT+CT) and scalar ``*`` (PT×CT) on tensors,
    preserving the FHE-compatibility invariant.
    """
    theta = {k: v.detach().clone() for k, v in theta0.items()}  # θ₀ baseline
    for i, w in enumerate(weights):
        d = deltas[i]
        for k in theta:
            theta[k] = theta[k] + w * d[k]      # CT+CT and PT(scalar w)×CT only
    return theta


def aggregate_step_deltas(
    theta0: Dict, all_step_deltas: List[List[Dict]], weights: Sequence[float]
) -> Dict:
    """Notebook-identical aggregation over per-step deltas (verbatim semantics).

    ``all_step_deltas[i]`` is client i's list of K per-step deltas. Sums
    θ₀ + Σ_step Σ_i w_i·d[i][step], which equals ``aggregate(theta0, [Σ_step
    d[i][step] for i], weights)``. Kept so the telescoping equality is directly
    checkable and the coherence ablation can use raw trajectories. Still
    linear-only (CT+CT, PT×CT).
    """
    K_local = len(all_step_deltas[0])
    theta = {k: v.detach().clone() for k, v in theta0.items()}
    for step in range(K_local):
        for i, w in enumerate(weights):
            d = all_step_deltas[i][step]
            for k in theta:
                theta[k] = theta[k] + w * d[k]
    return theta
