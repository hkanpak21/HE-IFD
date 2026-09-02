"""m7: LoRA-based local distillation.

Setup:
  - Teachers train normally on D_i (full LeNet, all weights free).
  - Students are LoRA-wrapped: conv layers frozen at the shared θ_0, only the
    fc layers get LoRA adapters (rank r). Distillation updates ONLY the LoRA
    params (A, B per fc layer).
  - "Delta" the client uploads is just the LoRA tensors {A_i, B_i}.
  - Server aggregates A and B SEPARATELY, sample-weighted.
  - Released student: W_eff = θ_0 (frozen) + (α/r) · B̄ · Ā per fc layer.

This is the cleanest test of the "fine-tuning regime" pivot. The backbone here
is a random θ_0 (not a real pretrained model) -- so the conv features are
random features, not learned features. The interesting question: does LoRA-only
delta aggregation survive heterogeneous data where the from-scratch full LeNet
aggregation collapsed?
"""
from __future__ import annotations
import argparse, copy, json, time
from pathlib import Path
from typing import Dict, List

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, Subset

from .data import client_subsets, dirichlet_partition, load_mnist, split_probe
from .evaluate import evaluate_module
from .lora import LoRALinear, wrap_with_lora, freeze_non_lora, lora_state, lora_deltas, trainable_param_count
from .model import LeNet5, build_mlp, shared_init
from .teacher import train_all_teachers


def kl_loss(s_logits, t_logits, tau):
    s = F.log_softmax(s_logits / tau, dim=1)
    t = F.softmax(t_logits / tau, dim=1)
    return F.kl_div(s, t, reduction="batchmean") * (tau ** 2)


def build_lora_student(arch: str, theta0_state: dict, rank: int, alpha: float,
                       device) -> nn.Module:
    """Build a fresh model, load θ_0 into it, wrap fc layers with LoRA, freeze the rest."""
    if arch == "lenet5":
        m = LeNet5().to(device)
        m.load_state_dict(theta0_state, strict=True)
        # Wrap the three fc layers; conv layers stay frozen at θ_0.
        wrap_with_lora(m, rank=rank, alpha=alpha,
                       target_names=("fc1", "fc2", "fc3"))
    elif arch == "mlp":
        m = build_mlp().to(device)
        m.load_state_dict(theta0_state, strict=True)
        # build_mlp is an nn.Sequential of Flatten,Linear,ReLU,Linear,ReLU,Linear
        # wrap every Linear inside.
        wrap_with_lora(m, rank=rank, alpha=alpha, target_names=None)
    else:
        raise ValueError(arch)
    freeze_non_lora(m)
    return m


def local_distill_lora(teacher: nn.Module, subset: Subset, theta0_state: dict,
                       *, arch: str, rank: int, alpha: float, K: int, lr: float,
                       batch_size: int, tau: float, seed: int, device) -> dict:
    """Run K epochs of KL distillation on D_i, updating only LoRA params.

    Returns the per-LoRA-tensor delta (A_after - A_init, B_after - B_init).
    Since B is init to zero, B_delta = B_after. A delta is A_after - A_kaiming.
    """
    torch.manual_seed(seed)
    s = build_lora_student(arch, theta0_state, rank=rank, alpha=alpha, device=device)
    lora_init = lora_state(s)
    teacher = teacher.to(device).eval()

    if len(subset) == 0:
        return lora_deltas(lora_init, lora_init), trainable_param_count(s)

    loader = DataLoader(subset, batch_size=batch_size, shuffle=True, num_workers=0)
    opt = optim.SGD([p for p in s.parameters() if p.requires_grad], lr=lr, momentum=0.9)
    s.train()
    for _ in range(K):
        for xb, _ in loader:
            xb = xb.to(device)
            with torch.no_grad():
                t_logits = teacher(xb)
            s_logits = s(xb)
            loss = kl_loss(s_logits, t_logits, tau)
            opt.zero_grad(); loss.backward(); opt.step()
    final = lora_state(s)
    return lora_deltas(lora_init, final), trainable_param_count(s)


def lora_aggregate(lora_init: dict, client_deltas: List[dict],
                   client_sizes: List[int], weight_mode: str) -> dict:
    """Sample-weighted sum of LoRA deltas, added to lora_init."""
    N = len(client_deltas)
    if weight_mode == "uniform":
        w = [1.0 / N] * N
    elif weight_mode == "samples":
        total = float(sum(client_sizes))
        w = [n / total for n in client_sizes]
    else:
        raise ValueError(weight_mode)
    out = {}
    for k in lora_init:
        acc = w[0] * client_deltas[0][k]
        for wi, d in zip(w[1:], client_deltas[1:]):
            acc = acc + wi * d[k]
        out[k] = lora_init[k] + acc
    return out


def build_eval_model(arch: str, theta0_state: dict, lora_state_dict: dict,
                     rank: int, alpha: float, device) -> nn.Module:
    """Construct the released model with averaged LoRA loaded."""
    m = build_lora_student(arch, theta0_state, rank=rank, alpha=alpha, device=device)
    own = m.state_dict()
    for k, v in lora_state_dict.items():
        own[k] = v.to(device)
    m.load_state_dict(own, strict=True)
    m.eval()
    return m


