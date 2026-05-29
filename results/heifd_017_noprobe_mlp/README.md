# heifd_017_noprobe_mlp

HE-IFD plaintext simulation of the one-shot federated distillation protocol: each client distils its own teacher into a student over a bounded K-step trajectory from a shared, Phase-0-aligned init θ₀, then uploads the cumulative trainable-parameter displacement Δ_i = θ_i^(K) − θ₀; the server's only operation is the sample-weighted linear combine θ₀ + Σ_i w_i·Δ_i (w_i = n_i/Σ_j n_j), which uses plaintext-scalar × ciphertext and ciphertext + ciphertext only and is thus FHE-compatible by construction (multiplicative depth ≈ 1). This case sweeps the grid below; IID test accuracy is the lead metric, with mean/best teacher and a centralised oracle as references, plus the standalone accuracy of the aligned init θ₀ (what alignment adds before distillation), the M3 per-client teacher-vs-aggregate gap on each client's own data (the participation-incentive metric), and the M4 per-client accuracy on classes a client held zero local examples of (the OOD value-proposition; n/a at α=1.0).

## Sweep configuration

- Backbones: `mlp_mnist`
- N values: `1,5,10,20,50`
- Dirichlet α: `0.01,0.05,0.1,0.3,1.0`
- Methods: `noprobe_dp_avg_eps2_K20,noprobe_dp_avg_eps8_K20,noprobe_raw_union_K20,dp_avg_eps2_K20,raw_union_K20`
- Seeds: `42,43,44`
- K (bounded trajectory length): `300`
- τ (distill temperature): `4.0`
- Student LR: `0.01`
- Labelled-probe size P: `None` (None = backbone default)

## Results

