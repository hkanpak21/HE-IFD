# Issues — HE-IFD TNSE resubmission

File-based issue tracker. Each issue is a self-contained brief for a **context-zero agent** (you have no conversation history — read the linked files). Plan: [`docs/prd/he-ifd-tnse-resubmission.md`](../prd/he-ifd-tnse-resubmission.md). Operations: [`../../CLAUDE.md`](../../CLAUDE.md). Authoritative implementation reference: `results/colab_results/results_notebook.ipynb`.

Status snapshot as of **2026-05-29** — Phase II (M1.5) experimentally complete: Phase α/β/γ done, Phase δ Part-A done (Part-B HITL-gated), Phase ε (019 text-backbone fix) done. Remaining unbuilt: **M2 Real-FHE (Lattigo) + MIA suite** and the comparator table. Per-issue verdicts in the issue STATUS blocks + `results/<case>/README.md`.

## Methodology framing (locked at the M1 review)

> *"Given a set of clients with a shared-basin initial model, produce a combined model by distillation, with HE guarantees on the updates and the data."*

Trainable-layer-scope adjustments (head-only ↔ LoRA-on-last-blocks ↔ last-N-blocks fine-tuning) are acceptable as long as the **server aggregation stays linear** (PT×CT + CT+CT only).

## Defensibility bar (Phase α must close every gap that fails this)

For each (backbone, dataset) in the final headline set:
- `raw_union > no_phase0` (alignment helps).
- `raw_union ≥ θ₀` in most regimes (distillation does not actively hurt).
- `raw_union → oracle` at α=1.0 (recovers centralised at IID).
- `M4 > 0` at low α (federation gives OOD value to clients).

## Milestone 1 — Foundation + Headline (LANDED 2026-05-28)

1800 cells, 0 failures. Status per issue (open file for full STATUS block):

| # | Issue | Type | Status | One-line summary |
|---|---|---|---|---|
| 001 | [Consolidate notebook → flat `src/`](001-consolidate-src-package.md) | AFK | ✅ DONE | 10-module `src/` + 3 hotfixes; v1/v2 archived; base verified green |
| 002 | [GPT-2 feature extraction fix](002-fix-gpt2-feature-extraction.md) | AFK | ✅ DONE | Left-pad + last-token; residual GPT-2 weakness DEFERRED |
| 003 | [Unit tests](003-unit-tests-load-bearing-modules.md) | AFK | ⚠️ PARTIAL | Tests merged; pytest install pending — folded into **010** |
| 004 | [Teacher cache](004-teacher-cache.md) | AFK | ⏸️ DEFERRED | Low value vs QOS-serial bottleneck |
| 005 | [M3/M4/θ₀/no-align metrics](005-incentive-ood-metrics.md) | AFK | ✅ DONE | All metrics inline; surfaced the alignment-does-most finding |
| 006 | [Aggregation-coherence ablation](006-aggregation-coherence-ablation.md) | AFK | 📦 HELD | Code merged; job held pending **011** (cnn5 fix) |
| 007 | [From-scratch headline sweep](007-from-scratch-headline-sweep.md) | AFK | ⚠️ PARTIAL | MNIST/MLP DONE; FMNIST+CIFAR-10 backbones merged; CNN5 grid blocked on **011** |
| 008 | [Pretrained headline sweep](008-pretrained-headline-sweep.md) | AFK | ✅ DONE | 1440/1440 cells; θ₀≥final + ViT saturation + GPT-2 weakness flagged → Phase II |
| 009 | [M1 review gate](009-m1-review-gate.md) | HITL | ✅ COMPLETED | User chose debugging round before paper framing |

## Milestone 1.5 — Phase α: debug what's broken (highest priority)  — ✅ COMPLETE

| # | Issue | Type | Status (verdict in `results/<case>/README.md`) |
|---|---|---|---|
| 010 | [KD hyperparams + pytest re-run](010-kd-hyperparams-pretrained.md) | AFK | ✅ DONE — τ is the lever; (K=100,τ=1,lr=0.001)→0.76 vs θ₀ 0.74 (partial). New pretrained KD default. Pytest installed (closes 003). |
| 011 | [Trainable-layer scope (head/LoRA/last-N)](011-trainable-layer-scope.md) | AFK + HITL | ✅ DONE — **head_only sufficient**; LoRA ≈ head, last_block harms. "Tiny head" framing vindicated. |
| 012 | [Harder vision dataset for ViT](012-harder-vision-dataset.md) | AFK | ✅ DONE — **ViT/CIFAR-100 client-benefit win** (m4 0.81, 3.6× mean_teacher, →oracle at IID). |
| 013 | [KD dynamics diagnostic](013-kd-dynamics-diagnostic.md) | AFK | ✅ DONE — basin-cancellation supported (~60% neg-cosine Δᵢ pairs). |

