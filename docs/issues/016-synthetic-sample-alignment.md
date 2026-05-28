# 016 — Synthetic-sample alignment strategy  [AFK]

> **STATUS: 📥 OPEN** (2026-05-28) — ready to claim.

**Phase:** M1.5 / γ (alignment-strategy expansion) · **Blocked by:** none (independent of α/β; can run alongside) · **Blocks:** nothing

**Required reading:**
1. `docs/prd/he-ifd-tnse-resubmission.md` (Phase II).
2. `CLAUDE.md`.
3. `src/phase0.py` — `build_probe_raw_union`, `build_probe_dp_averaged`, `dp_sigma`.
4. `src/protocol.py` — `parse_method`, `_load_features`, the phase0 dispatch inside `run_cell`.

## Why

Current alignment strategies: no_phase0, labelled_probe_warmup, raw_union, dp_avg. The user has called out **synthetic-sample alignment** as a desirable richer-payload variant: each client generates a small synthetic sample set per class and shares those (instead of mean prototypes) — potentially richer than a single mean vector, cheaper than sharing raw samples, and DP-protectable.

## What to build

1. New phase0 builder `build_probe_synthetic` in `src/phase0.py`. Pick the **simplest design that works first**, escalate only if results demand:
   - **MVP — Gaussian-around-mean**: per (client, class), compute the mean and per-feature variance from local samples; generate `K_pc` synthetic samples by `μ + N(0, diag(σ²))`. Trivial, no generator training, DP-protectable via the averaging variant (add Gaussian noise to μ; report the σ² along too OR keep σ² public if features are public-distribution-like).
   - **Escalation (only if MVP fails to differentiate from raw_union)**: per-client small Conditional VAE (a tiny encoder/decoder, 2–3 epochs on the local data) → sample K_pc per class from the latent prior.
2. New phase0 dispatch case: `synthetic`. New method names: `synthetic_K<K>` (no-DP) and `synthetic_dp_eps<ε>_K<K>` (DP-protected — apply the same averaging-variant accounting on the μ release).
3. Update `parse_method` to recognise the new method names.
4. New wrapper `jobs/heifd_016_synthetic_mlp.sh`: MNIST/MLP, `--methods synthetic_K20,synthetic_dp_eps2_K20,raw_union_K20,dp_avg_eps2_K20`, full N+α grid, 3 seeds. ~360 cells.

## Acceptance

- [ ] `build_probe_synthetic` builder + DP-protected variant implemented.
- [ ] MNIST/MLP cells with synthetic method run and produce sensible accuracy.
- [ ] Comparison: synthetic vs raw_union vs dp_avg at matched (ε, Kpc) — which is best at α=0.05?
- [ ] Two-paragraph note in case README: design rationale + comparison verdict + when synthetic is worth using vs the simpler mean-prototype.

## Hard boundaries

- Touch `src/phase0.py`, `src/protocol.py` (parse_method, dispatch). New wrapper.
- No push/commit/sbatch/ssh. ast.parse only.

## Report

1. Design choice (MVP vs escalation) and rationale.
2. MNIST/MLP comparison results (raw_union / dp_avg / synthetic / synthetic_dp).
3. Files touched.
