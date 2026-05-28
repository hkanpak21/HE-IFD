"""KD-dynamics diagnostics (issue 013) — empirical-evidence anchor for the
basin-cancellation hypothesis behind the θ₀≥final phenomenon (issue 008).

This module is **strictly opt-in**: every helper is only called by the
distillation/protocol path when ``diagnose=True``. When ``diagnose=False``
(the default everywhere), nothing in this file runs and the existing
distill→aggregate→evaluate pipeline is byte-identical to its pre-issue-013
behaviour. We therefore never branch on diagnose state inside the hot loop —
all measurements happen *outside* the gradient-update path, on params that
have already been computed.

The four diagnostics requested by issue 013:

1. **Teacher logit entropy on the augmented probe** (mean + std per client).
   At α=0.05 expect near-zero (peaky teachers ⇒ near-one-hot KL targets ⇒
   the basin-cancellation argument).
2. **Per-step ‖Δᵢ⁽ᵏ⁾‖₂** for k = 0…K (the trajectory's L2-magnitude profile)
   AND cumulative ‖Δᵢ‖₂ at end (=‖θ_K − θ₀‖₂).
3. **Pairwise cosine matrix `cosine(Δᵢ, Δⱼ)`** for all i ≠ j (N×N, JSON-
   serializable). Near-zero or negative entries mean clients' displacements
   point in opposing directions — cancellation under sample-weighted summation.
4. **Per-class accuracy of θ₀ vs the final aggregated student** on the test
   set (which classes does distillation actually move?).

All outputs are plain ``float`` / ``list`` / ``dict`` — never tensors —
so they drop straight into the per-cell JSON via ``json.dumps``.
"""
from __future__ import annotations

from typing import Callable, Dict, List, Optional, Sequence


# ---------------------------------------------------------------------------
# Internal: turn a state_dict-style parameter dict into one flat torch vector.
# Order is sorted-by-key so two parameter dicts produce vectors with the same
# coordinate semantics (a precondition for cosine / L2-distance comparisons).
# ---------------------------------------------------------------------------
def _flat_param_vector(params: Dict):
    """Concatenate sorted-by-key values into a single 1-D float tensor on CPU.

    Detached + cloned + moved to CPU so subsequent helpers can store the vector
    without holding GPU memory or interfering with the trainer's autograd state.
    """
    import torch

    keys = sorted(params.keys())
    pieces = [params[k].detach().reshape(-1).float().cpu() for k in keys]
    if not pieces:
        return torch.empty(0)
    return torch.cat(pieces, dim=0)


def _l2_norm(params: Dict) -> float:
    """‖vec(params)‖₂ as a plain float."""
    v = _flat_param_vector(params)
    return float(v.norm(p=2).item()) if v.numel() > 0 else 0.0


# ---------------------------------------------------------------------------
# 1. Teacher logit entropy on the augmented probe (per client mean + std).
# ---------------------------------------------------------------------------
def teacher_logit_entropy(
    teacher,
    X,
    bs: int = 512,
) -> Dict[str, float]:
    """Per-sample softmax entropy of teacher logits on ``X``, summarised.

    Entropy is computed in nats: ``H(p) = -Σ_c p_c log p_c``, with the standard
    log_softmax → −exp(log_softmax)·log_softmax trick (numerically stable on
    near-one-hot distributions where naive softmax+log underflows).

    A zero-sample input returns ``mean=std=count=0.0`` so the caller does not
    need to guard. Otherwise returns plain floats fit for JSON.
    """
    import torch
    import torch.nn.functional as F

    if X.shape[0] == 0:
        return {"mean": 0.0, "std": 0.0, "count": 0}

    device = "cuda" if torch.cuda.is_available() else "cpu"
    teacher.eval()
    entropies: List[float] = []
    with torch.no_grad():
        for i in range(0, X.shape[0], bs):
            xb = X[i:i + bs].to(device) if X.device.type == "cpu" else X[i:i + bs]
            logits = teacher(xb)
            log_p = F.log_softmax(logits, dim=1)
            p = log_p.exp()
            H = -(p * log_p).sum(dim=1)        # (batch,) nats
            entropies.extend(H.detach().cpu().tolist())
    import statistics
    mean = float(sum(entropies) / len(entropies))
    std = float(statistics.pstdev(entropies)) if len(entropies) > 1 else 0.0
    return {"mean": mean, "std": std, "count": int(len(entropies))}


