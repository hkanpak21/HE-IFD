# Issues — HE-IFD TNSE resubmission

File-based issue tracker. Each issue is a self-contained brief for a **context-zero agent** (you have no conversation history — read the linked files). Plan: [`docs/prd/he-ifd-tnse-resubmission.md`](../prd/he-ifd-tnse-resubmission.md). Operations: [`../../CLAUDE.md`](../../CLAUDE.md). Authoritative implementation reference: `results/colab_results/results_notebook.ipynb`.

Status snapshot as of **2026-05-30** — M1.5 complete; **M2 rooting underway**: FHE PoC (020) ✅, MIA suite (021) ✅ on MNIST, aggregation-design probes (023/024/025) ✅ verdict reached. A **2026-05-30 three-thread grill** (aggregation / MIA / synthetic — see [PRD Phase III](../prd/he-ifd-tnse-resubmission.md)) reframed the aggregation as **task arithmetic** and cut issues **026** (λ-coefficient verify), **027** (DP-MERF DP-soundness fix), **028** (MIA second backbone family). Open: 026/027/028 + the comparator table + paper writing. Per-issue verdicts in the STATUS blocks + `results/<case>/README.md`.

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

## Milestone 2 — Rooting: real-FHE + privacy (IN PROGRESS)

| # | Issue | Type | Status |
|---|---|---|---|
| 020 | [FHE PoC validation (Lattigo)](020-fhe-poc-validation.md) | AFK | ✅ DONE — end-to-end multiparty CKKS (DKG→encrypt→aggregate→threshold-decrypt); decrypted == plaintext **within CKKS bounds** (bar was ≤1e-3); cost table replaces the rejected 460 GB figure with a few MiB/round. |
| 021 | [MIA suite (3 attacks × 3 surfaces)](021-mia-suite.md) | AFK | ✅ DONE (MNIST) — released θ⋆ **near-chance** (AUC 0.49–0.57); prototype channel leaks raw (→0.80) but **DP ε≤8 → chance**. Extended by 028. |
| 028 | [MIA second backbone family](028-mia-second-backbone-family.md) | AFK | 📥 OPEN — ViT/CIFAR-100 (wrapper exists) + RoBERTa/AG-News (write wrapper, chunk shadows ≤3h). |
| 022 | [Synthetic-basin study (DP-MERF)](022-synthetic-basin-merf.md) | AFK | ⚠️ BLOCKED — generator DP-unsound (real records + cosmetic jitter); inverted contrast is an artifact. Superseded by 027. |
| 027 | [Fix DP-MERF generator (DP-sound) + re-verify](027-fix-dpmerf-generator-dpsound.md) | AFK | 📥 OPEN — sample fresh from a DP-fit model, never raw `X_c`; re-verify (Mode A acc must drop at ε=2), then re-run 022. |

## Milestone 2.5 — Aggregation design: task arithmetic (the 2026-05-30 grill)

Reframe: the server op θ⋆ = θ₀ + Σⱼwⱼ·Δⱼ **is task arithmetic** (Ilharco 2023). The deep conflict-resolution merges (TIES, FedFisher) are unnecessary *because the shared basin pre-aligns the deltas* — and cost prohibitive HE depth. The one HE-legal optimization knob is the scaling coefficient **λ**.

| # | Issue | Type | Status |
|---|---|---|---|
| 023 | [Local probe — how to combine updates](023-local-aggregation-trajectory-probe.md) | AFK (local) | ✅ DONE — round-robin trajectory == `weight_avg` exactly (diff 4e-7). |
| 024 | [Local probe — can non-linear one-shot beat averaging?](024-nonlinear-oneshot-combine-probe.md) | AFK (local) | ✅ DONE — no; `second_moment`/deep/depth-2 all lose (paired). "+22 RMSProp" was a non-reproducible artifact. |
| 025 | [Non-linear aggregation (VALAR)](025-nonlinear-aggregation-valar.md) | AFK | ✅ VERDICT — depth-1 weighted average wins; full 960-grid not needed. Reframed → 026. |
| 026 | [Task-arithmetic λ-coefficient cheap verify](026-task-arithmetic-lambda-verify.md) | AFK | 📥 OPEN — eval-only λ-interpolation sweep on MNIST-MLP + 1 ViT cell; decide a λ grid only if λ≠1 helps. |

## Milestone 3 — Paper writing (HITL with user)

Methodology + experiments rewrite from notebook/`src/` reality (bounded-trajectory **task-arithmetic** aggregation, not "encrypt final weights"). Framing locks from the 2026-05-30 grill: aggregation = task arithmetic + the basin-obviates-conflict-merges defense (cite Ilharco 2023, TIES/Yadav 2023, FedFisher/Jhunjhunwala 2024, MetaGPT/Zhou 2024); MIA dual story (model near-chance + prototype-DP collapses) across both modalities; synthetic = Mode-A DP-one-shot baseline vs Mode-B synth-few basin once 027 lands. Comparator table from `comparators/REPORTED_RESULTS.md`. HITL-paced with the user.

## How to read this directory (for a context-zero agent)

1. Open `docs/prd/he-ifd-tnse-resubmission.md` for the plan (read Phase II appendix for current state).
2. Open the issue file you're assigned (e.g. `010-*.md`). The **STATUS block at the top** tells you the current state and any continuation pointer; the body below is the original brief.
3. Operational rules: `../../CLAUDE.md` (VALAR/sbatch/conda/golden rules/3h cap/FL_TDSC deprecation banner).
4. Authoritative implementation reference: `results/colab_results/results_notebook.ipynb` (consult, do not modify — `src/` is the live code).
5. VALAR ops gotchas: `~/.claude/projects/-Users-a90-Documents-RESEARCH-HE-IFD/memory/valar-ops-gotchas.md`.
