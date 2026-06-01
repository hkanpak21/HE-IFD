# PRD — HE-IFD → IEEE TNSE resubmission

**Status:** needs-triage
**Created:** 2026-05-27
**Source of truth:** `results/colab_results/results_notebook.ipynb` (the observed results). `results/colab_results/methodology.md` is directionally correct but theoretically loose and will be rewritten to match the code. `src/v1`, `src/v2`, and `FL_TDSC/*` are deprecated/archived.
**Origin:** distilled from a grill-me session (2026-05-27). Prior submission "FedDil / HE-IFD" rejected from IEEE TDSC SI (TDSCSI-2026-04-1278); rejection reviews in `REJECTED_PAPER/`.

---

## Problem Statement

I have a privacy-preserving one-shot federated distillation paper that was **rejected from IEEE TDSC**, and since then I have **changed the methodology** — verified by a set of Colab experiments whose results I trust. The old paper sources (`FL_TDSC/`) and the old code (`src/v1`, `src/v2`) describe protocols I no longer use (encrypted intermediate-feature distillation, polynomial activations, server-side encrypted SGD, ~460 GB uploads). The current method lives only in a monolithic Colab notebook plus a loosely-written `methodology.md`.

I need to:
1. Reconcile the paper to the *current* method and resubmit to **IEEE TNSE** (a different venue, but a shared reviewer pool — so the same concerns will recur).
2. Close the rejection-level gaps the TDSC reviewers raised: **no comparators, no end-to-end CKKS cost measurement, no post-release MIA, weak scalability story, unjustified participation incentive, poor structure.**
3. Do this without wasting compute: the notebook is a monolith (it hid a silent GPT-2 feature-extraction bug that pinned every GPT-2 cell at chance), the code is duplicated across `v1`/`v2`, and experiments retrain teachers redundantly.

The work must produce **rooted, defensible numbers** — accuracy, communication, wall-clock, and privacy — not just a narrative.

## Solution

A **single flat, intuitive `src/` package** consolidated from the authoritative notebook, plus an **ordered experimental program** that produces the headline numbers first, roots them under real FHE and attack, and rewrites the paper to match.

The method, stated faithfully: each client locally distils its own teacher into a student over a **bounded K-step trajectory starting from a shared, Phase-0-aligned initialization `θ₀`**, and uploads the **cumulative trainable-parameter displacement `Δᵢ = θᵢ⁽ᴷ⁾ − θ₀`** encrypted under a **multiparty CKKS** key. The server's *only* cryptographic operation is the **sample-weighted linear combination `θ₀ + Σᵢ wᵢ·Δᵢ`** (plaintext-scalar × ciphertext + ciphertext + ciphertext, multiplicative depth ≈ 1), after which a threshold of clients jointly decrypts the final student. One upload, one download.

Two properties carry the paper:
- **FHE-friendliness:** because the server step is purely linear, the student can use any architecture (ReLU/GELU/softmax) with no polynomial-activation approximation and no depth-budget juggling — the redesign that eliminates the prior paper's central weaknesses.
- **Basin coherence:** because every client departs from the same `θ₀`, moves only a bounded distance, and was pulled toward a shared target by Phase 0, the single linear combine lands inside one loss basin. Naive averaging of independently-converged / full-fine-tuned / different-init students diverges — which is why the bounded-from-aligned-init structure is necessary, not cosmetic.

Privacy is a three-layer stack: **cryptographic** (server-side, lossless — the CKKS aggregate equals the plaintext result up to ~1e-3 noise) + **differential privacy** on the Phase 0 prototypes (the only signal released in clear, via an averaging-variant accounting) + **measured residual leakage** on the released student (MIA). The headline comparison is against **DP one-shot FL** (lossy privacy) and prior **HE-FL** (multi-round, expensive): HE-IFD sits at plaintext accuracy with cryptographic server-side privacy, at a fraction of prior HE-FL's communication and leakage.

## User Stories

Actors: **Researcher** (the author), **AFK agent** (autonomous compute orchestrator), **Client**, **Server**, **Reviewer** (as an evaluation lens).

