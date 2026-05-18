"""Shadow-model training infrastructure for LiRA (issue 21 / A7).

LiRA (Carlini et al. 2022, ``carlini2022membership``) calibrates per-point
logit distributions using a population of "shadow" models trained on random
~50% splits of the same data distribution as the target. For each candidate
point, the shadow models that *included* the point form the "in" distribution
and those that *excluded* it form the "out" distribution; the target model's
logit on that point is then scored against the in-vs-out Gaussian likelihood
ratio (see ``lira.py``).

This module owns:

- Tiny per-dataset architectures matching the released-student family used
  in the HE-IFD pipeline:
    * MNIST / FashionMNIST -> LeNet-5
    * CIFAR-10 -> ResNet-8
- A ``train_shadow_models(dataset, n_shadows, victim_size, seed)`` driver
  that trains the shadows and persists each one (state dict + the in/out
  membership mask) to a cache directory keyed by (dataset, seed).
- Cache helpers so that subsequent MIA invocations on the same
  (dataset, seed) skip retraining.

GOLDEN RULE: heavy training paths in this file must never be invoked from
the login node. The driver enforces a CUDA-availability check by default.
"""
from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np


LOG = logging.getLogger("mia_lib.shadow_models")


# ---------------------------------------------------------------------------
# Architectures (kept local so this file is self-contained and can be unit-
# tested without depending on the rest of the prototype tree).
# ---------------------------------------------------------------------------
def build_lenet5(num_classes: int = 10, in_channels: int = 1):
    """LeNet-5 used for MNIST / FashionMNIST shadow models.

    Matches the released-student LeNet-5 referenced by action plan A4 line
    headline-grid spec (issue 18). Input: 1x28x28; output: ``num_classes``
    logits.
    """
    import torch.nn as nn

    return nn.Sequential(
        nn.Conv2d(in_channels, 6, kernel_size=5, padding=2),
        nn.ReLU(inplace=True),
        nn.AvgPool2d(2),
        nn.Conv2d(6, 16, kernel_size=5),
        nn.ReLU(inplace=True),
        nn.AvgPool2d(2),
        nn.Flatten(),
        nn.Linear(16 * 5 * 5, 120),
        nn.ReLU(inplace=True),
        nn.Linear(120, 84),
        nn.ReLU(inplace=True),
        nn.Linear(84, num_classes),
    )


def build_resnet8(num_classes: int = 10):
    """A small ResNet-8 (3 residual blocks) for CIFAR-10 shadow models.

    Matches the spirit of the issue-18 released-student CIFAR-10 architecture.
    Kept intentionally small so we can fit ``n_shadows=64`` shadows inside
    the 4 h T4 budget noted in jobs/mia_lira.sh.
    """
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    class BasicBlock(nn.Module):
        def __init__(self, in_ch, out_ch, stride=1):
            super().__init__()
            self.conv1 = nn.Conv2d(in_ch, out_ch, 3, stride, 1, bias=False)
            self.bn1 = nn.BatchNorm2d(out_ch)
            self.conv2 = nn.Conv2d(out_ch, out_ch, 3, 1, 1, bias=False)
            self.bn2 = nn.BatchNorm2d(out_ch)
            self.short = nn.Sequential()
            if stride != 1 or in_ch != out_ch:
                self.short = nn.Sequential(
                    nn.Conv2d(in_ch, out_ch, 1, stride, bias=False),
                    nn.BatchNorm2d(out_ch),
                )

        def forward(self, x):
            out = F.relu(self.bn1(self.conv1(x)))
            out = self.bn2(self.conv2(out))
            out = out + self.short(x)
            return F.relu(out)

    class ResNet8(nn.Module):
        def __init__(self):
            super().__init__()
            self.stem = nn.Sequential(
                nn.Conv2d(3, 16, 3, 1, 1, bias=False),
                nn.BatchNorm2d(16),
                nn.ReLU(inplace=True),
            )
            self.layer1 = BasicBlock(16, 16, stride=1)
            self.layer2 = BasicBlock(16, 32, stride=2)
            self.layer3 = BasicBlock(32, 64, stride=2)
            self.pool = nn.AdaptiveAvgPool2d(1)
            self.fc = nn.Linear(64, num_classes)

        def forward(self, x):
            x = self.stem(x)
            x = self.layer1(x)
            x = self.layer2(x)
            x = self.layer3(x)
            x = self.pool(x).flatten(1)
            return self.fc(x)

    return ResNet8()


# ---------------------------------------------------------------------------
# Dataset adapters. Implemented with torchvision lazily so the module
# imports under CPU-only sandboxes (login node syntax-check is fine).
# ---------------------------------------------------------------------------
ARCH_BUILDERS = {
    "MNIST": lambda: build_lenet5(num_classes=10, in_channels=1),
    "FashionMNIST": lambda: build_lenet5(num_classes=10, in_channels=1),
    "CIFAR10": lambda: build_resnet8(num_classes=10),
}


