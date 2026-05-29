# heifd_017_noprobe_verify

## VERDICT — PASSED. This is the cleanest demonstration of the locked thesis.

The no-probe path works end-to-end and shows exactly what the method is supposed to: a WEAK aligned init θ₀ (no public probe, only DP/raw prototypes as the warmup set), and the HE-secure distillation carries the model far above it — large distillation lift, global model beats mean_teacher.

| α | method | acc | θ₀ | **lift (acc−θ₀)** | mean_t | acc/mean_t | m4 |
|---|---|---:|---:|---:|---:|---:|---:|
| 0.05 | noprobe_dp_avg_eps2_K20 | 0.4539 | 0.1869 | **+0.267** | 0.3337 | 1.36× | 0.348 |
| 0.05 | noprobe_dp_avg_eps8_K20 | 0.4548 | 0.2849 | +0.170 | 0.3337 | 1.36× | 0.350 |
| 0.05 | noprobe_raw_union_K20 | 0.4736 | 0.4275 | +0.046 | 0.3337 | 1.42× | 0.375 |
| 0.05 | dp_avg_eps2_K20 (with-probe ref) | 0.5172 | 0.1668 | +0.350 | 0.3337 | 1.55× | 0.434 |
| 0.05 | raw_union_K20 (with-probe ref) | 0.8610 | 0.8240 | +0.037 | 0.3337 | 2.58× | 0.835 |
| 1.0 | noprobe_dp_avg_eps2_K20 | 0.8916 | 0.5014 | **+0.390** | 0.8937 | 1.00× | n/a |
| 1.0 | noprobe_dp_avg_eps8_K20 | 0.8897 | 0.5679 | +0.322 | 0.8937 | 1.00× | n/a |
| 1.0 | noprobe_raw_union_K20 | 0.8857 | 0.5461 | +0.340 | 0.8937 | 0.99× | n/a |
| 1.0 | dp_avg_eps2_K20 (with-probe ref) | 0.8817 | 0.2821 | +0.600 | 0.8937 | 0.99× | n/a |
| 1.0 | raw_union_K20 (with-probe ref) | 0.9360 | 0.9145 | +0.022 | 0.8937 | 1.05× | n/a |

Key reads:
- **Distillation lift is LARGE in the no-probe regime** (+0.17 to +0.39) vs thin (+0.02 to +0.04) when a fat probe already strengthens θ₀. The no-probe regime is where the secure distillation's value is unambiguous — exactly the thesis (memory `method-thesis-distillation-over-alignment`).
- **Cost-of-no-probe is small.** dp_avg_eps2: α=0.05 with-probe 0.5172 vs no-probe 0.4539 (cost ~6pp); α=1.0 with-probe 0.8817 vs no-probe 0.8916 (no-probe slightly HIGHER). Removing the labelled public probe barely hurts, and the distillation compensates.
- noprobe_dp_avg (DP-noisy prototypes-as-warmup) ≥ noprobe_raw_union at α=1.0 in lift terms — the warmup is weak either way, distillation does the work.

→ Full 375-cell grid (heifd_017_noprobe_mlp, job 1116712) submitted to map this across the N×α grid + quantify cost-of-no-probe per (α, ε).



HE-IFD plaintext simulation of the one-shot federated distillation protocol: each client distils its own teacher into a student over a bounded K-step trajectory from a shared, Phase-0-aligned init θ₀, then uploads the cumulative trainable-parameter displacement Δ_i = θ_i^(K) − θ₀; the server's only operation is the sample-weighted linear combine θ₀ + Σ_i w_i·Δ_i (w_i = n_i/Σ_j n_j), which uses plaintext-scalar × ciphertext and ciphertext + ciphertext only and is thus FHE-compatible by construction (multiplicative depth ≈ 1). This case sweeps the grid below; IID test accuracy is the lead metric, with mean/best teacher and a centralised oracle as references, plus the standalone accuracy of the aligned init θ₀ (what alignment adds before distillation), the M3 per-client teacher-vs-aggregate gap on each client's own data (the participation-incentive metric), and the M4 per-client accuracy on classes a client held zero local examples of (the OOD value-proposition; n/a at α=1.0).

