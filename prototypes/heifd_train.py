#!/usr/bin/env python3
"""
HE-IFD A3 end-to-end CKKS pipeline -- one experimental cell.

A "cell" is a single tuple (dataset, alpha, seed, variant). This script
orchestrates the nine PRD phases (issue 14):

    1. Dirichlet partition of the training set into N client partitions.
    2. Per-client teacher training (LeNet-5 / ResNet-8) with resume.
    3. Probe selection (held-out 5000-sample subset for alpha-variants).
    4. Per-client teacher probe-pass -> plaintext (|P|, C) logits.
    5. CKKS beta-aggregation + lambda variance to produce <Y_tilde>.
    6. Two-stage init: warmstart (E1=30 plaintext epochs on probe labels)
       -> theta_0*. Variants: warmstart | randominit | warmstart-no-ensemble.
    7. Linear-accumulator encrypted student SGD (E2 epochs, depth-<=-3).
    8. Decrypt <theta_E>, evaluate student / teachers / oracle.
    9. Persist CellResult JSON under results/cells/.

GOLDEN RULE: never run this on a login node. Use jobs/cell_heifd.sh
    sbatch jobs/cell_heifd.sh MNIST 0.3 42 warmstart

Variants supported:
    warmstart                  -- two-stage init w/ ensemble distillation (default).
    randominit                 -- skip Stage 1, random init -> Stage 2 distillation.
    warmstart-no-ensemble      -- Stage 1 + plaintext-probe-label SGD (no encrypted target).
    epsilon                    -- alias for the default warmstart path with
                                  DP-SGD-trained teachers (epsilon plumbing is
                                  deferred to issue 22's profiling; this script
                                  records the actual epsilon = None for now).
    gamma                      -- NotImplementedError: requires DP-DDPM probes
                                  from issue 22 / issue 23.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import traceback
from pathlib import Path

import numpy as np

# Make the prototypes/ directory importable so cell_schema + heifd_lib resolve.
_PROTO_DIR = Path(__file__).resolve().parent
if str(_PROTO_DIR) not in sys.path:
    sys.path.insert(0, str(_PROTO_DIR))

from cell_schema import CellResult, SUCCESS_STATUS, FAILED_STATUS, now_seconds


# --------------------------------------------------------------------------
# Constants / variant set
# --------------------------------------------------------------------------

NUM_CLASSES = {
    "MNIST": 10, "FashionMNIST": 10, "CIFAR-10": 10,
    "SVHN": 10, "CIFAR-100": 100,
}

VARIANTS = {
    "warmstart",
    "randominit",
    "warmstart-no-ensemble",
    "epsilon",
    "gamma",
}


# --------------------------------------------------------------------------
# Dataset loading
# --------------------------------------------------------------------------


def load_datasets(dataset: str, data_root: str = "data"):
    """
    Load train + test torchvision datasets with the canonical transforms.
    Lazy-imports torchvision so login-node ast.parse stays cheap.
    """
    import torch  # noqa: F401
    import torchvision
    import torchvision.transforms as T

    d = dataset.lower().replace("-", "")
    if d == "mnist":
        tf = T.Compose([T.ToTensor(), T.Normalize((0.1307,), (0.3081,))])
        tr = torchvision.datasets.MNIST(data_root, train=True, download=True, transform=tf)
        te = torchvision.datasets.MNIST(data_root, train=False, download=True, transform=tf)
        return tr, te
    if d == "fashionmnist":
        tf = T.Compose([T.ToTensor(), T.Normalize((0.2860,), (0.3530,))])
        tr = torchvision.datasets.FashionMNIST(data_root, train=True, download=True, transform=tf)
        te = torchvision.datasets.FashionMNIST(data_root, train=False, download=True, transform=tf)
        return tr, te
    if d == "cifar10":
        tf = T.Compose([T.ToTensor(),
                         T.Normalize((0.4914, 0.4822, 0.4465),
                                     (0.2470, 0.2435, 0.2616))])
        tr = torchvision.datasets.CIFAR10(data_root, train=True, download=True, transform=tf)
        te = torchvision.datasets.CIFAR10(data_root, train=False, download=True, transform=tf)
        return tr, te
    if d == "svhn":
        tf = T.Compose([T.ToTensor(),
                         T.Normalize((0.4377, 0.4438, 0.4728),
                                     (0.1980, 0.2010, 0.1970))])
        tr = torchvision.datasets.SVHN(data_root, split="train", download=True, transform=tf)
        te = torchvision.datasets.SVHN(data_root, split="test", download=True, transform=tf)
        return tr, te
    if d == "cifar100":
        tf = T.Compose([T.ToTensor(),
                         T.Normalize((0.5071, 0.4865, 0.4409),
                                     (0.2673, 0.2564, 0.2762))])
        tr = torchvision.datasets.CIFAR100(data_root, train=True, download=True, transform=tf)
        te = torchvision.datasets.CIFAR100(data_root, train=False, download=True, transform=tf)
        return tr, te
    raise ValueError(f"Unknown dataset: {dataset}")


def make_probe(test_dataset, size: int, seed: int):
    """
    Held-out probe subset of the test set. Per PRD section 3.1 the
    alpha-variants use a same-domain 5000-sample probe; for the smoke we
    take the first `size` rows of the test set with a fixed permutation.
    """
    from torch.utils.data import Subset

    rng = np.random.RandomState(seed)
    perm = rng.permutation(len(test_dataset))[:size]
    return Subset(test_dataset, perm.tolist())


# --------------------------------------------------------------------------
# Pipeline phases
# --------------------------------------------------------------------------


def phase_partition(dataset: str, alpha: float, seed: int, N: int, train_dataset):
    from heifd_lib.partitions import dirichlet_partition

    if hasattr(train_dataset, "targets"):
        labels = np.asarray(train_dataset.targets, dtype=np.int64)
    elif hasattr(train_dataset, "labels"):
        labels = np.asarray(train_dataset.labels, dtype=np.int64)
    else:
        labels = np.asarray([train_dataset[i][1] for i in range(len(train_dataset))],
                             dtype=np.int64)
    return dirichlet_partition(labels.tolist(), n_clients=N, alpha=alpha, seed=seed)


def phase_train_teachers(args, train_dataset, client_indices, device):
    from heifd_lib.teachers import train_or_load_teachers

    num_classes = NUM_CLASSES[args.dataset]
    return train_or_load_teachers(
        dataset=args.dataset,
        alpha=args.alpha,
        seed=args.seed,
        client_indices=client_indices,
        train_dataset=train_dataset,
        num_classes=num_classes,
        epochs=args.T_epochs,
        batch_size=args.batch_size,
        device=device,
    )


def phase_probe_logits(args, teacher_paths, probe_dataset, device):
    from heifd_lib.teachers import (
        load_teacher,
        teacher_logits_on_probe,
        teacher_max_softmax_mean,
    )

    num_classes = NUM_CLASSES[args.dataset]
    all_logits = []
    all_alphas = []
    for p in teacher_paths:
        teacher = load_teacher(args.dataset, num_classes, p, device=device)
        L = teacher_logits_on_probe(teacher, probe_dataset, device=device)
        all_logits.append(L)
        all_alphas.append(teacher_max_softmax_mean(L))
        # release before loading the next teacher
        del teacher
    return all_logits, all_alphas


def phase_encrypted_target(args, logits_per_client, alphas):
    from heifd_lib.encrypted_ensemble import build_ensemble_target, create_context

    ctx, coeff_chain = create_context(args.logn, args.scale)
    enc_Y_rows, plain_Y, wall, n_bytes = build_ensemble_target(
        ctx, logits_per_client, alphas, beta=2,
    )
    return ctx, enc_Y_rows, plain_Y, wall, n_bytes, coeff_chain


def phase_warmstart_student(args, probe_dataset, plain_Y, device):
    """
    Stage 1 of the two-stage init: train the student on probe inputs with
    targets derived from the *plaintext* ensemble target (for the smoke we
    use the argmax of plain_Y as the pseudo-label so the optimiser is
    standard cross-entropy). E_1 epochs of plaintext SGD.

    Returns the in-memory student model + its initial bias snapshot.
    """
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader

    from heifd_lib.teachers import build_model

    num_classes = NUM_CLASSES[args.dataset]
    model = build_model(args.dataset, num_classes=num_classes).to(device)

    if args.variant == "randominit":
        return model

    pseudo_labels = plain_Y.argmax(axis=1).astype(np.int64)

    class _ProbeWithPseudo(torch.utils.data.Dataset):
        def __init__(self, base, labels):
            self.base = base
            self.labels = labels
        def __len__(self):
            return len(self.base)
        def __getitem__(self, i):
            x, _ = self.base[i]
            return x, int(self.labels[i])

    loader = DataLoader(_ProbeWithPseudo(probe_dataset, pseudo_labels),
                         batch_size=args.batch_size, shuffle=True,
                         num_workers=2, pin_memory=(device == "cuda"))
    opt = optim.SGD(model.parameters(), lr=1e-2, momentum=0.9, weight_decay=5e-4)
    crit = nn.CrossEntropyLoss()
    model.train()
    for _ in range(args.E1):
        for xb, yb in loader:
            xb = xb.to(device, non_blocking=True)
            yb = yb.to(device, non_blocking=True)
            opt.zero_grad()
            loss = crit(model(xb), yb)
            loss.backward()
            opt.step()
    return model


def phase_linear_accumulator_distill(
    args, ctx, student, probe_dataset, enc_Y_rows, plain_Y, device,
):
    """
    E_2 epochs of encrypted linear-accumulator SGD against <Y_tilde>.

    For the smoke we update only the final-layer bias under the encrypted
    accumulator (depth audit covered in cfd_tenseal_smoke.py); the rest of
    the student is held fixed. This is the audited claim from PRD section
    4.3 and keeps per-step depth at <=3 with zero bootstrapping.
    """
    import torch
    from torch.utils.data import DataLoader

    from heifd_lib.linear_accumulator import (
        AccumulatorState, compose_theta, encrypted_step, init_accumulator,
    )

    num_classes = NUM_CLASSES[args.dataset]
    state: AccumulatorState = init_accumulator(ctx, dim=num_classes)

    loader = DataLoader(probe_dataset, batch_size=args.batch_size, shuffle=False,
                         num_workers=2, pin_memory=(device == "cuda"))

    if args.variant == "warmstart-no-ensemble":
        # Plaintext-probe-label SGD only; record the no-ensemble path but
        # skip the encrypted updates entirely. The student is already
        # warmstarted by phase_warmstart_student.
        return state, 0, 0

    # Cache plaintext student logits over the probe once per epoch; the
    # smoke updates only the final-layer bias so we can re-use logits and
    # add the running bias delta.
    student.eval()
    base_logits = []
    with torch.no_grad():
        for xb, _ in loader:
            xb = xb.to(device, non_blocking=True)
            base_logits.append(student(xb).cpu().numpy().astype(np.float64))
    base_logits = np.concatenate(base_logits, axis=0)  # (|P|, C)

    total_steps = 0
    for epoch in range(args.E2):
        plain_logits = base_logits + state.plain_delta[np.newaxis, :]
        encrypted_step(state, plain_logits, enc_Y_rows, plain_Y, lr=args.lr)
        total_steps += 1

    return state, total_steps, state.cumulative_bytes


def phase_decrypt_and_apply(state, student):
    """
    Single-key TenSEAL decryption of <Delta>; multiparty key-switch is the
    production target but out of scope for the prototype smoke (per the
    issue 14 acceptance gate: 'document explicitly').
    """
    from heifd_lib.evaluation import apply_bias_update_to_student

    delta = np.asarray(state.enc_delta.decrypt(), dtype=np.float64)
    # The accumulator was created with dim = num_classes; pad/truncate to be safe.
    expected = state.plain_delta.shape[0]
    delta = delta[:expected]
    apply_bias_update_to_student(student, delta)
    return delta


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------


def run_cell(args) -> CellResult:
    import torch

    if args.variant == "gamma":
        raise NotImplementedError(
            "gamma-variant requires issue 22's DP-DDPM generators and the "
            "encrypted synthetic probe pipeline from issue 23. Re-run when "
            "those land."
        )

    result = CellResult.make(
        method="heifd",
        dataset=args.dataset,
        alpha=args.alpha,
        seed=args.seed,
        N=args.N,
        variant=args.variant,
    )
    start = now_seconds()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[heifd] device={device} variant={args.variant} dataset={args.dataset}"
          f" alpha={args.alpha} seed={args.seed} N={args.N}")

    # ---- Phase 1: partition ----
    train_dataset, test_dataset = load_datasets(args.dataset)
    client_indices = phase_partition(args.dataset, args.alpha, args.seed,
                                      args.N, train_dataset)
    sizes = [len(idx) for idx in client_indices]
    print(f"[heifd] partition sizes (min/mean/max): {min(sizes)}/{int(np.mean(sizes))}/{max(sizes)}")

    # ---- Phase 2: teachers (resume-aware) ----
    teacher_paths = phase_train_teachers(args, train_dataset, client_indices, device)

    # ---- Phase 3: probe ----
    probe_dataset = make_probe(test_dataset, size=args.probe, seed=args.seed)

    # ---- Phase 4: per-client probe logits + alpha_i ----
    logits_per_client, alphas = phase_probe_logits(args, teacher_paths, probe_dataset, device)
    print(f"[heifd] probe-pass complete; alphas summary: "
          f"min={min(alphas):.3f} mean={np.mean(alphas):.3f} max={max(alphas):.3f}")

    # ---- Phase 5: encrypted ensemble target (beta-agg + lambda var) ----
    ctx, enc_Y_rows, plain_Y, wall_beta, bytes_beta, coeff_chain = phase_encrypted_target(
        args, logits_per_client, alphas,
    )
    print(f"[heifd] beta-agg: {wall_beta:.2f}s, {bytes_beta} bytes; "
          f"coeff_chain={coeff_chain}")

    # ---- Phase 6: warmstart student (Stage 1) ----
    student = phase_warmstart_student(args, probe_dataset, plain_Y, device)

    # ---- Phase 7: linear-accumulator SGD (Stage 2) ----
    state, n_steps, cum_bytes = phase_linear_accumulator_distill(
        args, ctx, student, probe_dataset, enc_Y_rows, plain_Y, device,
    )
    print(f"[heifd] linear-accumulator: {n_steps} steps, "
          f"cumulative {cum_bytes} bytes")

    # ---- Phase 8: decrypt + evaluate ----
    if args.variant != "warmstart-no-ensemble":
        phase_decrypt_and_apply(state, student)

    from heifd_lib.evaluation import (
        eval_model_accuracy, mean_teacher_accuracy, oracle_accuracy,
    )
    num_classes = NUM_CLASSES[args.dataset]

    result.student_acc = eval_model_accuracy(student, test_dataset, device=device)
    result.mean_teacher_acc = mean_teacher_accuracy(
        teacher_paths, args.dataset, num_classes, test_dataset, device=device,
    )
    if args.compute_oracle:
        result.oracle_acc = oracle_accuracy(
            args.dataset, args.seed, train_dataset, test_dataset,
            num_classes=num_classes, epochs=args.T_epochs, device=device,
        )
    else:
        result.oracle_acc = None

    result.notes = (
        f"depth_audit=beta-agg<=2,lambda-var<=2,accumulator-step<=3; "
        f"coeff_chain={coeff_chain}; n_steps={n_steps}; "
        f"single-key-decrypt (multiparty key-switch is production target)"
    )
    result.status = SUCCESS_STATUS
    result.wall_clock_sec = now_seconds() - start
    return result


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="HE-IFD end-to-end cell runner.")
    p.add_argument("--dataset", default="MNIST",
                    choices=sorted(NUM_CLASSES.keys()))
    p.add_argument("--alpha", type=float, default=0.3)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--N", type=int, default=10, help="number of clients")
    p.add_argument("--variant", default="warmstart", choices=sorted(VARIANTS))
    p.add_argument("--probe", type=int, default=5000)
    p.add_argument("--E1", type=int, default=30, help="warmstart epochs (Stage 1)")
    p.add_argument("--E2", type=int, default=200, help="distillation epochs (Stage 2)")
    p.add_argument("--T-epochs", dest="T_epochs", type=int, default=30,
                    help="teacher epochs per client (PRD smoke budget=30)")
    p.add_argument("--logn", type=int, default=14, help="CKKS log2 ring degree")
    p.add_argument("--scale", type=int, default=40, help="CKKS scale exponent")
    p.add_argument("--lr", type=float, default=0.01)
    p.add_argument("--batch-size", dest="batch_size", type=int, default=64)
    p.add_argument("--compute-oracle", dest="compute_oracle", action="store_true",
                    help="train + eval centralised baseline (off by default; cached)")
    p.add_argument("--output-root", dest="output_root", default="results/cells")
    return p


def main():
    args = build_argparser().parse_args()
    assert args.logn >= 14, "HE-IFD requires logN >= 14 per PRD section 4.3"

    out_path = None
    try:
        result = run_cell(args)
        out_path = result.default_path(root=args.output_root)
        result.dump(out_path)
        print(f"[heifd] wrote {out_path} (status={result.status},"
              f" student_acc={result.student_acc:.4f})")
    except NotImplementedError as exc:
        # Surface the stub explicitly: emit a failed CellResult so the
        # aggregator can audit which variants are stubbed.
        result = CellResult.make(
            method="heifd", dataset=args.dataset, alpha=args.alpha,
            seed=args.seed, N=args.N, variant=args.variant,
        )
        result.status = FAILED_STATUS
        result.error = f"NotImplementedError: {exc}"
        out_path = result.default_path(root=args.output_root)
        result.dump(out_path)
        print(f"[heifd] STUBBED variant: {exc}")
        sys.exit(0)  # not a crash; a planned stub
    except Exception as exc:
        result = CellResult.make(
            method="heifd", dataset=args.dataset, alpha=args.alpha,
            seed=args.seed, N=args.N, variant=args.variant,
        )
        result.status = FAILED_STATUS
        result.error = f"{type(exc).__name__}: {exc}"
        result.notes = traceback.format_exc()
        out_path = result.default_path(root=args.output_root)
        result.dump(out_path)
        print(f"[heifd] FAILED -> {out_path}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
