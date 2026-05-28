# Issues — HE-IFD TNSE resubmission

File-based issue tracker. Each issue is a self-contained brief for a **context-zero agent** (you have no conversation history — read the linked files). Plan: [`docs/prd/he-ifd-tnse-resubmission.md`](../prd/he-ifd-tnse-resubmission.md). Operations: [`../../CLAUDE.md`](../../CLAUDE.md). Authoritative implementation reference: `results/colab_results/results_notebook.ipynb`.

Status snapshot as of **2026-05-28** — post M1 review gate, Phase II issues cut.

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

## Milestone 1.5 — Phase α: debug what's broken (highest priority)

| # | Issue | Type | What it does | Blocked by |
|---|---|---|---|---|
| 010 | [KD hyperparams + pytest re-run](010-kd-hyperparams-pretrained.md) | AFK | K/τ/LR sweep on resnet18 α=0.05 + close issue 003 | — |
| 011 | [Trainable-layer scope (head/LoRA/last-N)](011-trainable-layer-scope.md) | AFK + HITL review | The methodology lever; also fixes CNN-5 under-training | — |
| 012 | [Harder vision dataset for ViT](012-harder-vision-dataset.md) | AFK | CIFAR-100 + Tiny-ImageNet — addresses CIFAR-10 saturation | — |
| 013 | [KD dynamics diagnostic](013-kd-dynamics-diagnostic.md) | AFK | Teacher entropy + ‖Δᵢ‖ + cosine(Δᵢ,Δⱼ) — empirical-evidence anchor | — |

## Milestone 1.5 — Phase β: complete the from-scratch matrix

| # | Issue | Type | What it does | Blocked by |
|---|---|---|---|---|
| 014 | [Complete 3-dataset from-scratch matrix](014-complete-fromscratch-matrix.md) | AFK | LeNet/FMNIST full grid + N=1 extension + CNN-5/CIFAR-10 full grid | 011 (for CNN-5 part) |
| 015 | [DP-ε frontier on from-scratch](015-dp-epsilon-frontier-fromscratch.md) | AFK | ε ∈ {0.5, 32, ∞} + Kpc ∈ {1, 5} — the averaging-variant DP frontier figure | 014 (for FMNIST + CNN-5 parts; standalone for MNIST) |

## Milestone 1.5 — Phase γ: alignment-strategy expansion

| # | Issue | Type | What it does | Blocked by |
|---|---|---|---|---|
| 016 | [Synthetic-sample alignment](016-synthetic-sample-alignment.md) | AFK | Per-client small generator → synthetic samples instead of mean prototypes | — |
| 017 | [No-probe DP-common-basin](017-noprobe-dp-common-basin.md) | AFK | Fully-DP, no labelled public data — warmup on the noisy prototype set itself | — |

## Milestone 1.5 — Phase δ: scale to bigger models (LAST in M1.5)

| # | Issue | Type | What it does | Blocked by |
|---|---|---|---|---|
| 018 | [Bigger pretrained backbones](018-bigger-pretrained-backbones.md) | AFK + HITL review (Part A) | ViT-L / BERT-large / GPT-2-medium with mandatory sanity-check gating | 010, 011, 014 |

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
