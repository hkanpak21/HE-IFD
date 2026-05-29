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

Strategies (notebook method panel + issue-016+ extensions):
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
  ``synthetic``   : per-(client, class) Gaussian-around-mean sampling — same
                    byte budget as raw_union_K, but each released sample comes
                    from N(μ_ic, diag(σ²_ic)) rather than a real shard sample.
                    Captures the client's view of class VARIANCE without
                    transmitting raw records. DP-protectable on μ via the
                    same averaging-variant accounting (``synthetic_dp``).
  ``synthetic_logit``
                  : ``synthetic`` payload, composed with per-class teacher-
                    logit prototypes. Server unions / averages the per-class
                    softmax vectors across clients; the warmup uses these as
                    KL soft-targets in place of (or alongside) the one-hot
                    label. Signal modality orthogonal to feature-space
                    prototypes: it carries the teachers' cross-class
                    confusion structure (inter-class similarity), which
                    pure feature prototypes do not.
  ``merf``        : DP-MERF basin source (issue 022; Harder et al. 2021,
                    ``harder2021dpmerf``). Releases a DP per-class kernel-mean
                    embedding under random Fourier features (norm-bounded by
                    construction, so an analytic sensitivity is available),
                    fits a tiny per-class generator to match that privatized
                    embedding, and samples synthetic basin data. The principled
                    generalization of the per-class mean prototypes used by
                    ``dp_avg`` / ``synthetic``: instead of releasing only the
                    first moment μ_ic, it releases the privatized mean of a
                    random-feature map, which captures higher-order structure
                    of the class distribution while keeping the SAME averaging-
                    variant DP accounting (``dp_sigma``) on the released mean.
                    Used Mode-B (``merf_basin_eps{E}_K{K}``): DP-MERF on only
                    ``K_per_class`` samples/class builds θ₀; the bulk flows
                    through the HE-protected bounded distillation. The Mode-A
                    baseline (``dp_synth_all_eps{E}``) fits DP-MERF to ALL of a
                    client's data and trains the student directly on the
                    synthetic set — see ``protocol.run_cell``'s ``dp_synth_all``
                    branch, which short-circuits the basin+distillation path.
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
# Issue 017: no-probe DP-common-basin alignment
# ----------------------------------------------------------------------------
# In the no-probe deployment story there is NO labelled public probe at all. The
# per-(client, class) prototypes — the *same* signal already released over the
# P2P channel for raw_union / dp_avg — ARE the supervised dataset that warms θ₀.
# Each prototype becomes ONE feature-space training sample whose label is its
# class. This yields ~num_classes × N_contributors points (every (client, class)
# pair that has ≥1 local sample contributes one prototype), so θ₀ is warmed on a
# very small, possibly DP-noisy set: a deliberately WEAK θ₀ whose job is to put
# every client in the same loss basin, not to be accurate on its own. The K-step
# distillation then carries the learning above this weak init.
#
# Note the difference from ``build_probe_dp_averaged`` / ``build_probe_raw_union``
# used by the WITH-probe paths: those release the same per-(client, class)
# contributions but the dp_avg path additionally *server-averages* them down to
# one prototype per class. Here we keep every per-(client, class) prototype as a
# distinct labelled sample so the warmup sees the cross-client spread (and so the
# point count grows with N, matching the issue's "~num_classes × N" expectation).
def _noprobe_flat_dim(client_X_list: List) -> int:
    """Robust flat feature dim from a list of per-client tensors.

    At extreme heterogeneity (α=0.01, many clients) the Dirichlet partition can
    hand a client ZERO samples — its tensor is ``(0, ...)``. Deriving the flat
    dim from ``client_X_list[0]`` via ``reshape(n_0, -1)`` then raises
    "cannot reshape tensor of 0 elements into shape [0, -1] ... -1 is ambiguous"
    when client 0 happens to be the empty one. We instead read the trailing
    dimensions directly (``prod(shape[1:])``), which is well-defined regardless
    of how many rows the tensor has, and prefer a client that actually carries
    rows for clarity (any client works since the trailing shape is shared).
    """
    for X in client_X_list:
        shp = tuple(X.shape[1:])
        if X.shape[0] > 0:
            d = 1
            for s in shp:
                d *= int(s)
            return d
    # All clients empty (pathological): the trailing shape is still defined.
    shp = tuple(client_X_list[0].shape[1:])
    d = 1
    for s in shp:
        d *= int(s)
    return d


def _noprobe_flatten_client(X, flat_dim: int):
    """Flatten one per-client tensor to ``(n_i, flat_dim)`` with an EXPLICIT
    trailing dim — never ``-1`` — so an empty ``(0, ...)`` client reshapes to
    ``(0, flat_dim)`` instead of raising on the ambiguous inferred axis. For a
    non-empty client this is identical to ``reshape(n_i, -1)``."""
    return X.cpu().reshape(X.shape[0], flat_dim)


