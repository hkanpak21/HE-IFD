# heifd_mlp_mnist_headline

HE-IFD plaintext simulation of the one-shot federated distillation protocol: each client distils its own teacher into a student over a bounded K-step trajectory from a shared, Phase-0-aligned init θ₀, then uploads the cumulative trainable-parameter displacement Δ_i = θ_i^(K) − θ₀; the server's only operation is the sample-weighted linear combine θ₀ + Σ_i w_i·Δ_i (w_i = n_i/Σ_j n_j), which uses plaintext-scalar × ciphertext and ciphertext + ciphertext only and is thus FHE-compatible by construction (multiplicative depth ≈ 1). This case sweeps the grid below; IID test accuracy is the lead metric, with mean/best teacher and a centralised oracle as references, plus the standalone accuracy of the aligned init θ₀ (what alignment adds before distillation), the M3 per-client teacher-vs-aggregate gap on each client's own data (the participation-incentive metric), and the M4 per-client accuracy on classes a client held zero local examples of (the OOD value-proposition; n/a at α=1.0).

## Sweep configuration

- Backbones: `mlp_mnist`
- N values: `5,10,20,50`
- Dirichlet α: `0.01,0.05,0.1,0.3,1.0`
- Methods: `no_phase0,warmup_only_labelled,labelled_probe_warmup,raw_union_K20,dp_avg_eps2_K20,dp_avg_eps8_K20`
- Seeds: `42,43,44`
- K (bounded trajectory length): `300`
- τ (distill temperature): `4.0`
- Student LR: `0.01`
- Labelled-probe size P: `None` (None = backbone default)

## Results

