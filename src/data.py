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
* Vision/text feature tensors for the *pretrained-backbone* path are produced by
  ``backbones.py`` (they need the frozen extractor). The loaders here cover the
  *from-scratch* image paths: MNIST (flat 784-vectors for the MLP) and the two
  conv-net datasets FashionMNIST + CIFAR-10, which return image-shaped
  ``(N, C, H, W)`` tensors that the LeNet-5 / CNN-5 backbones consume directly.

Shape contract (read before adding a from-scratch backbone)
-----------------------------------------------------------
A from-scratch loader returns exactly the tensor shape its backbone's
``forward`` consumes — the protocol passes ``X[idx]`` straight into ``model(...)``
with no reshape. ``load_mnist_tensors`` flattens to ``(N, 784)`` because
``MLP_MNIST`` takes flat vectors; the conv loaders keep ``(N, C, H, W)`` because
``LeNet5_FMNIST`` / ``CNN5_CIFAR10`` flatten internally. The Dirichlet partition,
teacher/oracle/warmup SGD, raw-union probe build, distillation, aggregation and
evaluation are all shape-agnostic (they only index dim 0 or operate on the
model's ``state_dict``), so image-shaped data flows end-to-end unchanged on the
``no_phase0`` / ``raw_union`` / ``labelled`` / ``warmup_only`` paths. The single
exception is the ``dp_avg`` Phase-0 mechanism, which is defined in flat feature
space; ``protocol.run_cell`` flattens for that probe build and reshapes the
returned probe back to image shape before warmup (see the note there).
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


def _stack_image_tensors(train_ds, test_ds):
    """Materialise a torchvision dataset into image-shaped (N, C, H, W) tensors.

    ``transforms.ToTensor`` already yields ``(C, H, W)`` per sample, so stacking
    preserves the image shape — we deliberately do NOT flatten (unlike the MNIST
    MLP loader). Used by the conv-net from-scratch loaders below.
    """
    X_train = torch.stack([train_ds[i][0] for i in range(len(train_ds))])
    y_train = torch.tensor([train_ds[i][1] for i in range(len(train_ds))])
    X_test = torch.stack([test_ds[i][0] for i in range(len(test_ds))])
    y_test = torch.tensor([test_ds[i][1] for i in range(len(test_ds))])
    return X_train, y_train, X_test, y_test


# ----------------------------------------------------------------------------
# FashionMNIST raw-image loader for LeNet-5 (1x28x28; download=False)
# ----------------------------------------------------------------------------
def load_fmnist_tensors(
    data_root: str = "data",
    cache_root: str = "cache",
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """Return (X_train[N,1,28,28], y_train, X_test[M,1,28,28], y_test) for FashionMNIST.

    IMAGE-shaped (NOT flattened): the from-scratch LeNet-5 (``backbones.make_fmnist_lenet5``)
    is a conv net and consumes ``(B, 1, 28, 28)`` directly, so this loader keeps
    the channel/spatial dims rather than viewing to 784 the way the MNIST MLP
    loader does. Normalised with the standard FashionMNIST stats (0.2860, 0.3530).
    Cached to ``cache/features/fmnist.pt`` (regenerable; gitignored on VALAR).

    GOLDEN RULE: ``download=False`` — the raw IDX files must already be present at
    ``data/FashionMNIST/raw/`` (they are, on VALAR). torchvision is imported inside
    the function so a login-node syntax/CLI check does not pull in torch.
    """
    from torchvision import datasets, transforms  # local import: heavy, VALAR-only

    cache_dir = Path(cache_root) / "features"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = cache_dir / "fmnist.pt"
    if cache.exists():
        d = torch.load(cache)
        return d["X_train"], d["y_train"], d["X_test"], d["y_test"]

    tfm = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.2860,), (0.3530,)),
    ])
    train_ds = datasets.FashionMNIST(data_root, train=True, download=False, transform=tfm)
    test_ds = datasets.FashionMNIST(data_root, train=False, download=False, transform=tfm)
    X_train, y_train, X_test, y_test = _stack_image_tensors(train_ds, test_ds)
    torch.save(
        {"X_train": X_train, "y_train": y_train, "X_test": X_test, "y_test": y_test},
        cache,
    )
    return X_train, y_train, X_test, y_test


# ----------------------------------------------------------------------------
# CIFAR-10 RAW-image loader for CNN-5 (3x32x32; download=False)
# ----------------------------------------------------------------------------
def load_cifar10_raw_tensors(
    data_root: str = "data",
    cache_root: str = "cache",
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """Return (X_train[N,3,32,32], y_train, X_test[M,3,32,32], y_test) for CIFAR-10.

    RAW IMAGE tensors for the from-scratch CNN-5 (``backbones.make_cifar10_cnn5``)
    — this is the pixel-space path and is DISTINCT from the pretrained-feature
    path in ``backbones.extract_cifar10_features`` (which returns frozen
    ResNet/ViT embeddings for the linear-head protocol). No resize: the conv net
    trains on native 32x32. Normalised with the standard CIFAR-10 channel stats
    (mean (0.4914, 0.4822, 0.4465), std (0.2470, 0.2435, 0.2616)). Cached to
    ``cache/features/cifar10_raw.pt`` (regenerable; gitignored on VALAR).

    GOLDEN RULE: ``download=False`` — the python batches must already be present
    at ``data/cifar-10-batches-py/`` (they are, on VALAR). torchvision is imported
    inside the function so a login-node syntax/CLI check does not pull in torch.
    """
    from torchvision import datasets, transforms  # local import: heavy, VALAR-only

    cache_dir = Path(cache_root) / "features"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = cache_dir / "cifar10_raw.pt"
    if cache.exists():
        d = torch.load(cache)
        return d["X_train"], d["y_train"], d["X_test"], d["y_test"]

    tfm = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2470, 0.2435, 0.2616)),
    ])
    train_ds = datasets.CIFAR10(data_root, train=True, download=False, transform=tfm)
    test_ds = datasets.CIFAR10(data_root, train=False, download=False, transform=tfm)
    X_train, y_train, X_test, y_test = _stack_image_tensors(train_ds, test_ds)
    torch.save(
        {"X_train": X_train, "y_train": y_train, "X_test": X_test, "y_test": y_test},
        cache,
    )
    return X_train, y_train, X_test, y_test
