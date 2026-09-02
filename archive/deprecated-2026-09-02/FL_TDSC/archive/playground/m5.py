"""M5 = M4 + representation alignment via penultimate-feature MSE on anchors.

Adds a third loss term to the per-batch local-distillation loss:

    loss = KL(s(xb), T_i(xb))                       # real-data distillation
         + λ_anchor · CE(s(Z), y)                   # output-space anchor (M1/M4)
         + μ_emb   · MSE(feat(s, Z), E_y)           # NEW: penultimate alignment

where:
    Z  = K_a · C  synthetic class anchors (clustered, same as M4)
    y  = anchor labels
    E  ∈ R^{C × d_penult}  fixed shared target embeddings (orthonormal, deterministic)
    feat(s, z) = output of the model's penultimate (pre-classifier) layer

Together with M4's pre-alignment, this locks in BOTH the class-slot
assignment (output) AND the internal feature geometry. Two clients can no
longer correctly classify the anchors via different penultimate representations
-- the MSE term forces them to reach those classifications through the same
hidden manifold.
"""
from __future__ import annotations
import json, time, argparse
from pathlib import Path
from typing import Optional, Tuple

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
from .pre_align import pre_align
from .teacher import train_all_teachers


PENULTIMATE_DIM = {"mlp": 32, "lenet5": 84}


def make_target_embeddings(num_classes: int, penultimate_dim: int,
                           scale: float = 2.0, seed: int = 0,
                           device=None) -> torch.Tensor:
    """E ∈ R^{C × d_penult}, orthonormal rows scaled by `scale`.

    Requires C <= d_penult (true for MLP 32 ≥ 10 and LeNet 84 ≥ 10).
    Deterministic given seed → every client constructs the same E.
    """
    assert num_classes <= penultimate_dim
    g = torch.Generator(device="cpu").manual_seed(seed)
    raw = torch.randn(penultimate_dim, num_classes, generator=g)
    Q, _ = torch.linalg.qr(raw)              # (d_penult, num_classes)
    E = Q.T * scale                          # (num_classes, d_penult)
    if device is not None:
        E = E.to(device)
    return E


def extract_penultimate(model: nn.Module, x: torch.Tensor, arch: str) -> torch.Tensor:
    """Forward pass + return the penultimate-layer activation (post-ReLU)."""
    feats: list = []
    def hook(_mod, _inp, out):
        feats.append(out)
    if arch == "mlp":
        # nn.Sequential: Flatten, Linear(784,128), ReLU, Linear(128,32), ReLU, Linear(32,10)
        # The second ReLU is module index 4; its OUTPUT is the penultimate feature.
        target = model[4]
    elif arch == "lenet5":
        target = model.fc2          # we'll apply ReLU after
    else:
        raise ValueError(f"unknown arch {arch}")
    h = target.register_forward_hook(hook)
    try:
        _ = model(x)
    finally:
        h.remove()
    feat = feats[0]
    if arch == "lenet5":
        feat = F.relu(feat)
    return feat


def kl_loss(s_logits, t_logits, tau):
    s = F.log_softmax(s_logits / tau, dim=1)
    t = F.softmax(t_logits / tau, dim=1)
    return F.kl_div(s, t, reduction="batchmean") * (tau ** 2)


def local_distill_m5(teacher, local_subset, theta0, *, arch, anchors, E,
                     mu_emb, anchor_lambda, K, lr, batch_size, tau, seed, device):
    """One client's M5 local distillation. Returns ΔW_i."""
    torch.manual_seed(seed)
    s = build_model(arch).to(device); load_named(s, theta0); s.train()
    teacher = teacher.to(device).eval()
    Z, yZ = anchors
    Z_input = Z.view(Z.size(0), 1, 28, 28) if arch == "lenet5" else Z
    E_per_anchor = E[yZ]                              # (n_anchors, d_penult)

    if len(local_subset) == 0:
        return deltas(theta0, state_named(s))
    loader = DataLoader(local_subset, batch_size=batch_size, shuffle=True, num_workers=0)
    opt = optim.SGD(s.parameters(), lr=lr, momentum=0.9)
    for _ in range(K):
        for xb, _ in loader:
            xb = xb.to(device)
            with torch.no_grad():
                t_logits = teacher(xb)
            s_logits = s(xb)
            loss = kl_loss(s_logits, t_logits, tau)
            # anchor CE (output-space)
            loss = loss + anchor_lambda * F.cross_entropy(s(Z_input), yZ)
            # NEW: penultimate-feature MSE alignment
            feat = extract_penultimate(s, Z_input, arch)   # (n_anchors, d_penult)
            loss = loss + mu_emb * F.mse_loss(feat, E_per_anchor)
            opt.zero_grad(); loss.backward(); opt.step()
    return deltas(theta0, state_named(s))