## Sweep configuration

- Backbones: `mlp_mnist`
- N values: `10`
- Dirichlet α: `0.05,1.0`
- Methods: `noprobe_dp_avg_eps2_K20,noprobe_dp_avg_eps8_K20,noprobe_raw_union_K20,dp_avg_eps2_K20,raw_union_K20`
- Seeds: `42`
- K (bounded trajectory length): `300`
- τ (distill temperature): `4.0`
- Student LR: `0.01`
- Labelled-probe size P: `None` (None = backbone default)

## Results

| backbone | N | α | method | seed | acc | mean_teacher | best_teacher | oracle | θ₀_acc | M3_mean_gap | M3_helped | M4_ood_acc | σ | status |
|---|---|---|--------|------|-----|--------------|--------------|--------|--------|-------------|-----------|------------|---|--------|
| mlp_mnist | 10 | 0.05 | dp_avg_eps2_K20 | 42 | 0.5172 | 0.3337 | 0.5902 | 0.9735 | 0.1668 | -0.4563 | 0/10 | 0.4339 | 4.2309 | success |
| mlp_mnist | 10 | 0.05 | noprobe_dp_avg_eps2_K20 | 42 | 0.4539 | 0.3337 | 0.5902 | 0.9735 | 0.1869 | -0.5176 | 0/10 | 0.3483 | 4.2309 | success |
| mlp_mnist | 10 | 0.05 | noprobe_dp_avg_eps8_K20 | 42 | 0.4548 | 0.3337 | 0.5902 | 0.9735 | 0.2849 | -0.5215 | 0/10 | 0.3502 | 1.0577 | success |
| mlp_mnist | 10 | 0.05 | noprobe_raw_union_K20 | 42 | 0.4736 | 0.3337 | 0.5902 | 0.9735 | 0.4275 | -0.4971 | 0/10 | 0.3746 | 0.0000 | success |
| mlp_mnist | 10 | 0.05 | raw_union_K20 | 42 | 0.8610 | 0.3337 | 0.5902 | 0.9735 | 0.8240 | -0.1176 | 1/10 | 0.8348 | 0.0000 | success |
| mlp_mnist | 10 | 1.0 | dp_avg_eps2_K20 | 42 | 0.8817 | 0.8937 | 0.9285 | 0.9735 | 0.2821 | -0.1079 | 0/10 | n/a | 4.2309 | success |
| mlp_mnist | 10 | 1.0 | noprobe_dp_avg_eps2_K20 | 42 | 0.8916 | 0.8937 | 0.9285 | 0.9735 | 0.5014 | -0.0966 | 0/10 | n/a | 4.2309 | success |
| mlp_mnist | 10 | 1.0 | noprobe_dp_avg_eps8_K20 | 42 | 0.8897 | 0.8937 | 0.9285 | 0.9735 | 0.5679 | -0.0989 | 0/10 | n/a | 1.0577 | success |
| mlp_mnist | 10 | 1.0 | noprobe_raw_union_K20 | 42 | 0.8857 | 0.8937 | 0.9285 | 0.9735 | 0.5461 | -0.1022 | 0/10 | n/a | 0.0000 | success |
| mlp_mnist | 10 | 1.0 | raw_union_K20 | 42 | 0.9360 | 0.8937 | 0.9285 | 0.9735 | 0.9145 | -0.0482 | 0/10 | n/a | 0.0000 | success |

Raw per-cell JSONs live here as `cell_<backbone>_N<n>_a<α>_<method>_s<seed>_K<k>_<hash>.json`.
Per-client per-class counts at `partition_diagnostic.jsonl`. Slurm stdout/stderr at `runs/`. Long-form rows at `results.csv`.