**Code consolidation & correctness**
1. As a Researcher, I want a single flat `src/` package consolidated from the notebook, so that the code stack is intuitive and I never again chase a bug across `v1`/`v2`/notebook copies.
2. As a Researcher, I want the consolidated package to reproduce the colab numbers within seed noise, so that I can trust it as the new source of truth and archive the notebook.
3. As a Researcher, I want the GPT-2 feature extractor fixed (left-pad + last-token pooling instead of mean-pool over a causal sequence), so that GPT-2 cells stop sitting at chance and reflect the backbone's real capability.
4. As a Researcher, I want a regression test asserting GPT-2 yields non-trivial IID accuracy, so that a silent feature-extraction bug can never recur unnoticed.
5. As a Researcher, I want sample-weighted aggregation (`wᵢ = nᵢ/Σnⱼ`) used everywhere, so that the code matches the notebook and methodology rather than `src/v1`'s uniform `1/N`.
6. As a Researcher, I want `src/v1`, `src/v2`, and `FL_TDSC/` archived (not deleted), so that provenance is preserved without polluting the working stack.

**Teacher caching & experiment fusion**
7. As an AFK agent, I want a seed-keyed teacher cache on disk, so that a teacher trained for one cell is reused by every other cell that needs it instead of being retrained.
8. As a Researcher, I want experiments combined intelligently (shared teachers, shared feature caches, shared partitions across methods at fixed seed/α/N), so that the sweep cost is dominated by genuinely new work.

**Phase 0 alignment**
9. As a Client, I want to compute per-class feature prototypes and exchange them over P2P secure channels, so that the server never sees them and alignment happens strictly among clients.
10. As a Client, I want to optionally release prototypes under averaging-variant DP, so that the in-clear signal carries a calibrated (ε, δ) guarantee.
11. As a Researcher, I want to report a **no-alignment baseline** and the **standalone test accuracy of the initial student `θ₀`** that clients receive, so that I can separate what alignment contributes *before* distillation from what the K-step trajectory adds.
12. As a Researcher, I want to compare alignment strategies {no-Phase0, raw-prototype, DP-averaged at ε ∈ {0.5, 2, 8, 32}} × Kpc, so that the alignment-value-vs-(feature-weakness × heterogeneity) story is empirical.
13. As a Researcher, I want the centralized-coordinator vs each-client-builds-its-own alignment variants documented as equivalent (same attack surface), so that the protocol description is honest about the design latitude.

**Local distillation & aggregation**
14. As a Client, I want to distil my teacher into a student over a bounded K-step trajectory from `θ₀` and upload the cumulative displacement, so that my contribution stays in-basin and is one ciphertext-set, not K.
15. As a Researcher, I want **K treated as a swept hyperparameter**, so that I learn whether longer trajectories help or saturate rather than assuming K=300.
16. As a Server, I want to compute only `θ₀ + Σᵢ wᵢ·Δᵢ`, so that my operation is linear, FHE-compatible, and reveals nothing beyond the final aggregate.
17. As a Researcher, I want an **aggregation-coherence ablation** (bounded-from-aligned-init vs naive averaging of diverged/full-FT/different-init students), so that I can show *why* the design works and preempt the "isn't this just FedAvg-averaging?" reflex.

**Headline accuracy grid**
18. As a Researcher, I want from-scratch results on {MNIST, FMNIST, CIFAR-10} with small nets (MLP/LeNet-5/CNN-5), so that I have a fair, backbone-free comparison that isolates the protocol's contribution.
19. As a Researcher, I want pretrained-backbone results on {ViT-B/32, ResNet-18} for CIFAR-10 and {DistilBERT, GPT-2} for AG News, so that I demonstrate the intended deployment across vision and text.
20. As a Researcher, I want the grid swept over N ∈ {10, 20} (DP-peer comparison anchors) plus {5, 50} (scalability), so that I am comparable to prior work and answer the large-N degradation concern.
21. As a Researcher, I want α ∈ {0.01, 0.05, 0.1, 0.3, 1.0}, so that I overlap the extreme-non-IID cells DP peers report (α=0.01) and span to IID.
22. As a Researcher, I want every cell replicated across 3 seeds with mean ± std, so that results are statistically legible.

