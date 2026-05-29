"""The three membership-inference attacks.

All three reduce the target model (and, for the shadow attacks, a population of
shadow models) to one real-valued membership score per attack example, scored by
``mia.metrics``. Each attack is implemented to match its published algorithm.

1. ``threshold_attack`` — Yeom et al. 2018, "Privacy Risk in Machine Learning"
   (``yeom2018privacy``). The membership score is simply the *negative loss* of
   the target on the example: members are trained-on, so they have lower loss.
   No shadow models; the threshold is swept implicitly by the ROC. This is the
   interpretable floor.

2. ``lira_attack`` — Carlini et al. 2022, "Membership Inference Attacks From
   First Principles" (``carlini2022membership``), the offline+online
   likelihood-ratio attack. Algorithm ported from the TensorFlow-Privacy
   reference ``research/mi_lira_2021`` (``score.py`` / ``plot.py``):
     * For each example x, fit a Gaussian to the LiRA logit-scaled confidences
       φ from the shadow models that did NOT train on x  (OUT, μ_out, σ_out),
       and — in the online variant — also from those that DID  (IN, μ_in, σ_in).
     * The membership score is the likelihood ratio
         Λ(x) = N(φ_target ; μ_in, σ_in) / N(φ_target ; μ_out, σ_out)
       (online), or the one-sided  −log N(φ_target ; μ_out, σ_out)  (offline,
       used when no IN shadow models exist for x).
   We compute both and report the online variant where available, falling back
   per-example to offline. Variances are pooled across examples (``fix_variance``
   in the reference) for stability at ~64 shadows.

3. ``glira_attack`` — Galichin et al. 2025, "GLiRA: Black-Box Membership
   Inference Attack via Knowledge Distillation" (``galichin2025glira``).
   Implemented from the paper (no public repo). GLiRA is LiRA made black-box:
   the adversary cannot read the target's internals, only query it. It distils a
   *surrogate* student from the target's outputs (knowledge distillation), then
   runs the LiRA Gaussian likelihood-ratio test on the SURROGATE's logit-scaled
   confidences instead of the target's. The shadow population is likewise a set
   of surrogate-distilled models so the IN/OUT statistics are in the surrogate's
   confidence space. The paper's key claim is that distillation-guided shadows
   match white-box LiRA while needing only query access — the exact external
   surface of θ⋆ in our protocol.

A note on the protocol: a "model trained on x" here means a global model whose
*pre-aggregation* training subset contained x. Membership of the released θ⋆ is
therefore membership in the union of the clients' shards — the quantity §VI must
bound. The shadow IN/OUT masks (``mia.target.in_out_mask``) encode exactly this.
"""
from __future__ import annotations

from typing import Dict

import numpy as np

from .metrics import score_attack


# ===========================================================================
# 1. Yeom et al. 2018 — loss/confidence threshold
# ===========================================================================
def threshold_attack(target_loss: np.ndarray, labels: np.ndarray) -> Dict:
    """Yeom et al. 2018 threshold attack.

    ``target_loss[i]`` is the target model's per-example loss; ``labels[i]`` is
    1 for a member. Membership score = −loss (members have lower loss ⇒ higher
    score). The ROC sweeps the implicit threshold, so we report TPR@0.1%FPR /
    AUC directly. No shadow models, no calibration — the cheap floor.
    """
    scores = -np.asarray(target_loss, dtype=np.float64)
    return score_attack(scores, labels)


def confidence_threshold_attack(target_conf: np.ndarray, labels: np.ndarray) -> Dict:
    """Yeom-style confidence variant: score = true-class softmax confidence.

    Equivalent ranking to the loss variant for a monotone link, provided as a
    convenience so the prototype-channel surface (which works in confidence
    space) can call a threshold attack without a loss tensor."""
    return score_attack(np.asarray(target_conf, dtype=np.float64), labels)


# ===========================================================================
# LiRA Gaussian machinery (shared by LiRA and GLiRA — only the confidence
# *space* differs: target's own confidences for LiRA, surrogate's for GLiRA).
# ===========================================================================
def _gaussian_logpdf(x: np.ndarray, mu: np.ndarray, var: np.ndarray) -> np.ndarray:
    var = np.clip(var, 1e-12, None)
    return -0.5 * (np.log(2.0 * np.pi * var) + (x - mu) ** 2 / var)