def teacher_entropy_per_client(
    teachers: Sequence,
    client_X_list: Sequence,
    bs: int = 512,
) -> List[Dict[str, float]]:
    """Apply ``teacher_logit_entropy`` to each (teacher_i, D_i) pair.

    Returns a length-N list of ``{mean, std, count}`` dicts. JSON-serialisable.
    """
    out: List[Dict[str, float]] = []
    for i in range(len(teachers)):
        out.append(teacher_logit_entropy(teachers[i], client_X_list[i], bs=bs))
    return out


# ---------------------------------------------------------------------------
# 2. Per-step and cumulative ‖Δᵢ⁽ᵏ⁾‖₂ for a single client's trajectory.
# ---------------------------------------------------------------------------
def per_step_delta_norms(step_deltas: Sequence[Dict]) -> List[float]:
    """L2 norm of each per-step delta in a trajectory: ``[‖d^(k)‖₂ for k]``.

    ``step_deltas[k]`` is what ``local_distill_trajectory(..., return_steps=
    True)`` already produces — a parameter-dict whose values are
    ``params_after_step_k − params_before_step_k``. Returned list is one float
    per step, JSON-serialisable.
    """
    return [_l2_norm(d) for d in step_deltas]


def cumulative_delta_norm(delta: Dict) -> float:
    """‖Δᵢ‖₂ = ‖θ_K − θ₀‖₂, the cumulative-displacement magnitude (one float)."""
    return _l2_norm(delta)


# ---------------------------------------------------------------------------
# 3. Pairwise cosine matrix `cos(Δᵢ, Δⱼ)` over all clients (N x N).
# ---------------------------------------------------------------------------
def pairwise_cosine_matrix(deltas: Sequence[Dict]) -> List[List[float]]:
    """Symmetric N×N matrix of cosine similarities between client displacements.

    Each Δᵢ is flattened over its sorted-by-key parameter values, divided by
    its L2 norm (zero-norm rows yield zeros), and dot-producted with every
    other client's normalised vector. Diagonal is 1.0 by construction; the
    interesting cells are i ≠ j. Returned as a list-of-lists of plain floats.

    Near-zero / negative off-diagonal entries are the empirical signature of
    the basin-cancellation hypothesis: clients' bounded trajectories point in
    opposing directions, so the sample-weighted sum partially cancels.
    """
    import torch

    n = len(deltas)
    flats = [_flat_param_vector(d) for d in deltas]
    norms = [float(v.norm(p=2).item()) if v.numel() > 0 else 0.0 for v in flats]
    # Normalise (guard zero-norm clients — return zero rows for them).
    units = []
    for v, nrm in zip(flats, norms):
        if nrm > 0.0 and v.numel() > 0:
            units.append(v / nrm)
        else:
            units.append(v)
    M: List[List[float]] = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j and norms[i] > 0.0:
                M[i][j] = 1.0
            elif norms[i] == 0.0 or norms[j] == 0.0:
                M[i][j] = 0.0
            else:
                M[i][j] = float(torch.dot(units[i], units[j]).item())
    return M


# ---------------------------------------------------------------------------
# 4. Per-class test accuracy of two models (θ₀ vs final aggregated student).
# ---------------------------------------------------------------------------
def per_class_accuracy(
    model,
    X_test,
    y_test,
    num_classes: int,
    bs: int = 512,
) -> List[Optional[float]]:
    """Per-class top-1 accuracy on the test set.

    Returns a length-``num_classes`` list of floats (``None`` for classes with
    zero test samples — defensive; standard test sets are balanced so this
    branch rarely fires). Reuses the same eval idiom as ``evaluate.accuracy_on``
    (batched, no_grad, eval mode) but partitioned by ground-truth label.
    """
    import torch

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.eval()
    per_class_correct = [0] * num_classes
    per_class_total = [0] * num_classes
    with torch.no_grad():
        for i in range(0, X_test.shape[0], bs):
            xb = X_test[i:i + bs].to(device) if X_test.device.type == "cpu" else X_test[i:i + bs]
            yb = y_test[i:i + bs].to(device) if y_test.device.type == "cpu" else y_test[i:i + bs]
            preds = model(xb).argmax(1)
            correct = (preds == yb).to(torch.int64)
            for c in range(num_classes):
                mask = (yb == c)
                per_class_total[c] += int(mask.sum().item())
                per_class_correct[c] += int(correct[mask].sum().item())
    out: List[Optional[float]] = []
    for c in range(num_classes):
        if per_class_total[c] == 0:
            out.append(None)
        else:
            out.append(float(per_class_correct[c] / per_class_total[c]))
    return out


