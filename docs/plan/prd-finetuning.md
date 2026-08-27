> **Stale header, 2026-08-23.** Its status line still says the paper is being
> refactored from the pre-pivot draft. The method is settled and lives in
> `docs/paper/sections/method.tex`. Read this for the product reasoning behind
> the fine-tuning framing, not for the current protocol or the current plan.

# PRD — HE-IFD: One-Shot Federated Fine-Tuning of Pretrained Models under HE

**Status:** active
**Created:** 2026-06-01 (pivot from the one-shot federated *distillation* framing; previous PRD + issues archived at `docs/archive/pre-finetuning-pivot/`)
**Source of truth:** the consolidated `src/` package + landed `results/<case>/` numbers; the pre-pivot paper at `docs/paper/` (being refactored, not discarded). Checkpoint of the pre-pivot state: commit `55e0fc0`.
**Origin:** decided 2026-06-01 with the PIs — reframe the paper toward **federated fine-tuning of pretrained models** and publish it this way.

---

## Problem Statement

The method works and the crypto is sound, but the *framing* undersells it and one experiment actively hurts:

1. The paper is framed as one-shot federated **distillation** spanning from-scratch and pretrained models. The from-scratch half is off the real value proposition, and the "distillation" label obscures what the method actually does for deployment: **fine-tune a pretrained model, federatedly, in one shot, under encryption.**
2. **ViT-B/32 on CIFAR saturates** (≈0.97 IID): the frozen features are already linearly separable, so the method has no headroom to demonstrate value, and the per-client benefit is invisible.
3. **Figure 4 (distillation lift vs. basin strength) is a loss**: on these easy tasks the shared basin already classifies well, so the figure shows the trajectory adds ≈nothing on top of the basin — reading as "the method contributes nothing."
4. The cryptographic cost story (communication, computation, comparison to prior HE-FL) is under-developed for a venue that will scrutinize it.
5. There is no explicit argument for **why fine-tuning a pretrained model is the right setting** — which is precisely what the HE constraints force.

## Solution

Refactor the paper to **HE-IFD: one-shot federated fine-tuning of pretrained models under multiparty CKKS, from a shared loss basin**, and extend the evidence to **harder tasks where a frozen backbone is not already linear-probe-solvable**, so fine-tuning does real work and the per-client benefit is visible.

**The thesis spine (the argument the HE constraints hand us):**

1. **HE has no programmability.** The server computes on obfuscated ciphertexts: it cannot branch on a value, cannot run data-dependent control flow, cannot adapt its computation to the data. It can only evaluate a *fixed, low-depth arithmetic circuit*. The only honest server operation is therefore a depth-1 linear combine.
2. **So the learning must happen client-side, in plaintext**, and the server does nothing but a sample-weighted sum.
3. **A linear sum of independently-trained models only lands in a usable model if they share a loss basin.** A *frozen pretrained backbone* plus a shared adapter/head initialization *is* that basin — essentially for free.
4. **From-scratch cannot supply this** (no common frame; different inits diverge; recovering it needs the multi-round or server-side compute HE cannot afford). **Fine-tuning a pretrained model is therefore not a convenience but a consequence of HE's limits — and it is exactly where the method shines.**

**The method, post-decisions:**

- **Trainable unit:** **LoRA adapters (+ classifier head)** on a frozen pretrained backbone. Few parameters → few ciphertexts → still multiplicative depth 1. (Head-only and last-N blocks are reported as a trainable-unit comparison.)
- **Local step (headline):** each client **directly fine-tunes** the LoRA+head on its local data, for a **bounded K-step trajectory** starting from the shared basin `θ₀`, and produces the **cumulative displacement `Δᵢ = θᵢ⁽ᴷ⁾ − θ₀`**. (Teacher→student **distillation is retained as a labeled ablation**, not the headline.)
- **Server step (the only crypto op):** the depth-1 sample-weighted linear combine `θ⋆(λ) = θ₀ + λ·Σᵢ wᵢ·Δᵢ` under the joint CKKS key — **task arithmetic** on fine-tuning deltas, with `λ` the drift-regularizing scaling coefficient. A threshold of clients jointly decrypts. One upload, one download.
- **Shared basin `θ₀`:** the frozen backbone supplies it; the adapter/head init is aligned over P2P secure channels from per-class prototypes (raw or under averaging-variant DP).

## User Stories

Actors: **Researcher**, **AFK agent**, **Client**, **Server**, **Reviewer**.

**Method + code**
1. As a Researcher, I want a **direct fine-tuning** trajectory (LoRA+head on local hard labels from `θ₀`) as the headline local step, so the method matches a "federated fine-tuning" title.
2. As a Researcher, I want **LoRA adapters** as a first-class trainable unit alongside the head, aggregated by the same depth-1 linear combine, so I can credibly call it fine-tuning while staying HE-cheap.
3. As a Researcher, I want **distillation kept as a switchable ablation**, so I can test whether soft-label regularization helps on hard tasks without it being the headline.
4. As a Researcher, I want the LoRA/head displacement to flow through the *unchanged* `aggregate` (task arithmetic, depth-1), so the crypto story is identical to the pre-pivot one.