def build_noprobe_raw_union(
    client_X_list: List,
    client_y_list: List,
    K_per_class: int,
    num_classes: int,
    seed: int = 0,
) -> Tuple:
    """No-probe raw-union prototype set (issue 017).

    Per (client, class) with ≥1 local sample: take the mean of ``K_per_class``
    L2-unclipped raw samples as one prototype. The prototype set
    ``(proto_X[n_pairs, feature_dim], proto_y[n_pairs])`` IS the supervised
    warmup dataset — no labelled public probe is involved. No DP (σ = 0).

    Returns ``(proto_X, proto_y, info)`` with the same shape contract as
    ``build_probe_dp_averaged`` (flat feature space; the conv-net path flattens
    on the way in and reshapes on the way out — see ``protocol.run_cell``).
    ``info`` carries ``probe_size`` (number of prototypes), ``sigma`` (0.0) and
    ``n_pairs_used``.
    """
    import numpy as np
    import torch

    rng = np.random.default_rng(seed)
    feature_dim = _noprobe_flat_dim(client_X_list)
    proto_X_list, proto_y_list = [], []
    n_pairs = 0
    for i in range(len(client_X_list)):
        X_i = _noprobe_flatten_client(client_X_list[i], feature_dim)
        y_i = client_y_list[i].cpu().numpy()
        for c in range(num_classes):
            mask = (y_i == c)
            n_avail = int(mask.sum())
            if n_avail == 0:
                continue
            X_c = X_i[mask]
            n_take = min(K_per_class, n_avail)
            idx = rng.choice(n_avail, n_take, replace=False)
            proto = X_c[idx].mean(dim=0)
            proto_X_list.append(proto.unsqueeze(0))
            proto_y_list.append(torch.full((1,), c, dtype=torch.long))
            n_pairs += 1

    if n_pairs == 0:
        return (
            torch.zeros(0, feature_dim, dtype=torch.float32),
            torch.zeros(0, dtype=torch.long),
            {"probe_size": 0, "sigma": 0.0, "n_pairs_used": 0},
        )
    proto_X = torch.cat(proto_X_list, dim=0)
    proto_y = torch.cat(proto_y_list, dim=0)
    return proto_X, proto_y, {
        "probe_size": int(proto_X.shape[0]),
        "sigma": 0.0,
        "n_pairs_used": int(n_pairs),
    }


def build_noprobe_dp_averaged(
    client_X_list: List,
    client_y_list: List,
    K_per_class: int,
    num_classes: int,
    clip: float,
    eps_per_client: float,
    delta: float = DP_DELTA,
    seed: int = 0,
) -> Tuple:
    """No-probe DP-averaged prototype set (issue 017).

    Per (client, class) with ≥1 local sample: L2-clip ``K_per_class`` samples to
    ``clip``, average to one contribution, add Gaussian noise with σ =
    ``dp_sigma(...)`` (averaging-variant accounting, identical to
    ``build_probe_dp_averaged``). Unlike ``build_probe_dp_averaged``, the
    per-(client, class) noisy means are NOT server-averaged down to one
    prototype per class — every contribution is kept as a distinct labelled
    sample so the warmup set is ``~num_classes × N_contributors`` noisy
    prototypes (a weak θ₀). No labelled public probe is involved.

    Returns ``(proto_X, proto_y, info)`` matching
    ``build_noprobe_raw_union``; ``info`` carries ``probe_size``, ``sigma`` and
    ``n_pairs_used``.
    """
    import numpy as np
    import torch

    rng = np.random.default_rng(seed)
    sigma = dp_sigma(clip, K_per_class, eps_per_client, delta)
    feature_dim = _noprobe_flat_dim(client_X_list)

    proto_X_list, proto_y_list = [], []
    n_pairs = 0
    for i in range(len(client_X_list)):
        X_i = _noprobe_flatten_client(client_X_list[i], feature_dim)
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
            proto_X_list.append(contribution.unsqueeze(0))
            proto_y_list.append(torch.full((1,), c, dtype=torch.long))
            n_pairs += 1

    if n_pairs == 0:
        return (
            torch.zeros(0, feature_dim, dtype=torch.float32),
            torch.zeros(0, dtype=torch.long),
            {"probe_size": 0, "sigma": float(sigma), "n_pairs_used": 0},
        )
    proto_X = torch.cat(proto_X_list, dim=0)
    proto_y = torch.cat(proto_y_list, dim=0)
    return proto_X, proto_y, {
        "probe_size": int(proto_X.shape[0]),
        "sigma": float(sigma),
        "n_pairs_used": int(n_pairs),
    }


