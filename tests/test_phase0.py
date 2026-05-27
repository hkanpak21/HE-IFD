"""Behaviour tests for ``src.phase0`` — the averaging-variant DP accounting and
the probe builders (the only signal that leaves clients in clear).

DP contract (module docstring + PRD "Deep-module interfaces"):

    sensitivity = clip / K_per_class
    sigma       = sensitivity * sqrt(2 * ln(1.25 / delta)) / eps      (eps < inf)
    sigma       = 0                                                   (eps == inf)

We assert the *exact* closed form (so a future refactor that fudges the
Gaussian-mechanism constant or the clip/K sensitivity fails loudly), plus the
prototype shape/count contract when some clients lack a class.

``dp_sigma`` only needs numpy; the probe-builder tests need torch tensors, so
they ``importorskip('torch')`` and operate on tiny CPU feature matrices.
"""
from __future__ import annotations

import math

import pytest


# ---------------------------------------------------------------------------
# dp_sigma: assert the exact Gaussian-mechanism formula
# ---------------------------------------------------------------------------
def test_dp_sigma_matches_exact_gaussian_mechanism_formula():
    pytest.importorskip("numpy")
    from src.phase0 import dp_sigma

    clip, K, eps, delta = 3.0, 20, 2.0, 1e-5
    got = dp_sigma(clip, K, eps, delta=delta)

    sensitivity = clip / K
    expected = sensitivity * math.sqrt(2.0 * math.log(1.25 / delta)) / eps
    assert got == pytest.approx(expected, rel=1e-12)


def test_dp_sigma_eps_infinite_is_zero_noise():
    pytest.importorskip("numpy")
    from src.phase0 import dp_sigma

    assert dp_sigma(clip=5.0, K_per_class=10, eps_per_client=float("inf")) == 0.0


def test_dp_sigma_sensitivity_scales_as_clip_over_kpc():
    """sensitivity = clip / K_per_class — sigma must be linear in clip and
    inversely linear in K_per_class, holding (eps, delta) fixed."""
    pytest.importorskip("numpy")
    from src.phase0 import dp_sigma

    base = dp_sigma(clip=2.0, K_per_class=10, eps_per_client=1.0)

    # doubling clip doubles sigma
    assert dp_sigma(clip=4.0, K_per_class=10, eps_per_client=1.0) == pytest.approx(2 * base)
    # doubling K_per_class halves sigma
    assert dp_sigma(clip=2.0, K_per_class=20, eps_per_client=1.0) == pytest.approx(base / 2)
    # the two compose: clip*2, K*2 -> unchanged
    assert dp_sigma(clip=4.0, K_per_class=20, eps_per_client=1.0) == pytest.approx(base)


def test_dp_sigma_inverse_in_epsilon():
    """Tighter privacy (smaller eps) -> proportionally larger sigma."""
    pytest.importorskip("numpy")
    from src.phase0 import dp_sigma

    s_eps1 = dp_sigma(clip=1.0, K_per_class=5, eps_per_client=1.0)
    s_eps_half = dp_sigma(clip=1.0, K_per_class=5, eps_per_client=0.5)
    assert s_eps_half == pytest.approx(2 * s_eps1)


def test_dp_sigma_delta_enters_through_log_term():
    """The delta dependence is exactly sqrt(2 ln(1.25/delta)) — assert the ratio
    between two deltas matches the closed form, pinning the constant 1.25."""
    pytest.importorskip("numpy")
    from src.phase0 import dp_sigma

    s_a = dp_sigma(clip=1.0, K_per_class=1, eps_per_client=1.0, delta=1e-5)
    s_b = dp_sigma(clip=1.0, K_per_class=1, eps_per_client=1.0, delta=1e-6)
    ratio = s_b / s_a
    expected_ratio = math.sqrt(math.log(1.25 / 1e-6)) / math.sqrt(math.log(1.25 / 1e-5))
    assert ratio == pytest.approx(expected_ratio, rel=1e-12)


# ---------------------------------------------------------------------------
# Probe builders: shapes / counts correct when some clients lack a class
# ---------------------------------------------------------------------------
def _toy_clients(torch):
    """Two clients over 3 classes, feature_dim=4, with a deliberate gap:

      client 0 has classes {0, 1}      (no class 2)
      client 1 has classes {1, 2}      (no class 0)

    so class 0 has 1 contributor, class 1 has 2, class 2 has 1 — all three
    classes are represented across the union.
    """
    feature_dim = 4
    X0 = torch.arange(0, 5 * feature_dim, dtype=torch.float32).reshape(5, feature_dim)
    y0 = torch.tensor([0, 0, 1, 1, 1])  # classes {0,1}
    X1 = torch.arange(0, 4 * feature_dim, dtype=torch.float32).reshape(4, feature_dim) + 100.0
    y1 = torch.tensor([1, 1, 2, 2])  # classes {1,2}
    return [X0, X1], [y0, y1], feature_dim


