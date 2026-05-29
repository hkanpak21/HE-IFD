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
| mlp_mnist | 1 | 0.01 | dp_avg_eps2_K20 | 42 | 0.8991 | 0.9711 | 0.9711 | 0.9735 | 0.1764 | -0.0883 | 0/1 | n/a | 4.2309 | success |
| mlp_mnist | 1 | 0.01 | dp_avg_eps2_K20 | 43 | 0.9005 | 0.9737 | 0.9737 | 0.9747 | 0.2824 | -0.0897 | 0/1 | n/a | 4.2164 | success |
| mlp_mnist | 1 | 0.01 | noprobe_dp_avg_eps2_K20 | 42 | 0.8991 | 0.9711 | 0.9711 | 0.9735 | 0.1764 | -0.0883 | 0/1 | n/a | 4.2309 | success |
| mlp_mnist | 1 | 0.01 | noprobe_dp_avg_eps2_K20 | 43 | 0.9005 | 0.9737 | 0.9737 | 0.9747 | 0.2824 | -0.0897 | 0/1 | n/a | 4.2164 | success |
| mlp_mnist | 1 | 0.01 | noprobe_dp_avg_eps2_K20 | 44 | 0.8926 | 0.9635 | 0.9635 | 0.9776 | 0.1543 | -0.0903 | 0/1 | n/a | 4.2089 | success |
| mlp_mnist | 1 | 0.01 | noprobe_raw_union_K20 | 44 | 0.8886 | 0.9635 | 0.9635 | 0.9776 | 0.3388 | -0.0930 | 0/1 | n/a | 0.0000 | success |
| mlp_mnist | 1 | 0.05 | dp_avg_eps2_K20 | 42 | 0.8991 | 0.9711 | 0.9711 | 0.9735 | 0.1764 | -0.0883 | 0/1 | n/a | 4.2309 | success |
| mlp_mnist | 1 | 0.05 | dp_avg_eps2_K20 | 43 | 0.9005 | 0.9737 | 0.9737 | 0.9747 | 0.2824 | -0.0897 | 0/1 | n/a | 4.2164 | success |
| mlp_mnist | 1 | 0.05 | dp_avg_eps2_K20 | 44 | 0.8926 | 0.9635 | 0.9635 | 0.9776 | 0.1543 | -0.0903 | 0/1 | n/a | 4.2089 | success |
| mlp_mnist | 1 | 0.05 | noprobe_dp_avg_eps2_K20 | 43 | 0.9005 | 0.9737 | 0.9737 | 0.9747 | 0.2824 | -0.0897 | 0/1 | n/a | 4.2164 | success |
| mlp_mnist | 1 | 0.05 | noprobe_dp_avg_eps2_K20 | 44 | 0.8926 | 0.9635 | 0.9635 | 0.9776 | 0.1543 | -0.0903 | 0/1 | n/a | 4.2089 | success |
| mlp_mnist | 1 | 0.05 | noprobe_dp_avg_eps8_K20 | 42 | 0.8954 | 0.9711 | 0.9711 | 0.9735 | 0.2967 | -0.0900 | 0/1 | n/a | 1.0577 | success |
| mlp_mnist | 1 | 0.1 | dp_avg_eps2_K20 | 43 | 0.8917 | 0.9709 | 0.9709 | 0.9747 | 0.2873 | -0.0942 | 0/1 | n/a | 4.2164 | success |
| mlp_mnist | 1 | 0.1 | dp_avg_eps2_K20 | 44 | 0.8959 | 0.9744 | 0.9744 | 0.9776 | 0.1359 | -0.0968 | 0/1 | n/a | 4.2089 | success |
| mlp_mnist | 1 | 0.1 | noprobe_dp_avg_eps2_K20 | 44 | 0.8959 | 0.9744 | 0.9744 | 0.9776 | 0.1359 | -0.0968 | 0/1 | n/a | 4.2089 | success |
| mlp_mnist | 1 | 0.1 | noprobe_dp_avg_eps8_K20 | 42 | 0.9036 | 0.9702 | 0.9702 | 0.9735 | 0.2642 | -0.0836 | 0/1 | n/a | 1.0577 | success |
| mlp_mnist | 1 | 0.1 | noprobe_dp_avg_eps8_K20 | 43 | 0.8895 | 0.9709 | 0.9709 | 0.9747 | 0.3389 | -0.0968 | 0/1 | n/a | 1.0541 | success |
| mlp_mnist | 1 | 0.1 | raw_union_K20 | 42 | 0.9104 | 0.9702 | 0.9702 | 0.9735 | 0.6899 | -0.0766 | 0/1 | n/a | 0.0000 | success |
| mlp_mnist | 1 | 0.3 | dp_avg_eps2_K20 | 44 | 0.8959 | 0.9744 | 0.9744 | 0.9776 | 0.1359 | -0.0968 | 0/1 | n/a | 4.2089 | success |
| mlp_mnist | 1 | 0.3 | noprobe_dp_avg_eps8_K20 | 42 | 0.9049 | 0.9696 | 0.9696 | 0.9735 | 0.2787 | -0.0788 | 0/1 | n/a | 1.0577 | success |
| mlp_mnist | 1 | 0.3 | noprobe_dp_avg_eps8_K20 | 43 | 0.8999 | 0.9694 | 0.9694 | 0.9747 | 0.3727 | -0.0901 | 0/1 | n/a | 1.0541 | success |
| mlp_mnist | 1 | 0.3 | noprobe_dp_avg_eps8_K20 | 44 | 0.8941 | 0.9744 | 0.9744 | 0.9776 | 0.2421 | -0.0992 | 0/1 | n/a | 1.0522 | success |
| mlp_mnist | 1 | 0.3 | raw_union_K20 | 42 | 0.9114 | 0.9696 | 0.9696 | 0.9735 | 0.6662 | -0.0716 | 0/1 | n/a | 0.0000 | success |
| mlp_mnist | 1 | 0.3 | raw_union_K20 | 43 | 0.9017 | 0.9694 | 0.9694 | 0.9747 | 0.6336 | -0.0852 | 0/1 | n/a | 0.0000 | success |
| mlp_mnist | 1 | 1.0 | noprobe_dp_avg_eps8_K20 | 43 | 0.8919 | 0.9654 | 0.9654 | 0.9747 | 0.3046 | -0.0906 | 0/1 | n/a | 1.0541 | success |
| mlp_mnist | 1 | 1.0 | noprobe_dp_avg_eps8_K20 | 44 | 0.8992 | 0.9726 | 0.9726 | 0.9776 | 0.2956 | -0.0948 | 0/1 | n/a | 1.0522 | success |
| mlp_mnist | 1 | 1.0 | noprobe_raw_union_K20 | 42 | 0.8947 | 0.9717 | 0.9717 | 0.9735 | 0.4658 | -0.0930 | 0/1 | n/a | 0.0000 | success |
| mlp_mnist | 1 | 1.0 | raw_union_K20 | 42 | 0.9074 | 0.9717 | 0.9717 | 0.9735 | 0.6913 | -0.0785 | 0/1 | n/a | 0.0000 | success |
| mlp_mnist | 1 | 1.0 | raw_union_K20 | 43 | 0.9057 | 0.9654 | 0.9654 | 0.9747 | 0.5547 | -0.0775 | 0/1 | n/a | 0.0000 | success |
| mlp_mnist | 1 | 1.0 | raw_union_K20 | 44 | 0.9109 | 0.9726 | 0.9726 | 0.9776 | 0.6535 | -0.0808 | 0/1 | n/a | 0.0000 | success |
| mlp_mnist | 5 | 0.01 | noprobe_dp_avg_eps8_K20 | 44 | n/a | 0.2182 | 0.3985 | 0.9776 | n/a | n/a | n/a | n/a | 0.0000 | FAIL |
| mlp_mnist | 5 | 0.01 | noprobe_raw_union_K20 | 42 | 0.2897 | 0.2389 | 0.4043 | 0.9735 | 0.2271 | -0.7707 | 0/5 | 0.2124 | 0.0000 | success |
| mlp_mnist | 5 | 0.01 | noprobe_raw_union_K20 | 43 | 0.5699 | 0.2173 | 0.6002 | 0.9747 | 0.2217 | -0.8109 | 0/5 | 0.5260 | 0.0000 | success |
| mlp_mnist | 5 | 0.01 | raw_union_K20 | 43 | 0.6359 | 0.2173 | 0.6002 | 0.9747 | 0.7887 | -0.6595 | 0/5 | 0.5951 | 0.0000 | success |
| mlp_mnist | 5 | 0.01 | raw_union_K20 | 44 | 0.7495 | 0.2182 | 0.3985 | 0.9776 | 0.6192 | -0.3799 | 0/4 | 0.7412 | 0.0000 | success |
| mlp_mnist | 5 | 0.05 | noprobe_dp_avg_eps2_K20 | 42 | 0.3074 | 0.3903 | 0.5091 | 0.9735 | 0.1848 | -0.7013 | 0/5 | 0.1984 | 4.2309 | success |
| mlp_mnist | 5 | 0.05 | noprobe_raw_union_K20 | 42 | 0.2879 | 0.3903 | 0.5091 | 0.9735 | 0.2382 | -0.7271 | 0/5 | 0.1747 | 0.0000 | success |
| mlp_mnist | 5 | 0.05 | noprobe_raw_union_K20 | 43 | 0.5711 | 0.2590 | 0.6683 | 0.9747 | 0.3107 | -0.8068 | 0/5 | 0.4365 | 0.0000 | success |
| mlp_mnist | 5 | 0.05 | noprobe_raw_union_K20 | 44 | 0.4554 | 0.3521 | 0.5610 | 0.9776 | 0.3974 | -0.6913 | 0/5 | 0.3517 | 0.0000 | success |
| mlp_mnist | 5 | 0.05 | raw_union_K20 | 44 | 0.7521 | 0.3521 | 0.5610 | 0.9776 | 0.7432 | -0.3357 | 0/5 | 0.7119 | 0.0000 | success |
| mlp_mnist | 5 | 0.1 | dp_avg_eps2_K20 | 42 | 0.5506 | 0.4797 | 0.6834 | 0.9735 | 0.3124 | -0.4957 | 0/5 | 0.3603 | 4.2309 | success |
| mlp_mnist | 5 | 0.1 | noprobe_dp_avg_eps2_K20 | 42 | 0.5926 | 0.4797 | 0.6834 | 0.9735 | 0.2360 | -0.4592 | 0/5 | 0.3677 | 4.2309 | success |
| mlp_mnist | 5 | 0.1 | noprobe_dp_avg_eps2_K20 | 43 | 0.4144 | 0.4995 | 0.7011 | 0.9747 | 0.2026 | -0.5333 | 0/5 | 0.1322 | 4.2164 | success |
| mlp_mnist | 5 | 0.1 | noprobe_raw_union_K20 | 43 | 0.4365 | 0.4995 | 0.7011 | 0.9747 | 0.2935 | -0.5228 | 0/5 | 0.1480 | 0.0000 | success |
| mlp_mnist | 5 | 0.1 | noprobe_raw_union_K20 | 44 | 0.5076 | 0.4397 | 0.5485 | 0.9776 | 0.3406 | -0.6003 | 0/5 | 0.4655 | 0.0000 | success |
| mlp_mnist | 5 | 0.3 | dp_avg_eps2_K20 | 42 | 0.6838 | 0.7179 | 0.8165 | 0.9735 | 0.2960 | -0.2716 | 0/5 | 0.7349 | 4.2309 | success |
| mlp_mnist | 5 | 0.3 | dp_avg_eps2_K20 | 43 | 0.7741 | 0.7896 | 0.9307 | 0.9747 | 0.2460 | -0.2139 | 0/5 | n/a | 4.2164 | success |
| mlp_mnist | 5 | 0.3 | noprobe_dp_avg_eps2_K20 | 42 | 0.6855 | 0.7179 | 0.8165 | 0.9735 | 0.3126 | -0.2717 | 0/5 | 0.7881 | 4.2309 | success |
| mlp_mnist | 5 | 0.3 | noprobe_dp_avg_eps2_K20 | 43 | 0.7718 | 0.7896 | 0.9307 | 0.9747 | 0.2496 | -0.2131 | 0/5 | n/a | 4.2164 | success |
| mlp_mnist | 5 | 0.3 | noprobe_dp_avg_eps2_K20 | 44 | 0.5459 | 0.7479 | 0.8038 | 0.9776 | 0.2247 | -0.4180 | 0/5 | 0.2557 | 4.2089 | success |
| mlp_mnist | 5 | 0.3 | noprobe_raw_union_K20 | 44 | 0.5730 | 0.7479 | 0.8038 | 0.9776 | 0.3672 | -0.3983 | 0/5 | 0.1879 | 0.0000 | success |
| mlp_mnist | 5 | 1.0 | dp_avg_eps2_K20 | 42 | 0.8742 | 0.9251 | 0.9510 | 0.9735 | 0.3909 | -0.1165 | 0/5 | n/a | 4.2309 | success |
| mlp_mnist | 5 | 1.0 | dp_avg_eps2_K20 | 43 | 0.8703 | 0.8800 | 0.9367 | 0.9747 | 0.2200 | -0.1192 | 0/5 | n/a | 4.2164 | success |
| mlp_mnist | 5 | 1.0 | dp_avg_eps2_K20 | 44 | 0.8195 | 0.8957 | 0.9339 | 0.9776 | 0.2008 | -0.1734 | 0/5 | n/a | 4.2089 | success |
| mlp_mnist | 5 | 1.0 | noprobe_dp_avg_eps2_K20 | 43 | 0.8754 | 0.8800 | 0.9367 | 0.9747 | 0.2713 | -0.1132 | 0/5 | n/a | 4.2164 | success |
| mlp_mnist | 5 | 1.0 | noprobe_dp_avg_eps2_K20 | 44 | 0.8146 | 0.8957 | 0.9339 | 0.9776 | 0.1781 | -0.1764 | 0/5 | n/a | 4.2089 | success |
| mlp_mnist | 5 | 1.0 | noprobe_dp_avg_eps8_K20 | 42 | 0.8631 | 0.9251 | 0.9510 | 0.9735 | 0.3966 | -0.1294 | 0/5 | n/a | 1.0577 | success |
| mlp_mnist | 10 | 0.01 | dp_avg_eps2_K20 | 43 | 0.3196 | 0.1835 | 0.2904 | 0.9747 | 0.1677 | -0.6782 | 0/10 | 0.3001 | 4.2164 | success |
| mlp_mnist | 10 | 0.01 | dp_avg_eps2_K20 | 44 | 0.3554 | 0.1597 | 0.2014 | 0.9776 | 0.2757 | -0.7612 | 0/10 | 0.3707 | 4.2089 | success |
| mlp_mnist | 10 | 0.01 | noprobe_dp_avg_eps2_K20 | 44 | 0.2898 | 0.1597 | 0.2014 | 0.9776 | 0.1892 | -0.7747 | 0/10 | 0.2764 | 4.2089 | success |
| mlp_mnist | 10 | 0.01 | noprobe_dp_avg_eps8_K20 | 42 | n/a | 0.1824 | 0.4034 | 0.9735 | n/a | n/a | n/a | n/a | 0.0000 | FAIL |
| mlp_mnist | 10 | 0.01 | noprobe_dp_avg_eps8_K20 | 43 | 0.3317 | 0.1835 | 0.2904 | 0.9747 | 0.1344 | -0.6468 | 0/10 | 0.2799 | 1.0541 | success |
| mlp_mnist | 10 | 0.01 | raw_union_K20 | 42 | 0.7905 | 0.1824 | 0.4034 | 0.9735 | 0.7807 | -0.2530 | 0/8 | 0.7806 | 0.0000 | success |
| mlp_mnist | 10 | 0.05 | dp_avg_eps2_K20 | 44 | 0.4874 | 0.3385 | 0.5152 | 0.9776 | 0.2046 | -0.5588 | 0/10 | 0.4477 | 4.2089 | success |
| mlp_mnist | 10 | 0.05 | noprobe_dp_avg_eps8_K20 | 42 | 0.4548 | 0.3337 | 0.5902 | 0.9735 | 0.2849 | -0.5215 | 0/10 | 0.3502 | 1.0577 | success |
| mlp_mnist | 10 | 0.05 | noprobe_dp_avg_eps8_K20 | 43 | 0.5384 | 0.3327 | 0.5603 | 0.9747 | 0.2277 | -0.3959 | 0/10 | 0.4644 | 1.0541 | success |
| mlp_mnist | 10 | 0.05 | noprobe_dp_avg_eps8_K20 | 44 | 0.4565 | 0.3385 | 0.5152 | 0.9776 | 0.2956 | -0.5782 | 0/10 | 0.3629 | 1.0522 | success |
| mlp_mnist | 10 | 0.05 | raw_union_K20 | 42 | 0.8610 | 0.3337 | 0.5902 | 0.9735 | 0.8240 | -0.1176 | 1/10 | 0.8348 | 0.0000 | success |
| mlp_mnist | 10 | 0.05 | raw_union_K20 | 43 | 0.8539 | 0.3327 | 0.5603 | 0.9747 | 0.7895 | -0.1241 | 0/10 | 0.8417 | 0.0000 | success |
| mlp_mnist | 10 | 0.1 | noprobe_dp_avg_eps8_K20 | 43 | 0.3890 | 0.3316 | 0.4743 | 0.9747 | 0.3009 | -0.6973 | 0/10 | 0.3092 | 1.0541 | success |
| mlp_mnist | 10 | 0.1 | noprobe_dp_avg_eps8_K20 | 44 | 0.5674 | 0.4191 | 0.6561 | 0.9776 | 0.4281 | -0.3692 | 0/10 | 0.5671 | 1.0522 | success |
| mlp_mnist | 10 | 0.1 | noprobe_raw_union_K20 | 42 | 0.6059 | 0.4275 | 0.6231 | 0.9735 | 0.4410 | -0.4883 | 0/10 | 0.5725 | 0.0000 | success |
| mlp_mnist | 10 | 0.1 | raw_union_K20 | 42 | 0.8979 | 0.4275 | 0.6231 | 0.9735 | 0.8739 | -0.1163 | 0/10 | 0.8981 | 0.0000 | success |
| mlp_mnist | 10 | 0.1 | raw_union_K20 | 43 | 0.8373 | 0.3316 | 0.4743 | 0.9747 | 0.8076 | -0.1720 | 0/10 | 0.8256 | 0.0000 | success |
| mlp_mnist | 10 | 0.1 | raw_union_K20 | 44 | 0.8943 | 0.4191 | 0.6561 | 0.9776 | 0.8651 | -0.0909 | 1/10 | 0.8952 | 0.0000 | success |
| mlp_mnist | 10 | 0.3 | noprobe_dp_avg_eps8_K20 | 44 | 0.7787 | 0.7126 | 0.8846 | 0.9776 | 0.4835 | -0.2169 | 0/10 | 0.6957 | 1.0522 | success |
| mlp_mnist | 10 | 0.3 | noprobe_raw_union_K20 | 42 | 0.7927 | 0.6727 | 0.8286 | 0.9735 | 0.5798 | -0.1851 | 0/10 | 0.6851 | 0.0000 | success |
| mlp_mnist | 10 | 0.3 | noprobe_raw_union_K20 | 43 | 0.8164 | 0.7185 | 0.9304 | 0.9747 | 0.6087 | -0.1852 | 0/10 | 0.8319 | 0.0000 | success |
| mlp_mnist | 10 | 0.3 | raw_union_K20 | 43 | 0.9243 | 0.7185 | 0.9304 | 0.9747 | 0.8905 | -0.0687 | 0/10 | 0.9177 | 0.0000 | success |
| mlp_mnist | 10 | 0.3 | raw_union_K20 | 44 | 0.9251 | 0.7126 | 0.8846 | 0.9776 | 0.8969 | -0.0696 | 0/10 | 0.9153 | 0.0000 | success |
| mlp_mnist | 10 | 1.0 | noprobe_dp_avg_eps2_K20 | 42 | 0.8916 | 0.8937 | 0.9285 | 0.9735 | 0.5014 | -0.0966 | 0/10 | n/a | 4.2309 | success |
| mlp_mnist | 10 | 1.0 | noprobe_raw_union_K20 | 42 | 0.8857 | 0.8937 | 0.9285 | 0.9735 | 0.5461 | -0.1022 | 0/10 | n/a | 0.0000 | success |
| mlp_mnist | 10 | 1.0 | noprobe_raw_union_K20 | 43 | 0.8888 | 0.8886 | 0.9307 | 0.9747 | 0.7051 | -0.1008 | 0/10 | n/a | 0.0000 | success |
| mlp_mnist | 10 | 1.0 | noprobe_raw_union_K20 | 44 | 0.8507 | 0.8992 | 0.9203 | 0.9776 | 0.5765 | -0.1419 | 0/10 | n/a | 0.0000 | success |
| mlp_mnist | 10 | 1.0 | raw_union_K20 | 44 | 0.9405 | 0.8992 | 0.9203 | 0.9776 | 0.9133 | -0.0478 | 0/10 | n/a | 0.0000 | success |
| mlp_mnist | 20 | 0.01 | dp_avg_eps2_K20 | 42 | 0.4065 | 0.1529 | 0.3057 | 0.9735 | 0.2832 | -0.6132 | 0/18 | 0.3999 | 4.2309 | success |
| mlp_mnist | 20 | 0.01 | noprobe_dp_avg_eps2_K20 | 42 | n/a | 0.1529 | 0.3057 | 0.9735 | n/a | n/a | n/a | n/a | 0.0000 | FAIL |
| mlp_mnist | 20 | 0.01 | noprobe_dp_avg_eps2_K20 | 43 | n/a | 0.1329 | 0.3037 | 0.9747 | n/a | n/a | n/a | n/a | 0.0000 | FAIL |
| mlp_mnist | 20 | 0.01 | noprobe_raw_union_K20 | 43 | n/a | 0.1329 | 0.3037 | 0.9747 | n/a | n/a | n/a | n/a | 0.0000 | FAIL |
| mlp_mnist | 20 | 0.01 | noprobe_raw_union_K20 | 44 | n/a | 0.1353 | 0.2083 | 0.9776 | n/a | n/a | n/a | n/a | 0.0000 | FAIL |
| mlp_mnist | 20 | 0.05 | dp_avg_eps2_K20 | 42 | 0.3106 | 0.2578 | 0.5272 | 0.9735 | 0.2581 | -0.7537 | 0/19 | 0.2833 | 4.2309 | success |
| mlp_mnist | 20 | 0.05 | dp_avg_eps2_K20 | 43 | 0.5063 | 0.2643 | 0.4824 | 0.9747 | 0.2489 | -0.4675 | 0/20 | 0.4922 | 4.2164 | success |
| mlp_mnist | 20 | 0.05 | noprobe_dp_avg_eps2_K20 | 42 | n/a | 0.2578 | 0.5272 | 0.9735 | n/a | n/a | n/a | n/a | 0.0000 | FAIL |
| mlp_mnist | 20 | 0.05 | noprobe_dp_avg_eps2_K20 | 43 | 0.6415 | 0.2643 | 0.4824 | 0.9747 | 0.3506 | -0.3189 | 1/20 | 0.6223 | 4.2164 | success |
| mlp_mnist | 20 | 0.05 | noprobe_dp_avg_eps2_K20 | 44 | 0.5543 | 0.2730 | 0.5003 | 0.9776 | 0.3025 | -0.4026 | 0/20 | 0.5462 | 4.2089 | success |
| mlp_mnist | 20 | 0.05 | noprobe_raw_union_K20 | 44 | 0.5518 | 0.2730 | 0.5003 | 0.9776 | 0.4401 | -0.4038 | 0/20 | 0.5411 | 0.0000 | success |
| mlp_mnist | 20 | 0.1 | dp_avg_eps2_K20 | 42 | 0.5599 | 0.3979 | 0.6246 | 0.9735 | 0.2889 | -0.4156 | 0/20 | 0.5297 | 4.2309 | success |
| mlp_mnist | 20 | 0.1 | dp_avg_eps2_K20 | 43 | 0.5299 | 0.3870 | 0.5646 | 0.9747 | 0.2465 | -0.4434 | 0/20 | 0.4394 | 4.2164 | success |
| mlp_mnist | 20 | 0.1 | dp_avg_eps2_K20 | 44 | 0.6833 | 0.3700 | 0.5638 | 0.9776 | 0.1935 | -0.3084 | 0/20 | 0.6697 | 4.2089 | success |
| mlp_mnist | 20 | 0.1 | noprobe_dp_avg_eps2_K20 | 43 | 0.6380 | 0.3870 | 0.5646 | 0.9747 | 0.4981 | -0.3365 | 1/20 | 0.5532 | 4.2164 | success |
| mlp_mnist | 20 | 0.1 | noprobe_dp_avg_eps2_K20 | 44 | 0.7491 | 0.3700 | 0.5638 | 0.9776 | 0.4394 | -0.2350 | 0/20 | 0.7306 | 4.2089 | success |
| mlp_mnist | 20 | 0.1 | noprobe_dp_avg_eps8_K20 | 42 | 0.6386 | 0.3979 | 0.6246 | 0.9735 | 0.5843 | -0.3303 | 0/20 | 0.6031 | 1.0577 | success |
| mlp_mnist | 20 | 0.3 | dp_avg_eps2_K20 | 43 | 0.7571 | 0.6115 | 0.7931 | 0.9747 | 0.3354 | -0.2311 | 0/20 | 0.7926 | 4.2164 | success |
| mlp_mnist | 20 | 0.3 | dp_avg_eps2_K20 | 44 | 0.7132 | 0.6077 | 0.7891 | 0.9776 | 0.1785 | -0.3016 | 0/20 | 0.6300 | 4.2089 | success |
| mlp_mnist | 20 | 0.3 | noprobe_dp_avg_eps2_K20 | 44 | 0.8051 | 0.6077 | 0.7891 | 0.9776 | 0.4543 | -0.1975 | 0/20 | 0.7220 | 4.2089 | success |
| mlp_mnist | 20 | 0.3 | noprobe_dp_avg_eps8_K20 | 42 | 0.8405 | 0.6595 | 0.8515 | 0.9735 | 0.7656 | -0.1500 | 0/20 | 0.8162 | 1.0577 | success |
| mlp_mnist | 20 | 0.3 | noprobe_dp_avg_eps8_K20 | 43 | 0.8496 | 0.6115 | 0.7931 | 0.9747 | 0.7642 | -0.1424 | 0/20 | 0.8584 | 1.0541 | success |
| mlp_mnist | 20 | 0.3 | raw_union_K20 | 42 | 0.9438 | 0.6595 | 0.8515 | 0.9735 | 0.9309 | -0.0406 | 0/20 | 0.9451 | 0.0000 | success |
| mlp_mnist | 20 | 1.0 | dp_avg_eps2_K20 | 44 | 0.8691 | 0.8393 | 0.9182 | 0.9776 | 0.2274 | -0.1148 | 0/20 | 0.9656 | 4.2089 | success |
| mlp_mnist | 20 | 1.0 | noprobe_dp_avg_eps8_K20 | 42 | 0.8983 | 0.8596 | 0.9093 | 0.9735 | 0.6629 | -0.0898 | 0/20 | n/a | 1.0577 | success |
| mlp_mnist | 20 | 1.0 | noprobe_dp_avg_eps8_K20 | 43 | 0.8931 | 0.8426 | 0.9095 | 0.9747 | 0.7082 | -0.0937 | 0/20 | n/a | 1.0541 | success |
| mlp_mnist | 20 | 1.0 | noprobe_dp_avg_eps8_K20 | 44 | 0.8943 | 0.8393 | 0.9182 | 0.9776 | 0.7125 | -0.0906 | 0/20 | 0.9674 | 1.0522 | success |
| mlp_mnist | 20 | 1.0 | raw_union_K20 | 42 | 0.9535 | 0.8596 | 0.9093 | 0.9735 | 0.9300 | -0.0311 | 0/20 | n/a | 0.0000 | success |
| mlp_mnist | 20 | 1.0 | raw_union_K20 | 43 | 0.9437 | 0.8426 | 0.9095 | 0.9747 | 0.9309 | -0.0377 | 0/20 | n/a | 0.0000 | success |
| mlp_mnist | 50 | 0.01 | noprobe_dp_avg_eps8_K20 | 43 | n/a | 0.1321 | 0.2998 | 0.9747 | n/a | n/a | n/a | n/a | 0.0000 | FAIL |
| mlp_mnist | 50 | 0.01 | noprobe_dp_avg_eps8_K20 | 44 | n/a | 0.1177 | 0.2874 | 0.9776 | n/a | n/a | n/a | n/a | 0.0000 | FAIL |
| mlp_mnist | 50 | 0.01 | noprobe_raw_union_K20 | 42 | n/a | 0.1094 | 0.2011 | 0.9735 | n/a | n/a | n/a | n/a | 0.0000 | FAIL |
| mlp_mnist | 50 | 0.01 | raw_union_K20 | 42 | 0.8826 | 0.1094 | 0.2011 | 0.9735 | 0.8472 | -0.0877 | 0/36 | 0.8823 | 0.0000 | success |
| mlp_mnist | 50 | 0.01 | raw_union_K20 | 43 | 0.8863 | 0.1321 | 0.2998 | 0.9747 | 0.8628 | -0.0905 | 0/34 | 0.8850 | 0.0000 | success |
| mlp_mnist | 50 | 0.01 | raw_union_K20 | 44 | 0.8379 | 0.1177 | 0.2874 | 0.9776 | 0.8304 | -0.0825 | 2/32 | 0.8357 | 0.0000 | success |
| mlp_mnist | 50 | 0.05 | noprobe_dp_avg_eps8_K20 | 44 | n/a | 0.2005 | 0.5202 | 0.9776 | n/a | n/a | n/a | n/a | 0.0000 | FAIL |
| mlp_mnist | 50 | 0.05 | noprobe_raw_union_K20 | 42 | 0.7353 | 0.2029 | 0.4533 | 0.9735 | 0.7343 | -0.2209 | 3/50 | 0.7206 | 0.0000 | success |
| mlp_mnist | 50 | 0.05 | noprobe_raw_union_K20 | 43 | 0.6925 | 0.2106 | 0.5674 | 0.9747 | 0.7620 | -0.2729 | 5/50 | 0.6611 | 0.0000 | success |
| mlp_mnist | 50 | 0.05 | raw_union_K20 | 43 | 0.9164 | 0.2106 | 0.5674 | 0.9747 | 0.9142 | -0.0166 | 13/50 | 0.9116 | 0.0000 | success |
| mlp_mnist | 50 | 0.05 | raw_union_K20 | 44 | 0.9123 | 0.2005 | 0.5202 | 0.9776 | 0.9136 | -0.0251 | 12/49 | 0.9092 | 0.0000 | success |
| mlp_mnist | 50 | 0.1 | noprobe_dp_avg_eps2_K20 | 42 | 0.8421 | 0.3210 | 0.5280 | 0.9735 | 0.5915 | -0.1053 | 5/50 | 0.8407 | 4.2309 | success |
| mlp_mnist | 50 | 0.1 | noprobe_raw_union_K20 | 42 | 0.8334 | 0.3210 | 0.5280 | 0.9735 | 0.7741 | -0.1049 | 4/50 | 0.8263 | 0.0000 | success |
| mlp_mnist | 50 | 0.1 | noprobe_raw_union_K20 | 43 | 0.8004 | 0.3236 | 0.5856 | 0.9747 | 0.6684 | -0.1307 | 3/50 | 0.7774 | 0.0000 | success |
| mlp_mnist | 50 | 0.1 | noprobe_raw_union_K20 | 44 | 0.8091 | 0.3003 | 0.5662 | 0.9776 | 0.7566 | -0.1371 | 4/50 | 0.8012 | 0.0000 | success |
| mlp_mnist | 50 | 0.1 | raw_union_K20 | 44 | 0.9359 | 0.3003 | 0.5662 | 0.9776 | 0.9336 | -0.0147 | 10/50 | 0.9351 | 0.0000 | success |
| mlp_mnist | 50 | 0.3 | dp_avg_eps2_K20 | 42 | 0.8278 | 0.5626 | 0.8337 | 0.9735 | 0.4704 | -0.1436 | 0/50 | 0.7993 | 4.2309 | success |
| mlp_mnist | 50 | 0.3 | noprobe_dp_avg_eps2_K20 | 42 | 0.8819 | 0.5626 | 0.8337 | 0.9735 | 0.6416 | -0.0964 | 1/50 | 0.8784 | 4.2309 | success |
| mlp_mnist | 50 | 0.3 | noprobe_dp_avg_eps2_K20 | 43 | 0.8568 | 0.5160 | 0.7652 | 0.9747 | 0.5992 | -0.1117 | 2/50 | 0.8545 | 4.2164 | success |
| mlp_mnist | 50 | 0.3 | noprobe_raw_union_K20 | 43 | 0.8598 | 0.5160 | 0.7652 | 0.9747 | 0.7629 | -0.1146 | 3/50 | 0.8581 | 0.0000 | success |
| mlp_mnist | 50 | 0.3 | noprobe_raw_union_K20 | 44 | 0.8494 | 0.5418 | 0.8300 | 0.9776 | 0.7668 | -0.1159 | 1/50 | 0.8437 | 0.0000 | success |
| mlp_mnist | 50 | 1.0 | dp_avg_eps2_K20 | 42 | 0.8789 | 0.7642 | 0.8844 | 0.9735 | 0.3833 | -0.1003 | 0/50 | n/a | 4.2309 | success |
| mlp_mnist | 50 | 1.0 | dp_avg_eps2_K20 | 43 | 0.8671 | 0.7699 | 0.8809 | 0.9747 | 0.2912 | -0.1040 | 0/50 | 0.8033 | 4.2164 | success |
| mlp_mnist | 50 | 1.0 | noprobe_dp_avg_eps2_K20 | 42 | 0.8968 | 0.7642 | 0.8844 | 0.9735 | 0.6647 | -0.0858 | 0/50 | n/a | 4.2309 | success |
| mlp_mnist | 50 | 1.0 | noprobe_dp_avg_eps2_K20 | 43 | 0.8940 | 0.7699 | 0.8809 | 0.9747 | 0.7029 | -0.0832 | 0/50 | 0.8526 | 4.2164 | success |
| mlp_mnist | 50 | 1.0 | noprobe_dp_avg_eps2_K20 | 44 | 0.8895 | 0.7627 | 0.8686 | 0.9776 | 0.6385 | -0.0908 | 0/50 | n/a | 4.2089 | success |
| mlp_mnist | 50 | 1.0 | noprobe_raw_union_K20 | 44 | 0.8785 | 0.7627 | 0.8686 | 0.9776 | 0.7782 | -0.1010 | 0/50 | n/a | 0.0000 | success |

Raw per-cell JSONs live here as `cell_<backbone>_N<n>_a<α>_<method>_s<seed>_K<k>_<hash>.json`.
Per-client per-class counts at `partition_diagnostic.jsonl`. Slurm stdout/stderr at `runs/`. Long-form rows at `results.csv`.