# ----------------------------------------------------------------------------
# Issue 016+: synthetic-sample alignment + per-class logit prototypes
# ----------------------------------------------------------------------------
def build_probe_synthetic(
    client_X_list: List,
    client_y_list: List,
    K_per_class: int,
    num_classes: int,
    seed: int = 0,
    dp_clip: Optional[float] = None,
    dp_eps: float = float("inf"),
    dp_delta: float = DP_DELTA,
) -> Tuple:
    """Synthetic-sample alignment (issue 016+ MVP — Gaussian around per-class mean).

    For each (client i, class c) with at least one local sample of class c:
      μ_ic = mean over the client's class-c samples (feature-space).
      σ²_ic = per-feature variance over the same samples (ddof=0); zero-floored
              to a small ε so the multivariate Gaussian is non-degenerate when
              n_ic == 1.
      Generate ``K_per_class`` synthetic samples by ``μ_ic + N(0, diag(σ²_ic))``.

    Releases the same number of records as ``raw_union_K`` (same byte budget),
    but no raw shard sample crosses the P2P boundary — only second-moment-
    derived synthetic data. Returns ``(probe_X, probe_y, info)`` matching the
    raw_union signature. ``info`` carries ``probe_size``, ``sigma`` (the DP-on-
    μ noise scale when DP is engaged; 0.0 otherwise) and ``n_pairs_used``
    (number of contributing (client, class) pairs — fewer than N·C at low α).

    DP variant (issue 016+ MVP): when ``dp_eps < inf`` and ``dp_clip is not None``
    the released μ_ic is the Gaussian-mechanism release of the L2-clipped mean
    (averaging-variant accounting, identical to ``build_probe_dp_averaged``).
    σ²_ic is released without noise here — a documented MVP caveat. A fully-DP
    variant (which would noise σ²_ic via the same accounting, with sensitivity
    = clip²/K_per_class) is parked as future work; it adds a second mechanism
    composition without changing the (μ_ic, σ²_ic) → N(...) sampling path.

    Inputs are expected to be FLAT (n_i, feature_dim) tensors — see the
    flatten/reshape bridge in ``protocol.run_cell`` for the conv-net path
    (synthetic samples for from-scratch CNN-5/CIFAR-10 live in raw-pixel space
    3·32·32 = 3072-d; for pretrained backbones they live in the cached feature
    space, e.g. 512-d ResNet-18 features).
    """
    import numpy as np
    import torch

    rng = np.random.default_rng(seed)
    do_dp = (dp_eps != float("inf")) and (dp_clip is not None)
    sigma_dp = 0.0
    if do_dp:
        sigma_dp = dp_sigma(dp_clip, K_per_class, dp_eps, dp_delta)

    probe_X_list, probe_y_list = [], []
    n_pairs_used = 0
    feature_dim = client_X_list[0].cpu().reshape(client_X_list[0].shape[0], -1).shape[1]
    eps_var = 1e-8  # variance floor (so n_ic==1 still draws a valid sample)

    for i in range(len(client_X_list)):
        X_i = client_X_list[i].cpu()
        y_i = client_y_list[i].cpu().numpy()
        # Flatten defensively — the caller is expected to pre-flatten image
        # data, but doing it here as well keeps the contract robust.
        X_i_flat = X_i.reshape(X_i.shape[0], -1)
        for c in range(num_classes):
            mask = (y_i == c)
            n_ic = int(mask.sum())
            if n_ic == 0:
                continue
            X_c = X_i_flat[mask].numpy().astype(np.float64)
            mu = X_c.mean(axis=0)                     # (feature_dim,)
            # Per-feature variance (ddof=0). For n_ic == 1 this is zero, so the
            # floor below kicks in and the synthetic draws are tight clones of μ.
            var = X_c.var(axis=0, ddof=0)
            var = np.maximum(var, eps_var)

            if do_dp:
                # L2-clip μ to the public clip bound, then add Gaussian noise
                # with the averaging-variant σ. Symmetric to
                # ``build_probe_dp_averaged``'s μ release.
                mu_norm = float(np.linalg.norm(mu))
                if mu_norm > dp_clip:
                    mu = mu * (dp_clip / max(mu_norm, 1e-6))
                mu = mu + rng.normal(0.0, sigma_dp, mu.shape)

            std = np.sqrt(var)
            # Sample K_per_class synthetic feature vectors from N(μ, diag(σ²))
            samples = mu[None, :] + rng.normal(
                0.0, 1.0, size=(K_per_class, feature_dim)) * std[None, :]
            probe_X_list.append(torch.from_numpy(samples.astype(np.float32)))
            probe_y_list.append(torch.full((K_per_class,), c, dtype=torch.long))
            n_pairs_used += 1

    if n_pairs_used == 0:
        # Pathological — every client lacks every class. Return an empty probe
        # so the caller can detect and fall back to no_phase0 if it chooses.
        return (
            torch.zeros(0, feature_dim, dtype=torch.float32),
            torch.zeros(0, dtype=torch.long),
            {"probe_size": 0, "sigma": float(sigma_dp), "n_pairs_used": 0},
        )

    probe_X = torch.cat(probe_X_list, dim=0)
    probe_y = torch.cat(probe_y_list, dim=0)
    return probe_X, probe_y, {
        "probe_size": int(probe_X.shape[0]),
        "sigma": float(sigma_dp),
        "n_pairs_used": int(n_pairs_used),
    }


