# 017 — No-probe DP-common-basin alignment  [AFK]

> **STATUS: ✅ DONE** (2026-05-29) — **THESIS WIN**. No-probe grid 375/375 (empty-client reshape bug fixed mid-flight). In the weak-θ₀ / low-leak regime the HE distillation carries the model with **large lift** (acc−θ₀ = +0.17 to +0.60 across α), vs thin +0.06–0.08 when a fat probe pre-strengthens θ₀. **Cost-of-no-probe is NEGATIVE** (no-probe ≥ with-probe for dp_avg_eps2: −0.11 at α=0.01 → −0.014 at α=1.0) ⇒ the fully-DP, no-public-data deployment is competitive. This is the cleanest evidence the secure distillation — not the alignment scaffold — is the engine. Verdict: `results/heifd_017_noprobe_mlp/README.md` (+ `_verify`).

**Phase:** M1.5 / γ (alignment-strategy expansion) · **Blocked by:** none · **Blocks:** nothing

**Required reading:**
1. `docs/prd/he-ifd-tnse-resubmission.md` (Phase II).
2. `CLAUDE.md`.
3. `src/phase0.py` — `build_probe_*` builders + `warmup_init`.
4. `src/protocol.py` — `run_cell`, especially every call site of the labelled probe + `warmup_init`.

## Why

The current pipeline uses a *labelled public probe* in two places: the `labelled_probe_warmup`/`warmup_only_labelled` baselines, AND as the supervised dataset for the `warmup_init` call in `raw_union` / `dp_avg` paths (the warmup head is trained supervised on the probe-derived data). The "no public data at all" deployment story requires removing the labelled probe entirely.

## What to build

1. New phase0 strategies: `noprobe_dp_avg`, `noprobe_raw_union`. In these:
   - There is no labelled probe `(probe_X, probe_y)` available to `run_cell`.
   - The (DP-noisy or raw-union) per-class **prototypes themselves** become the supervised dataset for `warmup_init`: each prototype is a single feature-space sample with its class as label. Train the warmup classifier on this small dataset (typically `num_classes × N_clients_with_that_class` samples = ~tens to hundreds of points).
2. Refactor `run_cell` so it can branch into the no-probe path: if `phase0_kind in {"noprobe_dp_avg", "noprobe_raw_union"}`, build prototypes first, then call `warmup_init` with the prototype-set as the labelled dataset (no `probe_X` involved).
3. Method-name parsing: `noprobe_dp_avg_eps<ε>_K<K>`, `noprobe_raw_union_K<K>`. Extend `parse_method`.
4. New wrapper `jobs/heifd_017_noprobe_mlp.sh`: MNIST/MLP, methods `noprobe_dp_avg_eps2_K20`, `noprobe_dp_avg_eps8_K20`, `noprobe_raw_union_K20`, full N+α grid, 3 seeds. Compare to the corresponding *with-probe* baselines (already in M1).

## Acceptance

- [ ] No-probe variants runnable end-to-end on MNIST/MLP.
- [ ] Quantify the **cost of removing the probe** (Δacc between `dp_avg_eps2_K20` and `noprobe_dp_avg_eps2_K20`) per α.
- [ ] Two-paragraph note in case README: verdict — is the no-probe variant viable (i.e., not dramatically worse than the with-probe variant)?

## Hard boundaries

- Touch `src/phase0.py`, `src/protocol.py` (run_cell + parse_method). New wrapper.
- No push/commit/sbatch/ssh. ast.parse only.

## Report

1. Design choice for the no-probe warmup (how warmup_init proceeds without a labelled probe).
2. Cost-of-no-probe figure (Δacc table per α and ε).
3. Files touched.
