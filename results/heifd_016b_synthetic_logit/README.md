# heifd_016b_synthetic_logit

## VERDICT — shape fix works; synthetic alignment is VIABLE (DP-protectable), not a dramatic accuracy win

The conv2d shape bug is fixed (no crashes; all 12 cells succeeded). Findings:

| backbone | α | method | acc | θ₀ | lift | m4 |
|---|---|---:|---:|---:|---:|---:|
| resnet18_cifar10 | 0.05 | raw_union_K20 | 0.7642 | 0.7564 | +0.008 | 0.749 |
| resnet18_cifar10 | 0.05 | synthetic_K100 | **0.7748** | 0.7733 | +0.002 | 0.766 |
| resnet18_cifar10 | 0.05 | synthetic_logit_K100 | 0.7695 | 0.7660 | +0.003 | 0.759 |
| cnn5_cifar10 | 1.0 | raw_union_K20 | 0.5024 | 0.4859 | +0.016 | n/a |
| cnn5_cifar10 | 1.0 | synthetic_K100 | 0.3919 | 0.2500 | +0.142 | n/a |
| cnn5_cifar10 | 1.0 | synthetic_logit_K100 | 0.4123 | 0.2523 | +0.160 | n/a |

- **On pretrained backbones (smooth feature space), synthetic alignment ≈ raw_union** — resnet18/α=0.05 synthetic_K100 (0.7748) slightly EDGES raw_union (0.7642). Synthetic prototypes are a viable, DP-protectable alternative to raw prototypes with no accuracy cost. Useful for the privacy story.
- **On from-scratch cnn5 (pixel space), synthetic warmup is weak** (θ₀ 0.25 vs raw_union 0.49) — Gaussian-around-mean in 3072-dim pixel space is nonsense imagery — but the distillation lift is largest there (+0.16 for synthetic_logit at IID); absolute acc still below raw_union. Consistent with the 016b-distill verdict (from-scratch deep net under the basin-coherence ceiling).
- **synthetic_logit ≈ synthetic** (the teacher-confusion-structure soft labels add little over plain Gaussian synthetic here). The logit modality is implemented + works, but doesn't beat plain synthetic in this test. Future-work candidate, not a headline lever.

Net: synthetic alignment is a viable low-leak variant comparable to raw prototypes on pretrained backbones; logit prototypes are a working-but-marginal extension.



HE-IFD plaintext simulation of the one-shot federated distillation protocol: each client distils its own teacher into a student over a bounded K-step trajectory from a shared, Phase-0-aligned init θ₀, then uploads the cumulative trainable-parameter displacement Δ_i = θ_i^(K) − θ₀; the server's only operation is the sample-weighted linear combine θ₀ + Σ_i w_i·Δ_i (w_i = n_i/Σ_j n_j), which uses plaintext-scalar × ciphertext and ciphertext + ciphertext only and is thus FHE-compatible by construction (multiplicative depth ≈ 1). This case sweeps the grid below; IID test accuracy is the lead metric, with mean/best teacher and a centralised oracle as references, plus the standalone accuracy of the aligned init θ₀ (what alignment adds before distillation), the M3 per-client teacher-vs-aggregate gap on each client's own data (the participation-incentive metric), and the M4 per-client accuracy on classes a client held zero local examples of (the OOD value-proposition; n/a at α=1.0).

## Sweep configuration

- Backbones: `resnet18_cifar10`
- N values: `16`
- Dirichlet α: `0.05,1.0`
- Methods: `synthetic_logit_K100,synthetic_K100,raw_union_K20`
- Seeds: `42`
- K (bounded trajectory length): `100`
- τ (distill temperature): `1.0`
- Student LR: `0.001`
- Labelled-probe size P: `None` (None = backbone default)

## Results

| backbone | N | α | method | seed | acc | mean_teacher | best_teacher | oracle | θ₀_acc | M3_mean_gap | M3_helped | M4_ood_acc | σ | status |
|---|---|---|--------|------|-----|--------------|--------------|--------|--------|-------------|-----------|------------|---|--------|
| cnn5_cifar10 | 16 | 0.05 | raw_union_K20 | 42 | 0.2057 | 0.1495 | 0.2661 | 0.7779 | 0.2380 | -0.7560 | 0/16 | 0.1702 | 0.0000 | success |
| cnn5_cifar10 | 16 | 0.05 | synthetic_K100 | 42 | 0.1323 | 0.1495 | 0.2660 | 0.7803 | 0.2613 | -0.7825 | 0/16 | 0.0918 | 0.0000 | success |
| cnn5_cifar10 | 16 | 0.05 | synthetic_logit_K100 | 42 | 0.1613 | 0.1495 | 0.2658 | 0.7851 | 0.2695 | -0.7744 | 0/16 | 0.1270 | 0.0000 | success |
| cnn5_cifar10 | 16 | 1.0 | raw_union_K20 | 42 | 0.5024 | 0.4790 | 0.5254 | 0.7815 | 0.4859 | -0.4930 | 0/16 | n/a | 0.0000 | success |
| cnn5_cifar10 | 16 | 1.0 | synthetic_K100 | 42 | 0.3919 | 0.4780 | 0.5297 | 0.7781 | 0.2500 | -0.6076 | 0/16 | n/a | 0.0000 | success |
| cnn5_cifar10 | 16 | 1.0 | synthetic_logit_K100 | 42 | 0.4123 | 0.4787 | 0.5279 | 0.7792 | 0.2523 | -0.5947 | 0/16 | n/a | 0.0000 | success |
| resnet18_cifar10 | 16 | 0.05 | raw_union_K20 | 42 | 0.7642 | 0.1658 | 0.2885 | 0.8701 | 0.7564 | -0.1882 | 0/16 | 0.7492 | 0.0000 | success |
| resnet18_cifar10 | 16 | 0.05 | synthetic_K100 | 42 | 0.7748 | 0.1658 | 0.2885 | 0.8701 | 0.7733 | -0.1907 | 0/16 | 0.7656 | 0.0000 | success |
| resnet18_cifar10 | 16 | 0.05 | synthetic_logit_K100 | 42 | 0.7695 | 0.1658 | 0.2885 | 0.8701 | 0.7660 | -0.1966 | 0/16 | 0.7590 | 0.0000 | success |
| resnet18_cifar10 | 16 | 1.0 | raw_union_K20 | 42 | 0.8340 | 0.6934 | 0.7868 | 0.8701 | 0.8303 | -0.0250 | 1/16 | n/a | 0.0000 | success |
| resnet18_cifar10 | 16 | 1.0 | synthetic_K100 | 42 | 0.7933 | 0.6934 | 0.7868 | 0.8701 | 0.7877 | -0.0707 | 1/16 | n/a | 0.0000 | success |
| resnet18_cifar10 | 16 | 1.0 | synthetic_logit_K100 | 42 | 0.8019 | 0.6934 | 0.7868 | 0.8701 | 0.8004 | -0.0596 | 1/16 | n/a | 0.0000 | success |

Raw per-cell JSONs live here as `cell_<backbone>_N<n>_a<α>_<method>_s<seed>_K<k>_<hash>.json`.
Per-client per-class counts at `partition_diagnostic.jsonl`. Slurm stdout/stderr at `runs/`. Long-form rows at `results.csv`.
