# 022 — Synthetic-basin study: DP-synthesize-everything vs DP-few-for-basin + HE (DP-MERF)  [AFK]

> **STATUS: 📥 OPEN** (2026-05-29) — dispatched as a worktree agent. Implements the code; VALAR runs submitted separately.

**Phase:** M1.5 / γ extension (alignment-source) · **Blocked by:** none · **Blocks:** the alignment-source comparison table + the synthetic-basin paragraph.

**Required reading:**
1. `CLAUDE.md`. 2. `src/phase0.py` — existing builders incl. `build_probe_synthetic` (Gaussian MVP) + the
averaging-variant DP math. 3. `src/protocol.py` — `parse_method`, phase0 dispatch. 4. `docs/paper/sections/method.tex` §5.2 (shared loss basin, interchangeable sources) + §5.5 (privacy).

## Why — the contrast to demonstrate (the paper's value proposition, made concrete)

A DP synthetic-data generator can be used two ways. We show the gap between them:

- **Mode A — DP-synthesize everything (naive one-shot, the DP-one-shot-FL baseline, cf. FedDiff).** A client
  fits a DP generator to *all* its data and the synthetic data carries the whole contribution. Covering all
  samples needs large DP noise → **accuracy drops and MIA still succeeds.**
- **Mode B — DP a few samples for the basin, HE for the rest (ours).** The DP generator is applied to only a
  few samples per class, even at tight ε, *solely to build the shared basin θ₀* (which need only align, not
  classify). The bulk of the contribution flows through the bounded distillation, protected **losslessly by
  HE.** → **good accuracy + cryptographic privacy on the real contribution.**

## What to build

**Generator: DP-MERF** (Harder et al. 2021 — DP random-feature kernel mean embeddings → generator; public
code; analytic sensitivity; the principled generalization of our per-class mean prototypes). Add to bib as
`harder2021dpmerf` (the agent need not edit the bib; the orchestrator will — just use the key).

1. **`build_probe_merf`** in `src/phase0.py`: DP-MERF basin source — release a DP mean-embedding per class
   from `K_pc` samples, fit a small generator, sample synthetic basin data. Reuse the averaging-variant DP
   accounting; expose ε. New method names `merf_basin_eps{E}_K{K}` (Mode B).
2. **Mode-A path**: a `dp_synth_all_eps{E}` method that fits DP-MERF to the *full* local data, generates a
   synthetic training set, and trains the student one-shot on it directly (no HE benefit, no bounded-basin
   distillation) — the baseline. Keep it a clearly-separate dispatch branch.
3. `parse_method` recognises both. Existing `synthetic`/`synthetic_dp` (Gaussian MVP) stay as the simpler
   comparison points.
4. Wrapper `jobs/heifd_022_synth_basin.sh`: backbones `mnist_mlp`, `vit_b32_cifar100`; methods
   `dp_synth_all_eps{2,8}`, `merf_basin_eps{2,8}_K20`, `raw_union_K20`, `dp_avg_eps2_K20`,
   `noprobe_dp_avg_eps2_K20`; α∈{0.05,0.3,1.0}; N=10; 3 seeds. case `heifd_022_synth_basin`.

## Acceptance
- [ ] DP-MERF basin builder + Mode-A path implemented; `parse_method` updated; existing behaviour byte-identical without the new method names.
- [ ] Cells produce: Mode-A accuracy (expected low under meaningful ε) vs Mode-B accuracy (expected ≈ raw/DP-prototype basin) — the contrast.
- [ ] Placeholder `results/heifd_022_synth_basin/README.md` documenting the Mode-A-vs-Mode-B question + the alignment-source comparison it feeds.
- [ ] (Hook for 021) Mode-A and Mode-B checkpoints exportable so the MIA suite can attack both — Mode A should be MIA-vulnerable; Mode B's bulk is HE-protected so only θ⋆ is attackable.

## Hard boundaries
- Touch `src/phase0.py`, `src/protocol.py` (parse_method + dispatch), `jobs/heifd_022_*.sh`, the case README.
- Do NOT change distill.py/aggregate.py semantics or existing builders. No `git push`/`commit`/`sbatch`/`ssh`. ast.parse only.

## Report
1. DP-MERF implementation + Mode-A vs Mode-B dispatch; citation/algorithm + any port decisions.
2. Files touched + boundary confirmation.
3. The wrapper grid + the contrast it tests.
