"""Attack-scoring metrics: ROC, AUC, and TPR at a fixed low FPR.

The membership-inference literature scores attacks in the *low-false-positive*
regime, because an attacker who is confidently right about a few members is far
more dangerous than one with good average-case accuracy (Carlini et al. 2022,
"Membership Inference Attacks From First Principles", §3). We therefore report:

* the full ROC curve (arrays, so the paper can plot it on log-log axes),
* the AUC, and
* TPR @ 0.1% FPR — the headline number issue 021 asks for.

Every attack in this suite reduces to producing one real-valued *membership
score* per example (higher ⇒ more likely a member) plus a binary IN/OUT label;
these helpers turn (scores, labels) into the metrics. Pure NumPy — no torch — so
this module imports cleanly on the login node for a syntax/CLI check.
"""
from __future__ import annotations

from typing import Dict, List, Sequence

import numpy as np


def roc_curve(scores: Sequence[float], labels: Sequence[int]):
    """Return (fpr, tpr, thresholds) for membership scores vs IN/OUT labels.

    ``scores[i]`` is the attack's confidence that example ``i`` is a member;
    ``labels[i]`` is 1 for a true member (IN) and 0 for a non-member (OUT).
    Higher score ⇒ predicted member. Implemented directly (no sklearn) so the
    suite has no extra dependency: sort by descending score and sweep the
    decision threshold, accumulating true/false positives.

    Returns three equal-length arrays. ``fpr``/``tpr`` are monotone
    non-decreasing and both start at 0 (threshold above every score ⇒ nothing
    flagged) and end at 1.
    """
    scores = np.asarray(scores, dtype=np.float64)
    labels = np.asarray(labels, dtype=np.int64)
    n = scores.shape[0]
    if n == 0:
        return np.array([0.0, 1.0]), np.array([0.0, 1.0]), np.array([np.inf, -np.inf])

    order = np.argsort(-scores, kind="mergesort")  # stable, descending
    s_sorted = scores[order]
    l_sorted = labels[order]

    P = int(labels.sum())
    Neg = n - P
    # Cumulative TP / FP as the threshold descends through the sorted scores.
    tp_cum = np.cumsum(l_sorted)
    fp_cum = np.cumsum(1 - l_sorted)

    # Collapse ties: only keep the last index of each distinct score so a tied
    # block contributes a single (fpr, tpr) vertex (standard ROC tie handling).
    distinct = np.ones(n, dtype=bool)
    distinct[:-1] = s_sorted[1:] != s_sorted[:-1]
    tp_at = tp_cum[distinct]
    fp_at = fp_cum[distinct]

    tpr = tp_at / P if P > 0 else np.zeros_like(tp_at, dtype=np.float64)
    fpr = fp_at / Neg if Neg > 0 else np.zeros_like(fp_at, dtype=np.float64)

    # Prepend the origin (0,0) so the curve and trapezoidal AUC are well-formed.
    fpr = np.concatenate([[0.0], fpr])
    tpr = np.concatenate([[0.0], tpr])
    thr = np.concatenate([[np.inf], s_sorted[distinct]])
    return fpr, tpr, thr


def auc(fpr: Sequence[float], tpr: Sequence[float]) -> float:
    """Trapezoidal area under the ROC curve."""
    fpr = np.asarray(fpr, dtype=np.float64)
    tpr = np.asarray(tpr, dtype=np.float64)
    if fpr.shape[0] < 2:
        return 0.5
    return float(np.trapz(tpr, fpr))


def tpr_at_fpr(fpr: Sequence[float], tpr: Sequence[float], target_fpr: float) -> float:
    """TPR at the largest FPR that does not exceed ``target_fpr``.

    Linear-interpolates between ROC vertices so the headline TPR@0.1%FPR is not
    quantised to whichever discrete threshold happened to land near 0.001. If no
    vertex reaches ``target_fpr`` (too few negatives to resolve that FPR) returns
    the TPR at the smallest available FPR > 0, which is the conservative reading.
    """
    fpr = np.asarray(fpr, dtype=np.float64)
    tpr = np.asarray(tpr, dtype=np.float64)
    if fpr.shape[0] == 0:
        return 0.0
    if target_fpr <= fpr[0]:
        return float(tpr[0])
    if target_fpr >= fpr[-1]:
        return float(tpr[-1])
    # np.interp requires increasing x; fpr is non-decreasing by construction.
    return float(np.interp(target_fpr, fpr, tpr))


def score_attack(
    scores: Sequence[float],
    labels: Sequence[int],
    fpr_targets: Sequence[float] = (0.001, 0.01, 0.1),
) -> Dict:
    """Full metric bundle for one attack's (scores, labels).

    Returns a JSON-serialisable dict carrying the AUC, the TPR at each requested
    FPR (default 0.1%, 1%, 10% — 0.1% is the headline), the count of members /
    non-members scored, and the ROC arrays (as plain lists) so the paper figure
    can be drawn directly from the per-cell JSON.
    """
    fpr, tpr, thr = roc_curve(scores, labels)
    a = auc(fpr, tpr)
    tprs = {f"tpr_at_fpr_{t:g}": tpr_at_fpr(fpr, tpr, t) for t in fpr_targets}
    labels = np.asarray(labels, dtype=np.int64)
    return {
        "auc": a,
        **tprs,
        "n_members": int(labels.sum()),
        "n_nonmembers": int((1 - labels).sum()),
        "roc_fpr": [float(x) for x in fpr],
        "roc_tpr": [float(x) for x in tpr],
    }


def aggregate_scores(per_seed: List[Dict]) -> Dict:
    """Mean ± std of the scalar metrics across repeated runs (seeds).

    ROC arrays differ in length across runs, so only the scalar metrics
    (auc, tpr_at_fpr_*) are aggregated; the per-run ROC arrays stay in the
    per-cell JSON for plotting. Keys absent from a run are skipped.
    """
    if not per_seed:
        return {}
    scalar_keys = [
        k for k in per_seed[0]
        if isinstance(per_seed[0][k], (int, float)) and not k.startswith("n_")
    ]
    out: Dict = {}
    for k in scalar_keys:
        vals = np.asarray([r[k] for r in per_seed if k in r], dtype=np.float64)
        if vals.size == 0:
            continue
        out[f"{k}_mean"] = float(vals.mean())
        out[f"{k}_std"] = float(vals.std())
    out["n_runs"] = len(per_seed)
    return out
