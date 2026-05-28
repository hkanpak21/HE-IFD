# 008 — Pretrained headline sweep  [AFK]

> **STATUS: ✅ DONE** (2026-05-28) — full pretrained grid; caveats under investigation.
>
> Four per-backbone jobs (1112414–1112417), non-array (avoids feature-extraction race). **1440/1440 cells, all status=success.** Login-node prefetch (`jobs/prefetch_login.py`) populated HF + torchvision caches before submission; compute nodes loaded offline (`HF_HUB_OFFLINE=1`).
> **Headline raw_union accs (mean over 3 seeds, N=10) — α=0.05 / IID:**
> resnet18 0.48 / 0.83 · vit_b32 **0.93 / 0.97** · distilbert 0.44 / 0.86 · gpt2 0.40 / 0.48.
> **Caveats under investigation (NEW issues 010–013):**
>   - *θ₀ ≥ final at low α for strong pretrained backbones* (especially resnet18: θ₀=0.74 vs final=0.48 at α=0.05) → issues **010** (KD hyperparams), **011** (trainable layer scope), **013** (KD dynamics diagnostic).
>   - *ViT saturation on CIFAR-10* (0.97 IID = no headroom) → issue **012** (harder dataset: CIFAR-100 / Tiny-ImageNet).
>   - *GPT-2 weakness across α* → deferred to future work per issue **002**.

**Milestone:** M1 · **Blocked by:** 001, 002, 004, 005 · **Blocks:** 009

**Required reading:** [`docs/prd/...`](../prd/he-ifd-tnse-resubmission.md), [`CLAUDE.md`](../../CLAUDE.md) (networking note is critical here).

## What to build

The pretrained-backbone headline grid — the intended deployment, across vision and text:

- **Vision (CIFAR-10):** ViT-B/32 and ResNet-18, frozen backbone + trainable head.
- **Text (AG News):** DistilBERT and GPT-2 (with the **002 feature-extraction fix** — verify GPT-2 IID ≈ 0.90, not 0.25, before trusting any GPT-2 cell).
- **Axes:** N ∈ {5, 10, 20, 50}; α ∈ {0.01, 0.05, 0.1, 0.3, 1.0}; K-sweep; alignment-strategy ablation {no-Phase0, raw-proto, DP-avg ε ∈ {0.5, 2, 8, 32}} × Kpc.
- **Metrics per cell (inline, from 005):** IID + M3 + M4 + θ₀ + no-align; 3 seeds.
- One `results/<case>/` per (backbone, dataset).

## Acceptance criteria

- [ ] Weights (ViT, ResNet, DistilBERT, GPT-2) **and** the AG-News dataset are **pre-fetched on the login node** into the HF/torch cache before any compute-node job; jobs load with `HF_HUB_OFFLINE=1` / `local_files_only`.
- [ ] GPT-2 cells reflect the 002 fix (no ~0.25 chance-floor rows).
- [ ] Full grid run for all four (backbone, dataset) pairs, 3 seeds, under `results/<case>/`.
- [ ] Each cell reports IID + M3 + M4 + θ₀ + no-align inline; teacher/feature caches (004) reused.
- [ ] Grid split into **≤3-hour VALAR jobs**, resumable.

## How to verify

Confirm GPT-2 cells are non-trivial; inspect `results/<case>/` tables. Sanity: pretrained backbones lift the no-alignment baseline far above the from-scratch case; alignment still helps at α ≤ 0.1.

## Ops

**Pre-fetch on the login node first** (compute nodes have no internet). `sbatch` only; **`--time` ≤ 03:00:00**, chunked + resumable. Env `he_ofl`.
