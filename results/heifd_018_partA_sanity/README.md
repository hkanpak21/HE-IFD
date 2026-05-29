# heifd_018_partA_sanity

HE-IFD plaintext simulation of the one-shot federated distillation protocol: each client distils its own teacher into a student over a bounded K-step trajectory from a shared, Phase-0-aligned init θ₀, then uploads the cumulative trainable-parameter displacement Δ_i = θ_i^(K) − θ₀; the server's only operation is the sample-weighted linear combine θ₀ + Σ_i w_i·Δ_i (w_i = n_i/Σ_j n_j), which uses plaintext-scalar × ciphertext and ciphertext + ciphertext only and is thus FHE-compatible by construction (multiplicative depth ≈ 1). This case sweeps the grid below; IID test accuracy is the lead metric, with mean/best teacher and a centralised oracle as references, plus the standalone accuracy of the aligned init θ₀ (what alignment adds before distillation), the M3 per-client teacher-vs-aggregate gap on each client's own data (the participation-incentive metric), and the M4 per-client accuracy on classes a client held zero local examples of (the OOD value-proposition; n/a at α=1.0).

## Sweep configuration

- Backbones: `gpt2_medium_agnews`
- N values: `1`
- Dirichlet α: `1.0`
- Methods: `no_phase0`
- Seeds: `42`
- K (bounded trajectory length): `1`
- τ (distill temperature): `1.0`
- Student LR: `0.001`
- Labelled-probe size P: `None` (None = backbone default)

## Results

| backbone | N | α | method | seed | acc | mean_teacher | best_teacher | oracle | θ₀_acc | M3_mean_gap | M3_helped | M4_ood_acc | σ | status |
|---|---|---|--------|------|-----|--------------|--------------|--------|--------|-------------|-----------|------------|---|--------|
| bert_large_agnews | 1 | 1.0 | no_phase0 | 42 | 0.3155 | 0.9087 | 0.9087 | 0.9099 | 0.3121 | -0.5896 | 0/1 | n/a | 0.0000 | success |
| gpt2_medium_agnews | 1 | 1.0 | no_phase0 | 42 | 0.2504 | 0.2675 | 0.2675 | 0.4029 | 0.2500 | -0.0194 | 0/1 | n/a | 0.0000 | success |
| vit_l_cifar100 | 1 | 1.0 | no_phase0 | 42 | 0.0125 | 0.8782 | 0.8782 | 0.8762 | 0.0112 | -0.9331 | 0/1 | n/a | 0.0000 | success |

Raw per-cell JSONs live here as `cell_<backbone>_N<n>_a<α>_<method>_s<seed>_K<k>_<hash>.json`.
Per-client per-class counts at `partition_diagnostic.jsonl`. Slurm stdout/stderr at `runs/`. Long-form rows at `results.csv`.
