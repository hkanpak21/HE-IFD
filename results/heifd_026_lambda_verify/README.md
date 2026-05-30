# heifd_026_lambda_verify

Issue 026 — task-arithmetic scaling coefficient λ, cheap **EVAL-ONLY** verify
(placeholder; `src.lambda_verify` auto-populates the table on the first run).

**The question.** Our server op θ⋆ = θ₀ + Σ_j w_j·Δ_j **is task arithmetic**
(Ilharco et al. 2023, `ilharco2023editing`) with the scaling coefficient pinned to
λ=1. The one optimization lever that fits {one-shot, HE depth-1} and that we have
never tested is λ in

> θ⋆(λ) = θ₀ + λ·Σ_j w_j·Δ_j = (1−λ)·θ₀ + λ·θ⋆(1).

This is a pure **interpolation** along the line between the basin θ₀ (λ=0) and the
current aggregate θ⋆(1) (λ=1). So sweeping λ is **eval-only**: one bounded
distillation trajectory per cell, then one `aggregate` reweight (a public-scalar
multiply → still **depth-1** under CKKS) + one test eval per λ. **No per-λ
retraining.** A peak at **λ<1** means the basin deserves more trust (down-weight
the displacement); **λ>1** means push harder along the trajectory; **λ⋆≈1 with no
lift** means λ=1 holds in the basin regime and a λ grid is not worth running.

**Planned cells.** backbones {`mlp_mnist`, `vit_b32_cifar100`} × N {10} ×
α {0.05, 1.0} × method {`raw_union_K20`} × seed {42} = 4 cells, each evaluating the
λ grid {0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0} (9 points). The λ=0 column
reproduces the standalone θ₀ accuracy; the λ=1 column reproduces the headline
aggregate accuracy.

**Per-cell report (auto):** the acc-vs-λ curve, the argmax λ⋆, acc(λ⋆) − acc(λ=1)
(the lift over the pinned λ=1), and standalone θ₀ acc (= the λ=0 point).

Run: `sbatch jobs/heifd_026_lambda_verify.sh` (after login-node prefetch
`python jobs/prefetch_login.py --include-cifar100` for the ViT/CIFAR-100 cell).
