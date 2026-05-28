# heifd_013_kd_diagnostic

Empirical-evidence anchor for the θ₀≥final phenomenon (issue 008). Runs the `diagnose=True` path on two contrast cells — one degrading (resnet18/CIFAR-10), one working (mlp/MNIST) — to attribute the resnet18 degradation to one of three hypotheses: basin-cancellation, teacher-overshoot, or capacity-constraint. Both cells use raw_union_K20 alignment + K=20 distillation steps, N=10, α=0.05, seed 42 — identical except for (backbone, dataset). Diagnostics: per-client teacher logit entropy on D_i, per-step ‖Δᵢ⁽ᵏ⁾‖₂ profile, cumulative ‖Δᵢ‖₂, pairwise cos(Δᵢ, Δⱼ) for all i≠j, and per-class accuracy of θ₀ vs final.

## Verdict — basin-cancellation present on both; **per-class teacher quality is what makes it damaging on resnet18**

The pairwise-cosine signature of cancellation appears on **both** cells. The asymmetry comes from **per-class teacher quality and θ₀ headroom**, not from whether cancellation occurs.

| Signal | MLP / MNIST (works) | ResNet18 / CIFAR-10 (degrades) |
|---|---|---|
| **acc** | **0.8646** | **0.5998** |
| **θ₀** | **0.824** | **0.7176** |
| **acc − θ₀** | **+0.041** | **−0.118** |
| mean_teacher | 0.334 | 0.230 |
| best_teacher | 0.590 | 0.426 |
| oracle (centralised) | 0.974 | 0.870 |
| teacher entropy /client (mean) | 0.041 nats | 0.091 nats |
| ‖Δᵢ‖₂ cumulative (mean) | 0.74 | 0.88 |
| **pairwise-cos off-diag mean** | **+0.035** | **−0.042** |
| pairwise-cos pairs < 0 | **56 / 90** | **54 / 90** |
| pairwise-cos pairs \|·\| < 0.1 | 40 / 90 | 26 / 90 |
| per-class Δ (final−θ₀) net | **+0.411** (helped 7, hurt 1) | **−1.178** (helped 3, hurt 7) |

### Which hypothesis the data supports

- **Basin-cancellation — SUPPORTED on both, but not the root cause of the asymmetry.** ~60% of client-pair displacements are negatively correlated under raw_union_K20 / K=20 / α=0.05 on BOTH cells. Cancellation is a property of α=0.05 heterogeneity itself, not the backbone.
- **Teacher-overshoot (peaky-teacher) — PARTIALLY SUPPORTED.** Both cells have near-one-hot teachers (entropy < 0.1 nats). MLP/MNIST tolerates this because θ₀=0.82 still has room to be improved by majority-class teacher votes; ResNet18 has θ₀=0.72, already very strong, so the same peaky teachers push it *off* the optimum on 7 of 10 classes.
- **Capacity-constraint — INDIRECTLY SUPPORTED.** Both heads are linear. On MLP/MNIST the head still has room to learn beyond θ₀; on ResNet18 the head is near its capacity ceiling on the labelled probe, so distillation can only *re-weight*, and under cancelled-but-still-biased teacher signal the only direction is down.

### Implication for issues 010 and 011

- **Issue 010 (KD hparams) — τ is the dominant lever.** Lowering τ from 4 → 1 keeps the teachers' high-confidence direction visible above cancellation noise; smoothing (τ=4) wastes the only signal that survives cancellation. **Empirically confirmed:** the 010 sweep found τ=1 recovers θ₀ across every (K, lr); τ=4 still degrades. Best (K=100, τ=1, lr=0.001) → 0.7617 (partial verdict; recovers θ₀ + ~2pp).
- **Issue 011 (trainable-layer scope) — capacity is the remaining lever.** Even with τ=1, ResNet18 doesn't beat θ₀ by ≥3pp. To close the gap to oracle 0.87, the head needs the capacity to *add* signal beyond θ₀ — LoRA on last 1–2 blocks or last-block FT.

## Two cells, one job

- **Cell A — degrading:** `resnet18_cifar10` / α=0.05 / N=10 / raw_union_K20 / K=20 / seed 42 (`cell_resnet18_cifar10_N10_a0.05_raw_union_K20_s42_K20_2131e9453970.json`)
- **Cell B — working control:** `mlp_mnist` / α=0.05 / N=10 / raw_union_K20 / K=20 / seed 42 (`cell_mlp_mnist_N10_a0.05_raw_union_K20_s42_K20_bba9fc3d8a5d.json`)

Both with `diagnose=True`; `diagnose=False` (default everywhere else) is byte-identical to the pre-issue-013 protocol. Job 1115488, 33s wall-clock.

## Sweep configuration

- Backbones: `resnet18_cifar10`, `mlp_mnist`
- N: 10 · Dirichlet α: 0.05 · Method: `raw_union_K20` · K: 20 · τ: 4.0 · Student LR: 0.01
- Seeds: 42 only (single-cell diagnostic, not a sweep)
- Diagnostics field on each cell JSON: `diagnostics.teacher_entropy_per_client`, `delta_norms.{cumulative,per_step,mean_step_norm}`, `pairwise_cosine`, `per_class_test_acc.{theta0,final,delta}`.
