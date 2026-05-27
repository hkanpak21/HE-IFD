# v1_he-ifd_mlp_mnist_verify

HE-IFD plaintext simulation of the one-shot federated distillation protocol: each client distils its own teacher into a student over a bounded K-step trajectory from a shared, Phase-0-aligned init θ₀, then uploads the cumulative trainable-parameter displacement Δ_i = θ_i^(K) − θ₀; the server's only operation is the sample-weighted linear combine θ₀ + Σ_i w_i·Δ_i (w_i = n_i/Σ_j n_j), which uses plaintext-scalar × ciphertext and ciphertext + ciphertext only and is thus FHE-compatible by construction (multiplicative depth ≈ 1). This case sweeps the grid below; IID test accuracy is the lead metric, with mean/best teacher and a centralised oracle as references, plus the standalone accuracy of the aligned init θ₀ (what alignment adds before distillation), the M3 per-client teacher-vs-aggregate gap on each client's own data (the participation-incentive metric), and the M4 per-client accuracy on classes a client held zero local examples of (the OOD value-proposition; n/a at α=1.0).

## Sweep configuration

- Backbones: `mlp_mnist`
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
| mlp_mnist | 16 | 0.05 | no_phase0 | 42 | 0.4227 | 0.2532 | 0.5412 | 0.9735 | 0.0887 | -0.5650 | 0/16 | 0.3826 | 0.0000 | success |
| mlp_mnist | 16 | 0.05 | raw_union_K20 | 42 | 0.8999 | 0.2532 | 0.5412 | 0.9735 | 0.8688 | -0.0698 | 1/16 | 0.9000 | 0.0000 | success |
| mlp_mnist | 16 | 1.0 | no_phase0 | 42 | 0.8850 | 0.8835 | 0.9230 | 0.9735 | 0.0887 | -0.1041 | 0/16 | n/a | 0.0000 | success |
| mlp_mnist | 16 | 1.0 | raw_union_K20 | 42 | 0.9482 | 0.8835 | 0.9230 | 0.9735 | 0.9321 | -0.0349 | 0/16 | n/a | 0.0000 | success |

Raw per-cell JSONs live here as `cell_<backbone>_N<n>_a<α>_<method>_s<seed>_K<k>_<hash>.json`.
Per-client per-class counts at `partition_diagnostic.jsonl`. Slurm stdout/stderr at `runs/`. Long-form rows at `results.csv`.
