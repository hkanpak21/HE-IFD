# heifd_011_scope_resnet18

HE-IFD plaintext simulation of the one-shot federated distillation protocol: each client distils its own teacher into a student over a bounded K-step trajectory from a shared, Phase-0-aligned init θ₀, then uploads the cumulative trainable-parameter displacement Δ_i = θ_i^(K) − θ₀; the server's only operation is the sample-weighted linear combine θ₀ + Σ_i w_i·Δ_i (w_i = n_i/Σ_j n_j), which uses plaintext-scalar × ciphertext and ciphertext + ciphertext only and is thus FHE-compatible by construction (multiplicative depth ≈ 1). This case sweeps the grid below; IID test accuracy is the lead metric, with mean/best teacher and a centralised oracle as references, plus the standalone accuracy of the aligned init θ₀ (what alignment adds before distillation), the M3 per-client teacher-vs-aggregate gap on each client's own data (the participation-incentive metric), and the M4 per-client accuracy on classes a client held zero local examples of (the OOD value-proposition; n/a at α=1.0).

## Sweep configuration

- Backbones: `resnet18_cifar10`
- N values: `10`
- Dirichlet α: `0.05`
- Methods: `no_phase0,raw_union_K20`
- Seeds: `42,43,44`
- K (bounded trajectory length): `100`
- τ (distill temperature): `1.0`
- Student LR: `0.001`
- Labelled-probe size P: `None` (None = backbone default)

## Results

| backbone | N | α | method | seed | acc | mean_teacher | best_teacher | oracle | θ₀_acc | M3_mean_gap | M3_helped | M4_ood_acc | σ | status |
|---|---|---|--------|------|-----|--------------|--------------|--------|--------|-------------|-----------|------------|---|--------|
| resnet18_cifar10 | 10 | 0.05 | no_phase0 | 42 | 0.2358 | 0.2297 | 0.4259 | 0.8701 | 0.1112 | -0.8271 | 0/10 | 0.1998 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | no_phase0 | 42 | 0.1705 | 0.2200 | 0.4104 | 0.8722 | 0.1144 | -0.8347 | 0/10 | 0.1496 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | no_phase0 | 42 | 0.2358 | 0.2298 | 0.4253 | 0.8697 | 0.1112 | -0.8270 | 0/10 | 0.1998 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | no_phase0 | 43 | 0.1961 | 0.2879 | 0.3571 | 0.8680 | 0.1046 | -0.7403 | 0/10 | 0.1751 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | no_phase0 | 43 | 0.1407 | 0.2605 | 0.3470 | 0.8669 | 0.1124 | -0.8131 | 0/10 | 0.1580 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | no_phase0 | 43 | 0.1963 | 0.2881 | 0.3572 | 0.8678 | 0.1046 | -0.7403 | 0/10 | 0.1752 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | no_phase0 | 44 | 0.1899 | 0.2493 | 0.3431 | 0.8667 | 0.0998 | -0.7813 | 0/10 | 0.1728 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | no_phase0 | 44 | 0.1787 | 0.2126 | 0.3221 | 0.8694 | 0.0834 | -0.7777 | 0/10 | 0.1935 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | no_phase0 | 44 | 0.1902 | 0.2489 | 0.3433 | 0.8664 | 0.0998 | -0.7794 | 0/10 | 0.1730 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 42 | 0.7486 | 0.2297 | 0.4259 | 0.8701 | 0.7176 | -0.2030 | 0/10 | 0.7466 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 42 | 0.6299 | 0.2200 | 0.4104 | 0.8722 | 0.5822 | -0.3253 | 0/10 | 0.5961 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 42 | 0.7502 | 0.2298 | 0.4253 | 0.8697 | 0.7180 | -0.2025 | 0/10 | 0.7484 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 43 | 0.7630 | 0.2879 | 0.3571 | 0.8680 | 0.7476 | -0.1862 | 0/10 | 0.7431 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 43 | 0.6638 | 0.2605 | 0.3470 | 0.8669 | 0.6402 | -0.2555 | 0/10 | 0.6136 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 43 | 0.7627 | 0.2881 | 0.3572 | 0.8678 | 0.7479 | -0.1859 | 0/10 | 0.7425 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 44 | 0.7734 | 0.2493 | 0.3431 | 0.8667 | 0.7563 | -0.1725 | 0/10 | 0.7613 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 44 | 0.6454 | 0.2126 | 0.3221 | 0.8694 | 0.5989 | -0.2407 | 1/10 | 0.5922 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 44 | 0.7741 | 0.2489 | 0.3433 | 0.8664 | 0.7563 | -0.1711 | 0/10 | 0.7621 | 0.0000 | success |

Raw per-cell JSONs live here as `cell_<backbone>_N<n>_a<α>_<method>_s<seed>_K<k>_<hash>.json`.
Per-client per-class counts at `partition_diagnostic.jsonl`. Slurm stdout/stderr at `runs/`. Long-form rows at `results.csv`.
