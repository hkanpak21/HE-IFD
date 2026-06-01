# 006 — Aggregation-coherence ablation  [AFK]

> **STATUS: 📦 CODE MERGED, JOB HELD** (2026-05-28).
>
> New module `src/ablation.py` (4 regimes: heifd / converged-shared-init / converged-diff-init / unbounded-distill-shared) + per-client ‖Δᵢ‖ displacement tracking + `jobs/heifd_coherence_ablation.sh` — reuses existing aggregate/distill/teacher primitives without modifying them (`808b087`).
> **Why held:** sbatch runs on `mlp_mnist` + `cnn5_cifar10`; cnn5 has a 27pp IID gap to oracle (under-trained at 10 teacher epochs), so a CIFAR-10 ablation run now would produce misleading numbers.
> **Continuation:** queue `sbatch jobs/heifd_coherence_ablation.sh` after issue **011** (trainable-layer scope, which will fix the cnn5 regime) lands.

**Milestone:** M1 · **Blocked by:** 001, 003 · **Blocks:** 009

**Required reading:** [`docs/prd/...`](../prd/he-ifd-tnse-resubmission.md) (user story 17, the "basin coherence" argument), [`CLAUDE.md`](../../CLAUDE.md) ("The current method").

## What to build

A runnable experiment that demonstrates *why* the design works: **bounded-from-shared-aligned-init** aggregation lands in one loss basin, whereas naive averaging of divergent models does not. Compare, on the same setup, the final-student accuracy of:

1. **HE-IFD (ours):** bounded K-step displacements from a shared aligned `θ₀`, sample-weighted linear aggregate.
2. **Naive average of independently-converged students** (each trained to convergence on its own data).
3. **Naive average of full-fine-tuned students** (large displacement from init).
4. **Average of students from different random inits** (different basins).

This is the empirical evidence for the central design choice and preempts the "isn't this just FedAvg-averaging?" reviewer reflex.

## Acceptance criteria

- [ ] All four variants run on a shared cell (e.g. CIFAR-10 from-scratch, a low and a mid α) across 3 seeds.
- [ ] Results written to `results/heifd_<model>_<dataset>_coherence-ablation/` per the convention.
- [ ] The ablation shows (1) clearly above (2)–(4) at low α — the coherence claim holds — or, if not, the finding is reported honestly.

## How to verify

`sbatch` the ablation; read `results/<case>/README.md`. Expect HE-IFD ≫ the naive-average variants at low α.

## Ops

`sbatch` only; `--time` ≤ 03:00:00 (chunk if needed). `results/<case>/` convention.
