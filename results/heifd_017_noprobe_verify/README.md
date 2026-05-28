# heifd_017_noprobe_verify

> **PLACEHOLDER** — populated by `src.report` when the verify run completes.

Issue 017 — no-probe DP-common-basin **VERIFY** smoke run. Confirms the
no-probe path (no labelled public probe; the (raw-union or DP-noisy)
per-(client, class) prototypes themselves warm θ₀, with the conv/flat
flatten-reshape bridge reused from the dp_avg path) runs **end-to-end** on
MNIST/MLP before the full grid (`heifd_017_noprobe_mlp`) is launched. A local
`ast.parse` cannot catch the runtime prototype-set warmup or the shape bridge;
this 10-cell grid does.

## Pass condition

All 10 cells `status=success`; the no-probe θ₀ is weak (low `theta0_acc`) yet
`acc` (post-distillation) lifts above it — confirming the distillation carries
the learning in the low-leak regime. The 2 with-probe baselines anchor the
cost-of-no-probe comparison.

## Sweep configuration

- Backbones: `mlp_mnist`
- N values: `10`
- Dirichlet α: `0.05,1.0`
- Methods: `noprobe_dp_avg_eps2_K20,noprobe_dp_avg_eps8_K20,noprobe_raw_union_K20,dp_avg_eps2_K20,raw_union_K20`
- Seeds: `42`
- K (bounded trajectory length): `300`
- Grid size: 1 × 2 × 5 × 1 = **10 cells** (single job, no chunking).