def load_full_dataset(dataset: str, data_root: Path):
    """Return ``(train_xs, train_ys, test_xs, test_ys)`` as torch tensors.

    The shadow population is drawn from the *training* split of the same
    distribution; this matches the LiRA threat model where the adversary
    knows the data distribution but not the specific membership mask of
    the target.
    """
    import torch
    from torchvision import datasets, transforms

    data_root = Path(data_root)
    data_root.mkdir(parents=True, exist_ok=True)

    if dataset in ("MNIST", "FashionMNIST"):
        tfm = transforms.Compose([transforms.ToTensor()])
        cls = datasets.MNIST if dataset == "MNIST" else datasets.FashionMNIST
        tr = cls(root=str(data_root), train=True, download=True, transform=tfm)
        te = cls(root=str(data_root), train=False, download=True, transform=tfm)
    elif dataset == "CIFAR10":
        tfm = transforms.Compose([transforms.ToTensor()])
        tr = datasets.CIFAR10(root=str(data_root), train=True, download=True, transform=tfm)
        te = datasets.CIFAR10(root=str(data_root), train=False, download=True, transform=tfm)
    else:
        raise ValueError(f"unknown dataset {dataset!r}")

    def stack(ds):
        xs = torch.stack([ds[i][0] for i in range(len(ds))])
        ys = torch.tensor([ds[i][1] for i in range(len(ds))], dtype=torch.long)
        return xs, ys

    tr_x, tr_y = stack(tr)
    te_x, te_y = stack(te)
    return tr_x, tr_y, te_x, te_y


# ---------------------------------------------------------------------------
# Cache layout
# ---------------------------------------------------------------------------
# results/shadows/<dataset>_<seed>/
#   manifest.json                       <- {"dataset", "seed", "n_shadows",
#                                          "victim_size", "n_train_pool", ...}
#   masks.npy                           <- (n_shadows, n_train_pool) bool
#   shadow_{i:03d}.pt                   <- state_dict for shadow i
# ---------------------------------------------------------------------------
@dataclass
class ShadowBundle:
    """In-memory handle for a (dataset, seed)-keyed shadow population."""

    dataset: str
    seed: int
    n_shadows: int
    victim_size: int
    n_train_pool: int
    masks: np.ndarray         # (n_shadows, n_train_pool) bool
    ckpt_paths: List[Path]    # one per shadow
    cache_dir: Path
    cache_hit: bool


def cache_dir_for(shadow_cache_root: Path, dataset: str, seed: int) -> Path:
    return Path(shadow_cache_root) / f"{dataset}_{seed}"


def _manifest_path(cdir: Path) -> Path:
    return cdir / "manifest.json"


def load_shadow_bundle(
    shadow_cache_root: Path, dataset: str, seed: int
) -> Optional[ShadowBundle]:
    """Return cached bundle if present and consistent, else None."""
    cdir = cache_dir_for(shadow_cache_root, dataset, seed)
    mpath = _manifest_path(cdir)
    if not mpath.exists():
        return None
    with open(mpath) as f:
        manifest = json.load(f)
    masks_path = cdir / "masks.npy"
    if not masks_path.exists():
        return None
    masks = np.load(masks_path)
    n_shadows = int(manifest["n_shadows"])
    ckpts = [cdir / f"shadow_{i:03d}.pt" for i in range(n_shadows)]
    if not all(p.exists() for p in ckpts):
        return None
    return ShadowBundle(
        dataset=manifest["dataset"],
        seed=int(manifest["seed"]),
        n_shadows=n_shadows,
        victim_size=int(manifest["victim_size"]),
        n_train_pool=int(manifest["n_train_pool"]),
        masks=masks,
        ckpt_paths=ckpts,
        cache_dir=cdir,
        cache_hit=True,
    )


def _train_one_shadow(
    arch_factory,
    xs,
    ys,
    in_mask: np.ndarray,
    *,
    device: str,
    epochs: int,
    batch_size: int,
    lr: float,
) -> "torch.nn.Module":
    import torch
    from torch.utils.data import DataLoader, TensorDataset

    model = arch_factory().to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = torch.nn.CrossEntropyLoss()
    idx = np.where(in_mask)[0]
    sub_x = xs[idx]
    sub_y = ys[idx]
    loader = DataLoader(
        TensorDataset(sub_x, sub_y), batch_size=batch_size, shuffle=True
    )
    model.train()
    for _ in range(epochs):
        for bx, by in loader:
            bx = bx.to(device, non_blocking=True)
            by = by.to(device, non_blocking=True)
            opt.zero_grad(set_to_none=True)
            logits = model(bx)
            loss = loss_fn(logits, by)
            loss.backward()
            opt.step()
    model.eval()
    return model