def lira_scores_from_shadow_stats(
    target_phi: np.ndarray,            # (n_examples,) target's φ on each example
    shadow_phi: np.ndarray,            # (n_models, n_examples) shadow φ
    shadow_in_mask: np.ndarray,        # (n_models, n_examples) bool: model m trained on x
    fix_variance: bool = True,
) -> np.ndarray:
    """Per-example LiRA membership scores from shadow-model statistics.

    For each example x:
      * gather φ from OUT shadow models (¬trained on x) → Gaussian (μ_out,σ_out²),
      * gather φ from IN  shadow models ( trained on x) → Gaussian (μ_in, σ_in²),
      * online score  = logpdf(φ_t | in) − logpdf(φ_t | out)  (likelihood ratio),
      * offline score = −logpdf(φ_t | out)                     (one-sided; used
        per-example when that x has zero IN shadow models).

    ``fix_variance`` pools the per-example variances into one global σ_in / σ_out
    (the reference impl's ``fix_variance=True``), which is markedly more stable
    than per-example variance at ~64 shadows. Directly follows
    ``mi_lira_2021/plot.py``'s ``generate_ours`` scoring.
    """
    target_phi = np.asarray(target_phi, dtype=np.float64)
    shadow_phi = np.asarray(shadow_phi, dtype=np.float64)
    shadow_in_mask = np.asarray(shadow_in_mask, dtype=bool)
    n_models, n_ex = shadow_phi.shape

    mu_in = np.full(n_ex, np.nan)
    mu_out = np.full(n_ex, np.nan)
    var_in = np.full(n_ex, np.nan)
    var_out = np.full(n_ex, np.nan)
    n_in = np.zeros(n_ex, dtype=int)
    n_out = np.zeros(n_ex, dtype=int)

    for j in range(n_ex):
        col = shadow_phi[:, j]
        m = shadow_in_mask[:, j]
        ins = col[m]
        outs = col[~m]
        n_in[j] = ins.size
        n_out[j] = outs.size
        if ins.size > 0:
            mu_in[j] = ins.mean()
            var_in[j] = ins.var() if ins.size > 1 else np.nan
        if outs.size > 0:
            mu_out[j] = outs.mean()
            var_out[j] = outs.var() if outs.size > 1 else np.nan

    if fix_variance:
        # Pool a single global variance for IN and OUT (reference default).
        gv_in = np.nanmean(var_in) if np.isfinite(var_in).any() else 1.0
        gv_out = np.nanmean(var_out) if np.isfinite(var_out).any() else 1.0
        gv_in = gv_in if np.isfinite(gv_in) and gv_in > 0 else 1.0
        gv_out = gv_out if np.isfinite(gv_out) and gv_out > 0 else 1.0
        var_in = np.full(n_ex, gv_in)
        var_out = np.full(n_ex, gv_out)
    else:
        # Replace unusable (NaN / single-sample) variances with the global mean.
        var_in = _fill_nan(var_in)
        var_out = _fill_nan(var_out)

    scores = np.empty(n_ex, dtype=np.float64)
    for j in range(n_ex):
        has_out = n_out[j] > 0 and np.isfinite(mu_out[j])
        has_in = n_in[j] > 0 and np.isfinite(mu_in[j])
        lo_out = _gaussian_logpdf(target_phi[j], mu_out[j], var_out[j]) if has_out else 0.0
        lo_in = _gaussian_logpdf(target_phi[j], mu_in[j], var_in[j]) if has_in else None
        if has_in and has_out:
            scores[j] = lo_in - lo_out          # online likelihood ratio
        elif has_out:
            scores[j] = -lo_out                 # offline one-sided
        elif has_in:
            scores[j] = lo_in                    # degenerate: only IN observed
        else:
            scores[j] = 0.0                      # no shadow info ⇒ chance
    return scores


def _fill_nan(v: np.ndarray) -> np.ndarray:
    v = v.copy()
    finite = np.isfinite(v)
    fill = v[finite].mean() if finite.any() else 1.0
    fill = fill if np.isfinite(fill) and fill > 0 else 1.0
    v[~finite] = fill
    return np.clip(v, 1e-12, None)


