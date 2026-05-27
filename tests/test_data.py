"""Behaviour tests for ``src.data`` — Dirichlet partition reproducibility and
public-probe / client-training disjointness.

Two externally observable contracts (PRD Testing-Decisions, "lighter
assertion"):

  * the Dirichlet partition is *seed-reproducible* — same (y, N, alpha, seed,
    num_classes) => byte-identical index split (so a sweep cell is repeatable and
    matches the colab partition);
  * the public probe carved by ``reserve_probe_and_pool`` is *disjoint* from every
    client's training data — the pool that gets partitioned across clients is the
    probe's complement, so no training example leaks into the in-clear probe.

``dirichlet_partition`` is pure numpy (no torch). The probe/pool reservation and
``partition_pool`` index torch tensors, so those tests ``importorskip('torch')``.
"""
from __future__ import annotations

import pytest

import numpy as np


def _toy_labels(n=600, num_classes=3, seed=0):
    """A balanced-ish label vector to partition."""
    rng = np.random.default_rng(seed)
    return rng.integers(0, num_classes, size=n)


# ---------------------------------------------------------------------------
# Dirichlet partition: seed reproducibility
# ---------------------------------------------------------------------------
def test_dirichlet_partition_is_seed_reproducible():
    from src.data import dirichlet_partition

    y = _toy_labels()
    kw = dict(n_clients=5, alpha=0.3, seed=42, num_classes=3)

    a = dirichlet_partition(y, **kw)
    b = dirichlet_partition(y, **kw)

    assert len(a) == len(b) == 5
    for ca, cb in zip(a, b):
        np.testing.assert_array_equal(np.sort(ca), np.sort(cb))


def test_dirichlet_partition_differs_across_seeds():
    """Sanity that the seed actually drives the split (otherwise reproducibility
    would be vacuous)."""
    from src.data import dirichlet_partition

    y = _toy_labels()
    a = dirichlet_partition(y, n_clients=5, alpha=0.3, seed=1, num_classes=3)
    b = dirichlet_partition(y, n_clients=5, alpha=0.3, seed=2, num_classes=3)

    # at least one client's index set differs between the two seeds
    differs = any(
        len(ca) != len(cb) or not np.array_equal(np.sort(ca), np.sort(cb))
        for ca, cb in zip(a, b)
    )
    assert differs


def test_dirichlet_partition_is_a_disjoint_cover_of_all_indices():
    """Every index appears in exactly one client (a partition, not a sampling):
    the union is the full index set and the clients are pairwise disjoint."""
    from src.data import dirichlet_partition

    y = _toy_labels(n=500, num_classes=4, seed=3)
    parts = dirichlet_partition(y, n_clients=6, alpha=0.5, seed=7, num_classes=4)

    all_idx = np.concatenate([p for p in parts if len(p) > 0])
    # disjoint cover: every position 0..len(y)-1 exactly once
    assert np.array_equal(np.sort(all_idx), np.arange(len(y)))
    assert len(all_idx) == len(np.unique(all_idx))  # no index duplicated


def test_dirichlet_partition_class_indices_are_consistent_with_labels():
    """Indices handed to a client genuinely point at the labels they claim — the
    partition is by-class, so a client's indices only carry labels that exist in
    the source vector."""
    from src.data import dirichlet_partition

    y = _toy_labels(n=400, num_classes=3, seed=9)
    parts = dirichlet_partition(y, n_clients=4, alpha=1.0, seed=11, num_classes=3)
    for p in parts:
        if len(p):
            assert set(np.unique(y[p])).issubset({0, 1, 2})


def test_dirichlet_low_alpha_is_more_skewed_than_high_alpha():
    """alpha controls heterogeneity: very small alpha concentrates each class on
    few clients (more empty client-class cells) than large alpha. Asserted as a
    monotone count of zero cells, not exact masses."""
    from src.data import dirichlet_partition

    y = _toy_labels(n=1200, num_classes=4, seed=5)

    def zero_cells(alpha):
        parts = dirichlet_partition(y, n_clients=8, alpha=alpha, seed=5, num_classes=4)
        count = 0
        for p in parts:
            labels = y[p] if len(p) else np.array([], dtype=int)
            for c in range(4):
                if int((labels == c).sum()) == 0:
                    count += 1
        return count

    assert zero_cells(0.01) >= zero_cells(5.0)


# ---------------------------------------------------------------------------
# Public probe disjoint from client training data
# ---------------------------------------------------------------------------
def test_reserve_probe_and_pool_are_disjoint_and_exhaustive():
    """Probe + pool partition the training set: their sizes sum to N and (by
    unique row tagging) they share no example."""
    torch = pytest.importorskip("torch")
    from src.data import reserve_probe_and_pool

    n = 200
    # tag every row with a unique value in column 0 so set-membership is exact
    X = torch.arange(n, dtype=torch.float32).reshape(n, 1)
    y = torch.arange(n) % 4
    probe_X, probe_y, pool_X, pool_y = reserve_probe_and_pool(X, y, probe_size=30, seed=123)

    assert probe_X.shape[0] == 30
    assert pool_X.shape[0] == n - 30

    probe_ids = set(probe_X[:, 0].tolist())
    pool_ids = set(pool_X[:, 0].tolist())
    assert probe_ids.isdisjoint(pool_ids)            # no shared example
    assert probe_ids | pool_ids == set(range(n))     # together: the whole set


def test_reserve_probe_is_seed_reproducible():
    torch = pytest.importorskip("torch")
    from src.data import reserve_probe_and_pool

    n = 100
    X = torch.arange(n, dtype=torch.float32).reshape(n, 1)
    y = torch.arange(n) % 5
    p1, _, _, _ = reserve_probe_and_pool(X, y, probe_size=20, seed=7)
    p2, _, _, _ = reserve_probe_and_pool(X, y, probe_size=20, seed=7)
    assert set(p1[:, 0].tolist()) == set(p2[:, 0].tolist())


def test_public_probe_disjoint_from_every_client_training_set():
    """End-to-end of the data contract: carve a probe, Dirichlet-partition the
    POOL across clients, then confirm no client training example coincides with
    any probe example (unique row tags make this exact)."""
    torch = pytest.importorskip("torch")
    from src.data import reserve_probe_and_pool, partition_pool

    n, num_classes = 500, 4
    X = torch.arange(n, dtype=torch.float32).reshape(n, 1)  # unique id per row
    rng = np.random.default_rng(0)
    y = torch.from_numpy(rng.integers(0, num_classes, size=n).astype("int64"))

    probe_X, probe_y, pool_X, pool_y = reserve_probe_and_pool(X, y, probe_size=50, seed=99)
    client_X_list, client_y_list, sample_sizes = partition_pool(
        pool_X, pool_y, n_clients=6, alpha=0.3, seed=99, num_classes=num_classes
    )

    probe_ids = set(probe_X[:, 0].tolist())
    for cx in client_X_list:
        if cx.shape[0]:
            client_ids = set(cx[:, 0].tolist())
            assert probe_ids.isdisjoint(client_ids)

    # the partition covers exactly the pool (no probe row sneaks in, none lost)
    union_client_ids = set()
    for cx in client_X_list:
        union_client_ids |= set(cx[:, 0].tolist())
    assert union_client_ids == set(pool_X[:, 0].tolist())
    assert sum(sample_sizes) == pool_X.shape[0]