def run_one(*, arch, N, seed, alpha, K, teacher_epochs, weight_mode,
            rank, lora_alpha, lr, batch_size, tau, cache_root, device) -> dict:
    train_ds, test_ds = load_mnist()
    _, eval_ds = split_probe(test_ds, probe_size=5000, seed=seed)
    idx_per, holdings = dirichlet_partition(train_ds, N, alpha, seed)
    subs = client_subsets(train_ds, idx_per)
    client_sizes = [len(s) for s in subs]

    t0 = time.time()
    teachers = train_all_teachers(subs, arch=arch, N=N, alpha=alpha, seed=seed,
                                  cache_root=cache_root, epochs=teacher_epochs,
                                  device=device)
    teacher_sec = time.time() - t0

    theta0_state = shared_init(seed=seed, arch=arch, device=device)
    # Capture the lora_init (same for all clients since seeded the same way).
    # Use seed 2000 (matches the per-client offset before any client-specific reseeding).
    torch.manual_seed(2000)
    seeding_model = build_lora_student(arch, theta0_state, rank=rank, alpha=lora_alpha, device=device)
    lora_init = lora_state(seeding_model)

    t0 = time.time()
    client_deltas = []
    train_param_count = 0
    for ci, (teacher, sub) in enumerate(zip(teachers, subs)):
        d, tpc = local_distill_lora(teacher, sub, theta0_state,
                                    arch=arch, rank=rank, alpha=lora_alpha,
                                    K=K, lr=lr, batch_size=batch_size, tau=tau,
                                    seed=2000 + ci, device=device)
        client_deltas.append(d)
        train_param_count = tpc
    distill_sec = time.time() - t0

    final_lora = lora_aggregate(lora_init, client_deltas, client_sizes, weight_mode)
    m_eval = build_eval_model(arch, theta0_state, final_lora,
                              rank=rank, alpha=lora_alpha, device=device)
    student_acc = evaluate_module(m_eval, eval_ds, device)
    per_teacher = [evaluate_module(t, eval_ds, device) for t in teachers]

    return {
        "method": "M7_LoRA", "arch": arch, "weight_mode": weight_mode,
        "N": N, "seed": seed, "alpha": alpha, "K": K,
        "rank": rank, "lora_alpha": lora_alpha,
        "trainable_params_per_client": train_param_count,
        "student_acc": student_acc,
        "per_teacher_acc": per_teacher,
        "best_teacher": max(per_teacher), "mean_teacher": sum(per_teacher) / len(per_teacher),
        "worst_teacher": min(per_teacher),
        "per_client_total": client_sizes, "per_client_per_class": holdings.tolist(),
        "phase_teacher_sec": teacher_sec, "phase_distill_sec": distill_sec,
    }


def pick_device():
    return torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--Ns", type=str, default="4,8,16,32")
    ap.add_argument("--arch", type=str, default="lenet5", choices=["mlp", "lenet5"])
    ap.add_argument("--weight-mode", type=str, default="samples", choices=["uniform", "samples"])
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--alpha", type=float, default=0.1)
    ap.add_argument("--K", type=int, default=5)
    ap.add_argument("--teacher-epochs", type=int, default=10)
    ap.add_argument("--rank", type=int, default=8)
    ap.add_argument("--lora-alpha", type=float, default=16.0)
    ap.add_argument("--lr", type=float, default=1e-2)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--tau", type=float, default=4.0)
    ap.add_argument("--cache-root", type=str, default="playground/cache")
    ap.add_argument("--out", type=str, default="playground/results/m7_lora.json")
    args = ap.parse_args()

    device = pick_device()
    print(f"[m7] device={device} arch={args.arch} weight_mode={args.weight_mode} "
          f"rank={args.rank} lora_alpha={args.lora_alpha}")
    Ns = [int(x) for x in args.Ns.split(",")]
    rows = []
    for N in Ns:
        print(f"[m7] start N={N}")
        tic = time.time()
        r = run_one(arch=args.arch, N=N, seed=args.seed, alpha=args.alpha,
                    K=args.K, teacher_epochs=args.teacher_epochs,
                    weight_mode=args.weight_mode,
                    rank=args.rank, lora_alpha=args.lora_alpha,
                    lr=args.lr, batch_size=args.batch_size, tau=args.tau,
                    cache_root=args.cache_root, device=device)
        r["wall_sec"] = time.time() - tic
        print(f"[m7] ok    N={N}  student={r['student_acc']:.4f}  "
              f"best_t={r['best_teacher']:.4f}  "
              f"mean_t={r['mean_teacher']:.4f}  "
              f"trainable={r['trainable_params_per_client']}  "
              f"wall={r['wall_sec']:.1f}s")
        rows.append(r)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(rows, open(args.out, "w"), indent=2)
    print(f"[m7] done. wrote {args.out}")


if __name__ == "__main__":
    main()
