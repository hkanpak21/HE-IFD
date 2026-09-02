"""M8: 1.5-shot ensemble-distillation protocol.

Protocol (plaintext simulation; all "encryptions" are commented where they
would happen in production with multiparty CKKS):

  Phase 0 (setup): public seed -> θ_0 (shared init); public seed -> probe X
    (a small held-out set, |X| ≪ |test|).  No real data needed at this stage;
    X is plaintext-public.

  Phase 1a (each client, local plaintext):  compute teacher logits L_i = T_i(X).
  Phase 1b (each client -> server, ENCRYPTED in production): ship ⟨L_i⟩.
  Phase 1c (server, encrypted): aggregate
       ⟨Y_ens⟩ = Σ_i (w_i / Σ_j w_j) · ⟨L_i⟩          # PT × CT, depth +1
  Phase 1d (collective threshold decrypt): release Y_ens to all clients.

  Phase 2 (each client, local plaintext):  starting from θ_0, train a student
    on (X, Y_ens) as soft labels via KL.  Optionally also include the local
    (D_i, T_i) KL term to incorporate local data.  Run K epochs.

  Phase 3 (each client -> server, ENCRYPTED in production): ship ⟨ΔW_i⟩.
  Phase 4 (server, encrypted): aggregate
       ⟨W_E⟩ = θ_0 + Σ_i (w_i / Σ_j w_j) · ⟨ΔW_i⟩    # PT × CT, depth +1
  Phase 5 (collective threshold decrypt): release W_E.

Two phase-2 variants exposed:
    M8a -- "ensemble only":  loss = KL(S(X), Y_ens)
    M8b -- "ensemble + local": loss = KL(S(X), Y_ens) + λ · KL(S(D_i), T_i(D_i))

Why this should work for conv architectures:
    In M8a, every client trains on the exact same (X, Y_ens) starting from the
    exact same θ_0 with the same hyperparameters.  The resulting student weights
    are near-identical across clients (modulo SGD noise).  Linear averaging in
    phase 4 is therefore trivially well-behaved -- there is no conv-filter
    collision because every client's filters converged to almost the same point.

    In M8b, the local data signal reintroduces some drift, but the ensemble
    target keeps clients pulled toward a shared geometry.
"""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
from typing import List

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, Subset

from .aggregate import linear_aggregate
from .data import client_subsets, dirichlet_partition, load_mnist, split_probe
from .evaluate import evaluate_module, evaluate_state
from .model import build_model, load_named, state_named, deltas, shared_init
from .teacher import train_all_teachers


def kl_loss(s_logits, t_logits, tau):
    s = F.log_softmax(s_logits / tau, dim=1)
    t = F.softmax(t_logits / tau, dim=1)
    return F.kl_div(s, t, reduction="batchmean") * (tau ** 2)


# ---------------------- Phase 1: build Y_ens (plaintext sim) ----------------------

@torch.no_grad()
def teacher_logits_on_probe(teacher: nn.Module, probe_ds: Subset, device,
                            batch_size: int = 256) -> torch.Tensor:
    """Run teacher on the full probe in order, return logits (|X|, C)."""
    teacher = teacher.to(device).eval()
    loader = DataLoader(probe_ds, batch_size=batch_size, shuffle=False, num_workers=0)
    chunks = []
    for xb, _ in loader:
        chunks.append(teacher(xb.to(device)))
    return torch.cat(chunks, dim=0)


def build_ensemble_target(teachers: List[nn.Module], probe_ds: Subset,
                          client_sizes: List[int], weight_mode: str,
                          dp_sigma: float, device) -> torch.Tensor:
    """Phase 1: per-client teacher logits on X, server-side weighted average,
    optional DP noise. Returns Y_ens (|X|, C)."""
    N = len(teachers)
    if weight_mode == "uniform":
        weights = [1.0 / N] * N
    elif weight_mode == "samples":
        total = float(sum(client_sizes))
        weights = [n / total for n in client_sizes]
    else:
        raise ValueError(weight_mode)
    Y_ens = None
    for w, t in zip(weights, teachers):
        L = teacher_logits_on_probe(t, probe_ds, device)
        Y_ens = w * L if Y_ens is None else Y_ens + w * L
    if dp_sigma > 0.0:
        Y_ens = Y_ens + torch.randn_like(Y_ens) * dp_sigma
    return Y_ens   # (|X|, C)