**Evaluation metrics**
23. As a Researcher, I want IID test accuracy as the lead metric, so that I am directly comparable to every prior method.
24. As a Researcher, I want **M3: per-client teacher-vs-aggregate gap** (accuracy of the global student on client i's distribution minus client i's own teacher), so that I empirically justify the participation incentive the reviewers said was unsupported.
25. As a Researcher, I want **M4: OOD-class accuracy at low α** (accuracy on classes a client held zero local examples of), so that I demonstrate the "averaged all-label student handles out-of-distribution samples the local teacher never saw" value proposition.
26. As a Researcher, I want mean/best/oracle teacher references reported per cell, so that the comparison context is complete.

**Reporting**
27. As a Researcher, I want every experiment written under the `results/<case>/` convention (3-sentence README + auto-populated table, long-form `results.csv`, `partition_diagnostic.jsonl`, per-cell JSONs, `runs/` logs), so that results are uniform and auditable.
28. As an AFK agent, I want sweeps to be resumable (skip already-completed cells), so that a preempted Slurm job resumes instead of restarting.

**Real-FHE rooting (M2)**
29. As a Researcher, I want one end-to-end multiparty CKKS run in Lattigo on the MLP (DKG → encrypt → aggregate → threshold-decrypt), so that the protocol is demonstrated end-to-end at least once.
30. As a Researcher, I want the decrypted aggregate to match the plaintext aggregate to ≤ ~1e-3 relative L2 error, so that the entire plaintext simulation is validated as the encrypted result for accuracy purposes.
31. As a Researcher, I want measured client-side encryption time, ciphertext count and bytes per client, total upload, server aggregation time, threshold-decryption time, peak memory, and multiplicative depth, so that I precisely answer the cost questions (and replace the old 460 GB figure with a real number).

**Post-release MIA (M2)**
32. As a Researcher, I want an MIA attack chosen from prior work suited to this setting (aggregate one-shot student + prototype exchange), so that the privacy evaluation is principled rather than a generic bolt-on.
33. As a Researcher, I want MIA evaluated on three surfaces — prototype-distance (fellow client during Phase 0), external-LiRA (on the released student), fellow-client combined — across N × α, so that I characterize residual leakage against every adversary the threat model admits.
34. As a Researcher, I want to show the server cannot run a per-client MIA by construction (it sees only ciphertext + the aggregate), so that the cryptographic guarantee is contrasted against the residual output leakage.

**Paper (M3, HITL)**
35. As a Researcher, I want methodology and experiments rewritten from the notebook reality (bounded trajectory aggregation, not "encrypt final weights"), so that the paper matches the code and survives a reviewer's telescoping check.
36. As a Researcher, I want the TDSC structural complaints fixed (motivation moved into the intro, challenges↔contributions aligned, a clearer overview figure, future-work relocated), so that the readability objections do not recur.
37. As a Researcher, I want a comparator table built gradually during writing, citing prior numbers verbatim from `comparators/REPORTED_RESULTS.md` and placing HE-IFD on matched setups, so that the "no direct comparison" objection is closed.
38. As a Reviewer, I want a one-paragraph treatment of malicious/colluding clients pointing to robust-aggregation-under-HE as future work, so that the scope boundary is explicit.

## Implementation Decisions

**Package shape.** One flat Python package directly under `src/` (no `v1`/`v2`). Modules: `data`, `backbones`, `teacher`, `phase0`, `distill`, `aggregate`, `evaluate`, `protocol`, `sweep`, `report`. The real-FHE validation lives in a separate `fhe/` (Lattigo, Go); the attack suite in `mia` (added in M2). Old `src/v1`, `src/v2`, `FL_TDSC/` move to an archive location.

