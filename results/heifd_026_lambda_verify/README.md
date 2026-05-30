# heifd_026_lambda_verify

> **Results collected (2026-05-30).** Table below is verbatim from the auto-written
> `src.lambda_verify` README. Full per-cell `lambda_curve` JSONs committed alongside
> (VALAR chain rerun; matches the Colab run).

Issue 026 — task-arithmetic scaling coefficient λ, cheap **EVAL-ONLY** verify.
θ⋆(λ) = θ₀ + λ·Σ_j w_j·Δ_j = (1−λ)·θ₀ + λ·θ⋆(1): a pure interpolation between the
basin θ₀ (λ=0) and the current aggregate θ⋆(1) (λ=1). Eval-only — one trajectory
per cell, then one `aggregate` reweight (public-scalar multiply → depth-1 under
CKKS) + one test eval per λ; no per-λ retraining.

Config: backbones `mlp_mnist,vit_b32_cifar100` · N=10 · α∈{0.05,1.0} · method
`raw_union_K20` · seed 42 · K=300 · λ∈{0,0.25,…,2.0}.

## Results

| backbone | N | α | method | seed | λ=0 | λ=0.25 | λ=0.5 | λ=0.75 | λ=1 | λ=1.25 | λ=1.5 | λ=1.75 | λ=2 | λ⋆ | acc(λ⋆) | acc(λ=1) | lift(λ⋆−1) | θ₀(λ=0) | status |
|---|---|---|--------|------|---|---|---|---|---|---|---|---|---|---|--------|---------|-----------|---------|--------|
| mlp_mnist | 10 | 0.05 | raw_union_K20 | 42 | 0.8698 | 0.8702 | 0.8681 | 0.8606 | 0.8466 | 0.8258 | 0.8040 | 0.7803 | 0.7560 | 0.25 | 0.8702 | 0.8466 | 0.0236 | 0.8698 | success |
| mlp_mnist | 10 | 1.0 | raw_union_K20 | 42 | 0.8963 | 0.9162 | 0.9282 | 0.9370 | 0.9390 | 0.9386 | 0.9333 | 0.9257 | 0.9144 | 1 | 0.9390 | 0.9390 | 0.0000 | 0.8963 | success |
| vit_b32_cifar100 | 10 | 0.05 | raw_union_K20 | 42 | 0.8091 | 0.8062 | 0.8004 | 0.7896 | 0.7709 | 0.7523 | 0.7214 | 0.6904 | 0.6502 | 0 | 0.8091 | 0.7709 | 0.0382 | 0.8091 | success |
| vit_b32_cifar100 | 10 | 1.0 | raw_union_K20 | 42 | 0.8494 | 0.8531 | 0.8550 | 0.8566 | 0.8577 | 0.8559 | 0.8514 | 0.8454 | 0.8366 | 1 | 0.8577 | 0.8577 | 0.0000 | 0.8494 | success |

**Finding.** Near-IID (α=1.0): λ⋆=1, lift 0 — the pinned λ=1 is optimal. High
heterogeneity (α=0.05): λ⋆<1 with a real lift — MNIST λ⋆=0.25 (+2.4pt); **ViT
λ⋆=0.0 (+3.8pt), i.e. the basin θ₀ alone beats the distilled aggregate** (negative
distillation lift on that cell). λ<1 down-weights the harmful displacement — the
"why the scaling coefficient matters" point, plus a flag that distillation hurts
the ViT/α=0.05 cell.
