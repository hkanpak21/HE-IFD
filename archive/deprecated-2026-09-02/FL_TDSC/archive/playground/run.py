"""Run the method comparison grid on MNIST at N ∈ {Ns}.

Methods:
    M0 -- no method (current v1): KL on D_i only, sum deltas
    M1 -- anchors method: KL on D_i + CE on synthetic anisotropic class anchors
    M3 -- real public probe: KL on (P ∪ D_i), P = 5000 from test
    M4 -- clustered anchors + pre-alignment (M1 generalised)

Aggregator weight_mode:
    "uniform" -> (1/N) Σ ΔW_i
    "samples" -> Σ (|D_i|/Σ|D_j|) · ΔW_i
"""
from __future__ import annotations
import argparse, json, time
from pathlib import Path

import torch

from .anchors import make_anchors
from .aggregate import linear_aggregate
from .data import client_subsets, dirichlet_partition, load_mnist, split_probe, union
from .distill import DistillCfg, local_distill
from .evaluate import evaluate_module, evaluate_state
from .model import shared_init
from .pre_align import pre_align
from .teacher import train_all_teachers


def pick_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def run_one(method: str, *, arch: str, N: int, seed: int, alpha: float, device,
            K: int, teacher_epochs: int, probe_size: int,
            anchor_scale: float, anchor_lambda: float,
            anchors_per_class: int, within_class_cos: float,
            pre_align_epochs: int, weight_mode: str,
            cache_root: str) -> dict:
    train_ds, test_ds = load_mnist()
    probe_ds, eval_ds = split_probe(test_ds, probe_size=probe_size, seed=seed)
    idx_per, holdings = dirichlet_partition(train_ds, N, alpha, seed)
    subs = client_subsets(train_ds, idx_per)
    client_sizes = [len(s) for s in subs]

    t0 = time.time()
    teachers = train_all_teachers(
        subs, arch=arch, N=N, alpha=alpha, seed=seed,
        cache_root=cache_root, epochs=teacher_epochs, device=device,
    )
    teacher_sec = time.time() - t0

    theta0 = shared_init(seed=seed, arch=arch, device=device)

    if method in ("M1", "M4"):
        Z, yZ = make_anchors(num_classes=10, anchors_per_class=anchors_per_class,
                             input_dim=784, scale=anchor_scale,
                             within_class_cos=within_class_cos,
                             seed=seed, device=device)
        anchors = (Z, yZ)
    else:
        anchors = None

    # Pre-alignment (M4): produce a shared deterministic θ_pre
    if method == "M4" and pre_align_epochs > 0:
        theta0 = pre_align(theta0, anchors, arch=arch,
                           epochs=pre_align_epochs, seed=seed, device=device)

    use_probe = (method == "M3")
    use_anchors = method in ("M1", "M4")

    t0 = time.time()
    client_deltas = []
    for ci, (teacher, sub) in enumerate(zip(teachers, subs)):
        distill_ds = union(probe_ds, sub) if use_probe else sub
        cfg = DistillCfg(
            use_probe=use_probe, use_anchors=use_anchors,
            anchor_lambda=anchor_lambda, K=K,
        )
        d = local_distill(teacher, distill_ds, theta0,
                          cfg=cfg, device=device, seed=2000 + ci,
                          arch=arch, anchors=anchors)
        client_deltas.append(d)
    distill_sec = time.time() - t0

    t0 = time.time()
    W_E = linear_aggregate(theta0, client_deltas,
                           client_sizes=client_sizes,
                           weight_mode=weight_mode)
    aggregate_sec = time.time() - t0

    t0 = time.time()
    student_acc, per_class = evaluate_state(W_E, eval_ds, device, arch=arch)
    per_teacher = [evaluate_module(t, eval_ds, device) for t in teachers]
    eval_sec = time.time() - t0

    return {
        "method": method,
        "arch": arch, "weight_mode": weight_mode,
        "N": N, "seed": seed, "alpha": alpha, "K": K,
        "teacher_epochs": teacher_epochs,
        "anchor_scale": anchor_scale, "anchor_lambda": anchor_lambda,
        "anchors_per_class": anchors_per_class,
        "within_class_cos": within_class_cos,
        "pre_align_epochs": pre_align_epochs if method == "M4" else 0,
        "probe_size": probe_size if use_probe else 0,
        "student_acc": student_acc,
        "per_class_acc": per_class,
        "per_teacher_acc": per_teacher,
        "best_teacher": max(per_teacher) if per_teacher else None,
        "mean_teacher": sum(per_teacher) / len(per_teacher) if per_teacher else None,
        "worst_teacher": min(per_teacher) if per_teacher else None,
        "per_client_total": client_sizes,
        "per_client_per_class": holdings.tolist(),
        "phase_teacher_sec": teacher_sec,
        "phase_distill_sec": distill_sec,
        "phase_aggregate_sec": aggregate_sec,
        "phase_eval_sec": eval_sec,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--Ns", type=str, default="1,2,4")
    ap.add_argument("--methods", type=str, default="M0,M3,M4")
    ap.add_argument("--arch", type=str, default="mlp", choices=["mlp", "lenet5"])
    ap.add_argument("--weight-mode", type=str, default="uniform",
                    choices=["uniform", "samples"])
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--alpha", type=float, default=0.1)
    ap.add_argument("--K", type=int, default=5)
    ap.add_argument("--teacher-epochs", type=int, default=10)
    ap.add_argument("--probe-size", type=int, default=5000)
    ap.add_argument("--anchor-scale", type=float, default=3.0)
    ap.add_argument("--anchor-lambda", type=float, default=1.0)
    ap.add_argument("--anchors-per-class", type=int, default=50)
    ap.add_argument("--within-class-cos", type=float, default=0.5)
    ap.add_argument("--pre-align-epochs", type=int, default=5)
    ap.add_argument("--cache-root", type=str, default="playground/cache")
    ap.add_argument("--out", type=str, default="playground/results/grid.json")
    args = ap.parse_args()

    device = pick_device()
    print(f"[playground] device={device} arch={args.arch} weight_mode={args.weight_mode}")
    Ns = [int(x) for x in args.Ns.split(",")]
    methods = args.methods.split(",")

    rows = []
    for N in Ns:
        for method in methods:
            print(f"[playground] start  N={N} method={method}")
            tic = time.time()
            r = run_one(method, arch=args.arch,
                        N=N, seed=args.seed, alpha=args.alpha,
                        device=device, K=args.K,
                        teacher_epochs=args.teacher_epochs,
                        probe_size=args.probe_size,
                        anchor_scale=args.anchor_scale,
                        anchor_lambda=args.anchor_lambda,
                        anchors_per_class=args.anchors_per_class,
                        within_class_cos=args.within_class_cos,
                        pre_align_epochs=args.pre_align_epochs,
                        weight_mode=args.weight_mode,
                        cache_root=args.cache_root)
            r["wall_sec"] = time.time() - tic
            print(f"[playground] ok     N={N} method={method}  "
                  f"student={r['student_acc']:.4f}  "
                  f"best_t={r['best_teacher']:.4f}  "
                  f"mean_t={r['mean_teacher']:.4f}  "
                  f"wall={r['wall_sec']:.1f}s")
            rows.append(r)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(rows, open(args.out, "w"), indent=2)
    print(f"[playground] done. wrote {args.out}")


if __name__ == "__main__":
    main()
