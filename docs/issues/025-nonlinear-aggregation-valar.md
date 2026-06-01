# 025 — Non-linear one-shot aggregation, full VALAR investigation  [AFK]

> **STATUS: ✅ VERDICT REACHED → reframed (task arithmetic + λ, [026](026-task-arithmetic-lambda-verify.md))** (2026-05-30) — combines built + threaded; a 6-cell VALAR verify + the 408-row local probe (023/024) agree: **no one-shot non-linear combine beats the depth-1 weighted average**; `second_moment`/RMSProp **loses** on paired (within-partition) comparison; only multi-round `sync_sgd` wins, which breaks the one-shot constraint. The full 960-cell grid is **not needed** — superseded by the task-arithmetic reframe + the λ-coefficient verify (026). Our combine **is task arithmetic** (Ilharco 2023); the deep conflict-resolution merges (TIES, FedFisher) are unnecessary *because the shared basin pre-aligns the deltas*, and cost prohibitive HE depth.

**Why.** The local MNIST-MLP probe (023/024) found no non-linear one-shot combine beats the linear weighted average, but it used plain supervised SGD on a toy net. We want the **authoritative** test on the real `src/` pipeline — frozen pretrained backbones, the actual bounded-K **distillation** trajectory, with and without the Phase-0 basin — across the headline backbones. Question: does any non-linear, one-shot server combine of the encrypted displacements {Δᵢ} beat the depth-1 weighted average θ₀+Σwᵢ·Δᵢ on the real models, especially in the near-convex frozen-head regime? Annotate each combine's HE multiplicative depth.

## What to build

1. **`src/aggregate.py` — add `aggregate_nonlinear(theta0, deltas, weights, method, **kw)`** implementing these one-shot combines over the per-client cumulative displacements (operate per-parameter / flattened; keep the existing linear `aggregate` as the default, untouched):
   - `weight_avg` (depth-1, baseline — dispatches to existing `aggregate`)
   - `mag_weighted` (depth-1 linear: reweight clients by public scalar ‖Δᵢ‖)
   - `sign_majority` (coordinate weighted-majority sign × weighted mean |Δ|) — deep
   - `agreement_gated` (gⱼ=(ΣwᵢΔᵢⱼ)²/(ε+Σwᵢ·Δᵢⱼ²)∈[0,1]; θ₀+g⊙mean) — deep (÷)
   - `norm_normalized` (unit-normalize each Δᵢ, scale by weighted mean norm) — deep
   - `second_moment` (RMSProp: θ₀+(ΣwᵢΔᵢ)/√(ε+Σwᵢ·Δᵢ²), rescaled to the linear step norm) — deep
   - `coord_median` / `coord_trimmed_mean` (per-coordinate robust) — deep
   - `consensus_proj` (project each Δᵢ onto the weighted-mean direction, recombine) — deep
   - `poly_gate_d2_a`, `poly_gate_d2_b` (division-free degree-2 polynomial gates — the only CKKS-cheap non-linear candidates) — depth-2
   Each function returns the combined parameter dict; add a module-level `NONLINEAR_DEPTH = {method: "depth-1"|"depth-2"|"deep"}` map for the report.
2. **Thread a selector** through `src/protocol.py` (`run_cell`: a new `agg_method` arg, default `weight_avg` → existing linear path; otherwise call `aggregate_nonlinear`) and `src/sweep.py` (`--agg-methods` CSV, looped as a new axis; record `agg_method` + its depth in each cell + the CSV/report). Existing behaviour byte-identical when `agg_method=weight_avg`.
3. **`jobs/heifd_025_nonlinear_agg.sh`** (CLAUDE.md template, ≤3h, resumable job-array): backbones `mlp_mnist,lenet_fmnist,vit_b32_cifar100,roberta_base_agnews`; α `0.05,0.1,0.3,1.0`; basin axis via methods `raw_union_K20` (with basin) and `no_phase0` (no basin); `--agg-methods weight_avg,mag_weighted,sign_majority,agreement_gated,norm_normalized,second_moment,coord_median,consensus_proj,poly_gate_d2_a,poly_gate_d2_b`; N=10; seeds 42,43,44; K per backbone default. case `heifd_025_nonlinear_agg`. Login-node prefetch already done for these backbones. Placeholder README documenting the question + the depth annotation.

## Acceptance
- [ ] `aggregate_nonlinear` + all combines implemented; `NONLINEAR_DEPTH` map; linear path untouched/byte-identical at `weight_avg`.
- [ ] `--agg-methods` threaded through sweep→protocol→aggregate; per-cell JSON records `agg_method` + depth + acc + the usual metrics.
- [ ] `jobs/heifd_025_nonlinear_agg.sh` chunked/resumable; README placeholder.
- [ ] ast.parse clean on touched `src/` files; `bash -n` on the wrapper.

## Hard boundaries
- Touch `src/aggregate.py`, `src/protocol.py` (run_cell selector), `src/sweep.py` (--agg-methods axis), new `jobs/heifd_025_*.sh`, case README. Do NOT change distill.py semantics or the existing linear `aggregate`. No git push/commit/sbatch/ssh. Mac has no torch — ast.parse only.

## Report
1. Combines implemented + the depth map.
2. How `--agg-methods` threads through; confirmation the linear default is byte-identical.
3. The wrapper grid + chunking.