| backbone | N | α | method | seed | acc | mean_teacher | best_teacher | oracle | θ₀_acc | M3_mean_gap | M3_helped | M4_ood_acc | σ | status |
|---|---|---|--------|------|-----|--------------|--------------|--------|--------|-------------|-----------|------------|---|--------|
| mlp_mnist | 1 | 0.01 | noprobe_dp_avg_eps2_K20 | 42 | 0.8991 | 0.9711 | 0.9711 | 0.9735 | 0.1764 | -0.0883 | 0/1 | n/a | 4.2309 | success |
| mlp_mnist | 1 | 0.01 | noprobe_raw_union_K20 | 44 | 0.8886 | 0.9635 | 0.9635 | 0.9776 | 0.3388 | -0.0930 | 0/1 | n/a | 0.0000 | success |
| mlp_mnist | 1 | 0.05 | dp_avg_eps2_K20 | 42 | 0.8991 | 0.9711 | 0.9711 | 0.9735 | 0.1764 | -0.0883 | 0/1 | n/a | 4.2309 | success |
| mlp_mnist | 1 | 0.05 | noprobe_dp_avg_eps2_K20 | 43 | 0.9005 | 0.9737 | 0.9737 | 0.9747 | 0.2824 | -0.0897 | 0/1 | n/a | 4.2164 | success |
| mlp_mnist | 1 | 0.1 | dp_avg_eps2_K20 | 43 | 0.8917 | 0.9709 | 0.9709 | 0.9747 | 0.2873 | -0.0942 | 0/1 | n/a | 4.2164 | success |
| mlp_mnist | 1 | 0.1 | noprobe_dp_avg_eps2_K20 | 44 | 0.8959 | 0.9744 | 0.9744 | 0.9776 | 0.1359 | -0.0968 | 0/1 | n/a | 4.2089 | success |
| mlp_mnist | 1 | 0.3 | dp_avg_eps2_K20 | 44 | 0.8959 | 0.9744 | 0.9744 | 0.9776 | 0.1359 | -0.0968 | 0/1 | n/a | 4.2089 | success |
| mlp_mnist | 1 | 0.3 | noprobe_dp_avg_eps8_K20 | 42 | 0.9049 | 0.9696 | 0.9696 | 0.9735 | 0.2787 | -0.0788 | 0/1 | n/a | 1.0577 | success |
| mlp_mnist | 1 | 1.0 | noprobe_dp_avg_eps8_K20 | 43 | 0.8919 | 0.9654 | 0.9654 | 0.9747 | 0.3046 | -0.0906 | 0/1 | n/a | 1.0541 | success |
| mlp_mnist | 1 | 1.0 | raw_union_K20 | 42 | 0.9074 | 0.9717 | 0.9717 | 0.9735 | 0.6913 | -0.0785 | 0/1 | n/a | 0.0000 | success |
| mlp_mnist | 5 | 0.01 | noprobe_dp_avg_eps8_K20 | 44 | n/a | 0.2182 | 0.3985 | 0.9776 | n/a | n/a | n/a | n/a | 0.0000 | FAIL |
| mlp_mnist | 5 | 0.01 | raw_union_K20 | 43 | 0.6359 | 0.2173 | 0.6002 | 0.9747 | 0.7887 | -0.6595 | 0/5 | 0.5951 | 0.0000 | success |
| mlp_mnist | 5 | 0.05 | noprobe_raw_union_K20 | 42 | 0.2879 | 0.3903 | 0.5091 | 0.9735 | 0.2382 | -0.7271 | 0/5 | 0.1747 | 0.0000 | success |
| mlp_mnist | 5 | 0.05 | raw_union_K20 | 44 | 0.7521 | 0.3521 | 0.5610 | 0.9776 | 0.7432 | -0.3357 | 0/5 | 0.7119 | 0.0000 | success |
| mlp_mnist | 5 | 0.1 | noprobe_raw_union_K20 | 43 | 0.4365 | 0.4995 | 0.7011 | 0.9747 | 0.2935 | -0.5228 | 0/5 | 0.1480 | 0.0000 | success |
| mlp_mnist | 5 | 0.3 | noprobe_dp_avg_eps2_K20 | 42 | 0.6855 | 0.7179 | 0.8165 | 0.9735 | 0.3126 | -0.2717 | 0/5 | 0.7881 | 4.2309 | success |
| mlp_mnist | 5 | 0.3 | noprobe_raw_union_K20 | 44 | 0.5730 | 0.7479 | 0.8038 | 0.9776 | 0.3672 | -0.3983 | 0/5 | 0.1879 | 0.0000 | success |
| mlp_mnist | 5 | 1.0 | dp_avg_eps2_K20 | 42 | 0.8742 | 0.9251 | 0.9510 | 0.9735 | 0.3909 | -0.1165 | 0/5 | n/a | 4.2309 | success |
| mlp_mnist | 5 | 1.0 | noprobe_dp_avg_eps2_K20 | 43 | 0.8754 | 0.8800 | 0.9367 | 0.9747 | 0.2713 | -0.1132 | 0/5 | n/a | 4.2164 | success |
| mlp_mnist | 10 | 0.01 | dp_avg_eps2_K20 | 43 | 0.3196 | 0.1835 | 0.2904 | 0.9747 | 0.1677 | -0.6782 | 0/10 | 0.3001 | 4.2164 | success |
| mlp_mnist | 10 | 0.01 | noprobe_dp_avg_eps2_K20 | 44 | 0.2898 | 0.1597 | 0.2014 | 0.9776 | 0.1892 | -0.7747 | 0/10 | 0.2764 | 4.2089 | success |
| mlp_mnist | 10 | 0.05 | dp_avg_eps2_K20 | 44 | 0.4874 | 0.3385 | 0.5152 | 0.9776 | 0.2046 | -0.5588 | 0/10 | 0.4477 | 4.2089 | success |
| mlp_mnist | 10 | 0.05 | noprobe_dp_avg_eps8_K20 | 42 | 0.4548 | 0.3337 | 0.5902 | 0.9735 | 0.2849 | -0.5215 | 0/10 | 0.3502 | 1.0577 | success |
| mlp_mnist | 10 | 0.1 | noprobe_dp_avg_eps8_K20 | 43 | 0.3890 | 0.3316 | 0.4743 | 0.9747 | 0.3009 | -0.6973 | 0/10 | 0.3092 | 1.0541 | success |
| mlp_mnist | 10 | 0.1 | raw_union_K20 | 42 | 0.8979 | 0.4275 | 0.6231 | 0.9735 | 0.8739 | -0.1163 | 0/10 | 0.8981 | 0.0000 | success |
| mlp_mnist | 10 | 0.3 | noprobe_dp_avg_eps8_K20 | 44 | 0.7787 | 0.7126 | 0.8846 | 0.9776 | 0.4835 | -0.2169 | 0/10 | 0.6957 | 1.0522 | success |
| mlp_mnist | 10 | 0.3 | raw_union_K20 | 43 | 0.9243 | 0.7185 | 0.9304 | 0.9747 | 0.8905 | -0.0687 | 0/10 | 0.9177 | 0.0000 | success |
| mlp_mnist | 10 | 1.0 | noprobe_raw_union_K20 | 42 | 0.8857 | 0.8937 | 0.9285 | 0.9735 | 0.5461 | -0.1022 | 0/10 | n/a | 0.0000 | success |
| mlp_mnist | 10 | 1.0 | raw_union_K20 | 44 | 0.9405 | 0.8992 | 0.9203 | 0.9776 | 0.9133 | -0.0478 | 0/10 | n/a | 0.0000 | success |
| mlp_mnist | 20 | 0.01 | noprobe_raw_union_K20 | 43 | n/a | 0.1329 | 0.3037 | 0.9747 | n/a | n/a | n/a | n/a | 0.0000 | FAIL |
| mlp_mnist | 20 | 0.05 | noprobe_dp_avg_eps2_K20 | 42 | n/a | 0.2578 | 0.5272 | 0.9735 | n/a | n/a | n/a | n/a | 0.0000 | FAIL |
| mlp_mnist | 20 | 0.05 | noprobe_raw_union_K20 | 44 | 0.5518 | 0.2730 | 0.5003 | 0.9776 | 0.4401 | -0.4038 | 0/20 | 0.5411 | 0.0000 | success |
| mlp_mnist | 20 | 0.1 | dp_avg_eps2_K20 | 42 | 0.5599 | 0.3979 | 0.6246 | 0.9735 | 0.2889 | -0.4156 | 0/20 | 0.5297 | 4.2309 | success |
| mlp_mnist | 20 | 0.1 | noprobe_dp_avg_eps2_K20 | 43 | 0.6380 | 0.3870 | 0.5646 | 0.9747 | 0.4981 | -0.3365 | 1/20 | 0.5532 | 4.2164 | success |
| mlp_mnist | 20 | 0.3 | dp_avg_eps2_K20 | 43 | 0.7571 | 0.6115 | 0.7931 | 0.9747 | 0.3354 | -0.2311 | 0/20 | 0.7926 | 4.2164 | success |
| mlp_mnist | 20 | 0.3 | noprobe_dp_avg_eps2_K20 | 44 | 0.8051 | 0.6077 | 0.7891 | 0.9776 | 0.4543 | -0.1975 | 0/20 | 0.7220 | 4.2089 | success |
| mlp_mnist | 20 | 1.0 | dp_avg_eps2_K20 | 44 | 0.8691 | 0.8393 | 0.9182 | 0.9776 | 0.2274 | -0.1148 | 0/20 | 0.9656 | 4.2089 | success |
| mlp_mnist | 20 | 1.0 | noprobe_dp_avg_eps8_K20 | 42 | 0.8983 | 0.8596 | 0.9093 | 0.9735 | 0.6629 | -0.0898 | 0/20 | n/a | 1.0577 | success |
| mlp_mnist | 50 | 0.01 | noprobe_dp_avg_eps8_K20 | 43 | n/a | 0.1321 | 0.2998 | 0.9747 | n/a | n/a | n/a | n/a | 0.0000 | FAIL |
| mlp_mnist | 50 | 0.01 | raw_union_K20 | 42 | 0.8826 | 0.1094 | 0.2011 | 0.9735 | 0.8472 | -0.0877 | 0/36 | 0.8823 | 0.0000 | success |
| mlp_mnist | 50 | 0.05 | noprobe_dp_avg_eps8_K20 | 44 | n/a | 0.2005 | 0.5202 | 0.9776 | n/a | n/a | n/a | n/a | 0.0000 | FAIL |
| mlp_mnist | 50 | 0.05 | raw_union_K20 | 43 | 0.9164 | 0.2106 | 0.5674 | 0.9747 | 0.9142 | -0.0166 | 13/50 | 0.9116 | 0.0000 | success |
| mlp_mnist | 50 | 0.1 | noprobe_raw_union_K20 | 42 | 0.8334 | 0.3210 | 0.5280 | 0.9735 | 0.7741 | -0.1049 | 4/50 | 0.8263 | 0.0000 | success |
| mlp_mnist | 50 | 0.1 | raw_union_K20 | 44 | 0.9359 | 0.3003 | 0.5662 | 0.9776 | 0.9336 | -0.0147 | 10/50 | 0.9351 | 0.0000 | success |
| mlp_mnist | 50 | 0.3 | noprobe_raw_union_K20 | 43 | 0.8598 | 0.5160 | 0.7652 | 0.9747 | 0.7629 | -0.1146 | 3/50 | 0.8581 | 0.0000 | success |
| mlp_mnist | 50 | 1.0 | noprobe_dp_avg_eps2_K20 | 42 | 0.8968 | 0.7642 | 0.8844 | 0.9735 | 0.6647 | -0.0858 | 0/50 | n/a | 4.2309 | success |
| mlp_mnist | 50 | 1.0 | noprobe_raw_union_K20 | 44 | 0.8785 | 0.7627 | 0.8686 | 0.9776 | 0.7782 | -0.1010 | 0/50 | n/a | 0.0000 | success |

Raw per-cell JSONs live here as `cell_<backbone>_N<n>_a<α>_<method>_s<seed>_K<k>_<hash>.json`.
Per-client per-class counts at `partition_diagnostic.jsonl`. Slurm stdout/stderr at `runs/`. Long-form rows at `results.csv`.
