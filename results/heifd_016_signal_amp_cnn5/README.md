# heifd_016_signal_amp_cnn5

HE-IFD plaintext simulation of the one-shot federated distillation protocol: each client distils its own teacher into a student over a bounded K-step trajectory from a shared, Phase-0-aligned init θ₀, then uploads the cumulative trainable-parameter displacement Δ_i = θ_i^(K) − θ₀; the server's only operation is the sample-weighted linear combine θ₀ + Σ_i w_i·Δ_i (w_i = n_i/Σ_j n_j), which uses plaintext-scalar × ciphertext and ciphertext + ciphertext only and is thus FHE-compatible by construction (multiplicative depth ≈ 1). This case sweeps the grid below; IID test accuracy is the lead metric, with mean/best teacher and a centralised oracle as references, plus the standalone accuracy of the aligned init θ₀ (what alignment adds before distillation), the M3 per-client teacher-vs-aggregate gap on each client's own data (the participation-incentive metric), and the M4 per-client accuracy on classes a client held zero local examples of (the OOD value-proposition; n/a at α=1.0).

## Sweep configuration

- Backbones: `cnn5_cifar10`
- N values: `16`
- Dirichlet α: `0.05,1.0`
- Methods: `raw_union_K20,raw_union_K100,synthetic_K100,synthetic_logit_K100`
- Seeds: `42`
- K (bounded trajectory length): `300`
- τ (distill temperature): `4.0`
- Student LR: `0.01`
- Labelled-probe size P: `None` (None = backbone default)

## Results

| backbone | N | α | method | seed | acc | mean_teacher | best_teacher | oracle | θ₀_acc | M3_mean_gap | M3_helped | M4_ood_acc | σ | status |
|---|---|---|--------|------|-----|--------------|--------------|--------|--------|-------------|-----------|------------|---|--------|
| cnn5_cifar10 | 16 | 0.05 | raw_union_K100 | 42 | 0.3022 | 0.1494 | 0.2665 | 0.7824 | 0.4185 | -0.6493 | 0/16 | 0.2531 | 0.0000 | success |
| cnn5_cifar10 | 16 | 0.05 | raw_union_K20 | 42 | 0.2073 | 0.1493 | 0.2666 | 0.7877 | 0.2370 | -0.7564 | 0/16 | 0.1720 | 0.0000 | success |
| cnn5_cifar10 | 16 | 0.05 | synthetic_K100 | 42 | 0.1057 | 0.1495 | 0.2659 | 0.7811 | 0.2601 | -0.8072 | 0/16 | 0.0654 | 0.0000 | success |
| cnn5_cifar10 | 16 | 0.05 | synthetic_logit_K100 | 42 | n/a | 0.1493 | 0.2658 | 0.7831 | n/a | n/a | n/a | n/a | 0.0000 | FAIL |
| cnn5_cifar10 | 16 | 1.0 | raw_union_K100 | 42 | 0.6577 | 0.4787 | 0.5311 | 0.7824 | 0.6896 | -0.3024 | 0/16 | n/a | 0.0000 | success |
| cnn5_cifar10 | 16 | 1.0 | raw_union_K20 | 42 | 0.5194 | 0.4770 | 0.5269 | 0.7753 | 0.4854 | -0.4765 | 0/16 | n/a | 0.0000 | success |
| cnn5_cifar10 | 16 | 1.0 | synthetic_K100 | 42 | 0.3905 | 0.4784 | 0.5272 | 0.7854 | 0.2493 | -0.6079 | 0/16 | n/a | 0.0000 | success |
| cnn5_cifar10 | 16 | 1.0 | synthetic_logit_K100 | 42 | n/a | 0.4773 | 0.5234 | 0.7826 | n/a | n/a | n/a | n/a | 0.0000 | FAIL |

Raw per-cell JSONs live here as `cell_<backbone>_N<n>_a<α>_<method>_s<seed>_K<k>_<hash>.json`.
Per-client per-class counts at `partition_diagnostic.jsonl`. Slurm stdout/stderr at `runs/`. Long-form rows at `results.csv`.