**Deep-module interfaces (stable, hide complexity):**
- `aggregate(theta0, deltas, weights) → theta` — the only server operation; encapsulates the FHE-compatibility invariant (operations restricted to PT×CT and CT+CT; depth ≈ 1) and is where the basin-coherence-vs-naive-average ablation is exercised.
- `phase0.build_probe(...)` — returns the alignment probe / θ₀ for a chosen strategy; encapsulates the averaging-variant DP accounting (sensitivity = clip/Kpc, σ = sensitivity·√(2 ln(1.25/δ))/ε).
- `distill.local_distill_trajectory(...)` — runs the bounded K-step KL distillation and returns the cumulative displacement `Δ = θ_final − θ₀`.
- `protocol.run_cell(...)` — composes the above into one (dataset, backbone, N, α, K, method, seed) → CellResult.

**Method decisions.**
- The transmitted/encrypted object is the **cumulative displacement** `Δᵢ`, not absolute final weights and not the K per-step deltas — the K-step trajectory is *how* `Δᵢ` is generated; collapsing it for transport is valid only because the server step is linear, and the paper says so explicitly.
- Aggregation is **sample-weighted** (`wᵢ = nᵢ/Σnⱼ`).
- **K is a swept hyperparameter.**
- Crypto stack: **multiparty CKKS with DKG + threshold decryption** (no single party, server included, can decrypt). Phase 0 uses **T1 transport** (P2P secure channels; server excluded).
- Real FHE realized in **Lattigo** for one MLP cell; any mature CKKS library (incl. GPU-backed) is acceptable if Lattigo proves awkward — the goal is a single faithful end-to-end demonstration, not production crypto.

**Comparator framing.** Primary peer group = **DP one-shot FL** (FedAUXfdp, FedDiff, FedKT): lossless crypto vs lossy DP. Crypto-cost anchor = **POSEIDON** plus a recent HE-FL work (selection is a research task). Plaintext one-shot (DENSE, Co-Boosting, FuseFL) = ceiling reference only, no head-to-head. All baseline numbers cited verbatim from `comparators/REPORTED_RESULTS.md`; HE-IFD is run on matched setups.

**Operational.** All compute via `sbatch` on VALAR; never run training/FHE python on the login node. Conda env `he_ofl`. Large model weights pre-fetched on the **login node** into the HF/torch cache (compute nodes have slow/no internet); datasets already cached, `download=False`. Reporting follows `results/<case>/`. Work split: **paper writing is HITL** (with the researcher); **all compute — sweeps, FHE, MIA — is AFK** (agent-driven, researcher reviews outputs).

**Sequencing gate.** M1 (foundation + headline) runs to completion and **stops for researcher review** before M2 (rooting) begins, so that downstream FHE/MIA/comparator work is never built on headline numbers that might still shift.

## Testing Decisions

Tests verify **external behavior through public interfaces**, never internals. The repo currently has no test suite for the simulation code, so this PRD establishes the convention.

**Isolated unit tests (written now):**
- **`aggregate`** — (a) the FHE-compatibility invariant: the aggregation result equals a sample-weighted average of finals (telescoping property) and uses only additive/scalar-multiplicative operations; (b) basin-coherence: bounded-from-shared-init deltas aggregate to a usable model whereas a constructed divergent set (different inits) does not. This is the cryptographic-correctness guarantee, so it gets the most coverage.
- **`phase0`** — DP accounting: sensitivity = clip/Kpc; σ matches the Gaussian-mechanism formula for given (ε, δ); ε=∞ yields zero noise; prototype shapes/counts are correct when some clients lack a class.
- **`backbones`** — feature-extraction regression: GPT-2 with left-pad + last-token pooling yields **non-trivial** IID accuracy on a tiny AG-News subset (guards against the mean-pool bug returning); DistilBERT pooling unaffected.

**Lighter assertion:**
- **`data`** — Dirichlet partition is seed-reproducible and the public probe is disjoint from client training data.

**Integration gate (not a unit test):** the consolidated `sweep` reproduces the colab headline numbers within seed noise. This is the acceptance criterion for declaring the package the new source of truth.

Prior art: none in-repo for the simulation; the `results/<case>/` JSON schema and `partition_diagnostic.jsonl` serve as golden references for integration comparison.

## Out of Scope

