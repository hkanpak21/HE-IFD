"""Loss-threshold MIA baseline (Yeom et al. 2018, ``yeom2018privacy``).

The simplest membership-inference attack: compute the cross-entropy loss
of the target model on each candidate; declare "member" if the loss is
below a threshold. Since we only report AUC (not accuracy at a particular
threshold), no threshold tuning is needed -- AUC ranks candidates by
``-loss``, so low-loss points are predicted as members.

Per the issue 21 spec this is paired with LiRA as the canonical baseline.
"""
from __future__ import annotations

import logging
from typing import Tuple

import numpy as np


LOG = logging.getLogger("mia_lib.loss_threshold")


def per_point_cross_entropy(
    target_model, xs, ys, device: str = "cuda", batch_size: int = 512
) -> np.ndarray:
    import torch
    import torch.nn.functional as F

    target_model = target_model.to(device)
    target_model.eval()
    losses = []
    ys_t = ys if hasattr(ys, "to") else __import__("torch").as_tensor(ys)
    with torch.no_grad():
        for i in range(0, len(xs), batch_size):
            bx = xs[i : i + batch_size].to(device, non_blocking=True)
            by = ys_t[i : i + batch_size].to(device, non_blocking=True)
            logits = target_model(bx)
            # reduction='none' so we get per-point loss; same loss the
            # released student would have minimised during distillation.
            l = F.cross_entropy(logits, by, reduction="none")
            losses.append(l.cpu().numpy())
    return np.concatenate(losses, axis=0)


def loss_threshold_attack(
    *,
    target_model,
    candidate_xs,
    candidate_ys,
    is_member,
    device: str = "cuda",
) -> Tuple[float, np.ndarray]:
    """Compute AUC for the loss-threshold attack.

    Score is ``-loss`` so that "high score" => "predicted member" matches
    the convention used by ``lira.auc_from_scores``.
    """
    from prototypes.mia_lib.lira import auc_from_scores

    losses = per_point_cross_entropy(
        target_model, candidate_xs, candidate_ys, device=device
    )
    scores = -losses
    return auc_from_scores(scores, is_member), scores
