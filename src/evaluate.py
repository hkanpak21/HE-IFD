"""Evaluation helpers (test accuracy, OOD-class accuracy, incentive gap).

``accuracy_on`` is a verbatim port of notebook Section 0.3. ``ood_accuracy_on``
supports the M4 metric (accuracy on classes a client held zero local examples
of) flagged in the PRD; it is provided here so issue 005 can wire it without
re-touching this module, and is a thin restriction of the same accuracy pass.

Issue 005 adds the two per-client reporting quantities that justify the
participation incentive and the OOD value-proposition the TDSC reviewers said
were unsupported:

  * ``per_client_gap`` — M3: acc(final_student, D_i) − acc(teacher_i, D_i) for
    each client i. Positive ⇒ the federation helped client i on its own data.
  * ``ood_accuracy`` — M4: per-client accuracy of the final student on TEST
    examples drawn from classes client i held ZERO local examples of (the
    out-of-distribution classes). Vacuous (all-None) when every client saw every
    class — e.g. at α=1.0.

Both reuse the already-trained teachers and the per-client partition tensors
already materialised in ``protocol.run_cell``; they retrain nothing.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence


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


def ood_classes_for_client(per_class_counts: Sequence[int]) -> List[int]:
    """Classes a client held ZERO local examples of, from its per-class counts.

    ``per_class_counts[c]`` is client i's local sample count for class c (a row
    of ``data.per_client_per_class_counts``). The OOD classes for M4 are exactly
    the indices with a count of 0. At α=1.0 every client holds every class, so
    this is empty and M4 is vacuous for that client.
    """
    return [c for c, n in enumerate(per_class_counts) if int(n) == 0]


def per_client_gap(
    final_student,
    teachers: Sequence,
    client_X_list: Sequence,
    client_y_list: Sequence,
    bs: int = 512,
) -> Dict:
    """M3 — per-client teacher-vs-aggregate gap on each client's own data D_i.

    For each client i computes ``acc(final_student, D_i) − acc(teacher_i, D_i)``
    where ``D_i = (client_X_list[i], client_y_list[i])`` is client i's local
    (in-distribution) training shard — the same tensors already partitioned in
    ``run_cell``. A positive gap means the released global student outperforms
    that client's own teacher on its own distribution, i.e. the federation
    helped client i. Reuses the already-trained ``teachers``; trains nothing.

    Returns a summary dict::

        {
          "student_acc":   [acc(final_student, D_i)         for i],  # None if |D_i|=0
          "teacher_acc":   [acc(teacher_i, D_i)             for i],  # None if |D_i|=0
          "gap":           [student_acc_i − teacher_acc_i   for i],  # None if |D_i|=0
          "mean_gap":      mean over clients with |D_i|>0 (None if none),
          "n_clients_helped": #clients with gap > 0  (ignores empty/None clients),
          "n_clients_evaluated": #clients with |D_i|>0,
        }
    """
    student_acc: List[Optional[float]] = []
    teacher_acc: List[Optional[float]] = []
    gap: List[Optional[float]] = []
    for i in range(len(client_X_list)):
        Xi, yi = client_X_list[i], client_y_list[i]
        if int(Xi.shape[0]) == 0:
            student_acc.append(None)
            teacher_acc.append(None)
            gap.append(None)
            continue
        s = accuracy_on(final_student, Xi, yi, bs=bs)
        t = accuracy_on(teachers[i], Xi, yi, bs=bs)
        student_acc.append(float(s))
        teacher_acc.append(float(t))
        gap.append(float(s - t))
    valid = [g for g in gap if g is not None]
    return {
        "student_acc": student_acc,
        "teacher_acc": teacher_acc,
        "gap": gap,
        "mean_gap": float(sum(valid) / len(valid)) if valid else None,
        "n_clients_helped": int(sum(1 for g in valid if g > 0)),
        "n_clients_evaluated": len(valid),
    }


def ood_accuracy(
    final_student,
    X_test,
    y_test,
    per_client_per_class: Sequence[Sequence[int]],
    bs: int = 512,
) -> Dict:
    """M4 — per-client OOD-class accuracy of the final student on the test set.

    For each client i, restricts the test set to classes client i held ZERO
    local examples of (``ood_classes_for_client`` of its per-class row) and
    measures the final student's accuracy there. This is the "averaged all-label
    student handles samples the local teacher never saw" value-prop.

    ``per_client_per_class`` is the ``(N, num_classes)`` count matrix already in
    the CellResult (``res.per_client_per_class``). A client with no OOD classes
    (saw every class — e.g. every client at α=1.0) yields ``None`` for that
    client; if every client is None the metric is vacuous and ``mean`` is None.

    Returns::

        {
          "per_client": [ood_acc_i or None for i],
          "ood_classes": [[classes client i never saw] for i],
          "mean": mean over clients with a non-None ood_acc (None if vacuous),
          "n_clients_evaluated": #clients with a non-None ood_acc,
        }
    """
    per_client: List[Optional[float]] = []
    ood_classes: List[List[int]] = []
    for i in range(len(per_client_per_class)):
        classes = ood_classes_for_client(per_client_per_class[i])
        ood_classes.append(classes)
        per_client.append(ood_accuracy_on(final_student, X_test, y_test, classes, bs=bs))
    valid = [a for a in per_client if a is not None]
    return {
        "per_client": per_client,
        "ood_classes": ood_classes,
        "mean": float(sum(valid) / len(valid)) if valid else None,
        "n_clients_evaluated": len(valid),
    }
