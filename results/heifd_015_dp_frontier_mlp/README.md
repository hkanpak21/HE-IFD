# heifd_015_dp_frontier_mlp

## VERDICT (81 cells, mlp_mnist) — averaging-variant DP frontier FLATTENS from ε≈2; strong privacy is nearly free

**ε sweep @ Kpc=20 (acc, mean over 3 seeds):**

| α | ε=0.5 | ε=2 | ε=8 | ε=32 | ε=∞ |
|---|---:|---:|---:|---:|---:|
| 0.05 | 0.4917 | **0.5486** | 0.5484 | 0.5356 | 0.5346 |
| 0.3 | 0.7776 | **0.7898** | 0.7715 | 0.7688 | 0.7619 |
| 1.0 | 0.8653 | 0.8620 | 0.8605 | 0.8585 | 0.8642 |

- **The frontier is flat from ε=2 onward** at every α: ε=2 ≈ ε=8 ≈ ε=32 ≈ ε=∞ within seed noise. Strong DP (ε=2) costs essentially nothing vs no-DP. Only ε=0.5 dips (~6pp at α=0.05). Notably ε=2 ≥ ε=∞ in several rows (the calibrated Gaussian noise acts as mild regularization). **This is the paper's averaging-variant DP claim, confirmed.**

**Kpc sweep @ α=0.05 (acc):**

| ε | Kpc=1 | Kpc=5 | Kpc=20 |
|---|---:|---:|---:|
| 2 | 0.0992 | 0.5094 | 0.5486 |
| 8 | 0.5154 | 0.5451 | 0.5484 |

- At tight ε=2, **Kpc≥5 is required** — Kpc=1 collapses to chance (sensitivity = clip/Kpc is largest at Kpc=1, so the noise destroys the prototype). More samples per class per client lowers sensitivity → less noise → tolerates tighter privacy. At looser ε=8 even Kpc=1 works. This is exactly the averaging-variant accounting (σ ∝ clip/(Kpc·ε)): you buy privacy budget by averaging more samples, not by accepting accuracy loss.

→ lenet/cnn5 DP-frontier wrappers (heifd_015_dp_frontier_{lenet,cnn5}) extend this to harder backbones (orchestrator submits as the queue drains).



HE-IFD plaintext simulation of the one-shot federated distillation protocol: each client distils its own teacher into a student over a bounded K-step trajectory from a shared, Phase-0-aligned init θ₀, then uploads the cumulative trainable-parameter displacement Δ_i = θ_i^(K) − θ₀; the server's only operation is the sample-weighted linear combine θ₀ + Σ_i w_i·Δ_i (w_i = n_i/Σ_j n_j), which uses plaintext-scalar × ciphertext and ciphertext + ciphertext only and is thus FHE-compatible by construction (multiplicative depth ≈ 1). This case sweeps the grid below; IID test accuracy is the lead metric, with mean/best teacher and a centralised oracle as references, plus the standalone accuracy of the aligned init θ₀ (what alignment adds before distillation), the M3 per-client teacher-vs-aggregate gap on each client's own data (the participation-incentive metric), and the M4 per-client accuracy on classes a client held zero local examples of (the OOD value-proposition; n/a at α=1.0).

## Sweep configuration

- Backbones: `mlp_mnist`
- N values: `10`
- Dirichlet α: `0.05,0.3,1.0`
- Methods: `dp_avg_eps0.5_K20,dp_avg_eps2_K20,dp_avg_eps8_K20,dp_avg_eps32_K20,dp_avg_epsinf_K20,dp_avg_eps2_K1,dp_avg_eps2_K5,dp_avg_eps8_K1,dp_avg_eps8_K5`
- Seeds: `42,43,44`
- K (bounded trajectory length): `300`
- τ (distill temperature): `4.0`
- Student LR: `0.01`
- Labelled-probe size P: `None` (None = backbone default)

## Results

