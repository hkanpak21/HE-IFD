"""
Encrypted ensemble target construction (PRD section 4.2).

Reuses primitives from prototypes/cfd_tenseal_smoke.py to keep the depth
audit in one place:
    create_context, encrypt_vector, chunk_rows_to_ciphertexts,
    beta_aggregation, lambda_variance.

This module is the bridge from "I have N plaintext (|P|, C) logit tensors
plus N plaintext alpha_i confidence scalars" to "I have |P| encrypted
ciphertext rows <Y_tilde[r]> with measured depth <= 3".
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Tuple

import numpy as np

# Import the smoke primitives directly. They live at
# prototypes/cfd_tenseal_smoke.py; ensure prototypes/ is on sys.path so
# the import works whether we're invoked via `python prototypes/heifd_train.py`
# (cwd may differ) or as a module.
_PROTO_DIR = Path(__file__).resolve().parent.parent
if str(_PROTO_DIR) not in sys.path:
    sys.path.insert(0, str(_PROTO_DIR))

# Re-export so heifd_train.py can import everything from one place.
from cfd_tenseal_smoke import (  # noqa: E402  (sys.path tweak above is intentional)
    create_context,
    encrypt_vector,
    chunk_rows_to_ciphertexts,
    serialize_bytes,
    serialize_one_bytes,
    beta_aggregation,
    lambda_variance,
)


def encrypt_client_logits(ctx, logits_per_client: List[np.ndarray]):
    """
    Encrypt each client's (|P|, C) logit matrix as a list of |P| row
    ciphertexts. Returns the nested list shape expected by
    beta_aggregation / lambda_variance.
    """
    return [chunk_rows_to_ciphertexts(ctx, L, slots=2 ** 13) for L in logits_per_client]


def encrypt_alphas(ctx, alphas: List[float]):
    import tenseal as ts

    return [ts.ckks_vector(ctx, [float(a)]) for a in alphas]


def build_ensemble_target(
    ctx,
    logits_per_client: List[np.ndarray],
    alphas: List[float],
    beta: int = 2,
) -> Tuple[list, np.ndarray, float, int]:
    """
    Construct <Y_tilde> via beta-aggregation per PRD section 4.2.

    Returns (enc_Y_rows, plain_Y_reference, wall_clock_sec, bytes).
    The plain_Y_reference is for accuracy debugging only; the encrypted
    rows are what flow into the linear-accumulator student SGD.
    """
    plain_logits = np.stack(logits_per_client, axis=0)  # (N, |P|, C)
    plain_alphas = np.asarray(alphas, dtype=np.float64)

    enc_logits = encrypt_client_logits(ctx, logits_per_client)
    enc_alphas = encrypt_alphas(ctx, alphas)

    enc_Y_rows, plain_Y, wall, n_bytes = beta_aggregation(
        ctx, enc_logits, enc_alphas, beta=beta,
        plain_logits=plain_logits, plain_alphas=plain_alphas,
    )
    return enc_Y_rows, plain_Y, wall, n_bytes


__all__ = [
    "create_context",
    "encrypt_vector",
    "chunk_rows_to_ciphertexts",
    "serialize_bytes",
    "serialize_one_bytes",
    "beta_aggregation",
    "lambda_variance",
    "encrypt_client_logits",
    "encrypt_alphas",
    "build_ensemble_target",
]
