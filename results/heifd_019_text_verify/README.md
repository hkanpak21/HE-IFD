# heifd_019_text_verify

## ✅ RESOLVED (re-verify with zscore) — strong text backbones now MATCH the ViT/CIFAR-100 vision story

Feature z-score standardization fixed the α=0.05 warmup collapse. Both new frozen backbones now far exceed DistilBERT and reach the vision-story level.

**α=0.05 raw_union_K20 — before → after zscore:**

| backbone | acc | θ₀ | mean_t | oracle | m4_ood | acc/mean_t | (prior, no-norm) |
|---|---:|---:|---:|---:|---:|---:|---|
| roberta_base_agnews | **0.8555** | 0.8442 | 0.4542 | 0.9142 | **0.8541** | 1.9× | was 0.250/0.250/0.175 (random) |
| mpnet_st_agnews | **0.8497** | 0.8397 | 0.4379 | 0.9062 | **0.8469** | 1.9× | was 0.389/0.346/0.327 |
| distilbert (M1 bar) | 0.437 | 0.410 | — | 0.904 | 0.363 | 1.5× | — |

**α=1.0 raw_union_K20:** roberta 0.874 / mpnet 0.868 (≈ oracle 0.91). no_phase0 at α=0.05: roberta 0.704, mpnet 0.682 — so raw_union (0.856) >> no_phase0 (0.704): alignment contributes +0.15 even with the strong backbone.

### Reads
- **The fix:** raw RoBERTa/mpnet mean-pooled features had a scale the small-LR warmup head couldn't fit at α=0.05 (θ₀ = random). Per-feature z-score (train-stats only) reconditions them → θ₀ jumps to 0.84 and the protocol works. Backbone choice was right all along (oracle 0.91); the bug was feature scaling.
- **Client-benefit (thesis):** global model 1.9× the average client teacher, **m4_ood 0.85** (clients get 85% on classes they never saw locally). This now matches ViT/CIFAR-100 (acc 0.81, m4 0.81) — **the text deployment story is no longer the weak link.**
- **Distillation lift** is thin here (+0.01) because the labelled-probe warmup already builds a strong θ₀ (the "strong-probe → thin-lift, huge client-benefit" regime, like ViT/CIFAR-100). The no-probe / weak-θ₀ regime (issue 017) is where the lift is large.

→ Full headline grid (N×α×methods×seeds) + DBpedia-14 (14-class, richer m4) submitted to map this out.

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
| mpnet_st_agnews | 10 | 0.05 | no_phase0 | 42 | 0.6820 | 0.4379 | 0.5530 | 0.9062 | 0.2838 | -0.2552 | 0/9 | 0.6827 | 0.0000 | success |
| mpnet_st_agnews | 10 | 0.05 | raw_union_K20 | 42 | 0.8497 | 0.4379 | 0.5530 | 0.9062 | 0.8397 | -0.1014 | 0/9 | 0.8469 | 0.0000 | success |
| mpnet_st_agnews | 10 | 1.0 | no_phase0 | 42 | 0.7308 | 0.8600 | 0.8892 | 0.9062 | 0.2838 | -0.1990 | 0/10 | n/a | 0.0000 | success |
| mpnet_st_agnews | 10 | 1.0 | raw_union_K20 | 42 | 0.8676 | 0.8600 | 0.8892 | 0.9062 | 0.8647 | -0.0657 | 0/10 | n/a | 0.0000 | success |
| roberta_base_agnews | 10 | 0.05 | no_phase0 | 42 | 0.7041 | 0.4542 | 0.5711 | 0.9142 | 0.2036 | -0.3000 | 0/9 | 0.7066 | 0.0000 | success |
| roberta_base_agnews | 10 | 0.05 | raw_union_K20 | 42 | 0.8555 | 0.4542 | 0.5711 | 0.9142 | 0.8442 | -0.1016 | 0/9 | 0.8541 | 0.0000 | success |
| roberta_base_agnews | 10 | 1.0 | no_phase0 | 42 | 0.7583 | 0.8684 | 0.8975 | 0.9142 | 0.2036 | -0.1876 | 0/10 | n/a | 0.0000 | success |
| roberta_base_agnews | 10 | 1.0 | raw_union_K20 | 42 | 0.8739 | 0.8684 | 0.8975 | 0.9142 | 0.8692 | -0.0696 | 0/10 | n/a | 0.0000 | success |

Raw per-cell JSONs live here as `cell_<backbone>_N<n>_a<α>_<method>_s<seed>_K<k>_<hash>.json`.
Per-client per-class counts at `partition_diagnostic.jsonl`. Slurm stdout/stderr at `runs/`. Long-form rows at `results.csv`.
