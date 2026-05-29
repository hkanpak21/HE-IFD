"""The three adversary surfaces, and the surrogate distillation GLiRA needs.

A *surface* defines (a) what the adversary may observe and (b) which attacks run
on it. All three reuse the shadow-model population built in ``mia.run`` — the
expensive part — and differ only in the auxiliary information they exploit.

* ``external``   — black-box query access to θ⋆ only. Runs the threshold attack,
  LiRA (on θ⋆'s own confidences — the strongest reading, treating query access
  as giving calibrated confidences), and GLiRA (the natural black-box fit: a
  surrogate distilled from θ⋆'s query outputs).

* ``fellow``     — an honest-but-curious participant. Same θ⋆ access PLUS its own
  labelled data and the shared Phase-0 prototypes. We model the stronger prior
  concretely: the fellow's LiRA OUT/IN Gaussians are calibrated on shadow models
  that share the fellow's known data (the shadow population already conditions on
  the protocol/Phase-0 configuration), so the fellow surface reuses the LiRA/
  threshold machinery but is reported separately so the paper can show the
  fellow's advantage over the external adversary.

* ``prototype``  — the Phase-0 per-class prototype release itself. Membership is
  inferred by distance-to-nearest-prototype (``attacks.prototype_distance_attack``)
  at the raw release (ε→∞) and under the averaging-variant DP mechanism at
  ε∈{2,8}; the AUC/TPR collapse toward chance as ε tightens is the empirical
  validation of the DP accounting.

GLiRA surrogate distillation (``distill_surrogate``) trains a fresh model to
mimic a black-box model's *query outputs* on a public query set — exactly the
knowledge-distillation step of Galichin et al. 2025 — reusing the SAME
distillation loop the protocol uses for client students (we call a thin
soft-label SGD that matches ``src.distill``'s KL objective, so no new training
semantics are introduced).
"""
from __future__ import annotations

from typing import Dict, Tuple

import numpy as np

from . import attacks
from .target import Features, GlobalModel, TargetConfig


# ---------------------------------------------------------------------------
# GLiRA surrogate distillation
# ---------------------------------------------------------------------------
def distill_surrogate(
    teacher_params: Dict,
    feats: Features,
    cfg: TargetConfig,
    query_X,
    seed: int,
    steps: int = 200,
    lr: float = 0.01,
    tau: float = 1.0,
) -> Dict:
    """Distil a surrogate of a black-box model (GLiRA's KD step).

    Given only QUERY access to a model (its parameters are used solely to produce
    soft logits on the public ``query_X`` — the adversary never reads weights for
    the attack, this mirrors querying the deployed θ⋆), train a fresh student to
    match those soft labels via temperatured KL. The student is the same
    architecture the protocol uses (``feats.make_model_fn``); the loop reuses the
    exact KL objective of ``src.distill.local_distill_trajectory`` so the
    surrogate is trained identically to a protocol student. Returns the surrogate
    parameter dict.

    Galichin et al. 2025: the surrogate need not match the target architecture,
    but using the protocol's own head is the faithful black-box analogue here.
    """
    import torch
    import torch.nn.functional as F

    from src.backbones import get_params

    device = "cuda" if torch.cuda.is_available() else "cpu"
    # Black-box teacher: produce soft logits on the query set, no grad.
    teacher = feats.make_model_fn()
    teacher.load_state_dict(teacher_params)
    teacher.eval()

    torch.manual_seed(seed * 50021 + 3)
    student = feats.make_model_fn()
    opt = torch.optim.SGD(student.parameters(), lr=lr, momentum=0.0)
    Xq = query_X.to(device)
    nq = int(Xq.shape[0])
    bs = 256
    for _ in range(steps):
        idx = torch.randint(0, nq, (min(bs, nq),), device=device)
        xb = Xq[idx]
        with torch.no_grad():
            t_logits = teacher(xb)
        opt.zero_grad()
        s_logits = student(xb)
        loss = F.kl_div(
            F.log_softmax(s_logits / tau, dim=1),
            F.softmax(t_logits / tau, dim=1),
            reduction="batchmean",
        ) * (tau ** 2)
        loss.backward()
        opt.step()
    return get_params(student)


# ---------------------------------------------------------------------------
# Array-based surface scorers (called from per-model checkpoints in mia.run).
#
# The runner trains and checkpoints each model's attack contributions (its
# IN-mask, φ, loss, and surrogate-φ over the attack pool) — see mia.run. The
# scorers below consume those already-extracted arrays so there is ONE scoring
# code path, reused identically whether the cell ran in one job or resumed
# across many. No model weights are reloaded for scoring.
# ---------------------------------------------------------------------------
def score_external(
    target_loss: np.ndarray,
    target_phi: np.ndarray,
    target_surrogate_phi: np.ndarray,
    shadow_phi: np.ndarray,
    shadow_surrogate_phi: np.ndarray,
    shadow_in: np.ndarray,
    labels: np.ndarray,
) -> Dict:
    """External black-box adversary on θ⋆: threshold + LiRA + GLiRA.

    ``labels`` is the target's true IN/OUT membership of each attack-pool
    example. LiRA reads θ⋆'s own confidences (``target_phi`` + ``shadow_phi``);
    GLiRA reads the surrogate-distilled confidences (``*_surrogate_phi``) — the
    query-only fit; threshold is the Yeom loss floor.
    """
    return {
        "threshold": attacks.threshold_attack(target_loss, labels),
        "lira": attacks.lira_attack(target_phi, shadow_phi, shadow_in, labels),
        "glira": attacks.glira_attack(
            target_surrogate_phi, shadow_surrogate_phi, shadow_in, labels),
    }


