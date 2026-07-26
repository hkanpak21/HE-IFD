# ft02 — Harder-dataset loaders + Dirichlet partition + frozen-backbone caching  [AFK]

> **STATUS: 📥 OPEN** (2026-06-01) — supplies the tasks where a frozen backbone is NOT already linear-probe-solvable, so fine-tuning shows real lift (fixes the saturation + the old Figure 4).

**Phase:** Foundation · **Blocked by:** none (parallel with ft01) · **Blocks:** ft04–ft06, ft09.

**Required reading:**
1. `docs/prd/he-ifd-finetuning.md` (datasets section).
2. `CLAUDE.md` (datasets: `download=False`, pre-fetch on login node / Colab; results convention).
3. `src/data.py` (current loaders + Dirichlet partition + feature cache), `src/backbones.py` (frozen extractors).

## Why

ViT-B/32 on CIFAR saturates, so the method's value is invisible and the lift figure is empty. We need tasks with real headroom under a frozen backbone, across both modalities, partitioned with the same Dirichlet-α machinery and cached once for offline runs.

## What to build (in `src/data.py`, reusing the existing partition + cache)

1. **Fine-grained vision loaders**: CUB-200-2011, Stanford Cars, FGVC-Aircraft. Standard train/test splits; image transforms matching the frozen backbone's preprocessing.
2. **Large-label / domain-shift vision**: Tiny-ImageNet (200 classes) and/or one DomainNet domain-shift split. Pick whichever loads cleanly; document the choice.
3. **Harder many-class text**: Banking77 (77 intents), DBpedia-14, 20-Newsgroups, TREC. HF datasets — note the pre-fetch requirement (compute nodes / Colab offline after first fetch).
4. **Frozen-backbone feature + LoRA caching**: extend the feature cache so each (backbone, dataset) frozen-feature tensor is computed once and reused; LoRA fine-tuning reads features offline. Keyed by (backbone, dataset, split).
5. **Dirichlet partition reuse**: every new dataset partitions through the existing seed-keyed Dirichlet-α function; emit the per-client per-class `partition_diagnostic.jsonl`.

## Acceptance
- [ ] Each new dataset loads with `download=False` after a one-time fetch, partitions reproducibly by (seed, α), and caches frozen features offline.
- [ ] A `linear-probe vs frozen-feature` sanity print per (backbone, dataset) confirms the task is NOT already solved by a linear probe (headroom exists) — the selection criterion.
- [ ] `partition_diagnostic.jsonl` emitted; ast.parse clean.

## Hard boundaries
- Touch `src/data.py` (loaders + cache), maybe a small `src/backbones.py` preprocessing hook. Do NOT change partition/cache semantics for existing datasets. No `git push`/`commit`/`sbatch`/`ssh`. Document each dataset's fetch + license. Mac has no torch — ast.parse only.

## Report
1. Datasets wired + their splits/sizes/class counts + fetch instructions.
2. The linear-probe headroom check per (backbone, dataset) — which tasks qualify as "hard enough."
3. Cache keys + the partition-diagnostic output.
