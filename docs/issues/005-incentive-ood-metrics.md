# 005 — Incentive (M3) + OOD (M4) + θ₀ + no-align metrics  [AFK]

**Milestone:** M1 · **Blocked by:** 001 · **Blocks:** 007, 008

**Required reading:** [`docs/prd/...`](../prd/he-ifd-tnse-resubmission.md) (user stories 11, 23–26), [`CLAUDE.md`](../../CLAUDE.md).

## What to build

Wire four reporting quantities into `evaluate.py` + `report.py` so the headline sweeps (007/008) **emit them inline in the same job** — no separate full re-run:

- **M3 — per-client teacher-vs-aggregate gap:** for each client *i*, `acc(global_student, D_i) − acc(Tᵢ, D_i)`. Positive ⇒ federation helped client *i*. (Answers the TDSC "unjustified incentive" complaint.)
- **M4 — OOD-class accuracy at low α:** for each client *i*, accuracy of the global student on test examples from classes *i* held **zero** local examples of. (The "averaged all-label student handles OOD samples the local teacher never saw" value-prop.)
- **Standalone θ₀ accuracy:** test accuracy of the initial aligned student `θ₀` that clients receive, *before* any local distillation.
- **No-alignment baseline:** the cell run with Phase 0 disabled.

Already-present references (mean/best/oracle teacher) stay.

## Acceptance criteria

- [ ] `evaluate` computes M3, M4, and standalone-θ₀ accuracy given the per-client partitions + teachers + final student.
- [ ] `report` writes these columns into `results/<case>/results.csv` and the README table.
- [ ] M4 is reported at low α (and skipped/marked N/A at α=1.0 where it is vacuous).
- [ ] These are produced **within** a normal sweep cell — no dedicated extra job.

## How to verify

Run one low-α cell; confirm the report contains M3 (signed per-client gaps + summary), M4 (OOD-class acc), standalone θ₀ accuracy, and a no-alignment baseline row.

## Ops

`sbatch` only. Follow the `results/<case>/` convention.
