# Cover letter — HE-IFD TDSC resubmission (draft)

**Date:** 2026-05-17 (draft, weeks-20–21 finalisation target)
**Source materials:** action plan §0.2 retired-concerns table; PRD `reports/2026-05-05_methodology_pivot.md`; linear-accumulator clarification (user 2026-05-17); rejection letter TDSCSI-2026-04-1278 (2026-05-08); CHANGES.md before/after edits.
**Status:** structural draft, not the final wording. Numbers and exact claims are placeholders until A4.1 lands (per A10 §numbers freeze + replacement protocol). Voice match required against `methodology.tex:21` register before submit (per [Paper voice](memory)).

> *Note on the rejected version.* This cover letter references the manuscript at `reports/archive/PAPER_OLD.pdf` (the TDSCSI-2026-04-1278 submission) as "the rejected version" or "the previous version." All retired claims and obsolete numbers below describe that document, not the resubmission. The resubmission's methodology is the protocol described in PRD `reports/2026-05-05_methodology_pivot.md` with the linear-accumulator refinement of 2026-05-17.

---

## Section 1 — Opening, scope of revision, AE-invitation acknowledgement

To the Associate Editor and the Editorial Board of IEEE TDSC,

We thank the Associate Editor and the three reviewers for the careful read of TDSCSI-2026-04-1278 and for the explicit invitation to resubmit subject to substantial revisions. We have respected the six-month minimum window (rejection 2026-05-08 → resubmission 2026-11-XX) and used the intervening period for a substantive protocol redesign rather than a cosmetic revision. The work submitted here is best read as a **structurally different protocol that retains the HE-IFD acronym** for continuity but answers most of the reviewers' technical concerns at the *design* level rather than at the *exposition* level.

The remainder of this letter is organised in three parts:
- **Part A (this letter, §2):** A "what changed since the rejected version" mapping table. We urge the AE pool to read this first; many specific concerns the previous reviewers raised describe a protocol that this resubmission no longer implements.
- **Part B (this letter, §3–§5):** A per-reviewer, per-tag point-by-point response to every numbered concern from R1, R2, R3, and the AE summary.
- **Part C (companion document, `response_document.pdf`):** A more detailed point-by-point response keyed to the manuscript's revised section numbers, with line-level citations to where each change has landed.

---

## Section 2 — What changed since the rejected version

The single most consequential change is the **methodology pivot from block-wise HE-IFD to one-shot encrypted Collaborative Federated Distillation (CFD) on a probe**, with the encrypted state recast as a *linear accumulator* over encrypted teacher-induced gradient contributions rather than a full forward+backward chain through encrypted weights.

The table below maps the concerns raised by the rejected version's reviewers to their status in the resubmission. Entries marked **retired** describe a property of the rejected protocol that this resubmission no longer has; entries marked **addressed** describe a concern that still applies and that the resubmission answers with new work; entries marked **out-of-scope** describe a concern we have explicitly bounded as outside the contribution.

