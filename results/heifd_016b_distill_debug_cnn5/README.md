# heifd_016b_distill_debug_cnn5

De-confounds issue 016's "distillation degrades θ₀ on CNN-5" finding. Issue 016
distilled every CNN-5 cell at τ=4 / K=300 / lr=0.01 — the legacy from-scratch
defaults, which issue 010 proved are the KNOWN-BAD KD settings (on resnet18, τ=4
degrades acc to 0.48 while τ=1 recovers it to 0.76; that τ fix was never applied
to CNN-5). This case holds the leak-minimised Phase-0 alignment FIXED at
`raw_union_K20` and sweeps only the distillation knobs (K, τ, student LR) to ask
whether the bounded-K-step KL distillation ADDS VALUE over θ₀ once the KD
hyperparameters are correct (τ=1).

## The question

**Does the HE-secure distillation beat θ₀ on CNN-5 at τ=1, alignment held
minimal?** Win condition, per (K, τ, lr) cell: `acc > theta0_acc` — the
distilled+aggregated student beats the aligned init it started from, i.e.
distillation adds value. The headline contrast is τ=1 vs τ=4 cells:

- If τ=1 makes distillation beat θ₀ → mechanism is sound, τ=4 was the bug
  (the issue-010 finding transfers to from-scratch conv nets).
- If τ=1 STILL degrades θ₀ → full-from-scratch-deep-net distillation is outside
  the basin-coherence envelope (consistent with issue 011's last_block
  basin-escape finding) — a clean scoping statement for the paper.

## Sweep configuration

- Backbone: `cnn5_cifar10` (from-scratch CNN-5 on raw 3×32×32 CIFAR-10)
- N: `16`; seed: `42` (single seed — diagnostic)
- Dirichlet α: `0.05, 1.0`
- Method (FIXED, minimal-leak alignment): `raw_union_K20`
- K (bounded trajectory length): `30, 100, 300`
- τ (distill temperature): `1, 4`
- Student LR: `0.001, 0.01`
- Grid: 2 α × 3 K × 2 τ × 2 lr = **24 cells**

## Results

<!-- auto-populated by src/report.py on the VALAR side after the run -->

Raw per-cell JSONs live here as
`cell_<backbone>_N<n>_a<α>_<method>_s<seed>_K<k>_<hash>.json`.
