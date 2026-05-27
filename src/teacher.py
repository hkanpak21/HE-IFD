"""Supervised model training (teachers, oracle, Phase-0 warmups).

Ported verbatim from notebook Section 0.3 (`train_supervised_model`). This one
generic SGD trainer backs three roles in the protocol:

* **Teacher** — each client trains its own teacher on its local shard.
* **Oracle** — a centralised model on the whole pool (an upper-reference, NOT
  part of the protocol).
* **Phase-0 warmup** — supervised SGD on the alignment probe to produce θ₀
  (see ``phase0.warmup_init``).

Seeding follows the notebook conventions so a port reproduces the same teachers:
  teacher i -> seed*1000 + i ;  oracle -> seed*7919 ;  warmup -> fixed 12345.
``torch`` is imported lazily inside the function to keep login-node checks light.
"""
from __future__ import annotations

from typing import Callable, Dict, Optional


def train_supervised_model(
    make_model_fn: Callable,
    X,
    y,
    epochs: int,
    lr: float,
    momentum: float,
    bs: int,
    seed: int,
    init_params: Optional[Dict] = None,
    loss_fn=None,
):
    """Generic supervised SGD trainer. ``make_model_fn()`` returns a fresh model.

    Verbatim port of the notebook. Notes preserved exactly:
      * ``torch.manual_seed(seed)`` is set BEFORE the model is built, so weight
        init is seed-determined unless ``init_params`` overrides it.
      * Empty data (n == 0) returns the freshly-initialised model untouched —
        this is how zero-sample clients get a chance-level teacher.
      * SGD with momentum; full-batch reshuffle each epoch.
    """
    import torch
    import torch.nn.functional as F

    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch.manual_seed(seed)
    model = make_model_fn()
    if init_params is not None:
        model.load_state_dict(init_params)
    if loss_fn is None:
        loss_fn = F.cross_entropy
    X = X.to(device)
    y = y.to(device)
    n = X.shape[0]
    if n == 0:
        return model
    opt = torch.optim.SGD(model.parameters(), lr=lr, momentum=momentum)
    for _ in range(epochs):
        perm = torch.randperm(n, device=device)
        for i in range(0, n, bs):
            idx = perm[i:i + bs]
            opt.zero_grad()
            loss = loss_fn(model(X[idx]), y[idx])
            loss.backward()
            opt.step()
    return model


def train_client_teachers(
    make_model_fn: Callable,
    client_X_list,
    client_y_list,
    sample_sizes,
    num_classes: int,
    epochs: int,
    lr: float,
    momentum: float,
    bs: int,
    seed: int,
    eval_fn=None,
):
    """Train one teacher per client; return (teachers, per_teacher_acc).

    Mirrors the per-client teacher loop in the notebook's Section runners: a
    zero-sample client gets a fresh (chance-level) model and ``1/num_classes``
    accuracy; otherwise SGD with teacher seed ``seed*1000 + i``. ``eval_fn`` is
    an optional ``model -> float`` accuracy callback (so teacher caching / eval
    policy lives in the caller, not here).
    """
    teachers, t_accs = [], []
    for i in range(len(client_X_list)):
        if sample_sizes[i] == 0:
            t = make_model_fn()
            teachers.append(t)
            t_accs.append(1.0 / num_classes)
            continue
        t = train_supervised_model(
            make_model_fn, client_X_list[i], client_y_list[i],
            epochs=epochs, lr=lr, momentum=momentum, bs=bs,
            seed=seed * 1000 + i,
        )
        teachers.append(t)
        t_accs.append(eval_fn(t) if eval_fn is not None else float("nan"))
    return teachers, t_accs