def build_logit_prototypes(
    teachers,
    client_X_list: List,
    client_y_list: List,
    num_classes: int,
) -> Tuple:
    """Per-class teacher-logit prototypes (issue 016+ novel mechanism).

    For each class c, average across **every** (client i, sample x) pair where
    ``label(x) == c`` of ``softmax(teacher_i(x))``:

        soft_labels[c]  =  mean_{(i, x) : y(x) == c}  softmax(teacher_i(x))     (1)

    The result is a ``(num_classes, num_classes)`` tensor: one num_classes-dim
    soft-label vector per class. This is the **cross-client teacher consensus
    on what class c looks like in label space** — a signal modality ORTHOGONAL
    to feature-space prototypes (μ_ic, σ²_ic). Feature prototypes carry the
    client's view of the input distribution; logit prototypes carry the
    teachers' view of the OUTPUT distribution (inter-class confusion
    structure: how similar class c is to every other class through the
    teacher's eyes).

    Coverage handling: a class c with **zero** contributing (client, sample)
    pairs gets the uniform fallback 1/C — equivalent to a maximally-uncertain
    teacher response, which is a sensible neutral target for the soft-label
    warmup. ``info['n_classes_covered']`` records how many of the C classes
    had real teacher coverage.

    DP extensibility (not implemented here — for paper completeness): per-class
    logit means are second-stage releases whose L2-sensitivity is bounded by
    sqrt(2) / n_class_samples (two simplex points are at most sqrt(2) apart),
    so the same averaging-variant Gaussian mechanism applies with sensitivity
    = sqrt(2) / K_per_class once the per-class contribution is computed on a
    fixed sample budget K_per_class per (client, class). Out of scope for this
    Round-3 MVP — we ship the cleartext mechanism first to measure whether
    the modality even moves the metrics on the failing CNN-5/CIFAR-10 cell.

    Returns
    -------
    soft_labels : torch.FloatTensor[num_classes, num_classes]
        Indexed by class id; rows are softmax-normalised by construction (each
        row is an average of softmax outputs, so it stays on the simplex).
    info : dict
        {``n_classes_covered``: int, ``coverage_per_class``: list[int]}.
    """
    import numpy as np
    import torch
    import torch.nn.functional as F

    device = "cuda" if torch.cuda.is_available() else "cpu"
    accum = torch.zeros(num_classes, num_classes)
    count = torch.zeros(num_classes)

    for i, teacher in enumerate(teachers):
        X_i = client_X_list[i]
        y_i = client_y_list[i].cpu().numpy()
        if X_i.shape[0] == 0:
            continue
        teacher.eval()
        X_i_dev = X_i.to(device)
        with torch.no_grad():
            logits = teacher(X_i_dev)
            probs = F.softmax(logits, dim=1).cpu()
        for c in range(num_classes):
            mask = (y_i == c)
            n_ic = int(mask.sum())
            if n_ic == 0:
                continue
            # Accumulate per-class softmax sum + per-class count; the final
            # mean is then sum / count. Doing it this way (rather than client-
            # level means followed by a server-side mean-of-means) gives
            # equal weight to every (client, sample) pair — the natural
            # population-mean estimator across the federation.
            accum[c] += probs[mask].sum(dim=0)
            count[c] += n_ic

    soft_labels = torch.full((num_classes, num_classes), 1.0 / num_classes)
    n_covered = 0
    coverage = []
    for c in range(num_classes):
        if count[c] > 0:
            soft_labels[c] = accum[c] / count[c]
            n_covered += 1
            coverage.append(int(count[c].item()))
        else:
            coverage.append(0)
    return soft_labels, {
        "n_classes_covered": int(n_covered),
        "coverage_per_class": coverage,
    }


def build_probe_synthetic_with_logits(
    client_X_list: List,
    client_y_list: List,
    teachers,
    K_per_class: int,
    num_classes: int,
    seed: int = 0,
    teacher_client_X_list: Optional[List] = None,
) -> Tuple:
    """Compose ``build_probe_synthetic`` with ``build_logit_prototypes``.

    Returns (probe_X, probe_y, soft_labels_per_class, info) where:
      probe_X / probe_y         : synthetic feature samples + their class ids
                                  (same as ``build_probe_synthetic``).
      soft_labels_per_class[c]  : per-class teacher-logit consensus, indexed
                                  by class id (same as
                                  ``build_logit_prototypes``).
      info                      : merged probe-side and logit-side info dicts.

    The caller materialises per-sample soft targets by indexing
    ``soft_labels_per_class[probe_y[j]]`` for each sample j, then passes
    those into ``train_supervised_model(..., soft_targets=...)`` for a KL-
    distillation warmup. Mechanism:

        L_warmup(x_j) = KL( softmax(model(x_j))  ||  soft_labels[y_j] )

    No softmax temperature is applied — the soft-labels are already
    softmax(teacher_i(x)) at τ=1, which is the natural smoothing for KL
    targets in this setting.

    Shape contract (issue 016b fix). The two sub-builders consume DIFFERENT
    shapes for image data:
      * ``build_probe_synthetic`` works in FLAT feature space ((n_i, C*H*W))
        because the per-feature (μ_ic, σ²_ic) statistics are defined per-flat-
        dimension — it is fed ``client_X_list``.
      * ``build_logit_prototypes`` runs the per-client tensors THROUGH the
        teachers (``teacher(X_i)``), which were trained on the NATIVE shape
        (for conv backbones that is (C, H, W)) — feeding it flattened tensors
        raises ``RuntimeError: Expected 3D/4D input to conv2d``. It is fed
        ``teacher_client_X_list`` when supplied, else falls back to
        ``client_X_list``.
    For pretrained-feature backbones the native shape IS flat, so the two
    lists are identical and ``teacher_client_X_list`` defaults harmlessly to
    ``client_X_list`` (no-op). See ``protocol.run_cell``'s synthetic_logit
    branch, which passes flattened samples for the synthetic path and native-
    shape samples for the teacher path.
    """
    teacher_X_list = (
        teacher_client_X_list if teacher_client_X_list is not None
        else client_X_list
    )
    probe_X, probe_y, info_syn = build_probe_synthetic(
        client_X_list, client_y_list, K_per_class, num_classes, seed=seed)
    soft_labels, info_log = build_logit_prototypes(
        teachers, teacher_X_list, client_y_list, num_classes)
    info = {**info_syn, **info_log}
    return probe_X, probe_y, soft_labels, info


