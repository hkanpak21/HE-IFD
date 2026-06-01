# 028 — MIA on a second backbone family (ViT/CIFAR-100 + RoBERTa/AG-News)  [AFK]

> **STATUS: ✅ DONE** (2026-05-30) — both backbones landed on Colab; headline AUC/TPR table in `results/heifd_021_mia/`. Full ROC arrays still on the Colab VM (pull via the notebook EXPORT cell when needed). **extends 021** (the `mia/` suite already exists and landed clean on MNIST). Decided at the 2026-05-30 grill ("add a second backbone family").

**Phase:** M2 (privacy validation) · **Blocked by:** none (reuses the 021 `mia/` suite) · **Blocks:** the §VI residual-leakage evidence covering both modalities.

**Required reading:**
1. `CLAUDE.md` (VALAR/sbatch/3h cap; pre-fetch on login node; never python on login node).
2. `mia/` — the existing 3-attack × 3-surface suite (Yeom / LiRA / GLiRA; external / fellow / prototype). Reuse it unchanged where possible.
3. `results/heifd_021_mia/README.md` — the landed MNIST result + table format to extend.
4. `jobs/heifd_021_mia_vit_cifar100.sh` — the ViT wrapper already written.

## Why

021 landed a clean MNIST/MLP MIA: the **released model θ⋆ is near-chance** (AUC 0.49–0.57 across Yeom/LiRA/GLiRA × external/fellow), and the **prototype channel** leaks raw (AUC up to 0.80 at α=1.0) but **DP ε≤8 collapses it to chance**. The paper headlines pretrained backbones across **vision and language**, so the attack evidence must cover a pretrained backbone in **both** modalities — not just a toy MLP, or a reviewer will note the attack regime doesn't match the headline regime.

## What to build

1. **Submit the existing ViT/CIFAR-100 MIA** (`jobs/heifd_021_mia_vit_cifar100.sh`) — wrapper already exists; this is a submission, just confirm it runs the 3×3 and lands.
2. **Write a RoBERTa/AG-News MIA wrapper** `jobs/heifd_028_mia_roberta_agnews.sh`, reusing the `mia/` suite. 64 shadow models on a transformer is heavy → **chunk shadow-model training ≤3h, resumable** (the suite already supports resume via `shadows/<cell>/`). Pre-fetch RoBERTa + AG-News on the login node first (compute nodes have no internet).
3. **Cells:** `vit_b32_cifar100` and `roberta_base_agnews`, N=10, α ∈ {0.05, 1.0} (heterogeneous + near-IID), the 3 attacks × 3 surfaces, ~64 shadows per target.

## Acceptance
- [x] ViT/CIFAR-100 + RoBERTa/AG-News MIA cells landed (TPR@0.1%FPR + AUC across the 3×3) under `results/heifd_021_mia/`. (Headline table committed; full ROC arrays for the log-log plot remain in `cell_*.json` on the Colab VM — pull via EXPORT when needed.)
- [x] Shadow training chunked + resumable (suite supports `--num-chunks`/`--chunk-index` + `shadows/<cell>/` resume); on Colab it ran in one session (64 shadows × 2 backbones), the VALAR wrappers keep the ≤3h array form.
- [x] The case README table extended with both backbones; story confirmed for language, deviation flagged for vision (see Outcome).

## Hard boundaries
- New `jobs/heifd_028_*.sh` + the RoBERTa MIA wrapper; reuse `mia/` unchanged where possible (a small read-only hook is acceptable if unavoidable — document it). Do NOT change `src/` training/aggregation semantics. No `git push`/`commit`/`sbatch`/`ssh`. Mac has no torch — ast.parse only; `bash -n` the wrapper.

## Report
1. The two backbones' MIA tables (released model + prototype channel, all surfaces/attacks).
2. How shadow training is chunked/resumed for the transformer cell.
3. Whether the MNIST dual-story (model near-chance; prototype DP ε≤8 → chance) holds across vision + language, or where it deviates.

## Outcome — DONE (2026-05-30, Colab; `results/heifd_021_mia/`)

Both pretrained backbones landed: 64 shadows, 3 attacks × 3 surfaces, α∈{0.05,1.0}, seed 42. Reused `mia/`
unchanged; the only code change was a version-robust `ag_news`→`fancyzhx/ag_news` fallback in
`src/backbones.py` (newer `datasets` reject the bare id). Wrappers `jobs/heifd_028_mia_roberta_agnews.sh`
(+ the ViT one) are VALAR-ready; the Colab notebook `notebooks/colab_028_mia.ipynb` is the path used.

- **RoBERTa / AG-News (language) — MNIST dual story HOLDS cleanly.** Released θ⋆ **near-chance under every
  attack** (AUC 0.49–0.53, incl. LiRA). Prototype channel barely leaks even raw (AUC 0.53 @α=0.05, 0.64
  @α=1.0); DP ε≤8 → ~0.49. Text sentence-embedding prototypes are far less identifiable than image features.
- **ViT / CIFAR-100 (vision) — prototype HOLDS, released-model DEVIATES.** Prototype raw 0.97 / 1.00 → DP
  ε2 0.53 / 0.56 ✅; but **LiRA on θ⋆ = AUC 0.85** (TPR@0.1%FPR 0.13–0.16) while threshold/GLiRA stay
  0.53–0.68. The "released model near-chance" headline does NOT hold for pretrained vision under LiRA.
- **Net:** prototype-channel DP-collapse is **universal** (both modalities); the near-chance released-model
  claim is solid for language and for ViT under threshold/GLiRA, but needs a **caveat for pretrained vision
  under LiRA** (flag for the paper; likely separable CIFAR-100 features + α heterogeneity → more
  memorization). Single seed (42); full ROC arrays pending an EXPORT pull.
