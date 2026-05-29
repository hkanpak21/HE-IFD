# heifd_022_synth_basin — DP-MERF synthetic-basin study (Mode A vs Mode B)

> Placeholder README (issue 022). The sweep auto-writer (`src/report.py`) overwrites
> this file with the populated results table once cells land; the question and the
> grid documented here are the standing description of the case.

## The question this case answers

A DP synthetic-data generator (here **DP-MERF** — Harder et al. 2021,
`harder2021dpmerf`: differentially-private random-feature kernel mean embeddings →
generator) can be used two ways. This case measures the **gap** between them on the
same backbones, partitions, and seeds:

- **Mode A — DP-synthesize EVERYTHING** (`dp_synth_all_eps{2,8}`): the naive
  DP-one-shot-FL baseline (cf. FedDiff). DP-MERF is fit to **all** of a client's
  local data; the synthetic set must carry the **whole** contribution, and the
  student is trained one-shot **directly** on it — no shared basin, no bounded
  distillation, no HE benefit. Covering every sample at meaningful ε forces large
  DP noise, so **accuracy is expected to drop and the released model stays
  MIA-vulnerable.**
- **Mode B — DP a FEW samples for the basin, HE for the rest (ours)**
  (`merf_basin_eps{2,8}_K20`): DP-MERF is applied to only `K_per_class=20` samples
  per class, even at tight ε, **solely to build the shared basin θ₀** (which need
  only *align* clients in one loss region, not classify). The bulk of each client's
  contribution then flows through the **bounded distillation**, protected
  **losslessly by HE**. → **good accuracy + cryptographic privacy on the real
  contribution.**

Expected verdict: `merf_basin_eps2_K20 ≈ {raw_union_K20, dp_avg_eps2_K20}` (the
basin sources) **≫** `dp_synth_all_eps2` (synthesize-everything). That is the
paper's value proposition made concrete.

## How the metrics read

Standard `CellResult` columns (`src/report.py`): IID `acc` is the lead, with
`mean_teacher` / `best_teacher` / `oracle` references and `theta0_acc` (the aligned
init before distillation). For Mode A there is no basin, so `theta0_acc` reports the
fresh-init accuracy for column parity and `acc` is the synthetic-trained student.
`σ` is the DP noise scale on the released per-class mean embedding (0.0 at ε=inf;
larger as ε shrinks). M3 / M4 are populated for both modes.

## Reference (non-DP-MERF) rows in the same grid

These pin Mode B against the existing interchangeable basin sources
(`method.tex` §5.2):

- `raw_union_K20` — no-DP alignment ceiling for the basin.
- `dp_avg_eps2_K20` — DP per-class **mean prototype** basin (with labelled probe);
  the first-moment special case that DP-MERF generalizes to a privatized
  random-feature mean embedding.
- `noprobe_dp_avg_eps2_K20` — DP prototype basin with **no** labelled public probe
  (the weakest-leak alignment from issue 017).

This case therefore feeds **the alignment-source comparison table** and **the
synthetic-basin paragraph** of the paper.

## MIA hook (issue 021)

Both modes produce a released student via `protocol.run_cell` that the MIA suite
reconstructs and attacks:

- Mode A's θ⋆ is trained directly on the synthetic data → **MIA-vulnerable** (the
  synthetic data is the whole contribution).
- Mode B's θ⋆ is the HE aggregate whose **bulk is HE-protected**, so only the
  decrypted released model θ⋆ is attackable; the basin leaks only the DP-MERF
  mean-embedding release, accounted by the averaging-variant DP mechanism.

## Sweep configuration

- Backbones: `mlp_mnist`, `vit_b32_cifar100`
  - (The issue prose says "mnist_mlp"; the registered `BackboneSpec` key is
    `mlp_mnist` — we use the registry key.)
- N values: `10`
- Dirichlet α: `0.05, 0.3, 1.0`
- Methods: `dp_synth_all_eps2, dp_synth_all_eps8, merf_basin_eps2_K20,
  merf_basin_eps8_K20, raw_union_K20, dp_avg_eps2_K20, noprobe_dp_avg_eps2_K20`
- Seeds: `42, 43, 44`
- K (bounded trajectory length, basin methods only): `300`
- Grid size: 2 × 7 × 3 × 1 × 3 = **126 cells**.

Wrapper: `jobs/heifd_022_synth_basin.sh` (CLAUDE.md Slurm template; `--array=0-7`
job-array chunking via `sweep.py --num-chunks/--chunk-index`; resumable — re-submit
skips cells whose JSON already records `status=success`; ≤3h per chunk).

## Results

(Auto-populated by `src/report.py` after the first cells land — placeholder until then.)