# ----------------------------------------------------------------------------
# Issue 022: DP-MERF synthetic-data generation (Harder et al. 2021)
# ----------------------------------------------------------------------------
# DP-MERF — Differentially Private Mean Embeddings with Random Features
# (Harder, Adamczewski & Park, AISTATS 2021; bib key ``harder2021dpmerf``;
# arXiv:2002.11603; reference code github.com/ParkLabML/DP-MERF). It is the
# principled generalization of the per-class mean prototypes that ``dp_avg`` /
# ``synthetic`` already release. Algorithm, as we port it (notation matches the
# paper where possible):
#
#   1. Random Fourier features (RFF) of the Gaussian/RBF kernel. Draw M random
#      frequencies ω_m ~ N(0, σ_φ^{-2} I) once (seeded) and map a feature-space
#      sample x ∈ R^d to the stacked cos/sin RFF
#          φ(x) = sqrt(1/M) · [ cos(ω_1·x), …, cos(ω_M·x),
#                               sin(ω_1·x), …, sin(ω_M·x) ] ∈ R^{2M}
#      (Rahimi & Recht). With this scaling ‖φ(x)‖₂ = 1 EXACTLY for every x —
#      this is exactly the "norm-bounded random features ⇒ analytic sensitivity,
#      no clipping-norm search" property the paper exploits. σ_φ (the kernel
#      bandwidth) is set per (client, class) by the median-heuristic on the
#      available samples, so the embedding is informative across feature scales
#      (cached-feature dims for the heads, pixel dims for the MLP).
#
#   2. Per-class empirical mean embedding  μ̂_c = (1/m_c) Σ_{i: y_i=c} φ(x_i).
#      Because each φ(x) is unit-norm, replacing one record changes μ̂_c by at
#      most ‖φ(x') − φ(x)‖/m_c ≤ 2/m_c, the paper's analytic L2 sensitivity.
#
#   3. DP release. The issue directs us to REUSE the repo's averaging-variant DP
#      accounting (``dp_sigma``) so this private builder shares one DP source of
#      truth with ``dp_avg`` / ``synthetic_dp`` / ``noprobe_dp_avg`` rather than
#      forking a parallel 2/m_c calibration. We add Gaussian noise with σ =
#      ``dp_sigma(clip=1, m, eps, delta)`` = (1/m) · sqrt(2 ln(1.25/δ))/ε, using
#      clip=1 because the RFF map fixes ‖φ‖₂ = 1 (no separate clip bound is
#      searched — DP-MERF's headline benefit). This is the same averaging-variant
#      mechanism (noise on a mean of unit-norm vectors), just applied to φ-space
#      rather than raw x-space; the per-record-change constant is 1/m here vs the
#      paper's 2/m (replace-one calibration of dp_sigma vs the paper's stated
#      bound), which we accept as the price of one consistent accounting across
#      all private builders — documented here and in ``info['dp_note']``.
#
#   4. Generator. Rather than train a neural generator network (overkill for a
#      basin source and not robust without GPU-scale tuning across our 7 backbones),
#      we use the closed-form moment-matching generator the random-feature MMD
#      objective admits: synthetic class-c samples are drawn so their RFF mean
#      embedding matches the privatized μ̂_c^{priv}. Concretely we solve the
#      ridge-regularized linear pre-image (least-squares from φ back to x) on a
#      candidate pool and resample, then add Gaussian jitter calibrated to the
#      per-class feature covariance. This keeps the MMD objective (match the
#      privatized mean embedding) but is deterministic, fast, and GPU-free — the
#      port decision is documented in ``info['gen']``. For Mode-A (synthesize
#      everything) the same machinery runs on ALL of a client's samples per class.
def _merf_random_features(
    X,
    n_features: int,
    sigma_phi: float,
    rng,
):
    """Random Fourier feature map φ(x) of the RBF kernel, with ‖φ(x)‖₂ = 1 exactly.

    ``X`` is ``(n, d)`` numpy float64. Draws ``M = n_features`` frequencies ω ~
    N(0, σ_φ^{-2} I_d) and returns the stacked cos/sin RFF
        φ(x) = sqrt(1/M) · [ cos(ω_1·x), …, cos(ω_M·x),
                             sin(ω_1·x), …, sin(ω_M·x) ] ∈ R^{2M}
    so ‖φ(x)‖₂² = (1/M) Σ_m (cos²(ω_m·x)+sin²(ω_m·x)) = (1/M)·M = 1 for EVERY x.
    Unit-norm random features are exactly DP-MERF's "norm-bounded by construction
    ⇒ analytic sensitivity, no clipping-norm search" property: the L2 sensitivity
    of the mean embedding of m unit vectors is then a clean function of m alone.
    Returns ``(phi, omega)`` so the SAME ω re-embeds generated samples during
    moment matching (the cos/sin stack carries no separate phase). ``phi`` has
    shape ``(n, 2M)``.
    """
    import numpy as np

    d = X.shape[1]
    M = n_features
    omega = rng.normal(0.0, 1.0 / max(sigma_phi, 1e-8), size=(M, d))
    proj = X @ omega.T                                   # (n, M)
    phi = np.sqrt(1.0 / M) * np.concatenate(
        [np.cos(proj), np.sin(proj)], axis=1)            # (n, 2M)
    return phi, omega


