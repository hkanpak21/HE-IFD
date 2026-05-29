# heifd_015_dp_frontier_lenet

## VERDICT (81/81 cells, lenet_fmnist) — averaging-variant DP frontier FLATTENS from ε≈2 (generalizes from MLP/MNIST)

ε sweep @ Kpc=20 (acc, mean over 3 seeds):

| α | ε=0.5 | ε=2 | ε=8 | ε=32 | ε=∞ |
|---|---:|---:|---:|---:|---:|
| 0.05 | 0.2950 | 0.3117 | 0.3370 | 0.3561 | 0.2970 |
| 0.3 | 0.5337 | 0.5170 | 0.5141 | 0.4985 | 0.5051 |
| 1.0 | 0.6424 | 0.6392 | 0.6490 | 0.6453 | 0.6387 |

The frontier is flat across ε at every α (ε=2 ≈ ε=8 ≈ ε=32 ≈ ε=∞ within seed noise; no monotone privacy-cost). Same conclusion as the MLP/MNIST frontier (heifd_015_dp_frontier_mlp): the averaging-variant DP mechanism makes strong privacy (ε=2) essentially free on FashionMNIST/LeNet too. Confirms the claim generalizes beyond the MLP toy case to a small conv backbone.

---

HE-IFD plaintext simulation of the one-shot federated distillation protocol: each client distils its own teacher into a student over a bounded K-step trajectory from a shared, Phase-0-aligned init θ₀, then uploads the cumulative trainable-parameter displacement Δ_i = θ_i^(K) − θ₀; the server's only operation is the sample-weighted linear combine θ₀ + Σ_i w_i·Δ_i (w_i = n_i/Σ_j n_j), which uses plaintext-scalar × ciphertext and ciphertext + ciphertext only and is thus FHE-compatible by construction (multiplicative depth ≈ 1). This case sweeps the grid below; IID test accuracy is the lead metric, with mean/best teacher and a centralised oracle as references, plus the standalone accuracy of the aligned init θ₀ (what alignment adds before distillation), the M3 per-client teacher-vs-aggregate gap on each client's own data (the participation-incentive metric), and the M4 per-client accuracy on classes a client held zero local examples of (the OOD value-proposition; n/a at α=1.0).

## Sweep configuration

