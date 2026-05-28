# heifd_010_kd_hparams_resnet18

Focused KD-hyperparameter sweep on the regime issue 008 flagged broken: resnet18 / CIFAR-10 / α=0.05 / N=10 / raw_union_K20. Issue 008 found `raw_union=0.48` vs warmed init `θ₀=0.74` here — distillation degraded the aligned init by 26pp under the default (K=300, τ=4, lr=0.01). This case crosses K ∈ {30, 100, 300, 1000} × τ ∈ {1, 4} × student-LR ∈ {0.001, 0.01} over 3 seeds (48 cells) to test whether the gap closes by KD hyperparams alone.

## Verdict — **PARTIAL** (most of the gap closed by τ alone; ~2.2pp residual)

Best config: **K=100, τ=1, lr=0.001** → mean acc **0.7617** (std 0.0102) across 3 seeds, vs θ₀ ≈ **0.74**.

- The +3pp gap-closed gate (`max mean_acc > 0.77`) is **not** reached, so the conditional λ-schedule mini-sweep does **not** trigger.
- But distillation is no longer *actively degrading* the warmed init under the right τ. The 008 phenomenon was hyperparameter-driven, not a fundamental protocol issue.
- The residual ~1–3pp likely needs **issue 011** (LoRA / last-block FT) — capacity to *add* signal beyond the linear head's ability to re-weight an already-near-optimal θ₀.

### Single dominant lever — KD temperature τ

Every τ=1 config recovers θ₀ within seed noise; every τ=4 config still degrades. Clean separation.

| τ | range of mean_acc | regime |
|---|---|---|
| **1** | 0.7233 – 0.7617 | recovers / slightly improves θ₀ |
| **4** | 0.4564 – 0.6927 | actively degrades (the 008 phenomenon) |

The 008 default (K=300, τ=4, lr=0.01) reproduces here as 0.4845 ± 0.0595 — confirms τ was the culprit.

### Mean-of-3-seeds table (sorted desc)

| K | τ | LR | mean | std | vs θ₀≈0.74 |
|---:|---:|---:|---:|---:|---|
| 100 | 1.0 | 0.001 | **0.7617** | 0.0102 | partial best |
| 30 | 1.0 | 0.001 | 0.7612 | 0.0091 | partial |
| 30 | 1.0 | 0.01 | 0.7566 | 0.0127 | partial |
| 300 | 1.0 | 0.001 | 0.7558 | 0.0128 | partial |
| 100 | 1.0 | 0.01 | 0.7482 | 0.0165 | partial |
| 1000 | 1.0 | 0.001 | 0.7477 | 0.0163 | partial |
| 300 | 1.0 | 0.01 | 0.7385 | 0.0186 | ≈θ₀ |
| 1000 | 1.0 | 0.01 | 0.7233 | 0.0184 | slight degrade |
| 30 | 4.0 | 0.001 | 0.6927 | 0.0141 | degrades |
| 100 | 4.0 | 0.001 | 0.6058 | 0.0215 | degrades |
| 300 | 4.0 | 0.001 | 0.5433 | 0.0408 | degrades |
| 30 | 4.0 | 0.01 | 0.5369 | 0.0443 | degrades |
| 1000 | 4.0 | 0.001 | 0.5049 | 0.0520 | degrades |
| 100 | 4.0 | 0.01 | 0.5049 | 0.0498 | degrades |
| **300** | **4.0** | **0.01** | **0.4845** | **0.0595** | **008 default — 26pp loss reproduced** |
| 1000 | 4.0 | 0.01 | 0.4564 | 0.0690 | worst — degrades most |

### Interpretation with issue 013's diagnostic

Issue 013 found ~60% negative pairwise-cosine pairs in client displacements on this cell — basin-cancellation is real. With τ=4 the KD signal is heavily smoothed across all classes, so per-step gradients push hard along directions the cancellation then partly destroys; what survives is biased *away* from a near-optimal θ₀. With τ=1 the teacher's confident-prediction directions dominate the loss, cancellation cancels noise more than signal, and the surviving aggregate stays near θ₀.

### Recommended methodology change

The "tiny head suffices" framing **survives** — the warmed linear head can recover and slightly improve θ₀ under the right (K, τ, lr). The paper's KD default should change from (K=300, τ=4, lr=0.01) → **(K=100, τ=1, lr=0.001)** as the new pretrained-regime baseline. The residual ~1–3pp lift is what issue 011 targets.

## Sweep configuration

- Backbone: `resnet18_cifar10` (frozen ImageNet ResNet-18 features + trainable linear head)
- N: 10 · Dirichlet α: 0.05 · Method: `raw_union_K20`
- Seeds: 42, 43, 44
- K: swept `{30, 100, 300, 1000}`
- τ: swept `{1, 4}` · Student LR: swept `{0.001, 0.01}`
- 4-task SLURM array (`--array=0-3`), 12 cells per task, round-robin chunking. Each task ~1m22s; total ~6 min wall-clock (feature cache from issue 008 hot).
- Job 1115489 (array tasks `_0…_3`).
- Raw per-cell JSONs (one per seed × config) live in this directory.
