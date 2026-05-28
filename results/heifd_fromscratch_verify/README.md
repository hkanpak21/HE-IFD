# heifd_fromscratch_verify

HE-IFD plaintext simulation of the one-shot federated distillation protocol: each client distils its own teacher into a student over a bounded K-step trajectory from a shared, Phase-0-aligned init θ₀, then uploads the cumulative trainable-parameter displacement Δ_i = θ_i^(K) − θ₀; the server's only operation is the sample-weighted linear combine θ₀ + Σ_i w_i·Δ_i (w_i = n_i/Σ_j n_j), which uses plaintext-scalar × ciphertext and ciphertext + ciphertext only and is thus FHE-compatible by construction (multiplicative depth ≈ 1). This case sweeps the grid below; IID test accuracy is the lead metric, with mean/best teacher and a centralised oracle as references, plus the standalone accuracy of the aligned init θ₀ (what alignment adds before distillation), the M3 per-client teacher-vs-aggregate gap on each client's own data (the participation-incentive metric), and the M4 per-client accuracy on classes a client held zero local examples of (the OOD value-proposition; n/a at α=1.0).

## Issue 011 Part 3 CNN-5 reverify — **GATE FAILS** (acc 0.5159 < 0.60)

Sanity gate from issue 011: CIFAR-10 IID `raw_union ≥ 0.60` at α=1.0 with bumped hparams (`teacher_epochs=30, teacher_lr=0.005, oracle_epochs=50, warmup_epochs=10`).

Observed at α=1.0 / `raw_union_K20`: **acc = 0.5159** vs gate **0.60** → **gap −0.085**.

Diagnosis from per-cell numbers (job 1115543, 10m45s):
- **Teachers still under-trained.** `mean_teacher = 0.4587`, `best_teacher = 0.5115` (oracle at 50 epochs = 0.7781). Teachers at 30 epochs are leaving 30+pp on the table relative to what 50 epochs delivers; the bump from 10 → 30 epochs lifted teachers, but not enough.
- **Distillation does add value.** acc 0.5159 − θ₀ 0.4512 = +0.0647 lift; acc ≥ best_teacher (0.5115). The protocol works mechanically — it's just bounded by the teachers' weak signal.
- **No basin-cancellation pathology here** (this is α=1.0 IID — the issue 013 finding was specific to α=0.05). The bound is purely teacher-training compute.

Two reasonable paths forward (orchestrator surfaces both at the HITL touchpoint):
- **(A) Push teacher budget further.** `teacher_epochs=60, teacher_lr=0.005 → 0.001 cosine schedule, oracle_epochs=100`. Each cell ~doubles in wall-clock; under QOS-serial this adds ~20 min per 014 chunk. High likelihood of clearing 0.60, possibly 0.65+.
- **(B) Accept the current ~0.52 baseline.** Document that from-scratch CNN-5/CIFAR-10 is teacher-bound, run 014's full grid with current hparams, and explain in the paper that this regime exists at the protocol's CIFAR-10 ceiling. Faster to land Phase β, weaker headline number.

The α=0.05 cell (0.1911) is also lifted by distillation (θ₀=0.2273 → 0.1911; net distillation hurts at very low α because of basin-cancellation, but the magnitude is small compared to the resnet18 case before issue 010's fix). This is consistent with issue 013's framing.

## Sweep configuration

- Backbones: `lenet_fmnist,cnn5_cifar10`
- N values: `16`
- Dirichlet α: `0.05,1.0`
- Methods: `no_phase0,raw_union_K20`
- Seeds: `42`
- K (bounded trajectory length): `300`
- τ (distill temperature): `4.0`
- Student LR: `0.01`
- Labelled-probe size P: `None` (None = backbone default)

## Results

| backbone | N | α | method | seed | acc | mean_teacher | best_teacher | oracle | θ₀_acc | M3_mean_gap | M3_helped | M4_ood_acc | σ | status |
|---|---|---|--------|------|-----|--------------|--------------|--------|--------|-------------|-----------|------------|---|--------|
| cnn5_cifar10 | 16 | 0.05 | no_phase0 | 42 | 0.1006 | 0.1442 | 0.2646 | 0.7833 | 0.0839 | -0.8005 | 0/16 | 0.0596 | 0.0000 | success |
| cnn5_cifar10 | 16 | 0.05 | raw_union_K20 | 42 | 0.1911 | 0.1441 | 0.2651 | 0.7754 | 0.2273 | -0.7542 | 0/16 | 0.1554 | 0.0000 | success |
| cnn5_cifar10 | 16 | 1.0 | no_phase0 | 42 | 0.3510 | 0.4543 | 0.5182 | 0.7782 | 0.0839 | -0.5932 | 0/16 | n/a | 0.0000 | success |
| cnn5_cifar10 | 16 | 1.0 | raw_union_K20 | 42 | 0.5159 | 0.4587 | 0.5115 | 0.7781 | 0.4512 | -0.4422 | 0/16 | n/a | 0.0000 | success |
| lenet_fmnist | 16 | 0.05 | no_phase0 | 42 | 0.2796 | 0.2285 | 0.5550 | 0.8857 | 0.1000 | -0.5774 | 0/16 | 0.1861 | 0.0000 | success |
| lenet_fmnist | 16 | 0.05 | raw_union_K20 | 42 | 0.6741 | 0.2335 | 0.5892 | 0.8853 | 0.6673 | -0.2821 | 1/16 | 0.6472 | 0.0000 | success |
| lenet_fmnist | 16 | 1.0 | no_phase0 | 42 | 0.6287 | 0.6865 | 0.7671 | 0.8876 | 0.1000 | -0.2246 | 0/16 | n/a | 0.0000 | success |
| lenet_fmnist | 16 | 1.0 | raw_union_K20 | 42 | 0.8058 | 0.6962 | 0.7727 | 0.8822 | 0.7820 | -0.0550 | 2/16 | n/a | 0.0000 | success |

Raw per-cell JSONs live here as `cell_<backbone>_N<n>_a<α>_<method>_s<seed>_K<k>_<hash>.json`.
Per-client per-class counts at `partition_diagnostic.jsonl`. Slurm stdout/stderr at `runs/`. Long-form rows at `results.csv`.
