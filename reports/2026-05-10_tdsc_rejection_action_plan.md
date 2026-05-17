# HE-IFD TDSC rejection — action plan
## Source: TDSCSI-2026-04-1278 — Decision (Reject), 2026-05-08

**Date:** 2026-05-10
**Author:** H.İ. Kanpak (with assistance — planning doc only, no experimental runs)
**Status:** Working document; entries flagged `[OPEN]` are awaiting decisions in an ongoing grilling session and will be locked once resolved.
**Anchored to:** the methodology pivot in `reports/2026-05-05_methodology_pivot.md` (the **PRD**) and the May-5 results in `reports/2026-05-05_one_shot_cfd_central_vs_client_update.md`. **Canonical project repo:** `https://github.com/hkanpak21/HE-IFD.git` (public). All experimental code, prototypes, job scripts, and figure-generation scripts referenced below live here; the local working tree at `/scratch/hkanpak21/HE_IFD/` must remain in sync with this remote.

> The PRD is the authoritative reference for the methodology; this file is the *response strategy* layered on top of it. Where the PRD has already locked a design decision, this file restates only the decision's effect on the resubmission narrative.

> **🛑 GOLDEN RULE — never run anything on the login node.** Every Python invocation that uses GPU, opens a CKKS context, trains a model, or generates synthetic data must go through `sbatch` or `srun --partition=t4_ai --account=comx29`. The login node has no GPU, throttles long-running CPU jobs, and is shared with other users. See [Valar HPC cheatsheet](memory) for sbatch templates. This rule supersedes any timing concern: a missed deadline is recoverable, a banned account is not.

> **⚠️ Valar concurrency wall (2026-05-17 audit).** User `hkanpak21` is bound to QoS `comx29` which caps **concurrent GPU usage at 1 Tesla T4 across the entire cluster** (`sacctmgr show qos comx29 → gres/gpu:tesla_t4=1`). The partition itself has 64 T4s and the alternative `t4_ai` QoS would allow 16 concurrent GPUs at the same billing rate, but the user's association does not currently include that QoS (`sacctmgr show user hkanpak21 → Qos=comx29` only; 159 historical jobs all single-GPU). **Action item P0:** open an admin ticket requesting `t4_ai` QoS be added to hkanpak21's comx29 association. Without this, A4.1 sequential on 1 GPU at tier-1 scope (360 cells × 1–2 GPU-h) is 45–90 calendar days — the 26-week plan is infeasible. The plan below assumes the QoS escalation lands by end of week 1; if it does not, scope cuts in §0.1 apply.

> **⏱️ 8-hour wallclock cap on t4_ai.** All jobs >8 h must checkpoint and auto-requeue. Convention: write `state.ckpt` every 30 min, read on startup, `scontrol requeue $SLURM_JOB_ID` on `SIGUSR1`. DP-DDPM training (6–12 h per client per dataset), end-to-end CKKS A3 runs, and the heavier A4.1 cells all need this. Vendoring this pattern into a shared `scripts/sbatch_resume_wrapper.sh` is part of week-1 setup.

### 0.05 Adaptive execution — see PRD §9.5

This action plan executes under the **adaptive execution methodology** added to PRD `reports/2026-05-05_methodology_pivot.md` §9.5 on 2026-05-17. The summary: methodology has a *stable core* (binding invariant, multiparty CKKS at $t=N$, linear-accumulator construction, α-vs-γ variant boundaries, CKKS regime) and *adjustable peripherals* (hyperparameters, dataset / α / comparator scope, student architecture, sbatch chunking). An agent running this plan:

- **Tweaks peripherals freely**, logging each in a `reports/2026-MM-DD_tweak_<slug>.md` report per PRD §9.5.3 and appending one line to `reports/decision_log.md` per PRD §9.5.6.
- **Halts and escalates** on any stable-core touch, compute overrun > 50 %, critical-path slip > 1 week, A4-sanity failure, > 3 pp number divergence from A10's working text, both-tier-1-DP-comparator failure, linear-accumulator gradient-norm divergence > 5 %, or any login-node violation. See PRD §9.5.4 for the full list.
- **Follows a three-strike debug protocol** before escalating (PRD §9.5.5): the obvious fix, then the documented fallback, then a peripheral tweak. Specific conventions for numerical / checkpoint-resume / HE-precision / slurm-side errors are listed there.

This frees both the user and any future agent from having to round-trip approval for routine deviations, while protecting the design properties that define the work. The cover letter §6 (closing) cites the decision log as evidence of methodological transparency through the resubmission window.

### 0.1 Scope cuts if QoS escalation fails (contingency)

If P0 (t4_ai QoS access) is denied, the plan must cut to fit 1-GPU-concurrent across 26 weeks. Roughly 4 200 GPU-hours of compute are available continuously over 6 months (24 h × 175 days × 1 GPU). Distribution under this constraint:

