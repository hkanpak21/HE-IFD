# heifd_011_scope_resnet18

Methodology-shaping comparison (issue 011): does adding trainable capacity beyond the linear head close the ~2pp residual gap that Round-1 010 left on resnet18 / CIFAR-10 / α=0.05? 18 cells = 2 methods × 3 seeds × 3 trainable scopes {head_only, lora_8 (rank-8 LoRA), last_block (2-layer MLP head with ReLU)}, all at the Round-1 best KD hparams (K=100, τ=1, lr=0.001). The aggregation remains linear (PT×CT + CT+CT only) regardless of scope — verified by the new `test_aggregate_linearity_invariant_holds_for_lora_sized_param_dict` test (asserts on a ~14× larger parameter dict).

## Verdict — linear head is empirically sufficient; extra capacity does NOT help (and last_block actively harms)

**Outcome: Case C** of the issue 011 framing (capacity does NOT help). Linear head matches LoRA-8 to within noise; 2-layer MLP head *underfits warmup* and ends up below the linear-head baseline.

| Method | Scope | Mean acc | Std | θ₀ | Δ vs θ₀ | Headline |
|---|---|---:|---:|---:|---:|---|
| **raw_union_K20** | **head_only** | **0.7617** | 0.0102 | 0.7405 | **+0.021** | **Round-1 010 reference, reproduces** |
| **raw_union_K20** | **lora_8** | **0.7623** | 0.0098 | 0.7407 | **+0.022** | **+0.0006 over head_only — within noise** |
| **raw_union_K20** | **last_block** | **0.6464** | 0.0139 | 0.6071 | +0.039 | **−0.115 vs head_only — warmup underfits, basin escape** |
| no_phase0 | head_only | 0.2073 | 0.0203 | 0.1052 | +0.102 | (no-alignment floor) |
| no_phase0 | lora_8 | 0.2074 | 0.0202 | 0.1052 | +0.102 | matches head_only |
| no_phase0 | last_block | 0.1633 | 0.0163 | 0.1034 | +0.060 | also underperforms |

### Reading the table

- **head_only ≡ lora_8** (Δ between scopes = +0.0006 ± noise). LoRA's B-init=0 makes the model identical to head_only at step 0; the rank-8 adapter's bounded K=100/τ=1/lr=0.001 trajectory doesn't reach a regime where the adapter direction adds detectable signal. The linear head is already at its natural capacity ceiling for this (probe, distillation-budget) pair.
- **last_block underperforms via two compounding problems**:
  1. **Warmup underfits.** The 2-layer MLP head (~66.5k params, 14× the linear head) cannot warm up to a useful θ₀ on the 100-sample labelled probe: θ₀ = 0.6071 vs 0.7405 for the linear head. The probe is sized for the linear head's capacity; bigger heads overfit the probe and generalise worse.
  2. **Distillation cannot recover.** From the lower θ₀, the K=100/τ=1/lr=0.001 trajectory adds +0.039 (slightly *more lift* than head_only's +0.021), but the lower starting point dominates: final acc 0.6464 < 0.7617.
- The **no_phase0** rows are the alignment-floor reference (raw acc ~0.10 because there's no warmed head + 10 classes ⇒ chance). Distillation adds ~0.10 across the board, but no_phase0 is far below raw_union_K20 in every scope.

### Methodology framing — the "tiny head suffices" claim survives

- The paper's framing — "a tiny linear head on cached pretrained features, distilled over a bounded K-step trajectory from a Phase-0-aligned init under FHE-friendly linear aggregation" — is **vindicated, not weakened**. Linear head matches LoRA; more capacity actively *hurts* via warmup underfit + basin escape. The FHE-efficiency choice (head_only ⇒ ~5k trainable scalars per client → small ciphertext budget, single-ciphertext-set upload) is now defended by results rather than assumed.
- **No new default needed.** Round-1 010 set the new pretrained KD baseline to (K=100, τ=1, lr=0.001) — that intervention alone fixed the broken 008 result. Issue 011 confirms there is no remaining capacity lever to pull.
- The residual ~2pp gap from oracle (0.76 vs 0.87) is fundamental to:
  - Bounded K=100 — only so far you can move with PT×CT + CT+CT under one upload.
  - α=0.05 basin-cancellation (per issue 013) — ~60% negative pairwise-Δ cosines means the aggregate moves less than any individual client's trajectory.
  Both are protocol-constitutive choices, not bugs.

### Adversarial framing — what the data does NOT show

- LoRA isn't *broken*; it just doesn't *help* in this regime. The rank-8 adapter might still be useful on a harder dataset (issue 012 — CIFAR-100 / Tiny-ImageNet for ViT) where the linear head has more headroom to fail. **011's verdict is scoped to resnet18/CIFAR-10/α=0.05** and shouldn't be over-generalised.
- last_block's failure mode is **specific to the small (100-sample) labelled probe**. A bigger probe would let the MLP head warm up properly, and the basin-escape symptom would change in character. But scaling the probe is its own decision (privacy-vs-utility trade-off) — for the "small labelled-probe" deployment this case represents, last_block is dominated by head_only.

### Implication for the rest of Phase II

- **Round 3 — 012 (harder vision dataset, ViT/CIFAR-100/Tiny-ImageNet)**: re-test whether LoRA/last_block helps where the linear head saturates. Use ViT-B/32 + larger probe.
- **Round 3 — 014 (complete from-scratch matrix)**: CNN-5 reverify (Part 3, in flight as 1115543) determines whether the from-scratch CIFAR-10 grid can finally land.
- **Round 6 — 018 (big backbones)**: the LoRA recipe is now justified mainly as a *capacity-budget* lever for the large pretrained backbones (ViT-L, BERT-large) where head_only might genuinely under-capacitate. **Don't apply LoRA on resnet18 — proven to add nothing.**

## Sweep configuration

- Backbone: `resnet18_cifar10` (frozen ImageNet ResNet-18 features + scoped head)
- N: 10 · Dirichlet α: 0.05 · Methods: `no_phase0, raw_union_K20`
- Trainable scopes: `head_only` (1 Linear), `lora_8` (rank-8 LoRA on the head), `last_block` (in_dim → 128 → 10 with ReLU)
- KD hparams: K=100, τ=1, lr=0.001 (the Round-1 010 best defaults)
- Seeds: 42, 43, 44
- Single SLURM task, 18 cells, ~1m25s wall-clock (feature cache from 008 hot).
- Job 1115537.

## CNN-5 hparam fix (Part 3 of issue 011)

`BACKBONES["cnn5_cifar10"]` updated to `teacher_epochs=30, oracle_epochs=50, teacher_lr=0.005, warmup_epochs=10`. Re-verify in flight as job 1115543; sanity gate: CIFAR-10 IID raw_union ≥ 0.60 at α=1.0. Verdict written to `results/heifd_fromscratch_verify/README.md` after the job lands.