## Milestone 1.5 — Phase β: complete the from-scratch matrix  — ✅ COMPLETE

| # | Issue | Type | Status |
|---|---|---|---|
| 014 | [Complete 3-dataset from-scratch matrix](014-complete-fromscratch-matrix.md) | AFK | ✅ DONE — LeNet/FMNIST 450/450 solid + MLP/MNIST N=1; **CNN-5/CIFAR-10 outside the basin-coherence envelope** (see 016b). |
| 015 | [DP-ε frontier on from-scratch](015-dp-epsilon-frontier-fromscratch.md) | AFK | ✅ DONE (mlp+lenet) — averaging-variant frontier **flattens from ε≈2**; Kpc≥5 at ε=2. cnn5 deferred (out of envelope). |

## Milestone 1.5 — Phase γ: alignment-strategy expansion  — ✅ COMPLETE

| # | Issue | Type | Status |
|---|---|---|---|
| 016 | [Synthetic-sample alignment](016-synthetic-sample-alignment.md) | AFK | ✅ DONE — synthetic viable + DP-protectable (≈raw_union on pretrained); logit marginal. Extended: 016+ (K_pc-fattening rejected), 016b (CNN-5 distill out of envelope). |
| 017 | [No-probe DP-common-basin](017-noprobe-dp-common-basin.md) | AFK | ✅ DONE — **THESIS WIN** (375/375): large distillation lift (+0.17–0.60) in the low-leak/weak-θ₀ regime; cost-of-no-probe negative. |

## Milestone 1.5 — Phase δ: scale to bigger models (LAST in M1.5)

| # | Issue | Type | Status |
|---|---|---|---|
| 018 | [Bigger pretrained backbones](018-bigger-pretrained-backbones.md) | AFK + HITL | ⚠️ **Part A done, Part B HITL-gated** — ViT-L/CIFAR-100 PASS (0.876); BERT-large marginal (0.910 vs 0.92); GPT-2-medium fail-informational (0.403). Part B awaits user authorization. |

## Milestone 1.5 — Phase ε: pretrained-backbone improvement (AFK autonomous, 2026-05-29)

| # | Issue | Type | Status |
|---|---|---|---|
| 019 | [Stronger frozen text backbones](019-stronger-text-backbones.md) | AFK | ✅ DONE (AG-News; DBpedia-14 running) — roberta-base + all-mpnet + **z-score feature normalization** fix the text weak link: α=0.05 acc 0.85 / m4 0.85, matching ViT/CIFAR-100 (~2× DistilBERT). |

## Milestone 2 — Rooting (DEFERRED until Phase α + β land — to be re-grilled)

Original scope (subject to re-grill after Phase α/β results because methodology may shift):
- Real-FHE validation in Lattigo: one MLP end-to-end multiparty CKKS run (DKG → encrypt → aggregate → threshold-decrypt). L2 ≤ ~1e-3 vs plaintext + timing + comm bytes.
- MIA suite over 3 surfaces (prototype-distance fellow-client / external-LiRA on released student / fellow-client combined).

## Milestone 3 — Paper writing (HITL with user, AFTER all experiments)

Locked at the M1 review: **paper writing does not begin until Phase α + β land** — no parallel writing on shaky methodology. Methodology + experiments rewrite from notebook reality + the alignment-preserving framing if it survives M1.5. Comparator table from `comparators/REPORTED_RESULTS.md`. HITL-paced with the user.

## How to read this directory (for a context-zero agent)

1. Open `docs/prd/he-ifd-tnse-resubmission.md` for the plan (read Phase II appendix for current state).
2. Open the issue file you're assigned (e.g. `010-*.md`). The **STATUS block at the top** tells you the current state and any continuation pointer; the body below is the original brief.
3. Operational rules: `../../CLAUDE.md` (VALAR/sbatch/conda/golden rules/3h cap/FL_TDSC deprecation banner).
4. Authoritative implementation reference: `results/colab_results/results_notebook.ipynb` (consult, do not modify — `src/` is the live code).
5. VALAR ops gotchas: `~/.claude/projects/-Users-a90-Documents-RESEARCH-HE-IFD/memory/valar-ops-gotchas.md`.
