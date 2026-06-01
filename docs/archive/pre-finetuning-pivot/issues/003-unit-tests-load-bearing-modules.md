# 003 — Unit tests for load-bearing modules  [AFK]

> **STATUS: ⚠️ PARTIAL** (2026-05-28) — code merged; runtime verification pending.
>
> Behavior-level unit tests written for `aggregate` (FHE invariant + telescoping + basin), `phase0` (DP σ formula), `backbones` (GPT-2 regression), `data` (partition reproducibility) — `c1409f0` → merged `6f81645`. The test sbatch job (1112418) **FAILED** with `No module named pytest`: pytest is not installed in the `he_ofl` conda env.
> **Continuation (small):** on the VALAR login node, `pip install --quiet pytest` into `he_ofl`, then re-submit `jobs/heifd_tests.sh`. ~5 minute task. Folded into issue **010** (housekeeping bundle) or run standalone.

**Milestone:** M1 · **Blocked by:** 001 (002 for the backbones test) · **Blocks:** 006

**Required reading:** [`docs/prd/...`](../prd/he-ifd-tnse-resubmission.md) (Testing Decisions), [`CLAUDE.md`](../../CLAUDE.md).

## What to build

Behavior-level unit tests (verify external behavior through public interfaces, never internals) for the three modules where bugs are silent and correctness is load-bearing, plus one data assertion:

- **`aggregate`** — (a) FHE-compat invariant: result uses only addition + plaintext-scalar multiply (no non-linear ops); (b) telescoping: aggregating per-step deltas equals aggregating the cumulative displacement equals the sample-weighted average of finals; (c) basin-coherence: bounded deltas from a shared init aggregate to a usable model, while a constructed divergent set (different inits) does not.
- **`phase0`** — DP accounting: sensitivity = `clip / Kpc`; σ = `sensitivity · √(2 ln(1.25/δ)) / ε`; `ε=∞` ⇒ zero noise; prototype shapes/counts correct when some clients lack a class.
- **`backbones`** — the GPT-2 regression from 002 (non-trivial IID accuracy).
- **`data`** — Dirichlet partition is seed-reproducible; the public probe is disjoint from client training data.

## Acceptance criteria

- [ ] Tests for `aggregate`, `phase0`, `backbones`, `data` exist and pass.
- [ ] `aggregate` telescoping + linearity + basin tests present.
- [ ] `phase0` sensitivity/σ tests assert the exact formulae.
- [ ] Tests run via the project's test runner; fast ones runnable in a short `srun`; any needing a model go through `sbatch` with pre-fetched weights.

## How to verify

Run the suite; all green. The `aggregate` and `phase0` tests must encode the formulae from the PRD / methodology, so a future refactor that breaks the FHE invariant or the DP math fails loudly.

## Ops

Pure-tensor tests need no GPU and can run in a short `srun`/`sbatch`; never python on the login node for anything importing torch.
