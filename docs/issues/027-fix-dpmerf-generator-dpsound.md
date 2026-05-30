# 027 — Fix the DP-MERF generator (make it DP-sound) + re-verify  [AFK]

> **STATUS: ✅ DONE — fix validated; ⚠️ open PI decision** (2026-05-30) — generator now DP-sound, primary gate passed (Mode A drops at ε=2), but the corrected numbers invert the 022 framing (see Outcome). Results in `results/heifd_027_merf_verify/`. **SUPERSEDES the generator built in 022.** Decided at the 2026-05-30 grill ("fix generator, keep both; DP-MERF done properly").

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
- [x] Generator samples fresh points from a DP-fit model; **never returns raw `X_c`** (guard `_merf_assert_synthetic_disjoint` + `tests/test_merf_dpsound.py`, 9 passed on Colab).
- [x] `dp_sigma` accounting reused; ε=∞ ⇒ zero noise; existing non-MERF builders byte-identical.
- [x] 2-cell re-verify shows the DP now bites (Mode A ε=2 dropped ~0.97 → 0.78 MNIST / 0.65 ViT) — before/after in `results/heifd_027_merf_verify/README.md`.
- [x] ast.parse clean on `src/phase0.py`.

## Hard boundaries
- Touch `src/phase0.py` (the generator + Mode A/B builders), a small test, `jobs/heifd_027_merf_verify.sh`, the case README. Do NOT change `distill.py`/`aggregate.py` semantics or the prototype/`dp_avg` builders. No `git push`/`commit`/`sbatch`/`ssh`. Mac has no torch — ast.parse only.

## Report
1. The DP-sound generator design + the soundness guard; the port decisions vs the reference repo.
2. The 2-cell before/after (old 0.97 artifact vs the corrected Mode A accuracy at ε=2).
3. Confirmation Mode A is now a legitimate DP-one-shot baseline whose released model the MIA suite (028) can attack.

## Outcome — DONE, fix validated; ⚠️ open decision (2026-05-30, Colab; `results/heifd_027_merf_verify/`)

`_merf_generate_class` now trains a small MLP generator G on the **privatized** RFF mean and samples fresh
`G(z)`; the raw-record `base = X_c[pick]` leak is **deleted**. Guard + 9-test suite pass on Colab. ε=∞⇒σ=0
preserved; prototype/dp_avg/synthetic/noprobe builders byte-identical.

**Primary tell — PASSED.** Mode A `dp_synth_all` ε=2 dropped from the old bogus **~0.97 → 0.7776 (MNIST) /
0.6490 (ViT)** — the DP bites, the artifact is gone.

| backbone | raw_union (ref) | Mode A ε2 / ε8 | Mode B ε2 / ε8 |
|---|---|---|---|
| mlp_mnist | 0.8466 | 0.7776 / 0.7835 | 0.5726 / 0.6217 |
| vit_b32_cifar100 | 0.7709 | 0.6490 / 0.7848 | 0.2902 / 0.3506 |

**⚠️ Deviation — needs a PI decision (gated; full 022 grid NOT re-run).** The 022 framing expected
`Mode B ≈ raw_union ≫ Mode A`. The honest numbers **invert** it: `raw_union > Mode A (dp_synth_all) >
Mode B (merf_basin)`. Mode B privatizes only K=20 samples/class → large σ → weak basin θ₀ (acc 0.24 MNIST /
0.017 ViT); Mode A uses all data/class → small σ → decent synthetic. So **DP-MERF is not a competitive
basin source once the DP is real.** Options: (a) tune the Mode-B generator (more capacity / K, at higher DP
cost), or (b) reframe/drop the synthetic-basin angle (raw_union / dp_avg prototypes remain the basin).
