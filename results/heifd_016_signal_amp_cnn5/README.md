# heifd_016_signal_amp_cnn5

Signal-amplification diagnostic on the failing CNN-5/CIFAR-10 regime: results/heifd_fromscratch_verify shows the protocol misses BOTH participation-incentive gates here (IID raw_union α=1.0 = 0.5071 vs gate 0.60; m4_ood α=0.05 = 0.1702 vs gate 0.40), with 6/16 teachers stuck at random at α=0.05 and bounded-K distillation actively degrading the warmed init (θ₀=0.2374 → final=0.2058). This case amplifies the Phase-0 channel across four arms (raw_union_K20 baseline, raw_union_K100 byte-budget bump, synthetic_K100 Gaussian-around-mean MVP, synthetic_logit_K100 novel teacher-logit-prototype mechanism) holding distillation constant (K=300, τ=4.0, student_lr=0.01), to answer the headline question: does any Phase-0 lever lift θ₀ AND m4_ood substantially over the baseline?

## Method-arm dictionary

| Arm | Phase 0 payload | Mechanism modality | Bytes/client/class | DP-extensible? |
|---|---|---|---|---|
| `raw_union_K20` | 20 raw clipped samples per class per client | feature space | 20·D | yes (existing `dp_avg`) |
| `raw_union_K100` | 100 raw clipped samples per class per client | feature space | 100·D | yes |
| `synthetic_K100` | 100 N(μ_ic, diag(σ²_ic)) synthetic samples per (i, c) | feature space (variance-aware) | 100·D | yes (issue 016+: `synthetic_dp_eps<ε>_K<K>` parsed, implements DP-on-μ) |
| `synthetic_logit_K100` | 100 synthetic samples PLUS C-dim per-class teacher-softmax consensus | feature space ⊕ output space | 100·D + C·C | feature: yes; logit: future work |

D = 3·32·32 = 3072 (raw-pixel space, CNN-5 from-scratch); C = 10. Soft-label payload C·C = 100 scalars total — negligible vs the feature payload.

## Sweep configuration

- Backbone: `cnn5_cifar10` (from-scratch CNN-5 on raw 3×32×32 CIFAR-10 images)
- N: 16 · Dirichlet α: 0.05, 1.0
- Methods: `raw_union_K20, raw_union_K100, synthetic_K100, synthetic_logit_K100`
- Seeds: 42 (single seed — this is a diagnostic, not a sweep)
- K (bounded trajectory length): 300 (legacy from-scratch default — issue 010's K=100 finding is pretrained-regime only)
- τ (distill temperature): 4.0 (legacy default — Phase-0 lever isolation; τ is orthogonal to this comparison)
- Student LR: 0.01 (legacy default)
- 8 cells × ~5 min each ≈ 30-50 min wall-clock; one task, no array.

## Results

(populated by `src.report.write_report` after the job completes)

## Pre-run hypothesis

Each arm "wins" if it lifts both θ₀ AND m4_ood substantially over the `raw_union_K20` baseline (θ₀=0.2374, m4_ood=0.1702 at α=0.05; θ₀=0.4850, m4_ood n/a at α=1.0). Concretely:

- **`raw_union_K100` wins iff** θ₀ ≥ 0.30 AND m4_ood ≥ 0.25 at α=0.05 — would mean the byte budget itself was the bottleneck (mean-feature mechanism scales).
- **`synthetic_K100` wins iff** θ₀ ≥ 0.35 AND m4_ood ≥ 0.30 at α=0.05 — would mean class-variance structure carries useful information that mean-only prototypes lack.
- **`synthetic_logit_K100` wins iff** θ₀ ≥ 0.40 AND m4_ood ≥ 0.30 at α=0.05 — would mean inter-class confusion structure (output-space prototype) carries signal modality orthogonal to feature-space.

If all four arms stay within ±5pp of each other at α=0.05, Phase-0-only amplification is insufficient and the failure is teacher-side (6 random teachers are dragging the federation down regardless of payload richness); next step would be teacher-quality interventions (teacher_epochs ↑, stronger augmentation, or filtering random-acc teachers from the aggregate).

Raw per-cell JSONs live here as `cell_<backbone>_N<n>_a<α>_<method>_s<seed>_K<k>_<hash>.json`. Per-client per-class counts at `partition_diagnostic.jsonl`. Slurm stdout/stderr at `runs/`. Long-form rows at `results.csv`.
