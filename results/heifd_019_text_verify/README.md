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
| mpnet_st_agnews | 10 | 0.05 | no_phase0 | 42 | 0.6820 | 0.4379 | 0.5530 | 0.9062 | 0.2838 | -0.2552 | 0/9 | 0.6827 | 0.0000 | success |
| mpnet_st_agnews | 10 | 0.05 | raw_union_K20 | 42 | 0.8497 | 0.4379 | 0.5530 | 0.9062 | 0.8397 | -0.1014 | 0/9 | 0.8469 | 0.0000 | success |
| mpnet_st_agnews | 10 | 1.0 | no_phase0 | 42 | 0.7308 | 0.8600 | 0.8892 | 0.9062 | 0.2838 | -0.1990 | 0/10 | n/a | 0.0000 | success |
| mpnet_st_agnews | 10 | 1.0 | raw_union_K20 | 42 | 0.8676 | 0.8600 | 0.8892 | 0.9062 | 0.8647 | -0.0657 | 0/10 | n/a | 0.0000 | success |
| roberta_base_agnews | 10 | 0.05 | no_phase0 | 42 | 0.7041 | 0.4542 | 0.5711 | 0.9142 | 0.2036 | -0.3000 | 0/9 | 0.7066 | 0.0000 | success |
| roberta_base_agnews | 10 | 0.05 | raw_union_K20 | 42 | 0.8555 | 0.4542 | 0.5711 | 0.9142 | 0.8442 | -0.1016 | 0/9 | 0.8541 | 0.0000 | success |
| roberta_base_agnews | 10 | 1.0 | no_phase0 | 42 | 0.7583 | 0.8684 | 0.8975 | 0.9142 | 0.2036 | -0.1876 | 0/10 | n/a | 0.0000 | success |
| roberta_base_agnews | 10 | 1.0 | raw_union_K20 | 42 | 0.8739 | 0.8684 | 0.8975 | 0.9142 | 0.8692 | -0.0696 | 0/10 | n/a | 0.0000 | success |

Raw per-cell JSONs live here as `cell_<backbone>_N<n>_a<α>_<method>_s<seed>_K<k>_<hash>.json`.
Per-client per-class counts at `partition_diagnostic.jsonl`. Slurm stdout/stderr at `runs/`. Long-form rows at `results.csv`.