def per_class_accuracy_pair(
    make_model_fn: Callable,
    theta0_params: Dict,
    final_params: Dict,
    X_test,
    y_test,
    num_classes: int,
    bs: int = 512,
) -> Dict[str, List[Optional[float]]]:
    """Materialise both models from their state-dicts and return their
    per-class accuracies side-by-side. Also returns the per-class delta
    ``final − theta0`` (or ``None`` where either side is ``None``).

    Output schema (JSON-serialisable)::

        {
          "theta0":      [acc_0, ..., acc_{C-1}],   # None for empty class
          "final":       [acc_0, ..., acc_{C-1}],
          "delta":       [final_c - theta0_c, ...], # None where either side None
        }
    """
    m0 = make_model_fn()
    m0.load_state_dict(theta0_params)
    acc0 = per_class_accuracy(m0, X_test, y_test, num_classes, bs=bs)
    m1 = make_model_fn()
    m1.load_state_dict(final_params)
    acc1 = per_class_accuracy(m1, X_test, y_test, num_classes, bs=bs)
    delta = []
    for a0, a1 in zip(acc0, acc1):
        if a0 is None or a1 is None:
            delta.append(None)
        else:
            delta.append(float(a1 - a0))
    return {"theta0": acc0, "final": acc1, "delta": delta}


# ---------------------------------------------------------------------------
# Composite: assemble a single diagnostics dict for the per-cell JSON.
# ---------------------------------------------------------------------------
def build_diagnostics(
    *,
    teachers,
    align_X,
    align_y,
    client_X_list,
    deltas,
    step_deltas_per_client,
    theta0_params,
    final_params,
    make_model_fn,
    X_test,
    y_test,
    num_classes: int,
    bs: int = 512,
) -> Dict:
    """Assemble the issue-013 diagnostics dict (JSON-serialisable).

    Parameters mirror objects the protocol already has in memory at the end of
    a ``diagnose=True`` ``run_cell``; nothing here trains/decrypts anything.

    Schema::

        {
          "teacher_entropy_on_align_probe":  {"mean", "std", "count"},
          "teacher_entropy_per_client":      [ {"mean","std","count"}_i ],
          "delta_norms": {
              "cumulative":      [‖Δᵢ‖₂ for i],
              "per_step":        [[‖d^(k)‖₂ for k] for i],   # may be []
              "mean_step_norm":  [ mean_k ‖d^(k)‖₂ for i ],  # convenience
          },
          "pairwise_cosine":      [[N×N]],
          "per_class_test_acc":   {"theta0":[...], "final":[...], "delta":[...]},
        }

    ``align_X`` may be ``None`` (e.g. ``method=no_phase0``) — entropy on the
    aligned probe is then reported as a zero-count entry. ``step_deltas_per_
    client`` may be ``[None, ...]`` if a client returned no trajectory (zero
    samples); its per-step row is ``[]`` and its mean is ``0.0``.
    """
    # (1) Teacher entropy on the alignment probe (if one exists). We use
    #     teacher 0 as a representative — entropy on the *same* labelled input
    #     across teachers correlates trivially with class balance, not what
    #     issue 013 asks for. The per-client entropy below uses each client's
    #     own data D_i, which is the relevant quantity.
    if align_X is not None and align_X.shape[0] > 0 and len(teachers) > 0:
        ent_probe = teacher_logit_entropy(teachers[0], align_X, bs=bs)
    else:
        ent_probe = {"mean": 0.0, "std": 0.0, "count": 0}

    # (2) Per-client teacher entropy on D_i.
    ent_per_client = teacher_entropy_per_client(teachers, client_X_list, bs=bs)

    # (3) Δ norms — cumulative + per-step.
    cum_norms = [cumulative_delta_norm(d) for d in deltas]
    per_step: List[List[float]] = []
    mean_step: List[float] = []
    for sd in step_deltas_per_client:
        if sd is None or len(sd) == 0:
            per_step.append([])
            mean_step.append(0.0)
        else:
            norms = per_step_delta_norms(sd)
            per_step.append(norms)
            mean_step.append(float(sum(norms) / len(norms)) if norms else 0.0)

    # (4) Pairwise cosine over cumulative Δ.
    cos_mat = pairwise_cosine_matrix(deltas)

    # (5) Per-class accuracy θ₀ vs final.
    pc = per_class_accuracy_pair(
        make_model_fn, theta0_params, final_params, X_test, y_test,
        num_classes, bs=bs,
    )

    return {
        "teacher_entropy_on_align_probe": ent_probe,
        "teacher_entropy_per_client": ent_per_client,
        "delta_norms": {
            "cumulative": cum_norms,
            "per_step": per_step,
            "mean_step_norm": mean_step,
        },
        "pairwise_cosine": cos_mat,
        "per_class_test_acc": pc,
    }