| backbone | N | α | method | seed | acc | mean_teacher | best_teacher | oracle | θ₀_acc | M3_mean_gap | M3_helped | M4_ood_acc | σ | status |
|---|---|---|--------|------|-----|--------------|--------------|--------|--------|-------------|-----------|------------|---|--------|
| mlp_mnist | 10 | 0.05 | dp_avg_eps0.5_K20 | 42 | 0.4967 | 0.3337 | 0.5902 | 0.9735 | 0.1066 | -0.4708 | 0/10 | 0.4061 | 16.9237 | success |
| mlp_mnist | 10 | 0.05 | dp_avg_eps0.5_K20 | 43 | 0.6291 | 0.3327 | 0.5603 | 0.9747 | 0.1534 | -0.3120 | 0/10 | 0.6016 | 16.8657 | success |
| mlp_mnist | 10 | 0.05 | dp_avg_eps0.5_K20 | 44 | 0.3493 | 0.3385 | 0.5152 | 0.9776 | 0.0745 | -0.6928 | 0/10 | 0.2810 | 16.8355 | success |
| mlp_mnist | 10 | 0.05 | dp_avg_eps2_K1 | 42 | 0.1017 | 0.3337 | 0.5902 | 0.9735 | 0.0820 | -0.8802 | 0/10 | 0.1031 | 84.6187 | success |
| mlp_mnist | 10 | 0.05 | dp_avg_eps2_K1 | 43 | 0.0980 | 0.3327 | 0.5603 | 0.9747 | 0.1024 | -0.8963 | 0/10 | 0.1519 | 84.3287 | success |
| mlp_mnist | 10 | 0.05 | dp_avg_eps2_K1 | 44 | 0.0980 | 0.3385 | 0.5152 | 0.9776 | 0.0848 | -0.9243 | 0/10 | 0.0246 | 84.1773 | success |
| mlp_mnist | 10 | 0.05 | dp_avg_eps2_K20 | 42 | 0.5172 | 0.3337 | 0.5902 | 0.9735 | 0.1668 | -0.4563 | 0/10 | 0.4339 | 4.2309 | success |
| mlp_mnist | 10 | 0.05 | dp_avg_eps2_K20 | 43 | 0.6411 | 0.3327 | 0.5603 | 0.9747 | 0.3547 | -0.3113 | 0/10 | 0.5977 | 4.2164 | success |
| mlp_mnist | 10 | 0.05 | dp_avg_eps2_K20 | 44 | 0.4874 | 0.3385 | 0.5152 | 0.9776 | 0.2046 | -0.5588 | 0/10 | 0.4477 | 4.2089 | success |
| mlp_mnist | 10 | 0.05 | dp_avg_eps2_K5 | 42 | 0.4964 | 0.3337 | 0.5902 | 0.9735 | 0.1563 | -0.4885 | 0/10 | 0.4058 | 16.9237 | success |
| mlp_mnist | 10 | 0.05 | dp_avg_eps2_K5 | 43 | 0.5947 | 0.3327 | 0.5603 | 0.9747 | 0.1448 | -0.3629 | 0/10 | 0.5674 | 16.8657 | success |
| mlp_mnist | 10 | 0.05 | dp_avg_eps2_K5 | 44 | 0.4370 | 0.3385 | 0.5152 | 0.9776 | 0.1131 | -0.5774 | 0/10 | 0.3800 | 16.8355 | success |
| mlp_mnist | 10 | 0.05 | dp_avg_eps32_K20 | 42 | 0.5080 | 0.3337 | 0.5902 | 0.9735 | 0.4067 | -0.4730 | 0/10 | 0.4153 | 0.2644 | success |
| mlp_mnist | 10 | 0.05 | dp_avg_eps32_K20 | 43 | 0.5842 | 0.3327 | 0.5603 | 0.9747 | 0.4050 | -0.3567 | 0/10 | 0.5277 | 0.2635 | success |
| mlp_mnist | 10 | 0.05 | dp_avg_eps32_K20 | 44 | 0.5146 | 0.3385 | 0.5152 | 0.9776 | 0.4241 | -0.5061 | 0/10 | 0.4505 | 0.2631 | success |
| mlp_mnist | 10 | 0.05 | dp_avg_eps8_K1 | 42 | 0.5108 | 0.3337 | 0.5902 | 0.9735 | 0.1434 | -0.4619 | 0/10 | 0.4263 | 21.1547 | success |
| mlp_mnist | 10 | 0.05 | dp_avg_eps8_K1 | 43 | 0.5504 | 0.3327 | 0.5603 | 0.9747 | 0.0828 | -0.3860 | 0/10 | 0.5222 | 21.0822 | success |
| mlp_mnist | 10 | 0.05 | dp_avg_eps8_K1 | 44 | 0.4849 | 0.3385 | 0.5152 | 0.9776 | 0.1270 | -0.5560 | 0/10 | 0.4303 | 21.0443 | success |
| mlp_mnist | 10 | 0.05 | dp_avg_eps8_K20 | 42 | 0.5093 | 0.3337 | 0.5902 | 0.9735 | 0.2981 | -0.4743 | 0/10 | 0.4192 | 1.0577 | success |
| mlp_mnist | 10 | 0.05 | dp_avg_eps8_K20 | 43 | 0.6068 | 0.3327 | 0.5603 | 0.9747 | 0.3903 | -0.3407 | 0/10 | 0.5532 | 1.0541 | success |
| mlp_mnist | 10 | 0.05 | dp_avg_eps8_K20 | 44 | 0.5291 | 0.3385 | 0.5152 | 0.9776 | 0.3594 | -0.4977 | 0/10 | 0.4816 | 1.0522 | success |
| mlp_mnist | 10 | 0.05 | dp_avg_eps8_K5 | 42 | 0.5270 | 0.3337 | 0.5902 | 0.9735 | 0.3172 | -0.4502 | 0/10 | 0.4405 | 4.2309 | success |
| mlp_mnist | 10 | 0.05 | dp_avg_eps8_K5 | 43 | 0.6249 | 0.3327 | 0.5603 | 0.9747 | 0.3245 | -0.3206 | 0/10 | 0.5721 | 4.2164 | success |
| mlp_mnist | 10 | 0.05 | dp_avg_eps8_K5 | 44 | 0.4834 | 0.3385 | 0.5152 | 0.9776 | 0.2376 | -0.5480 | 0/10 | 0.4207 | 4.2089 | success |
| mlp_mnist | 10 | 0.05 | dp_avg_epsinf_K20 | 42 | 0.5151 | 0.3337 | 0.5902 | 0.9735 | 0.4516 | -0.4642 | 0/10 | 0.4248 | 0.0000 | success |
| mlp_mnist | 10 | 0.05 | dp_avg_epsinf_K20 | 43 | 0.5733 | 0.3327 | 0.5603 | 0.9747 | 0.4190 | -0.3703 | 0/10 | 0.5131 | 0.0000 | success |
| mlp_mnist | 10 | 0.05 | dp_avg_epsinf_K20 | 44 | 0.5155 | 0.3385 | 0.5152 | 0.9776 | 0.4252 | -0.5118 | 0/10 | 0.4531 | 0.0000 | success |
| mlp_mnist | 10 | 0.3 | dp_avg_eps0.5_K20 | 42 | 0.7760 | 0.6727 | 0.8286 | 0.9735 | 0.1479 | -0.2029 | 0/10 | 0.6736 | 16.9237 | success |
| mlp_mnist | 10 | 0.3 | dp_avg_eps0.5_K20 | 43 | 0.7973 | 0.7185 | 0.9304 | 0.9747 | 0.1871 | -0.2038 | 0/10 | 0.8410 | 16.8657 | success |
| mlp_mnist | 10 | 0.3 | dp_avg_eps0.5_K20 | 44 | 0.7594 | 0.7126 | 0.8846 | 0.9776 | 0.1910 | -0.2390 | 0/10 | 0.6798 | 16.8355 | success |
| mlp_mnist | 10 | 0.3 | dp_avg_eps2_K1 | 42 | 0.1116 | 0.6727 | 0.8286 | 0.9735 | 0.0959 | -0.8647 | 0/10 | 0.0596 | 84.6187 | success |
| mlp_mnist | 10 | 0.3 | dp_avg_eps2_K1 | 43 | 0.1195 | 0.7185 | 0.9304 | 0.9747 | 0.1089 | -0.8556 | 0/10 | 0.2263 | 84.3287 | success |
| mlp_mnist | 10 | 0.3 | dp_avg_eps2_K1 | 44 | 0.0757 | 0.7126 | 0.8846 | 0.9776 | 0.1005 | -0.9129 | 0/10 | 0.0974 | 84.1773 | success |
| mlp_mnist | 10 | 0.3 | dp_avg_eps2_K20 | 42 | 0.7991 | 0.6727 | 0.8286 | 0.9735 | 0.3801 | -0.1787 | 0/10 | 0.7056 | 4.2309 | success |
| mlp_mnist | 10 | 0.3 | dp_avg_eps2_K20 | 43 | 0.7883 | 0.7185 | 0.9304 | 0.9747 | 0.3373 | -0.2069 | 0/10 | 0.8418 | 4.2164 | success |
| mlp_mnist | 10 | 0.3 | dp_avg_eps2_K20 | 44 | 0.7820 | 0.7126 | 0.8846 | 0.9776 | 0.3537 | -0.2152 | 0/10 | 0.7175 | 4.2089 | success |
| mlp_mnist | 10 | 0.3 | dp_avg_eps2_K5 | 42 | 0.7401 | 0.6727 | 0.8286 | 0.9735 | 0.1856 | -0.2354 | 0/10 | 0.6065 | 16.9237 | success |
| mlp_mnist | 10 | 0.3 | dp_avg_eps2_K5 | 43 | 0.7867 | 0.7185 | 0.9304 | 0.9747 | 0.1580 | -0.2174 | 0/10 | 0.8033 | 16.8657 | success |
| mlp_mnist | 10 | 0.3 | dp_avg_eps2_K5 | 44 | 0.7695 | 0.7126 | 0.8846 | 0.9776 | 0.0985 | -0.2230 | 0/10 | 0.6643 | 16.8355 | success |
| mlp_mnist | 10 | 0.3 | dp_avg_eps32_K20 | 42 | 0.7852 | 0.6727 | 0.8286 | 0.9735 | 0.4825 | -0.1910 | 0/10 | 0.6740 | 0.2644 | success |
| mlp_mnist | 10 | 0.3 | dp_avg_eps32_K20 | 43 | 0.7674 | 0.7185 | 0.9304 | 0.9747 | 0.4273 | -0.2225 | 0/10 | 0.8226 | 0.2635 | success |
| mlp_mnist | 10 | 0.3 | dp_avg_eps32_K20 | 44 | 0.7537 | 0.7126 | 0.8846 | 0.9776 | 0.4012 | -0.2408 | 0/10 | 0.6619 | 0.2631 | success |
| mlp_mnist | 10 | 0.3 | dp_avg_eps8_K1 | 42 | 0.7351 | 0.6727 | 0.8286 | 0.9735 | 0.1393 | -0.2324 | 0/10 | 0.5938 | 21.1547 | success |
| mlp_mnist | 10 | 0.3 | dp_avg_eps8_K1 | 43 | 0.7481 | 0.7185 | 0.9304 | 0.9747 | 0.1721 | -0.2429 | 0/10 | 0.8341 | 21.0822 | success |
| mlp_mnist | 10 | 0.3 | dp_avg_eps8_K1 | 44 | 0.7658 | 0.7126 | 0.8846 | 0.9776 | 0.1117 | -0.2270 | 0/10 | 0.6618 | 21.0443 | success |
| mlp_mnist | 10 | 0.3 | dp_avg_eps8_K20 | 42 | 0.7827 | 0.6727 | 0.8286 | 0.9735 | 0.4919 | -0.1930 | 0/10 | 0.6718 | 1.0577 | success |
| mlp_mnist | 10 | 0.3 | dp_avg_eps8_K20 | 43 | 0.7600 | 0.7185 | 0.9304 | 0.9747 | 0.3939 | -0.2328 | 0/10 | 0.8208 | 1.0541 | success |
| mlp_mnist | 10 | 0.3 | dp_avg_eps8_K20 | 44 | 0.7717 | 0.7126 | 0.8846 | 0.9776 | 0.4278 | -0.2241 | 0/10 | 0.6977 | 1.0522 | success |
| mlp_mnist | 10 | 0.3 | dp_avg_eps8_K5 | 42 | 0.7635 | 0.6727 | 0.8286 | 0.9735 | 0.3561 | -0.2140 | 0/10 | 0.6437 | 4.2309 | success |
| mlp_mnist | 10 | 0.3 | dp_avg_eps8_K5 | 43 | 0.7689 | 0.7185 | 0.9304 | 0.9747 | 0.2112 | -0.2249 | 0/10 | 0.7935 | 4.2164 | success |
| mlp_mnist | 10 | 0.3 | dp_avg_eps8_K5 | 44 | 0.7879 | 0.7126 | 0.8846 | 0.9776 | 0.2058 | -0.2069 | 0/10 | 0.6944 | 4.2089 | success |
| mlp_mnist | 10 | 0.3 | dp_avg_epsinf_K20 | 42 | 0.7673 | 0.6727 | 0.8286 | 0.9735 | 0.4595 | -0.2038 | 0/10 | 0.6407 | 0.0000 | success |
| mlp_mnist | 10 | 0.3 | dp_avg_epsinf_K20 | 43 | 0.7671 | 0.7185 | 0.9304 | 0.9747 | 0.4030 | -0.2243 | 0/10 | 0.8205 | 0.0000 | success |
| mlp_mnist | 10 | 0.3 | dp_avg_epsinf_K20 | 44 | 0.7512 | 0.7126 | 0.8846 | 0.9776 | 0.3601 | -0.2434 | 0/10 | 0.6554 | 0.0000 | success |
| mlp_mnist | 10 | 1.0 | dp_avg_eps0.5_K20 | 42 | 0.8806 | 0.8937 | 0.9285 | 0.9735 | 0.1733 | -0.1125 | 0/10 | n/a | 16.9237 | success |
| mlp_mnist | 10 | 1.0 | dp_avg_eps0.5_K20 | 43 | 0.8867 | 0.8886 | 0.9307 | 0.9747 | 0.1568 | -0.1050 | 0/10 | n/a | 16.8657 | success |
| mlp_mnist | 10 | 1.0 | dp_avg_eps0.5_K20 | 44 | 0.8285 | 0.8992 | 0.9203 | 0.9776 | 0.1260 | -0.1654 | 0/10 | n/a | 16.8355 | success |
| mlp_mnist | 10 | 1.0 | dp_avg_eps2_K1 | 42 | 0.1294 | 0.8937 | 0.9285 | 0.9735 | 0.1011 | -0.8608 | 0/10 | n/a | 84.6187 | success |
| mlp_mnist | 10 | 1.0 | dp_avg_eps2_K1 | 43 | 0.0891 | 0.8886 | 0.9307 | 0.9747 | 0.1009 | -0.9031 | 0/10 | n/a | 84.3287 | success |
| mlp_mnist | 10 | 1.0 | dp_avg_eps2_K1 | 44 | 0.1006 | 0.8992 | 0.9203 | 0.9776 | 0.1089 | -0.8968 | 0/10 | n/a | 84.1773 | success |
| mlp_mnist | 10 | 1.0 | dp_avg_eps2_K20 | 42 | 0.8817 | 0.8937 | 0.9285 | 0.9735 | 0.2821 | -0.1079 | 0/10 | n/a | 4.2309 | success |
| mlp_mnist | 10 | 1.0 | dp_avg_eps2_K20 | 43 | 0.8812 | 0.8886 | 0.9307 | 0.9747 | 0.2428 | -0.1089 | 0/10 | n/a | 4.2164 | success |
| mlp_mnist | 10 | 1.0 | dp_avg_eps2_K20 | 44 | 0.8230 | 0.8992 | 0.9203 | 0.9776 | 0.1996 | -0.1726 | 0/10 | n/a | 4.2089 | success |
| mlp_mnist | 10 | 1.0 | dp_avg_eps2_K5 | 42 | 0.8755 | 0.8937 | 0.9285 | 0.9735 | 0.1417 | -0.1152 | 0/10 | n/a | 16.9237 | success |
| mlp_mnist | 10 | 1.0 | dp_avg_eps2_K5 | 43 | 0.8826 | 0.8886 | 0.9307 | 0.9747 | 0.3088 | -0.1076 | 0/10 | n/a | 16.8657 | success |
| mlp_mnist | 10 | 1.0 | dp_avg_eps2_K5 | 44 | 0.8228 | 0.8992 | 0.9203 | 0.9776 | 0.1317 | -0.1711 | 0/10 | n/a | 16.8355 | success |
| mlp_mnist | 10 | 1.0 | dp_avg_eps32_K20 | 42 | 0.8677 | 0.8937 | 0.9285 | 0.9735 | 0.5047 | -0.1237 | 0/10 | n/a | 0.2644 | success |
| mlp_mnist | 10 | 1.0 | dp_avg_eps32_K20 | 43 | 0.8805 | 0.8886 | 0.9307 | 0.9747 | 0.4140 | -0.1091 | 0/10 | n/a | 0.2635 | success |
| mlp_mnist | 10 | 1.0 | dp_avg_eps32_K20 | 44 | 0.8274 | 0.8992 | 0.9203 | 0.9776 | 0.4352 | -0.1657 | 0/10 | n/a | 0.2631 | success |
| mlp_mnist | 10 | 1.0 | dp_avg_eps8_K1 | 42 | 0.8710 | 0.8937 | 0.9285 | 0.9735 | 0.0789 | -0.1227 | 0/10 | n/a | 21.1547 | success |
| mlp_mnist | 10 | 1.0 | dp_avg_eps8_K1 | 43 | 0.8668 | 0.8886 | 0.9307 | 0.9747 | 0.1753 | -0.1246 | 0/10 | n/a | 21.0822 | success |
| mlp_mnist | 10 | 1.0 | dp_avg_eps8_K1 | 44 | 0.8317 | 0.8992 | 0.9203 | 0.9776 | 0.1270 | -0.1600 | 0/10 | n/a | 21.0443 | success |
| mlp_mnist | 10 | 1.0 | dp_avg_eps8_K20 | 42 | 0.8751 | 0.8937 | 0.9285 | 0.9735 | 0.4199 | -0.1159 | 0/10 | n/a | 1.0577 | success |
| mlp_mnist | 10 | 1.0 | dp_avg_eps8_K20 | 43 | 0.8813 | 0.8886 | 0.9307 | 0.9747 | 0.3805 | -0.1080 | 0/10 | n/a | 1.0541 | success |
| mlp_mnist | 10 | 1.0 | dp_avg_eps8_K20 | 44 | 0.8251 | 0.8992 | 0.9203 | 0.9776 | 0.3215 | -0.1692 | 0/10 | n/a | 1.0522 | success |
| mlp_mnist | 10 | 1.0 | dp_avg_eps8_K5 | 42 | 0.8835 | 0.8937 | 0.9285 | 0.9735 | 0.2231 | -0.1068 | 0/10 | n/a | 4.2309 | success |
| mlp_mnist | 10 | 1.0 | dp_avg_eps8_K5 | 43 | 0.8878 | 0.8886 | 0.9307 | 0.9747 | 0.3670 | -0.1018 | 0/10 | n/a | 4.2164 | success |
| mlp_mnist | 10 | 1.0 | dp_avg_eps8_K5 | 44 | 0.8158 | 0.8992 | 0.9203 | 0.9776 | 0.2245 | -0.1810 | 0/10 | n/a | 4.2089 | success |
| mlp_mnist | 10 | 1.0 | dp_avg_epsinf_K20 | 42 | 0.8745 | 0.8937 | 0.9285 | 0.9735 | 0.4949 | -0.1175 | 0/10 | n/a | 0.0000 | success |
| mlp_mnist | 10 | 1.0 | dp_avg_epsinf_K20 | 43 | 0.8824 | 0.8886 | 0.9307 | 0.9747 | 0.4473 | -0.1079 | 0/10 | n/a | 0.0000 | success |
| mlp_mnist | 10 | 1.0 | dp_avg_epsinf_K20 | 44 | 0.8358 | 0.8992 | 0.9203 | 0.9776 | 0.3872 | -0.1557 | 0/10 | n/a | 0.0000 | success |

Raw per-cell JSONs live here as `cell_<backbone>_N<n>_a<α>_<method>_s<seed>_K<k>_<hash>.json`.
Per-client per-class counts at `partition_diagnostic.jsonl`. Slurm stdout/stderr at `runs/`. Long-form rows at `results.csv`.
