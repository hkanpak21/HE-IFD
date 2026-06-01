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


# ----------------------------------------------------------------------------
# CIFAR-100 RAW-image loader (issue 012; 100 classes, 3x32x32; download=False)
# ----------------------------------------------------------------------------
def load_cifar100_tensors(
    data_root: str = "data",
    cache_root: str = "cache",
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """Return (X_train[N,3,32,32], y_train, X_test[M,3,32,32], y_test) for CIFAR-100.

    Mirrors ``load_cifar10_raw_tensors`` but for the 100-class variant — drives
    the harder-vision-dataset cells in issue 012 (ViT-B/32 on CIFAR-10 is
    saturated at 0.97 IID; CIFAR-100's ~0.75-0.80 linear-probe ceiling gives
    the protocol headroom to demonstrate distillation value). Same channel
    stats as CIFAR-10 (the two datasets share images; mean/std are nearly
    identical and reusing the CIFAR-10 stats is the standard torchvision
    convention — minimises preprocessing skew vs the existing CIFAR-10 path).
    Cached to ``cache/features/cifar100_raw.pt`` (regenerable; gitignored).

    GOLDEN RULE: ``download=False`` — the python batches must already be present
    at ``data/cifar-100-python/`` on VALAR; ``jobs/prefetch_login.py`` populates
    them on the login node when ``--include-cifar100`` is set. torchvision is
    imported inside the function so a login-node syntax/CLI check does not pull
    in torch.
    """
    from torchvision import datasets, transforms  # local import: heavy, VALAR-only

    cache_dir = Path(cache_root) / "features"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = cache_dir / "cifar100_raw.pt"
    if cache.exists():
        d = torch.load(cache)
        return d["X_train"], d["y_train"], d["X_test"], d["y_test"]

    tfm = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2470, 0.2435, 0.2616)),
    ])
    train_ds = datasets.CIFAR100(data_root, train=True, download=False, transform=tfm)
    test_ds = datasets.CIFAR100(data_root, train=False, download=False, transform=tfm)
    X_train, y_train, X_test, y_test = _stack_image_tensors(train_ds, test_ds)
    torch.save(
        {"X_train": X_train, "y_train": y_train, "X_test": X_test, "y_test": y_test},
        cache,
    )
    return X_train, y_train, X_test, y_test