# ===========================================================================
# 2. Carlini et al. 2022 — LiRA (white/grey-box: target's own confidences)
# ===========================================================================
def lira_attack(
    target_phi: np.ndarray,
    shadow_phi: np.ndarray,
    shadow_in_mask: np.ndarray,
    labels: np.ndarray,
    fix_variance: bool = True,
) -> Dict:
    """Carlini et al. 2022 LiRA.

    ``target_phi`` — the target model's LiRA logit-scaled confidence φ on each
    attack example. ``shadow_phi`` / ``shadow_in_mask`` — the (n_models,
    n_examples) shadow φ matrix and IN/OUT membership of each shadow model.
    ``labels`` — the TARGET's true IN/OUT membership of each example (the ground
    truth being attacked). Returns the metric bundle from ``score_attack``.
    """
    scores = lira_scores_from_shadow_stats(
        target_phi, shadow_phi, shadow_in_mask, fix_variance=fix_variance)
    return score_attack(scores, labels)


# ===========================================================================
# 3. Galichin et al. 2025 — GLiRA (black-box: surrogate-distilled confidences)
# ===========================================================================
def glira_attack(
    target_surrogate_phi: np.ndarray,     # φ of the surrogate distilled from θ⋆
    shadow_surrogate_phi: np.ndarray,     # (n_models, n_ex) surrogate-φ of shadows
    shadow_in_mask: np.ndarray,
    labels: np.ndarray,
    fix_variance: bool = True,
) -> Dict:
    """Galichin et al. 2025 GLiRA — distillation-guided black-box LiRA.

    Structurally identical to ``lira_attack`` but every φ is computed on a
    *surrogate* distilled from the corresponding model's QUERY outputs (the
    target surrogate from θ⋆; each shadow surrogate from that shadow's outputs),
    never from the model's own internals. This is GLiRA's core idea: replace
    LiRA's white-box per-model confidences with confidences of a knowledge-
    distilled black-box surrogate, recovering LiRA-level separation under
    query-only access. The surrogate distillation itself is done in
    ``mia.surfaces`` (it needs a model factory + the protocol's data); this
    function performs the likelihood-ratio test in surrogate-φ space.
    """
    scores = lira_scores_from_shadow_stats(
        target_surrogate_phi, shadow_surrogate_phi, shadow_in_mask,
        fix_variance=fix_variance)
    return score_attack(scores, labels)


# ===========================================================================
# Prototype-channel membership test (used by the prototype surface)
# ===========================================================================
def prototype_distance_attack(
    target_feats: np.ndarray,        # (n_ex, d) raw features of attack examples
    target_labels: np.ndarray,       # (n_ex,) class of each example
    prototypes: np.ndarray,          # (n_proto, d) released per-class prototypes
    proto_labels: np.ndarray,        # (n_proto,) class of each prototype
    membership: np.ndarray,          # (n_ex,) 1 if example was in the prototype set
) -> Dict:
    """Direct membership inference on the Phase-0 prototype release.

    The prototype channel releases per-(client,class) feature means (raw, or
    Gaussian-noised under the averaging-variant DP mechanism). An example that
    was averaged into a class-c prototype pulls that prototype toward itself, so
    the membership signal is the *negative distance* from the example to the
    nearest released prototype of its own class: members sit closer.

    This is the empirical analogue of the paper's averaging-variant DP claim —
    at ε→∞ (raw) the distance gap (and hence AUC/TPR) should be large; under
    ε∈{2,8} the Gaussian noise should compress it toward chance, validating that
    the released summaries leak no more than the (ε,δ) budget permits.
    """
    target_feats = np.asarray(target_feats, dtype=np.float64)
    prototypes = np.asarray(prototypes, dtype=np.float64)
    target_labels = np.asarray(target_labels)
    proto_labels = np.asarray(proto_labels)
    n_ex = target_feats.shape[0]
    scores = np.full(n_ex, -np.inf, dtype=np.float64)
    for c in np.unique(target_labels):
        ex_mask = target_labels == c
        proto_mask = proto_labels == c
        if not proto_mask.any() or not ex_mask.any():
            continue
        ex = target_feats[ex_mask]                     # (k, d)
        pr = prototypes[proto_mask]                    # (p, d)
        # squared euclidean to nearest same-class prototype
        d2 = ((ex[:, None, :] - pr[None, :, :]) ** 2).sum(-1).min(axis=1)
        scores[ex_mask] = -d2                          # closer ⇒ higher score
    finite = np.isfinite(scores)
    if not finite.all():
        # examples of a class with no released prototype: assign the min score
        scores[~finite] = scores[finite].min() if finite.any() else 0.0
    return score_attack(scores, membership)