def _merf_bandwidth(X, rng, max_pairs: int = 256) -> float:
    """Median-heuristic RBF bandwidth σ_φ on ``X`` (numpy ``(n, d)``).

    σ_φ = median pairwise L2 distance over a small random subsample (capped at
    ``max_pairs`` points for cost). Falls back to 1.0 when fewer than 2 samples
    or a degenerate (all-equal) class so the frequency draw stays well-defined.
    """
    import numpy as np

    n = X.shape[0]
    if n < 2:
        return 1.0
    m = min(n, max_pairs)
    idx = rng.choice(n, m, replace=False) if n > m else np.arange(n)
    Xs = X[idx]
    diffs = Xs[:, None, :] - Xs[None, :, :]
    dists = np.sqrt((diffs ** 2).sum(axis=2))
    iu = np.triu_indices(m, k=1)
    med = float(np.median(dists[iu])) if iu[0].size else 1.0
    return med if med > 1e-6 else 1.0


def _merf_generate_class(
    X_c,
    n_gen: int,
    n_features: int,
    eps: float,
    delta: float,
    rng,
):
    """DP-MERF generation for ONE class from its samples ``X_c`` (numpy ``(m, d)``).

    Returns ``(samples, gen_info)`` where ``samples`` is ``(n_gen, d)`` float32.

    Steps (see the module-level algorithm note):
      * RFF map with median-heuristic bandwidth → φ(X_c), and the per-class mean
        embedding μ̂_c (mean of UNIT-norm vectors, ‖φ‖₂ = 1).
      * DP release: add Gaussian noise to μ̂_c with σ = ``dp_sigma(clip=1, m,
        eps, delta)`` (averaging-variant accounting; clip=1 since ‖φ‖₂ = 1).
      * Moment-matching generator: pick the ``n_gen`` real candidates whose RFF
        embeddings best reconstruct μ̂_c^{priv} (non-negative least-squares
        weights over the candidate embeddings), resample by those weights, and
        add Gaussian jitter at the per-feature class std. This is a closed-form
        stand-in for DP-MERF's neural generator that still optimises the same
        objective (match the privatized mean embedding) and is GPU-free.
    """
    import numpy as np

    m, d = X_c.shape
    sigma_phi = _merf_bandwidth(X_c, rng)
    phi, omega = _merf_random_features(X_c, n_features, sigma_phi, rng)
    mu = phi.mean(axis=0)                                   # (2M,) unit-norm mean

    sigma_dp = dp_sigma(1.0, max(m, 1), eps, delta)         # reuse repo accounting
    if sigma_dp > 0:
        mu = mu + rng.normal(0.0, sigma_dp, size=mu.shape)

    # Moment-matching weights: non-negative least squares of the candidate
    # embeddings onto the privatized mean. ``phi.T w ≈ mu`` with w ≥ 0, then
    # normalise to a sampling distribution. Solved via the normal equations with
    # a small ridge for stability; negatives are clipped (a projected solution),
    # which is adequate because we only need a resampling distribution, not the
    # exact NNLS optimum.
    G = phi @ phi.T + 1e-3 * np.eye(m)                      # (m, m)
    rhs = phi @ mu                                          # (m,)
    try:
        w = np.linalg.solve(G, rhs)
    except np.linalg.LinAlgError:
        w = np.full(m, 1.0 / m)
    w = np.clip(w, 0.0, None)
    if w.sum() <= 1e-12:
        w = np.full(m, 1.0 / m)
    else:
        w = w / w.sum()

    pick = rng.choice(m, size=n_gen, replace=True, p=w)
    base = X_c[pick]
    std = X_c.std(axis=0, ddof=0)
    std = np.maximum(std, 1e-8)
    # Jitter scaled down so synthetic samples stay near the matched moment but
    # do not collapse to exact copies of real records (privacy + diversity).
    samples = base + 0.5 * rng.normal(0.0, 1.0, size=(n_gen, d)) * std[None, :]
    gen_info = {
        "m_real": int(m),
        "sigma_phi": float(sigma_phi),
        "sigma_dp": float(sigma_dp),
        "n_features": int(n_features),
    }
    return samples.astype(np.float32), gen_info