| backbone | N | α | method | seed | acc | mean_teacher | best_teacher | oracle | θ₀_acc | M3_mean_gap | M3_helped | M4_ood_acc | σ | status |
|---|---|---|--------|------|-----|--------------|--------------|--------|--------|-------------|-----------|------------|---|--------|
| mlp_mnist | 5 | 0.01 | dp_avg_eps8_K20 | 43 | 0.5784 | 0.2173 | 0.6002 | 0.9747 | 0.3172 | -0.8095 | 0/5 | 0.5345 | 1.0541 | success |
| mlp_mnist | 5 | 0.01 | labelled_probe_warmup | 44 | 0.5836 | 0.2182 | 0.3985 | 0.9776 | 0.2927 | -0.6379 | 0/4 | 0.5733 | 0.0000 | success |
| mlp_mnist | 5 | 0.01 | no_phase0 | 42 | 0.3254 | 0.2389 | 0.4043 | 0.9735 | 0.0887 | -0.7570 | 0/5 | 0.2506 | 0.0000 | success |
| mlp_mnist | 5 | 0.05 | dp_avg_eps2_K20 | 44 | 0.4391 | 0.3521 | 0.5610 | 0.9776 | 0.1970 | -0.6980 | 0/5 | 0.3332 | 4.2089 | success |
| mlp_mnist | 5 | 0.05 | labelled_probe_warmup | 42 | 0.4520 | 0.3903 | 0.5091 | 0.9735 | 0.4358 | -0.5846 | 0/5 | 0.3887 | 0.0000 | success |
| mlp_mnist | 5 | 0.1 | dp_avg_eps2_K20 | 42 | 0.5506 | 0.4797 | 0.6834 | 0.9735 | 0.3124 | -0.4957 | 0/5 | 0.3603 | 4.2309 | success |
| mlp_mnist | 5 | 0.1 | warmup_only_labelled | 43 | 0.5519 | 0.4995 | 0.7011 | 0.9747 | 0.5519 | -0.4327 | 0/5 | 0.5001 | 0.0000 | success |
| mlp_mnist | 5 | 0.3 | no_phase0 | 44 | 0.5085 | 0.7479 | 0.8038 | 0.9776 | 0.1006 | -0.4548 | 0/5 | 0.0856 | 0.0000 | success |
| mlp_mnist | 5 | 0.3 | raw_union_K20 | 43 | 0.9046 | 0.7896 | 0.9307 | 0.9747 | 0.8795 | -0.0894 | 0/5 | n/a | 0.0000 | success |
| mlp_mnist | 5 | 1.0 | dp_avg_eps8_K20 | 43 | 0.8583 | 0.8800 | 0.9367 | 0.9747 | 0.3338 | -0.1365 | 0/5 | n/a | 1.0541 | success |
| mlp_mnist | 5 | 1.0 | labelled_probe_warmup | 44 | 0.8723 | 0.8957 | 0.9339 | 0.9776 | 0.2927 | -0.1179 | 0/5 | n/a | 0.0000 | success |
| mlp_mnist | 5 | 1.0 | no_phase0 | 42 | 0.8473 | 0.9251 | 0.9510 | 0.9735 | 0.0887 | -0.1465 | 0/5 | n/a | 0.0000 | success |
| mlp_mnist | 10 | 0.01 | dp_avg_eps2_K20 | 44 | 0.3554 | 0.1597 | 0.2014 | 0.9776 | 0.2757 | -0.7612 | 0/10 | 0.3707 | 4.2089 | success |
| mlp_mnist | 10 | 0.01 | labelled_probe_warmup | 42 | 0.4646 | 0.1824 | 0.4034 | 0.9735 | 0.4358 | -0.6323 | 0/8 | 0.4415 | 0.0000 | success |
| mlp_mnist | 10 | 0.05 | dp_avg_eps2_K20 | 42 | 0.5172 | 0.3337 | 0.5902 | 0.9735 | 0.1668 | -0.4563 | 0/10 | 0.4339 | 4.2309 | success |
| mlp_mnist | 10 | 0.05 | warmup_only_labelled | 43 | 0.5519 | 0.3327 | 0.5603 | 0.9747 | 0.5519 | -0.4556 | 0/10 | 0.6002 | 0.0000 | success |
| mlp_mnist | 10 | 0.1 | no_phase0 | 44 | 0.5884 | 0.4191 | 0.6561 | 0.9776 | 0.1006 | -0.3974 | 0/10 | 0.6373 | 0.0000 | success |
| mlp_mnist | 10 | 0.1 | raw_union_K20 | 43 | 0.8373 | 0.3316 | 0.4743 | 0.9747 | 0.8076 | -0.1720 | 0/10 | 0.8256 | 0.0000 | success |
| mlp_mnist | 10 | 0.3 | dp_avg_eps8_K20 | 43 | 0.7600 | 0.7185 | 0.9304 | 0.9747 | 0.3939 | -0.2328 | 0/10 | 0.8208 | 1.0541 | success |
| mlp_mnist | 10 | 0.3 | labelled_probe_warmup | 44 | 0.8063 | 0.7126 | 0.8846 | 0.9776 | 0.2927 | -0.1882 | 0/10 | 0.7360 | 0.0000 | success |
| mlp_mnist | 10 | 0.3 | no_phase0 | 42 | 0.7286 | 0.6727 | 0.8286 | 0.9735 | 0.0887 | -0.2424 | 0/10 | 0.5793 | 0.0000 | success |
| mlp_mnist | 10 | 1.0 | dp_avg_eps2_K20 | 44 | 0.8230 | 0.8992 | 0.9203 | 0.9776 | 0.1996 | -0.1726 | 0/10 | n/a | 4.2089 | success |
| mlp_mnist | 10 | 1.0 | labelled_probe_warmup | 42 | 0.8879 | 0.8937 | 0.9285 | 0.9735 | 0.4358 | -0.1016 | 0/10 | n/a | 0.0000 | success |
| mlp_mnist | 20 | 0.01 | dp_avg_eps2_K20 | 42 | 0.4065 | 0.1529 | 0.3057 | 0.9735 | 0.2832 | -0.6132 | 0/18 | 0.3999 | 4.2309 | success |
| mlp_mnist | 20 | 0.01 | warmup_only_labelled | 43 | 0.5519 | 0.1329 | 0.3037 | 0.9747 | 0.5519 | -0.4156 | 0/16 | 0.5481 | 0.0000 | success |
| mlp_mnist | 20 | 0.05 | no_phase0 | 44 | 0.4319 | 0.2730 | 0.5003 | 0.9776 | 0.1006 | -0.5195 | 0/20 | 0.4344 | 0.0000 | success |
| mlp_mnist | 20 | 0.05 | raw_union_K20 | 43 | 0.9098 | 0.2643 | 0.4824 | 0.9747 | 0.8696 | -0.0600 | 3/20 | 0.9089 | 0.0000 | success |
| mlp_mnist | 20 | 0.1 | dp_avg_eps8_K20 | 43 | 0.5187 | 0.3870 | 0.5646 | 0.9747 | 0.3329 | -0.4571 | 0/20 | 0.4185 | 1.0541 | success |
| mlp_mnist | 20 | 0.1 | labelled_probe_warmup | 44 | 0.6913 | 0.3700 | 0.5638 | 0.9776 | 0.2927 | -0.3037 | 0/20 | 0.6864 | 0.0000 | success |
| mlp_mnist | 20 | 0.1 | no_phase0 | 42 | 0.4830 | 0.3979 | 0.6246 | 0.9735 | 0.0887 | -0.5002 | 0/20 | 0.4644 | 0.0000 | success |
| mlp_mnist | 20 | 0.3 | dp_avg_eps2_K20 | 44 | 0.7132 | 0.6077 | 0.7891 | 0.9776 | 0.1785 | -0.3016 | 0/20 | 0.6300 | 4.2089 | success |
| mlp_mnist | 20 | 0.3 | labelled_probe_warmup | 42 | 0.7953 | 0.6595 | 0.8515 | 0.9735 | 0.4358 | -0.1852 | 0/20 | 0.7388 | 0.0000 | success |
| mlp_mnist | 20 | 1.0 | dp_avg_eps2_K20 | 42 | 0.8885 | 0.8596 | 0.9093 | 0.9735 | 0.4148 | -0.0990 | 0/20 | n/a | 4.2309 | success |
| mlp_mnist | 20 | 1.0 | warmup_only_labelled | 43 | 0.5519 | 0.8426 | 0.9095 | 0.9747 | 0.5519 | -0.4297 | 0/20 | n/a | 0.0000 | success |
| mlp_mnist | 50 | 0.01 | no_phase0 | 44 | 0.1198 | 0.1177 | 0.2874 | 0.9776 | 0.1006 | -0.7625 | 0/32 | 0.1109 | 0.0000 | success |
| mlp_mnist | 50 | 0.01 | raw_union_K20 | 43 | 0.8863 | 0.1321 | 0.2998 | 0.9747 | 0.8628 | -0.0905 | 0/34 | 0.8850 | 0.0000 | success |
| mlp_mnist | 50 | 0.05 | dp_avg_eps8_K20 | 43 | 0.5076 | 0.2106 | 0.5674 | 0.9747 | 0.4378 | -0.4738 | 2/50 | 0.4619 | 1.0541 | success |
| mlp_mnist | 50 | 0.05 | labelled_probe_warmup | 44 | 0.5326 | 0.2005 | 0.5202 | 0.9776 | 0.2927 | -0.4185 | 3/49 | 0.5116 | 0.0000 | success |
| mlp_mnist | 50 | 0.05 | no_phase0 | 42 | 0.2895 | 0.2029 | 0.4533 | 0.9735 | 0.0887 | -0.6248 | 1/50 | 0.2473 | 0.0000 | success |
| mlp_mnist | 50 | 0.1 | dp_avg_eps2_K20 | 44 | 0.5803 | 0.3003 | 0.5662 | 0.9776 | 0.2934 | -0.3400 | 2/50 | 0.5495 | 4.2089 | success |
| mlp_mnist | 50 | 0.1 | labelled_probe_warmup | 42 | 0.7241 | 0.3210 | 0.5280 | 0.9735 | 0.4358 | -0.2280 | 3/50 | 0.7481 | 0.0000 | success |
| mlp_mnist | 50 | 0.3 | dp_avg_eps2_K20 | 42 | 0.8278 | 0.5626 | 0.8337 | 0.9735 | 0.4704 | -0.1436 | 0/50 | 0.7993 | 4.2309 | success |
| mlp_mnist | 50 | 0.3 | warmup_only_labelled | 43 | 0.5519 | 0.5160 | 0.7652 | 0.9747 | 0.5519 | -0.4275 | 0/50 | 0.5857 | 0.0000 | success |
| mlp_mnist | 50 | 1.0 | no_phase0 | 44 | 0.8433 | 0.7627 | 0.8686 | 0.9776 | 0.1006 | -0.1368 | 0/50 | n/a | 0.0000 | success |
| mlp_mnist | 50 | 1.0 | raw_union_K20 | 43 | 0.9516 | 0.7699 | 0.8809 | 0.9747 | 0.9482 | -0.0131 | 9/50 | 0.9468 | 0.0000 | success |

Raw per-cell JSONs live here as `cell_<backbone>_N<n>_a<α>_<method>_s<seed>_K<k>_<hash>.json`.
Per-client per-class counts at `partition_diagnostic.jsonl`. Slurm stdout/stderr at `runs/`. Long-form rows at `results.csv`.
