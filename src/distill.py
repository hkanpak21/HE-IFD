"""Local bounded-trajectory distillation -> per-client cumulative displacement Δ.

This is the client-side compute. From the shared, Phase-0-aligned init θ₀, a
client runs a **bounded K-step** distillation trajectory, pulling its student
toward its own teacher via temperatured KL. The object it then encrypts and
uploads is the **cumulative trainable-parameter displacement**

        Δ_i = θ_i^(K) − θ₀

— a SINGLE parameter-set, not the K per-step deltas. The K-step trajectory is
merely *how* Δ_i is produced; collapsing the K steps into one Δ for transport is
valid precisely because the server's aggregation is linear (see ``aggregate``),
and the paper states this explicitly. Boundedness + shared θ₀ + Phase-0 pull are
what keep every Δ_i in one loss basin so the single linear combine lands inside it.

Ported from notebook Section 0.3 ``local_distill_trajectory``. The notebook
returned the *list* of K per-step deltas and summed them only inside
``server_aggregate``; here we return the cumulative Δ directly (their sum, i.e.
``θ_final − θ₀``), which is the PRD's stated interface and is numerically
identical to summing the per-step deltas. ``return_steps=True`` additionally
exposes the per-step list for the aggregation-coherence ablation (issue 006).
"""
from __future__ import annotations

from typing import Callable, Dict, List, Tuple, Union


def zero_like(params: Dict) -> Dict:
    import torch

    return {k: torch.zeros_like(v) for k, v in params.items()}


def params_diff(p1: Dict, p0: Dict) -> Dict:
    return {k: p1[k] - p0[k] for k in p1}


def local_distill_trajectory(
    teacher,
    init_params: Dict,
    make_model_fn: Callable,
    X,
    K_steps: int,
    lr: float,
    momentum: float,
    tau: float,
    bs: int,
    return_steps: bool = False,
) -> Union[Dict, Tuple[Dict, List[Dict]]]:
    """Run K KL-distillation steps from θ₀ and return the cumulative displacement.

    Parameters mirror the notebook. Per step: sample a minibatch with
    replacement, take teacher soft targets at temperature ``tau``, do one SGD
    step minimising ``KL(softmax_s/τ || softmax_t/τ) * τ²``.

    Returns
    -------
    delta : dict
        Cumulative displacement Δ = θ_final − θ₀ (per trainable tensor).
    (delta, step_deltas) : if ``return_steps`` — also the list of K per-step
        deltas (for the coherence ablation). ``sum_k step_deltas[k] == delta``.

    A zero-sample client returns Δ = 0 (it moves the aggregate not at all),
    matching the notebook's ``[zero_like(...) for _ in range(K_steps)]`` which
    sums to zero.
    """
    import torch
    import torch.nn.functional as F

    from .backbones import get_params

    device = "cuda" if torch.cuda.is_available() else "cpu"

    student = make_model_fn()
    student.load_state_dict(init_params)
    teacher.eval()
    X = X.to(device)
    n = X.shape[0]

    if n == 0:
        delta = zero_like(init_params)
        if return_steps:
            return delta, [zero_like(init_params) for _ in range(K_steps)]
        return delta

    opt = torch.optim.SGD(student.parameters(), lr=lr, momentum=momentum)
    step_deltas: List[Dict] = []
    for _ in range(K_steps):
        idx = torch.randint(0, n, (min(bs, n),), device=device)
        xb = X[idx]
        with torch.no_grad():
            t_logits = teacher(xb)
        prev = get_params(student)
        opt.zero_grad()
        s_logits = student(xb)
        loss = F.kl_div(
            F.log_softmax(s_logits / tau, dim=1),
            F.softmax(t_logits / tau, dim=1),
            reduction="batchmean",
        ) * (tau ** 2)
        loss.backward()
        opt.step()
        if return_steps:
            step_deltas.append(params_diff(get_params(student), prev))

    # Cumulative displacement Δ = θ_final − θ₀ (the object that is encrypted).
    final = get_params(student)
    delta = params_diff(final, init_params)
    if return_steps:
        return delta, step_deltas
    return delta


def distill_all_clients(
    teachers: List,
    init_params: Dict,
    make_model_fn: Callable,
    client_X_list: List,
    K_steps: int,
    lr: float,
    momentum: float,
    tau: float,
    bs: int,
) -> List[Dict]:
    """Run the bounded trajectory for every client; return the list of Δ_i.

    Each Δ_i is what client i would encrypt under the multiparty CKKS key. The
    server never sees the trajectory, only Δ_i (here, the plaintext simulation
    of it).
    """
    deltas: List[Dict] = []
    for i in range(len(teachers)):
        deltas.append(
            local_distill_trajectory(
                teachers[i], init_params, make_model_fn,
                client_X_list[i], K_steps, lr, momentum, tau, bs,
            )
        )
    return deltas
