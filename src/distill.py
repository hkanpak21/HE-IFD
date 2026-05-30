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


def _make_optimizer(params, optimizer: str, lr: float, momentum: float):
    """Build the client-side torch optimizer for the K-step distillation.

    The ``"sgd"`` branch is BYTE-IDENTICAL to the historical inline
    ``torch.optim.SGD(student.parameters(), lr=lr, momentum=momentum)`` so the
    default trajectory (hence every Δ_i) is bit-for-bit unchanged. The other
    names are the client-optimizer axis (issue: TIER-1 aggregation study, Axis
    A). torch is imported lazily to match the file's no-top-level-torch style.
    """
    import torch

    if optimizer == "sgd":
        return torch.optim.SGD(params, lr=lr, momentum=momentum)
    if optimizer == "sgd_momentum":
        return torch.optim.SGD(params, lr=lr, momentum=0.9)
    if optimizer == "nesterov":
        return torch.optim.SGD(params, lr=lr, momentum=0.9, nesterov=True)
    if optimizer == "adam":
        return torch.optim.Adam(params, lr=lr)
    if optimizer == "adamw":
        return torch.optim.AdamW(params, lr=lr)
    if optimizer == "rmsprop":
        return torch.optim.RMSprop(params, lr=lr)
    if optimizer == "adagrad":
        return torch.optim.Adagrad(params, lr=lr)
    if optimizer == "lamb":
        return _build_lamb(params, lr=lr)
    raise ValueError(f"unknown optimizer {optimizer!r}")


def _build_lamb(params, lr: float, betas=(0.9, 0.999), eps: float = 1e-6,
                weight_decay: float = 0.0):
    """Minimal, self-contained LAMB optimizer (You et al. 2020).

    Standard LAMB: maintain Adam first/second moments → bias-correct → form the
    Adam direction ``r = m̂/(√v̂ + ε) + wd·θ`` → compute the layerwise trust
    ratio ``φ(‖θ‖)/‖r‖`` (here φ = identity, clamped, and 0 when EITHER norm is
    0, which falls back to a plain scaled step) → ``θ -= lr · trust · r``.

    Defined as a closure so the class subclasses ``torch.optim.Optimizer``
    without forcing a top-level torch import (matching this file's lazy style).
    """
    import torch

    class Lamb(torch.optim.Optimizer):
        def __init__(self, params, lr, betas, eps, weight_decay):
            defaults = dict(lr=lr, betas=betas, eps=eps,
                            weight_decay=weight_decay)
            super().__init__(params, defaults)

        @torch.no_grad()
        def step(self, closure=None):
            loss = None
            if closure is not None:
                with torch.enable_grad():
                    loss = closure()
            for group in self.param_groups:
                b1, b2 = group["betas"]
                lr_, eps_, wd_ = group["lr"], group["eps"], group["weight_decay"]
                for p in group["params"]:
                    if p.grad is None:
                        continue
                    grad = p.grad
                    state = self.state[p]
                    if len(state) == 0:
                        state["step"] = 0
                        state["exp_avg"] = torch.zeros_like(p)
                        state["exp_avg_sq"] = torch.zeros_like(p)
                    m, v = state["exp_avg"], state["exp_avg_sq"]
                    state["step"] += 1
                    t = state["step"]
                    # Adam moments.
                    m.mul_(b1).add_(grad, alpha=1 - b1)
                    v.mul_(b2).addcmul_(grad, grad, value=1 - b2)
                    # Bias correction.
                    m_hat = m / (1 - b1 ** t)
                    v_hat = v / (1 - b2 ** t)
                    # Adam direction + decoupled weight decay.
                    r = m_hat / (v_hat.sqrt() + eps_)
                    if wd_ != 0:
                        r = r + wd_ * p
                    # Layerwise trust ratio φ(‖θ‖)/‖r‖, 0 when EITHER norm is 0
                    # (the standard guard — no step for a zero param or zero
                    # direction).
                    w_norm = float(p.norm())
                    r_norm = float(r.norm())
                    trust = w_norm / r_norm if (w_norm > 0 and r_norm > 0) else 0.0
                    p.add_(r, alpha=-lr_ * trust)
            return loss

    return Lamb(params, lr=lr, betas=betas, eps=eps, weight_decay=weight_decay)


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
    optimizer: str = "sgd",
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

    opt = _make_optimizer(student.parameters(), optimizer, lr, momentum)
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
    diagnose: bool = False,
    optimizer: str = "sgd",
) -> Union[List[Dict], Tuple[List[Dict], List[List[Dict]]]]:
    """Run the bounded trajectory for every client; return the list of Δ_i.

    Each Δ_i is what client i would encrypt under the multiparty CKKS key. The
    server never sees the trajectory, only Δ_i (here, the plaintext simulation
    of it).

    Parameters
    ----------
    diagnose : bool
        If ``False`` (default) — return only the list of cumulative Δ_i;
        the per-client call sets ``return_steps=False`` and the function is
        BYTE-IDENTICAL to its pre-issue-013 behaviour. If ``True`` —
        additionally collect per-step deltas via ``return_steps=True`` and
        return ``(deltas, step_deltas_per_client)`` so ``src.diagnostics`` can
        compute per-step ‖Δ⁽ᵏ⁾‖₂. The diagnostic branch is opt-in and never
        runs in normal sweeps.
    """
    if not diagnose:
        # Default sweep path — no semantic change vs. pre-issue-013. With the
        # default optimizer="sgd" this remains byte-identical to that behaviour.
        deltas: List[Dict] = []
        for i in range(len(teachers)):
            deltas.append(
                local_distill_trajectory(
                    teachers[i], init_params, make_model_fn,
                    client_X_list[i], K_steps, lr, momentum, tau, bs,
                    optimizer=optimizer,
                )
            )
        return deltas

    # Diagnostic path — also retain the per-step trajectory for issue 013.
    deltas_d: List[Dict] = []
    step_deltas_per_client: List[List[Dict]] = []
    for i in range(len(teachers)):
        delta_i, steps_i = local_distill_trajectory(
            teachers[i], init_params, make_model_fn,
            client_X_list[i], K_steps, lr, momentum, tau, bs,
            return_steps=True, optimizer=optimizer,
        )
        deltas_d.append(delta_i)
        step_deltas_per_client.append(steps_i)
    return deltas_d, step_deltas_per_client