| # | Concern (rejected version) | Status in resubmission | Where addressed |
|---|---|---|---|
| AE-1, R1-W1 | Severe accuracy degradation under larger N and stronger non-IID (79.2 % at N=1 → 35–37 % at N=16 on CIFAR-10) | **Largely retired.** The cited collapse is a property of block-wise sequential block refinement under the original HE-IFD; the CFD protocol distils all client signal in one server-side step against an aggregated encrypted ensemble target, with no block-wise sequential dependency. New A4.1 grid measures the residual accuracy gap at N ∈ {5, 10, 20, 50} on CIFAR-10 / α=0.1; preliminary May-5 results at N=10 already approach Co-Boosting's privacy-unaware ceiling within 0.8 pp on MNIST α=0.3. | A4.1 + N-ablation, §VI |
| AE-2, R1-W3 | ≈ 460 GB per-client upload, no compression discussion | **Retired.** Single round, single encrypted ciphertext bundle per client of size ≈ 8 MB total (5 000 probe-row logits + α-scalar, CKKS logN=14 packing) per PRD §5. The two-orders-of-magnitude difference comes from removing per-block intermediate feature uploads, not from compression. | §V Communication, Fig. comm |
| AE-3, R2-Q2 | No end-to-end CKKS training run reported; only sub-operations | **Addressed.** A3 ships a real-HE end-to-end single-cell run on `t4_ai` covering Phase 0 (multiparty DKG) → Phase 4 (collective key-switch) on TenSEAL. Linear-accumulator design means per-step encrypted depth is ≤ 3 levels regardless of student architecture, so no bootstrapping is required — the entire protocol executes inside a single CKKS level chain. Wall-clock, memory, rotation counts, convergence reported in §V. | A3 §V-A |
| AE-3, R2-Q3 | No client-side encryption throughput at the 115 GB / N=4 upload | **Retired.** The 115 GB number is a property of the rejected protocol's per-block feature uploads; the resubmission uploads ≈ 8 MB / client and reports both per-phase encryption wall-clock and samples/sec throughput at this scale. | §V-B Encryption Throughput |
| AE-4, R2-Q4 | Malicious / colluding clients; encrypted-feature poisoning; robust aggregation under HE | **Out-of-scope, explicitly named in §VII Future Work.** We cite Viand–Knabenhans–Hithnawi 2023 SoK on verifiable HE compilers as the natural extension and acknowledge the threat surface without claiming protection. | §VII |
| AE-5, R2-Q5 | Privacy leakage from the released (decrypted) student | **Addressed.** A7 runs LiRA (Carlini et al. 2022) + loss-threshold (Yeom et al. 2018) MIA against the decrypted student across the A4.1 grid; AUC reported in §V-D. PRD §2.4 also derives the IND-CPA-with-statistical-query-floor framing that bounds release-time leakage formally. | A7 §V-D, §IV-C |
| AE-6, R3-2 | Three legacy challenges (polynomial magnitude explosion, training–distillation distribution gap, scale-aligned distillation loss) misaligned with the four contributions | **Retired.** The three legacy challenges are artefacts of the depth-heavy block-wise protocol. The resubmission's §I-A "Our Approach" restates the four challenges in terms of the new protocol: (C1) binding invariant under N−1 collusion; (C2) β/λ ensemble boost without division under HE; (C3) HE depth budget for the encrypted linear accumulator; (C4) post-release SQ-floor mitigation via DP-SGD teachers + per-row Gaussian noise. Each contribution is now cross-cited against its addressing challenge with explicit §§ pointers. | §I-A |
| AE-7, R2-Q1, R3-5 | No comparison with prior FL frameworks (FedAvg, FedMD, etc.); only mean-teacher reported | **Addressed.** A4.1 is a triple-axis comparison grid against 8 comparators across 4 method families: no-DP one-shot FL (FedMD, Co-Boosting, optional DENSE / FedDF / FuseFL); DP one-shot FL (FedDiff, FedKT, optional FedMD-NFDP / FedDM); HE multi-round FL for the communication axis only (POSEIDON, CURE, FedSHE, BatchCrypt, cited from published numbers). | A4.1 / A4.2 / A4.3, §V |
| R1-W2 | Operator-replacement cost (ReLU → poly, BN → ChannelScale, MaxPool → identity) not isolated and quantified | **Largely retired.** The linear-accumulator design runs the student forward pass on **plaintext** weights, so polynomial activations are not required in the forward path during training. Operator replacement now only affects the released student's inference-time compatibility — a much smaller surface than the rejected version. A4.1 reports the `Acc_plain_ReLU` / `Acc_plain_poly` / `Acc_cipher` triple on ours-rows to quantify the residual tax. | A4.1 operator-replacement triple, §V-A |
| R1-W4 | Privacy from empirical attacks only; decrypted-student leakage acknowledged but not addressed | **Addressed.** PRD §2 / §IV-C formalises the binding invariant on threshold decryption + the IND-CPA-with-SQ-floor framing + the all-zeros amplification defence via DP-SGD teachers + per-row Gaussian noise. Empirical MIA bounds the SQ-floor in A7. | A8 §IV-C, A7 §V-D |
| R1-W5 | Restricted to CIFAR-10 / FashionMNIST; missing ablations (magnitude reg vs affine bridges; 10 % feature budget; threshold-decryption impact on accuracy) | **Addressed.** A4.1 covers 5 datasets (MNIST, FashionMNIST, SVHN, CIFAR-10, CIFAR-100), 3 α (0.05, 0.1, 0.3), 3 seeds. The cited "magnitude reg vs affine bridges" / "10 % feature budget" ablations are artefacts of the block-wise protocol and are retired alongside it; the threshold-decryption impact on accuracy is reported as the `Acc_plain_poly` − `Acc_cipher` column of A4.1. | A4.1, §V |
| R2-Q6 | Why not keep student weights plaintext (CT×PT instead of CT×CT)? | **Retired — we do.** Student weights are plaintext during training; only a separate encrypted accumulator ⟨Δ⟩ holding the teacher-induced refinement is in ciphertext. At release time we compose ⟨θ_E⟩ = ⟨θ_0*⟩ + ⟨Δ⟩, threshold-decrypt, and ship. CT×PT is the dominant arithmetic throughout; CT×CT appears only in the β/λ ensemble target construction (depth ≤ 3 levels, once per protocol run). The R2-Q6 distinction is now structural rather than implementation-tax-driven. | §IV-A, A8 paragraph, Fig. protocol-overview |
| R3-1 | Abstract "strong incentive" claim insufficiently justified | **Addressed.** Abstract revised with concrete numbers (May-5 working text, reconciled against A4.1 in week 14): each client receives back a model strictly better than its local teacher with no plaintext leakage of its data; structural argument made explicit. | §Abstract |
| R3-3 | Motivation for one-shot + HE belongs in §I, not §II-C | **Addressed.** Motivation paragraph relocated from §II-C to §I-B per A11. | §I-B |
| R3-4 | Fig. 1 information-poor | **Addressed.** Replaced by two figures: `figures/threat_model_v2.svg` (threat model, already in CHANGES.md §5.1) and a new `figures/protocol_overview_v2.svg` (four-phase CFD pipeline with the plaintext-θ-track vs. encrypted-Δ-track distinction visualised inside Phase 2c). | Figs. 1 + 2 |
| R3-6 | §V-F future-directions belongs outside feasibility analysis | **Addressed.** §V-F moved to §VII Discussion / Future Work per A11. | §VII |
| R1/R2/R3 readability | "Difficult to read and understand"; organisation could be improved | **Addressed.** Wholesale rewrite of `methodology.tex` §3 onwards per PRD §9.5 (A1); §I-A rewrite per A10; §II-C → §I-B motivation move per A11. Voice consistency held against `methodology.tex:21` (per [Paper voice](memory)). | §I, §II, §III, §IV |
| ADV-Pruning (advisor freetext) | Should pruning be discussed? | Scoped per A12 outcome; depends on the Kerem (Küpçü) session in week 1. Three readings (block-wise interpretation retired by pivot; CFD-reading as compression knob; CFD-reading as structured-sparse-CKKS extension) addressed per the chosen interpretation. | A12 outcome — TBD |

