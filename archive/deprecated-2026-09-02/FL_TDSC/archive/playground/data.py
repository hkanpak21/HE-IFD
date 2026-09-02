"""MNIST loader + Dirichlet partition + probe split."""
from __future__ import annotations
import numpy as np
import torch
from torch.utils.data import Dataset, Subset, ConcatDataset
from torchvision import datasets, transforms


def load_mnist(root: str = "playground/data"):
    tfm = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))])
    train = datasets.MNIST(root=root, train=True, transform=tfm, download=False)
    test = datasets.MNIST(root=root, train=False, transform=tfm, download=False)
    return train, test


def split_probe(test_ds, probe_size: int, seed: int):
    rng = np.random.RandomState(seed)
    perm = rng.permutation(len(test_ds))
    return Subset(test_ds, perm[:probe_size].tolist()), Subset(test_ds, perm[probe_size:].tolist())


def dirichlet_partition(train_ds, n_clients: int, alpha: float, seed: int,
                        min_samples: int = 16):
    labels = np.array([train_ds[i][1] for i in range(len(train_ds))], dtype=np.int64)
    nC = int(labels.max()) + 1
    rng = np.random.RandomState(seed)
    while True:
        holdings = np.zeros((n_clients, nC), dtype=np.int64)
        idx_per = [[] for _ in range(n_clients)]
        for c in range(nC):
            cls = np.where(labels == c)[0]
            rng.shuffle(cls)
            props = rng.dirichlet([alpha] * n_clients)
            cuts = (np.cumsum(props) * len(cls)).astype(int)[:-1]
            for ci, shard in enumerate(np.split(cls, cuts)):
                idx_per[ci].extend(shard.tolist())
                holdings[ci, c] = len(shard)
        if (holdings.sum(axis=1) >= min_samples).all() or n_clients == 1:
            return idx_per, holdings


def client_subsets(train_ds, idx_per):
    return [Subset(train_ds, idx) for idx in idx_per]


def union(probe, local):
    return ConcatDataset([probe, local])
