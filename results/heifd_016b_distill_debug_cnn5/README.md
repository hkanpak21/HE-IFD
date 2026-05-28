# heifd_016b_distill_debug_cnn5

HE-IFD plaintext simulation of the one-shot federated distillation protocol: each client distils its own teacher into a student over a bounded K-step trajectory from a shared, Phase-0-aligned init θ₀, then uploads the cumulative trainable-parameter displacement Δ_i = θ_i^(K) − θ₀; the server's only operation is the sample-weighted linear combine θ₀ + Σ_i w_i·Δ_i (w_i = n_i/Σ_j n_j), which uses plaintext-scalar × ciphertext and ciphertext + ciphertext only and is thus FHE-compatible by construction (multiplicative depth ≈ 1). This case sweeps the grid below; IID test accuracy is the lead metric, with mean/best teacher and a centralised oracle as references, plus the standalone accuracy of the aligned init θ₀ (what alignment adds before distillation), the M3 per-client teacher-vs-aggregate gap on each client's own data (the participation-incentive metric), and the M4 per-client accuracy on classes a client held zero local examples of (the OOD value-proposition; n/a at α=1.0).

## Sweep configuration

- Backbones: `cnn5_cifar10`
- N values: `16`
- Dirichlet α: `0.05,1.0`
- Methods: `raw_union_K20`
- Seeds: `42`
- K (bounded trajectory length): `300`
- τ (distill temperature): `4.0`
- Student LR: `0.01`
- Labelled-probe size P: `None` (None = backbone default)

## Results

