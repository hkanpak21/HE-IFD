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
