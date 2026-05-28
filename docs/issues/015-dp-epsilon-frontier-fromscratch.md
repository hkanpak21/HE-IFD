# 015 — DP-ε frontier sweep on from-scratch  [AFK]

> **STATUS: 📥 OPEN** (2026-05-28) — partially blocked by 014 for FMNIST + CIFAR-10 portions.

**Phase:** M1.5 / β · **Blocked by:** 014 for FMNIST + CNN-5; standalone for MNIST/MLP · **Blocks:** nothing

**Required reading:**
1. `docs/prd/he-ifd-tnse-resubmission.md` (Phase II).
2. `CLAUDE.md`.
3. `src/phase0.py` — averaging-variant DP accounting (`dp_sigma`, `build_probe_dp_averaged`).
4. `src/protocol.py` — `parse_method` (handles `dp_avg_eps<ε>_K<K>` already).

## Why

Current DP method panel has only `dp_avg_eps2_K20` and `dp_avg_eps8_K20`. The averaging-variant DP claim (`methodology.md` §7 and `paper headline`) lives on a *frontier* — we need ε ∈ {0.5, 2, 8, 32, ∞} and Kpc ∈ {1, 5, 20} to show whether the frontier flattens from ε ≈ 2 onward as claimed.

## What to build

1. Extend the method panel with:
   - ε values: `dp_avg_eps0.5_K20`, `dp_avg_eps32_K20`, `dp_avg_epsinf_K20` (= raw_union with the DP-noise machinery set to σ=0 — sanity reference).
   - Kpc values: `dp_avg_eps2_K1`, `dp_avg_eps2_K5`, `dp_avg_eps8_K1`, `dp_avg_eps8_K5`.
   - Confirm `parse_method` handles all these (string parsing should already; verify or extend).
2. New wrapper `jobs/heifd_015_dp_frontier_mlp.sh` running on `mlp_mnist`. Axes: the expanded method panel × `--Ns 10` × `--alphas 0.05,0.3,1.0` × `--seeds 42,43,44`. ~90 cells (already small; mlp_mnist cells are fast).
3. After 014 lands: analogous wrappers for `lenet_fmnist` and `cnn5_cifar10`.
4. Produce DP-frontier figure data: per (backbone, α), table of (ε, Kpc) → acc with seed-mean ± std.

## Acceptance

- [ ] DP-frontier curve on MNIST/MLP for α ∈ {0.05, 0.3, 1.0} (acc vs ε at fixed Kpc=20; and acc vs Kpc at fixed ε ∈ {2, 8}).
- [ ] Verdict in the case README: does the averaging-variant DP frontier flatten from ε ≈ 2 onward? (Y/N + the numbers.)
- [ ] Extended to LeNet/FMNIST + CNN-5/CIFAR-10 after 014.

## Hard boundaries

- New sbatch wrappers; verify `parse_method` already handles the new method strings (extend if not).
- No push/commit/sbatch/ssh. ast.parse only.

## Report

1. MNIST/MLP DP-frontier table.
2. Verdict on the averaging-variant flatness claim.
3. Files touched.
