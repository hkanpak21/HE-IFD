# heifd_027_merf_verify — DP-MERF generator soundness fix (before/after)

> Placeholder README (issue 027). The sweep auto-writer (`src/report.py`)
> overwrites this file with the populated results table once the 10 cells land;
> the bug, the fix, and the expected before/after documented here are the
> standing description of the case.

## The bug this case corrects

The DP-MERF generator built in issue 022 was **NOT differentially private**. The
old `_merf_generate_class` (src/phase0.py) privatized the φ-space mean embedding
but then **released real records**:

```python
pick = rng.choice(m, size=n_gen, replace=True, p=w)   # w from the DP mean
base = X_c[pick]                                        # <-- RAW real records
samples = base + 0.5 * rng.normal(...) * std           # + cosmetic jitter
```

So the released "synthetic" set contained real data → **no sample-level DP
guarantee**. Mode A (`dp_synth_all`) consequently reached an implausible
**0.97 @ ε=2 on MNIST** because the DP never bit. The 022 verify's inverted
contrast (Mode A accuracy **>** Mode B accuracy at tight ε) was an **artifact of
this leak, not a finding**.

## The fix (DP-sound generator)

`_merf_generate_class` now:

1. computes the per-class **privatized RFF mean embedding** `μ̂^priv` (RFF map +
   `dp_sigma(clip=1, m, eps, δ)` Gaussian noise; clip=1 because ‖φ‖₂=1 by
   construction; **ε=∞ ⇒ σ=0**, the raw-MERF ceiling — preserved);
2. **trains a small neural generator G** (2-layer MLP, latent=16, ~400 Adam
   steps) `z ~ N(0,I) ↦ x̂` minimizing the **random-feature MMD**
   `‖ (1/B)·Σ_b φ(G(z_b)) − μ̂^priv ‖₂²`, re-embedding generated points with the
   **same ω** as the real embedding (DP-MERF, Harder et al. 2021);
3. **samples `n_gen` fresh points** `x̂ = G(z)` — the released set is **draws from
   G, never `X_c`**. After `μ̂` is privatized, G's training and sampling are pure
   post-processing of a DP quantity + fresh generator noise, so the released
   samples inherit the (ε, δ) guarantee.

A **runtime guard** (`_merf_assert_synthetic_disjoint`) asserts no released
sample is within `atol=1e-6` L2 of any raw record, and
`tests/test_merf_dpsound.py` pins the invariant (both modes). Both builders
(`build_dp_synth_all` Mode A, `build_probe_merf` Mode B) call the same fixed
function, so this one fix corrects both.

Residual non-DP statistic (documented MVP caveat): the median-heuristic
bandwidth `σ_φ` and the frequency draw `ω` are computed on raw `X_c` and
influence G only via the kernel they define (a public DP-MERF hyperparameter),
never as a released output. The hard invariant — no released sample equals a real
record — holds with zero exceptions regardless.

## The 2-cell re-verify (this case fills in the after)

Grid: backbones {`mlp_mnist`, `vit_b32_cifar100`} × methods
{`dp_synth_all_eps2`, `dp_synth_all_eps8`, `merf_basin_eps2_K20`,
`merf_basin_eps8_K20`, `raw_union_K20`} × α=0.05 × N=10 × seed=42 = 10 cells
(`sbatch jobs/heifd_027_merf_verify.sh`).

**Expected tell it is fixed:**

| method | before (buggy generator) | after (DP-sound generator, expected) |
|---|---|---|
| `dp_synth_all_eps2` (Mode A, MNIST) | **~0.97** (artifact — DP never bit) | **drops** — DP now bites at ε=2 |
| `dp_synth_all_eps8` (Mode A, MNIST) | inflated | above eps2, still well below the old 0.97 |
| `merf_basin_eps2_K20` (Mode B) | competitive | competitive (≈ `raw_union_K20`) — basin only aligns; bulk is HE-protected |
| `merf_basin_eps8_K20` (Mode B) | competitive | competitive |
| `raw_union_K20` (ref) | no-DP ceiling | no-DP ceiling (unchanged) |

