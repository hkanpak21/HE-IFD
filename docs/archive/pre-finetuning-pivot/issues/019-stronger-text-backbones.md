# 019 — Stronger pretrained TEXT backbones (+ richer text dataset)  [AFK, autonomous]

> **STATUS: ✅ DONE** (AG-News; DBpedia-14 in flight; 2026-05-29) — **text is no longer the weak link**. Root cause of GPT-2/DistilBERT weakness diagnosed (GPT-2 is a poor frozen extractor, oracle 0.67; DistilBERT collapses at α=0.05). Swapped in strong frozen encoders **roberta-base + all-mpnet-base-v2** (transformers-only, no new deps). First verify exposed an α=0.05 warmup collapse (roberta θ₀=random 0.25) → fixed with **per-backbone z-score feature standardization** (gated; others byte-identical). Result: roberta/mpnet AG-News α=0.05 **acc 0.85, m4 0.85** — matches ViT/CIFAR-100, ~2× DistilBERT. Full headline grids 360/360 each (m4 0.81–0.87 across α, → oracle 0.91 at IID). DBpedia-14 (14-class, richer OOD) verify running. Verdict: `results/heifd_019_text_verify/README.md` + `heifd_019_text_headline/`.

**Phase:** M1.5 / pretrained-backbone improvement · **Blocked by:** none · **Blocks:** the text half of the pretrained-deployment headline

## Why (investigation findings)

The pretrained-vision story is strong (ViT-B/32 / CIFAR-100, α=0.05: acc 0.811, θ₀ 0.806, mean_teacher 0.226, oracle 0.868, **m4_ood 0.807**, global model 3.6× the average client teacher). The **text story is the weak link**:

| backbone | α=0.05 acc | θ₀ | mean_t | **oracle** | m4_ood |
|---|---:|---:|---:|---:|---:|
| distilbert_agnews | 0.437 | 0.410 | 0.293 | **0.904** | 0.363 |
| gpt2_agnews | 0.333 | 0.266 | 0.274 | **0.666** | 0.337 |
| gpt2_medium_agnews (Part-A) | — | — | — | **0.403** | — |
| bert_large_agnews (Part-A) | — | — | — | **0.910** | — |

Two root causes:
1. **GPT-2 family is a poor FROZEN extractor for classification** — `gpt2_agnews` oracle is only 0.666, `gpt2_medium` linear-probe 0.403. Causal-LM features aren't linearly separable for topic classification. (This is the issue-002 deferred weakness, now quantified.) GPT-2 should be replaced, not tuned.
2. **DistilBERT works at IID (0.864) but collapses at α=0.05 (0.437 vs its own oracle 0.904)** — a 47-pp gap. AG-News has only **4 classes**, so α=0.05 Dirichlet over 4 classes ≈ 1 class/client (extreme heterogeneity) and m4 has only 3 OOD classes to demonstrate value on. A stronger frozen encoder (higher oracle ceiling, more linearly-separable features) should lift the heterogeneous regime closer to the vision story.

## Locked thesis (the bar)

The backbone is **frozen** — it never enters the HE combination; only the small trainable head displacement Δᵢ is encrypted/aligned/combined. So we have **total freedom on the backbone choice** (the user explicitly lifted the model constraint for language). Success = the federated global model is strong + beats each party's local teacher (mean_teacher) + m4_ood > 0, with low-leak one-shot aligned updates. Target: bring the text α=0.05 client-benefit numbers up toward the ViT/CIFAR-100 level.

## What to build

### Part 1 — Strong frozen text backbones (primary)

Add 2 modern frozen text encoders as `BACKBONES` entries (kind="head", feature_loader `text:<name>`), wired through the existing `extract_text_features` mechanism. Recommended (agent may substitute with justification, prioritising offline-prefetchable HF models + strong frozen linear-probe on AG-News):
- **`roberta_base`** (`roberta-base`, 125M, bidirectional) — mean-pool last hidden state (right-pad), like distilbert. Expected AG-News linear-probe ~0.92+.
- **`mpnet_st`** (`sentence-transformers/all-mpnet-base-v2`, 768-dim) — a purpose-built sentence-embedding model; use **mean-pooling over tokens** (its training-time pooling). This is the cleanest "strong frozen embedding → linear head" candidate; expected AG-News linear-probe ≥0.93.