**Harder datasets**
5. As a Researcher, I want **fine-grained vision** tasks (CUB-200, Stanford Cars, FGVC-Aircraft) where a frozen ViT-B/32 is *not* already linear-probe-solvable, so fine-tuning shows real lift.
6. As a Researcher, I want **large-label / domain-shift vision** (Tiny-ImageNet / iNaturalist / DomainNet), so the large-label and feature-skew regimes are covered.
7. As a Researcher, I want **harder many-class text** (Banking77, DBpedia-14, 20-Newsgroups, TREC), so the text side leaves real headroom.
8. As a Researcher, I want a **couple of tries** at additional backbones (CLIP / DINOv2 vision, E5 / BGE text), low-priority, to show breadth if they train well.

**Experiments + figures**
9. As a Researcher, I want every headline cell over **N ∈ {5,10,20,50}, α ∈ {0.01,0.05,0.1,0.3,1.0}, 3 seeds {42,43,44}**, reporting global acc ± std, standalone `θ₀` acc, the **fine-tuning lift** (acc − θ₀), and locally-unseen-class coverage.
10. As a Researcher, I want the **distillation-lift figure rebuilt on the hard tasks**, where the lift is real, so the figure demonstrates contribution rather than its absence.
11. As a Researcher, I want a **trainable-unit comparison** (head / LoRA / last-N) on a hard task, showing the accuracy↔ciphertext trade-off.
12. As a Researcher, I want a **reduced from-scratch section** (secondary), so the backbone-free baseline is present but not the headline.

**Crypto cost + writing**
13. As a Researcher, I want a **comprehensive CKKS communication/computation section** with measured DKG/encrypt/aggregate/decrypt timing, ciphertext counts and bytes across N and head sizes (incl. the LoRA parameter budget), and a like-for-like comparison to prior HE-FL.
14. As a Researcher, I want a **"why fine-tuning, not from-scratch" section** built on the no-programmability + shared-basin-necessity argument.
15. As a Reviewer, I want the privacy account (attack surface + leak minimization, MIA) carried forward and re-stated for the fine-tuning setting.

**Operational (the sleep constraint)**
16. As a Researcher, I want each experiment notebook to be **start-once**: a single configuration cell asks for *every* choice up front, then the notebook runs the whole grid unattended to completion (resumable), so I can start it and sleep.

## Implementation Decisions

**Method.** Direct fine-tuning headline + distillation ablation (decision 2026-06-01). Trainable unit = LoRA(+head); the aggregate (`src/aggregate.py`, depth-1 task arithmetic) is **untouched** — only the local-step path and the trainable-parameter set change. `λ` (scaling coefficient) is the regularizer (carry forward issue-026 work).

**Backbones.** Core: ViT-B/32 (vision), RoBERTa-base + MPNet (text). Optional ("couple of tries"): CLIP / DINOv2, E5 / BGE.

**Datasets.** Fine-grained vision {CUB-200, Stanford Cars, FGVC-Aircraft}; large-label/domain-shift {Tiny-ImageNet or DomainNet}; harder text {Banking77, DBpedia-14, 20-Newsgroups, TREC}. Reduced from-scratch {MNIST/FMNIST} kept secondary.

**Axes.** N ∈ {5,10,20,50}; α ∈ {0.01,0.05,0.1,0.3,1.0}; K-sweep; λ-sweep; alignment {no-Phase0, raw, DP-ε∈{0.5,2,8,32}}; trainable-unit {head, LoRA, last-N}; 3 seeds {42,43,44}.

**Carry-forward (do NOT redo).** FHE PoC (Lattigo, depth-1, validated + the measured cost sweep — already landed); MIA suite (021/028, leak-minimization framing); λ regularizer (026); DP-MERF DP-soundness fix (027, with the "not a competitive basin source" verdict). These transfer unchanged; the LoRA parameter count only changes the **ciphertext budget** in the cost section, not the protocol.

**Notebook framework.** All experiment notebooks follow one pattern: **one config cell (ipywidgets / a single prompt block) collecting every choice**, then a **run-all** that builds the grid and executes it autonomously, **resumable** (skip completed cells), writing per-cell JSON + a combined table under `results/<case>/`, logging and continuing past per-cell errors. Designed for Colab (clone/pull repo, pip deps, login-node-style prefetch, then config + run). No interaction after the config cell.

## Testing Decisions

- **`aggregate`** unchanged → existing depth-1/task-arithmetic invariants still hold (telescoping, PT×CT + CT+CT only). Add a test that LoRA+head displacements aggregate identically to a head-only displacement of the same flattened length.
- **LoRA path**: a regression asserting the LoRA-fine-tuned model's IID accuracy exceeds the linear-probe (head-only) baseline on a hard task (i.e. LoRA actually fine-tunes).
- **Dataset loaders**: Dirichlet partition seed-reproducible; public probe disjoint from client data; feature cache hits offline.
- **Integration gate**: the start-once notebook reproduces a single sanity cell's number before the full grid runs.

## Out of Scope (this paper)

- Fine-tuning the *full* backbone (breaks the ciphertext budget; LoRA/last-N is the boundary).
- Multi-round protocols of any kind (the one-shot + depth-1 constraint is the thesis).
- Backbones beyond the "couple of tries" if they fail to train well.
- Malicious/Byzantine robustness beyond one future-work paragraph.

## Further Notes

- The pivot strengthens the paper: the HE-no-programmability argument *derives* the design rather than defending it.
- Figure 4's fate is empirical: on hard tasks the fine-tuning lift should be real; if a task still shows ≈0 lift, that task is too easy and is dropped, not reframed.
- Previous planning state (distillation-era PRD + issues 001–028) is at `docs/archive/pre-finetuning-pivot/` for provenance.