def run_one_m5(*, arch, N, seed, alpha, device, K, teacher_epochs, weight_mode,
               anchors_per_class, anchor_scale, within_class_cos, anchor_lambda,
               pre_align_epochs, mu_emb, emb_scale, cache_root, lr, batch_size, tau):
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
    Z, yZ = make_anchors(num_classes=10, anchors_per_class=anchors_per_class,
                         input_dim=784, scale=anchor_scale,
                         within_class_cos=within_class_cos,
                         seed=seed, device=device)
    anchors = (Z, yZ)
    E = make_target_embeddings(num_classes=10,
                               penultimate_dim=PENULTIMATE_DIM[arch],
                               scale=emb_scale, seed=seed, device=device)
    if pre_align_epochs > 0:
        theta0 = pre_align(theta0, anchors, arch=arch,
                           epochs=pre_align_epochs, seed=seed, device=device)

    t0 = time.time()
    client_deltas = []
    for ci, (teacher, sub) in enumerate(zip(teachers, subs)):
        d = local_distill_m5(teacher, sub, theta0,
                             arch=arch, anchors=anchors, E=E, mu_emb=mu_emb,
                             anchor_lambda=anchor_lambda, K=K, lr=lr,
                             batch_size=batch_size, tau=tau,
                             seed=2000 + ci, device=device)
        client_deltas.append(d)
    distill_sec = time.time() - t0

    t0 = time.time()
    W_E = linear_aggregate(theta0, client_deltas,
                           client_sizes=client_sizes, weight_mode=weight_mode)
    aggregate_sec = time.time() - t0

    t0 = time.time()
    student_acc, per_class = evaluate_state(W_E, eval_ds, device, arch=arch)
    per_teacher = [evaluate_module(t, eval_ds, device) for t in teachers]
    eval_sec = time.time() - t0

    return {
        "method": "M5", "arch": arch, "weight_mode": weight_mode,
        "N": N, "seed": seed, "alpha": alpha, "K": K,
        "teacher_epochs": teacher_epochs,
        "anchor_scale": anchor_scale, "anchor_lambda": anchor_lambda,
        "anchors_per_class": anchors_per_class,
        "within_class_cos": within_class_cos,
        "pre_align_epochs": pre_align_epochs,
        "mu_emb": mu_emb, "emb_scale": emb_scale,
        "student_acc": student_acc,
        "per_class_acc": per_class,
        "per_teacher_acc": per_teacher,
        "best_teacher": max(per_teacher), "mean_teacher": sum(per_teacher) / len(per_teacher),
        "worst_teacher": min(per_teacher),
        "per_client_total": client_sizes,
        "per_client_per_class": holdings.tolist(),
        "phase_teacher_sec": teacher_sec, "phase_distill_sec": distill_sec,
        "phase_aggregate_sec": aggregate_sec, "phase_eval_sec": eval_sec,
    }


def pick_device():
    return torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--Ns", type=str, default="4,8,16,32")
    ap.add_argument("--arch", type=str, default="mlp", choices=["mlp", "lenet5"])
    ap.add_argument("--weight-mode", type=str, default="samples",
                    choices=["uniform", "samples"])
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--alpha", type=float, default=0.1)
    ap.add_argument("--K", type=int, default=5)
    ap.add_argument("--teacher-epochs", type=int, default=10)
    ap.add_argument("--anchors-per-class", type=int, default=50)
    ap.add_argument("--anchor-scale", type=float, default=3.0)
    ap.add_argument("--within-class-cos", type=float, default=0.5)
    ap.add_argument("--anchor-lambda", type=float, default=1.0)
    ap.add_argument("--pre-align-epochs", type=int, default=5)
    ap.add_argument("--mu-emb", type=float, default=0.1,
                    help="weight on penultimate-feature MSE alignment")
    ap.add_argument("--emb-scale", type=float, default=2.0,
                    help="L2 length of each per-class target embedding")
    ap.add_argument("--lr", type=float, default=1e-2)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--tau", type=float, default=4.0)
    ap.add_argument("--cache-root", type=str, default="playground/cache")
    ap.add_argument("--out", type=str, default="playground/results/m5.json")
    args = ap.parse_args()

    device = pick_device()
    print(f"[m5] device={device} arch={args.arch} weight_mode={args.weight_mode} "
          f"mu_emb={args.mu_emb} emb_scale={args.emb_scale}")
    Ns = [int(x) for x in args.Ns.split(",")]
    rows = []
    for N in Ns:
        print(f"[m5] start N={N}")
        tic = time.time()
        r = run_one_m5(arch=args.arch, N=N, seed=args.seed, alpha=args.alpha,
                       device=device, K=args.K, teacher_epochs=args.teacher_epochs,
                       weight_mode=args.weight_mode,
                       anchors_per_class=args.anchors_per_class,
                       anchor_scale=args.anchor_scale,
                       within_class_cos=args.within_class_cos,
                       anchor_lambda=args.anchor_lambda,
                       pre_align_epochs=args.pre_align_epochs,
                       mu_emb=args.mu_emb, emb_scale=args.emb_scale,
                       cache_root=args.cache_root, lr=args.lr,
                       batch_size=args.batch_size, tau=args.tau)
        r["wall_sec"] = time.time() - tic
        print(f"[m5] ok    N={N}  student={r['student_acc']:.4f}  "
              f"best_t={r['best_teacher']:.4f}  wall={r['wall_sec']:.1f}s")
        rows.append(r)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(rows, open(args.out, "w"), indent=2)
    print(f"[m5] done. wrote {args.out}")


if __name__ == "__main__":
    main()
