# heifd_fromscratch_verify

HE-IFD plaintext simulation of the one-shot federated distillation protocol: each client distils its own teacher into a student over a bounded K-step trajectory from a shared, Phase-0-aligned init θ₀, then uploads the cumulative trainable-parameter displacement Δ_i = θ_i^(K) − θ₀; the server's only operation is the sample-weighted linear combine θ₀ + Σ_i w_i·Δ_i (w_i = n_i/Σ_j n_j), which uses plaintext-scalar × ciphertext and ciphertext + ciphertext only and is thus FHE-compatible by construction (multiplicative depth ≈ 1). This case sweeps the grid below; IID test accuracy is the lead metric, with mean/best teacher and a centralised oracle as references, plus the standalone accuracy of the aligned init θ₀ (what alignment adds before distillation), the M3 per-client teacher-vs-aggregate gap on each client's own data (the participation-incentive metric), and the M4 per-client accuracy on classes a client held zero local examples of (the OOD value-proposition; n/a at α=1.0).

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
| cnn5_cifar10 | 16 | 0.05 | no_phase0 | 42 | 0.1514 | 0.1331 | 0.2600 | 0.7451 | 0.0839 | -0.8121 | 0/16 | 0.1338 | 0.0000 | success |
| cnn5_cifar10 | 16 | 0.05 | raw_union_K20 | 42 | 0.1621 | 0.1328 | 0.2595 | 0.7484 | 0.2028 | -0.7564 | 0/16 | 0.1263 | 0.0000 | success |
| cnn5_cifar10 | 16 | 1.0 | no_phase0 | 42 | 0.2555 | 0.4046 | 0.4658 | 0.7483 | 0.0839 | -0.4181 | 0/16 | n/a | 0.0000 | success |
| cnn5_cifar10 | 16 | 1.0 | raw_union_K20 | 42 | 0.4844 | 0.4039 | 0.4636 | 0.7517 | 0.4239 | -0.1969 | 1/16 | n/a | 0.0000 | success |
| lenet_fmnist | 16 | 0.05 | no_phase0 | 42 | 0.2796 | 0.2285 | 0.5550 | 0.8857 | 0.1000 | -0.5774 | 0/16 | 0.1861 | 0.0000 | success |
| lenet_fmnist | 16 | 0.05 | raw_union_K20 | 42 | 0.6741 | 0.2335 | 0.5892 | 0.8853 | 0.6673 | -0.2821 | 1/16 | 0.6472 | 0.0000 | success |
| lenet_fmnist | 16 | 1.0 | no_phase0 | 42 | 0.6287 | 0.6865 | 0.7671 | 0.8876 | 0.1000 | -0.2246 | 0/16 | n/a | 0.0000 | success |
| lenet_fmnist | 16 | 1.0 | raw_union_K20 | 42 | 0.8058 | 0.6962 | 0.7727 | 0.8822 | 0.7820 | -0.0550 | 2/16 | n/a | 0.0000 | success |

Raw per-cell JSONs live here as `cell_<backbone>_N<n>_a<α>_<method>_s<seed>_K<k>_<hash>.json`.
Per-client per-class counts at `partition_diagnostic.jsonl`. Slurm stdout/stderr at `runs/`. Long-form rows at `results.csv`.
