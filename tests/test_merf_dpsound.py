"""Soundness tests for the DP-MERF generator (issue 027).

The bug this fixes: the old ``_merf_generate_class`` privatized the φ-space mean
embedding but then RELEASED REAL RECORDS (``base = X_c[pick]``) plus cosmetic
jitter, so the "synthetic" set literally contained raw data — no sample-level DP.
Mode A reached an implausible 0.97 @ ε=2 on MNIST because the DP never bit.

The fix replaces the closed-form record-resampling stand-in with a DP-sound
generator: privatize the per-class RFF mean embedding μ̂^priv, train a small
neural generator G to match it under the random-feature MMD, then SAMPLE FRESH
points from G. After μ̂ is privatized, G's training + sampling is post-processing
of a DP quantity, so the released samples inherit the (ε, δ) guarantee.

The HARD invariant pinned here, with zero exceptions: **no released sample equals
a raw record**. We assert it three ways — (1) directly on ``_merf_generate_class``
output (the guard's own min-distance), (2) by feeding the guard a copied record
and requiring it to RAISE, and (3) end-to-end through both public builders
(``build_probe_merf`` Mode B and ``build_dp_synth_all`` Mode A). We also pin
ε=∞ ⇒ σ_dp=0 (raw-MERF ceiling) and seed reproducibility.

torch is imported lazily via ``importorskip`` so a collection pass on a machine
without the scientific stack skips (this Mac has no torch — ast.parse only; the
tests run on VALAR's ``he_ofl`` env).
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _toy_class(np, n=24, d=12, seed=0):
    """A small, well-separated single-class real matrix ``X_c`` (numpy float64)."""
    rng = np.random.default_rng(seed)
    return rng.normal(5.0, 1.0, size=(n, d)).astype(np.float64)


# ---------------------------------------------------------------------------
# the guard: it must catch a copied record
# ---------------------------------------------------------------------------
def test_guard_raises_when_a_sample_is_a_copied_record():
    """``_merf_assert_synthetic_disjoint`` is the soundness GUARD. If ANY released
    row equals a raw record (the old-generator bug), it must raise — this is the
    regression tripwire for re-introducing raw-record passthrough."""
    np = pytest.importorskip("numpy")
    from src.phase0 import _merf_assert_synthetic_disjoint

    X_c = _toy_class(np, n=10, d=6, seed=1)
    # Build a "synthetic" set that smuggles in two exact real records — exactly
    # what ``base = X_c[pick]`` did. The guard must reject it.
    bad = np.concatenate([X_c[2:3].copy(), X_c[7:8].copy(),
                          X_c[0:1].copy()], axis=0)
    with pytest.raises(AssertionError, match="soundness violation"):
        _merf_assert_synthetic_disjoint(bad, X_c)


def test_guard_passes_for_genuinely_fresh_points():
    """Fresh continuous points are almost-surely distinct from the finite real
    set, so the guard returns a positive min distance and does not raise."""
    np = pytest.importorskip("numpy")
    from src.phase0 import _merf_assert_synthetic_disjoint

    X_c = _toy_class(np, n=10, d=6, seed=2)
    fresh = X_c + 3.0  # shifted far away — clearly not copies
    min_dist = _merf_assert_synthetic_disjoint(fresh, X_c)
    assert min_dist > 1e-6


# ---------------------------------------------------------------------------
# the generator: released samples are draws from G, never raw records
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("eps", [2.0, float("inf")])
def test_generate_class_samples_are_disjoint_from_raw_records(eps):
    """``_merf_generate_class`` must return FRESH generator draws, never rows of
    ``X_c``. We assert (a) the returned shape is (n_gen, d), (b) NO generated row
    coincides (to tight tolerance) with any real record, at both a tight ε and
    ε=∞. The internal guard already enforces this; here we re-check independently
    on the returned array so the invariant is pinned at the public boundary."""
    np = pytest.importorskip("numpy")
    pytest.importorskip("torch")
    from src.phase0 import _merf_generate_class

    X_c = _toy_class(np, n=30, d=10, seed=3)
    n_gen = 16
    rng = np.random.default_rng(123)
    samples, gen_info = _merf_generate_class(
        X_c, n_gen=n_gen, n_features=64, eps=eps, delta=1e-5, rng=rng)

    assert samples.shape == (n_gen, X_c.shape[1])
    assert samples.dtype == np.float32

    # Independent disjointness check: min L2 from each sample to the real set > 0.
    diffs = samples[:, None, :].astype(np.float64) - X_c[None, :, :]
    min_dist = np.sqrt((diffs ** 2).sum(axis=2)).min()
    assert min_dist > 1e-6, "released sample coincides with a raw record"

    # No generated row is byte-equal to any real row (the literal old bug).
    real_rows = {tuple(np.round(r, 6)) for r in X_c}
    for s in samples:
        assert tuple(np.round(s.astype(np.float64), 6)) not in real_rows

    # Provenance the guard recorded.
    assert gen_info["min_real_dist"] > 1e-6


def test_generate_class_eps_inf_is_zero_dp_noise():
    """ε=∞ ⇒ σ_dp=0 (raw-MERF ceiling): the privatized mean embedding is the raw
    mean embedding, but the released samples are STILL fresh generator draws (not
    raw records). Pins that the no-noise ceiling path is preserved."""
    np = pytest.importorskip("numpy")
    pytest.importorskip("torch")
    from src.phase0 import _merf_generate_class

    X_c = _toy_class(np, n=20, d=8, seed=4)
    rng = np.random.default_rng(7)
    samples, gen_info = _merf_generate_class(
        X_c, n_gen=12, n_features=64, eps=float("inf"), delta=1e-5, rng=rng)

    assert gen_info["sigma_dp"] == 0.0
    # even at ε=∞ the released set must be generator draws, not raw records
    diffs = samples[:, None, :].astype(np.float64) - X_c[None, :, :]
    assert np.sqrt((diffs ** 2).sum(axis=2)).min() > 1e-6


def test_generate_class_is_reproducible_under_fixed_rng():
    """A fixed numpy rng seed must reproduce the generator (torch seed is derived
    from the rng), so a resumable sweep cell is deterministic."""
    np = pytest.importorskip("numpy")
    pytest.importorskip("torch")
    from src.phase0 import _merf_generate_class

    X_c = _toy_class(np, n=20, d=8, seed=5)
    s1, _ = _merf_generate_class(
        X_c, n_gen=10, n_features=64, eps=2.0, delta=1e-5,
        rng=np.random.default_rng(999))
    s2, _ = _merf_generate_class(
        X_c, n_gen=10, n_features=64, eps=2.0, delta=1e-5,
        rng=np.random.default_rng(999))
    assert np.allclose(s1, s2)


# ---------------------------------------------------------------------------
# end-to-end through the two public builders (Mode B / Mode A)
# ---------------------------------------------------------------------------
def _two_clients(torch):
    """Two clients over 3 classes, flat feature_dim=8."""
    g = torch.Generator().manual_seed(0)
    X0 = torch.randn(12, 8, generator=g) + 4.0
    y0 = torch.tensor([0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2])
    X1 = torch.randn(9, 8, generator=g) - 4.0
    y1 = torch.tensor([0, 0, 0, 1, 1, 1, 2, 2, 2])
    return [X0, X1], [y0, y1]


def test_build_probe_merf_releases_only_generator_draws():
    """Mode B (``build_probe_merf``): the released probe must be disjoint from
    every client's raw records, at a tight ε. Pins the soundness invariant at the
    builder boundary and the info-dict contract (probe_size, sigma, n_pairs_used,
    dp_note, gen)."""
    torch = pytest.importorskip("torch")
    np = pytest.importorskip("numpy")
    from src.phase0 import build_probe_merf

    client_X, client_y = _two_clients(torch)
    pX, pY, info = build_probe_merf(
        client_X, client_y, K_per_class=4, num_classes=3,
        seed=42, eps=2.0, n_features=64)

    assert pX.shape[0] == info["probe_size"] > 0
    assert pX.shape[1] == 8
    assert info["sigma"] > 0.0           # finite eps -> DP noise on the mean
    assert info["n_pairs_used"] == 6     # 2 clients x 3 classes, each non-empty
    assert "dp_note" in info and "gen" in info
    assert "fresh" in info["gen"].lower() or "generator" in info["gen"].lower()

    # No released row coincides with ANY raw record across all clients.
    released = pX.numpy().astype(np.float64)
    all_real = torch.cat([c.reshape(c.shape[0], -1) for c in client_X],
                         dim=0).numpy().astype(np.float64)
    diffs = released[:, None, :] - all_real[None, :, :]
    assert np.sqrt((diffs ** 2).sum(axis=2)).min() > 1e-6


def test_build_dp_synth_all_releases_only_generator_draws():
    """Mode A (``build_dp_synth_all``, the DP-one-shot baseline): the WHOLE
    released synthetic set must be generator draws, never raw records — this is
    the model the MIA suite (028) attacks, so its privacy depends entirely on this
    invariant holding."""
    torch = pytest.importorskip("torch")
    np = pytest.importorskip("numpy")
    from src.phase0 import build_dp_synth_all

    client_X, client_y = _two_clients(torch)
    sX, sY, info = build_dp_synth_all(
        client_X, client_y, num_classes=3, seed=42, eps=2.0, n_features=64)

    assert sX.shape[0] == info["synth_size"] > 0
    assert sX.shape[1] == 8
    assert info["sigma"] > 0.0
    assert "dp_note" in info and "gen" in info

    released = sX.numpy().astype(np.float64)
    all_real = torch.cat([c.reshape(c.shape[0], -1) for c in client_X],
                         dim=0).numpy().astype(np.float64)
    diffs = released[:, None, :] - all_real[None, :, :]
    assert np.sqrt((diffs ** 2).sum(axis=2)).min() > 1e-6


def test_both_builders_eps_inf_zero_noise_still_generator_draws():
    """At ε=∞ both builders report sigma==0 (raw-MERF ceiling) yet STILL release
    generator draws, never raw records — the no-noise ceiling is a legitimate
    upper bound on accuracy, not a raw-data leak."""
    torch = pytest.importorskip("torch")
    np = pytest.importorskip("numpy")
    from src.phase0 import build_probe_merf, build_dp_synth_all

    client_X, client_y = _two_clients(torch)
    all_real = torch.cat([c.reshape(c.shape[0], -1) for c in client_X],
                         dim=0).numpy().astype(np.float64)

    for builder, kw, size_key in (
        (build_probe_merf, dict(K_per_class=4), "probe_size"),
        (build_dp_synth_all, dict(), "synth_size"),
    ):
        out_X, _out_y, info = builder(
            client_X, client_y, num_classes=3, seed=1,
            eps=float("inf"), n_features=64, **kw)
        assert info["sigma"] == 0.0
        released = out_X.numpy().astype(np.float64)
        diffs = released[:, None, :] - all_real[None, :, :]
        assert np.sqrt((diffs ** 2).sum(axis=2)).min() > 1e-6
