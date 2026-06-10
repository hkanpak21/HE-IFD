# Issues — HE-IFD: Federated Fine-Tuning of Pretrained Models under HE

File-based issue tracker for the **fine-tuning pivot** (2026-06-01). Each issue is a self-contained brief
for a **context-zero agent** (no conversation history — read the linked files). Plan:
[`docs/prd/he-ifd-finetuning.md`](../prd/he-ifd-finetuning.md). Operations: [`../../CLAUDE.md`](../../CLAUDE.md).

> **📥 NEEDS-TRIAGE (2026-06-10):** new PRD
> [`docs/prd/he-ifd-freeze-a-improvement.md`](../prd/he-ifd-freeze-a-improvement.md) — the
> **freeze-A era**: both-A-B LoRA's bilinear merge falsified the task-arithmetic spine (and caused
> the α=0.1 seed collapses), so the method moves to freeze-A + a measured improvement program
> (semantic head init, depth-1 Fisher/count-head num-denom merges, λ grid + client-vote selection,
> CIFAR-100/ViT vision arm) BEFORE headline claims are worded. Code already landed:
> `jobs/finetune_improve.{py,sh}`, `notebooks/improve_program.ipynb`,
> `results/finetune_improve/`. It supersedes the "both LoRA matrices trained" wording of ft01 and
> re-scopes ft04–ft09's configs to the program's winning configuration; triage should break it
> into issues (suggested: run-S1–S6, agg-math unit tests, matched-setup comparators, threat-model
> + leakage section rewrite, FHE cost re-measurement on the freeze-A payload).
Pre-pivot planning state (distillation era, issues 001–028) is archived at
[`docs/archive/pre-finetuning-pivot/`](../archive/pre-finetuning-pivot/).

## Thesis (the spine these issues serve)

One-shot federated **fine-tuning of pretrained models** under multiparty CKKS, from a **shared loss basin**.
HE has no programmability (compute on obfuscated ciphertexts → a fixed depth-1 circuit only), so the learning
happens client-side and the server only does a sample-weighted linear combine (**task arithmetic** on
fine-tuning deltas). A frozen pretrained backbone supplies the shared basin; **LoRA(+head)** is the trainable
unit; **direct fine-tuning** is the headline local step (**distillation = ablation**).

## Locked decisions (2026-06-01 grill)

- Method = direct fine-tuning headline + distillation ablation.
- Trainable unit = LoRA adapters (+ head); head-only / last-N reported as a comparison.
- Datasets = fine-grained vision + large-label/domain-shift vision + harder many-class text; reduced
  from-scratch kept secondary; core backbones ViT-B/32 + RoBERTa/MPNet, optional CLIP/DINOv2/E5/BGE ("a couple of tries").
- 3 seeds {42,43,44} throughout.
- **Notebooks are start-once**: one config cell asks everything, then the grid runs unattended + resumable.

## Carry-forward (do NOT redo — transfers from the archived issues)

FHE PoC + measured cost sweep (Lattigo, depth-1); MIA suite (leak-minimization framing); λ regularizer;
DP-MERF DP-soundness fix (verdict: not a competitive basin source). LoRA only changes the **ciphertext
budget** in the cost section, not the protocol.

## Foundation (unblocks everything; do these first)

| # | Issue | Type | Status | One-line |
|---|---|---|---|---|
| ft01 | [Method: LoRA + direct fine-tuning (distillation as ablation)](ft01-method-lora-direct-finetuning.md) | AFK | 📥 OPEN | direct-FT trajectory + LoRA trainable unit in `src/`; aggregate untouched |
| ft02 | [Harder-dataset loaders + partition + caching](ft02-harder-dataset-loaders.md) | AFK | 📥 OPEN | CUB/Cars/Aircraft, TinyImageNet/DomainNet, Banking77/DBpedia/20NG/TREC + Dirichlet + feature cache |
| ft03 | [Start-once unattended notebook framework](ft03-unattended-notebook-framework.md) | AFK | 📥 OPEN | one config cell asks everything → autonomous, resumable run-all |

## Headline experiments (depend on ft01–ft03)

| # | Issue | Type | Status | One-line |
|---|---|---|---|---|
| ft04 | Fine-grained vision headline | AFK | ⬜ TODO | CUB/Cars/Aircraft × LoRA × N×α × 3 seeds; lift + coverage |
| ft05 | Large-label / domain-shift vision headline | AFK | ⬜ TODO | TinyImageNet/DomainNet × LoRA × axes × 3 seeds |
| ft06 | Harder many-class text headline | AFK | ⬜ TODO | Banking77/DBpedia/20NG/TREC × RoBERTa/MPNet × axes × 3 seeds |

## Ablations + analysis (depend on ft01–ft03)

| # | Issue | Type | Status | One-line |
|---|---|---|---|---|
| ft07 | Trainable-unit comparison (head/LoRA/last-N) + ciphertext budget | AFK | ⬜ TODO | accuracy ↔ ciphertext trade-off on a hard task |
| ft08 | Direct-FT vs distillation ablation | AFK | ⬜ TODO | does soft-label regularization help on hard tasks? |
| ft09 | λ-regularizer + rebuild the fine-tuning-lift figure on hard tasks | AFK | ⬜ TODO | fixes the old Figure 4 (lift should be real on hard tasks) |
| ft10 | Couple-of-tries extra backbones (CLIP/DINOv2/E5/BGE) | AFK | ⬜ TODO | low priority; breadth if they train well |

## Crypto cost + paper (carry-forward / HITL)

| # | Issue | Type | Status | One-line |
|---|---|---|---|---|
| ft11 | CKKS comm/compute section + LoRA ciphertext budget + prior-work comparison | AFK + HITL | ⬜ TODO | extend the measured cost sweep; write the comprehensive section |
| ft12 | Paper refactor: "why fine-tuning" section, experiments refactor, Figure 4 replacement, reduced from-scratch, MIA carry-forward | HITL | ⬜ TODO | the writing pass, with the user |

## How to read this directory (context-zero agent)

1. `docs/prd/he-ifd-finetuning.md` — the plan.
2. Your issue file (`ft0N-*.md`) — the **STATUS block** + brief.
3. `../../CLAUDE.md` — VALAR/Colab ops, golden rules, conda env, results convention.
4. Carried-forward code lives in `src/`, `fhe/`, `mia/`; archived planning context in `docs/archive/pre-finetuning-pivot/`.
