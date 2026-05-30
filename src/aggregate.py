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

THE LINEARITY INVARIANT IS LOAD-BEARING for ``aggregate``: do not introduce any
non-linear op into the linear combine. The default protocol aggregate must remain
expressible as PT×CT and CT+CT only.

------------------------------------------------------------------------------
Non-linear one-shot combine study (issue 025)
------------------------------------------------------------------------------
``aggregate_nonlinear`` ports the issue-024 *local probe*'s non-linear one-shot
server combines into the real ``src`` pipeline so they can be measured on the
headline backbones / partitions, NOT just the MNIST-MLP probe. The research
question (closed negatively by the 024 probe) is: *given the SAME one-shot uploads
{Δ_i}, does any NON-LINEAR server function of them beat the flat weighted average
θ₀+Σw_iΔ_i under heterogeneity, and is any winner CKKS-cheap?*

Every combine here operates on the SAME one-shot cumulative displacements {Δ_i}
(flattened per-parameter into one stacked (N, P) tensor, combined, then
unflattened back to the per-tensor state dict). ``weight_avg`` is NOT reimplemented
— it routes to the existing linear ``aggregate`` so that path stays byte-identical;
``aggregate_nonlinear(..., method="weight_avg")`` simply delegates to ``aggregate``.

HE depth (``NONLINEAR_DEPTH``):
  * **depth-1**  — linear / reweighted-average combines (PT×CT + CT+CT only; a
                   public-scalar reweight is still linear). CKKS-cheap.
  * **depth-2**  — the division-free degree-2 polynomial gates: m and s² are each
                   one linear pass, the gate is ONE extra elementwise ct·ct
                   multiply, no ciphertext denominator. CKKS-cheap.
  * **deep**     — needs sign/compare/sqrt/division/sort. NOT low-depth CKKS;
                   included only to measure the *idea* in plaintext (these are the
                   theoretically-richer schemes the 024 probe found still ≤ WA).

THE LINEARITY INVARIANT for the *protocol default* is preserved precisely because
the default ``agg_method="weight_avg"`` never enters this module — it stays on the
``aggregate`` path. The non-linear combines are an investigation axis, gated behind
an explicit ``--agg-methods`` selector; none is the production aggregator.
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


