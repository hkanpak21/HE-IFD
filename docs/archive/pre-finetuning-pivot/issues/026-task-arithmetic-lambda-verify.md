# 026 — Task-arithmetic scaling coefficient (λ): cheap verify before any grid  [AFK]

> **STATUS: ✅ DONE** (2026-05-30) — landed on Colab; results in `results/heifd_026_lambda_verify/`. Eval-only verify (no retraining). Decided at the 2026-05-30 three-thread grill ("verify λ cheaply first"). A fuller λ grid is gated on user sign-off (see Outcome).

**Phase:** M2.5 (aggregation design) · **Blocked by:** none · **Blocks:** the "why depth-1 / why λ" paragraph in the aggregation section + the decision on whether a λ grid is worth running.

**Required reading:**
1. `CLAUDE.md` (VALAR/sbatch/3h cap; never python on login node; the method note).
2. `src/aggregate.py` — the linear `aggregate(theta0, deltas, weights)` (the only server op).
3. `src/protocol.py`, `src/evaluate.py` — how θ⋆ is produced and scored.
4. Memory `aggregation-framing.md` — the task-arithmetic reframe and why this is the one HE-legal knob.

## Why

Our server op θ⋆ = θ₀ + Σⱼ wⱼ·Δⱼ **is task arithmetic** (Ilharco et al. 2023, `ilharco2023editing`) with the scaling coefficient pinned to **λ = 1**. The one optimization lever that fits {one-shot, HE depth-1} and that we have **never tested** is λ in

> θ⋆(λ) = θ₀ + λ·Σⱼ wⱼ·Δⱼ.

It collapses to an **interpolation**:  θ⋆(λ) = (1−λ)·θ₀ + λ·θ⋆(1). So sweeping λ is sliding along the line between the basin θ₀ (λ=0) and the current aggregate θ⋆(1) (λ=1) — **eval-only, no retraining**. It also tests the "alignment does most of the work" finding head-on: a peak at **λ<1** means the basin deserves more trust (down-weight the displacement); **λ>1** means push harder along the trajectory. λ stays a public scalar → still depth-1 under HE. Verify cheaply BEFORE committing any grid.

## What to build

1. **λ-scaling in `aggregate`**: add a `lambda_scale: float = 1.0` parameter to the linear aggregate so it computes θ₀ + λ·Σⱼ wⱼ·Δⱼ. Default 1.0 → **byte-identical** to current behaviour. (Per-layer λ is an optional stretch; global λ first.)
2. **λ-sweep eval harness**: given the θ₀ and the {Δⱼ, wⱼ} (or θ⋆(1)) a normal `run_cell` already produces, evaluate θ⋆(λ) for λ ∈ {0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0} on the test set — reuse the single trajectory; do not retrain per λ.
3. **Cheap verify cells**: `mnist_mlp` + `vit_b32_cifar100`, N=10, α ∈ {0.05, 1.0}, `raw_union` basin, K = backbone default. Per cell report: test-acc-vs-λ curve, argmax λ⋆, and acc(λ⋆) − acc(λ=1). Also report standalone θ₀ acc (= λ=0) for context.
4. **Wrapper** `jobs/heifd_026_lambda_verify.sh` (CLAUDE.md template, ≤3h — this is fast: one trajectory + 9 evals per cell). case `heifd_026_lambda_verify`, placeholder README stating the question.

## Acceptance
- [x] `lambda_scale` threaded into `aggregate`; default 1.0 byte-identical (λ folded into each weight); ast.parse clean.
- [x] λ-sweep eval produces the acc-vs-λ curve + argmax + Δ-vs-(λ=1) per cell, eval-only (no per-λ retrain) — `run_cell(lambda_scales=…)` + `CellResult.lambda_curve` + `src/lambda_verify.py`.
- [x] Verify cells landed in `results/heifd_026_lambda_verify/`; README reports λ≠1 helps in the basin regime.

## Hard boundaries
- Touch `src/aggregate.py` (add `lambda_scale`), a small eval harness (new module or a `sweep` flag), `jobs/heifd_026_*.sh`, the case README. Do NOT change `distill.py`/`phase0.py` semantics or the default aggregate path. No `git push`/`commit`/`sbatch`/`ssh`. Mac has no torch — ast.parse only.

## Report
1. How `lambda_scale` threads through; confirmation λ=1 is byte-identical.
2. The acc-vs-λ curves for the 4 cells + the argmax λ⋆ and the lift over λ=1.
3. Recommendation: is a λ grid worth running, or does λ=1 hold in the basin regime?

## Outcome — DONE (2026-05-30, Colab; `results/heifd_026_lambda_verify/`)

Ran on Colab (VALAR queue backed up). `lambda_scale` landed in `aggregate` (λ=1 byte-identical), opt-in
`run_cell(lambda_scales=…)` + `CellResult.lambda_curve`, harness `src/lambda_verify.py`. 4 cells, seed 42,
λ∈{0,0.25,…,2.0}.

| backbone | α | θ₀ (λ=0) | acc(λ=1) | λ⋆ | acc(λ⋆) | lift over λ=1 |
|---|---|---|---|---|---|---|
| mlp_mnist | 0.05 | 0.8698 | 0.8466 | **0.25** | 0.8702 | **+0.0236** |
| mlp_mnist | 1.0 | 0.8963 | 0.9390 | 1.00 | 0.9390 | +0.0000 |
| vit_b32_cifar100 | 0.05 | 0.8091 | 0.7709 | **0.00** | 0.8091 | **+0.0382** |
| vit_b32_cifar100 | 1.0 | 0.8494 | 0.8577 | 1.00 | 0.8577 | +0.0000 |

**Finding.** Near-IID (α=1.0): λ⋆=1, lift 0 — the pinned λ=1 is optimal. High heterogeneity (α=0.05): λ⋆<1
with a real lift; **ViT λ⋆=0 means the basin θ₀ alone beats the distilled aggregate** (negative distillation
lift on that cell). λ is the one HE-legal knob and it matters off-IID.

**Recommendation.** λ=1 holds in the homogeneous regime; λ<1 (or per-α λ) helps under heterogeneity. A
fuller λ grid (more seeds / α / backbones) is worth running **only if the paper leans on the heterogeneous
regime** — single-seed (42) here. **Gated:** do not launch the grid without user sign-off.
