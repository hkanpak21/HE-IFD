"""
Evaluation utilities: decrypt the final student bias, evaluate accuracy on
the test set, average teacher accuracy, optional oracle (centralised) baseline.
"""
from __future__ import annotations

import os
from typing import List

import numpy as np


def eval_model_accuracy(model, test_dataset, device: str = "cuda",
                        batch_size: int = 512) -> float:
    """Top-1 accuracy on the supplied test_dataset."""
    import torch
    from torch.utils.data import DataLoader

    model = model.to(device).eval()
    loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False,
                        num_workers=2, pin_memory=(device == "cuda"))
    correct, total = 0, 0
    with torch.no_grad():
        for xb, yb in loader:
            xb = xb.to(device, non_blocking=True)
            yb = yb.to(device, non_blocking=True)
            pred = model(xb).argmax(dim=1)
            correct += int((pred == yb).sum().item())
            total += int(yb.numel())
    return correct / max(total, 1)


def mean_teacher_accuracy(teacher_paths: List[str], dataset: str, num_classes: int,
                           test_dataset, device: str = "cuda") -> float:
    """Average top-1 test accuracy across the N teacher checkpoints."""
    from .teachers import load_teacher

    accs = []
    for p in teacher_paths:
        t = load_teacher(dataset, num_classes, p, device=device)
        accs.append(eval_model_accuracy(t, test_dataset, device=device))
    return float(np.mean(accs)) if accs else 0.0


def oracle_accuracy(
    dataset: str,
    seed: int,
    train_dataset,
    test_dataset,
    num_classes: int,
    epochs: int = 30,
    device: str = "cuda",
    cache_root: str = "results/oracles",
) -> float:
    """
    Centralised baseline: train one model on the pooled training set.
    Cached at results/oracles/<dataset>_s<seed>.pt to amortise across cells.
    """
    import torch
    from torch.utils.data import DataLoader

    from .teachers import build_model, train_one_teacher

    cache_path = os.path.join(cache_root, f"{dataset}_s{seed}.pt")
    model = build_model(dataset, num_classes=num_classes)
    if os.path.exists(cache_path):
        state = torch.load(cache_path, map_location=device)
        model.load_state_dict(state)
    else:
        os.makedirs(cache_root, exist_ok=True)
        torch.manual_seed(seed)
        loader = DataLoader(train_dataset, batch_size=128, shuffle=True,
                            num_workers=2, pin_memory=(device == "cuda"))
        train_one_teacher(model, loader, device=device, epochs=epochs)
        torch.save(model.state_dict(), cache_path)
    return eval_model_accuracy(model, test_dataset, device=device)


def apply_bias_update_to_student(student, delta: np.ndarray):
    """
    After Phase 4 decrypt we receive a (C,) vector that perturbs the final
    fully-connected layer's bias. Locate the last Linear module and apply
    `delta` to its bias term in place. This is the smoke-version
    interpretation of <theta_E> = <theta_0*> + <Delta>; the production
    target is to slot the full parameter vector into the encrypted
    accumulator.
    """
    import torch
    import torch.nn as nn

    last_linear = None
    for m in student.modules():
        if isinstance(m, nn.Linear):
            last_linear = m
    if last_linear is None:
        raise RuntimeError("No nn.Linear found in student; cannot apply bias delta.")
    with torch.no_grad():
        last_linear.bias.add_(torch.tensor(delta, dtype=last_linear.bias.dtype,
                                            device=last_linear.bias.device))
    return student
