"""1-shot regularization methods (no extra communication).

Tests Path A from the discussion: prevent neuron drift at the local-distillation
step so server-side linear aggregation actually works.

Methods:
    M0   -- baseline: KL local distill on D_i only, sum deltas
    A2   -- disjoint sparse mask: each client only updates its assigned subset
            of parameters, derived deterministically from public seed.
    A3   -- multi-layer activation-target regularization: each client's
            activations on shared anchors are pulled toward a deterministic
            shared target. Generalises M5 to all hidden layers, no extra
            comms. No anchor CE term, only the activation alignment.

All FHE-compatible: server-side stays vanilla linear sum.
Sample-weighted aggregation throughout.
"""
from __future__ import annotations
import argparse, json, time
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader

from .anchors import make_anchors
from .aggregate import linear_aggregate
from .data import client_subsets, dirichlet_partition, load_mnist, split_probe
from .evaluate import evaluate_module, evaluate_state
from .model import build_model, load_named, state_named, deltas, shared_init
from .teacher import train_all_teachers


# ---------------------------- A2: sparse masks ----------------------------

def deterministic_sparse_masks(theta0: dict, N: int, seed: int) -> list[dict]:
    """Return N masks: per-parameter, one client gets weight 1, others 0.

    Assignment is fully deterministic from `seed`. Each parameter is assigned
    to exactly one client by uniform random sampling.
    """
    g = torch.Generator(device="cpu").manual_seed(seed * 7 + N * 13)
    masks: list[dict] = [{} for _ in range(N)]
    for k, v in theta0.items():
        assign = torch.randint(N, v.shape, generator=g)   # int in [0, N)
        for i in range(N):
            masks[i][k] = (assign == i).to(v.dtype).to(v.device)
    return masks


# ------------------- A3: multi-layer activation alignment -------------------

def collect_intermediate_features(model: nn.Module, x: torch.Tensor,
                                  arch: str) -> dict[str, torch.Tensor]:
    """Capture activations after each dense-layer ReLU."""
    feats: dict = {}
    handles = []
    def hook_factory(name):
        def hook(_m, _i, o): feats[name] = F.relu(o)
        return hook
    if arch == "mlp":
        # nn.Sequential: 0=Flatten, 1=Linear, 2=ReLU, 3=Linear, 4=ReLU, 5=Linear
        # Hook the Linear pre-ReLU, then ReLU in the hook (cleaner).
        handles.append(model[1].register_forward_hook(hook_factory("h1_128")))
        handles.append(model[3].register_forward_hook(hook_factory("h2_32")))
    elif arch == "lenet5":
        # LeNet5: fc1 (120) and fc2 (84) — the dense penultimates.
        handles.append(model.fc1.register_forward_hook(hook_factory("fc1_120")))
        handles.append(model.fc2.register_forward_hook(hook_factory("fc2_84")))
    else:
        raise ValueError(f"unknown arch={arch}")
    try:
        _ = model(x)
    finally:
        for h in handles: h.remove()
    return feats


def deterministic_layer_targets(arch: str, num_anchors_per_class: int,
                                num_classes: int, seed: int,
                                device) -> dict[str, torch.Tensor]:
    """Per-anchor target activations, deterministic from seed.

    Layout: target_layer[k * K_a + j] = per-class target replicated K_a times.
    Each class's target is a random unit vector in the layer's activation space,
    scaled. Targets are mutually orthogonal across classes (QR).
    """
    K_a = num_anchors_per_class
    targets: dict[str, torch.Tensor] = {}
    g = torch.Generator(device="cpu").manual_seed(seed + 999)
    dims = {
        "mlp": {"h1_128": 128, "h2_32": 32},
        "lenet5": {"fc1_120": 120, "fc2_84": 84},
    }[arch]
    for layer_name, d in dims.items():
        # one target unit vector per class
        raw = torch.randn(d, num_classes, generator=g)
        Q, _ = torch.linalg.qr(raw)                         # (d, num_classes)
        T = (Q.T * 2.0)                                     # (num_classes, d), scaled
        # repeat per anchor
        T_per_anchor = T.repeat_interleave(K_a, dim=0)      # (K_a * C, d)
        targets[layer_name] = T_per_anchor.to(device)
    return targets


# ---------------------------- distillation step ----------------------------

def local_distill_method(method: str, teacher: nn.Module, local_subset,
                         theta0: dict, *, arch: str, anchors, layer_targets,
                         client_mask, K: int, lr: float, batch_size: int,
                         tau: float, mu_a3: float, seed: int, device) -> dict:
    torch.manual_seed(seed)
    s = build_model(arch).to(device); load_named(s, theta0); s.train()
    teacher = teacher.to(device).eval()

    if len(local_subset) == 0:
        return deltas(theta0, state_named(s))
    loader = DataLoader(local_subset, batch_size=batch_size, shuffle=True, num_workers=0)
    opt = optim.SGD(s.parameters(), lr=lr, momentum=0.9)

    Z = anchors[0] if anchors is not None else None
    Z_in = Z.view(Z.size(0), 1, 28, 28) if (Z is not None and arch == "lenet5") else Z

    for _ in range(K):
        for xb, _ in loader:
            xb = xb.to(device)
            with torch.no_grad():
                t_logits = teacher(xb)
            s_logits = s(xb)
            s_log = F.log_softmax(s_logits / tau, dim=1)
            t_soft = F.softmax(t_logits / tau, dim=1)
            loss = F.kl_div(s_log, t_soft, reduction="batchmean") * (tau ** 2)
            if method == "A3":
                feats = collect_intermediate_features(s, Z_in, arch)
                for ln, target in layer_targets.items():
                    loss = loss + mu_a3 * F.mse_loss(feats[ln], target)
            opt.zero_grad(); loss.backward(); opt.step()

    d = deltas(theta0, state_named(s))
    if method == "A2" and client_mask is not None:
        d = {k: v * client_mask[k] for k, v in d.items()}
    return d


