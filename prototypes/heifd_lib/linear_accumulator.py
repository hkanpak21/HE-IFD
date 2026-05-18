"""
Encrypted linear-accumulator SGD against the ensemble target.

Per the memory `project-linear-accumulator` and PRD section 4.3:
    * Student forward pass is plaintext (so all chain-rule factors are pt).
    * Per-step encrypted depth <= 3 on the accumulator ciphertext <Delta>.
    * Composition at end of training: <theta_E> = <theta_0*> + <Delta>.

For the smoke we keep the encrypted accumulator one-dimensional (the
output-bias coordinate); the prose generalises to the full parameter
vector by tiling across CKKS slots. This matches what the
prototypes/cfd_tenseal_smoke.py validation already audited as depth-<=3.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np


@dataclass
class AccumulatorState:
    enc_delta: object              # ts.CKKSVector
    plain_delta: np.ndarray        # plaintext shadow, for divergence audit
    steps: int = 0
    cumulative_bytes: int = 0


def init_accumulator(ctx, dim: int) -> AccumulatorState:
    """Zero-initialised encrypted accumulator + plaintext shadow."""
    import tenseal as ts

    plain = np.zeros(dim, dtype=np.float64)
    enc = ts.ckks_vector(ctx, plain.tolist())
    return AccumulatorState(enc_delta=enc, plain_delta=plain)


def encrypted_step(
    state: AccumulatorState,
    plain_student_logits: np.ndarray,   # (|P|, C)
    enc_Y_rows: List,                   # list of |P| ts.CKKSVector rows
    plain_Y_ref: np.ndarray,            # (|P|, C) -- shadow for audit only
    lr: float,
) -> Dict[str, float]:
    """
    One encrypted SGD step on the output-bias coordinate.

    Depth audit:
        residual r = -<Y_tilde[r]> + S_plain[r]  -- depth +0 (ct+pt).
        grad g = (1/P) sum_r r                   -- depth +1 (pt*ct then ct+ct).
        delta_step = -lr * g                     -- depth +1 (pt*ct).
        <Delta> += delta_step                    -- depth +0 (ct+ct).
    Net per-step encrypted depth from the residual = 2; +1 carry-over from
    the beta-aggregated input puts us at the depth-<=-3 budget.
    """
    P, C = plain_student_logits.shape
    inv_P = 1.0 / P

    # Encrypted residual + accumulated gradient (per-coordinate mean).
    enc_grad = None
    for r in range(P):
        # residual = -Y_tilde[r] + S_plain[r]  (ct+pt at depth +0)
        residual = (-enc_Y_rows[r]) + plain_student_logits[r].tolist()
        scaled = residual * inv_P                      # pt*ct, depth +1
        if enc_grad is None:
            enc_grad = scaled
        else:
            enc_grad = enc_grad + scaled               # ct+ct, depth 0

    enc_step = enc_grad * (-lr)                        # pt*ct, depth +1
    state.enc_delta = state.enc_delta + enc_step       # ct+ct, depth 0
    state.steps += 1

    # Plaintext shadow.
    plain_residuals = plain_student_logits - plain_Y_ref
    plain_grad = plain_residuals.mean(axis=0)
    state.plain_delta = state.plain_delta + (-lr) * plain_grad

    from cfd_tenseal_smoke import serialize_one_bytes  # lazy to avoid TenSEAL import at module load
    n_bytes = serialize_one_bytes(state.enc_delta)
    state.cumulative_bytes += n_bytes
    return {"bytes": n_bytes, "P": P, "C": C}


def compose_theta(enc_theta0_star, enc_delta):
    """
    <theta_E> = <theta_0*> + <Delta>. Depth 0 (ct+ct). Called once at the
    end of E_2 distillation epochs.
    """
    return enc_theta0_star + enc_delta
