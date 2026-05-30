# heifd_025_nonlinear_agg

**Status:** placeholder — populated by `src/report.py` once `jobs/heifd_025_nonlinear_agg.sh` lands its first cells.

Non-linear ONE-SHOT server-combine investigation, run in the real `src/` pipeline
on the headline backbones (the issue-024 local MNIST-MLP probe, now generalised).
The HE-IFD server aggregate is the linear, sample-weighted θ⋆ = θ₀ + Σᵢ wᵢ·Δᵢ
(multiplicative depth ≈ 1 — the paper's selling point), which telescopes to a
weighted average of the clients' final models and leaves a heterogeneity gap at
small α. Staying STRICTLY one-shot (the SAME bounded-K-step uploads {Δᵢ}, no extra
client↔server rounds), this case asks whether ANY non-linear server function of
{Δᵢ} beats that flat average under heterogeneity, and whether any winner is
CKKS-cheap. Every combine is applied to the identical {Δᵢ}; distillation is
unchanged across combines, so `weight_avg` is a byte-identical baseline.

## Server combines (the `--agg-methods` axis) and HE depth

`m = Σᵢ wᵢ·Δᵢ`, `s² = Σᵢ wᵢ·Δᵢ²` (per-coordinate, over the flattened parameter
vector). HE depth is annotated (`aggregate.NONLINEAR_DEPTH`), not implemented.

| combine | what it does | HE depth |
|---|---|---|
| `weight_avg` | θ₀ + m — the current HE-IFD aggregate (routes to the linear `aggregate`; baseline). | **depth-1** |
| `mag_weighted` | reweight by public scalar ‖Δᵢ‖ — still linear (a reweighted average). | **depth-1** |
| `poly_gate_d2_a` | θ₀ + m − clamp(c·ŝ², 0, 1)⊙m — division-free degree-2 gate, **bounded** shrink. | **depth-2** |
| `poly_gate_d2_b` | θ₀ + m − clamp(c·v̂, 0, 1)⊙m, v̂ = (s²−m²)/s² — cancellation-aware, **bounded**. | **depth-2** |
| `sign_majority` | θ₀ + scale·sign(Σwᵢ·sign(Δᵢⱼ))·mean\|Δⱼ\| (signSGD-style). | deep |
| `agreement_gated` | θ₀ + g⊙m, gⱼ = mⱼ²/(ε+s²ⱼ) ∈ [0,1] (bounded ratio gate). | deep |
| `norm_normalized` | θ₀ + (mean‖Δ‖)·Σwᵢ(Δᵢ/‖Δᵢ‖) (unit-vector average). | deep |
| `second_moment` | θ₀ + scale·m/√(ε+s²) (RMSProp-style per-coord precond). | deep |
| `coord_median` | per-coordinate median across clients (robust location), rescaled to m's L1. | deep |
| `consensus_proj` | project each Δᵢ on the mean direction, average projections + a residual of m. | deep |

The two `poly_gate_d2_*` are the only candidates that are both non-linear AND
CKKS-cheap. They keep the 024 probe's division-free degree-2 polynomial form but
**clamp the per-coordinate shrink fraction into [0,1]** before applying it — the
issue-025 safety fix for the 024 finding that the *unbounded* gate detonates
heavy-tailed coordinates (ŝ²/v̂ max ≈ 500× the mean). With the clamp the gate can
at most zero a coordinate's mean, never flip or amplify it. (The clamp is a
min/max, so a faithful CKKS realisation would approximate it with a low-degree
polynomial; the plaintext study here measures whether the bounded-gate IDEA
helps.)

## Grid

- Backbones: `mlp_mnist`, `lenet_fmnist`, `vit_b32_cifar100`, `roberta_base_agnews`
  (from-scratch MNIST/FMNIST + pretrained-head CIFAR-100 + text AG-News).
- α ∈ {0.05, 0.1, 0.3, 1.0} (heterogeneity from extreme skew to IID).
- Protocol method ∈ {`raw_union_K20` (shared basin θ₀, coherence ON),
  `no_phase0` (no basin — maximally incoherent {Δᵢ}, the hardest case)}.
- `--agg-methods` = the 10 combines above.
- N = 10, seeds {42, 43, 44}, K = 20.
- 4 × 4 × 2 × 10 × 1 × 3 = **960 cells**.

## How to read it

For each (backbone, α, method, seed) the table reports IID test acc per
`agg_method`; compare each combine's `acc` against the `weight_avg` row at the
same cell. The hypothesis under test (from the 024 probe, expected to replicate):
**no non-linear one-shot combine reliably beats the flat weighted average under
heterogeneity, and the only CKKS-cheap candidates have no headroom** — i.e. the
depth-1 `weight_avg` is on the Pareto front of {one-shot, CKKS-cheap} combines, a
reviewer-facing justification for keeping the server op at depth ≈ 1.

Submit with `sbatch jobs/heifd_025_nonlinear_agg.sh` (resumable job array). Raw
per-cell JSONs land here as
`cell_<backbone>_N<n>_a<α>_<method>_s<seed>_K<k>[_agg<combine>]_<hash>.json`
(the `_agg<combine>` segment is omitted for the `weight_avg` baseline so it reuses
the legacy filename/hash). Long-form rows at `results.csv` (with `agg_method` /
`agg_depth` columns); Slurm logs at `runs/`.