| backbone | N | α | method | seed | acc | mean_teacher | best_teacher | oracle | θ₀_acc | M3_mean_gap | M3_helped | M4_ood_acc | σ | status |
|---|---|---|--------|------|-----|--------------|--------------|--------|--------|-------------|-----------|------------|---|--------|
| cnn5_cifar10 | 16 | 0.05 | raw_union_K20 | 42 | 0.1719 | 0.1496 | 0.2679 | 0.7793 | 0.2375 | -0.7693 | 0/16 | 0.1344 | 0.0000 | success |
| cnn5_cifar10 | 16 | 0.05 | raw_union_K20 | 42 | 0.1591 | 0.1494 | 0.2661 | 0.7806 | 0.2379 | -0.7820 | 0/16 | 0.1143 | 0.0000 | success |
| cnn5_cifar10 | 16 | 0.05 | raw_union_K20 | 42 | 0.2029 | 0.1495 | 0.2655 | 0.7833 | 0.2379 | -0.7573 | 0/16 | 0.1649 | 0.0000 | success |
| cnn5_cifar10 | 16 | 0.05 | raw_union_K20 | 42 | 0.2332 | 0.1495 | 0.2667 | 0.7816 | 0.2365 | -0.7262 | 0/16 | 0.1904 | 0.0000 | success |
| cnn5_cifar10 | 16 | 0.05 | raw_union_K20 | 42 | 0.2075 | 0.1494 | 0.2662 | 0.7819 | 0.2376 | -0.7550 | 0/16 | 0.1721 | 0.0000 | success |
| cnn5_cifar10 | 16 | 0.05 | raw_union_K20 | 42 | 0.1437 | 0.1495 | 0.2669 | 0.7826 | 0.2374 | -0.7862 | 0/16 | 0.0984 | 0.0000 | success |
| cnn5_cifar10 | 16 | 0.05 | raw_union_K20 | 42 | 0.1969 | 0.1496 | 0.2667 | 0.7785 | 0.2367 | -0.7641 | 0/16 | 0.1624 | 0.0000 | success |
| cnn5_cifar10 | 16 | 0.05 | raw_union_K20 | 42 | 0.2123 | 0.1494 | 0.2669 | 0.7765 | 0.2377 | -0.7476 | 0/16 | 0.1697 | 0.0000 | success |
| cnn5_cifar10 | 16 | 0.05 | raw_union_K20 | 42 | 0.1623 | 0.1497 | 0.2665 | 0.7825 | 0.2375 | -0.7953 | 0/16 | 0.1277 | 0.0000 | success |
| cnn5_cifar10 | 16 | 0.05 | raw_union_K20 | 42 | 0.1898 | 0.1494 | 0.2663 | 0.7759 | 0.2378 | -0.7628 | 0/16 | 0.1459 | 0.0000 | success |
| cnn5_cifar10 | 16 | 0.05 | raw_union_K20 | 42 | 0.2075 | 0.1496 | 0.2662 | 0.7822 | 0.2357 | -0.7480 | 0/16 | 0.1652 | 0.0000 | success |
| cnn5_cifar10 | 16 | 0.05 | raw_union_K20 | 42 | 0.2428 | 0.1495 | 0.2655 | 0.7834 | 0.2365 | -0.7150 | 0/16 | 0.2000 | 0.0000 | success |
| cnn5_cifar10 | 16 | 1.0 | raw_union_K20 | 42 | 0.4626 | 0.4775 | 0.5277 | 0.7829 | 0.4862 | -0.5289 | 0/16 | n/a | 0.0000 | success |
| cnn5_cifar10 | 16 | 1.0 | raw_union_K20 | 42 | 0.4657 | 0.4785 | 0.5249 | 0.7784 | 0.4867 | -0.5363 | 0/16 | n/a | 0.0000 | success |
| cnn5_cifar10 | 16 | 1.0 | raw_union_K20 | 42 | 0.4918 | 0.4783 | 0.5291 | 0.7840 | 0.4839 | -0.5029 | 0/16 | n/a | 0.0000 | success |
| cnn5_cifar10 | 16 | 1.0 | raw_union_K20 | 42 | 0.4861 | 0.4778 | 0.5249 | 0.7831 | 0.4858 | -0.5133 | 0/16 | n/a | 0.0000 | success |
| cnn5_cifar10 | 16 | 1.0 | raw_union_K20 | 42 | 0.5025 | 0.4776 | 0.5276 | 0.7804 | 0.4854 | -0.4897 | 0/16 | n/a | 0.0000 | success |
| cnn5_cifar10 | 16 | 1.0 | raw_union_K20 | 42 | 0.4806 | 0.4781 | 0.5254 | 0.7785 | 0.4837 | -0.5224 | 0/16 | n/a | 0.0000 | success |
| cnn5_cifar10 | 16 | 1.0 | raw_union_K20 | 42 | 0.5064 | 0.4782 | 0.5278 | 0.7829 | 0.4858 | -0.4898 | 0/16 | n/a | 0.0000 | success |
| cnn5_cifar10 | 16 | 1.0 | raw_union_K20 | 42 | 0.4880 | 0.4784 | 0.5238 | 0.7782 | 0.4865 | -0.5104 | 0/16 | n/a | 0.0000 | success |
| cnn5_cifar10 | 16 | 1.0 | raw_union_K20 | 42 | 0.4116 | 0.4779 | 0.5285 | 0.7777 | 0.4848 | -0.5875 | 0/16 | n/a | 0.0000 | success |
| cnn5_cifar10 | 16 | 1.0 | raw_union_K20 | 42 | 0.4622 | 0.4782 | 0.5251 | 0.7805 | 0.4839 | -0.5368 | 0/16 | n/a | 0.0000 | success |
| cnn5_cifar10 | 16 | 1.0 | raw_union_K20 | 42 | 0.4872 | 0.4787 | 0.5254 | 0.7831 | 0.4857 | -0.5116 | 0/16 | n/a | 0.0000 | success |
| cnn5_cifar10 | 16 | 1.0 | raw_union_K20 | 42 | 0.4851 | 0.4781 | 0.5280 | 0.7821 | 0.4853 | -0.5150 | 0/16 | n/a | 0.0000 | success |

Raw per-cell JSONs live here as `cell_<backbone>_N<n>_a<α>_<method>_s<seed>_K<k>_<hash>.json`.
Per-client per-class counts at `partition_diagnostic.jsonl`. Slurm stdout/stderr at `runs/`. Long-form rows at `results.csv`.
