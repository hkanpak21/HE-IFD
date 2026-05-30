# 027 — Fix the DP-MERF generator (make it DP-sound) + re-verify  [AFK]

> **STATUS: 📥 OPEN** (2026-05-30) — **SUPERSEDES the generator built in 022.** Decided at the 2026-05-30 grill ("fix generator, keep both; DP-MERF done properly").

**Phase:** M2.5 (privacy / alignment source) · **Blocked by:** none · **Blocks:** the synthetic-basin study (022) AND the DP-one-shot-baseline MIA contrast ("crypto leaks less than DP").

**Required reading:**
1. `CLAUDE.md`.
2. `src/phase0.py` — `_merf_generate_class`, `build_probe_merf` (Mode B), `build_dp_synth_all` (Mode A), and the averaging-variant `dp_sigma` accounting.
3. `results/heifd_022_verify/` — the inverted verify (Mode A 0.97 @ ε=2 on MNIST) that this fix must correct.
4. Memory `aggregation-framing.md` and the DP-MERF note in `MEMORY.md`.

## Why — the current generator is NOT differentially private

`_merf_generate_class` (src/phase0.py) emits

```python
base = X_c[pick]                                # RAW real records
samples = base + 0.5 * rng.normal(...) * std    # + fixed, NON-DP jitter
```

The DP Gaussian noise is added only to the φ-space mean embedding that sets the resampling weights `w`; the **released samples are real records plus cosmetic jitter**. So:
- the released "synthetic" set contains real data → **no sample-level DP guarantee**;
- Mode A (`dp_synth_all`) reaches an implausible **0.97 @ ε=2** on MNIST because the DP never bites → the 022 verify's **inverted contrast (Mode A > Mode B accuracy) is an artifact, not a finding.**

This must be fixed before *any* 022 number (accuracy or MIA) means anything.

## What to build

1. **A DP-sound generator** replacing the closed-form stand-in. Train a small generator network G (per client; per-class or class-conditional) to match the **DP-privatized RFF mean embedding** via the random-feature MMD objective (DP-MERF, Harder et al. 2021, `harder2021dpmerf`), then **sample fresh points from G**. The released basin samples must be **draws from G — never `X_c` (raw records)**. Reuse the analytic `dp_sigma` accounting (clip=1 from unit-norm RFF); ε=∞ → no noise (raw-MERF ceiling). Crib correctness from the reference repo (`github.com/ParkLabML/DP-MERF`) **without** taking it as a runtime dependency. Keep G small + GPU-optional (basin source, not a production generator).
2. **A code-level guard + test** asserting the generator output is disjoint from / not a copy of the raw `X_c` (the soundness invariant: no released sample equals a real record).
3. **Re-verify 2 cells** (`mnist_mlp`, `vit_b32_cifar100`; α=0.05; ε ∈ {2, 8}): the **tell it's fixed** — Mode A accuracy now **drops at tight ε** (the 0.97 artifact disappears) and the Mode-A-vs-Mode-B contrast corrects (Mode B basin competitive or better at meaningful ε). Attach before/after.
4. Only after the verify looks right does 022's full grid (both modes, ε/α) get re-run — that scaling is a separate submission, not this issue.

## Acceptance
- [ ] Generator samples fresh points from a DP-fit model; **never returns raw `X_c`** (guard + test).
- [ ] `dp_sigma` accounting reused; ε=∞ ⇒ zero noise; existing non-MERF builders byte-identical.
- [ ] 2-cell re-verify shows the DP now bites (Mode A accuracy drops at ε=2 vs the old 0.97) — before/after attached in `results/heifd_027_merf_verify/README.md`.
- [ ] ast.parse clean on `src/phase0.py`.

## Hard boundaries
- Touch `src/phase0.py` (the generator + Mode A/B builders), a small test, `jobs/heifd_027_merf_verify.sh`, the case README. Do NOT change `distill.py`/`aggregate.py` semantics or the prototype/`dp_avg` builders. No `git push`/`commit`/`sbatch`/`ssh`. Mac has no torch — ast.parse only.

## Report
1. The DP-sound generator design + the soundness guard; the port decisions vs the reference repo.
2. The 2-cell before/after (old 0.97 artifact vs the corrected Mode A accuracy at ε=2).
3. Confirmation Mode A is now a legitimate DP-one-shot baseline whose released model the MIA suite (028) can attack.