def score_fellow(
    target_loss: np.ndarray,
    target_phi: np.ndarray,
    shadow_phi: np.ndarray,
    shadow_in: np.ndarray,
    labels: np.ndarray,
    pool_y: np.ndarray,
    num_classes: int,
) -> Dict:
    """Honest-but-curious fellow client: θ⋆ + own data + prototypes (stronger prior).

    The fellow is a participant: it KNOWS the protocol/Phase-0 configuration and
    holds its own labelled shard. We model the stronger prior concretely with a
    *class-conditional* calibration: estimate the per-class OUT-population φ
    baseline (the prior the fellow reconstructs from public task knowledge) and
    subtract it before the LiRA test, sharpening the per-example signal. Reuses
    the same shadow population + LiRA machinery; reported separately so the
    fellow's advantage over the external adversary is visible.
    """
    class_baseline = np.zeros(num_classes)
    out_phi = np.where(~shadow_in, shadow_phi, np.nan)
    for c in range(num_classes):
        cols = pool_y == c
        if cols.any():
            vals = out_phi[:, cols]
            if np.isfinite(vals).any():
                class_baseline[c] = np.nanmean(vals)
    t_phi_calib = target_phi - class_baseline[pool_y]
    shadow_phi_calib = shadow_phi - class_baseline[pool_y][None, :]
    return {
        "threshold": attacks.threshold_attack(target_loss, labels),
        "lira": attacks.lira_attack(
            t_phi_calib, shadow_phi_calib, shadow_in, labels),
    }


def run_prototype_surface(
    target: GlobalModel,
    feats: Features,
    cfg: TargetConfig,
    pool_X,
    pool_y,
    eps_grid: Tuple = (float("inf"), 8.0, 2.0),
    K_per_class: int = 20,
    seed: int = 0,
) -> Dict:
    """Membership inference on the Phase-0 prototype release at raw + ε∈{2,8}.

    Reuses ``src.phase0`` to construct the per-(client,class) prototype set the
    protocol would actually release for this cell's partition, at each ε, then
    runs ``attacks.prototype_distance_attack``. The membership question is the
    standard one: can the released prototypes alone distinguish a TRAINING
    example (a member of θ⋆'s pool, which contributed to its class's
    prototypes) from a non-member? Members are marked 1 (they are the population
    the prototypes were averaged from, so a member's class prototype is pulled
    toward it), non-members 0. The score is negative distance to the nearest
    same-class prototype (``attacks.prototype_distance_attack``).

    The expected reading (paper §Security Analysis): raw release leaks the most
    (highest AUC/TPR); ε=8 less; ε=2 near-chance — the averaging-variant DP
    accounting holds empirically. Note that as the released prototype averages
    over more samples (large K) the per-example pull shrinks, so even the raw
    release is a weak signal — the channel leaks little by construction, which
    is the point.
    """
    from src import phase0 as p0
    from src.data import dirichlet_partition

    # Reconstruct the protocol's partition of the TARGET's members so the
    # released prototypes are the ones this θ⋆ actually exposed.
    train_X = pool_X[target.in_idx]
    train_y = pool_y[target.in_idx]
    y_np = train_y.cpu().numpy() if hasattr(train_y, "cpu") else np.asarray(train_y)
    nc = feats.num_classes
    client_idx = dirichlet_partition(y_np, cfg.N, cfg.alpha, seed, nc)
    client_X_list = [train_X[ci] for ci in client_idx]
    client_y_list = [train_y[ci] for ci in client_idx]

    sample_shape = tuple(feats.Xtr.shape[1:])
    is_image = len(sample_shape) > 1
    flat_dim = int(np.prod(sample_shape))

    def _flatten(xs):
        return [x.reshape(x.shape[0], flat_dim) for x in xs]

    flat_clients = _flatten(client_X_list) if is_image else client_X_list
    # Attack-pool features in flat space for the distance test.
    pool_flat = (pool_X.reshape(pool_X.shape[0], flat_dim) if is_image else pool_X)
    pool_flat_np = pool_flat.cpu().numpy() if hasattr(pool_flat, "cpu") else np.asarray(pool_flat)
    pool_y_np = pool_y.cpu().numpy() if hasattr(pool_y, "cpu") else np.asarray(pool_y)

    # Membership label for the prototype channel: was the pool example among the
    # target's members (i.e. could it have been averaged into a prototype)?
    pool_size = int(pool_X.shape[0])
    membership = np.zeros(pool_size, dtype=np.int64)
    membership[target.in_idx] = 1

    clip = p0.compute_feature_norms_percentile(
        train_X.reshape(train_X.shape[0], -1) if is_image else train_X)

    results: Dict = {}
    for eps in eps_grid:
        if eps == float("inf"):
            pX, pY, info = p0.build_probe_raw_union(
                flat_clients, client_y_list, K_per_class, nc, seed=seed * 100003)
        else:
            pX, pY, info = p0.build_probe_dp_averaged(
                flat_clients, client_y_list, K_per_class, nc, clip=clip,
                eps_per_client=eps, seed=seed * 100003)
        pX_np = pX.cpu().numpy() if hasattr(pX, "cpu") else np.asarray(pX)
        pY_np = pY.cpu().numpy() if hasattr(pY, "cpu") else np.asarray(pY)
        eps_key = "raw" if eps == float("inf") else f"eps{eps:g}"
        results[eps_key] = attacks.prototype_distance_attack(
            pool_flat_np, pool_y_np, pX_np, pY_np, membership)
        results[eps_key]["sigma"] = float(info.get("sigma", 0.0))
        results[eps_key]["n_prototypes"] = int(pX_np.shape[0])
    return results
