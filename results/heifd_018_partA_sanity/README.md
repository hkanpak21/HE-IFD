# heifd_018_partA_sanity

## VERDICT (HITL GATE) — Part A done; ViT-L PASS, BERT-large marginal, GPT-2-medium fail (informational). Part B awaits user authorization.

Standalone centralised linear-probe (frozen big-backbone features → linear head on full train set, held-out test acc = `oracle`). This gates whether each backbone is worth running the protocol (Part B) on.

| backbone | oracle (linear-probe) | gate | verdict |
|---|---:|---:|---|
| ViT-L/16 / CIFAR-100 | **0.8762** | ≥0.78 | **PASS** |
| BERT-large / AG-News | **0.9099** | ≥0.92 | marginal FAIL (−0.9pp) |
| GPT-2-medium / AG-News | **0.4029** | ≥0.50 | FAIL (informational, non-blocking) |

Reads:
- **ViT-L/CIFAR-100 PASS** — linear-probes to 0.876, comfortably above 0.78. A valid Part-B backbone (would extend the ViT-B/32/CIFAR-100 client-benefit win to a larger backbone).
- **BERT-large marginal FAIL** — 0.910 vs 0.92 is a *threshold-calibration* miss, not a broken backbone: a frozen-feature linear probe sitting ~3-4pp below fully-fine-tuned BERT-large (~0.945) on AG-News is expected and healthy. Recommendation: accept for Part B (or tune max_len 128→256 / last-token pooling to clear 0.92 if a clean pass is wanted). **User's call.**
- **GPT-2-medium FAIL (informational)** — 0.403 < 0.50. Consistent with the deferred GPT-2-family weakness (issue 002); per the issue spec this is non-blocking and does not gate Part B. GPT-2-medium would be dropped from any Part-B run.

**Part B (protocol + LoRA on big backbones) is HITL-gated and NOT submitted.** Awaiting user authorization after this review.


HE-IFD plaintext simulation of the one-shot federated distillation protocol: each client distils its own teacher into a student over a bounded K-step trajectory from a shared, Phase-0-aligned init θ₀, then uploads the cumulative trainable-parameter displacement Δ_i = θ_i^(K) − θ₀; the server's only operation is the sample-weighted linear combine θ₀ + Σ_i w_i·Δ_i (w_i = n_i/Σ_j n_j), which uses plaintext-scalar × ciphertext and ciphertext + ciphertext only and is thus FHE-compatible by construction (multiplicative depth ≈ 1). This case sweeps the grid below; IID test accuracy is the lead metric, with mean/best teacher and a centralised oracle as references, plus the standalone accuracy of the aligned init θ₀ (what alignment adds before distillation), the M3 per-client teacher-vs-aggregate gap on each client's own data (the participation-incentive metric), and the M4 per-client accuracy on classes a client held zero local examples of (the OOD value-proposition; n/a at α=1.0).

## Sweep configuration

- Backbones: `gpt2_medium_agnews`
- N values: `1`
- Dirichlet α: `1.0`
- Methods: `no_phase0`
- Seeds: `42`
- K (bounded trajectory length): `1`
- τ (distill temperature): `1.0`
- Student LR: `0.001`
- Labelled-probe size P: `None` (None = backbone default)

## Results

| backbone | N | α | method | seed | acc | mean_teacher | best_teacher | oracle | θ₀_acc | M3_mean_gap | M3_helped | M4_ood_acc | σ | status |
|---|---|---|--------|------|-----|--------------|--------------|--------|--------|-------------|-----------|------------|---|--------|
| bert_large_agnews | 1 | 1.0 | no_phase0 | 42 | 0.3155 | 0.9087 | 0.9087 | 0.9099 | 0.3121 | -0.5896 | 0/1 | n/a | 0.0000 | success |
| gpt2_medium_agnews | 1 | 1.0 | no_phase0 | 42 | 0.2504 | 0.2675 | 0.2675 | 0.4029 | 0.2500 | -0.0194 | 0/1 | n/a | 0.0000 | success |
| vit_l_cifar100 | 1 | 1.0 | no_phase0 | 42 | 0.0125 | 0.8782 | 0.8782 | 0.8762 | 0.0112 | -0.9331 | 0/1 | n/a | 0.0000 | success |

Raw per-cell JSONs live here as `cell_<backbone>_N<n>_a<α>_<method>_s<seed>_K<k>_<hash>.json`.
Per-client per-class counts at `partition_diagnostic.jsonl`. Slurm stdout/stderr at `runs/`. Long-form rows at `results.csv`.