def train_shadow_models(
    dataset: str,
    *,
    n_shadows: int = 64,
    victim_size: Optional[int] = None,
    seed: int = 0,
    shadow_cache_root: Path = Path("results/shadows"),
    data_root: Path = Path("data"),
    epochs: int = 20,
    batch_size: int = 128,
    lr: float = 1e-3,
    require_cuda: bool = True,
) -> ShadowBundle:
    """Train (or load from cache) ``n_shadows`` shadow models for ``dataset``.

    Returns a :class:`ShadowBundle` whose ``ckpt_paths`` point at the per-
    shadow state-dicts and whose ``masks`` is the (n_shadows, n_train_pool)
    boolean in/out membership matrix.

    The training pool is the full training split of ``dataset``; each shadow
    is trained on a uniformly-random subset of size ``victim_size`` (default
    ``N_train // 2``), with the complement serving as the per-shadow "out"
    set. The mask convention is ``masks[i, j] == True`` iff point ``j`` was
    in shadow ``i``'s training set.

    The cache key is ``(dataset, seed)``: shadows are *student-independent*,
    so the first MIA invocation for a given (dataset, seed) pays the full
    training cost and subsequent ones load instantly. This is the contract
    documented in the issue 21 Comments block.
    """
    import torch

    cached = load_shadow_bundle(shadow_cache_root, dataset, seed)
    if cached is not None and cached.n_shadows >= n_shadows:
        LOG.info(
            "[shadow_models] cache hit at %s (%d shadows >= requested %d)",
            cached.cache_dir, cached.n_shadows, n_shadows,
        )
        return cached

    if require_cuda and not torch.cuda.is_available():
        raise RuntimeError(
            "train_shadow_models requires CUDA (no shadow training on the "
            "login node). Set require_cuda=False only for tests."
        )

    arch_factory = ARCH_BUILDERS.get(dataset)
    if arch_factory is None:
        raise ValueError(
            f"no shadow architecture registered for dataset {dataset!r}"
        )

    device = "cuda" if torch.cuda.is_available() else "cpu"

    tr_x, tr_y, _, _ = load_full_dataset(dataset, data_root)
    n_pool = int(tr_x.shape[0])
    if victim_size is None:
        victim_size = n_pool // 2

    cdir = cache_dir_for(shadow_cache_root, dataset, seed)
    cdir.mkdir(parents=True, exist_ok=True)

    # Reproducible mask generation; one RNG stream per (dataset, seed).
    rng = np.random.default_rng(seed)
    masks = np.zeros((n_shadows, n_pool), dtype=bool)
    for i in range(n_shadows):
        chosen = rng.choice(n_pool, size=victim_size, replace=False)
        masks[i, chosen] = True
    np.save(cdir / "masks.npy", masks)

    ckpt_paths: List[Path] = []
    t0 = time.perf_counter()
    for i in range(n_shadows):
        # Per-shadow seed so the training trajectory is reproducible
        # independently of the mask draw.
        torch.manual_seed(seed * 100003 + i)
        model = _train_one_shadow(
            arch_factory,
            tr_x,
            tr_y,
            masks[i],
            device=device,
            epochs=epochs,
            batch_size=batch_size,
            lr=lr,
        )
        p = cdir / f"shadow_{i:03d}.pt"
        torch.save(model.state_dict(), p)
        ckpt_paths.append(p)
        LOG.info(
            "[shadow_models] trained shadow %d/%d in %.1fs (cum)",
            i + 1, n_shadows, time.perf_counter() - t0,
        )

    manifest = {
        "dataset": dataset,
        "seed": int(seed),
        "n_shadows": int(n_shadows),
        "victim_size": int(victim_size),
        "n_train_pool": int(n_pool),
        "epochs": int(epochs),
        "batch_size": int(batch_size),
        "lr": float(lr),
        "arch": "lenet5" if dataset in ("MNIST", "FashionMNIST") else "resnet8",
    }
    with open(_manifest_path(cdir), "w") as f:
        json.dump(manifest, f, indent=2)

    return ShadowBundle(
        dataset=dataset,
        seed=seed,
        n_shadows=n_shadows,
        victim_size=victim_size,
        n_train_pool=n_pool,
        masks=masks,
        ckpt_paths=ckpt_paths,
        cache_dir=cdir,
        cache_hit=False,
    )


def load_shadow_state_dict(path: Path):
    import torch

    return torch.load(str(path), map_location="cpu")


def instantiate_arch(dataset: str):
    """Convenience: build a fresh nn.Module of the dataset's shadow arch."""
    factory = ARCH_BUILDERS.get(dataset)
    if factory is None:
        raise ValueError(f"no shadow architecture registered for {dataset!r}")
    return factory()
