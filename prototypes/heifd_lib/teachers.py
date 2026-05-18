"""
Per-client teacher training for HE-IFD.

Architecture choices (locked here to keep the smoke deterministic):
    * MNIST, FashionMNIST  -> LeNet-5 (28x28 grayscale, ~62k params).
    * CIFAR-10, CIFAR-100  -> ResNet-8 (3-block ResNet variant, ~78k params).
    * SVHN                 -> ResNet-8 on 32x32 RGB (same as CIFAR-10).

Plaintext SGD only. No DP-SGD on the headline path (epsilon-variant lives in
a separate cell). Checkpoints land in
    results/teachers_v2/<dataset>_a<alpha>_s<seed>/client_<i>.pt
and are skipped if already present (resume support).
"""
from __future__ import annotations

import os
from typing import List, Sequence

import numpy as np


# --------------------------------------------------------------------------
# Models
# --------------------------------------------------------------------------


def _build_lenet5(num_classes: int = 10):
    import torch.nn as nn

    return nn.Sequential(
        nn.Conv2d(1, 6, kernel_size=5, padding=2),
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


def _build_resnet8(num_classes: int = 10):
    """A small ResNet (3 stages, 1 block each) for CIFAR-10 / SVHN."""
    import torch.nn as nn

    class BasicBlock(nn.Module):
        def __init__(self, in_ch, out_ch, stride):
            super().__init__()
            self.conv1 = nn.Conv2d(in_ch, out_ch, 3, stride, 1, bias=False)
            self.bn1 = nn.BatchNorm2d(out_ch)
            self.conv2 = nn.Conv2d(out_ch, out_ch, 3, 1, 1, bias=False)
            self.bn2 = nn.BatchNorm2d(out_ch)
            self.relu = nn.ReLU(inplace=True)
            self.shortcut = nn.Sequential()
            if stride != 1 or in_ch != out_ch:
                self.shortcut = nn.Sequential(
                    nn.Conv2d(in_ch, out_ch, 1, stride, bias=False),
                    nn.BatchNorm2d(out_ch),
                )

        def forward(self, x):
            out = self.relu(self.bn1(self.conv1(x)))
            out = self.bn2(self.conv2(out))
            out = out + self.shortcut(x)
            return self.relu(out)

    class ResNet8(nn.Module):
        def __init__(self):
            super().__init__()
            self.stem = nn.Sequential(
                nn.Conv2d(3, 16, 3, 1, 1, bias=False),
                nn.BatchNorm2d(16),
                nn.ReLU(inplace=True),
            )
            self.layer1 = BasicBlock(16, 16, 1)
            self.layer2 = BasicBlock(16, 32, 2)
            self.layer3 = BasicBlock(32, 64, 2)
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


def build_model(dataset: str, num_classes: int):
    """Return an untrained teacher/student model for the dataset family."""
    d = dataset.lower().replace("-", "")
    if d in {"mnist", "fashionmnist"}:
        return _build_lenet5(num_classes=num_classes)
    if d in {"cifar10", "cifar100", "svhn"}:
        return _build_resnet8(num_classes=num_classes)
    raise ValueError(f"Unknown dataset family: {dataset}")


# --------------------------------------------------------------------------
# Training / checkpointing
# --------------------------------------------------------------------------


def teacher_ckpt_path(dataset: str, alpha: float, seed: int, client_id: int,
                      root: str = "results/teachers_v2") -> str:
    return f"{root}/{dataset}_a{alpha}_s{seed}/client_{client_id}.pt"


def train_one_teacher(model, train_loader, device, epochs: int, lr: float = 1e-2,
                       momentum: float = 0.9, weight_decay: float = 5e-4):
    """Plaintext SGD with cosine schedule. Mutates `model` in place."""
    import torch
    import torch.nn as nn
    import torch.optim as optim

    model = model.to(device)
    opt = optim.SGD(model.parameters(), lr=lr, momentum=momentum,
                    weight_decay=weight_decay)
    sched = optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    crit = nn.CrossEntropyLoss()
    model.train()
    for _ in range(epochs):
        for xb, yb in train_loader:
            xb = xb.to(device, non_blocking=True)
            yb = yb.to(device, non_blocking=True)
            opt.zero_grad()
            logits = model(xb)
            loss = crit(logits, yb)
            loss.backward()
            opt.step()
        sched.step()
    return model


def train_or_load_teachers(
    dataset: str,
    alpha: float,
    seed: int,
    client_indices: Sequence[Sequence[int]],
    train_dataset,
    num_classes: int,
    epochs: int,
    batch_size: int = 64,
    device: str = "cuda",
    ckpt_root: str = "results/teachers_v2",
) -> List[str]:
    """
    For each client: load checkpoint if present, else train and save.

    Returns the list of checkpoint paths so the caller can reload selectively
    (one teacher at a time keeps peak GPU memory bounded).
    """
    import torch
    from torch.utils.data import DataLoader, Subset

    paths: List[str] = []
    for cid, idx in enumerate(client_indices):
        path = teacher_ckpt_path(dataset, alpha, seed, cid, root=ckpt_root)
        paths.append(path)
        if os.path.exists(path):
            print(f"[teachers] client {cid}: checkpoint exists, skipping ({path})")
            continue

        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.manual_seed(seed + cid)  # deterministic per-client init
        model = build_model(dataset, num_classes=num_classes)
        loader = DataLoader(
            Subset(train_dataset, list(idx)),
            batch_size=batch_size,
            shuffle=True,
            num_workers=2,
            pin_memory=(device == "cuda"),
            drop_last=False,
        )
        print(f"[teachers] client {cid}: training {len(idx)} samples, {epochs} epochs")
        train_one_teacher(model, loader, device=device, epochs=epochs)
        torch.save(model.state_dict(), path)
        print(f"[teachers] client {cid}: saved -> {path}")
    return paths


def load_teacher(dataset: str, num_classes: int, ckpt_path: str, device: str = "cuda"):
    import torch

    model = build_model(dataset, num_classes=num_classes)
    state = torch.load(ckpt_path, map_location=device)
    model.load_state_dict(state)
    model.to(device).eval()
    return model


# --------------------------------------------------------------------------
# Probe-pass: produce a (|P|, C) logit tensor
# --------------------------------------------------------------------------


def teacher_logits_on_probe(
    teacher, probe_dataset, device: str = "cuda", batch_size: int = 256,
) -> np.ndarray:
    """Single forward pass over the probe; returns a numpy (|P|, C) array."""
    import torch
    from torch.utils.data import DataLoader

    loader = DataLoader(probe_dataset, batch_size=batch_size, shuffle=False,
                        num_workers=2, pin_memory=(device == "cuda"))
    teacher.eval()
    all_logits = []
    with torch.no_grad():
        for xb, _ in loader:
            xb = xb.to(device, non_blocking=True)
            out = teacher(xb).detach().cpu().numpy().astype(np.float64)
            all_logits.append(out)
    return np.concatenate(all_logits, axis=0)


def teacher_max_softmax_mean(logits: np.ndarray) -> float:
    """
    alpha_i = E[max softmax(T_i(x))] over the probe. Used as the plaintext
    confidence weight that gets encrypted into the beta-aggregation.
    """
    x = logits - logits.max(axis=1, keepdims=True)
    expx = np.exp(x)
    sm = expx / expx.sum(axis=1, keepdims=True)
    return float(sm.max(axis=1).mean())