def test_raw_union_skips_absent_classes_and_caps_per_client_per_class():
    """raw_union takes min(K_per_class, available) per (client, class) and a
    client contributes nothing for a class it lacks. probe_size in info must
    equal the actual number of rows."""
    torch = pytest.importorskip("torch")
    from src.phase0 import build_probe_raw_union

    client_X, client_y, feature_dim = _toy_clients(torch)
    K_per_class = 2
    pX, pY, info = build_probe_raw_union(
        client_X, client_y, K_per_class=K_per_class, num_classes=3, seed=0
    )

    # expected rows:
    #   client0: class0 -> min(2,2)=2 ; class1 -> min(2,3)=2  => 4
    #   client1: class1 -> min(2,2)=2 ; class2 -> min(2,2)=2  => 4
    assert pX.shape == (8, feature_dim)
    assert pY.shape == (8,)
    assert info["probe_size"] == 8
    assert info["sigma"] == 0.0

    # no rows labelled with a class no client had (all 3 are present here)
    present = set(int(c) for c in pY.tolist())
    assert present == {0, 1, 2}
    # class 0 appears exactly twice (only client0 had it, capped at 2)
    assert (pY == 0).sum().item() == 2
    # class 1 appears 4 times (2 from each client)
    assert (pY == 1).sum().item() == 4


def test_raw_union_class_with_no_contributor_is_absent():
    """If NO client has class c, that class must not appear in the probe at
    all."""
    torch = pytest.importorskip("torch")
    from src.phase0 import build_probe_raw_union

    # both clients only have classes {0,1}; declare num_classes=3 so class 2 is
    # entirely absent.
    X0 = torch.randn(3, 4)
    y0 = torch.tensor([0, 0, 1])
    X1 = torch.randn(3, 4)
    y1 = torch.tensor([1, 1, 0])
    pX, pY, info = build_probe_raw_union([X0, X1], [y0, y1], K_per_class=5, num_classes=3, seed=1)

    assert 2 not in set(int(c) for c in pY.tolist())
    assert info["probe_size"] == pX.shape[0]


def test_dp_averaged_one_prototype_per_class_with_contributor():
    """build_probe_dp_averaged returns ONE averaged row per class that has at
    least one contributing client; absent classes are dropped. With eps=inf the
    contributions are noiseless (sigma==0)."""
    torch = pytest.importorskip("torch")
    from src.phase0 import build_probe_dp_averaged

    client_X, client_y, feature_dim = _toy_clients(torch)
    pX, pY, info = build_probe_dp_averaged(
        client_X, client_y,
        K_per_class=2, num_classes=3,
        clip=1e9,                      # effectively no clipping for shape check
        eps_per_client=float("inf"),  # no noise
        seed=0,
    )

    # all three classes have >=1 contributor -> 3 prototype rows
    assert pX.shape == (3, feature_dim)
    assert pY.tolist() == [0, 1, 2]
    assert info["probe_size"] == 3
    assert info["sigma"] == 0.0


def test_dp_averaged_drops_classes_with_no_contributor():
    torch = pytest.importorskip("torch")
    from src.phase0 import build_probe_dp_averaged

    # neither client has class 2 -> only classes {0,1} should yield prototypes,
    # even though num_classes=3.
    X0 = torch.randn(4, 4)
    y0 = torch.tensor([0, 0, 1, 1])
    X1 = torch.randn(2, 4)
    y1 = torch.tensor([0, 1])
    pX, pY, info = build_probe_dp_averaged(
        [X0, X1], [y0, y1],
        K_per_class=2, num_classes=3,
        clip=1e9, eps_per_client=float("inf"), seed=0,
    )

    assert pY.tolist() == [0, 1]
    assert pX.shape == (2, 4)
    assert info["probe_size"] == 2


def test_dp_averaged_sigma_recorded_matches_dp_sigma():
    """The info dict must report the same sigma the public ``dp_sigma`` formula
    produces for the given (clip, K, eps, delta)."""
    torch = pytest.importorskip("torch")
    from src.phase0 import build_probe_dp_averaged, dp_sigma

    client_X, client_y, _ = _toy_clients(torch)
    clip, K, eps, delta = 2.0, 2, 4.0, 1e-5
    _, _, info = build_probe_dp_averaged(
        client_X, client_y,
        K_per_class=K, num_classes=3,
        clip=clip, eps_per_client=eps, delta=delta, seed=0,
    )
    assert info["sigma"] == pytest.approx(dp_sigma(clip, K, eps, delta=delta), rel=1e-12)
    assert info["sigma"] > 0.0  # finite eps -> some noise
