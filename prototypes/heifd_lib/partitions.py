"""
Dirichlet partitioning of torchvision datasets for HE-IFD cells.

Deterministic on (dataset_name, alpha, seed, N): the same tuple always
yields the same index lists across runs and across hosts. Implemented with
a locally-seeded numpy.random.RandomState so we do not perturb global state.
"""
from __future__ import annotations

from typing import List, Sequence

import numpy as np


def dirichlet_partition(
    labels: Sequence[int],
    n_clients: int,
    alpha: float,
    seed: int,
) -> List[List[int]]:
    """
    Return a list of `n_clients` index lists drawn from Dirichlet(alpha) over
    per-class proportions. Mirrors the canonical FedML / FedAvg recipe used
    throughout the legacy codebase (see legacy/src/utils.py::partition_data)
    but takes labels directly so we never read the dataset twice.

    Args:
        labels: integer class labels, one per training sample.
        n_clients: number of partitions.
        alpha: Dirichlet concentration. Lower -> more skewed.
        seed: deterministic RNG seed.

    Returns:
        List of length `n_clients`; each entry is a sorted list of dataset
        indices owned by that client. The union is a permutation of
        range(len(labels)).
    """
    rng = np.random.RandomState(seed)
    labels = np.asarray(labels, dtype=np.int64)
    n_classes = int(labels.max()) + 1

    client_indices: List[List[int]] = [[] for _ in range(n_clients)]
    for c in range(n_classes):
        class_idx = np.where(labels == c)[0]
        rng.shuffle(class_idx)

        props = rng.dirichlet(np.repeat(alpha, n_clients))
        props = np.maximum(props, 1e-10)
        props = props / props.sum()

        n_c = len(class_idx)
        splits = (props * n_c).astype(int)

        # Distribute rounding remainder deterministically.
        diff = n_c - splits.sum()
        i = 0
        while diff > 0:
            splits[i % n_clients] += 1
            diff -= 1
            i += 1
        while diff < 0:
            if splits[i % n_clients] > 0:
                splits[i % n_clients] -= 1
                diff += 1
            i += 1

        start = 0
        for cid, take in enumerate(splits):
            end = start + int(take)
            client_indices[cid].extend(class_idx[start:end].tolist())
            start = end

    for cid in range(n_clients):
        client_indices[cid].sort()
    return client_indices


def load_torchvision_labels(dataset: str, root: str = "data"):
    """
    Thin wrapper around torchvision datasets that returns the train-set
    label vector. Kept here so partition logic does not pull torch at
    import time when only the partition math is needed.
    """
    import torchvision  # noqa: WPS433  (intentional lazy import)

    dataset = dataset.lower().replace("-", "")
    if dataset == "mnist":
        ds = torchvision.datasets.MNIST(root, train=True, download=True)
        return np.asarray(ds.targets, dtype=np.int64)
    if dataset == "fashionmnist":
        ds = torchvision.datasets.FashionMNIST(root, train=True, download=True)
        return np.asarray(ds.targets, dtype=np.int64)
    if dataset == "cifar10":
        ds = torchvision.datasets.CIFAR10(root, train=True, download=True)
        return np.asarray(ds.targets, dtype=np.int64)
    if dataset == "svhn":
        ds = torchvision.datasets.SVHN(root, split="train", download=True)
        return np.asarray(ds.labels, dtype=np.int64)
    if dataset == "cifar100":
        ds = torchvision.datasets.CIFAR100(root, train=True, download=True)
        return np.asarray(ds.targets, dtype=np.int64)
    raise ValueError(f"Unknown dataset: {dataset}")