# ---------------------- Phase 2: local distillation ----------------------

class ProbeWithSoftLabels(torch.utils.data.Dataset):
    """Pair (x, y_soft) for distillation. x from probe, y from Y_ens row."""
    def __init__(self, probe_ds, Y_ens):
        self.probe = probe_ds
        self.Y = Y_ens          # (|X|, C)
        assert len(probe_ds) == Y_ens.size(0)
    def __len__(self): return len(self.probe)
    def __getitem__(self, i):
        x, _ = self.probe[i]
        return x, self.Y[i]


def local_distill_m8(method: str, *, arch, theta0, teacher, local_subset,
                     probe_ds, Y_ens, K, lr, batch_size, tau, local_lambda,
                     seed, device) -> dict:
    """Phase 2 for one client.

    method='M8a' -> distill on (X, Y_ens) only.
    method='M8b' -> also add KL on (D_i, T_i(D_i)).
    """
    torch.manual_seed(seed)
    s = build_model(arch).to(device); load_named(s, theta0); s.train()
    probe_loader = DataLoader(ProbeWithSoftLabels(probe_ds, Y_ens),
                              batch_size=batch_size, shuffle=True, num_workers=0)
    local_loader = (DataLoader(local_subset, batch_size=batch_size, shuffle=True, num_workers=0)
                    if method == "M8b" and len(local_subset) > 0 else None)
    teacher = teacher.to(device).eval()
    opt = optim.SGD(s.parameters(), lr=lr, momentum=0.9)

    for _ in range(K):
        if local_loader is not None:
            local_iter = iter(local_loader)
        for xb, yb_soft in probe_loader:
            xb = xb.to(device); yb_soft = yb_soft.to(device)
            s_logits = s(xb)
            loss = kl_loss(s_logits, yb_soft, tau)
            if method == "M8b" and local_loader is not None:
                try:
                    xl, _ = next(local_iter)
                except StopIteration:
                    local_iter = iter(local_loader)
                    xl, _ = next(local_iter)
                xl = xl.to(device)
                with torch.no_grad():
                    tl = teacher(xl)
                sl = s(xl)
                loss = loss + local_lambda * kl_loss(sl, tl, tau)
            opt.zero_grad(); loss.backward(); opt.step()
    return deltas(theta0, state_named(s))


# ---------------------- driver ----------------------

