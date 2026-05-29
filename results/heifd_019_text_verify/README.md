# heifd_019_text_verify

## VERDICT (verify) — strong backbones CONFIRMED (oracle 0.90), but α=0.05 warmup collapses → feature-normalization fix needed

| backbone | α | acc | θ₀ | mean_t | oracle | m4 |
|---|---|---:|---:|---:|---:|---:|
| mpnet_st_agnews | 0.05 | 0.3888 | 0.3455 | 0.285 | **0.8976** | 0.327 |
| mpnet_st_agnews | 1.0 | 0.8391 | 0.8387 | 0.670 | 0.8976 | — |
| roberta_base_agnews | 0.05 | **0.2500** | **0.2500** | 0.274 | **0.9021** | 0.175 |
| roberta_base_agnews | 1.0 | 0.7830 | 0.5813 | 0.652 | 0.9021 | — |
| distilbert (M1 bar) | 0.05 | 0.437 | 0.410 | — | 0.904 | 0.363 |

- **Backbone choice validated:** oracles 0.898 / 0.902 (≈ DistilBERT 0.904) — roberta/mpnet ARE strong frozen extractors. At α=1.0 the protocol works (mpnet 0.839 near-oracle; roberta +0.20 distillation lift).
- **But α=0.05 underperforms DistilBERT:** roberta θ₀ = exactly 0.25 (random) — the warmup head learned NOTHING; mpnet θ₀ 0.35. A strong-oracle backbone whose *warmup* θ₀ is random ⇒ **feature-scale problem**: raw RoBERTa / mpnet mean-pooled features need standardization (z-score or L2-norm) for the small-LR warmup head to converge at extreme heterogeneity. DistilBERT happens to be adequately scaled; mpnet embeddings are normally used L2-normalized.

**Next:** debug-agent adds per-backbone feature standardization (gated, so ViT/ResNet/DistilBERT stay byte-identical), then re-verify. Hypothesis: with normalization, roberta/mpnet α=0.05 should clear the DistilBERT bar (acc ≥ 0.44, ideally toward the ViT/CIFAR-100 level).

---

HE-IFD plaintext simulation of the one-shot federated distillation protocol: each client distils its own teacher into a student over a bounded K-step trajectory from a shared, Phase-0-aligned init θ₀, then uploads the cumulative trainable-parameter displacement Δ_i = θ_i^(K) − θ₀; the server's only operation is the sample-weighted linear combine θ₀ + Σ_i w_i·Δ_i (w_i = n_i/Σ_j n_j), which uses plaintext-scalar × ciphertext and ciphertext + ciphertext only and is thus FHE-compatible by construction (multiplicative depth ≈ 1). This case sweeps the grid below; IID test accuracy is the lead metric, with mean/best teacher and a centralised oracle as references, plus the standalone accuracy of the aligned init θ₀ (what alignment adds before distillation), the M3 per-client teacher-vs-aggregate gap on each client's own data (the participation-incentive metric), and the M4 per-client accuracy on classes a client held zero local examples of (the OOD value-proposition; n/a at α=1.0).

## Sweep configuration

- Backbones: `roberta_base_agnews,mpnet_st_agnews`
- N values: `10`
- Dirichlet α: `0.05,1.0`
- Methods: `no_phase0,raw_union_K20`
- Seeds: `42`
- K (bounded trajectory length): `100`
- τ (distill temperature): `1.0`
- Student LR: `0.001`
- Labelled-probe size P: `None` (None = backbone default)

## Results

| backbone | N | α | method | seed | acc | mean_teacher | best_teacher | oracle | θ₀_acc | M3_mean_gap | M3_helped | M4_ood_acc | σ | status |
|---|---|---|--------|------|-----|--------------|--------------|--------|--------|-------------|-----------|------------|---|--------|
| mpnet_st_agnews | 10 | 0.05 | no_phase0 | 42 | 0.3351 | 0.2847 | 0.4750 | 0.8976 | 0.2725 | -0.5501 | 0/9 | 0.3541 | 0.0000 | success |
| mpnet_st_agnews | 10 | 0.05 | raw_union_K20 | 42 | 0.3888 | 0.2847 | 0.4750 | 0.8976 | 0.3455 | -0.4292 | 1/9 | 0.3270 | 0.0000 | success |
| mpnet_st_agnews | 10 | 1.0 | no_phase0 | 42 | 0.3238 | 0.6702 | 0.8504 | 0.8976 | 0.2725 | -0.5508 | 0/10 | n/a | 0.0000 | success |
| mpnet_st_agnews | 10 | 1.0 | raw_union_K20 | 42 | 0.8391 | 0.6702 | 0.8504 | 0.8976 | 0.8387 | -0.0337 | 1/10 | n/a | 0.0000 | success |
| roberta_base_agnews | 10 | 0.05 | no_phase0 | 42 | 0.2492 | 0.2735 | 0.4746 | 0.9021 | 0.2500 | -0.5781 | 0/9 | 0.1750 | 0.0000 | success |
| roberta_base_agnews | 10 | 0.05 | raw_union_K20 | 42 | 0.2500 | 0.2735 | 0.4746 | 0.9021 | 0.2500 | -0.5750 | 0/9 | 0.1750 | 0.0000 | success |
| roberta_base_agnews | 10 | 1.0 | no_phase0 | 42 | 0.2624 | 0.6516 | 0.8339 | 0.9021 | 0.2500 | -0.5323 | 0/10 | n/a | 0.0000 | success |
| roberta_base_agnews | 10 | 1.0 | raw_union_K20 | 42 | 0.7830 | 0.6516 | 0.8339 | 0.9021 | 0.5813 | -0.0516 | 1/10 | n/a | 0.0000 | success |

Raw per-cell JSONs live here as `cell_<backbone>_N<n>_a<α>_<method>_s<seed>_K<k>_<hash>.json`.
Per-client per-class counts at `partition_diagnostic.jsonl`. Slurm stdout/stderr at `runs/`. Long-form rows at `results.csv`.
