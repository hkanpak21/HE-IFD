# heifd_015_dp_frontier_mlp

DP-ε frontier sweep of the averaging-variant DP Phase-0 alignment on the
from-scratch MLP / MNIST backbone (issue 015). HE-IFD one-shot federated
distillation: each client distils its teacher into a student over a bounded
K-step trajectory from a shared, Phase-0-aligned init θ₀, uploads the cumulative
displacement Δ_i = θ_i^(K) − θ₀, and the server linearly combines θ₀ + Σ_i w_i·Δ_i
(FHE-compatible PT×CT + CT+CT). Here Phase-0 is always the averaging-variant DP
probe (`dp_avg`), swept across the privacy frontier to test whether accuracy
flattens from ε ≈ 2 onward as the methodology claims.

## Frontier question

Does the averaging-variant DP frontier **flatten from ε ≈ 2 onward**? The probe
releases per-(client, class) means under the Gaussian mechanism with
σ = (clip / Kpc) · √(2 ln(1.25/δ)) / ε, so:

- **ε sweep at fixed Kpc=20** — `dp_avg_eps{0.5, 2, 8, 32, ∞}_K20`. As ε grows,
  σ shrinks toward 0; `epsinf` sets σ=0 exactly (the raw_union-equivalent
  no-noise sanity reference). The claim is that acc is already near the
  no-noise ceiling by ε ≈ 2, i.e. the curve from ε=2 → ∞ is roughly flat and
  only ε=0.5 pays a visible accuracy tax.
- **Kpc sweep at fixed ε ∈ {2, 8}** — `dp_avg_eps{2,8}_K{1,5,20}`. Larger Kpc
  averages more samples per release, lowering sensitivity (clip/Kpc) and hence
  σ at fixed ε — so larger Kpc should recover accuracy at a given ε.

## Sweep configuration

- Backbone: `mlp_mnist` (from-scratch MLP on raw 28×28 MNIST)
- N values: `10`
- Dirichlet α: `0.05, 0.3, 1.0`
- Methods (the DP frontier panel):
  - ε sweep @ Kpc=20: `dp_avg_eps0.5_K20`, `dp_avg_eps2_K20`,
    `dp_avg_eps8_K20`, `dp_avg_eps32_K20`, `dp_avg_epsinf_K20`
  - Kpc sweep @ ε=2: `dp_avg_eps2_K1`, `dp_avg_eps2_K5` (+ `dp_avg_eps2_K20`)
  - Kpc sweep @ ε=8: `dp_avg_eps8_K1`, `dp_avg_eps8_K5` (+ `dp_avg_eps8_K20`)
- Seeds: `42, 43, 44`
- Cells: 9 methods × 1 N × 3 α × 3 seeds = **81**.

## Verdict

_To be filled once the sweep lands_: does the averaging-variant DP frontier
flatten from ε ≈ 2 onward? (Y/N + the per-(α) acc-vs-ε and acc-vs-Kpc numbers,
seed-mean ± std.) The auto-writer populates the results table below.

## Results

_Auto-populated by `src.report` after the sweep runs._
