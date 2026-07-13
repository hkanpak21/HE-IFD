# Design note — encrypted-inference threat-model upgrade

Branch: `threat-model-encrypted-inference` · opened 2026-07-13 · status: **in grilling, not locked**

This note records an in-progress design discussion. It is not yet a PRD or an ADR. The
authoritative method is still the classification protocol in the paper; this note captures a
*candidate upgrade* and the decisions reached while stress-testing it.

## The upgrade in one line

Do **not** decrypt the aggregated adapter/head. Keep it in ciphertext permanently and serve
**inference** under encryption: clients receive only query answers (labels), never the model.

## Threat-model change

| | current paper | upgrade |
|---|---|---|
| per-client Δⱼ | never exposed (only the aggregate is) | unchanged — still never exposed |
| aggregate model | **decrypted & handed to every client** (whitebox) | **never decrypted**; no plaintext whitebox artifact exists |
| what a client learns | the full model + released-model MIA (near-chance) | **only the labels it legitimately queries**, budgeted or DP-noised |

New protected asset = **aggregate-head confidentiality** (a model-IP / anti-redistribution
property, *not* a privacy property — per-client privacy and near-chance MIA were already
airtight without this). Q5 answered **yes**: we do want this stronger model.

Discipline: never claim clients learn "nothing at all" (impossible while serving useful
answers). Claim: *nothing about the weights or other clients' data beyond the budgeted/noised
label channel.*

## Why the design is forced, step by step

1. Head is **linear on frozen plaintext features** (`backbones.py` `LoRAHead.forward`:
   `fc(x) + s·B(A(x))`, `x = φ(x)` cached). So the *linear* inference `W_eff·φ` is **depth-1 CKKS**
   — same op as aggregation, moved to query time. Feasible only because the adapter is
   head-only/linear; internal-layer LoRA would push the whole nonlinear forward into ciphertext
   (intractable) and is out of scope.
2. Revealing **logits** → closed-form extraction of the linear head in ~`d` queries
   (Tramèr et al., USENIX Sec 2016). So reveal only the **argmax label**.
3. Strong threat model forbids decrypting logits even to the threshold-decrypting **coalition**
   → **argmax must be computed under encryption**, before decryption. This makes a nonlinear op
   load-bearing (the one the one-shot method never needed).

## Boundary search is a real, noted risk

Argmax-only does **not** close extraction: label-only boundary search (Lowd–Meek 2005;
Choquette-Choo et al. ICML 2021) still recovers a **functional clone** (up to scale+shift, never
exact weights) in polynomial (~10⁴–10⁶ adaptively chosen) queries. Mitigation is
**regime-dependent**:

- **Budget enforceable → rate-limit alone.** Honest use ≪ extraction threshold and ideally
  non-adaptive. *Scenario:* per-release **validation allotment** — run the fixed agreed held-out
  test set (~10³ queries) once per model version + a small monthly quota. Cap at ~2× eval-set
  size starves extraction; noise is ornamental.
- **Budget never enforceable → DP noise required.** Honest use ≫ extraction threshold and
  client-chosen. *Scenario:* the classifier **embedded in each client's production backend**
  (hospitals triaging every EHR record, millions/yr) — or the future generative service (one
  document = thousands of token-queries). No budget separates honest from adversarial traffic;
  only per-query **report-noisy-max** bounds cumulative leakage.

**report-noisy-max** (McSherry–Talwar / Dwork): add noise to each logit, report argmax → per-query
ε-DP. Implemented **distributively on the threshold-decryption smudge already run for MHE security**
(Mouchet 2021) → no new trust assumption; up to `t-1` colluding clients cannot subtract the noise.
Argmax kills closed-form regression; noise kills the boundary line-search that would defeat
argmax-alone. Frame as **DP + query-budget economics + label-only hardness — NOT cryptographic /
LWE hardness** (real-valued noisy regression is defeated by least squares; noise raises query cost
polynomially, and noise large enough to block extraction also corrupts the answer).

## Open items

1. **Argmax scheme: CKKS-approx vs CKKS→TFHE switch.** CKKS-approx argmax over `C=100` is
   bootstrap-heavy (~70 levels). TFHE functional bootstrapping does comparison/max/noisy-max
   natively (~`C` bootstraps); switch via PEGASUS (S&P 2021) / CHIMERA. **Blocker:** threshold/
   multiparty TFHE is far less mature than the multiparty CKKS the paper stands on; scheme-switch
   keys need DKG. Recommend: present argmax abstractly, TFHE-switch as efficient realization +
   honest maturity caveat; prototype CKKS-approx first only to measure.