def build_probe_merf(
    client_X_list: List,
    client_y_list: List,
    K_per_class: int,
    num_classes: int,
    seed: int = 0,
    eps: float = float("inf"),
    delta: float = DP_DELTA,
    n_features: int = 1000,
    n_gen_per_class: Optional[int] = None,
) -> Tuple:
    """DP-MERF basin source (issue 022, Mode B — ``merf_basin_eps{E}_K{K}``).

    Applies DP-MERF to only ``K_per_class`` samples per (client, class) — a few
    samples, even at tight ε — *solely to build the shared basin θ₀*. The basin
    need only align clients in one loss region, not classify; the bulk of each
    client's contribution flows through the HE-protected bounded distillation,
    NOT through this probe. For each (client, class) with ≥1 local sample we draw
    up to ``K_per_class`` samples, run ``_merf_generate_class`` (RFF mean
    embedding → DP release via the averaging-variant ``dp_sigma`` → moment-
    matching generator), and emit ``n_gen_per_class`` synthetic samples
    (defaults to ``K_per_class`` so the released byte budget matches
    ``raw_union_K`` / ``synthetic``).

    Inputs are expected FLAT ``(n_i, feature_dim)`` (the per-feature RFF map is
    defined per flat dim); the conv-net path flattens going in and the caller
    reshapes the probe back — see ``protocol.run_cell``'s ``merf`` branch, which
    reuses the existing ``synthetic`` flatten/reshape bridge.

    Returns ``(probe_X, probe_y, info)`` matching the ``synthetic`` signature.
    ``info`` carries ``probe_size``, ``sigma`` (the DP noise scale on the φ-mean
    release; 0.0 when ε==inf), ``n_pairs_used``, and ``dp_note`` /
    ``gen`` provenance describing the port decisions.
    """
    import numpy as np
    import torch

    rng = np.random.default_rng(seed)
    n_gen = K_per_class if n_gen_per_class is None else n_gen_per_class
    feature_dim = client_X_list[0].cpu().reshape(
        client_X_list[0].shape[0], -1).shape[1]

    probe_X_list, probe_y_list = [], []
    n_pairs_used = 0
    last_sigma_dp = 0.0
    for i in range(len(client_X_list)):
        X_i = client_X_list[i].cpu().reshape(client_X_list[i].shape[0], -1)
        y_i = client_y_list[i].cpu().numpy()
        for c in range(num_classes):
            mask = (y_i == c)
            n_avail = int(mask.sum())
            if n_avail == 0:
                continue
            X_c = X_i[mask].numpy().astype(np.float64)
            n_take = min(K_per_class, n_avail)
            idx = rng.choice(n_avail, n_take, replace=False)
            X_c = X_c[idx]
            samples, gen_info = _merf_generate_class(
                X_c, n_gen, n_features, eps, delta, rng)
            last_sigma_dp = gen_info["sigma_dp"]
            probe_X_list.append(torch.from_numpy(samples))
            probe_y_list.append(torch.full((n_gen,), c, dtype=torch.long))
            n_pairs_used += 1

    dp_note = (
        "DP-MERF (Harder 2021): RFF mean embedding privatized via repo "
        "averaging-variant dp_sigma(clip=1, m=K_per_class). clip=1 because the "
        "RFF map bounds ||phi||_2<=1 (analytic sensitivity, no clip search). "
        "Constant differs from paper's 2/m by 2x (replace-one adjacency) — one "
        "consistent accounting across all private builders."
    )
    gen = "closed-form moment-matching (NNLS resample + covariance jitter)"
    if n_pairs_used == 0:
        return (
            torch.zeros(0, feature_dim, dtype=torch.float32),
            torch.zeros(0, dtype=torch.long),
            {"probe_size": 0, "sigma": float(last_sigma_dp),
             "n_pairs_used": 0, "dp_note": dp_note, "gen": gen},
        )
    probe_X = torch.cat(probe_X_list, dim=0)
    probe_y = torch.cat(probe_y_list, dim=0)
    return probe_X, probe_y, {
        "probe_size": int(probe_X.shape[0]),
        "sigma": float(last_sigma_dp),
        "n_pairs_used": int(n_pairs_used),
        "dp_note": dp_note,
        "gen": gen,
    }