# ----------------------------------------------------------------------------
# Tiny-ImageNet RAW-image loader (issue 012; 200 classes, 3x64x64; ImageFolder)
# ----------------------------------------------------------------------------
def load_tiny_imagenet_tensors(
    data_root: str = "data",
    cache_root: str = "cache",
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """Return (X_train[N,3,64,64], y_train, X_test[M,3,64,64], y_test) for Tiny-ImageNet.

    Stanford CS231n Tiny-ImageNet-200: 200 classes × 500 train images each
    (100K total), 50 images per class in the validation set. Native 64×64.
    Layout produced by the prefetch script's extraction:

        data/tiny-imagenet-200/
            wnids.txt
            train/<wnid>/images/<filename>.JPEG    (500 images per wnid)
            val/images/<filename>.JPEG             (10000 images, flat dir)
            val/val_annotations.txt                 (<filename>\\t<wnid>\\t...)

    The ``val`` directory is used as the **test set** (Tiny-ImageNet's test
    split has no labels, by convention val is treated as test for evaluation).
    Class indices are assigned by sorting the 200 wnids lexicographically so
    train and val agree.

    Normalised with the standard ImageNet channel stats (this is an ImageNet
    subset; the ImageNet-pretrained backbones in ``backbones.py`` expect those
    stats anyway, and the from-scratch path is not used on this dataset).
    Cached to ``cache/features/tiny_imagenet_raw.pt`` (regenerable; gitignored).

    GOLDEN RULE: ``download=False`` — the extracted directory must already exist
    at ``data/tiny-imagenet-200/`` on VALAR. ``jobs/prefetch_login.py`` populates
    it on the login node when ``--include-tiny-imagenet`` is set (download +
    unzip; ~250MB on disk). torchvision is imported inside the function so a
    login-node syntax/CLI check does not pull in torch.

    NOTE: This loader is **best-effort** per issue 012. CIFAR-100 is the
    higher-value cell; Tiny-ImageNet is included so the orchestrator can
    optionally run those rows in the verify wrapper. If the on-disk layout
    deviates from the standard Stanford zip layout, this loader raises
    FileNotFoundError with a clear message rather than silently returning
    garbage.
    """
    from PIL import Image
    from torchvision import transforms  # local import: heavy, VALAR-only

    cache_dir = Path(cache_root) / "features"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = cache_dir / "tiny_imagenet_raw.pt"
    if cache.exists():
        d = torch.load(cache)
        return d["X_train"], d["y_train"], d["X_test"], d["y_test"]

    root = Path(data_root) / "tiny-imagenet-200"
    if not root.exists():
        raise FileNotFoundError(
            f"Tiny-ImageNet directory {root} not found. Run "
            f"`python jobs/prefetch_login.py --include-tiny-imagenet` on the "
            f"VALAR login node first."
        )

    # Class index = lexicographic position of wnid in wnids.txt (consistent
    # with the standard CS231n convention).
    wnids_path = root / "wnids.txt"
    if not wnids_path.exists():
        raise FileNotFoundError(
            f"Expected {wnids_path} (Tiny-ImageNet class-id manifest)."
        )
    wnids = sorted(wnids_path.read_text().split())
    wnid_to_idx = {w: i for i, w in enumerate(wnids)}

    tfm = transforms.Compose([
        transforms.ToTensor(),  # PIL -> (C, H, W) float in [0,1]
        # ImageNet stats: this is an ImageNet subset and the linear-probe
        # head consumes ImageNet-pretrained features (ResNet/ViT) further on.
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    def _load_pil(p: Path) -> "torch.Tensor":
        # Tiny-ImageNet ships a handful of grayscale images; ``convert("RGB")``
        # promotes them to 3 channels so the tensor stack is uniform shape.
        with Image.open(p) as img:
            return tfm(img.convert("RGB"))

    # Train: data/tiny-imagenet-200/train/<wnid>/images/*.JPEG (500 per wnid).
    train_root = root / "train"
    train_X_list = []
    train_y_list = []
    for wnid in wnids:
        img_dir = train_root / wnid / "images"
        if not img_dir.exists():
            raise FileNotFoundError(
                f"Expected {img_dir} (Tiny-ImageNet train images for {wnid})."
            )
        idx = wnid_to_idx[wnid]
        for p in sorted(img_dir.iterdir()):
            train_X_list.append(_load_pil(p))
            train_y_list.append(idx)
    X_train = torch.stack(train_X_list)
    y_train = torch.tensor(train_y_list, dtype=torch.long)

    # Val: data/tiny-imagenet-200/val/images/*.JPEG (flat) + val_annotations.txt
    val_root = root / "val"
    val_ann = val_root / "val_annotations.txt"
    if not val_ann.exists():
        raise FileNotFoundError(
            f"Expected {val_ann} (Tiny-ImageNet val_annotations)."
        )
    val_img_dir = val_root / "images"
    val_X_list = []
    val_y_list = []
    # Each line: <filename>\t<wnid>\t<bbox_x1>\t<bbox_y1>\t<bbox_x2>\t<bbox_y2>
    for line in val_ann.read_text().splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        fname, wnid = parts[0], parts[1]
        if wnid not in wnid_to_idx:
            # Unknown wnid (shouldn't happen for a clean Stanford dump); skip
            # so a corrupted line doesn't poison the whole tensor stack.
            continue
        val_X_list.append(_load_pil(val_img_dir / fname))
        val_y_list.append(wnid_to_idx[wnid])
    X_test = torch.stack(val_X_list)
    y_test = torch.tensor(val_y_list, dtype=torch.long)

    torch.save(
        {"X_train": X_train, "y_train": y_train, "X_test": X_test, "y_test": y_test},
        cache,
    )
    return X_train, y_train, X_test, y_test


# ----------------------------------------------------------------------------
# Fine-grained vision datasets (issue ft02): CUB-200-2011, Stanford Cars,
# FGVC-Aircraft. These are the "frozen-backbone NOT linear-probe-solvable"
# tasks the fine-tuning pivot needs (ViT-B/32 saturates CIFAR-10 at 0.97).
# ----------------------------------------------------------------------------
#
# DESIGN — why these return torchvision *datasets*, not pre-decoded raw tensors
# ----------------------------------------------------------------------------
# Unlike MNIST/CIFAR (small, fixed 28/32 px), the fine-grained sets are tens of
# thousands of variable-resolution natural images that must be Resize(224)-d for
# the ImageNet backbones. Caching the *decoded* 224×224×3 raw tensors would be
# 7-10 GB per dataset and pointless: the protocol only ever consumes the FROZEN
# FEATURES (~tens of MB/dataset at 768-d), which ``backbones.extract_finegrained_*``
# caches once. So the loaders below return a ``torchvision`` dataset the extractor
# drives directly with the backbone's own transform — exactly the
# ``extract_cifar10_features`` pattern, not the Tiny-ImageNet raw-tensor pattern.
# (Tiny-ImageNet pre-decodes because it is the from-scratch/raw-pixel path too;
# the fine-grained sets are pretrained-feature-only.)
#
# OFFLINE CONTRACT — ``download=False`` after a one-time fetch
# ----------------------------------------------------------------------------
# All three are placed on disk once (login node / Colab; see fetch + license
# notes per loader) and then opened with ``download=False``. Stanford Cars and
# FGVC-Aircraft use the torchvision built-in dataset classes (which read the
# standard on-disk layout); CUB-200-2011 has no torchvision class, so it is read
# from its standard ``images/<class>/<file>.jpg`` tree + index files (the same
# robust offline approach as ``load_tiny_imagenet_tensors``). None of the loaders
# ever download — each raises FileNotFoundError with the fetch command if absent.


def _finegrained_root(data_root: str, name: str) -> Path:
    return Path(data_root) / name


def make_cub200_datasets(transform, data_root: str = "data"):
    """Return (train_ds, test_ds, num_classes=200) for CUB-200-2011.

    CUB-200-2011 (Caltech-UCSD Birds): 200 bird species, 11,788 images total,
    official split 5,994 train / 5,794 test (per ``train_test_split.txt``). There
    is NO torchvision built-in for CUB, so we read the standard release layout
    via the index files shipped in the tarball:

        data/CUB_200_2011/
            images/<NNN.classname>/<file>.jpg
            images.txt                 (<img_id> <relative_path>)
            image_class_labels.txt     (<img_id> <class_id 1..200>)
            train_test_split.txt       (<img_id> <is_train 0|1>)
            classes.txt                (<class_id> <NNN.classname>)

    Class index = ``class_id − 1`` (0..199), matching the release's 1-based ids.
    A lightweight ``torch.utils.data.Dataset`` is built over the official split
    so the extractor's DataLoader can stream it under the backbone transform.

    FETCH (login node / Colab, once):
        # CUB-200-2011, ~1.1 GB. Official Caltech mirror:
        url=https://data.caltech.edu/records/65de6-vp158/files/CUB_200_2011.tgz
        curl -L "$url" -o data/CUB_200_2011.tgz && tar -xzf data/CUB_200_2011.tgz -C data/
    LICENSE: research / non-commercial use (Caltech-UCSD Birds-200-2011, Wah et
        al. 2011). Images sourced from Flickr; cite the CUB-200-2011 tech report.

    ``download=False`` semantics: the loader NEVER downloads — it raises
    FileNotFoundError with the fetch command if the tree is absent.
    """
    from torch.utils.data import Dataset
    from PIL import Image

    root = _finegrained_root(data_root, "CUB_200_2011")
    if not (root / "images.txt").exists():
        raise FileNotFoundError(
            f"CUB-200-2011 not found at {root}. Fetch it once on the login "
            f"node:\n  url=https://data.caltech.edu/records/65de6-vp158/files/"
            f"CUB_200_2011.tgz\n  curl -L \"$url\" -o {data_root}/CUB_200_2011.tgz "
            f"&& tar -xzf {data_root}/CUB_200_2011.tgz -C {data_root}/"
        )

    def _read_pairs(fname):
        out = {}
        for line in (root / fname).read_text().splitlines():
            parts = line.split()
            if len(parts) >= 2:
                out[int(parts[0])] = parts[1]
        return out

    id_to_path = _read_pairs("images.txt")
    id_to_label = {k: int(v) - 1 for k, v in _read_pairs("image_class_labels.txt").items()}
    id_to_istrain = {k: int(v) for k, v in _read_pairs("train_test_split.txt").items()}

    train_items, test_items = [], []
    for img_id, rel in sorted(id_to_path.items()):
        item = (str(root / "images" / rel), id_to_label[img_id])
        (train_items if id_to_istrain.get(img_id, 0) == 1 else test_items).append(item)

    class _CUBSplit(Dataset):
        def __init__(self, items, tfm):
            self.items = items
            self.tfm = tfm

        def __len__(self):
            return len(self.items)

        def __getitem__(self, i):
            path, label = self.items[i]
            with Image.open(path) as img:
                x = self.tfm(img.convert("RGB"))
            return x, label

    return _CUBSplit(train_items, transform), _CUBSplit(test_items, transform), 200


def make_stanford_cars_datasets(transform, data_root: str = "data"):
    """Return (train_ds, test_ds, num_classes=196) for Stanford Cars.

    Stanford Cars: 196 car models, 16,185 images, official split 8,144 train /
    8,041 test. Read via torchvision's built-in ``datasets.StanfordCars`` with
    ``download=False`` (the torchvision auto-download URL is dead upstream, so
    the files MUST be placed on disk manually — see FETCH).

    On-disk layout torchvision expects (``data/stanford_cars/``):
        cars_train/<file>.jpg
        cars_test/<file>.jpg
        devkit/cars_meta.mat, devkit/cars_train_annos.mat
        cars_test_annos_withlabels.mat

    FETCH (login node / Colab, once — manual, the torchvision mirror is gone):
        # Kaggle mirror is the reliable source as of 2024+:
        #   kaggle datasets download -d jutrera/stanford-car-dataset-by-classes-folder
        # or an HF mirror. Place files under data/stanford_cars/ in the layout
        # above, then load offline with download=False.
    LICENSE: research / non-commercial (Krause et al., 3D Object Representations
        for Fine-Grained Categorization, ICCV-W 2013). Cite the Stanford Cars
        dataset; images are not redistributed by torchvision.

    Labels are 0..195 (torchvision returns 0-based class ids).
    """
    from torchvision import datasets

    root = _finegrained_root(data_root, "stanford_cars")
    try:
        train_ds = datasets.StanfordCars(str(data_root), split="train",
                                         transform=transform, download=False)
        test_ds = datasets.StanfordCars(str(data_root), split="test",
                                        transform=transform, download=False)
    except (RuntimeError, OSError) as e:
        raise FileNotFoundError(
            f"Stanford Cars not found/decodable under {root}. The torchvision "
            f"auto-download URL is dead; place the files manually (Kaggle/HF "
            f"mirror) under {root}/ in the cars_train/cars_test/devkit layout, "
            f"then load with download=False. Original error: {e}"
        ) from e
    return train_ds, test_ds, 196


def make_fgvc_aircraft_datasets(transform, data_root: str = "data",
                                annotation_level: str = "variant"):
    """Return (train_ds, test_ds, num_classes) for FGVC-Aircraft.

    FGVC-Aircraft: 10,000 images of aircraft, hierarchical labels. At the
    default ``annotation_level="variant"`` there are 100 classes (the standard
    fine-grained benchmark setting); "family"=70, "manufacturer"=30 are also
    available. Official split: 6,667 train (train+val) / 3,333 test. Read via
    torchvision's built-in ``datasets.FGVCAircraft`` with ``download=False``.

    The torchvision class reads ``data/fgvc-aircraft-2013b/``. We use the
    combined ``trainval`` split for train and ``test`` for test (the conventional
    train/test partition).

    FETCH (login node / Colab, once):
        # torchvision can fetch it (the VGG mirror is live); trigger on login
        # node so compute nodes load offline:
        python -c "from torchvision.datasets import FGVCAircraft as A; \\
            A('data', split='trainval', download=True); \\
            A('data', split='test', download=True)"
    LICENSE: research / non-commercial (Maji et al., Fine-Grained Visual
        Classification of Aircraft, 2013). Cite the FGVC-Aircraft dataset.

    Labels are 0-based class ids over the chosen ``annotation_level``.
    """
    from torchvision import datasets

    root = _finegrained_root(data_root, "fgvc-aircraft-2013b")
    try:
        train_ds = datasets.FGVCAircraft(
            str(data_root), split="trainval", annotation_level=annotation_level,
            transform=transform, download=False)
        test_ds = datasets.FGVCAircraft(
            str(data_root), split="test", annotation_level=annotation_level,
            transform=transform, download=False)
    except (RuntimeError, OSError) as e:
        raise FileNotFoundError(
            f"FGVC-Aircraft not found under {root}. Fetch once on the login "
            f"node: python -c \"from torchvision.datasets import FGVCAircraft "
            f"as A; A('{data_root}', split='trainval', download=True); "
            f"A('{data_root}', split='test', download=True)\". Original error: {e}"
        ) from e
    # num_classes depends on annotation_level: variant=100, family=70, manuf=30.
    nc = {"variant": 100, "family": 70, "manufacturer": 30}[annotation_level]
    return train_ds, test_ds, nc


# ----------------------------------------------------------------------------
# DomainNet single-domain split (issue ft02): the documented domain-shift option.
# ----------------------------------------------------------------------------
def make_domainnet_datasets(transform, data_root: str = "data",
                            domain: str = "clipart"):
    """Return (train_ds, test_ds, num_classes=345) for one DomainNet domain.

    DomainNet (Peng et al., ICCV 2019): 6 domains (clipart, infograph, painting,
    quickdraw, real, sketch), 345 object classes shared across domains — the
    standard domain-shift / feature-skew benchmark. We load ONE domain at a time
    (default ``clipart``, a clean-loading + widely-cited single split) via its
    official train/test list files:

        data/domainnet/
            <domain>/<class>/<file>.jpg
            <domain>_train.txt          (<relative_path> <class_id 0..344>)
            <domain>_test.txt

    A single domain is the domain-shift axis the PRD asks for: train the
    federation on one shifted domain whose ImageNet-frozen features are weaker
    than the natural-photo "real" domain, giving fine-tuning headroom.

    NOTE — Tiny-ImageNet is the PRIMARY large-label/domain-shift choice (it
    already loads cleanly via ``load_tiny_imagenet_tensors`` and is wired into
    BACKBONES). DomainNet is the DOCUMENTED ALTERNATIVE per the issue ("Tiny-
    ImageNet and/or one DomainNet split — pick what loads cleanly, document it").
    This loader is provided + syntax-validated so the orchestrator can opt into a
    true domain-shift cell, but the headline large-label task is Tiny-ImageNet.

    FETCH (login node / Colab, once — per domain, ``clipart`` is ~1.2 GB):
        base=http://csr.bu.edu/ftp/visda/2019/multi-source
        mkdir -p data/domainnet
        curl -L "$base/clipart.zip" -o data/clipart.zip
        curl -L "$base/txt/clipart_train.txt" -o data/domainnet/clipart_train.txt
        curl -L "$base/txt/clipart_test.txt"  -o data/domainnet/clipart_test.txt
        unzip -q data/clipart.zip -d data/domainnet/
    LICENSE: research / non-commercial (DomainNet, Moment Matching for Multi-
        Source Domain Adaptation, Peng et al. 2019). Cite the DomainNet paper.

    Labels are the 0..344 class ids from the official list files.
    """
    from torch.utils.data import Dataset
    from PIL import Image

    root = _finegrained_root(data_root, "domainnet")
    train_list = root / f"{domain}_train.txt"
    test_list = root / f"{domain}_test.txt"
    if not train_list.exists():
        raise FileNotFoundError(
            f"DomainNet domain {domain!r} not found at {root} (missing "
            f"{train_list.name}). Fetch the domain zip + train/test txt lists "
            f"from http://csr.bu.edu/ftp/visda/2019/multi-source and unzip "
            f"under {root}/ (see this loader's docstring for the exact commands)."
        )

    def _read_list(p):
        items = []
        for line in p.read_text().splitlines():
            parts = line.split()
            if len(parts) >= 2:
                items.append((str(root / parts[0]), int(parts[1])))
        return items

    train_items = _read_list(train_list)
    test_items = _read_list(test_list)

    class _DomainNetSplit(Dataset):
        def __init__(self, items, tfm):
            self.items = items
            self.tfm = tfm

        def __len__(self):
            return len(self.items)

        def __getitem__(self, i):
            path, label = self.items[i]
            with Image.open(path) as img:
                x = self.tfm(img.convert("RGB"))
            return x, label

    return _DomainNetSplit(train_items, transform), _DomainNetSplit(test_items, transform), 345