2. **Serving / liveness model (Q4).** *Resolved re: confidentiality.* A designated serving party
   is an **untrusted evaluator**: in multiparty CKKS (Mouchet 2021) no entity ever holds the
   decryption key, so it holds only the collective *public* key + *evaluation* keys + ciphertext,
   and **cannot decrypt** — it sees no plaintext, learns neither the head nor client data. No
   party holds the LoRA weights in plaintext at all (ciphertext-only by construction). Collusion:
   serving-party + `(t-1)` clients → still `< t` shares → cannot decrypt; only `t` clients decrypt,
   which they could already do. **So the serving party adds no confidentiality trust and does not
   move the `t`-client collusion threshold.** It is trusted only for (a) liveness — mitigated by
   letting *any client* play the evaluator (needs only public keys) — and (b) honest computation —
   mitigated by verifiable HE (Viand 2023, Atapoor 2024, already cited). A malicious serving party
   still learns nothing (receives no decryptions).
   - **Key hierarchy / binary trees:** NOT needed for confidentiality (flat `t`-of-`N` already
     gives no-single-decryptor). Warranted only for **per-query liveness at scale** (a committee
     holding a *re-shared* threshold key so a sub-quorum decrypts each query — hierarchical/Shamir
     or Benaloh–Leichter access structures) or a **non-flat trust policy** (weighted/grouped
     clients). Recommend flat `t`-of-`N` for the paper; committee re-sharing as the high-QPS
     scalability lever, alongside report-noisy-max + serving-party (the "embedded/high-throughput
     deployment point").
3. **New experiment (feasibility crux).** Per-query encrypted **(noisy-)argmax + threshold-decrypt
   latency**, CKKS-approx vs TFHE-switch, `C ∈ {4…100}`. Accuracy is unchanged (same aggregate),
   so no new accuracy runs — but the systems profile shifts from *one-shot* to *persistent
   nonlinear inference service*, which the current cost section does not model.

## Paper integration (decided 2026-07-13)

**Strategic fork: ONE paper, both methods** (user chose fork (a) over a follow-up). Flow
preservation is the top constraint.

**Storytelling spine:** *"HE-OFT removes FL's training-time surface with a one-shot encrypted
aggregate; that same aggregate is either **released** (near-chance to release) or, for the
strongest deployments, **never decrypted** and **served** under encryption. One protocol, two
disclosure settings, one threat-model spectrum."*

Two flow-preservation insights:
1. **Single terminal fork, not a restructure.** Phase-0, local FT, encrypted displacement,
   depth-1 aggregate, vote, task-arithmetic — all **shared verbatim**. Only the last step differs:
   *Release* (threshold-decrypt + distribute — the current method) vs *Serve* (keep ciphertext,
   answer queries via encrypted argmax). ~95% of the paper untouched.
2. **Serve answers a question the paper already raises.** The honestly-reported MIA elevation
   (Banking77 0.59, CIFAR ~0.62) + Release handing a whitebox model to every client = the two
   residual exposures Serve closes. The disclosed limitation becomes Serve's motivation → strongest
   bridge. MIA section: "near-chance *if you release*; nothing *if you don't*." By whitebox ≥
   blackbox, the released-model MIA numbers also **upper-bound** Serve-mode leakage (one table,
   two uses).

**Naming:** use descriptive **Release / Serve**, not "Mode A/B" (banned dev-artifact terms per
`paper-structure-decisions`).

**Structure:** intro (+ compliance motivation + 1 contributions sentence); method (+ terminal
subsection "Releasing vs. serving the aggregate" + 2-tier threat-model para); ONE experiments
section with a **both-settings vs serve-only legend** (accuracy/heterogeneity/poison/comm/MIA =
both; timing = serve-only); new subsection **"The price of non-disclosure"** (per-query latency
delta); related (+ Tramèr/Lowd-Meek/Choquette-Choo/report-noisy-max/PEGASUS); conclusion unify.

**Motivation — compliance-backed FTaaS:** confidential data is *small + application-close*, not
big; pretrain public → fine-tune small confidential → high domain accuracy; regulation *strictly
restricts* pooling raw records → federated FT, and (when the model memorizes confidential data)
*not releasing the model* = Serve.

**VERB DISCIPLINE (reviewer-safety):** GDPR/KVKK do **not** literally "forbid" pooling. They impose
a **default prohibition on special-category (health) data with narrow exceptions** + **transfer
conditions**. Write "subject to a default processing prohibition / heightened conditions / transfer
restrictions," NOT "forbids." (Flagged by research pass; a reviewer will pounce on "forbids.")

**Verified citations (research pass 2026-07-13):**
- **GDPR** (verbatim from gdpr-info.eu, reproduces EUR-Lex): Art **5(1)(c)** data minimisation
  ("adequate, relevant and limited to what is necessary…"); Art **5(1)(b)** purpose limitation;
  Art **9(1)** special categories — health/genetic/biometric are *prohibited by default*;
  **Chapter V** third-country transfers — **Arts 44 et seq. (spans 44–50, NOT 44–49)**.
- **KVKK Law 6698** (article numbers official via kvkk.gov.tr booklet; wording via reputable
  secondary translation mbkaya.com — no verbatim EN statute exists): Art **6** special categories
  incl. health (default prohibition); Art **5** general processing / explicit consent; Art **9**
  transfer abroad — **amended by Law 7499, in force 2024-06-01 → cite as post-2024 adequacy
  regime**. (Art 8 = domestic transfer.)
- **FL/data-local as recognized response:** AEPD/EDPS joint statement 2025-06-10 ("models are
  trained locally … only the result is shared, without … send[ing] the original data to a central
  server") — companion to **EDPS TechDispatch #1/2025 on Federated Learning** (direct page 403; quote
  the AEPD mirror). Healthcare peer-reviewed: *Eurosurveillance* (ECDC), "potential of federated
  learning for public health … GDPR compliance," PMC11484284.
- Three provision-tied motivation sentences drafted (in research output) — ready to adapt once
  story is signed off. **Do not add .bib/.tex until user approves storytelling (HITL).**

**Status:** storytelling + structure = PROPOSED, awaiting user sign-off before any `.tex` edits
(paper writing = HITL). Open: (a) confirm spine + Release/Serve naming; (b) OK to foreground the
MIA-elevation-as-motivation bridge; (c) run timing benchmark now vs defer.