---

## Section 3 — Per-reviewer response (Reviewer 1, "Reject")

We thank R1 for the detailed weaknesses list. The five W1–W5 concerns are addressed above; we summarise here.

- **R1-W1 (accuracy collapse).** Retired by the protocol pivot. The CFD design's one-shot server-side distillation against an aggregated encrypted ensemble target removes the block-wise sequential refinement that produced the cited collapse. A4.1's N-ablation (N ∈ {5, 10, 20, 50}) on CIFAR-10 α=0.1 measures the residual gap; we expect — and report empirically — a substantially smaller degradation than the cited 79.2 % → 35–37 % collapse.
- **R1-W2 (operator-replacement cost).** Largely retired. The linear-accumulator design uses plaintext student weights during training; polynomial activations are only needed for the released encrypted student's inference compatibility. A4.1 reports `Acc_plain_ReLU` / `Acc_plain_poly` / `Acc_cipher` to quantify the residual tax explicitly.
- **R1-W3 (~460 GB upload).** Retired. ≈ 8 MB / client total per PRD §5.
- **R1-W4 (privacy from empirical attacks only).** Addressed via A8's formal IND-CPA-with-SQ-floor framing + the binding invariant on threshold decryption (§IV-C) + A7's empirical MIA bounds.
- **R1-W5 (limited datasets / ablations).** Addressed via A4.1's 5-dataset × 3-α grid + the operator-replacement triple. The block-wise-protocol-specific ablations are retired alongside the protocol.

