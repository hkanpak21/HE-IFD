"""CIFAR-10 / CIFAR-100 loaders for ViT-B/16 fine-tuning.

ViT-B/16 expects 224x224 RGB input. CIFAR is 32x32 RGB. We upscale via
bilinear interp + apply ImageNet normalization (matches the pretrained
backbone's expected input distribution).

Dirichlet-by-class partition same as src/v1/data.py.
"""
from __future__ import annotations

import numpy as np
import torch
from torch.utils.data import Dataset, Subset
from torchvision import datasets, transforms


def vit_train_transform():
    return transforms.Compose([
        transforms.Resize(224, interpolation=transforms.InterpolationMode.BILINEAR),
        transforms.RandomCrop(224, padding=8),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225]),
    ])


def vit_eval_transform():
    return transforms.Compose([
        transforms.Resize(224, interpolation=transforms.InterpolationMode.BILINEAR),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225]),
    ])


def load_cifar10(root: str = "data"):
    train = datasets.CIFAR10(root=root, train=True, transform=vit_train_transform(),
                             download=False)
    test = datasets.CIFAR10(root=root, train=False, transform=vit_eval_transform(),
                            download=False)
    return train, test


def load_cifar100(root: str = "data"):
    train = datasets.CIFAR100(root=root, train=True, transform=vit_train_transform(),
                              download=False)
    test = datasets.CIFAR100(root=root, train=False, transform=vit_eval_transform(),
                             download=False)
    return train, test


def split_probe_from_test(test_ds, probe_size: int, seed: int):
    rng = np.random.RandomState(seed)
    n = len(test_ds)
    perm = rng.permutation(n)
    return Subset(test_ds, perm[:probe_size].tolist()), Subset(test_ds, perm[probe_size:].tolist())


def dirichlet_partition(train_ds, n_clients: int, alpha: float, seed: int,
                        min_samples_per_client: int = 64):
    """Dirichlet-by-class partition. Returns (idx_per_client, holdings (N, C))."""
    # CIFAR-10 has .targets; CIFAR-100 has .targets too. Both are lists/arrays.
    labels = np.array(train_ds.targets, dtype=np.int64)
    n_classes = int(labels.max()) + 1
    rng = np.random.RandomState(seed)
    while True:
        holdings = np.zeros((n_clients, n_classes), dtype=np.int64)
        idx_per = [[] for _ in range(n_clients)]
        for c in range(n_classes):
            cls_idx = np.where(labels == c)[0]
            rng.shuffle(cls_idx)
            props = rng.dirichlet([alpha] * n_clients)
            cuts = (np.cumsum(props) * len(cls_idx)).astype(int)[:-1]
            shards = np.split(cls_idx, cuts)
            for i, shard in enumerate(shards):
                idx_per[i].extend(shard.tolist())
                holdings[i, c] = len(shard)
        totals = holdings.sum(axis=1)
        if (totals >= min_samples_per_client).all() or n_clients == 1:
            return idx_per, holdings


def client_subsets(train_ds, idx_per):
    return [Subset(train_ds, idx) for idx in idx_per]
