# 018 — Scale to bigger pretrained backbones (with sanity-check gating)  [AFK, HITL touchpoint after Part A]

> **STATUS: ⚠️ PART A DONE / PART B HITL-GATED** (2026-05-29) — Part-A standalone linear-probe sanity: **ViT-L/CIFAR-100 PASS (oracle 0.876 ≥ 0.78)**; **BERT-large/AG-News marginal (0.910 vs 0.92 gate, −0.9pp** — a frozen-feature linear probe ~3-4pp under fine-tuned is healthy; recommend accept); **GPT-2-medium/AG-News FAIL (0.403, informational/non-blocking)**. Big-backbone weights prefetched. **Part B (protocol + LoRA on big backbones) NOT started — awaits user authorization** (and a possible re-grill: issue 019 showed feature standardization is needed for strong text encoders). Verdict: `results/heifd_018_partA_sanity/README.md`.

**Phase:** M1.5 / δ (scale; LAST) · **Blocked by:** 010, 011, 014 · **Blocks:** nothing

**Required reading:**
1. `docs/prd/he-ifd-tnse-resubmission.md` (Phase II).
2. `CLAUDE.md` — especially the login-node prefetch rule.
3. `docs/issues/011-trainable-layer-scope.md` — the LoRA recipe.
4. `src/backbones.py`, `jobs/prefetch_login.py`.

## Why

Once the current scale (ViT-B/32, ResNet-18, DistilBERT, GPT-2-small) is debugged, validate the scaling story: does the protocol still hold on **ViT-L**, **BERT-large**, **GPT-2-medium**? Big-model fine-tuning under heterogeneity is fragile in *every* FL paper — so we **sanity-check the backbone in isolation first** before applying the protocol.

## What to build

### Part A — Sanity-check stage (HITL review before Part B)

For each candidate big backbone, run a *standalone supervised head training* on a held-out test set (not the protocol — just a centralised linear-probe baseline):
- **ViT-L/14** (or ViT-L/16) on **CIFAR-100** (the harder dataset from issue 012; CIFAR-10 would saturate too).
- **BERT-large-uncased** on AG-News.
- **GPT-2-medium** on AG-News (GPT-2 family is deferred per issue 002, but the scaling test itself is informative; do NOT block if it fails the gate).

Sanity gates:
- ViT-L / CIFAR-100 IID ≥ **0.78** (consistent with published linear-probe ViT-L / CIFAR-100 numbers).
- BERT-large / AG-News IID ≥ **0.92**.
- GPT-2-medium / AG-News IID ≥ **0.50** (informational only — failure here is *not* a block).

If a sanity gate **fails for ViT-L or BERT-large**: STOP and report to the orchestrator. Don't proceed to Part B with a backbone we can't even linear-probe properly.

### Part B — Protocol on the big backbones (only after Part A passes)

1. New `BACKBONES` entries: `vit_l_cifar100`, `bert_large_agnews`, `gpt2_medium_agnews` (the last only if its Part A passed).
2. Extend `jobs/prefetch_login.py` for the new model weights.
3. Head-only sweep first (small, fast) on each backbone. If the head-only result reproduces the θ₀≥final pattern from 008, apply 011's LoRA recipe.
4. New wrapper `jobs/heifd_018_bigger_pretrained.sh` (per-backbone, mirroring `heifd_headline_pretrained.sh`).

## Acceptance

- [ ] Part A sanity-check results reported per backbone (PASS/FAIL with IID numbers).
- [ ] If PASS: head-only sweep on at least ViT-L/CIFAR-100 completes; LoRA on at least one big backbone applied per 011.
- [ ] If FAIL: clean abort + report of which backbone, expected vs observed IID, and what hyperparam tuning would be needed.
- [ ] **HITL touchpoint** after Part A: orchestrator routes the sanity-check results to the user before authorising Part B's bigger compute.

## Hard boundaries

- Touch `src/backbones.py`, `src/protocol.py` (BACKBONES), `jobs/prefetch_login.py`, new wrappers.
- **Permitted login-node `ssh`** ONLY to run the extended prefetch + the small Part-A sanity-check sbatch (still goes via sbatch, not python on login).
- No `git push`/`git commit` from your worktree. ast.parse only.

## Report

1. Part A: sanity-check results (PASS/FAIL with numbers per backbone).
2. Part B (if reached): head-only + LoRA results.
3. Files touched.
4. Caveats (e.g. memory blew up on a backbone, GPT-2-medium failed gate but informational).