- **M2 and M3 at full resolution.** They are sketched here but deliberately under-specified; they are re-planned after the M1 review gate, because headline numbers may shift the design.
- **Parked method extensions:** synthetic-data Phase 0 alignment; no-probe DP-common-basin alignment; a fully data-free HE-IFD variant; per-step DP noise / per-step reweighting (the non-linear server hook that would make the K-step series genuinely order-dependent and non-collapsible). All documented as future work, none built now.
- **Malicious / colluding / Byzantine clients** beyond a single future-work paragraph and a pointer to robust-aggregation-under-HE. No robust-aggregation implementation.
- **Production-grade cryptography.** The Lattigo run is a one-shot correctness + cost demonstration, not a hardened deployment; no second implementation or PoC duplication.
- **Re-running comparator code.** Baselines are cited from published numbers; their brittle vendored implementations are not re-executed.
- **SVHN / CIFAR-100 / Tiny-ImageNet breadth** for from-scratch comparison — noted as a straightforward extension, not required for the submission.

## Further Notes

- **Rejection scorecard (TDSC → addressed):** polynomial activations (R1-W2) and ~460 GB upload (R1-W3) are *killed by the pivot*. Comparators (R2-1/R3-5), end-to-end CKKS cost (R2-2/R2-3), post-release MIA (R2-5/R1-W4), scalability/large-N (R1-W1, via N-sweep + basin framing), participation incentive (R3-1, via M3), structure/figures (R3-3/4/6, in the rewrite), and malicious clients (R2-4, via a future-work paragraph) are all addressed by this program.
- **Venue:** IEEE TNSE (was TDSC SI). Shared reviewer pool — treat every TDSC concern as live.
- **Naming/archive convention:** no `v1`/`v2`/`Mode-A` proliferation. When the submission's milestones are met or deferred, the current state is archived and the next state (e.g., the privacy follow-up paper: synthetic Phase 0 + DP-synthetic + MIA depth + malicious-client robustness) is switched on.
- **Honest caveat to preserve in the paper:** cryptographic privacy protects the server-side *computation*; DP protects the released *output*. They are complementary, which is precisely why Phase 0 prototypes are DP-protected and the released student's residual leakage is measured by MIA. The comparison to DP one-shot FL is on the utility axis (lossless vs lossy privacy), stated with this caveat explicit.

---

## Phase II — M1.5 + Extensions (appended 2026-05-28, post M1 review gate)

### Position assessment at the M1 review