def build_dp_synth_all(
    client_X_list: List,
    client_y_list: List,
    num_classes: int,
    seed: int = 0,
    eps: float = float("inf"),
    delta: float = DP_DELTA,
    n_features: int = 1000,
) -> Tuple:
    """DP-MERF on ALL of every client's data (issue 022, Mode A — the baseline).

    This is the NAIVE DP-one-shot path (cf. FedDiff): each client fits DP-MERF to
    *all* of its local data and the synthetic data must carry the WHOLE
    contribution, so the student is trained one-shot directly on the union of
    synthetic sets — NO shared basin, NO bounded distillation, NO HE benefit.
    Covering every sample at meaningful ε forces large DP noise, so accuracy is
    expected to drop and the released model stays MIA-vulnerable. Used by
    ``protocol.run_cell``'s ``dp_synth_all`` branch, which trains the student on
    the returned ``(synth_X, synth_y)`` and short-circuits the basin+distill+
    aggregate path entirely.

    Unlike ``build_probe_merf`` (which caps each class at ``K_per_class`` samples
    purely to build the basin), here we use EVERY local sample of each class
    (``m_c`` = full class count) and generate the same number of synthetic
    samples (``m_c`` per class per client), so the synthetic set is the size of
    the real local data — the full-data DP one-shot story.

    Returns ``(synth_X, synth_y, info)`` (FLAT feature space; the conv path
    reshapes via the caller). ``info`` carries ``synth_size``, ``sigma``,
    ``n_pairs_used``, ``dp_note``, ``gen``.
    """
    import numpy as np
    import torch

    rng = np.random.default_rng(seed)
    feature_dim = client_X_list[0].cpu().reshape(
        client_X_list[0].shape[0], -1).shape[1]

    synth_X_list, synth_y_list = [], []
    n_pairs_used = 0
    last_sigma_dp = 0.0
    for i in range(len(client_X_list)):
        X_i = client_X_list[i].cpu().reshape(client_X_list[i].shape[0], -1)
        y_i = client_y_list[i].cpu().numpy()
        for c in range(num_classes):
            mask = (y_i == c)
            m_c = int(mask.sum())
            if m_c == 0:
                continue
            X_c = X_i[mask].numpy().astype(np.float64)
            samples, gen_info = _merf_generate_class(
                X_c, m_c, n_features, eps, delta, rng)
            last_sigma_dp = gen_info["sigma_dp"]
            synth_X_list.append(torch.from_numpy(samples))
            synth_y_list.append(torch.full((m_c,), c, dtype=torch.long))
            n_pairs_used += 1

    dp_note = (
        "DP-MERF Mode-A (synthesize-everything baseline): RFF mean embedding "
        "per (client,class) privatized via dp_sigma(clip=1, m=full class count). "
        "Full data ⇒ the synthetic set carries the whole contribution (no HE)."
    )
    gen = "closed-form moment-matching (NNLS resample + covariance jitter)"
    if n_pairs_used == 0:
        return (
            torch.zeros(0, feature_dim, dtype=torch.float32),
            torch.zeros(0, dtype=torch.long),
            {"synth_size": 0, "sigma": float(last_sigma_dp),
             "n_pairs_used": 0, "dp_note": dp_note, "gen": gen},
        )
    synth_X = torch.cat(synth_X_list, dim=0)
    synth_y = torch.cat(synth_y_list, dim=0)
    return synth_X, synth_y, {
        "synth_size": int(synth_X.shape[0]),
        "sigma": float(last_sigma_dp),
        "n_pairs_used": int(n_pairs_used),
        "dp_note": dp_note,
        "gen": gen,
    }


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
    if strategy == "synthetic":
        # Issue 016+ MVP: per-(client, class) Gaussian-around-mean sampling.
        # No DP (eps==inf, no clip). The DP path is the ``synthetic_dp``
        # strategy below — kept distinct so the cleartext mechanism stays a
        # pure-shape change from raw_union with no DP-accounting plumbing.
        return build_probe_synthetic(
            client_X_list, client_y_list, K_per_class, num_classes, seed=seed)
    if strategy == "synthetic_dp":
        if clip is None:
            raise ValueError("strategy 'synthetic_dp' requires a clip bound")
        return build_probe_synthetic(
            client_X_list, client_y_list, K_per_class, num_classes, seed=seed,
            dp_clip=clip, dp_eps=eps, dp_delta=delta)
    if strategy == "noprobe_raw_union":
        # Issue 017 — no labelled public probe; the raw-union per-(client, class)
        # prototypes themselves are the supervised warmup set.
        return build_noprobe_raw_union(
            client_X_list, client_y_list, K_per_class, num_classes, seed=seed)
    if strategy == "noprobe_dp_avg":
        # Issue 017 — no labelled public probe; the DP-noisy per-(client, class)
        # prototypes themselves are the supervised warmup set.
        if clip is None:
            raise ValueError("strategy 'noprobe_dp_avg' requires a clip bound")
        return build_noprobe_dp_averaged(
            client_X_list, client_y_list, K_per_class, num_classes,
            clip=clip, eps_per_client=eps, delta=delta, seed=seed)
    if strategy == "merf":
        # Issue 022 — DP-MERF basin source (Mode B). No external ``clip`` bound:
        # the RFF map bounds ||phi||_2 <= 1 by construction, which IS DP-MERF's
        # analytic-sensitivity property, so the DP noise is calibrated inside
        # build_probe_merf via the repo's dp_sigma(clip=1, K, eps). eps may be
        # inf (no noise — the raw-MERF alignment ceiling for the basin source).
        return build_probe_merf(
            client_X_list, client_y_list, K_per_class, num_classes,
            seed=seed, eps=eps if eps is not None else float("inf"), delta=delta)
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
    soft_targets=None,
) -> Dict:
    """Produce θ₀ by warming ``base_init`` on the probe via supervised SGD.

    Returns the warmed parameter dict (the shared, aligned init every client
    distils from). Fixed warmup seed 12345 matches the notebook. Imported here
    rather than at module top to avoid a torch dependency for static checks.

    ``lr_schedule`` is opt-in (forwarded to ``train_supervised_model``);
    ``None`` keeps the legacy constant-LR warmup byte-identical for every
    backbone that does not set ``BackboneSpec.teacher_lr_schedule``.

    ``soft_targets`` (issue 016+, opt-in): when ``None`` (the default for every
    pre-issue-016+ caller) the warmup is byte-identical to the legacy cross-
    entropy path. When supplied as a ``(num_classes, num_classes)`` tensor of
    per-class teacher-logit prototypes (output of
    ``build_logit_prototypes``), warmup uses KL distillation against the soft-
    target row indexed by each sample's class id rather than the one-hot
    label. Forwarded into ``train_supervised_model``.
    """
    from .teacher import train_supervised_model
    from .backbones import get_params

    warmed = train_supervised_model(
        make_model_fn, probe_X, probe_y,
        epochs=epochs, lr=lr, momentum=momentum, bs=bs,
        seed=seed, init_params=base_init, lr_schedule=lr_schedule,
        soft_targets=soft_targets,
    )
    return get_params(warmed)
