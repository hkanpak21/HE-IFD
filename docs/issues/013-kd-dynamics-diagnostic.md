# 013 — KD dynamics diagnostic  [AFK]

> **STATUS: 📥 OPEN** (2026-05-28) — ready to claim.

**Phase:** M1.5 / α (empirical-evidence anchor) · **Blocked by:** none · **Blocks:** nothing; informs interpretation of 010/011/012

**Required reading:**
1. `docs/prd/he-ifd-tnse-resubmission.md` (Phase II).
2. `CLAUDE.md`.
3. `docs/issues/008-pretrained-headline-sweep.md` STATUS (the θ₀≥final phenomenon).
4. `src/distill.py`, `src/protocol.py`, `src/aggregate.py`.

## Why

While 010 (KD hyperparams) and 011 (trainable-layer scope) try *fixes*, this issue *measures* what is going wrong. If teachers at low α produce near-one-hot KL targets and per-client Δᵢ point in opposing directions (small or negative pairwise cosine), the basin-cancellation hypothesis is empirically grounded. If not, alternative hypotheses emerge.

## What to build

1. New module `src/diagnostics.py` with hooks called from `local_distill_trajectory` and `aggregate` when a `diagnose=True` flag is set:
   - **Teacher logit entropy** on the augmented probe per client (mean + std). At α=0.05 expect near-zero (peaky).
   - **Per-client Δ trajectory**: `‖Δᵢ⁽ᵏ⁾‖₂` for k = 0…K (step-wise) and cumulative `‖Δᵢ‖₂` at end.
   - **Pairwise cosine matrix**: `cosine(Δᵢ, Δⱼ)` for all i ≠ j. Near-zero or negative = disagreement → cancellation.
   - **Per-class accuracy** of θ₀ vs final on the test set (which classes does distillation actually move?).
2. Persist diagnostics in the cell JSON under a new `diagnostics` field (extends `CellResult` with an optional dict).
3. Run on exactly two cells for contrast:
   - `resnet18_cifar10 / α=0.05 / N=10 / raw_union_K20 / seed 42` — the degrading case.
   - `mlp_mnist / α=0.05 / N=10 / raw_union_K20 / seed 42` — the working case.
4. Produce a one-page diagnostic summary: a CSV/markdown table + 2–3 small plots (entropy histogram, ‖Δ‖ distribution, cosine matrix heatmap). Persist under `results/heifd_013_kd_diagnostic/`.

## Acceptance

- [ ] `src/diagnostics.py` + protocol hook (no semantic change to distillation/aggregation).
- [ ] Both diagnostic cells run; `diagnostics` JSON populated.
- [ ] One-paragraph interpretation in the case README: which hypothesis is supported by the data? (basin-cancellation vs teacher-overshoot vs capacity-constraint).
- [ ] Pointer for 010/011's path forward.

## Hard boundaries

- New file `src/diagnostics.py`; optional `diagnose` flag added to `src/distill.py` + `src/protocol.py` (no semantic change unless diagnose=True).
- No push/commit/sbatch/ssh.
- ast.parse only.

## Report

1. Diagnostic numbers from both cells (concise).
2. Hypothesis verdict (which one(s) the data support).
3. Files touched.
