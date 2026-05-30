# 028 — second backbone family (RoBERTa/AG-News), extends 021

> This note lives in a **separate file** on purpose: `README.md` in this case dir
> is auto-overwritten by `mia.report.write_report` (`mia/report.py` →
> `(root / "README.md").write_text(...)`) every time `mia.run` produces results.
> Anything written into README.md by hand would be clobbered on the next run, so
> the durable 028 description belongs here.

## What 028 adds

021 landed the MNIST/MLP MIA. 028 extends the **same `mia/` suite, unchanged**, to
a **pretrained backbone in each modality**, so the §VI residual-leakage evidence
matches the paper's pretrained-backbone headline regime rather than a toy MLP:

| backbone | modality | dataset | wired in | wrapper |
|---|---|---|---|---|
| `vit_b32_cifar100`     | vision   | CIFAR-100 (100 cls) | 021 | `jobs/heifd_021_mia_vit_cifar100.sh` |
| `roberta_base_agnews`  | language | AG-News (4 cls)     | **028 (new)** | `jobs/heifd_028_mia_roberta_agnews.sh` |

Both cells share **CASE `heifd_021_mia`**, so both pretrained backbones land in
**one** case dir and **one** auto-written README table (alongside the MNIST cell).
`roberta_base_agnews` is already a registered backbone in
`src.protocol.BACKBONES` (`kind="head"`, `num_classes=4`,
`feature_loader="text:roberta_base"`, `normalize_features="zscore"`) — so
`mia.run --backbones roberta_base_agnews` runs without any edit to `src/` or
`mia/`.

## Cells (028 RoBERTa)

`roberta_base_agnews`, **N=10**, **α∈{0.05, 1.0}** (heterogeneous + near-IID),
the **3 attacks** (Yeom threshold / LiRA / GLiRA) × **3 surfaces** (external /
fellow / prototype, the prototype channel sweeping ε∈{∞(raw),8,2} internally),
**~64 shadow models** per target. Same grid shape as the ViT cell.

## REQUIRED login-node prefetch (compute nodes have no internet)

Before submitting the RoBERTa wrapper, populate the HF caches ONCE on the
**login node** (this is the sanctioned download-only login-node exception):

```sh
python jobs/prefetch_login.py --include-text019   # roberta-base weights + ag_news
```

`--include-text019` pulls `roberta-base` (the `ag_news` HF dataset is pulled by
the always-on path in `prefetch_login.py`, so this single command covers both
the backbone weights and the dataset). The first compute-node task then runs the
frozen extractor ONCE — `extract_text_features("roberta_base", "ag_news", …)` —
caching the 768-d AG-News sentence embeddings to
`cache/features/ag_news_roberta_base.pt`. Every subsequent task / shadow model
reads that cache offline (`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`).

## Chunk / resume scheme (the 3h cap)

64 shadows on a transformer is heavy, so the suite chunks at the **model** level
(target = model 0, then 64 shadows = 65 models per (α, seed)) and resumes from
per-model checkpoints — identical to the ViT wrapper:

1. **Warm the feature cache once** (cold-cache → single task), to avoid a
   concurrent-extraction race when the array fans out onto a cold cache:
   ```sh
   sbatch --export=ALL,NUM_CHUNKS=8,CHUNK_INDEX=0 jobs/heifd_028_mia_roberta_agnews.sh
   ```
2. **Fan out the remaining model chunks** (round-robin over the 65 models via
   `NUM_CHUNKS`/`CHUNK_INDEX`, set from `SLURM_ARRAY_TASK_COUNT`/`_ID`); each task
   trains ~8 models and lands well under 3h:
   ```sh
   sbatch --array=1-7 --export=ALL,NUM_CHUNKS=8 jobs/heifd_028_mia_roberta_agnews.sh
   ```
3. **Score** once all 65 `shadows/<cell>/model_XXXX.npz` checkpoints exist (a
   cheap report-only pass that rewrites README/summary):
   ```sh
   sbatch --export=ALL,SCORE_ONLY=1 jobs/heifd_028_mia_roberta_agnews.sh
   ```

A preempted task resumes by skipping models whose checkpoint already exists; no
single job exceeds the 3h cap.

## Expected story to confirm (to be filled by the run)

The MNIST dual-story should reproduce on a pretrained backbone in **both**
modalities (vision ViT + language RoBERTa):

1. **Released model θ⋆ (external / fellow)** — near-chance: low TPR@0.1%FPR, AUC
   ≈ 0.5 across Yeom/LiRA/GLiRA. (MNIST: AUC 0.49–0.57.) The bounded K-step
   distillation from a shared basin over N=10 clients limits per-example
   memorisation.
2. **Prototype channel** — leaks raw (high AUC/TPR at raw release, larger at the
   near-IID α=1.0), then **collapses toward chance as ε tightens** (ε=8 then
   ε=2 → AUC→0.5, TPR@0.1%FPR→0.001), confirming the averaging-variant DP
   accounting empirically.

Fill the numbers from the per-cell JSONs / `summary.json` once both ViT and
RoBERTa cells land; flag any deviation from this story (e.g. if RoBERTa's
prototype channel leaks more/less than ViT, or the released model is above chance
on either modality).
