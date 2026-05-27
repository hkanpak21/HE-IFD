"""Evaluation helpers (test accuracy and OOD-class accuracy).

``accuracy_on`` is a verbatim port of notebook Section 0.3. ``ood_accuracy_on``
supports the M4 metric (accuracy on classes a client held zero local examples
of) flagged in the PRD; it is provided here so issue 005 can wire it without
re-touching this module, and is a thin restriction of the same accuracy pass.
"""
from __future__ import annotations

from typing import Optional, Sequence


def accuracy_on(model, X, y, bs: int = 512) -> float:
    """Top-1 accuracy of ``model`` on (X, y), batched. Verbatim from notebook.

    Handles CPU tensors by moving each batch to the model's device; tensors
    already on-device are used in place. Sets eval mode and runs under no_grad.
    """
    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.eval()
    n = X.shape[0]
    correct = 0
    with torch.no_grad():
        for i in range(0, n, bs):
            xb = X[i:i + bs].to(device) if X.device.type == "cpu" else X[i:i + bs]
            yb = y[i:i + bs].to(device) if y.device.type == "cpu" else y[i:i + bs]
            correct += (model(xb).argmax(1) == yb).sum().item()
    return correct / n


def ood_accuracy_on(
    model, X, y, ood_classes: Sequence[int], bs: int = 512
) -> Optional[float]:
    """Accuracy restricted to test samples whose label is in ``ood_classes``.

    M4 metric: per-client, ``ood_classes`` are the labels that client had zero
    local examples of. Returns None if no test sample falls in that set.
    """
    import torch

    if len(ood_classes) == 0:
        return None
    ood_set = torch.as_tensor(list(ood_classes))
    mask = torch.isin(y.cpu(), ood_set)
    if int(mask.sum()) == 0:
        return None
    return accuracy_on(model, X[mask], y[mask], bs=bs)