# ------------------------------- driver -------------------------------

def run_one(method: str, *, arch: str, N: int, seed: int, alpha: float,
            K: int, teacher_epochs: int, mu_a3: float, anchors_per_class: int,
            weight_mode: str, cache_root: str, device) -> dict:
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

    theta0 = shared_init(seed=seed, arch=arch, device=device)

    masks = deterministic_sparse_masks(theta0, N, seed) if method == "A2" else [None] * N
    if method == "A3":
        Z, yZ = make_anchors(num_classes=10, anchors_per_class=anchors_per_class,
                             input_dim=784, scale=3.0, within_class_cos=0.0,
                             seed=seed, device=device)
        anchors = (Z, yZ)
        layer_targets = deterministic_layer_targets(
            arch, anchors_per_class, num_classes=10, seed=seed, device=device)
    else:
        anchors = None
        layer_targets = None

    t0 = time.time()
    client_deltas = []
    for ci, (teacher, sub) in enumerate(zip(teachers, subs)):
        d = local_distill_method(
            method, teacher, sub, theta0, arch=arch,
            anchors=anchors, layer_targets=layer_targets,
            client_mask=masks[ci], K=K, lr=1e-2, batch_size=64,
            tau=4.0, mu_a3=mu_a3, seed=2000 + ci, device=device,
        )
        client_deltas.append(d)
    distill_sec = time.time() - t0

    # For A2 with disjoint masks: each parameter was touched by exactly 1 client,
    # so the "weight" for that client on that parameter is its sample-weight share.
    # Standard sample-weighted sum still works.
    W_E = linear_aggregate(theta0, client_deltas,
                           client_sizes=client_sizes, weight_mode=weight_mode)

    student_acc, per_class = evaluate_state(W_E, eval_ds, device, arch=arch)
    per_teacher = [evaluate_module(t, eval_ds, device) for t in teachers]

    return {
        "method": method, "arch": arch, "weight_mode": weight_mode,
        "N": N, "seed": seed, "alpha": alpha, "K": K,
        "mu_a3": mu_a3, "anchors_per_class": anchors_per_class,
        "student_acc": student_acc, "per_class_acc": per_class,
        "per_teacher_acc": per_teacher,
        "best_teacher": max(per_teacher), "mean_teacher": sum(per_teacher)/len(per_teacher),
        "worst_teacher": min(per_teacher),
        "per_client_total": client_sizes, "per_client_per_class": holdings.tolist(),
        "phase_teacher_sec": teacher_sec, "phase_distill_sec": distill_sec,
    }


def pick_device():
    return torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--Ns", type=str, default="4,16")
    ap.add_argument("--methods", type=str, default="M0,A2,A3")
    ap.add_argument("--arch", type=str, default="mlp", choices=["mlp", "lenet5"])
    ap.add_argument("--weight-mode", type=str, default="samples")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--alpha", type=float, default=0.1)
    ap.add_argument("--K", type=int, default=5)
    ap.add_argument("--teacher-epochs", type=int, default=10)
    ap.add_argument("--anchors-per-class", type=int, default=50)
    ap.add_argument("--mu-a3", type=float, default=0.5)
    ap.add_argument("--cache-root", type=str, default="playground/cache")
    ap.add_argument("--out", type=str, default="playground/results/m6.json")
    args = ap.parse_args()

    device = pick_device()
    print(f"[m6] device={device} arch={args.arch} weight_mode={args.weight_mode} mu_a3={args.mu_a3}")
    Ns = [int(x) for x in args.Ns.split(",")]
    methods = args.methods.split(",")

    rows = []
    for N in Ns:
        for method in methods:
            print(f"[m6] start N={N} method={method}")
            tic = time.time()
            r = run_one(method, arch=args.arch, N=N, seed=args.seed, alpha=args.alpha,
                        K=args.K, teacher_epochs=args.teacher_epochs,
                        mu_a3=args.mu_a3, anchors_per_class=args.anchors_per_class,
                        weight_mode=args.weight_mode, cache_root=args.cache_root,
                        device=device)
            r["wall_sec"] = time.time() - tic
            print(f"[m6] ok    N={N} method={method}  "
                  f"student={r['student_acc']:.4f}  "
                  f"best_t={r['best_teacher']:.4f}  "
                  f"mean_t={r['mean_teacher']:.4f}  "
                  f"wall={r['wall_sec']:.1f}s")
            rows.append(r)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(rows, open(args.out, "w"), indent=2)
    print(f"[m6] done. wrote {args.out}")


if __name__ == "__main__":
    main()
