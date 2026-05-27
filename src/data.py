"""Datasets, Dirichlet partitioning, and probe/pool reservation.

Ported from `results/colab_results/results_notebook.ipynb`:
  - `dirichlet_partition`  (Section 0.3)
  - the MNIST raw-tensor loader `get_mnist` (Section A.1)
  - the labelled-probe / pool split used at the top of every Section-A/B/C task.

Faithful-port notes
--------------------
* Partition randomness uses ``np.random.default_rng(seed)`` exactly as the
  notebook does, so a given (seed, alpha, N, num_classes) is reproducible and
  matches the colab partition byte-for-byte.
* MNIST is loaded with ``download=False`` (CLAUDE.md GOLDEN RULE — datasets are
  pre-cached on VALAR under ``data/``; the compute node has no internet). Raw
  feature tensors are cached under ``cache/features/`` so a partition/teacher
  sweep does not re-decode the images every cell.
* Vision/text feature tensors are produced by ``backbones.py`` (they need the
  pretrained extractor); the loaders here cover only the from-scratch MNIST
  path that the M1 verification cell exercises.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import numpy as np
import torch


# ----------------------------------------------------------------------------
# Dirichlet partition (verbatim logic from notebook Section 0.3)
# ----------------------------------------------------------------------------
def dirichlet_partition(
    y_np: np.ndarray,
    n_clients: int,
    alpha: float,
    seed: int,
    num_classes: int,
) -> List[np.ndarray]:
    """Dirichlet-by-class label partition of an index set.

    Returns a list of length ``n_clients`` of int index arrays (positions into
    the array ``y_np`` was taken from). Some clients may receive zero samples of
    some classes at small ``alpha`` — that heterogeneity is the point and is
    surfaced downstream via ``per_client_per_class`` counts.

    Identical to the notebook's ``dirichlet_partition`` (same RNG, same
    cumulative-split rounding), so partitions are reproducible across the port.
    """
    rng = np.random.default_rng(seed)
    by_class = [np.where(y_np == c)[0] for c in range(num_classes)]
    client_idx: List[List[int]] = [[] for _ in range(n_clients)]
    for c in range(num_classes):
        idx = by_class[c].copy()
        rng.shuffle(idx)
        props = rng.dirichlet([alpha] * n_clients)
        splits = np.split(idx, (np.cumsum(props) * len(idx)).astype(int)[:-1])
        for i, s in enumerate(splits):
            client_idx[i].extend(s.tolist())
    return [np.array(c) for c in client_idx]


def per_client_per_class_counts(
    client_y_list: List[torch.Tensor], num_classes: int
) -> List[List[int]]:
    """(n_clients, num_classes) sample-count matrix for the partition diagnostic."""
    out: List[List[int]] = []
    for y in client_y_list:
        y_np = y.cpu().numpy() if hasattr(y, "cpu") else np.asarray(y)
        out.append([int((y_np == c).sum()) for c in range(num_classes)])
    return out


# ----------------------------------------------------------------------------
# Labelled-probe / pool reservation (notebook: top of each Section task)
# ----------------------------------------------------------------------------
def reserve_probe_and_pool(
    X_train: torch.Tensor,
    y_train: torch.Tensor,
    probe_size: int,
    seed: int,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """Carve a deterministic labelled probe out of the training set.

    The probe is the labelled-public set used by the ``warmup_only`` /
    ``labelled`` Phase-0 baselines; the *pool* (its complement) is what gets
    Dirichlet-partitioned across clients and what the oracle/DP-clip use.

    Mirrors the notebook exactly: ``rng = np.random.default_rng(seed)`` then
    ``rng.choice(len(X_train), probe_size, replace=False)``.
    """
    rng = np.random.default_rng(seed)
    n = len(X_train)
    probe_idx = rng.choice(n, probe_size, replace=False)
    probe_mask = np.zeros(n, dtype=bool)
    probe_mask[probe_idx] = True
    probe_X = X_train[probe_idx]
    probe_y = y_train[probe_idx]
    pool_X = X_train[~probe_mask]
    pool_y = y_train[~probe_mask]
    return probe_X, probe_y, pool_X, pool_y


def partition_pool(
    pool_X: torch.Tensor,
    pool_y: torch.Tensor,
    n_clients: int,
    alpha: float,
    seed: int,
    num_classes: int,
) -> Tuple[List[torch.Tensor], List[torch.Tensor], List[int]]:
    """Dirichlet-split the pool into per-client (X, y) tensors + sample sizes."""
    client_idx = dirichlet_partition(pool_y.numpy(), n_clients, alpha, seed, num_classes)
    client_X_list = [pool_X[ci] for ci in client_idx]
    client_y_list = [pool_y[ci] for ci in client_idx]
    sample_sizes = [len(ci) for ci in client_idx]
    return client_X_list, client_y_list, sample_sizes


# ----------------------------------------------------------------------------
# MNIST raw-tensor loader (notebook Section A.1, download=False per CLAUDE.md)
# ----------------------------------------------------------------------------
def load_mnist_tensors(
    data_root: str = "data",
    cache_root: str = "cache",
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """Return (X_train[N,784], y_train, X_test[M,784], y_test) for MNIST.

    Normalised with the standard (0.1307, 0.3081) MNIST stats and flattened to
    784-dim vectors, matching the notebook's ``get_mnist``. Cached to
    ``cache/features/mnist.pt`` (regenerable; gitignored on VALAR).

    GOLDEN RULE: ``download=False`` — the raw IDX files must already be present
    at ``data/MNIST/raw/`` (they are, on VALAR). Import of torchvision is kept
    inside the function so that a syntax/CLI check on the login node does not
    pull in torch.
    """
    from torchvision import datasets, transforms  # local import: heavy, VALAR-only

    cache_dir = Path(cache_root) / "features"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = cache_dir / "mnist.pt"
    if cache.exists():
        d = torch.load(cache)
        return d["X_train"], d["y_train"], d["X_test"], d["y_test"]

    tfm = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,)),
    ])
    train_ds = datasets.MNIST(data_root, train=True, download=False, transform=tfm)
    test_ds = datasets.MNIST(data_root, train=False, download=False, transform=tfm)
    X_train = torch.stack([train_ds[i][0] for i in range(len(train_ds))]).view(-1, 784)
    y_train = torch.tensor([train_ds[i][1] for i in range(len(train_ds))])
    X_test = torch.stack([test_ds[i][0] for i in range(len(test_ds))]).view(-1, 784)
    y_test = torch.tensor([test_ds[i][1] for i in range(len(test_ds))])
    torch.save(
        {"X_train": X_train, "y_train": y_train, "X_test": X_test, "y_test": y_test},
        cache,
    )
    return X_train, y_train, X_test, y_test