- Backbones: `lenet_fmnist`
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
| lenet_fmnist | 10 | 0.05 | dp_avg_eps0.5_K20 | 42 | 0.3596 | 0.2966 | 0.4733 | 0.8845 | 0.0656 | -0.7531 | 0/10 | 0.2860 | 17.9384 | success |
| lenet_fmnist | 10 | 0.05 | dp_avg_eps0.5_K20 | 43 | 0.2250 | 0.2525 | 0.3674 | 0.8887 | 0.1002 | -0.6894 | 0/10 | 0.2026 | 18.0345 | success |
| lenet_fmnist | 10 | 0.05 | dp_avg_eps0.5_K20 | 44 | 0.3004 | 0.2723 | 0.4574 | 0.8744 | 0.1040 | -0.7110 | 0/10 | 0.2437 | 17.9708 | success |
| lenet_fmnist | 10 | 0.05 | dp_avg_eps2_K1 | 42 | 0.1000 | 0.2951 | 0.4627 | 0.8821 | 0.1000 | -0.9412 | 0/10 | 0.0635 | 89.6919 | success |
| lenet_fmnist | 10 | 0.05 | dp_avg_eps2_K1 | 43 | 0.1000 | 0.2543 | 0.3710 | 0.8832 | 0.1000 | -0.8806 | 0/10 | 0.1180 | 90.1727 | success |
| lenet_fmnist | 10 | 0.05 | dp_avg_eps2_K1 | 44 | 0.1003 | 0.2730 | 0.4534 | 0.8862 | 0.1000 | -0.8562 | 0/10 | 0.1029 | 89.8538 | success |
| lenet_fmnist | 10 | 0.05 | dp_avg_eps2_K20 | 42 | 0.4153 | 0.2964 | 0.4723 | 0.8884 | 0.2018 | -0.7337 | 0/10 | 0.3519 | 4.4846 | success |
| lenet_fmnist | 10 | 0.05 | dp_avg_eps2_K20 | 43 | 0.2371 | 0.2542 | 0.3675 | 0.8830 | 0.0899 | -0.7024 | 0/10 | 0.1929 | 4.5086 | success |
| lenet_fmnist | 10 | 0.05 | dp_avg_eps2_K20 | 44 | 0.2826 | 0.2646 | 0.4800 | 0.8754 | 0.1810 | -0.6683 | 0/10 | 0.2180 | 4.4927 | success |
| lenet_fmnist | 10 | 0.05 | dp_avg_eps2_K5 | 42 | 0.4372 | 0.2940 | 0.4608 | 0.8887 | 0.1046 | -0.7236 | 0/10 | 0.3766 | 17.9384 | success |
| lenet_fmnist | 10 | 0.05 | dp_avg_eps2_K5 | 43 | 0.2642 | 0.2520 | 0.3592 | 0.8868 | 0.1000 | -0.6742 | 0/10 | 0.2179 | 18.0345 | success |
| lenet_fmnist | 10 | 0.05 | dp_avg_eps2_K5 | 44 | 0.2888 | 0.2546 | 0.4562 | 0.8861 | 0.1136 | -0.6583 | 1/10 | 0.1999 | 17.9708 | success |
| lenet_fmnist | 10 | 0.05 | dp_avg_eps32_K20 | 42 | 0.4296 | 0.2963 | 0.4693 | 0.8866 | 0.1000 | -0.7310 | 0/10 | 0.3678 | 0.2803 | success |
| lenet_fmnist | 10 | 0.05 | dp_avg_eps32_K20 | 43 | 0.3128 | 0.2514 | 0.3583 | 0.8847 | 0.0999 | -0.6114 | 0/10 | 0.2693 | 0.2818 | success |
| lenet_fmnist | 10 | 0.05 | dp_avg_eps32_K20 | 44 | 0.3259 | 0.2643 | 0.4557 | 0.8793 | 0.1758 | -0.6929 | 0/10 | 0.2480 | 0.2808 | success |
| lenet_fmnist | 10 | 0.05 | dp_avg_eps8_K1 | 42 | 0.3909 | 0.2967 | 0.4810 | 0.8873 | 0.1221 | -0.7540 | 0/10 | 0.3423 | 22.4230 | success |
| lenet_fmnist | 10 | 0.05 | dp_avg_eps8_K1 | 43 | 0.3472 | 0.2512 | 0.3603 | 0.8805 | 0.0213 | -0.5912 | 0/10 | 0.2805 | 22.5432 | success |
| lenet_fmnist | 10 | 0.05 | dp_avg_eps8_K1 | 44 | 0.2786 | 0.2547 | 0.4604 | 0.8818 | 0.1229 | -0.6725 | 0/10 | 0.1952 | 22.4634 | success |
| lenet_fmnist | 10 | 0.05 | dp_avg_eps8_K20 | 42 | 0.4252 | 0.2956 | 0.4664 | 0.8873 | 0.1008 | -0.7422 | 0/10 | 0.3713 | 1.1211 | success |
| lenet_fmnist | 10 | 0.05 | dp_avg_eps8_K20 | 43 | 0.2608 | 0.2546 | 0.3661 | 0.8907 | 0.0998 | -0.6619 | 0/10 | 0.2253 | 1.1272 | success |
| lenet_fmnist | 10 | 0.05 | dp_avg_eps8_K20 | 44 | 0.3251 | 0.2819 | 0.4734 | 0.8779 | 0.2512 | -0.7032 | 0/10 | 0.2372 | 1.1232 | success |
| lenet_fmnist | 10 | 0.05 | dp_avg_eps8_K5 | 42 | 0.4282 | 0.2945 | 0.4700 | 0.8809 | 0.1724 | -0.7321 | 0/10 | 0.3705 | 4.4846 | success |
| lenet_fmnist | 10 | 0.05 | dp_avg_eps8_K5 | 43 | 0.3040 | 0.2510 | 0.3677 | 0.8825 | 0.1056 | -0.6160 | 0/10 | 0.2613 | 4.5086 | success |
| lenet_fmnist | 10 | 0.05 | dp_avg_eps8_K5 | 44 | 0.3071 | 0.2538 | 0.4791 | 0.8783 | 0.1832 | -0.6552 | 0/10 | 0.2211 | 4.4927 | success |
| lenet_fmnist | 10 | 0.05 | dp_avg_epsinf_K20 | 42 | 0.4427 | 0.2946 | 0.4635 | 0.8871 | 0.1000 | -0.7289 | 0/10 | 0.3857 | 0.0000 | success |
| lenet_fmnist | 10 | 0.05 | dp_avg_epsinf_K20 | 43 | 0.2678 | 0.2523 | 0.3680 | 0.8878 | 0.0998 | -0.6330 | 0/10 | 0.2398 | 0.0000 | success |
| lenet_fmnist | 10 | 0.05 | dp_avg_epsinf_K20 | 44 | 0.1804 | 0.2581 | 0.4707 | 0.8770 | 0.2324 | -0.7311 | 0/10 | 0.1334 | 0.0000 | success |
| lenet_fmnist | 10 | 0.3 | dp_avg_eps0.5_K20 | 42 | 0.5635 | 0.6054 | 0.7716 | 0.8831 | 0.2464 | -0.3819 | 0/10 | 0.4113 | 17.9384 | success |
| lenet_fmnist | 10 | 0.3 | dp_avg_eps0.5_K20 | 43 | 0.6094 | 0.5141 | 0.6356 | 0.8840 | 0.1714 | -0.3321 | 0/10 | 0.6151 | 18.0345 | success |
| lenet_fmnist | 10 | 0.3 | dp_avg_eps0.5_K20 | 44 | 0.4281 | 0.5675 | 0.7516 | 0.8772 | 0.0899 | -0.4731 | 0/10 | 0.5018 | 17.9708 | success |
| lenet_fmnist | 10 | 0.3 | dp_avg_eps2_K1 | 42 | 0.5735 | 0.6065 | 0.7945 | 0.8780 | 0.1000 | -0.3718 | 0/10 | 0.4144 | 89.6919 | success |
| lenet_fmnist | 10 | 0.3 | dp_avg_eps2_K1 | 43 | 0.3246 | 0.5132 | 0.6394 | 0.8861 | 0.1000 | -0.6488 | 0/10 | 0.3443 | 90.1727 | success |
| lenet_fmnist | 10 | 0.3 | dp_avg_eps2_K1 | 44 | 0.2751 | 0.5616 | 0.7435 | 0.8791 | 0.1000 | -0.6365 | 0/10 | 0.2375 | 89.8538 | success |
| lenet_fmnist | 10 | 0.3 | dp_avg_eps2_K20 | 42 | 0.5711 | 0.6016 | 0.7851 | 0.8892 | 0.1207 | -0.3794 | 0/10 | 0.4198 | 4.4846 | success |
| lenet_fmnist | 10 | 0.3 | dp_avg_eps2_K20 | 43 | 0.5950 | 0.5120 | 0.6554 | 0.8872 | 0.1134 | -0.3785 | 0/10 | 0.6413 | 4.5086 | success |
| lenet_fmnist | 10 | 0.3 | dp_avg_eps2_K20 | 44 | 0.3849 | 0.5647 | 0.7528 | 0.8778 | 0.1728 | -0.5004 | 0/10 | 0.4006 | 4.4927 | success |
| lenet_fmnist | 10 | 0.3 | dp_avg_eps2_K5 | 42 | 0.5976 | 0.5974 | 0.7630 | 0.8778 | 0.2154 | -0.3578 | 0/10 | 0.4607 | 17.9384 | success |
| lenet_fmnist | 10 | 0.3 | dp_avg_eps2_K5 | 43 | 0.5473 | 0.5086 | 0.6494 | 0.8848 | 0.1086 | -0.3900 | 0/10 | 0.5486 | 18.0345 | success |
| lenet_fmnist | 10 | 0.3 | dp_avg_eps2_K5 | 44 | 0.4341 | 0.5621 | 0.7307 | 0.8788 | 0.1704 | -0.4684 | 0/10 | 0.5783 | 17.9708 | success |
| lenet_fmnist | 10 | 0.3 | dp_avg_eps32_K20 | 42 | 0.5829 | 0.6067 | 0.7860 | 0.8741 | 0.1087 | -0.3665 | 0/10 | 0.4137 | 0.2803 | success |
| lenet_fmnist | 10 | 0.3 | dp_avg_eps32_K20 | 43 | 0.5335 | 0.5119 | 0.6466 | 0.8856 | 0.0990 | -0.4362 | 0/10 | 0.5654 | 0.2818 | success |
| lenet_fmnist | 10 | 0.3 | dp_avg_eps32_K20 | 44 | 0.3790 | 0.5644 | 0.7451 | 0.8841 | 0.2506 | -0.5226 | 0/10 | 0.4416 | 0.2808 | success |
| lenet_fmnist | 10 | 0.3 | dp_avg_eps8_K1 | 42 | 0.5848 | 0.6031 | 0.7913 | 0.8871 | 0.2116 | -0.3643 | 0/10 | 0.4339 | 22.4230 | success |
| lenet_fmnist | 10 | 0.3 | dp_avg_eps8_K1 | 43 | 0.5394 | 0.5099 | 0.6607 | 0.8855 | 0.1000 | -0.4250 | 0/10 | 0.5513 | 22.5432 | success |
| lenet_fmnist | 10 | 0.3 | dp_avg_eps8_K1 | 44 | 0.4086 | 0.5657 | 0.7295 | 0.8793 | 0.1340 | -0.4751 | 0/10 | 0.3718 | 22.4634 | success |
| lenet_fmnist | 10 | 0.3 | dp_avg_eps8_K20 | 42 | 0.5505 | 0.6009 | 0.7860 | 0.8800 | 0.1191 | -0.3950 | 0/10 | 0.4035 | 1.1211 | success |
| lenet_fmnist | 10 | 0.3 | dp_avg_eps8_K20 | 43 | 0.6078 | 0.5085 | 0.6344 | 0.8791 | 0.0995 | -0.3569 | 0/10 | 0.6194 | 1.1272 | success |
| lenet_fmnist | 10 | 0.3 | dp_avg_eps8_K20 | 44 | 0.3841 | 0.5630 | 0.7491 | 0.8781 | 0.2263 | -0.5024 | 0/10 | 0.4449 | 1.1232 | success |
| lenet_fmnist | 10 | 0.3 | dp_avg_eps8_K5 | 42 | 0.5734 | 0.5998 | 0.7688 | 0.8853 | 0.1337 | -0.3757 | 0/10 | 0.4236 | 4.4846 | success |
| lenet_fmnist | 10 | 0.3 | dp_avg_eps8_K5 | 43 | 0.5874 | 0.5119 | 0.6469 | 0.8902 | 0.1075 | -0.3779 | 0/10 | 0.6118 | 4.5086 | success |
| lenet_fmnist | 10 | 0.3 | dp_avg_eps8_K5 | 44 | 0.3992 | 0.5685 | 0.7427 | 0.8755 | 0.1878 | -0.4961 | 0/10 | 0.4748 | 4.4927 | success |
| lenet_fmnist | 10 | 0.3 | dp_avg_epsinf_K20 | 42 | 0.5656 | 0.6047 | 0.7851 | 0.8774 | 0.1006 | -0.3833 | 0/10 | 0.4165 | 0.0000 | success |
| lenet_fmnist | 10 | 0.3 | dp_avg_epsinf_K20 | 43 | 0.5766 | 0.5099 | 0.6561 | 0.8803 | 0.1001 | -0.3889 | 0/10 | 0.6030 | 0.0000 | success |
| lenet_fmnist | 10 | 0.3 | dp_avg_epsinf_K20 | 44 | 0.3730 | 0.5718 | 0.7408 | 0.8782 | 0.2476 | -0.5228 | 0/10 | 0.4360 | 0.0000 | success |
| lenet_fmnist | 10 | 1.0 | dp_avg_eps0.5_K20 | 42 | 0.6753 | 0.7637 | 0.8481 | 0.8830 | 0.2234 | -0.2025 | 0/10 | n/a | 17.9384 | success |
| lenet_fmnist | 10 | 1.0 | dp_avg_eps0.5_K20 | 43 | 0.6259 | 0.7555 | 0.8093 | 0.8909 | 0.1850 | -0.2490 | 0/10 | n/a | 18.0345 | success |
| lenet_fmnist | 10 | 1.0 | dp_avg_eps0.5_K20 | 44 | 0.6260 | 0.7631 | 0.8257 | 0.8703 | 0.1477 | -0.2500 | 0/10 | n/a | 17.9708 | success |
| lenet_fmnist | 10 | 1.0 | dp_avg_eps2_K1 | 42 | 0.6467 | 0.7610 | 0.8405 | 0.8820 | 0.1000 | -0.2397 | 0/10 | n/a | 89.6919 | success |
| lenet_fmnist | 10 | 1.0 | dp_avg_eps2_K1 | 43 | 0.5908 | 0.7580 | 0.8013 | 0.8822 | 0.1141 | -0.2850 | 0/10 | n/a | 90.1727 | success |
| lenet_fmnist | 10 | 1.0 | dp_avg_eps2_K1 | 44 | 0.2857 | 0.7556 | 0.8130 | 0.8816 | 0.1000 | -0.5918 | 0/10 | n/a | 89.8538 | success |
| lenet_fmnist | 10 | 1.0 | dp_avg_eps2_K20 | 42 | 0.6710 | 0.7690 | 0.8346 | 0.8833 | 0.1711 | -0.2147 | 0/10 | n/a | 4.4846 | success |
| lenet_fmnist | 10 | 1.0 | dp_avg_eps2_K20 | 43 | 0.6173 | 0.7634 | 0.8213 | 0.8877 | 0.1150 | -0.2585 | 0/10 | n/a | 4.5086 | success |
| lenet_fmnist | 10 | 1.0 | dp_avg_eps2_K20 | 44 | 0.6293 | 0.7575 | 0.7959 | 0.8737 | 0.2218 | -0.2416 | 0/10 | n/a | 4.4927 | success |
| lenet_fmnist | 10 | 1.0 | dp_avg_eps2_K5 | 42 | 0.6858 | 0.7704 | 0.8323 | 0.8830 | 0.2175 | -0.1967 | 0/10 | n/a | 17.9384 | success |
| lenet_fmnist | 10 | 1.0 | dp_avg_eps2_K5 | 43 | 0.6132 | 0.7586 | 0.8048 | 0.8799 | 0.2002 | -0.2605 | 0/10 | n/a | 18.0345 | success |
| lenet_fmnist | 10 | 1.0 | dp_avg_eps2_K5 | 44 | 0.6596 | 0.7682 | 0.8352 | 0.8702 | 0.1260 | -0.2092 | 0/10 | n/a | 17.9708 | success |
| lenet_fmnist | 10 | 1.0 | dp_avg_eps32_K20 | 42 | 0.6838 | 0.7632 | 0.8349 | 0.8894 | 0.1001 | -0.2020 | 0/10 | n/a | 0.2803 | success |
| lenet_fmnist | 10 | 1.0 | dp_avg_eps32_K20 | 43 | 0.6348 | 0.7599 | 0.8183 | 0.8908 | 0.0996 | -0.2463 | 0/10 | n/a | 0.2818 | success |
| lenet_fmnist | 10 | 1.0 | dp_avg_eps32_K20 | 44 | 0.6174 | 0.7695 | 0.7918 | 0.8743 | 0.2041 | -0.2637 | 0/10 | n/a | 0.2808 | success |
| lenet_fmnist | 10 | 1.0 | dp_avg_eps8_K1 | 42 | 0.6936 | 0.7698 | 0.8376 | 0.8847 | 0.1096 | -0.1947 | 0/10 | n/a | 22.4230 | success |
| lenet_fmnist | 10 | 1.0 | dp_avg_eps8_K1 | 43 | 0.6276 | 0.7617 | 0.8165 | 0.8822 | 0.1921 | -0.2451 | 0/10 | n/a | 22.5432 | success |
| lenet_fmnist | 10 | 1.0 | dp_avg_eps8_K1 | 44 | 0.6751 | 0.7486 | 0.8058 | 0.8822 | 0.1866 | -0.1877 | 1/10 | n/a | 22.4634 | success |
| lenet_fmnist | 10 | 1.0 | dp_avg_eps8_K20 | 42 | 0.6740 | 0.7708 | 0.8329 | 0.8899 | 0.1000 | -0.2107 | 0/10 | n/a | 1.1211 | success |
| lenet_fmnist | 10 | 1.0 | dp_avg_eps8_K20 | 43 | 0.6260 | 0.7585 | 0.8013 | 0.8839 | 0.1084 | -0.2505 | 0/10 | n/a | 1.1272 | success |
| lenet_fmnist | 10 | 1.0 | dp_avg_eps8_K20 | 44 | 0.6471 | 0.7697 | 0.8262 | 0.8828 | 0.1850 | -0.2271 | 0/10 | n/a | 1.1232 | success |
| lenet_fmnist | 10 | 1.0 | dp_avg_eps8_K5 | 42 | 0.6691 | 0.7651 | 0.8231 | 0.8836 | 0.1553 | -0.2194 | 0/10 | n/a | 4.4846 | success |
| lenet_fmnist | 10 | 1.0 | dp_avg_eps8_K5 | 43 | 0.6317 | 0.7594 | 0.8166 | 0.8904 | 0.1002 | -0.2460 | 0/10 | n/a | 4.5086 | success |
| lenet_fmnist | 10 | 1.0 | dp_avg_eps8_K5 | 44 | 0.6466 | 0.7686 | 0.8290 | 0.8744 | 0.1683 | -0.2198 | 0/10 | n/a | 4.4927 | success |
| lenet_fmnist | 10 | 1.0 | dp_avg_epsinf_K20 | 42 | 0.6640 | 0.7674 | 0.8276 | 0.8805 | 0.1004 | -0.2194 | 0/10 | n/a | 0.0000 | success |
| lenet_fmnist | 10 | 1.0 | dp_avg_epsinf_K20 | 43 | 0.6218 | 0.7488 | 0.8111 | 0.8814 | 0.0997 | -0.2508 | 0/10 | n/a | 0.0000 | success |
| lenet_fmnist | 10 | 1.0 | dp_avg_epsinf_K20 | 44 | 0.6302 | 0.7640 | 0.8173 | 0.8764 | 0.2316 | -0.2476 | 0/10 | n/a | 0.0000 | success |

Raw per-cell JSONs live here as `cell_<backbone>_N<n>_a<α>_<method>_s<seed>_K<k>_<hash>.json`.
Per-client per-class counts at `partition_diagnostic.jsonl`. Slurm stdout/stderr at `runs/`. Long-form rows at `results.csv`.