Corrected contrast: `merf_basin ≈ raw_union ≫ dp_synth_all` at ε=2 — the inverted
022 contrast is gone, and Mode A is now a **legitimate DP-one-shot baseline**
whose released model the MIA suite (028) can attack. Actual numbers populate here
once the cells land.

## How the metrics read

Standard `CellResult` columns (`src/report.py`): IID `acc` is the lead, with
`mean_teacher` / `best_teacher` / `oracle` references and `theta0_acc` (the
aligned init before distillation; fresh-init accuracy for Mode A column parity).
`σ` is the DP noise scale on the released per-class RFF mean embedding (0.0 at
ε=∞; larger as ε shrinks).

## COLLECTED RESULTS (Colab run, 2026-05-30) — pytest 9 passed; 10 cells

| backbone | α | method | acc | θ₀_acc | mean_teacher | oracle | M3_mean_gap |
|---|---|--------|-----|--------|--------------|--------|-------------|
| mlp_mnist | 0.05 | dp_synth_all_eps2 (Mode A) | **0.7776** | 0.0887 | 0.3328 | 0.9735 | −0.2148 |
| mlp_mnist | 0.05 | dp_synth_all_eps8 (Mode A) | 0.7835 | 0.0887 | 0.3328 | 0.9735 | −0.2105 |
| mlp_mnist | 0.05 | merf_basin_eps2_K20 (Mode B) | 0.5726 | 0.2377 | 0.3328 | 0.9735 | −0.4173 |
| mlp_mnist | 0.05 | merf_basin_eps8_K20 (Mode B) | 0.6217 | 0.3511 | 0.3328 | 0.9735 | −0.3546 |
| mlp_mnist | 0.05 | raw_union_K20 (ref) | 0.8466 | 0.8698 | 0.3328 | 0.9735 | −0.1358 |
| vit_b32_cifar100 | 0.05 | dp_synth_all_eps2 (Mode A) | **0.6490** | 0.0121 | 0.2252 | 0.8692 | −0.3232 |
| vit_b32_cifar100 | 0.05 | dp_synth_all_eps8 (Mode A) | 0.7848 | 0.0121 | 0.2252 | 0.8692 | −0.1796 |
| vit_b32_cifar100 | 0.05 | merf_basin_eps2_K20 (Mode B) | 0.2902 | 0.0173 | 0.2252 | 0.8692 | −0.6992 |
| vit_b32_cifar100 | 0.05 | merf_basin_eps8_K20 (Mode B) | 0.3506 | 0.1011 | 0.2252 | 0.8692 | −0.6334 |
| vit_b32_cifar100 | 0.05 | raw_union_K20 (ref) | 0.7709 | 0.8091 | 0.2252 | 0.8692 | −0.1903 |

**Primary gate PASSED:** Mode A `dp_synth_all_eps2` dropped from the old bogus
**~0.97 → 0.7776 (MNIST) / 0.6490 (ViT)** — the DP now bites, the artifact is gone,
the generator is honestly DP.

**⚠️ Narrative DEVIATION (decision needed, not auto-resolved):** the 022 framing
expected `Mode B ≈ raw_union ≫ Mode A`. The honest numbers are the **opposite**:
`raw_union > Mode A (dp_synth_all) > Mode B (merf_basin)`. Mode B privatizes only
K=20 samples/class → large σ → weak basin θ₀ (acc 0.24 MNIST / 0.017 ViT); Mode A
privatizes all data/class → small σ → decent synthetic. Once the DP is real,
"synthesize everything" beats "synthesize a few for the basin," and DP-MERF is NOT
a competitive basin vs raw_union. **Open question for the PIs:** tune the Mode-B
generator (more capacity/K, at higher DP cost) vs reframe/drop the synthetic-basin
angle (raw_union/dp_avg prototypes remain the basin).