def run_one(*, method, arch, N, seed, alpha, K, teacher_epochs, weight_mode,
            probe_size, dp_sigma, local_lambda, lr, batch_size, tau,
            cache_root, device) -> dict:
    train_ds, test_ds = load_mnist()
    probe_ds, eval_ds = split_probe(test_ds, probe_size=probe_size, seed=seed)
    idx_per, holdings = dirichlet_partition(train_ds, N, alpha, seed)
    subs = client_subsets(train_ds, idx_per)
    client_sizes = [len(s) for s in subs]

    t0 = time.time()
    teachers = train_all_teachers(subs, arch=arch, N=N, alpha=alpha, seed=seed,
                                  cache_root=cache_root, epochs=teacher_epochs,
                                  device=device)
    teacher_sec = time.time() - t0

    # Phase 1: ensemble target on the probe
    t0 = time.time()
    Y_ens = build_ensemble_target(teachers, probe_ds, client_sizes,
                                  weight_mode, dp_sigma, device)
    phase1_sec = time.time() - t0

    theta0 = shared_init(seed=seed, arch=arch, device=device)

    # Phase 2: each client distils against (probe, Y_ens) [+ optional local]
    t0 = time.time()
    client_deltas = []
    for ci, (teacher, sub) in enumerate(zip(teachers, subs)):
        d = local_distill_m8(method, arch=arch, theta0=theta0,
                             teacher=teacher, local_subset=sub,
                             probe_ds=probe_ds, Y_ens=Y_ens,
                             K=K, lr=lr, batch_size=batch_size, tau=tau,
                             local_lambda=local_lambda,
                             seed=2000 + ci, device=device)
        client_deltas.append(d)
    distill_sec = time.time() - t0

    # Phase 4: server aggregate
    W_E = linear_aggregate(theta0, client_deltas,
                           client_sizes=client_sizes, weight_mode=weight_mode)
    student_acc, per_class = evaluate_state(W_E, eval_ds, device, arch=arch)
    per_teacher = [evaluate_module(t, eval_ds, device) for t in teachers]

    return {
        "method": method, "arch": arch, "weight_mode": weight_mode,
        "N": N, "seed": seed, "alpha": alpha, "K": K,
        "teacher_epochs": teacher_epochs,
        "probe_size": probe_size, "dp_sigma": dp_sigma, "local_lambda": local_lambda,
        "student_acc": student_acc, "per_class_acc": per_class,
        "per_teacher_acc": per_teacher,
        "best_teacher": max(per_teacher), "mean_teacher": sum(per_teacher) / len(per_teacher),
        "worst_teacher": min(per_teacher),
        "per_client_total": client_sizes, "per_client_per_class": holdings.tolist(),
        "phase_teacher_sec": teacher_sec,
        "phase1_ensemble_sec": phase1_sec,
        "phase2_distill_sec": distill_sec,
    }


def pick_device():
    return torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--Ns", type=str, default="4,16")
    ap.add_argument("--methods", type=str, default="M8a,M8b")
    ap.add_argument("--arch", type=str, default="mlp", choices=["mlp", "lenet5"])
    ap.add_argument("--weight-mode", type=str, default="samples")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--alpha", type=float, default=0.1)
    ap.add_argument("--K", type=int, default=5)
    ap.add_argument("--teacher-epochs", type=int, default=10)
    ap.add_argument("--probe-size", type=int, default=1000)
    ap.add_argument("--dp-sigma", type=float, default=0.0,
                    help="Gaussian noise std added to Y_ens for DP. 0 = no noise.")
    ap.add_argument("--local-lambda", type=float, default=1.0,
                    help="weight on local KL term in M8b")
    ap.add_argument("--lr", type=float, default=1e-2)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--tau", type=float, default=4.0)
    ap.add_argument("--cache-root", type=str, default="playground/cache")
    ap.add_argument("--out", type=str, default="playground/results/m8.json")
    args = ap.parse_args()

    device = pick_device()
    print(f"[m8] device={device} arch={args.arch} weight_mode={args.weight_mode} "
          f"probe={args.probe_size} dp_sigma={args.dp_sigma}")
    Ns = [int(x) for x in args.Ns.split(",")]
    methods = args.methods.split(",")

    rows = []
    for N in Ns:
        for method in methods:
            print(f"[m8] start N={N} method={method}")
            tic = time.time()
            r = run_one(method=method, arch=args.arch, N=N, seed=args.seed,
                        alpha=args.alpha, K=args.K,
                        teacher_epochs=args.teacher_epochs,
                        weight_mode=args.weight_mode,
                        probe_size=args.probe_size, dp_sigma=args.dp_sigma,
                        local_lambda=args.local_lambda,
                        lr=args.lr, batch_size=args.batch_size, tau=args.tau,
                        cache_root=args.cache_root, device=device)
            r["wall_sec"] = time.time() - tic
            print(f"[m8] ok    N={N} method={method}  "
                  f"student={r['student_acc']:.4f}  "
                  f"best_t={r['best_teacher']:.4f}  "
                  f"mean_t={r['mean_teacher']:.4f}  "
                  f"wall={r['wall_sec']:.1f}s")
            rows.append(r)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(rows, open(args.out, "w"), indent=2)
    print(f"[m8] done. wrote {args.out}")


if __name__ == "__main__":
    main()
