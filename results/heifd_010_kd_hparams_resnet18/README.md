# heifd_010_kd_hparams_resnet18

HE-IFD plaintext simulation of the one-shot federated distillation protocol: each client distils its own teacher into a student over a bounded K-step trajectory from a shared, Phase-0-aligned init θ₀, then uploads the cumulative trainable-parameter displacement Δ_i = θ_i^(K) − θ₀; the server's only operation is the sample-weighted linear combine θ₀ + Σ_i w_i·Δ_i (w_i = n_i/Σ_j n_j), which uses plaintext-scalar × ciphertext and ciphertext + ciphertext only and is thus FHE-compatible by construction (multiplicative depth ≈ 1). This case sweeps the grid below; IID test accuracy is the lead metric, with mean/best teacher and a centralised oracle as references, plus the standalone accuracy of the aligned init θ₀ (what alignment adds before distillation), the M3 per-client teacher-vs-aggregate gap on each client's own data (the participation-incentive metric), and the M4 per-client accuracy on classes a client held zero local examples of (the OOD value-proposition; n/a at α=1.0).

## Sweep configuration

- Backbones: `resnet18_cifar10`
- N values: `10`
- Dirichlet α: `0.05`
- Methods: `raw_union_K20`
- Seeds: `42,43,44`
- K (bounded trajectory length): `300`
- τ (distill temperature): `4.0`
- Student LR: `0.01`
- Labelled-probe size P: `None` (None = backbone default)

## Results