M1 produced **1800 cells, 0 failures**, but defensibility across settings is uneven:
- ✅ **Strong**: from-scratch MNIST/MLP — clean wins across every baseline; scales smoothly with N.
- ⚠️ **Saturated**: ViT-B/32 / CIFAR-10 (0.97 IID = no headroom; alignment-vs-distill contribution can't be measured).
- ❌ **Bad at low α**: ResNet-18 / CIFAR-10 — raw_union 0.48 vs θ₀ 0.74 (distillation *degrades* the warmed init by 26pp).
- ⚠️ **Middling**: DistilBERT / AG-News — edges θ₀/no_phase0 by ~3pp at α=0.05; near-oracle at IID.
- ⏸️ **Deferred**: GPT-2 — residual weakness deferred to future work per issue 002.

**This is not yet a publishable position for the pretrained-backbone deployment story.** It is publishable for the from-scratch MLP/MNIST story. M1.5 fixes the pretrained regime + completes the from-scratch matrix before any paper writing begins.

### Methodology framing locked at this review

> *"Given a set of clients with a shared-basin initial model, produce a combined model by distillation, with HE guarantees on the updates and the data."*

Trainable-layer-scope adjustments (head-only ↔ LoRA-on-last-blocks ↔ last-N-blocks fine-tuning) are acceptable **as long as the server aggregation stays linear** (PT×CT + CT+CT only). More trainable params → more ciphertexts per client; multiplicative depth stays ≈1.

### N grid

Phase II grids use **N ∈ {1, 5, 10, 20, 50}**. N=1 = degenerate single-client baseline (raw_union should ≈ θ₀); useful as a sanity floor.

### Phase α — debug what's broken (highest priority)

- **Issue 010** — KD hyperparams on resnet18/α=0.05 (K, τ, λ, LR) + the 003 pytest re-run.
- **Issue 011** — Trainable-layer scope (head ↔ LoRA ↔ last-N blocks). The methodology lever. Also fixes CNN-5/CIFAR-10 under-training.
- **Issue 012** — Harder vision dataset (CIFAR-100 / Tiny-ImageNet) for ViT — addresses CIFAR-10 saturation.
- **Issue 013** — KD dynamics diagnostic — empirical-evidence anchor for the basin-cancellation hypothesis.

### Phase β — complete the from-scratch matrix

- **Issue 014** — LeNet/FMNIST full grid + N=1 extension on all from-scratch + CNN-5/CIFAR-10 full grid (after 011).
- **Issue 015** — DP-ε frontier sweep (ε ∈ {0.5, 2, 8, 32, ∞} + Kpc ∈ {1, 5, 20}) across the 3 from-scratch datasets.

### Phase γ — alignment-strategy expansion

- **Issue 016** — Synthetic-sample alignment (per-client small generator → synthetic samples instead of mean prototypes).
- **Issue 017** — No-probe DP-common-basin (fully-DP, no labelled public data — warmup on the noisy prototype set itself).

### Phase δ — scale to bigger models (only after α/β/γ stabilize)

- **Issue 018** — Bigger pretrained backbones (ViT-L, BERT-large, GPT-2-medium) with **mandatory sanity-check gating** + HITL touchpoint before protocol application.

### Phase ε — M2 (Real-FHE + MIA, deferred until α + β land)

Original M2 plan (Lattigo + MIA suite — see existing User Stories 29–34) — to be **re-grilled** once Phase α + β results are in, because the methodology may shift (e.g. LoRA-on-last-blocks would change the ciphertext budget to validate).

### Fallback path if Phase α fails to fix ResNet-18

If issues 010 + 011 *both* fail to close the θ₀→final gap on ResNet-18 at α=0.05:
- (a) **Do NOT** drop ResNet-18 from the headline set as a first move.
- (b) **Do NOT** reframe the paper away from bounded-trajectory aggregation (rejected by the user at the M1 review).
- (c) **DO** spawn a third-round debugging issue informed by issue 013's diagnostic findings.

### Updated AFK/HITL split

All Phase II issues are **AFK** by default with **HITL review touchpoints** at:
- 011 (methodology-shaping — user reviews trainable-scope comparison before locking the new default).
- 018 (sanity-check stage results need user review before authorising big-backbone protocol runs).

Paper writing remains HITL with the user; everything else AFK. **Paper writing does NOT begin until all of Phase α + β land** — locked at the M1 review.

### Defensibility criteria (the bar we hold the protocol to)

For each (backbone, dataset) cell in the final headline set:
- `raw_union > no_phase0` (alignment helps).
- `raw_union ≥ θ₀` in *most* regimes (distillation does not actively hurt the aligned init).
- `raw_union → oracle` as α → 1.0 (recovers centralised training at IID).
- `M4 > 0` at low α (federation provides OOD value to clients).

Any setting that fails *raw_union ≥ θ₀* at α=0.05 must be fixed by Phase α, or that setting drops from the headline (per the fallback path).

---

## Phase III — Post-MIA three-thread grill (appended 2026-05-30)

### Position at this grill

M1.5 landed; M2 rooting is underway. **FHE PoC (020) ✅** (end-to-end multiparty CKKS, decrypted == plaintext within CKKS bounds, cost a few MiB/round — replaces the rejected 460 GB figure). **MIA (021) ✅ on MNIST.** Aggregation-design probes (023/024/025) reached a verdict. A grill consolidated the three remaining experimental threads — **aggregation, MIA, synthetic generation** — into four decisions.

### Thread 1 — Aggregation is *task arithmetic* (framing lock + one cheap verify)

The server op θ⋆ = θ₀ + Σⱼ wⱼ·Δⱼ (Δⱼ = θⱼ⁽ᴷ⁾ − θ₀) **is task arithmetic** (Ilharco et al. 2023, `ilharco2023editing`) — task vectors merged from a shared init. This is the dominant model-merging framework, not a naive trick; it answers the "isn't this too simple?" reflex by *naming* it.

- **Non-linear verdict (settled).** The 408-row local probe (023/024) + a 6-cell VALAR verify (025) agree: **no one-shot non-linear combine beats the depth-1 weighted average.** `second_moment`/RMSProp loses on paired (within-partition) comparison; the only thing that wins is multi-round `sync_sgd`, which breaks one-shot. The full 960-cell grid is **not needed**. (The earlier "+22 RMSProp win" was a non-reproducible single-run artifact — the Dirichlet-partition lottery alone moves accuracy up to ~15pp.)
- **Why the deep merges lose — the citable defense.** TIES (Yadav 2023, `yadav2023ties`) sign-election and FedFisher (Jhunjhunwala et al. 2024, `jhunjhunwala2024fedfisher`) curvature-weighting help only when task vectors **conflict**; the merging literature reports diminishing returns when deltas are well-aligned. **Our shared basin θ₀ pre-aligns the deltas, so these merges have no conflict to resolve while still costing deep HE.** Same mechanism as the "basin is the lever" headline. Momentum/curvature therefore live **client-side**, in the bounded local trajectory (already SGD+momentum, `distill.py`), not at the encrypted server step.
- **The one HE-legal optimization lever = the scaling coefficient λ.** θ⋆(λ) = θ₀ + λ·Σⱼ wⱼ·Δⱼ (we pin λ=1). It collapses to an interpolation θ⋆(λ) = (1−λ)θ₀ + λθ⋆(1), so it is **eval-only, no retraining**, and λ stays a public scalar → depth-1. MetaGPT (Zhou 2024, `zhou2024metagpt`) even solves λ in closed form from task-vector geometry. **Decision: verify λ cheaply first (issue 026)** before committing any grid; a peak at λ<1 reinforces "alignment does most of the work," λ>1 means push harder along the trajectory.

### Thread 2 — MIA: extend to a second backbone family (issue 028)

021 landed clean on MNIST: **released θ⋆ near-chance** (AUC 0.49–0.57 across Yeom/LiRA/GLiRA × external/fellow); **prototype channel** leaks raw (AUC→0.80 @ α=1.0) but **DP ε≤8 → chance** (validates the averaging-variant accounting). The dual story (crypto protects the model; DP collapses the only leaky channel) is publishable. **Decision: cover a pretrained backbone in *both* modalities** — ViT/CIFAR-100 (wrapper exists) + RoBERTa/AG-News (write a wrapper; chunk 64-shadow training ≤3h).

### Thread 3 — Synthetic generation: fix DP-MERF, keep both modes (issue 027 → re-run 022)

The 022 generator is **not differentially private**: it emits raw records + cosmetic jitter, with DP noise only on the φ-mean that sets resampling weights. The verify's inverted contrast (Mode A `dp_synth_all` 0.97 @ ε=2 > Mode B basin) is therefore an **artifact of the DP not biting**, not a finding. **Decision: keep both modes and fix the generator properly (DP-MERF, Harder 2021)** — train a small generator to match the DP-privatized RFF mean embedding and **sample fresh points, never raw `X_c`**; re-verify (Mode A accuracy must *drop* at ε=2) before re-running the grid. Our basin lives in frozen-backbone feature space, so DP-MERF there is already "perceptual" — its strongest regime.

### Cross-thread payoff

Once the DP generator is sound, **Mode A becomes our own measured DP-one-shot baseline**, and its released-model MIA contrasts directly against HE-IFD's near-chance leakage — the **"crypto leaks less than DP"** claim, the strongest privacy statement in the paper, tying threads 2 and 3 together. The λ result ties thread 1 to the "alignment does most of the work" headline.

### Issues cut at this grill

- **026** — task-arithmetic λ-coefficient cheap verify (eval-only) [AFK].
- **027** — fix the DP-MERF generator to be DP-sound + re-verify; supersedes 022's generator [AFK].
- **028** — MIA second backbone family (ViT/CIFAR-100 + RoBERTa/AG-News); extends 021 [AFK].

All AFK (compute); paper writing remains HITL. New bib keys to add when writing: `ilharco2023editing`, `yadav2023ties`, `jhunjhunwala2024fedfisher`, `zhou2024metagpt` (DP-MERF `harder2021dpmerf` already planned).