---

## Section 4 — Per-reviewer response (Reviewer 2, "Major Revision")

We thank R2 for the structured Q1–Q6 list.

- **R2-Q1 (no FL framework comparison).** Addressed via A4.1's 8-comparator triple-axis grid: FedMD, Co-Boosting (no-DP one-shot), FedDiff, FedKT (DP one-shot) as tier-1; FedDF, DENSE, FuseFL, FedMD-NFDP, FedDM as tier-2 conditional. HE multi-round FL (POSEIDON, CURE, FedSHE, BatchCrypt) compared on the communication axis only.
- **R2-Q2 (no end-to-end CKKS).** Addressed via A3's TenSEAL single-cell end-to-end run. Linear-accumulator design means per-step depth ≤ 3 levels, fits TenSEAL's 7-level chain at logN=14 without bootstrapping.
- **R2-Q3 (encryption throughput at 115 GB).** Retired by [R1-W3] retirement. Throughput reported at the new ≈ 8 MB / client scale.
- **R2-Q4 (malicious / colluding clients).** Out-of-scope, named in §VII; verifiable HE cited as natural extension.
- **R2-Q5 (post-release MIA on decrypted student).** Addressed via A7 (LiRA + loss-threshold + population MIA single-cell ablation).
- **R2-Q6 (why not plaintext student weights).** Retired — we already do, per §0.2 retired-concerns table and A8's R2-Q6 paragraph. Student weights are plaintext during training; only the teacher-induced delta accumulator is encrypted.

---

## Section 5 — Per-reviewer response (Reviewer 3, "Revise & resubmit as new")

We thank R3 for the recommendation to resubmit-as-new and have followed that path, with the substantial revisions outlined here.

- **R3-1 (abstract incentive).** Addressed via A10 abstract rewrite with concrete numbers (per the working text; numbers reconciled against A4.1 in week 14).
- **R3-2 (challenges ↔ contributions mismatch).** Retired and rewritten. The three legacy challenges are artefacts of the block-wise protocol; §I-A now lists C1–C4 in terms of the new CFD protocol with cross-section pointers.
- **R3-3 (motivation belongs in §I).** Addressed — motivation moved §II-C → §I-B per A11.
- **R3-4 (Fig. 1 information-poor).** Addressed — replaced by two figures (threat model + protocol overview) with the plaintext-track / encrypted-track distinction.
- **R3-5 (no FedAvg / FedMD baseline comparison).** Addressed via A4.1's 8-comparator grid.
- **R3-6 (§V-F future directions outside feasibility).** Addressed — §V-F moved to §VII.

---

## Section 6 — Closing

We are grateful for the rigour of the previous review cycle. The substantial revisions invited by the AE have been read at the level of *protocol design* rather than *prose polish*, and we believe the resubmission is materially stronger across all three reviewer axes (security, evaluation, presentation). Out-of-scope adversaries — actively malicious clients, encrypted-feature poisoning, and the open problem of HE-compatible robust aggregation — are acknowledged explicitly in §VII Future Work, with verifiable HE cited as the natural extension via the Viand SoK and Atapoor et al.'s lattice-SNARK construction for CKKS. We look forward to the editorial decision.

Sincerely,
[Author block: corresponding author Sav, with Kanpak, Küpçü]
