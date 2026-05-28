# heifd_012_harder_vision_verify

HE-IFD plaintext simulation of the one-shot federated distillation protocol: each client distils its own teacher into a student over a bounded K-step trajectory from a shared, Phase-0-aligned init θ₀, then uploads the cumulative trainable-parameter displacement Δ_i = θ_i^(K) − θ₀; the server's only operation is the sample-weighted linear combine θ₀ + Σ_i w_i·Δ_i (w_i = n_i/Σ_j n_j), which uses plaintext-scalar × ciphertext and ciphertext + ciphertext only and is thus FHE-compatible by construction (multiplicative depth ≈ 1). This case sweeps the grid below; IID test accuracy is the lead metric, with mean/best teacher and a centralised oracle as references, plus the standalone accuracy of the aligned init θ₀ (what alignment adds before distillation), the M3 per-client teacher-vs-aggregate gap on each client's own data (the participation-incentive metric), and the M4 per-client accuracy on classes a client held zero local examples of (the OOD value-proposition; n/a at α=1.0).

## Sweep configuration

- Backbones: `vit_b32_cifar100,resnet18_cifar100`
- N values: `16`
- Dirichlet α: `0.05`
- Methods: `no_phase0,raw_union_K20`
- Seeds: `42`
- K (bounded trajectory length): `100`
- τ (distill temperature): `1.0`
- Student LR: `0.001`
- Labelled-probe size P: `None` (None = backbone default)

## Results

| backbone | N | α | method | seed | acc | mean_teacher | best_teacher | oracle | θ₀_acc | M3_mean_gap | M3_helped | M4_ood_acc | σ | status |
|---|---|---|--------|------|-----|--------------|--------------|--------|--------|-------------|-----------|------------|---|--------|
| resnet18_cifar100 | 16 | 0.05 | no_phase0 | 42 | 0.0172 | 0.1107 | 0.1657 | 0.6661 | 0.0161 | -0.8369 | 0/16 | 0.0163 | 0.0000 | success |
| resnet18_cifar100 | 16 | 0.05 | raw_union_K20 | 42 | 0.5385 | 0.1107 | 0.1657 | 0.6661 | 0.5237 | -0.2955 | 0/16 | 0.5321 | 0.0000 | success |
| vit_b32_cifar100 | 16 | 0.05 | no_phase0 | 42 | 0.0248 | 0.1840 | 0.2890 | 0.8692 | 0.0121 | -0.9540 | 0/16 | 0.0228 | 0.0000 | success |
| vit_b32_cifar100 | 16 | 0.05 | raw_union_K20 | 42 | 0.8305 | 0.1840 | 0.2890 | 0.8692 | 0.8252 | -0.1300 | 0/16 | 0.8283 | 0.0000 | success |

Raw per-cell JSONs live here as `cell_<backbone>_N<n>_a<α>_<method>_s<seed>_K<k>_<hash>.json`.
Per-client per-class counts at `partition_diagnostic.jsonl`. Slurm stdout/stderr at `runs/`. Long-form rows at `results.csv`.