Both must use the existing bidirectional mean-pool path (right-pad), NOT the GPT-2 causal last-token path. Reuse `extract_text_features` — just add the new model-name branches + tokenizer/model loading mirroring `distilbert`/`bert_large`.

### Part 2 — Richer text dataset (secondary, the text analogue of CIFAR-100)

AG-News's 4 classes cap the heterogeneity + OOD story. Add **`dbpedia_14`** (DBpedia-14, 14 topic classes, standard HF dataset, ~560k train / 70k test — subsample test to ~10k for speed). 14 classes gives a meaningful α=0.05 heterogeneity + 13 OOD classes for m4 — mirroring CIFAR-100's role on vision. Add a loader to `src/data.py` (or extend `extract_text_features` to take a dataset arg; AG-News is currently hardcoded as `"ag_news"`). New BACKBONES entries: `roberta_base_dbpedia`, `mpnet_st_dbpedia` (num_classes=14). If dataset plumbing is heavy, keep AG-News backbones as the must-have and mark DBpedia best-effort.

### Part 3 — Verify wrapper

`jobs/heifd_019_text_verify.sh` (CLAUDE.md template, ≤3h, t4_ai/comx29/comx29, ≥32G mem, HF_HUB_OFFLINE + TRANSFORMERS_OFFLINE): run the new backbones × {no_phase0, raw_union_K20} × α∈{0.05, 1.0} × N=10 × seed 42, K=100/τ=1/lr=0.001 (the issue-010 best KD defaults). Plus the AG-News dbpedia cells if Part 2 lands. case slug `heifd_019_text_verify`. Placeholder README documenting the comparison-to-DistilBERT question.

A full grid wrapper `jobs/heifd_019_text_headline.sh` (mirroring the pretrained headline, N+α grid, 3 seeds) prepared but NOT auto-submitted — the orchestrator submits after the verify confirms the new backbones beat DistilBERT at α=0.05.

## Acceptance

- [ ] ≥2 strong frozen text backbones runnable via `extract_text_features` (offline-loadable after login-node prefetch).
- [ ] Verify shows the new backbone's α=0.05 raw_union acc + m4_ood **substantially above DistilBERT** (target: acc ≥ 0.6, m4 ≥ 0.5 — toward the ViT/CIFAR-100 level), with oracle ≥ 0.93.
- [ ] (If Part 2) DBpedia-14 cells produce sensible numbers (richer OOD/m4 story).
- [ ] Verdict in case README: does a stronger frozen text encoder bring the text deployment story up to the vision level?

## Hard boundaries
- NO `git push`/`git commit`/`sbatch`/`ssh` from the worktree (orchestrator merges, prefetches weights on the login node, and submits). ast.parse only — Mac has no torch/transformers.
- Touch only: `src/backbones.py` (new text extractor branches), `src/protocol.py` (new BACKBONES entries; `extract_text_features` dataset-arg if doing Part 2), `src/data.py` (DBpedia loader if Part 2), `jobs/prefetch_login.py` (flag-gated additions for the new weights + dataset), `jobs/heifd_019_text_verify.sh` + `jobs/heifd_019_text_headline.sh` (new), `results/heifd_019_text_verify/README.md` (placeholder).
- DO NOT touch distill.py / aggregate.py semantics, existing BACKBONES entries, FL_TDSC/, src/v1/, src/v2/, comparators/.
- Existing behaviour byte-identical without the new backbone names / prefetch flag.

## Report
1. Which backbones added + why (frozen linear-probe expectations on AG-News).
2. Whether DBpedia-14 (Part 2) was implemented or deferred.
3. Prefetch additions (model IDs, est. sizes) — the orchestrator will run the login-node prefetch.
4. Verify wrapper grid + the comparison-to-DistilBERT it tests.
5. Files touched + boundary confirmation.
