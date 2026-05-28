"""Phase-0 alignment: build the shared, aligned initialization θ₀.

Phase 0 is the one place a signal leaves the clients in clear (the alignment
probe), so it is the locus of the differential-privacy guarantee. Every client
departs the K-step distillation from the SAME θ₀; that shared, probe-aligned
start is what keeps the later single linear aggregate inside one loss basin.

This module ports the notebook's Section 0.4 probe builders verbatim and adds
two deep-module entry points used by ``protocol.run_cell``:

  * ``build_probe(strategy, ...)`` — dispatch to the chosen alignment strategy,
    returning a probe (X, y) and an ``info`` dict (probe_size, sigma). It
    encapsulates the averaging-variant DP accounting:
        sensitivity = clip / K_per_class
        sigma       = sensitivity * sqrt(2 * ln(1.25 / delta)) / eps      (eps<inf)
        sigma       = 0                                                   (eps==inf)
  * ``warmup_init(...)`` — supervised SGD on a probe to produce θ₀.

Strategies (notebook method panel):
  ``none``        : no Phase 0 — θ₀ is the fresh random init (no probe built).
  ``warmup_only`` : warm on the labelled probe, but DO NOT distil afterwards.
                    This is the probe-only baseline (handled in ``protocol``,
                    not here, because it short-circuits the protocol).
  ``labelled``    : warm θ₀ on a held-out labelled probe of size P (cheating-
                    with-public-data baseline).
  ``raw_union``   : θ₀ warmed on the union of K raw clipped samples/class/client
                    (no DP — the no-privacy alignment ceiling).
  ``dp_avg``      : θ₀ warmed on per-class client averages released under the
                    averaging-variant Gaussian mechanism (the private path).
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple


# Notebook globals (Section 0.2)
DP_DELTA = 1e-5
CLIP_PERCENTILE = 95


# ----------------------------------------------------------------------------
# Feature-norm clip estimate (notebook Section 0.3)
# ----------------------------------------------------------------------------
def compute_feature_norms_percentile(X, p: float = CLIP_PERCENTILE,
                                     max_samples: int = 5000) -> float:
    """Robust L2-norm clip = p-th percentile of feature norms on a public sample.

    Computed on the (public) training pool, matching the notebook. Used as the
    DP clip bound for the averaging mechanism.
    """
    import numpy as np

    n = min(X.shape[0], max_samples)
    idx = np.random.default_rng(0).choice(X.shape[0], n, replace=False)
    return float(np.percentile(X[idx].norm(dim=1).numpy(), p))


# ----------------------------------------------------------------------------
# Probe builders (verbatim port, notebook Section 0.4)
# ----------------------------------------------------------------------------
def build_probe_raw_union(
    client_X_list: List,
    client_y_list: List,
    K_per_class: int,
    num_classes: int,
    seed: int = 0,
) -> Tuple:
    """Union of clipped raw samples, K per client per class. No DP.

    Returns (probe_X, probe_y, info). ``info`` carries ``probe_size`` and
    ``sigma`` (0.0 here). A client contributes nothing for a class it lacks.
    """
    import numpy as np
    import torch

    rng = np.random.default_rng(seed)
    probe_X_list, probe_y_list = [], []
    for i in range(len(client_X_list)):
        X_i = client_X_list[i].cpu()
        y_i = client_y_list[i].cpu().numpy()
        for c in range(num_classes):
            mask = (y_i == c)
            n_avail = int(mask.sum())
            if n_avail == 0:
                continue
            X_c = X_i[mask]
            n_take = min(K_per_class, n_avail)
            idx = rng.choice(n_avail, n_take, replace=False)
            samples = X_c[idx]
            probe_X_list.append(samples)
            probe_y_list.append(torch.full((n_take,), c, dtype=torch.long))
    probe_X = torch.cat(probe_X_list, dim=0)
    probe_y = torch.cat(probe_y_list, dim=0)
    return probe_X, probe_y, {"probe_size": int(probe_X.shape[0]), "sigma": 0.0}


def dp_sigma(clip: float, K_per_class: int, eps_per_client: float,
             delta: float = DP_DELTA) -> float:
    """Gaussian-mechanism σ for the averaging-variant DP probe.

    The released contribution per (client, class) is the *mean* of ``K_per_class``
    samples, each L2-clipped to ``clip``. Under replace-one neighbouring datasets
    the L2-sensitivity of that mean is ``clip / K_per_class`` (one record changes
    the average by at most clip/K). With parallel composition over classes the
    per-class mechanism is calibrated independently:

        sigma = (clip / K_per_class) * sqrt(2 * ln(1.25 / delta)) / eps

    ``eps == inf`` -> σ = 0 (no noise). Exposed separately from
    ``build_probe_dp_averaged`` so the DP-accounting unit test (issue 003) can
    assert the formula through a public interface.
    """
    import numpy as np

    if eps_per_client == float("inf"):
        return 0.0
    sensitivity = clip / K_per_class
    return float(sensitivity * np.sqrt(2.0 * np.log(1.25 / delta)) / eps_per_client)


def build_probe_dp_averaged(
    client_X_list: List,
    client_y_list: List,
    K_per_class: int,
    num_classes: int,
    clip: float,
    eps_per_client: float,
    delta: float = DP_DELTA,
    seed: int = 0,
) -> Tuple:
    """Averaging-variant DP probe (verbatim port, notebook Section 0.4).

    Per (client, class): L2-clip ``K_per_class`` samples to ``clip``, average to
    one contribution, add Gaussian noise with σ = ``dp_sigma(...)``. Server then
    averages the per-class contributions across clients. Returns
    (probe_X[num_classes_with_contributors, feature_dim], probe_y, info).
    """
    import numpy as np
    import torch

    rng = np.random.default_rng(seed)
    sigma = dp_sigma(clip, K_per_class, eps_per_client, delta)

    feature_dim = client_X_list[0].shape[1]
    accum = torch.zeros(num_classes, feature_dim)
    count = torch.zeros(num_classes)

    for i in range(len(client_X_list)):
        X_i = client_X_list[i].cpu()
        y_i = client_y_list[i].cpu().numpy()
        for c in range(num_classes):
            mask = (y_i == c)
            n_avail = int(mask.sum())
            if n_avail == 0:
                continue
            X_c = X_i[mask]
            n_take = min(K_per_class, n_avail)
            idx = rng.choice(n_avail, n_take, replace=False)
            samples = X_c[idx].clone()
            norms = samples.norm(dim=1, keepdim=True)
            scale = torch.minimum(torch.ones_like(norms),
                                  clip / norms.clamp_min(1e-6))
            samples = samples * scale
            contribution = samples.mean(dim=0)
            if sigma > 0:
                noise = torch.from_numpy(
                    rng.normal(0, sigma, contribution.shape).astype(np.float32))
                contribution = contribution + noise
            accum[c] += contribution
            count[c] += 1

    valid = count > 0
    probe_X = accum[valid] / count[valid].unsqueeze(1)
    probe_y = torch.arange(num_classes)[valid]
    return probe_X, probe_y, {"probe_size": int(valid.sum()), "sigma": float(sigma)}


# ----------------------------------------------------------------------------
# Deep-module entry points used by protocol.run_cell
# ----------------------------------------------------------------------------
def build_probe(
    strategy: str,
    *,
    client_X_list: List,
    client_y_list: List,
    num_classes: int,
    K_per_class: Optional[int] = None,
    eps: Optional[float] = None,
    clip: Optional[float] = None,
    delta: float = DP_DELTA,
    seed: int = 0,
    labelled_probe: Optional[Tuple] = None,
) -> Tuple:
    """Return (probe_X, probe_y, info) for a chosen alignment strategy.

    ``labelled`` simply echoes a pre-reserved labelled probe (passed in via
    ``labelled_probe=(X, y, P)``) — the public-data baseline. ``raw_union`` and
    ``dp_avg`` build a client-derived probe. ``none``/``warmup_only`` build no
    probe and are handled by the caller. This is the single dispatch point the
    PRD names; θ₀ is then produced by ``warmup_init`` on the returned probe.
    """
    if strategy == "labelled":
        if labelled_probe is None:
            raise ValueError("strategy 'labelled' requires labelled_probe=(X, y, P)")
        pX, pY, P = labelled_probe
        return pX, pY, {"probe_size": int(P), "sigma": 0.0}
    if strategy == "raw_union":
        return build_probe_raw_union(
            client_X_list, client_y_list, K_per_class, num_classes, seed=seed)
    if strategy == "dp_avg":
        if clip is None:
            raise ValueError("strategy 'dp_avg' requires a clip bound")
        return build_probe_dp_averaged(
            client_X_list, client_y_list, K_per_class, num_classes,
            clip=clip, eps_per_client=eps, delta=delta, seed=seed)
    raise ValueError(f"build_probe: no probe for strategy {strategy!r}")


def warmup_init(
    make_model_fn,
    probe_X,
    probe_y,
    base_init: Dict,
    *,
    epochs: int,
    lr: float,
    momentum: float,
    bs: int,
    seed: int = 12345,
    lr_schedule: Optional[str] = None,
) -> Dict:
    """Produce θ₀ by warming ``base_init`` on the probe via supervised SGD.

    Returns the warmed parameter dict (the shared, aligned init every client
    distils from). Fixed warmup seed 12345 matches the notebook. Imported here
    rather than at module top to avoid a torch dependency for static checks.

    ``lr_schedule`` is opt-in (forwarded to ``train_supervised_model``);
    ``None`` keeps the legacy constant-LR warmup byte-identical for every
    backbone that does not set ``BackboneSpec.teacher_lr_schedule``.
    """
    from .teacher import train_supervised_model
    from .backbones import get_params

    warmed = train_supervised_model(
        make_model_fn, probe_X, probe_y,
        epochs=epochs, lr=lr, momentum=momentum, bs=bs,
        seed=seed, init_params=base_init, lr_schedule=lr_schedule,
    )
    return get_params(warmed)
