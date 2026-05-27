"""MNIST loading, Dirichlet partition, probe extraction."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import numpy as np
import torch
from torch.utils.data import Dataset, Subset
from torchvision import datasets, transforms


def load_mnist(root: str = "data") -> tuple[Dataset, Dataset]:
    """Load MNIST from the user's data/ root (data/MNIST/raw/*-ubyte already present).

    `download=False` -- never re-download. If the files are missing the load
    fails fast rather than silently fetching from the network.
    """
    tfm = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))])
    train = datasets.MNIST(root=root, train=True, transform=tfm, download=False)
    test = datasets.MNIST(root=root, train=False, transform=tfm, download=False)
    return train, test


def split_probe_from_test(test_ds: Dataset, probe_size: int, seed: int) -> tuple[Subset, Subset]:
    """Held-out probe is a 5000-sample subset of the *test* set per FedMD convention.

    The remaining test samples are the global eval set (so probe and eval don't overlap).
    """
    rng = np.random.RandomState(seed)
    n = len(test_ds)
    perm = rng.permutation(n)
    probe_idx = perm[:probe_size].tolist()
    eval_idx = perm[probe_size:].tolist()
    return Subset(test_ds, probe_idx), Subset(test_ds, eval_idx)


def dirichlet_partition(
    train_ds: Dataset,
    n_clients: int,
    alpha: float,
    seed: int,
    min_samples_per_client: int = 32,
) -> tuple[List[List[int]], np.ndarray]:
    """Dirichlet-by-class partition of the training set into n_clients shards.

    Returns
    -------
    indices_per_client : list of length n_clients of train-index lists.
    per_class_holdings : (n_clients, n_classes) int array, sample counts.

    Notes
    -----
    Some clients may end up with zero samples of some classes -- this is a
    property of small alpha and is intentionally surfaced via per_class_holdings.
    A safety net (min_samples_per_client) only triggers if a client would get
    fewer than min_samples_per_client total samples; we redraw the affected
    rows of the Dirichlet sample in that case (rare at alpha=0.1, N<=32).
    """
    labels = np.array([train_ds[i][1] for i in range(len(train_ds))], dtype=np.int64)
    n_classes = int(labels.max()) + 1
    rng = np.random.RandomState(seed)

    while True:
        per_class_holdings = np.zeros((n_clients, n_classes), dtype=np.int64)
        indices_per_client: List[List[int]] = [[] for _ in range(n_clients)]
        for c in range(n_classes):
            class_idx = np.where(labels == c)[0]
            rng.shuffle(class_idx)
            proportions = rng.dirichlet(alpha=[alpha] * n_clients)
            # Cumulative split points
            cuts = (np.cumsum(proportions) * len(class_idx)).astype(int)[:-1]
            shards = np.split(class_idx, cuts)
            for client_i, shard in enumerate(shards):
                indices_per_client[client_i].extend(shard.tolist())
                per_class_holdings[client_i, c] = len(shard)
        client_totals = per_class_holdings.sum(axis=1)
        if (client_totals >= min_samples_per_client).all() or n_clients == 1:
            break
        # else redraw (rare)
    return indices_per_client, per_class_holdings


def client_subsets(
    train_ds: Dataset, indices_per_client: List[List[int]]
) -> List[Subset]:
    return [Subset(train_ds, idx) for idx in indices_per_client]


def probe_and_local_union_dataset(probe: Subset, local: Subset) -> Dataset:
    """Concatenation of public probe and a client's local data for distillation."""
    return torch.utils.data.ConcatDataset([probe, local])


def materialize_probe_tensor(probe: Subset) -> tuple[torch.Tensor, torch.Tensor]:
    """Stack the probe into a single (P, 784) tensor + (P,) label tensor.

    Used by the server-side teacher-prediction pass when distillation uses
    only the probe.  For probe + local, see probe_and_local_union_dataset.
    """
    xs, ys = [], []
    for i in range(len(probe)):
        x, y = probe[i]
        xs.append(x.view(-1))
        ys.append(int(y))
    X = torch.stack(xs, dim=0)
    y = torch.tensor(ys, dtype=torch.long)
    return X, y