| backbone | N | α | method | seed | acc | mean_teacher | best_teacher | oracle | θ₀_acc | M3_mean_gap | M3_helped | M4_ood_acc | σ | status |
|---|---|---|--------|------|-----|--------------|--------------|--------|--------|-------------|-----------|------------|---|--------|
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 42 | 0.4970 | 0.2297 | 0.4259 | 0.8701 | 0.7176 | -0.5352 | 0/10 | 0.4550 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 42 | 0.5566 | 0.2297 | 0.4259 | 0.8701 | 0.7176 | -0.4358 | 0/10 | 0.5143 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 42 | 0.7066 | 0.2297 | 0.4259 | 0.8701 | 0.7176 | -0.3100 | 0/10 | 0.6879 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 42 | 0.7255 | 0.2297 | 0.4259 | 0.8701 | 0.7176 | -0.2572 | 0/10 | 0.7135 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 42 | 0.5542 | 0.2297 | 0.4259 | 0.8701 | 0.7176 | -0.4375 | 0/10 | 0.5120 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 42 | 0.6269 | 0.2297 | 0.4259 | 0.8701 | 0.7176 | -0.3667 | 0/10 | 0.5942 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 42 | 0.7255 | 0.2297 | 0.4259 | 0.8701 | 0.7176 | -0.2578 | 0/10 | 0.7138 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 42 | 0.7486 | 0.2297 | 0.4259 | 0.8701 | 0.7176 | -0.2030 | 0/10 | 0.7466 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 42 | 0.5316 | 0.2297 | 0.4259 | 0.8701 | 0.7176 | -0.4682 | 0/10 | 0.4895 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 42 | 0.5884 | 0.2297 | 0.4259 | 0.8701 | 0.7176 | -0.4127 | 0/10 | 0.5502 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 42 | 0.7152 | 0.2297 | 0.4259 | 0.8701 | 0.7176 | -0.2830 | 0/10 | 0.6999 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 42 | 0.7388 | 0.2297 | 0.4259 | 0.8701 | 0.7176 | -0.2271 | 0/10 | 0.7313 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 42 | 0.5850 | 0.2297 | 0.4259 | 0.8701 | 0.7176 | -0.4180 | 0/10 | 0.5469 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 42 | 0.6888 | 0.2297 | 0.4259 | 0.8701 | 0.7176 | -0.2805 | 0/10 | 0.6680 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 42 | 0.7397 | 0.2297 | 0.4259 | 0.8701 | 0.7176 | -0.2265 | 0/10 | 0.7315 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 42 | 0.7495 | 0.2297 | 0.4259 | 0.8701 | 0.7176 | -0.1921 | 0/10 | 0.7515 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 43 | 0.3593 | 0.2879 | 0.3571 | 0.8680 | 0.7476 | -0.5683 | 0/10 | 0.2926 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 43 | 0.4337 | 0.2879 | 0.3571 | 0.8680 | 0.7476 | -0.4940 | 0/10 | 0.3676 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 43 | 0.7145 | 0.2879 | 0.3571 | 0.8680 | 0.7476 | -0.2272 | 0/10 | 0.6729 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 43 | 0.7538 | 0.2879 | 0.3571 | 0.8680 | 0.7476 | -0.1938 | 0/10 | 0.7270 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 43 | 0.4366 | 0.2879 | 0.3571 | 0.8680 | 0.7476 | -0.4896 | 0/10 | 0.3706 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 43 | 0.5763 | 0.2879 | 0.3571 | 0.8680 | 0.7476 | -0.3535 | 0/10 | 0.5167 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 43 | 0.7549 | 0.2879 | 0.3571 | 0.8680 | 0.7476 | -0.1927 | 0/10 | 0.7282 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 43 | 0.7630 | 0.2879 | 0.3571 | 0.8680 | 0.7476 | -0.1862 | 0/10 | 0.7431 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 43 | 0.4006 | 0.2879 | 0.3571 | 0.8680 | 0.7476 | -0.5252 | 0/10 | 0.3338 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 43 | 0.4896 | 0.2879 | 0.3571 | 0.8680 | 0.7476 | -0.4361 | 0/10 | 0.4241 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 43 | 0.7395 | 0.2879 | 0.3571 | 0.8680 | 0.7476 | -0.2062 | 0/10 | 0.7065 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 43 | 0.7588 | 0.2879 | 0.3571 | 0.8680 | 0.7476 | -0.1890 | 0/10 | 0.7368 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 43 | 0.4780 | 0.2879 | 0.3571 | 0.8680 | 0.7476 | -0.4431 | 0/10 | 0.4127 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 43 | 0.6777 | 0.2879 | 0.3571 | 0.8680 | 0.7476 | -0.2611 | 0/10 | 0.6343 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 43 | 0.7595 | 0.2879 | 0.3571 | 0.8680 | 0.7476 | -0.1885 | 0/10 | 0.7367 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 43 | 0.7626 | 0.2879 | 0.3571 | 0.8680 | 0.7476 | -0.1864 | 0/10 | 0.7439 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 44 | 0.5130 | 0.2493 | 0.3431 | 0.8667 | 0.7563 | -0.4654 | 0/10 | 0.4509 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 44 | 0.5243 | 0.2493 | 0.3431 | 0.8667 | 0.7563 | -0.4518 | 0/10 | 0.4645 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 44 | 0.7489 | 0.2493 | 0.3431 | 0.8667 | 0.7563 | -0.2166 | 0/10 | 0.7283 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 44 | 0.7639 | 0.2493 | 0.3431 | 0.8667 | 0.7563 | -0.1887 | 0/10 | 0.7473 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 44 | 0.5238 | 0.2493 | 0.3431 | 0.8667 | 0.7563 | -0.4530 | 0/10 | 0.4640 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 44 | 0.6142 | 0.2493 | 0.3431 | 0.8667 | 0.7563 | -0.3516 | 0/10 | 0.5679 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 44 | 0.7642 | 0.2493 | 0.3431 | 0.8667 | 0.7563 | -0.1897 | 0/10 | 0.7477 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 44 | 0.7734 | 0.2493 | 0.3431 | 0.8667 | 0.7563 | -0.1725 | 0/10 | 0.7613 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 44 | 0.5213 | 0.2493 | 0.3431 | 0.8667 | 0.7563 | -0.4580 | 0/10 | 0.4605 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 44 | 0.5519 | 0.2493 | 0.3431 | 0.8667 | 0.7563 | -0.4204 | 0/10 | 0.4952 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 44 | 0.7608 | 0.2493 | 0.3431 | 0.8667 | 0.7563 | -0.2007 | 0/10 | 0.7431 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 44 | 0.7697 | 0.2493 | 0.3431 | 0.8667 | 0.7563 | -0.1803 | 0/10 | 0.7544 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 44 | 0.5477 | 0.2493 | 0.3431 | 0.8667 | 0.7563 | -0.4278 | 0/10 | 0.4904 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 44 | 0.7115 | 0.2493 | 0.3431 | 0.8667 | 0.7563 | -0.2521 | 0/10 | 0.6817 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 44 | 0.7705 | 0.2493 | 0.3431 | 0.8667 | 0.7563 | -0.1807 | 0/10 | 0.7551 | 0.0000 | success |
| resnet18_cifar10 | 10 | 0.05 | raw_union_K20 | 44 | 0.7716 | 0.2493 | 0.3431 | 0.8667 | 0.7563 | -0.1731 | 0/10 | 0.7617 | 0.0000 | success |

Raw per-cell JSONs live here as `cell_<backbone>_N<n>_a<α>_<method>_s<seed>_K<k>_<hash>.json`.
Per-client per-class counts at `partition_diagnostic.jsonl`. Slurm stdout/stderr at `runs/`. Long-form rows at `results.csv`.
