# heifd_019_text_verify

HE-IFD plaintext simulation of the one-shot federated distillation protocol: each client distils its own teacher into a student over a bounded K-step trajectory from a shared, Phase-0-aligned init θ₀, then uploads the cumulative trainable-parameter displacement Δ_i = θ_i^(K) − θ₀; the server's only operation is the sample-weighted linear combine θ₀ + Σ_i w_i·Δ_i (w_i = n_i/Σ_j n_j), which uses plaintext-scalar × ciphertext and ciphertext + ciphertext only and is thus FHE-compatible by construction (multiplicative depth ≈ 1). This case sweeps the grid below; IID test accuracy is the lead metric, with mean/best teacher and a centralised oracle as references, plus the standalone accuracy of the aligned init θ₀ (what alignment adds before distillation), the M3 per-client teacher-vs-aggregate gap on each client's own data (the participation-incentive metric), and the M4 per-client accuracy on classes a client held zero local examples of (the OOD value-proposition; n/a at α=1.0).

## Sweep configuration

- Backbones: `roberta_base_agnews,mpnet_st_agnews`
- N values: `10`
- Dirichlet α: `0.05,1.0`
- Methods: `no_phase0,raw_union_K20`
- Seeds: `42`
- K (bounded trajectory length): `100`
- τ (distill temperature): `1.0`
- Student LR: `0.001`
- Labelled-probe size P: `None` (None = backbone default)

## Results

| backbone | N | α | method | seed | acc | mean_teacher | best_teacher | oracle | θ₀_acc | M3_mean_gap | M3_helped | M4_ood_acc | σ | status |
|---|---|---|--------|------|-----|--------------|--------------|--------|--------|-------------|-----------|------------|---|--------|
| mpnet_st_agnews | 10 | 0.05 | no_phase0 | 42 | 0.3351 | 0.2847 | 0.4750 | 0.8976 | 0.2725 | -0.5501 | 0/9 | 0.3541 | 0.0000 | success |
| mpnet_st_agnews | 10 | 0.05 | raw_union_K20 | 42 | 0.3888 | 0.2847 | 0.4750 | 0.8976 | 0.3455 | -0.4292 | 1/9 | 0.3270 | 0.0000 | success |
| mpnet_st_agnews | 10 | 1.0 | no_phase0 | 42 | 0.3238 | 0.6702 | 0.8504 | 0.8976 | 0.2725 | -0.5508 | 0/10 | n/a | 0.0000 | success |
| mpnet_st_agnews | 10 | 1.0 | raw_union_K20 | 42 | 0.8391 | 0.6702 | 0.8504 | 0.8976 | 0.8387 | -0.0337 | 1/10 | n/a | 0.0000 | success |
| roberta_base_agnews | 10 | 0.05 | no_phase0 | 42 | 0.2492 | 0.2735 | 0.4746 | 0.9021 | 0.2500 | -0.5781 | 0/9 | 0.1750 | 0.0000 | success |
| roberta_base_agnews | 10 | 0.05 | raw_union_K20 | 42 | 0.2500 | 0.2735 | 0.4746 | 0.9021 | 0.2500 | -0.5750 | 0/9 | 0.1750 | 0.0000 | success |
| roberta_base_agnews | 10 | 1.0 | no_phase0 | 42 | 0.2624 | 0.6516 | 0.8339 | 0.9021 | 0.2500 | -0.5323 | 0/10 | n/a | 0.0000 | success |
| roberta_base_agnews | 10 | 1.0 | raw_union_K20 | 42 | 0.7830 | 0.6516 | 0.8339 | 0.9021 | 0.5813 | -0.0516 | 1/10 | n/a | 0.0000 | success |

Raw per-cell JSONs live here as `cell_<backbone>_N<n>_a<α>_<method>_s<seed>_K<k>_<hash>.json`.
Per-client per-class counts at `partition_diagnostic.jsonl`. Slurm stdout/stderr at `runs/`. Long-form rows at `results.csv`.