- **A4.1 to tier-1 + 3 datasets + 2 α + 2 seeds:** 8 method-rows × 12 cells × 1–2 GPU-h = 96–192 GPU-h. Drops SVHN, CIFAR-100, α=0.1 (keep 0.05 and 0.3), drops 3rd seed.
- **A5 γ to MNIST + FashionMNIST only at 1 α:** 2 datasets × 10 clients × 6–12 h = 120–240 GPU-h.
- **A3 single cell:** ~100 GPU-h.
- **A7 MIA at 16 shadows:** ~120 GPU-h.
- **N-ablation:** drop entirely (cite Co-Boosting's Table 6 instead).

Total ≈ 450–650 GPU-h, plus teacher training and ablations. Fits, but the response document is materially weaker (3 datasets, 2 α, 2 seeds). **Get the QoS escalation; this contingency is the floor.**

---

## 0. Priority order — user-directive, 2026-05-17

The resubmission's headline contribution is a **triple-axis Pareto argument**: HE-IFD dominates one or more of {accuracy, communication, time} against every comparator family while being honest where it does not. This reorders the action plan as follows; lower-priority items execute in parallel where compute allows, but the methodology-comparison grid (A4-tri-axis, §4) is the single critical-path artefact that the response document is built on.

**Priority 1 — Methodology comparison grid (time × accuracy × communication vs prior SOTA).** Three axes, each with its own comparator family:
- *Accuracy axis* — vs (a) **no-DP one-shot FL** baselines (FedMD `li2019fedmd`, DENSE `zhang2022dense`, FedDF `lin2020feddf`, Co-Boosting `dai2024coboosting`, FuseFL `tang2024fusefl`) as the privacy-unaware ceiling we approach; and vs (b) **DP one-shot FL** family (FedKT `li2021fedkt`, FedMD-NFDP `sun2021fedmdnfdp`, FedDiff `feddiff2024`, FedDM `xiong2023feddm`) where cryptographic privacy lets us avoid the DP utility tax at meaningful ε. Re-run all comparators at our (dataset, α, N=10, seed) settings so the comparison is matched.
- *Communication axis* — vs **HE multi-round FL** (POSEIDON `sav2021poseidon`, CURE `kanpak2024cure`, FedSHE `wei2025fedshe`, BatchCrypt `zhang2020batchcrypt`). Our one-shot encrypted upload (~8 MB/client) is asymptotically better than any multi-round HE FL: each round of POSEIDON/CURE/FedSHE costs comparable per-round bytes but they need 50–200 rounds. *Honest framing:* the comparison is not perfectly apples-to-apples — they solve standard FL aggregation under HE; we solve one-shot distillation. State this in the table caption; it is not unfair because we are solving the harder protocol-design problem under the same cryptographic regime.
- *Time axis* — same comparator families as communication. Same caveat; same framing.

**Priority 2 — Real end-to-end CKKS training time** (A3, §4). Required by [R2-Q2] but does not block the grid above; runs in parallel.

**Priority 3 — MIA / security checks** (A7, §4). Required by [AE-5] / [R2-Q5] but a numbers-only afterthought to the headline grid.

Everything else (textual rewrites, structural fixes, formal privacy framing, advisor-flagged improvements) is downstream of Priority 1's numbers landing.

### 0.2 Methodology-pivot framing — many reviewer concerns are now obsolete

**The reviewers reviewed an earlier version of the paper.** Since the rejection (2026-05-08), the methodology has been substantially redesigned: block-wise HE-IFD → one-shot encrypted CFD on a probe (PRD pivot, 2026-05-05), and within Phase 2c the encrypted state has been recast as a *linear accumulator* over encrypted teacher-induced gradient contributions rather than a full forward+backward chain through encrypted weights (user clarification, 2026-05-17). The response document must lead with this — many specific R1/R2/R3 weaknesses describe a protocol that no longer exists.

**Concerns retired (or substantially defanged) by the methodology pivot:**

| Tag | Original concern (rejected version) | Why obsolete in current protocol |
|---|---|---|
| [R1-W3] | ~460 GB / client upload, no compression | Retired. PRD §5: ≈ 8 MB / client total. Single round, single ciphertext bundle per client. |
| [R1-W1] | Accuracy collapse 79.2% (N=1) → 35–37% (N=16) | Likely retired. The cited collapse is for block-wise HE-IFD's sequential block refinement; the CFD protocol distils all client signal in one server-side step with no block-wise sequential dependency. A4.1 measures this empirically. |
| [R1-W2] | Operator-replacement cost (ReLU→poly, BN→ChannelScale, MaxPool→identity) not isolated | Largely retired. The linear-accumulator design means the student forward pass during training runs on plaintext weights, so polynomial activations are not required in the forward path. Operator replacement only affects the released encrypted student's inference compatibility, which is a much smaller surface than the rejected version implied. |
| [R2-Q2] | No end-to-end CKKS training run reported | Vastly easier to answer. A3's TenSEAL-only single-cell run fits LeNet-5 in a 7-level chain without bootstrapping; the protocol is structurally end-to-end-capable rather than aspirationally so. |
| [R2-Q3] | No client-side encryption throughput at the 115 GB upload | Retired by [R1-W3]'s retirement. Throughput measured at the new ≈ 8 MB scale; the question's premise (115 GB upload) is gone. |
| [R2-Q6] | Why not keep student weights plaintext (CT×PT vs CT×CT)? | Retired. Student weights *are* plaintext during training; only a separate encrypted accumulator ⟨Δ⟩ carries the teacher signal. CT×PT is the dominant arithmetic; CT×CT appears only in β/λ ensemble target construction, depth ≤ 3 levels, once per protocol run. See A8 rewrite. |
| [R3-2] | Three legacy challenges (polynomial magnitude explosion, training–distillation gap, scale-aligned loss) misaligned with contributions | Retired. The three legacy challenges are artefacts of the depth-heavy block-wise protocol. The new protocol introduces fundamentally different challenges (C1 binding invariant under N−1 collusion; C2 β/λ ensemble boost without division under HE; C3 post-release SQ-floor mitigation). See A10 §I-A rewrite. |

**Concerns that still apply (the work A1–A12 addresses):**

[AE-1], [AE-2 (already retired but reformulated)], [AE-3], [AE-4], [AE-5], [AE-6], [AE-7], [R1-W4], [R1-W5], [R2-Q1], [R2-Q4], [R2-Q5], [R3-1], [R3-3], [R3-4], [R3-5], [R3-6], [ADV-Pruning], [R1/R2/R3-readability].

**Cover-letter implication.** The "what changed since the rejected version" mapping table at the front of the response document (per §8 item 9) should explicitly list the retired-concerns table above. This is not deflection — the protocol genuinely is different, and the AE pool likely values seeing that the substantial revisions they invited (per the AE recommendation: *"explicit invitation to revise and resubmit subject to a six-month minimum waiting period and substantial revisions addressing major concerns"*) have actually landed at the protocol-design level rather than at the prose-rewrite level.

---

## 1. Decision letter at a glance

- **Manuscript:** "HE-IFD: Privacy-Preserving One-Shot Federated Distillation under Homomorphic Encryption"
- **Manuscript type:** SI — Special Issue on Security and Privacy in Federated Learning and Unlearning
- **Submitted:** 2026-04-xx · **Decision:** Reject (2026-05-08)
- **Authors:** Sav (corresponding), Kanpak, Küpçü
- **AE recommendation:** Reject; explicit invitation to revise and resubmit subject to a six-month minimum waiting period and substantial revisions addressing major concerns.
- **Reviewer recommendations:**
  - **R1 — Reject.** Empirical privacy story acknowledged (S1, S2). Five weaknesses (W1–W5) on accuracy degradation, operator-replacement cost, communication overhead, formal-vs-empirical privacy, and missing ablations.
  - **R2 — Major Revision.** Six numbered concerns (Q1–Q6) on missing related-work comparisons, missing end-to-end CKKS measurements, encryption throughput, malicious-clients robustness, post-release MIA, and a "why not plaintext student" question on the threat model.
  - **R3 — Revise and resubmit as new.** Six numbered concerns (#1–#6) on incentive justification, challenge↔contribution mismatch, motivation placement, Fig.1 information density, missing FedAvg/FedMD baselines, and §V-F scope creep.
- **Earliest TDSC resubmission window:** **2026-11-10** (six-month bar from rejection).

---

## 2. Advisor (AKUPCU) annotations — verbatim transcription

Extracted from the PDF on 2026-05-10 via PyMuPDF. Three FreeText notes in the advisor's voice plus 14 highlights without textual content. Highlights are marked by the underlying text they cover.

### 2.1 FreeText notes (advisor's own words)

| Page | Anchored to | Note |
|---|---|---|
| 2 | top-margin, after R1's W5 ablations bullet | **"Pruning? discuss with Kerem"** |
| 5 | R3 #1, the abstract-incentive paragraph | **"Add some more explanation"** |
| 5 | R3 #2, the challenge↔contribution mismatch paragraph | **"Write in a more direct manner, linking to chapters"** |

### 2.2 Highlights (no advisor text; the highlight itself is the signal)

**Page 1 — AE summary (3 highlights).**
- "the method suffers from severe performance degradation under larger client counts and stronger non-IID settings, without proposing mechanisms to mitigate this limitation."
- "the practical communication overhead remains extremely large, and that the manuscript lacks sufficient discussion of deployment feasibility, bandwidth constraints, or compression strategies."
- "Important experimental details are also missing, including end-to-end CKKS training measurements, encryption throughput, memory usage, and convergence behavior."

**Page 2 — R1 weaknesses (3 highlights).**
- W1, accuracy collapse from 79.2% (N=1) to 35–37% (N=16), no mitigation mechanism.
- W2, operator-replacement cost (ReLU→poly, BN→ChannelScale, MaxPool→identity) not isolated and quantified.
- W5, restriction to CIFAR-10/FashionMNIST and missing ablations (magnitude reg vs affine bridges, 10% feature budget sensitivity, threshold-decryption impact on accuracy).

**Page 3 — R2 Q2 (1 highlight).**
- "Did you execute any end-to-end training runs under CKKS with ciphertext weights and data (not just forward passes or sub-operations)?"

**Page 4 — R2 Q2/Q3/Q4/Q5 (4 highlights).**
- Q2 cont., wall-clock, rotation counts, memory, convergence for at least one block / small CNN.
- Q3, client-side encryption time and per-sample encryption throughput at the stated 115 GB/client (N=4) upload.
- Q4, malicious or colluding clients; encrypted-feature poisoning; robust aggregation compatible with encryption.
- Q5, MIA / inference attack against the **decrypted** student, across N and α.

**Page 5 — R3 #2/#4/#3/#5 (5 highlights).**
- "The challenges claimed in this paper and the contributions of this work are seriously mismatched."
- "the overview Fig.1 contains insufficient information"
- "the Motivation for One-Shot Communication and Homomorphic Encryption" — flagging the §II-C placement.
- "should be discussed in the Introduction"
- "no comparisons are made with other federated learning frameworks such as FedAvg, FedMD, etc., resulting in the lack of persuasiveness of the results."

### 2.3 Reading of the advisor's signal

Three buckets:

1. **Substantive technical** — the AE-summary trio, R1 W1/W2/W5, R2 Q2/Q3/Q4/Q5. The advisor wants these *answered with new experiments and analysis*, not deflected.
2. **Presentation / structural** — R3 #1/#2/#3/#4/#5. The advisor wants the introduction and abstract rewritten for tighter challenge↔contribution alignment, the motivation moved to the introduction, the overview figure replaced, and FedAvg/FedMD added as baselines.
3. **One open technical question** — "Pruning? discuss with Kerem". This is the only suggestion the advisor authored *as a possible answer* rather than as a flag on a reviewer concern. It needs a dedicated working session before it can be slotted into the action plan; provisionally placed in §6 below.

---

## 3. Reviewer-comment citation tags

Each reviewer concern below gets a short tag that the action items in §4 cite. Advisor freetext annotations get the prefix `ADV-`.

**Associate Editor (page 1).**
- `[AE-1]` — performance degradation under larger N and stronger non-IID; no mitigation. *Highlighted.*
- `[AE-2]` — practical communication overhead "extremely large"; no compression strategies. *Highlighted.*
- `[AE-3]` — missing end-to-end CKKS measurements, encryption throughput, memory, convergence behaviour. *Highlighted.*
- `[AE-4]` — malicious / colluding clients (R2 echo).
- `[AE-5]` — privacy leakage from released student (R2 echo).
- `[AE-6]` — challenge↔contribution alignment (R3 echo).
- `[AE-7]` — limited baselines (R3 echo).

**Reviewer 1 — Reject.**
- `[R1-W1]` — accuracy 79.2% (N=1) → 35–37% (N=16) on CIFAR-10; no mitigation. *Highlighted.*
- `[R1-W2]` — operator-replacement cost (ReLU→poly, BN→ChannelScale, MaxPool→identity) not isolated. *Highlighted.*
- `[R1-W3]` — ~460 GB upload, no compression discussion.
- `[R1-W4]` — privacy from empirical attacks only; decrypted-student leakage acknowledged but not addressed.
- `[R1-W5]` — limited datasets; missing ablations (magnitude reg vs affine bridges, 10 % feature budget, threshold-decryption impact). *Highlighted.*
- `[R1-readability]` — "Difficult to read and understand"; organisation could be improved.

**Reviewer 2 — Major Revision.**
- `[R2-Q1]` — no direct numerical comparison with prior FL / encrypted-FL methods.
- `[R2-Q2]` — no end-to-end CKKS training run reported (wall-clock, rotation counts, memory, convergence). *Highlighted.*
- `[R2-Q3]` — no client-side encryption throughput / time at the stated 115 GB upload. *Highlighted.*
- `[R2-Q4]` — malicious / colluding clients; encrypted-feature poisoning; robust aggregation under HE. *Highlighted.*
- `[R2-Q5]` — MIA against the **decrypted** student across N and α. *Highlighted.*
- `[R2-Q6]` — why not keep student weights plaintext (CT×PT instead of CT×CT)?
- `[R2-readability]` — "Difficult to read and understand"; organisation could be improved.

**Reviewer 3 — Revise & resubmit as new.**
- `[R3-1]` — abstract's "strong incentive" claim insufficiently justified. *Advisor freetext: "Add some more explanation".*
- `[R3-2]` — three challenges (polynomial magnitude explosion, training–distillation gap, scale-aligned loss) and four contributions misaligned. *Highlighted; advisor freetext: "Write in a more direct manner, linking to chapters".*
- `[R3-3]` — motivation for one-shot + HE belongs in §I, not §II-C. *Highlighted.*
- `[R3-4]` — Fig.1 (overview) information-poor. *Highlighted.*
- `[R3-5]` — only mean teacher compared; missing FedAvg, FedMD, etc. *Highlighted.*
- `[R3-6]` — §V-F future directions belongs outside feasibility analysis.
- `[R3-readability]` — "Difficult to read and understand"; organisation could be improved.

**Advisor (AKUPCU) standalone signal.**
- `[ADV-Pruning]` — "Pruning? discuss with Kerem" — the only authored technical suggestion; not a flag on a reviewer concern. See §5.

---

## 4. Action plan

Twelve actions A1–A12. Each lists (a) the reviewer / advisor tags it resolves, (b) the work, (c) status / gating. Sequencing is in §7.

### A1 — Wholesale methodology pivot to encrypted CFD on a probe (PRD §1, §4)

**Resolves:** [AE-1] (partly; completed by A4), [AE-2] (fully), [R1-W1] (partly; completed by A4), [R1-W3] (fully — 460 GB → ≈ 8 MB/client per PRD §5), [R3-2] (legacy challenges retire), [R3-4] (partly; completed by A11).

**Work.** Already locked in `reports/2026-05-05_methodology_pivot.md`. Wholesale replacement of `methodology.tex` §3 onwards per PRD §9.5. Communication-cost section recomputed from PRD §5 — directly retires the 460 GB number that anchored [AE-2] / [R1-W3]. Logged in `FL_TDSC/CHANGES.md` per the project rule.

**Status.** Design locked; textual rewrite is part of A8 / A11 below.

### A2 — TenSEAL prototype + primitive validation (PRD §8)

**Resolves:** [AE-3] (partly — primitives, not end-to-end), [R2-Q3] (fully — encryption throughput per phase).

**Work.** Implement `prototypes/cfd_tenseal_smoke.py`: TenSEAL CKKS context (logN=14, scale=2⁴⁰), encrypt mock teacher logit tensors, run §4.2 β-aggregation + λ variance, one encrypted SGD step on a 2-layer MLP student. Three measured outputs: per-step plaintext-vs-HE divergence (correctness), wall-clock per phase (compute), ciphertext bytes per phase (communication). Run on `t4_ai`, never login-node.

**Gating.** If the prototype's wall-clock for one encrypted SGD step extrapolates within 10× of the simulator's per-cell budget, A3 may stay simulator-only. If not, A3 must escalate.

### A3 — End-to-end CKKS run on a single cell — **committed (locked 2026-05-10)**

**Resolves:** [AE-3] (fully), [R2-Q2] (fully).

**Decision.** A real-HE end-to-end run on one cell of A4's grid (default: MNIST α=0.3, N=10, LeNet-5 student) covering Phase 0 (DKG) → Phase 5 (collective key-switch). This is the credible answer to [R2-Q2]'s literal question — *yes, we ran end-to-end* — and provides the calibration anchor the simulator-based 180-cell grid in A4 needs.

**Precedent.** End-to-end CKKS training on small models is already implemented in this codebase under `legacy/`:
- [`legacy/toy_ifd_ckks.py`](legacy/toy_ifd_ckks.py) — TenSEAL, 2-layer linear regression, end-to-end (ciphertext weights + ciphertext data, full forward + backward + SGD update).
- [`legacy/toy_ifd_real_he.py`](legacy/toy_ifd_real_he.py) — TenSEAL with real HE ops, MLP 784 → 128 (polynomial activation) → 10, end-to-end with per-operation timing measurements.
- [`legacy/toy_ifd.py`](legacy/toy_ifd.py) — matched plaintext baseline.

These predate the pivot but establish that the TenSEAL bindings, the polynomial-activation forward pass, and the encrypted weight update are all working in this codebase.

**Depth budget clarification (user-confirmed 2026-05-17).** The current CFD protocol does **not** forward-propagate through encrypted weights. The encrypted weights ⟨θ⟩ are a *linear accumulator* over encrypted gradient contributions: ⟨θ_E⟩ = ⟨θ_0⟩ + Σ_t lr · ⟨grad_t⟩, where each ⟨grad_t⟩ is a per-layer SGD update computed from the encrypted teacher signal applied to plaintext student state. No backward chain rule on encrypted intermediate activations; no per-layer depth accumulation across the network's depth. **Per-step encrypted depth ≤ 3 levels** (residual + scalar × CT for lr + addition). LeNet-5 (or any deeper architecture) fits TenSEAL's 7-level chain trivially at logN=14. **PRD §4.3's forward+backward depth model (depth +1 per layer for forward, depth-equivalent backward) describes an idealised full-encrypted-training variant that we do not implement;** the PRD prose needs updating to match the simpler protocol that is actually built. This obviates the bootstrapping concern entirely.

**Work.** Port `toy_ifd_real_he.py`'s end-to-end pipeline to the CFD protocol: Phase 0 DKG (multiparty CKKS), Phase 1 client logit upload, Phase 2 β-aggregation + λ variance (PRD §4.2), Phase 3 linear-accumulator SGD updates on ⟨θ⟩ against Ỹ on plaintext probe inputs, Phase 4 collective key-switch. Report wall-clock per phase, rotation counts, memory peak, ⟨θ_E⟩-vs-plaintext-θ_E discrepancy.

**Library decision (formerly §8 item 2, now resolved 2026-05-17): TenSEAL.** No native bootstrapping is needed because the protocol's per-step depth is constant ≤ 3 levels. The Lattigo escalation path is retired. This collapses the A3 dev estimate from 3–4 weeks to ~1–2 weeks (porting `toy_ifd_real_he.py`'s already-working TenSEAL ops to the CFD phase structure).

**Schedule.** Weeks 5–6 of §7 (revised down from weeks 5–8). The protocol simplicity moves the A3 finish line earlier, freeing weeks 7–8 for A4.1 launch overlap.

**Action item — update PRD §4.3.** The PRD prose ("plaintext-times-ciphertext at each layer (depth +1 per multiplied weight matrix), with polynomial activations (depth +deg)" and "expected 1k–5k bootstraps per protocol run") describes the wrong protocol. Replace with the linear-accumulator description above. Pending; not blocking the action plan but should land before the methodology rewrite in weeks 13–16 references PRD §4.3.

### A4 — Headline grid + N-ablation table (matched to Co-Boosting / FedMD / FuseFL)

**Resolves:** [AE-1] (fully via the N-ablation table), [AE-3] (convergence behaviour), [R1-W1] (fully via the N-ablation table), [R1-W2] (fully via the operator-replacement column), [R1-W5] (fully on datasets and ablations), [R3-5] (prior-work alignment), **[R2-Q1] (fully, via the DP-baseline comparator column added 2026-05-17)**.

**Restructured 2026-05-17 around the triple-axis Pareto argument** (per §0 user directive). A4 is no longer a single accuracy table against one comparator family; it is a three-table artefact (one per axis) anchored to four comparator families. Each table has its own re-run / cite-only protocol per the cost-honesty principle of §0.

#### A4.1 — Accuracy table (re-run all comparators at matched settings)

The privacy-unaware accuracy ceiling and the DP-encumbered accuracy floor between which HE-IFD sits.

| Method family | Members in scope | Privacy guarantee | Why included |
|---|---|---|---|
| Ours | HE-IFD α-warmstart, γ-encrypted-synth (if A5-profile permits) | CKKS IND-CPA + binding invariant; (γ) + DP-on-synthetic (ε=10) | the method under review |
| No-DP one-shot FL (ceiling) | FedMD `li2019fedmd`, DENSE `zhang2022dense`, FedDF `lin2020feddf`, Co-Boosting `dai2024coboosting`, FuseFL `tang2024fusefl` | none — server sees plaintext logits / weights / synthetic | privacy-unaware Pareto front; we approach but do not surpass |
| DP one-shot FL (floor at meaningful ε) | **FedDiff `feddiff2024`** (WACV 2025, direct γ-variant competitor), **FedKT `li2021fedkt`** (canonical PATE-style baseline) — both tier-1 must-have. FedMD-NFDP `sun2021fedmdnfdp`, FedDM `xiong2023feddm` retained as tier-2 redundancy. | (ε, δ)-DP at ε ∈ {1, 10} | shows the utility tax of statistical privacy at ε we can match cryptographically; **directly answers [R2-Q1]**. FedDiff specifically lets us run the γ-vs-FedDiff headline comparison: same problem space (one-shot FL with DP-on-diffusion-generated data), differing only in whether the distillation channel is plaintext (FedDiff) or HE (ours γ). |

**Matched-setting protocol.** All comparators re-run on our (dataset × α × N × seed) grid. Justification: cited numbers from each paper use bespoke partitions, teacher architectures, and probe constructions that make table-to-table comparisons noisy. Matched re-runs cost more compute but produce a single fair table.

**Headline grid dimensions.** 5 datasets (MNIST, FashionMNIST, SVHN, CIFAR-10, CIFAR-100) × 3 α (0.05, 0.1, 0.3) × 3 seeds × N=10 = **45 cells per method**. Methods in the grid (tier-1 = must-have, tier-2 = conditional on weeks 5–6 vendoring landing cleanly):
- *Ours* (tier-1): α-warmstart, α-warmstart-no-ensemble (A4-sanity continuation), γ (conditional per A5-profile gate): **2–3 method-rows**
- *No-DP one-shot* tier-1 (2): FedMD `li2019fedmd`, Co-Boosting `dai2024coboosting` — **2 method-rows × 1 = 2**
- *No-DP one-shot* tier-2 (3): FedDF `lin2020feddf`, DENSE `zhang2022dense`, FuseFL `tang2024fusefl` — **3 method-rows × 1 = 3 (conditional)**
- *DP one-shot* tier-1 (2): FedDiff `feddiff2024`, FedKT `li2021fedkt` — each at ε ∈ {1, 10} → **2 methods × 2 ε = 4 method-rows**
- *DP one-shot* tier-2 (2): FedMD-NFDP `sun2021fedmdnfdp`, FedDM `xiong2023feddm` — each at ε ∈ {1, 10} → **2 methods × 2 ε = 4 method-rows (conditional)**

**Locked-tier-1 minimum: 8–9 method-rows × 45 cells = 360–405 cells.** **Tier-1+tier-2 maximum: 17–18 method-rows × 45 = 765–810 cells.** Compute estimate per cell: 1–2 GPU-h for plaintext comparators, 2–4 GPU-h for our ours-rows at 100-epoch teachers (extrapolated from May-5 job 1032521 at 30-epoch teachers = 2h22m for full MNIST CFD). Tier-1 minimum ≈ 720–1 600 GPU-h; tier-1+tier-2 maximum ≈ 1 500–3 200 GPU-h. On 16-GPU concurrent (post-QoS-escalation): tier-1 fits in 2–4 days wall-clock, tier-1+tier-2 in 4–8 days. **On 1-GPU concurrent (current QoS), tier-1 alone is 30–67 days continuous — does not fit weeks 7–10.** P0 (QoS escalation) is the gating action; see §0.

**N-ablation sub-table.** CIFAR-10, α=0.1, N ∈ {5, 10, 20, 50}, 4 variants × 3 seeds = 48 cells (ours only — comparators reported once at N=10 in main table).

**ε=1.0 IID reference.** Optional, 5 datasets × 1 α=1.0 × N=10 × 3 seeds = 15 cells per method-row.

**Operator-replacement triple** (`Acc_plain_ReLU`, `Acc_plain_poly`, `Acc_cipher`) measured on the *ours* rows only — the comparators are plaintext so this column is N/A for them. Resolves [R1-W2] without inflating comparator compute.

**Approximate compute.** 14 method-rows × 45 cells × 1–2 GPU-h per cell = **~700–1 400 GPU-hours** for the headline grid. Plus N-ablation 48 cells × 1–2 GPU-h = ~70–100 GPU-h. Fits weeks 7–10 if 20–30 concurrent `t4_ai` jobs run; **never on the login node** (§0 golden rule).

#### A4.2 — Communication table (measure ours, cite published numbers for HE multi-round)

Where HE-IFD's one-shot design wins decisively.

| Method family | Comparator | What to report | Source |
|---|---|---|---|
| Ours (HE-IFD α) | — | Total bytes/client to convergence; per-phase breakdown (DKG → logit upload → ensemble → SGD → key-switch) | measured by A3 prototype + A4 grid |
| Ours (HE-IFD γ) | — | Same, plus encrypted-synthetic upload bytes | measured by A3 prototype + A4 grid |
| HE multi-round FL | POSEIDON `sav2021poseidon`, CURE `kanpak2024cure`, FedSHE `wei2025fedshe`, BatchCrypt `zhang2020batchcrypt` | Bytes/client per round × number of rounds to convergence; total bytes/client to convergence at the SAME accuracy target | cited from each paper at the closest matching dataset / model |
| No-DP one-shot FL | FedMD, DENSE, FedDF, Co-Boosting, FuseFL | Total bytes/client (one round each) | measured during A4.1 re-run |
| DP one-shot FL | FedKT, FedMD-NFDP, FedDM | Total bytes/client (one round each) | measured during A4.1 re-run |

**Honest-framing note in caption.** *"HE multi-round FL solves standard federated averaging under HE; HE-IFD solves one-shot federated distillation under HE. The comparison is asymmetric in protocol scope but matched in cryptographic regime (CKKS, multiparty key-management); we report it because the bytes/client-to-convergence metric is comparable across both and because the one-shot vs. multi-round design choice is the dominant lever for total communication."*

**No re-runs of HE multi-round comparators.** Published per-round and rounds-to-convergence numbers are sufficient and reproducible. Re-running POSEIDON/CURE/FedSHE/BatchCrypt at our settings would consume the entire compute budget for marginal accuracy on numbers their authors already report.

#### A4.3 — Time table (measure ours, cite published numbers for HE multi-round)

Same structure as A4.2 — wall-clock per phase for ours (from A3); cited wall-clocks for HE multi-round; measured wall-clocks for plaintext comparators (from A4.1 re-runs).

**Honest-framing note in caption.** *"HE-IFD is order-of-magnitude slower than any plaintext one-shot baseline because of CKKS arithmetic overhead. The relevant comparison is against other HE-protected FL systems, where HE-IFD's one-shot design eliminates the multi-round bootstrap cascade and amortises the DKG cost across exactly one protocol execution."*

#### A4.4 — A4-sanity — paper-existential pre-flight check (week 5, blocks A4 grid launch)

The PRD flags variant α-warmstart-no-ensemble as paper-existential: if it matches or comes within ~2 pp of α-warmstart, the entire encrypted-teacher-logit machinery is unjustified and the contribution narrative must pivot to "warm-start is enough." Discovering this in week 12 (A4 consolidation) is too late — the buffer weeks would not absorb a contribution-narrative rewrite.

**Work.** Single cell, week 5, on `t4_ai` (`sbatch --partition=t4_ai --account=comx29 ...`; **never the login node**): MNIST, α=0.3, N=10, 1 seed, **two variants**: α-warmstart (full CFD) and α-warmstart-no-ensemble. Both at 100-epoch teachers, 30+200 epoch student schedule per PRD §7.2. Half a day of compute; one afternoon of analysis.

**Decision rule:**
- Gap ≥ 5 pp (warmstart-no-ensemble loses by 5 pp or more) → proceed with confidence; full A4 grid launches week 7.
- 2 pp ≤ gap < 5 pp → proceed but flag in A10 that the headline framing emphasises non-IID / α=0.05 regime where the gap is widest.
- Gap < 2 pp → **HALT the full A4 grid.** Convene a planning session: either pivot the contribution to "warm-start is the right one-shot CFD primitive; encrypted ensemble adds privacy at no utility cost" (defensible if HE tax is the differentiator), or fundamentally rethink the resubmission.

Failure of this gate is the single most likely way the 26-week plan derails; cost of the gate is < 1% of A4's compute budget.

**Status.** A4.1 / A4.2 / A4.3 depend on A2 (depth budget validated), A6 (now folded into A4.1 as DP-baseline rerun jobs), and A4-sanity clearing. **A4 is now the single critical-path artefact for the response document** per §0.

**A4-sanity — paper-existential pre-flight check (week 5, blocks A4 grid launch).**

The PRD flags variant α-warmstart-no-ensemble as paper-existential: if it matches or comes within ~2 pp of α-warmstart, the entire encrypted-teacher-logit machinery is unjustified and the contribution narrative must pivot to "warm-start is enough." Discovering this in week 12 (A4 consolidation) is too late — the buffer weeks would not absorb a contribution-narrative rewrite.

**Work.** Single cell, week 5, on `t4_ai`: MNIST, α=0.3, N=10, 1 seed, **two variants**: α-warmstart (full CFD) and α-warmstart-no-ensemble. Both at 100-epoch teachers, 30+200 epoch student schedule per PRD §7.2. Half a day of compute; one afternoon of analysis.

**Decision rule:**
- Gap ≥ 5 pp (warmstart-no-ensemble loses by 5 pp or more) → proceed with confidence; full A4 grid launches week 7.
- 2 pp ≤ gap < 5 pp → proceed but flag in A10 that the headline framing emphasises non-IID / α=0.05 regime where the gap is widest.
- Gap < 2 pp → **HALT the full A4 grid.** Convene a planning session: either pivot the contribution to "warm-start is the right one-shot CFD primitive; encrypted ensemble adds privacy at no utility cost" (defensible if HE tax is the differentiator), or fundamentally rethink the resubmission.

Failure of this gate is the single most likely way the 26-week plan derails; cost of the gate is < 1% of A4's compute budget.

### A5 — γ-variant: DP-DDPM-generated probe (PRD §3.2)

**Resolves:** strengthens the privacy story; not directly demanded by reviewers but hardens [R1-W4] (formal privacy budget on synthetic) and [R2-Q5] (post-release privacy of synthetic-trained student).

**Work.** Per-client pixel-space DP-DDPM (Dockhorn et al. TMLR 2022, `dockhorn2022dpdm` in bib) at (ε_G, δ_G) = (10, 10⁻⁵) headline + (1, 10⁻⁵) ablation. Reference implementation: `github.com/nv-tlabs/DPDM` (U-Net ~2–3M params, DP-SGD via Opacus).

**Key scheduling insight.** DP-DDPM generators are trained *once per (dataset, α)* and reused across all 3 seeds — the seeds vary the distillation initialisation only, not the client data partition or the generator. Corrected compute:

| Scope | (dataset, α) pairs | Clients parallel per pair | GPU-hours | Wall-clock (pairs sequential) |
|---|---|---|---|---|
| Full grid (3 α/dataset) | 15 | 10 | 150 × h | 15 × h |
| Subset (1 α/dataset) | 5 | 10 | 50 × h | 5 × h |

where **h = wall-clock hours to train one DP-DDPM on a single client's partition on T4** (~5–6k samples at N=10). This estimate is *unvalidated in this codebase* — the PRD's ≈ 6–12 h figure was extrapolated from Dockhorn et al.'s A100 numbers at full-dataset scale. The actual per-client value at 1/N data could be anywhere from 1 h (MNIST, ε=10) to 20+ h (CIFAR-100, ε=1).

**Profiling micro-task (week 1, gates §8 item 10).** Before any generator training: run 1 client, MNIST, ε=10, on a single `t4_ai` node (`srun --partition=t4_ai --account=comx29 python prototypes/dpdm_profile.py --dataset=mnist --epsilon=10 --n_clients=1`). Captures wall-clock to convergence (FID plateau), GPU memory peak, and samples/sec. Takes ≤ h wall-clock by definition; result available within week 1 or early week 2.

**Conditional paths based on profiling result (§8 item 10, gate closes end of week 2):**

- **h ≤ 3 h → full-grid path.** γ becomes the 4th column in A4's 180-cell headline grid. Generator training for all 15 (dataset, α) pairs runs in *weeks 5–6*, in parallel with teacher re-training (both are per-client independent jobs on `t4_ai`). A4 grid execution in weeks 7–10 includes γ cells from day one. Weeks 11–14: γ analysis and integration only, no blocking compute.
- **3 h < h ≤ 8 h → subset path.** γ runs as a separate table at 1 α per dataset (5 pairs). Generator training in weeks 11–14 as currently planned; γ cells append after A4 consolidation.
- **h > 8 h → CIFAR-100/SVHN exclusion.** γ runs subset but only on MNIST + FashionMNIST + CIFAR-10 (3 pairs). SVHN and CIFAR-100 dropped from γ scope; noted explicitly in §experiments.

**Status.** Profiling micro-task to be added to `prototypes/`; grid-scope decision (§8 item 10) closes end of week 2.

### A6 — Comparator baselines (folded into A4.1 as of 2026-05-17)

**Resolves:** [R2-Q1] (fully — DP family included), [R3-5] (fully), [AE-7].

**Status.** Subsumed by A4.1 restructure. The 5 no-DP one-shot comparators (FedMD, DENSE, FedDF, Co-Boosting, FuseFL) and the 3 DP one-shot comparators (FedKT, FedMD-NFDP, FedDM) × 2 ε-values are now part of A4.1's 14-method-row headline grid. FedAvg (multi-round plaintext) is *not* re-run — its bytes / wall-clock numbers are cited from `mcmahan2017communication` for the A4.2 communication table where the multi-round baseline reference is needed; matched accuracy re-runs are unnecessary because no FL paper in the last five years uses FedAvg as the headline accuracy comparator.

**Sub-task that survives the fold-in.** Each comparator's reference implementation must be wrapped in our jobs harness (`jobs/cfd_v2_comp_<method>.sh`) and pinned to a specific commit in our fork or vendored under `comparators/<method>/`. Implementation hand-list:

| Comparator | Tier | Upstream | Action |
|---|---|---|---|
| Co-Boosting | **1** | reuse our May-5 implementation at `experiments/coboost_baseline.py` | re-run on 5-dataset × 3-α grid |
| FedMD | **1** | github.com/diogenes0319/FedMD_clean | vendor under `comparators/fedmd/`; wrap |
| **FedDiff** | **1** | github.com/mendieta/FedDiff (Mendieta–Sun–Chen WACV 2025 — `feddiff2024`) | **vendor; primary γ-variant comparator**; wrap at ε ∈ {1, 10} |
| FedKT | **1** | github.com/QinbinLi/FedKT | vendor; wrap with DP-SGD via Opacus at ε ∈ {1, 10} |
| FedDF | 2 | github.com/epfml/federated-learning-public-code | vendor; wrap |
| DENSE | 2 | github.com/zj-jayzhang/DENSE | vendor; wrap |
| FuseFL | 2 | github.com/wizard1203/FuseFL | vendor; verify M=5 protocol parses to N=10 fairly (their convention vs ours) |
| FedMD-NFDP | 2 | github.com/MingruiSun2019/FedMD-NFDP | vendor; wrap |
| FedDM | 2 | github.com/yuanhaoxiong/FedDM (Xiong et al. CVPR 2023 — `xiong2023feddm`) | vendor; wrap with optional DP toggle; note: iterative not one-shot — adapt to single-round or use as iterative reference |

**All implementation work pinned to the canonical project repo `https://github.com/hkanpak21/HE-IFD.git`.** Each comparator commit referenced as a submodule or a `comparators/<method>/COMMIT.txt` pinning record. No comparator work in scratch directories outside the repo.

### A7 — Post-release MIA against the decrypted student

**Resolves:** [AE-5], [R2-Q5], [R1-W4] (release-leakage acknowledgement → measurement).

**Decision (locked 2026-05-10).** Match the prior-work MIA pair we already used in the rejected paper for the encrypted training-time MIA, applied post-decryption:
- **LiRA** ([Carlini et al. 2022](https://arxiv.org/abs/2112.03570), `carlini2022membership` in bib) — strongest individual-record attack, the field standard.
- **Loss-threshold** ([Yeom et al. 2018](https://arxiv.org/abs/1709.01604), `yeom2018privacy` in bib) — the simplest baseline.

This pair is canonical in the MIA literature and is what the rejected paper used at training time; applying it post-decryption keeps the methodology internally consistent.

**Work.** Per cell of A4's headline grid (180 cells) + N-ablation (48 cells), run LiRA + loss-threshold on the decrypted student. Report AUC. Add a §V subsection. ≈ 1 day of compute on top of A4. **Population MIA** ([Ye et al.](https://arxiv.org/abs/2111.09679), needs adding to bib if cited) as a single-cell ablation on CIFAR-10 α=0.1 N=10.

**Schedule.** Week 11 of §7, in parallel with A5's γ-variant compute.

### A8 — Formal privacy framing: binding invariant + IND-CPA-with-SQ-floor

**Resolves:** [R1-W4] (formal proofs), [R2-Q6] (largely retired by linear-accumulator design — see §0.2; A8 reframes the question), reframes [AE-5].

**Work.** Rewrite `methodology.tex` §threat-model and §discussion to import PRD §2 (binding invariant on threshold decryption per §2.3, all-zeros amplification defence via DP-SGD teachers + per-row Gaussian noise per §2.5, SQ-floor on released student as the unavoidable lower bound per §2.4). Cite Mouchet et al. 2021 (`mouchet2021multiparty`, already in `references.bib` per CHANGES.md §3).

**R2-Q6 rewrite (stronger framing, user-confirmed 2026-05-17).** The previous draft argued from the binding invariant — *"plaintext weights would violate the invariant."* That defensive framing is unnecessary because the protocol *already does* what R2 asked. Single methodology paragraph (sketch):

> *We do keep the student weights in plaintext during training: the warm-started student $\theta_0^*$ and the per-iteration plaintext student state used to compute gradients are never encrypted. What carries cryptographic protection is a separate encrypted accumulator $\langle\Delta\rangle = \sum_t \eta \langle g_t\rangle$ holding the teacher-induced refinement, computed from the encrypted teacher signal $\langle T_i(\mathcal P)\rangle$ applied to the plaintext student state. At release time we compose the two: $\langle\theta_E\rangle = \langle\theta_0^*\rangle + \langle\Delta\rangle$, threshold-decrypt, and ship. The CT$\times$PT vs.\ CT$\times$CT distinction R2-Q6 raises is therefore real but already optimised — we use CT$\times$PT throughout, with CT$\times$CT appearing only in the $\beta/\lambda$ ensemble target construction (§\ref{sec:methodology_ensemble}), which is depth-bounded by $\leq 3$ levels and runs once per protocol execution. The binding invariant of §\ref{sec:threat_binding} is preserved because the only ciphertext ever subjected to threshold decryption is $\langle\theta_E\rangle$ — the composed end-state — never an intermediate $\langle\Delta\rangle$ or $\langle T_i(\mathcal P)\rangle$ in isolation.*

This paragraph also pre-empts the depth-budget concern that the (now-stale) PRD §4.3 prose would otherwise import.

**Status.** PRD content ready (with the §4.3 prose update flagged in A3); needs textual integration. Logged in `FL_TDSC/CHANGES.md`.

### A9 — Out-of-scope discussion of malicious / colluding clients

**Resolves:** [AE-4], [R2-Q4].

**Work.** One discussion paragraph in §future-work that (a) names the threats — encrypted-feature poisoning, model poisoning under encryption, robust aggregation compatible with HE; (b) cites Viand SoK 2023 (`viand2023verifiable`, already in bib per CHANGES.md §5.2) and recent vCKKS lines as the natural extension; (c) is explicit about the out-of-scope status. Cover letter to acknowledge the question and point here.

**Status.** Straightforward; ≈ half a page.

### A10 — Rewrite §I-A challenges + abstract incentive paragraph

**Resolves:** [AE-6], [R3-1] (advisor's "Add some more explanation"), [R3-2] (advisor's "Write in a more direct manner, linking to chapters").

**Work.**
- *Abstract.* Rewrite the participation-incentive paragraph with the concrete numbers from May-5 (MNIST α=0.3: 0.965 student vs 0.81 mean teacher; CIFAR-10 α=0.3: 0.521 vs 0.408) as the **working text**. These are the values that ship to advisor + co-authors at the week-16 draft handoff. The protocol is byte-identical to May-5 except for the teacher epoch count (30 → 100 to match Co-Boosting); per user judgment 2026-05-17, this should produce *near-identical* student-vs-mean-teacher ratios, so the May-5 numbers are the right working values. If the eventual A4.1 numbers diverge by more than 1–2 pp on either ratio, that itself is a flag that something is wrong with the new training pipeline — investigate before changing the abstract.
- *§I-A "Our Approach".* Replace the three legacy challenges (polynomial magnitude explosion, training–distillation gap, scale-aligned loss) with the post-pivot challenges: (C1) HE depth budget for end-to-end student SGD; (C2) β/λ ensemble boost without division under HE; (C3) binding invariant under N−1 collusion; (C4) post-release SQ-floor mitigation via DP-SGD teachers + per-row Gaussian noise. Each contribution cited against its addressing challenge with §§ pointers — the "linking to chapters" the advisor flagged.

**Numbers freeze + replacement protocol.**
- *Working text uses May-5 numbers* (above) — written into the abstract during weeks 16–18.
- *Real A4.1 numbers land in two waves:*
  - **2026-07-01 (mid-week 8):** MNIST α=0.3 + CIFAR-10 α=0.3 cells finish for the ours-rows + mean-teacher computation. These are the 4 abstract numbers.
  - **2026-08-01 (end-week 12):** Full A4.1 consolidation, all 5 datasets × 3 α + tier-1 comparators.
- *Replacement check (~1 hour, week 14):* compare the live A4.1 numbers against the May-5 working text. Apply diff:
  - |Δ| ≤ 1 pp on both ratios → keep May-5 text, footnote "consistent with our re-run at 100-epoch teachers."
  - 1 pp < |Δ| ≤ 3 pp → silently update to A4.1 numbers; no narrative change.
  - |Δ| > 3 pp → **stop and diagnose**: protocol divergence between May-5 and A4.1 implementations. Likely root cause: epoch-100 teacher overfitting in non-IID, or hyperparameter drift in the re-implementation.

**Status.** Working text written in weeks 16–18 with May-5 numbers (no blocking dependency on A4.1). Numbers reconciliation pass in week 14 against the 2026-07-01 partial results; final reconciliation in week 19 against 2026-08-01 consolidation. **A10's critical path no longer waits on A4.1** — it ships with May-5 values that the user has explicitly judged byte-identical-protocol-equivalent.

### A11 — Structural fixes: motivation move, future-directions move, new figures

**Resolves:** [R3-3] (motivation §II-C → §I-B), [R3-4] (Fig.1 replacement — both threat-model and protocol-overview), [R3-6] (§V-F → §VI / §discussion).

**Work.** Localised edits across `introduction.tex`, `background.tex`, `experiments.tex`, `conclusion.tex`. New protocol-overview figure at `FL_TDSC/figures/protocol_overview_v2.svg` (companion to `threat_model_v2.svg` per CHANGES.md §5.1) showing the four-phase CFD pipeline from PRD §4.1 with the encrypted boundary marked. All logged in `FL_TDSC/CHANGES.md`.

**Figure spec update (2026-05-17, Q10 follow-through).** The protocol-overview figure must visually distinguish the **plaintext warm-started student** track from the **encrypted accumulator** track inside Phase 2c. Single panel, left-to-right phase progression (0 → 1 → 2a → 2b → 2c → 3), but inside Phase 2c the two tracks render in parallel:
- *Top track (plaintext):* labelled `θ (plaintext)`, light-tinted Client beige fill `#C6A87D` (lightened ~30%); a `forward pass` glyph inside.
- *Bottom track (encrypted):* labelled `⟨Δ⟩ (encrypted accumulator over ⟨g_t⟩)`, Server grey-blue fill `#8B9EA8`; an `accumulate ⟨g_t⟩` glyph inside.
- *Composition glyph at the Phase 2c → Phase 3 boundary:* a `+` symbol bridging the two tracks, output labelled `⟨θ_E⟩ = ⟨θ_0*⟩ + ⟨Δ⟩` in Server colour; arrow to Phase 3 "collective key-switch" → each client.
- SVG structure: separate `<g id="plaintext-track">` and `<g id="encrypted-track">` groups so the colour distinction is editor-friendly.

This rendering pre-empts R2-Q6 visually and is the figure-level counterpart of A8's R2-Q6 rewrite (§A8). Anyone reading the figure can see at a glance that the student forward pass runs in plaintext during training; only the teacher-induced delta is encrypted.

**Status.** Mechanical once specs are confirmed.

### A12 — Pruning ablation [OPEN — depends on Kerem session]

**Resolves:** [ADV-Pruning].

**Work.** See §5.

**Status.** Scheduling the Kerem session is a §0 prerequisite (week 1).

### Optional / deferred

- **Large-scale dataset row** (CIFAR-100 / TinyImageNet): partly resolves the "no large-scale benchmarks" subcomponent of [R1-W5]. ≈ 2× A4's compute. **[OPEN — §8 item 5.]**
- **Lattigo end-to-end on multiple cells** (extension of A3): only if A3 is option (a) and the single-cell run lands cleanly with budget left over.

---

## 5. The "Pruning? discuss with Kerem" question

The advisor's only authored technical suggestion. Two readings:

1. **Block-wise reading (interpretation against the rejected paper).** Pruning the polynomial student attacks the magnitude-explosion problem (smaller network → fewer compositions → smaller end-to-end degree d^L → tractable HE depth) and trims the per-block ciphertext payload (fewer parameters → fewer ciphertexts to upload). This reading is mostly retired by the pivot.
2. **CFD reading (interpretation against the pivoted paper).** Pruning could (a) shrink the encrypted-student download (PRD §5: ~4 ctxts at 1 MB each per client, modest savings), (b) reduce the per-step depth budget by skipping multiplications against zero weights (CKKS does not have native sparse primitives, so this saves wall-clock only if a structured-sparsity scheme — block / channel pruning — is used so the matmul shape itself shrinks), or (c) post-decryption: prune the released student locally per client (Phase 5 of PRD §4.1) to fit a client's compute budget for inference.

**Action:** schedule a working session with Kerem (Küpçü) to clarify which reading the advisor intended, then either:
- if (1), respond in the cover letter that the magnitude-explosion challenge is retired by the pivot and pruning is no longer load-bearing;
- if (2a/c), add a short paragraph in §discussion / §extensions that names structured pruning as a complementary compression knob, with a single ablation cell (LeNet-5 student at 50 % structured channel pruning, MNIST α=0.3, plaintext only) to demonstrate the lever exists;
- if (2b), this becomes a non-trivial protocol addition (sparse CKKS primitives) that does not fit a 6-month timeline and is named as future work.

[OPEN — depends on Kerem session]

---

### A13 — Modern-architecture feasibility extension (ViT-tiny / ViT-small; user-added 2026-05-17)

**Resolves:** Strengthens [R1-W5] (extends scale beyond toy CNNs); pre-empts a likely line of reviewer pushback at any security venue ("does your method work beyond LeNet-5?"); supports the §V Feasibility narrative; positions the resubmission as forward-compatible with modern student architectures rather than tied to the small-CNN regime of the rejected paper.

**Rationale.** The linear-accumulator protocol (per [[project-linear-accumulator]]) makes per-step encrypted depth *constant in network depth* — ⟨θ⟩ accumulates encrypted gradient contributions, never propagates through encrypted forwards/backwards. The cost of running CFD with a ViT-class student is therefore not dominated by HE depth (which is the wall the rejected paper hit) but by the *width* of the encrypted gradient accumulator. This is exactly the regime where moving from LeNet-5 (~60 k params) to ViT-tiny (~5.5 M params) was previously unthinkable but is now a straightforward parameter-count scale-up. We exploit this.

**Two-phase scope.**

#### A13-Phase A — primitive-cost projection simulation (weeks 6–8)

**Work.**
1. *Primitive cost measurement.* Run a single `prototypes/he_primitive_bench.py` script on `t4_ai` (`sbatch`, **never login-node**). For logN ∈ {14, 15} and scale = 2^40, measure:
   - CT×PT mul (per CT, per slot-width)
   - CT+CT add
   - scalar × CT
   - rotation
   - encryption (per plaintext vector)
   - decryption (per ciphertext)
   - encoding / decoding overhead
   Output: a `prototypes/he_primitive_costs.json` keyed by (op, logN). Reproducible; checked into `https://github.com/hkanpak21/HE-IFD.git`.
2. *Per-step linear-accumulator model.* For a student of P parameters and L layers, derive the per-SGD-step encrypted cost as a closed-form function of (P, L, primitive costs). Linear-accumulator structure: ~L × (CT×PT for η + CT+CT add for accumulator update) per step. Per-step download: 0 bytes (server-side). Final download: ⌈P / N_slots⌉ ciphertexts × per-ciphertext bytes.
3. *Projection table for §V Feasibility.* Architectures: LeNet-5 (60 k), ResNet-18-poly (11 M), ViT-tiny (5.5 M, DeiT-tiny variant for distillation friendliness), ViT-small (22 M). SGD-step counts: {200, 1 000}. Output columns: per-step wall-clock, total wall-clock, server-state size, final download per client. Output: a single table in `experiments.tex` §V-C "Computational Feasibility at Scale."

**Status.** Independent of A2/A3 since it measures HE primitives directly, not the full protocol. Depends only on Valar capacity and the TenSEAL install. ≈ 1 GPU-day of compute, fits trivially within the 1-GPU contingency budget.

#### A13-Phase B — reduced-scale real-HE run on ViT-tiny (weeks 11–13, conditional on Phase A + A3 cost budget)

**Work.** Single cell, real end-to-end TenSEAL: ViT-tiny student on CIFAR-10, α=0.3, N=10, 1 seed, full Phase 0 → Phase 4. Validates the Phase A projection against measured wall-clock at the largest single-architecture point we can afford to run.

**Cost estimate.** ViT-tiny has ~5.5 M params vs LeNet-5's ~60 k → encrypted accumulator state is ~90× larger; per-SGD-step ops scale linearly with P → ~90× LeNet-5's A3 cell wall-clock. If LeNet-5's A3 single cell is estimated at ~50 GPU-h (per current §0.1 contingency math), ViT-tiny single cell would be ~4 500 GPU-h — does *not* fit on 1 GPU but fits 12 days wall-clock on 16 GPUs post-QoS-escalation. On 1-GPU contingency, **Phase B becomes infeasible and is dropped**, leaving Phase A as the load-bearing feasibility evidence.

**Gating.** Phase B proceeds only if (i) QoS escalation has landed, (ii) A3 LeNet-5 cell wall-clock measured at week 8 is within projection (validates the simulation), (iii) the Valar partition isn't preempting our jobs at the 1-GPU level.

**Output.** A single row in A4.1's communication/time table for ViT-tiny showing measured end-to-end numbers + the operator-replacement and HE-tax columns. Plus a narrative paragraph in §V Feasibility distinguishing projection (Phase A) from measurement (Phase B).

#### Architecture choice rationale

| Option | Params | Pros | Cons | Decision |
|---|---|---|---|---|
| DeiT-tiny / ViT-tiny | 5.5 M | Standard, distillation-friendly (DeiT is *the* ViT distillation paper), CIFAR-10/100 evaluated points in literature, ~90× LeNet-5 — pushes scale meaningfully | First time we'd handle attention under encrypted gradients — needs attention layers to fit the linear-accumulator model (which they do: query/key/value matrices are just linear layers, softmax in attention can stay plaintext for forward passes) | **Phase B target** |
| ViT-small | 22 M | More headline-worthy as a "modern model" | ~360× LeNet-5; infeasible on 1 GPU, tight even on 16 GPUs | Phase A projection only |
| BERT-base / DistilBERT | 66 M / 110 M | Text-domain coverage | Requires a new text-domain evaluation pipeline (new dataset, tokenisation, distillation loss form); doesn't fit 26-week window; CIFAR-10 / CIFAR-100 anchor of the rest of the paper would break | **Excluded.** Mention as future work in §VII. |
| ResNet-18 (polynomial) | 11 M | Already validated in our May-5 plaintext baselines as the student variant | Older architecture; reviewer push will favour ViT | Phase A projection only (cheap to add to the projection table); not Phase B |

**Net effect on the resubmission narrative.** §V Feasibility gains a subsection titled *"Computational Feasibility at Scale"* with (a) the Phase A projection table covering 4 architectures and 2 SGD-step counts, (b) the Phase B measured row for ViT-tiny CIFAR-10, (c) a closing sentence: *"the linear-accumulator construction makes the per-protocol-run HE cost a function of parameter count, not network depth; this removes the structural wall that previously confined encrypted federated distillation to LeNet-class students."* This is a substantive answer to the "scale" criticism that the rejected paper invited.

**Status.** Phase A locked (independent of QoS, ≈ 1 GPU-day, weeks 6–8). Phase B conditional on (i) QoS escalation (P0), (ii) projection validation in week 8, (iii) compute budget left over after A4.1 grid. **A13 does not delay the critical path** — both phases run in parallel with A4.1 / A3.

---

## 6. Resubmission venue options (for the record; decision deferred)

Per the user, the venue choice is open and not blocking the action plan. All canonical venue homepages below; **CFP cycle dates and submission portals must be verified per cycle** — do not rely on what's typed here for an actual submission deadline.

| # | Venue | Type | Homepage | Fit | Cycle / typical timing |
|---|---|---|---|---|---|
| 1 | **IEEE TDSC (resubmit-as-new)** | Journal (rolling) | `https://www.computer.org/csdl/journal/tq` · Submission: `https://mc.manuscriptcentral.com/tdsc-cs` | Native fit; same AE pool likely; reject letter explicitly invites this path. | No fixed deadlines; six-month bar applies, earliest **2026-11-10**. SI follow-ons announced via the IEEE-CS CFP page. |
| 2 | **IEEE TIFS** | Journal (rolling) | `https://www.ieee.org/publications/tifs` · `https://signalprocessingsociety.org/publications-resources/ieee-transactions-information-forensics-and-security` | Adjacent venue; HE+ML papers appear regularly; signal-processing leaning more than systems. | Rolling; first decision typically 2–4 months. No 6-month bar. |
| 3 | **USENIX Security** | Conference | `https://www.usenix.org/conferences` (find current Security year) | Top-tier security; HE+FL fits in the "applied crypto" / "ML privacy" tracks; reviewer pool is more systems-oriented. | Multi-cycle; recent format has summer + fall + winter deadlines per year. |
| 4 | **NDSS** | Conference | `https://www.ndss-symposium.org/` | Top-tier security; strong applied-crypto track; HE-FL papers appear. | Annual or two-cycle; summer deadline historically. |
| 5 | **IEEE S&P (Oakland)** | Conference | `https://www.ieee-security.org/TC/SP-Index.html` | Top-tier security; reviewer pool tougher on systems-only contributions; HE+ML papers do appear. | Recently moved to a multi-deadline format; check the year's CFP. |
| 6 | **ACM CCS** | Conference | `https://www.sigsac.org/ccs.html` | Top-tier security; strong applied-crypto / FL tracks. | Two cycles per year (typically Jan and May deadlines). |
| 7 | **PETS / PoPETs** | Journal-conference hybrid | `https://petsymposium.org/` | Direct fit on the privacy axis; quarterly cycles; smaller community than the top-4 above but very HE/DP-friendly. | Four cycles per year (Feb / May / Aug / Nov submissions, decisions ~2 months after each). |

**Notes on the matrix.** Venues 3–6 are top-tier security conferences; submission to one of these is a different positioning bet than venue 1–2. A paper that is currently structured for TDSC's interface ("manuscript-style" prose, generous related-work tables, full proofs in body) would need a substantial reformat to fit the conference page limits. If the resub target shifts to 3–6, the reformat itself is on the critical path; if it stays 1–2, it does not.

**Recommendation (carried forward from the grilling, not yet user-confirmed):** TDSC-as-new (venue 1) — the six-month wait absorbs cleanly into the experimental program of PRD §7–§8, the AE pool already knows the work, and a "this is the substantial-revisions version you invited" cover letter is a strong acceptance signal. PETS (venue 7) is the natural backup if TDSC-as-new fails; deadlines are quarterly so the cost of routing there after a TDSC second reject is bounded.

---

## 7. Timeline — keyed to actions A1–A12

26 weeks from 2026-05-10 to the earliest TDSC bar 2026-11-10. Calendar-week endpoints inclusive; overlapping rows mean parallel work.

| Week | Calendar | Action(s) | Notes |
|---|---|---|---|
| 1 | 2026-05-10 → 2026-05-16 | **P0: QoS escalation ticket**; §8 close-out; A12 scoping; **A5-profile**; `scripts/sbatch_resume_wrapper.sh` | Open Valar admin ticket for t4_ai QoS access (without this the plan slips into §0.1 contingency); resolve §8 open items; Kerem session for [ADV-Pruning]; run `prototypes/dpdm_profile.py` on `t4_ai` (1 client, MNIST, ε=10); write the checkpoint-resume sbatch wrapper used by all jobs >8 h |
| 2 | 2026-05-17 → 2026-05-23 | A2 dev; **§8 item 10 gate** | TenSEAL context, β-aggregation primitive; profiling result in → decide full-grid vs subset vs CIFAR-100/SVHN-exclusion |
| 3 | 2026-05-24 → 2026-05-30 | A2 cont. | One encrypted SGD step; depth-budget validation |
| 4 | 2026-05-31 → 2026-06-06 | A2 finish; A3 gate | Run prototype on `t4_ai`; user decides A3 (a) vs (b) |
| 5 | 2026-06-07 → 2026-06-13 | A4 setup; **A4-sanity gate**; A3 dev (if a); **A5-prep [full-grid path]** | Job templates `jobs/cfd_v2_*.sh`; teachers re-trained to 100 epochs (PRD §7.1); **single-cell α-warmstart vs α-warmstart-no-ensemble on MNIST α=0.3 N=10 — gap decides whether full grid launches**; Lattigo bindings in parallel; **[full-grid only]** launch DP-DDPM generator jobs for all 15 (dataset, α) pairs × 10 clients on `t4_ai` in parallel with teacher training |
| 6 | 2026-06-14 → 2026-06-20 | A4-sanity result in; full-grid launch decision | If gap ≥ 5 pp → green-light week-7 launch; if gap < 2 pp → halt + replan |
| 6–8 | 2026-06-14 → 2026-07-04 | **A13 Phase A: HE primitive bench + projection table** | `prototypes/he_primitive_bench.py` on `t4_ai`; logN ∈ {14,15}; projection for LeNet-5 / ResNet-18-poly / ViT-tiny / ViT-small. Output: `experiments.tex` §V-C table. ~1 GPU-day. |
| 7–10 | 2026-06-21 → 2026-07-18 | **A4.1 triple-axis grid execution** (top priority per §0) | 14 method-rows × 45 cells = 585–630 cells: ours (2–3 rows), no-DP one-shot ×5, DP one-shot ×3 × 2 ε. **+ γ cells [full-grid path]**; N-ablation 48 cells. Comparator wrappers from A6 fold-in must land week 6 or earlier; **every job sbatched, no login-node execution** |
| 11–13 | 2026-07-19 → 2026-08-08 | **A13 Phase B: ViT-tiny real-HE single cell (conditional)** | Only if QoS escalated, projection validated, compute budget remains. CIFAR-10 α=0.3 N=10 1 seed full Phase 0→4 TenSEAL on ViT-tiny. Validates Phase A projection. |
| 8 | 2026-06-28 → 2026-07-04 | A3 single-cell run (if a) | Wall-clock + memory + convergence captured |
| 11 | 2026-07-19 → 2026-07-25 | A7 MIA pass | LiRA + loss-threshold across A4 cells (≈ 1 day compute + 1 week analysis) |
| 11–14 | 2026-07-19 → 2026-08-15 | **A5 generator training [subset/exclusion path only]** | DP-DDPM training for 5 (or 3) (dataset, α) pairs × 10 clients; **[full-grid path]** no blocking compute here — A5 is analysis + integration only |
| 12 | 2026-07-26 → 2026-08-01 | A4 + A6 consolidation | Tables, figures regenerated |
| 13–16 | 2026-08-02 → 2026-08-29 | A1, A8, A9, A11 textual edits | Wholesale `methodology.tex` rewrite; threat-model paragraph; malicious-clients discussion; structural fixes; new figures |
| 16–18 | 2026-08-23 → 2026-09-12 | A10 — abstract + §I-A rewrite | Depends on A4 numbers |
| 17 | 2026-08-30 → 2026-09-05 | A12 (if scoped) | Pruning ablation if Kerem session selected reading 2a / 2c |
| 19 | 2026-09-13 → 2026-09-19 | A5 consolidation | γ-variant numbers integrated into §experiments (both paths converge here) |
| 20–21 | 2026-09-20 → 2026-10-03 | Response document drafted | Per-reviewer, per-tag, citing the resolving action |
| 22–23 | 2026-10-04 → 2026-10-17 | Sav + advisor passes | Two minimum; revisions in `FL_TDSC/CHANGES.md` |
| 24 | 2026-10-18 → 2026-10-24 | Final figure regen + bib pass | Optional FedSHE comm-curve add per CHANGES.md §5.4 |
| 25 | 2026-10-25 → 2026-10-31 | Final integration + co-author signoff | All co-authors |
| 26 | 2026-11-01 → 2026-11-10 | Submit | Earliest TDSC bar (2026-11-10) |

**Critical path** (blocking, reordered per §0 priority directive 2026-05-17): **A4-sanity → A4.1 (triple-axis comparison grid, including DP and no-DP baselines from former A6) → A10 → response doc → submit**. A4 is the single artefact the response document is built on; A2 → A3 is a parallel secondary track that supplies A4.2 / A4.3 wall-clock and bytes numbers but does not block the accuracy table.

**Independent / parallel (secondary):** A3 (E2E HE timing), A7 (MIA), A8, A9, A11.

**Long-pole compute (conditional):**
- *Full-grid path* (h ≤ 3 h): A5 generator training in weeks 5–6, fully parallel with teacher training — γ cells complete inside A4's execution window. **No separate long-pole.**
- *Subset path* (3 h < h ≤ 8 h): A5 generator training in weeks 11–14; 5 × 10 × h GPU-hours, parallelised across N clients per pair.
- *Exclusion path* (h > 8 h): 3 × 10 × h GPU-hours on MNIST + FashionMNIST + CIFAR-10 only.

**Decision gates that block downstream:**
- **P0 (Valar t4_ai QoS escalation) must close by end of week 1.** Without this, plan slips into §0.1 contingency (scope cuts to fit 1 GPU concurrent).
- §8 items 1–6 must close by end of week 1.
- **§8 item 10 (γ grid scope) must close by end of week 2** — full-grid path requires A5-prep to start in week 5 alongside teacher training.
- A3 (a) vs (b) must close by end of week 4.
- A4's N-sweep / large-scale-dataset extent must close by end of week 5.
- **A4-sanity (week 5, α-warmstart vs α-warmstart-no-ensemble gap) must close by end of week 6** — gates the full A4 grid launch.

**Risks to flag.**
- *A2 → A3*: If the TenSEAL prototype reveals a depth-budget violation, the simulator-based headline framing has to be rethought. **A2 must complete cleanly before A4 launches.**
- *A5-profile miss*: If the DPDM profiling job does not run in week 1 (login-node constraint, queue backlog), the §8 item 10 gate slips to week 3, which compresses the full-grid path's week-5 launch window. Run the profiling job as the first `sbatch` of the project.

---

## 8. Open items requiring user decision

Closing each unblocks the timeline above. Each cites its action.

1. **Venue (§6).** TDSC-as-new vs TIFS vs top-tier security vs PETS. *Status: deferred per user.*
2. **A3 — library choice for the end-to-end run.** ~~Open.~~ Resolved 2026-05-17 (user clarification): **TenSEAL.** The current CFD protocol uses encrypted weights as a linear accumulator over encrypted gradient contributions (no forward propagation through encrypted weights, no backward chain on encrypted intermediate activations). Per-step depth ≤ 3 levels, fits TenSEAL's 7-level chain at logN=14 trivially. No bootstrapping needed, no Lattigo escalation. PRD §4.3's depth model is the wrong protocol — pending PRD revision (see A3 action item).
3. **A4 — N-sweep.** ~~Open.~~ Resolved 2026-05-10: match prior-work convention. Headline at **N=10** (FedMD, Co-Boosting main, our May-5); dedicated N-ablation table at **N ∈ {5, 10, 20, 50}** on CIFAR-10 / α=0.1 (mirrors Co-Boosting Table 6 exactly). Legacy ε-clientupdate dropped from headline (3-cell diagnostic appendix only). Total ≈ 159 cells. See A4.
4. **A4 — operator-replacement isolation column.** ~~Open.~~ Resolved 2026-05-10: yes, the `Acc_plain_ReLU` / `Acc_plain_poly` / `Acc_cipher` triple is part of A4's spec. Directly answers [R1-W2].
5. **A4 — datasets.** ~~Open.~~ Resolved 2026-05-10: match Co-Boosting's 5-dataset set exactly — MNIST + FashionMNIST + SVHN + CIFAR-10 + CIFAR-100. TinyImageNet excluded (only FuseFL uses it; requires student-arch redesign that breaks the 6-month window). Directly answers [R1-W5]'s "limited datasets" complaint.
6. **A7 — decrypted-student MIA scope.** ~~Open.~~ Resolved 2026-05-10: LiRA + loss-threshold (the pair already used at training time in the rejected paper) across the full headline grid + N-ablation. Population MIA as single-cell ablation on CIFAR-10 α=0.1 N=10.
7. **A12 — pruning question (§5).** Still open; depends on Kerem session, scheduled for week 1.
8. **A11 — protocol-overview figure (Fig.1 replacement) specs.** ~~Open.~~ Resolved 2026-05-10: a single-panel figure showing the four-phase CFD pipeline from PRD §4.1 with the encrypted boundary marked (per the [Color scheme](memory) Client=#C6A87D / Server=#8B9EA8 convention), distinct from the threat-model figure. Source file: `FL_TDSC/figures/protocol_overview_v2.svg`.
9. **Cover-letter / response-document tone.** ~~Open.~~ Resolved 2026-05-10: forward-looking, with a clearly marked "what changed since the rejected version" mapping table at the front. This mirrors the TDSC convention for resubmit-as-new manuscripts.
10. **A5 — γ grid scope: full-grid vs subset vs CIFAR-100/SVHN-exclusion.** Depends on DP-DDPM profiling result from week 1 (1 client, MNIST, ε=10, `t4_ai`). Thresholds: h ≤ 3 h → full 180-cell grid (γ as 4th variant column, generators in weeks 5–6); 3 h < h ≤ 8 h → subset (5 (dataset, α) pairs, separate table, generators in weeks 11–14); h > 8 h → exclusion path (MNIST + FashionMNIST + CIFAR-10 only). **Must close by end of week 2** to keep the full-grid path's week-5 launch open. *Status: open — profiling job not yet run.*

---

## Appendix A — file inventory at the time of this plan

- Decision letter: `reports/FedDil - TDSCSI-2026-04-1278 - Decision (Reject).pdf`
- Methodology PRD (authoritative for the new protocol): `reports/2026-05-05_methodology_pivot.md`
- Empirical comparison vs Co-Boosting: `reports/2026-05-05_one_shot_cfd_central_vs_client_update.md`
- Earlier investigation notes: `reports/hypothesis_investigation.md`, `reports/methodology_investigation.md`
- Paper sources (block-wise text, deprecated content): `FL_TDSC/{main,introduction,background,methodology,experiments,conclusion,supplementary}.tex`
- Edits-since-rejection log: `FL_TDSC/CHANGES.md`
- Compute environment: Valar `t4_ai` partition, `comx29` account; **never login-node** (per the cluster cheatsheet memory and the §0 golden rule restated 2026-05-17).
- Canonical project repository: `https://github.com/hkanpak21/HE-IFD.git` (public). All experimental code, comparator wrappers, prototypes, job scripts, and figure-generation scripts must live in this repo. Local working tree at `/scratch/hkanpak21/HE_IFD/` is not currently linked to the remote (no `.git/` directory present; `git` binary missing from this Valar node). Linking step: clone the remote on a host with git installed, copy in the local edits, push back. **Owed before any new experimental code lands** — otherwise the comparator wrappers and prototype scripts have no canonical home and reproducibility for the response document collapses.
