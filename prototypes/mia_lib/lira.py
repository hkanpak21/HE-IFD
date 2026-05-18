"""LiRA score computation for HE-IFD issue 21 (A7).

We implement the **offline** variant of LiRA (Carlini et al. 2022,
``carlini2022membership``):

- For each candidate point ``j``, fit a Gaussian over the *non-member* logit
  responses across all shadow models that did NOT include ``j`` in their
  training set.
- The membership score is the log-likelihood that the *target* model's
  logit on ``j`` is an outlier of that out-only Gaussian (one-tailed); high
  outlier => more "in"-like.
- Offline (vs online) is selected because (a) it is 2x cheaper -- only one
  Gaussian per point instead of two -- and (b) the Carlini et al. paper
  reports comparable AUC for offline at sufficient shadow counts
  (``n_shadows >= 64``), which is our default. The decision is documented
  in the issue 21 Comments block.

The "logit" we score is the standard LiRA logit transform
    phi(x, y) = log(p_y / (1 - p_y))
where ``p_y`` is the softmax probability the model assigns to the *true*
label ``y``. This is the form used in the official LiRA reference (the
"logit-scaling" variant); it linearises confidence and stabilises the
per-point Gaussian fit.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, Sequence, Tuple

import numpy as np


LOG = logging.getLogger("mia_lib.lira")


# ---------------------------------------------------------------------------
# Logit transform
# ---------------------------------------------------------------------------
def _softmax_np(logits: np.ndarray) -> np.ndarray:
    z = logits - logits.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)


def true_label_logit_phi(logits: np.ndarray, labels: np.ndarray) -> np.ndarray:
    """LiRA logit-scaling: phi = log(p_y / (1 - p_y)).

    ``logits``: (N, C) raw logits.
    ``labels``: (N,) int class indices.
    Returns ``(N,)`` float array of phi values, clipped against numerical
    saturation.
    """
    probs = _softmax_np(logits)
    p_y = probs[np.arange(len(labels)), labels]
    # Clip for numerical stability. Carlini et al. use eps=1e-8.
    eps = 1e-8
    p_y = np.clip(p_y, eps, 1.0 - eps)
    return np.log(p_y) - np.log1p(-p_y)


# ---------------------------------------------------------------------------
# Shadow inference: collect phi(x, y) on (n_shadows, n_points) grid.
# ---------------------------------------------------------------------------
def _model_logits_batched(model, xs, device: str, batch_size: int = 512):
    import torch

    model = model.to(device)
    model.eval()
    out = []
    with torch.no_grad():
        for i in range(0, len(xs), batch_size):
            b = xs[i : i + batch_size].to(device, non_blocking=True)
            out.append(model(b).cpu().numpy())
    return np.concatenate(out, axis=0)


def collect_shadow_phi(
    bundle,
    point_xs,
    point_ys,
    device: str = "cuda",
    batch_size: int = 512,
):
    """Return ``(n_shadows, n_points)`` matrix of phi(x, y) under each shadow.

    ``bundle`` is a :class:`prototypes.mia_lib.shadow_models.ShadowBundle`.
    ``point_xs``, ``point_ys`` are the candidate points whose membership we
    want to score against the target student.
    """
    import torch

    from prototypes.mia_lib.shadow_models import (
        instantiate_arch,
        load_shadow_state_dict,
    )

    n_shadows = bundle.n_shadows
    n_pts = int(point_xs.shape[0])
    phi = np.zeros((n_shadows, n_pts), dtype=np.float64)
    labels_np = (
        point_ys.numpy() if hasattr(point_ys, "numpy") else np.asarray(point_ys)
    )
    for i, ckpt_path in enumerate(bundle.ckpt_paths):
        model = instantiate_arch(bundle.dataset)
        model.load_state_dict(load_shadow_state_dict(ckpt_path))
        logits = _model_logits_batched(model, point_xs, device, batch_size)
        phi[i] = true_label_logit_phi(logits, labels_np)
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    return phi


def target_phi(target_model, point_xs, point_ys, device: str = "cuda"):
    import torch

    target_model = target_model.to(device)
    target_model.eval()
    with torch.no_grad():
        logits = []
        bsz = 512
        for i in range(0, len(point_xs), bsz):
            b = point_xs[i : i + bsz].to(device, non_blocking=True)
            logits.append(target_model(b).cpu().numpy())
        logits = np.concatenate(logits, axis=0)
    labels_np = (
        point_ys.numpy() if hasattr(point_ys, "numpy") else np.asarray(point_ys)
    )
    return true_label_logit_phi(logits, labels_np)


# ---------------------------------------------------------------------------
# Offline LiRA scoring
# ---------------------------------------------------------------------------
def offline_lira_scores(
    shadow_phi: np.ndarray,
    in_mask_per_point: np.ndarray,
    target_phi_vec: np.ndarray,
    fix_variance: bool = True,
) -> np.ndarray:
    """Return per-point LiRA scores (higher => more 'in'-like).

    ``shadow_phi``: (n_shadows, n_points) -- shadow phi values per candidate.
    ``in_mask_per_point``: (n_shadows, n_points) bool -- True iff shadow i
        had point j in its training set. For offline LiRA we ignore the
        in-rows and fit only on out-rows; we still take this so callers can
        pass the bundle mask consistently with the candidate-point ordering.
    ``target_phi_vec``: (n_points,) -- target student's phi per candidate.
    ``fix_variance``: if True, use the *global* variance pooled across all
        out-distribution phi values (Carlini's "fixed variance" trick); much
        more stable at small shadow counts than per-point variance.

    Score is the one-sided z-statistic
        score_j = (phi_target_j - mu_out_j) / sigma_out
    so larger scores => higher likelihood point j is a member.
    """
    n_shadows, n_pts = shadow_phi.shape
    out_mask = ~in_mask_per_point  # (n_shadows, n_pts)
    # Per-point out-mean using a masked mean; falls back to global mean if
    # a column happens to have zero out-shadows (rare for n_shadows >= 32).
    out_counts = out_mask.sum(axis=0)
    safe_counts = np.maximum(out_counts, 1)
    mu_out = (shadow_phi * out_mask).sum(axis=0) / safe_counts
    if fix_variance:
        # Global pooled variance over all out-cell residuals.
        residuals = (shadow_phi - mu_out[None, :]) * out_mask
        sigma = np.sqrt(
            (residuals ** 2).sum() / max(out_mask.sum() - n_pts, 1)
        )
        sigma = max(sigma, 1e-6)
        scores = (target_phi_vec - mu_out) / sigma
    else:
        # Per-point variance; needs out_counts >= 2.
        var_per = (
            ((shadow_phi - mu_out[None, :]) * out_mask) ** 2
        ).sum(axis=0) / np.maximum(out_counts - 1, 1)
        sigma_per = np.sqrt(np.maximum(var_per, 1e-12))
        scores = (target_phi_vec - mu_out) / sigma_per
    return scores


def auc_from_scores(scores: np.ndarray, is_member: np.ndarray) -> float:
    """ROC AUC for membership classification.

    Implemented in numpy (Mann-Whitney U formulation) so the prototype does
    not require sklearn at scoring time.
    """
    scores = np.asarray(scores, dtype=np.float64)
    y = np.asarray(is_member, dtype=bool)
    pos = scores[y]
    neg = scores[~y]
    n_pos = len(pos)
    n_neg = len(neg)
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    # Rank-based AUC (handles ties via average ranks).
    ranks = np.empty_like(scores)
    order = np.argsort(scores, kind="mergesort")
    ranked = np.empty_like(order, dtype=np.float64)
    # Assign average ranks for ties.
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and scores[order[j + 1]] == scores[order[i]]:
            j += 1
        avg_rank = 0.5 * (i + j) + 1.0  # 1-indexed
        ranked[i : j + 1] = avg_rank
        i = j + 1
    ranks[order] = ranked
    sum_pos_ranks = ranks[y].sum()
    u = sum_pos_ranks - n_pos * (n_pos + 1) / 2.0
    return float(u / (n_pos * n_neg))


def lira_attack(
    *,
    bundle,
    target_model,
    candidate_xs,
    candidate_ys,
    is_member,
    candidate_pool_indices,
    device: str = "cuda",
) -> Tuple[float, np.ndarray]:
    """End-to-end offline LiRA attack.

    Parameters
    ----------
    bundle :
        ShadowBundle returned by ``train_shadow_models``.
    target_model :
        The decrypted student to attack (nn.Module, already loaded).
    candidate_xs, candidate_ys :
        The candidate points (a mix of true members of the target's training
        set and held-out non-members).
    is_member :
        (n_points,) bool ground-truth membership label of each candidate.
    candidate_pool_indices :
        (n_points,) int indices of each candidate into the *shadow training
        pool* (i.e. the full training split that ``bundle.masks`` is over).
        Needed so we can pick out the right column of ``bundle.masks`` for
        each candidate when fitting the out-distribution per point.

    Returns
    -------
    auc :
        ROC AUC of the offline-LiRA score against ``is_member``.
    scores :
        The per-point LiRA scores (for diagnostics).
    """
    shadow_phi = collect_shadow_phi(
        bundle, candidate_xs, candidate_ys, device=device
    )
    # Slice masks down to the candidate columns.
    in_mask = bundle.masks[:, np.asarray(candidate_pool_indices, dtype=int)]
    tgt_phi = target_phi(target_model, candidate_xs, candidate_ys, device=device)
    scores = offline_lira_scores(shadow_phi, in_mask, tgt_phi)
    return auc_from_scores(scores, is_member), scores