def aggregate(theta0: Dict, deltas: List[Dict], weights: Sequence[float],
              lambda_scale: float = 1.0) -> Dict:
    """Server aggregation: θ = θ₀ + λ·Σ_i w_i·Δ_i (linear, sample-weighted).

    Parameters
    ----------
    theta0 : dict
        The shared aligned init θ₀ (the download baseline; known to the server).
    deltas : list of dict
        Per-client cumulative displacements Δ_i (the encrypted uploads).
    weights : sequence of float
        Sample weights w_i (use ``sample_weights(sample_sizes)``). Need not be
        re-normalised here — they are passed pre-normalised by the protocol.
    lambda_scale : float, default 1.0
        The task-arithmetic SCALING COEFFICIENT λ (Ilharco et al. 2023): the
        server computes θ₀ + λ·Σ_i w_i·Δ_i. λ is a PUBLIC scalar, so under CKKS
        the combine stays depth-1 — it folds into each weight (wl = w·λ) and the
        op is still PT(scalar)×CT + CT+CT only, NO ciphertext multiply. At the
        default λ=1.0 this is BYTE-IDENTICAL to the pre-λ path: λ is folded as
        ``wl = w * lambda_scale`` and ``w * 1.0 == w`` exactly in IEEE float, so
        ``theta[k] + wl * d[k]`` reduces to the original ``theta[k] + w * d[k]``
        term-for-term. The result interpolates the basin and the λ=1 aggregate:
        θ⋆(λ) = (1−λ)·θ₀ + λ·θ⋆(1) — sweeping λ slides along that line, eval-only
        (no retraining), which is what issue 026 verifies cheaply.

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
        wl = w * lambda_scale                   # fold the PUBLIC scalar λ into w_i
        for k in theta:
            theta[k] = theta[k] + wl * d[k]     # CT+CT and PT(scalar w·λ)×CT only
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


# ===========================================================================
# Non-linear one-shot server combines (issue 025) — INVESTIGATION AXIS ONLY.
#
# These are NOT the production aggregator (the default protocol path stays on the
# linear ``aggregate`` above). They port the issue-024 local-probe combines into
# the real pipeline so they can be measured on the headline backbones; the 024
# probe already showed (on MNIST-MLP) that none reliably beats ``weight_avg``
# under heterogeneity and the only CKKS-cheap candidates (depth-1 reweights,
# division-free depth-2 poly gates) have no headroom. Each combine is a fixed
# server-side function of the SAME one-shot {Δ_i}; HE depth is annotated, NOT
# implemented (plaintext study of the idea).
# ===========================================================================

# HE multiplicative-depth annotation per non-linear method. "depth-1"/"depth-2"
# are CKKS-feasible (depth-2 = one extra ct·ct multiply, division-free); "deep"
# needs sign/compare/sqrt/division/sort -> not low-depth CKKS. ``weight_avg`` is
# the depth-1 linear baseline (routes to ``aggregate``).
NONLINEAR_DEPTH: Dict[str, str] = {
    "weight_avg":          "depth-1",
    "mag_weighted":        "depth-1",
    "norm_normalized":     "deep",
    "sign_majority":       "deep",
    "agreement_gated":     "deep",
    "second_moment":       "deep",
    "coord_median":        "deep",
    "coord_trimmed_mean":  "deep",
    "consensus_proj":      "deep",
    "poly_gate_d2_a":      "depth-2",
    "poly_gate_d2_b":      "depth-2",
}

# Numerical floor shared by the division/ratio combines (matches the 024 probe).
_EPS = 1e-12

# Poly-gate strength. The 024 probe recorded c=0.01 with an UNBOUNDED gate and
# found it detonates heavy-tailed coordinates (s2_hat/var_hat max ≈ 500× the
# mean), collapsing accuracy for any c large enough to gate meaningfully. Issue
# 025's brief requires a SAFE BOUNDED gate that does not detonate: we keep the
# division-free degree-2 polynomial form but additionally CLAMP the per-coordinate
# shrink fraction into [0, 1] before applying it, so the gate can at most zero a
# coordinate's mean and can NEVER flip its sign or amplify it. The clamp is the
# safety device; with it bounded we can afford a stronger nominal c (so the gate
# is not a near-no-op like the safe c≈0.005 in the probe). NOTE the clamp is a
# min/max (a compare), so a *faithful* CKKS realisation would approximate it with
# a low-degree polynomial — this is flagged in the depth annotation discussion;
# the plaintext study measures whether the bounded gate IDEA helps at all.
_POLY_C = 1.0


# ---- flat-vector helpers: stack the per-client state dicts into one (N, P)
# tensor in a fixed key order, and unflatten a (P,) vector back to a state dict.
def _state_keys(theta0: Dict) -> List[str]:
    return list(theta0.keys())


def _flatten_state(state: Dict, keys: List[str]):
    import torch

    return torch.cat([state[k].reshape(-1) for k in keys])


def _unflatten_state(vec, theta0: Dict, keys: List[str]) -> Dict:
    out: Dict = {}
    off = 0
    for k in keys:
        n = theta0[k].numel()
        out[k] = vec[off:off + n].reshape(theta0[k].shape).clone()
        off += n
    return out


# ---- the combines. Each takes the stacked client displacements D (N, P), the
# sample weights w (N,), and the flat θ₀ vector t0 (P,); returns the combined
# flat θ vector (P,). All operate on the SAME one-shot {Δ_i}. Mirrors the issue
# 024 ``run_nonlinear.py`` math verbatim (except the bounded poly gates).
def _combine_weight_avg(D, w, t0):
    m = (w[:, None] * D).sum(0)                       # Σ_i w_i Δ_i
    return t0 + m


def _combine_mag_weighted(D, w, t0):
    norms = D.norm(dim=1)                             # ‖Δ_i‖ (a PUBLIC scalar)
    coef = w * norms
    coef = coef / (coef.sum() + _EPS)                 # renormalised public scalars
    m = (coef[:, None] * D).sum(0)                    # still linear (PT×CT + CT+CT)
    return t0 + m


def _combine_sign_majority(D, w, t0):
    import torch

    vote = (w[:, None] * torch.sign(D)).sum(0)        # weighted sign vote / coord
    direction = torch.sign(vote)
    mag = D.abs().mean(0)                              # mean magnitude / coord
    m = (w[:, None] * D).sum(0)
    # rescale so its global L1 matches weight_avg's |m| (compare update *shape*).
    scale = m.abs().sum() / (direction.abs() * mag).sum().clamp_min(_EPS)
    return t0 + scale * direction * mag


def _combine_norm_normalized(D, w, t0):
    norms = D.norm(dim=1, keepdim=True).clamp_min(_EPS)
    units = D / norms                                 # per-vector division
    mean_norm = D.norm(dim=1).mean()
    m = (w[:, None] * units).sum(0)
    return t0 + mean_norm * m


def _combine_agreement_gated(D, w, t0, eps_rel=1e-3):
    m = (w[:, None] * D).sum(0)                       # Σ_i w_i Δ_i
    s2 = (w[:, None] * D.pow(2)).sum(0)               # Σ_i w_i Δ_i²
    eps = eps_rel * s2.mean()
    g = m.pow(2) / (eps + s2)                          # ∈ [0,1], downweights cancellation
    return t0 + g * m


def _combine_second_moment(D, w, t0, eps_rel=1e-3):
    import torch

    m = (w[:, None] * D).sum(0)
    s2 = (w[:, None] * D.pow(2)).sum(0)
    eps = eps_rel * s2.mean()
    pre = m / torch.sqrt(eps + s2)                    # RMSProp-style per-coord precond
    scale = m.abs().sum() / pre.abs().sum().clamp_min(_EPS)
    return t0 + scale * pre


def _combine_coord_median(D, w, t0):
    """Per-coordinate median across clients (robust location, ignores weights).

    The issue-025 robust-statistic analogue of coord_trimmed_mean: take the
    median of {Δ_ij}_i for every coordinate j, then rescale to weight_avg's
    global L1 so the comparison is about robustness, not step size. Needs a sort
    -> ``deep``."""
    import torch

    n = D.shape[0]
    if n == 1:
        return t0 + D[0]
    med = D.median(dim=0).values                      # per-coord median (sort)
    m = (w[:, None] * D).sum(0)
    scale = m.abs().sum() / med.abs().sum().clamp_min(_EPS)
    return t0 + scale * med


def _combine_coord_trimmed_mean(D, w, t0):
    import torch

    n = D.shape[0]
    if n <= 2:
        return _combine_weight_avg(D, w, t0)          # nothing to trim
    k = 1                                              # drop top-1 and bottom-1 / coord
    sorted_D, _ = torch.sort(D, dim=0)                # sort across clients / coord
    trimmed = sorted_D[k:n - k]                        # (n-2k, P)
    m = trimmed.mean(0)
    return t0 + m


def _combine_consensus_proj(D, w, t0, residual=0.3):
    m = (w[:, None] * D).sum(0)                       # consensus direction (mean)
    u = m / m.norm().clamp_min(_EPS)
    proj = (D * u[None, :]).sum(1)                    # scalar proj of each Δ_i on u
    coh = (w * proj).sum()                             # weighted mean projection length
    return t0 + coh * u + residual * (m - coh * u)


# --- division-free depth-2 poly gates with a SAFE BOUNDED shrink (issue 025).
# Coordinates are scaled by a single PUBLIC scalar s = sqrt(mean_j s2_j) (the
# global RMS displacement, a public summary) so one c works across cells; this
# scaling is a public-scalar multiply and adds NO ciphertext depth. m and
# s2=Σ_i w_i Δ_i² are each one linear pass; the gate is ONE extra elementwise
# ct·ct multiply (depth-2 total), no ciphertext denominator. The shrink fraction
# is CLAMPED to [0,1] so a heavy-tailed coordinate is at worst zeroed, never
# flipped/amplified — the fix for the 024 detonation.
def _poly_scale(D, w):
    import torch

    s2 = (w[:, None] * D.pow(2)).sum(0)
    s = torch.sqrt(s2.mean() + _EPS)                  # public global RMS scalar
    return s2, s


def _combine_poly_gate_d2_a(D, w, t0, c=_POLY_C):
    """θ₀ + m − clamp(c·ŝ², 0, 1)⊙m,  ŝ² = s²/s² (public-scalar rescale).

    Shrinks high-disagreement-energy coordinates toward θ₀, keeps low-energy ones.
    One ct·ct multiply; the clamp bounds the shrink fraction to [0,1] so the gate
    never detonates (the 024-probe failure mode). Division-free on ciphertexts."""
    m = (w[:, None] * D).sum(0)
    s2, s = _poly_scale(D, w)
    s2_hat = s2 / (s * s)                              # public-scalar division only
    shrink = (c * s2_hat).clamp(0.0, 1.0)             # SAFE bounded gate ∈ [0,1]
    return t0 + m - shrink * m


def _combine_poly_gate_d2_b(D, w, t0, c=_POLY_C):
    """Cancellation-aware: θ₀ + m − clamp(c·v̂, 0, 1)⊙m,
    var = s² − m² (weighted per-coord variance, ≥0), v̂ = var/s².

    Where clients agree var≈0 -> keep m; where they cancel var large -> shrink m.
    One ct·ct multiply (m·v̂), division-free on ciphertexts (public-scalar s²); the
    [0,1] clamp keeps the shrink bounded (the issue-025 safety fix)."""
    m = (w[:, None] * D).sum(0)
    s2, s = _poly_scale(D, w)
    var = (s2 - m.pow(2)).clamp_min(0.0)
    var_hat = var / (s * s)                            # public-scalar division only
    shrink = (c * var_hat).clamp(0.0, 1.0)            # SAFE bounded gate ∈ [0,1]
    return t0 + m - shrink * m


_COMBINE_FN = {
    "mag_weighted":       _combine_mag_weighted,
    "sign_majority":      _combine_sign_majority,
    "norm_normalized":    _combine_norm_normalized,
    "agreement_gated":    _combine_agreement_gated,
    "second_moment":      _combine_second_moment,
    "coord_median":       _combine_coord_median,
    "coord_trimmed_mean": _combine_coord_trimmed_mean,
    "consensus_proj":     _combine_consensus_proj,
    "poly_gate_d2_a":     _combine_poly_gate_d2_a,
    "poly_gate_d2_b":     _combine_poly_gate_d2_b,
}


def aggregate_nonlinear(
    theta0: Dict,
    deltas: List[Dict],
    weights: Sequence[float],
    method: str,
    **kw,
) -> Dict:
    """Server combine of the one-shot {Δ_i} via a (possibly non-linear) ``method``.

    INVESTIGATION AXIS (issue 025) — NOT the production aggregator. The default
    protocol path uses the linear ``aggregate`` and never calls this function.

    Parameters
    ----------
    theta0 : dict
        The shared aligned init θ₀ (the download baseline; known to the server).
    deltas : list of dict
        Per-client cumulative displacements Δ_i (the one-shot uploads).
    weights : sequence of float
        Sample weights w_i (pre-normalised; ``sample_weights(sample_sizes)``).
    method : str
        One of ``NONLINEAR_DEPTH``. ``"weight_avg"`` delegates to the linear
        ``aggregate`` so that path is byte-identical to the production combine.
    **kw :
        Combine-specific overrides forwarded verbatim (e.g. ``c=`` for the poly
        gates, ``residual=`` for consensus_proj, ``eps_rel=`` for the ratio
        gates). Unused by ``weight_avg``.

    Returns
    -------
    theta : dict
        The combined final-student parameters (same shapes/keys as ``theta0``).

    All combines operate on the SAME {Δ_i}, flattened per-parameter into one
    stacked (N, P) tensor, combined, then unflattened back to the state dict.
    """
    if method == "weight_avg":
        # Route to the existing linear path so the baseline stays byte-identical.
        return aggregate(theta0, deltas, weights)
    if method not in _COMBINE_FN:
        raise ValueError(
            f"unknown agg_method {method!r}; expected one of {sorted(NONLINEAR_DEPTH)}")

    import torch

    keys = _state_keys(theta0)
    t0 = _flatten_state(theta0, keys)
    D = torch.stack([_flatten_state(d, keys) for d in deltas])   # (N, P)
    w = torch.as_tensor(list(weights), dtype=D.dtype, device=D.device)
    vec = _COMBINE_FN[method](D, w, t0, **kw)
    return _unflatten_state(vec, theta0, keys)
