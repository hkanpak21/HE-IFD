# heifd_017_noprobe_mlp

> **PLACEHOLDER** — populated by `src.report` when the sweep runs. This file
> documents the question the case answers; the results table is appended below
> on the first `sbatch jobs/heifd_017_noprobe_mlp.sh`.

Issue 017 — **no-probe DP-common-basin** alignment (CENTRAL Phase-II
experiment). This is the **weak-alignment / low-leak** regime: the labelled
public probe is **removed entirely**. θ₀ is warmed **only** on the (DP-noisy or
raw-union) per-(client, class) prototypes — each prototype is one feature-space
sample with its class as label (~`num_classes × N_contributors` points) — so θ₀
is deliberately **weak**. The thesis to demonstrate: the HE-secure bounded
K-step distillation lifts the aggregated global model **well above this weak θ₀**
(large `acc − θ₀`) and **above the average client teacher** (`acc ≥
mean_teacher`), with `m4_ood > 0` — i.e. the distillation carries the learning
while the alignment leaks minimally.

## The cost-of-no-probe question

The grid runs the 3 no-probe methods **alongside** their 2 with-probe twins so
the **cost of removing the probe** is a direct, per-(α, ε) accuracy delta:

| no-probe variant         | with-probe twin   | Δacc reported |
|--------------------------|-------------------|---------------|
| `noprobe_dp_avg_eps2_K20`  | `dp_avg_eps2_K20`   | acc(with) − acc(noprobe) |
| `noprobe_dp_avg_eps8_K20`  | (`dp_avg_eps8` if present in M1) / vs `noprobe_dp_avg_eps2` | ε ablation |
| `noprobe_raw_union_K20`    | `raw_union_K20`     | acc(with) − acc(noprobe) |

The headline metrics for the verdict are: (a) `acc` vs `mean_teacher` /
`best_teacher` (client benefit), (b) `m4_ood` (OOD-class value), and **(c)
`acc − θ₀_acc`** — the distillation lift over the minimal alignment, the MOST
meaningful metric here because no-probe makes θ₀ weak, so the distillation has
room to prove its value.

**Verdict (two-paragraph note) — to fill after the run:** is the no-probe
variant viable, i.e. not dramatically worse than its with-probe twin? At which
α / ε does the cost become prohibitive? Does the distillation lift (`acc − θ₀`)
stay large as θ₀ weakens, and does `acc ≥ mean_teacher` hold across the grid?

## Sweep configuration

- Backbones: `mlp_mnist`
- N values: `1,5,10,20,50` (N=1 = degenerate single-client sanity floor)
- Dirichlet α: `0.01,0.05,0.1,0.3,1.0`
- Methods: `noprobe_dp_avg_eps2_K20,noprobe_dp_avg_eps8_K20,noprobe_raw_union_K20,dp_avg_eps2_K20,raw_union_K20`
- Seeds: `42,43,44`
- K (bounded trajectory length): `300`
- Grid size: 5 × 5 × 5 × 3 = **375 cells**, chunked over an 8-task SLURM array
  (resumable; re-submit to resume).

Run `jobs/heifd_017_noprobe_verify.sh` (10-cell smoke) first and confirm all
cells `status=success` before launching this grid.
