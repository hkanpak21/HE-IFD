# Editorial Decision Package

**Manuscript.** HE-OFT: Privacy-Preserving One-Shot Federated Fine-Tuning under Homomorphic Encryption.
**Venue.** IEEE Transactions on Network Science and Engineering.
**Phase 2, editorial synthesis.** 2026-09-08. Panel `academic-paper-reviewer` v1.11.1, mode `full`, five seats.
**Calibration status.** `NOT_CALIBRATED`.

**Provenance statement.** The five seats were dispatched in parallel with no shared state and committed without reading each other. That is role separation. It is not independence and this package does not claim it as such. All five seats share one model family, so correlated error across seats is possible and is not excluded by the panel design. The editor's verification memo (`06-VERIFICATION-MEMO.md`) checked the load-bearing claims directly against `SUBMISSION.txt` and `TECHNICAL-REPORT.txt`. Where the memo and a seat disagree, the memo governs, and every such correction is recorded below.

**Attribution rule in force.** Every item in this package traces to a named seat. The synthesizer raised no finding of its own. Three arithmetic confirmations are marked as the editor's own reading of the manuscript, and each supports a seat's finding rather than adding one.

---

## 1. Decision

### Major Revision.

Four of the five seats recommend Major Revision. The Devil's Advocate recommends Reject. Under the one-outlier rule of `editorial_decision_standards.md`, the Reject rationale was examined before the decision was set rather than averaged into it. That rationale rests on two findings, DA C1 and DA C2, which are validated below and which do require new measurement whose outcome could move numbers in the abstract. It does not reach Reject, because Reject requires a fundamental unfixable failure or three of four seats recommending it, and neither holds. Every seat, the Devil's Advocate included, affirms the same three things: the design chain that forces the shared trained map to sit after the last nonlinearity is correct and is derived rather than asserted (EIC S1, R2 strength 1, R3 strength 3, DA observations), the cryptography is implemented in real multiparty CKKS and checked against the plaintext path rather than simulated (EIC S4, R1 S1, R2 strength 4, R3 strength 2), and the encrypted selection rule is new and is motivated by a correctly diagnosed negative result (EIC S2, R1 S2, R2 F16, DA closing paragraph). Those are the elements a Reject would discard, and no seat argues they are unsound.

What the panel does establish, unanimously, is that the ten-page submission cannot be assessed on its own. Every seat found load-bearing material that exists in the companion technical report and was removed from the paper. The editor verified eight such omissions directly. The submission's Theorem 1 states IND-CPA as its only hypothesis while the report states that the simulation step rests on a hypothesis the measured configuration does not satisfy. The submission gives an operational rule for setting the query allowance and never gives the allowance a number. The abstract carries a GPU latency that appears nowhere else in the ten pages. Section V-G states a range that Table I cannot produce. Two caption sentences the authors themselves wrote, disclosing that the effective federation was seven clients on one task and that two figure panels are single-seed, were dropped, which leaves the printed sentence in Section V-A false. That pattern, and not any one defect, is what sets the decision. It is repairable, most of it by moving text and numbers the authors have already written, and that is why the decision is Major Revision and not Reject.

The revision will be sent for re-review. Two items require new measurement before the claims that depend on them can stand, and they are marked as such in the roadmap.

---

## 2. Consensus

Threshold for this table is three or more seats, as the editorial brief sets it. The disposition column applies the panel's own counting rule, in which the denominator is the four non-Devil's-Advocate seats and the Devil's Advocate is tracked separately. A seat that did not speak to an issue is silent, and silence is not agreement.

| # | Issue | Seats raising it | Non-DA count and disposition | Editor verification |
|---|---|---|---|---|
| 1 | The ten-page submission cannot be checked on its own. Proofs, the extraction study, the allowance derivation, every selection cell, the survey and all three limitations "in full" are deferred to a companion cited as `arXiv:XXXX.XXXXX`, which no referee can obtain during review. | EIC W1, R1 (recommendation paragraph), R2 (summary), R3 (summary), DA (observations) | 4/4, CONSENSUS-4 | Not a memo item. The deferral pattern is visible in the submission text and each seat cites its own locations. |
| 2 | The abstract's "48.9 to 176.6 s with GPU acceleration" is a projection stated in the same clause and the same grammatical form as a measurement, and it appears nowhere in the body. | EIC W2, R1 F9(4), R3 W3, DA M5 | 3/4, CONSENSUS-3, R2 silent | Verified, memo item 1. The strings 48.9 and 176.6 occur exactly once each, and the word GPU occurs once in the whole submission, all in that one sentence. |
| 3 | The level-restoration mechanism is never named. Section V-E's prose latencies come from server-side bootstrapping and Figure 2 panel (d) is captioned under collective refresh, a factor of thirteen apart, with nothing marking the difference. The parameter sentence also omits ring degree 2^16, which the headline circuit uses. | R1 F9(1)(2), R2 F3, R3 W2(1)(2), DA M6 | 3/4, CONSENSUS-3, EIC silent | Not a memo item. Confirmed by the editor against the submission's Figure 2 caption and Section V-E prose. |
| 4 | Availability. Section II-A states that any t clients form a quorum so serving does not require every client online, and the same page states that the implementation instantiates t = N, under which one absent client blocks every query. The submission never joins the two, and availability is not among the three stated limitations. | EIC W4 and question 6, R2 F7, R3 W4, DA M4 | 3/4, CONSENSUS-3, R1 silent | Not a memo item. The two sentences and the three-limitation list are directly checkable in the submission. |
| 5 | No numeric query allowance appears in the submission, although the allowance is the paper's only operational privacy control and Section IV-E rests half the security claim on it. | R2 F8, R3 W1, DA C5 | 2/4, corroborated finding | Verified, memo item 2. The word allowance occurs seven times and no numeric bound on Q appears. The report gives Q under roughly 1.3e3 per client on AG-News and 2.2e4 on Banking77 at N = 10. |
| 6 | Table I lacks an A_sel column, and Section V-G's stated range of 0.029 to 0.136 cannot be produced from Table I, which yields 0.010 on CIFAR-100 and 0.090 on AG-News. | R1 F2, R3 W10(b), DA C3 | 2/4, corroborated finding | Verified, memo item 3, in the narrow form. See the correction in section 4, ruling D3. |
| 7 | The one-time selection cost is given only as a count of encrypted comparisons, while a cost more than four hundred times smaller is given in mebibytes. The measured figures, 7111 s and 145.4 GiB at twenty clients and a hundred classes, are report-only. | EIC W5, R3 W2(4), DA M1 | 2/4, corroborated finding | Verified, memo item 6. The strings 145.4 and 7111 occur once each in the report and zero times in the submission. |
| 8 | Two caption qualifications the authors wrote were dropped in the cut to ten pages. The effective federation is seven on AG-News and nine on TREC on one seed, and Figure 2 panels (a) and (c) are single-seed, which makes Section V-A's "every number is the mean over three seeds" false as printed. | EIC W3, R1 F3, DA M2 and M3 | 2/4, corroborated finding | Verified, memo item 7. Both sentences in Section V-B(a) describe DBpedia at the default configuration and give 0.789 and 0.803. |
| 9 | Section IV-D presents the provenance check in the present indicative, immediately after Proposition 1 opens the gap it would close. The report says "we implement neither". | R2 F3, R3 W5, DA M11 | 2/4, corroborated finding | Not a memo item. The two sentences are directly comparable across the documents. |
| 10 | The novelty claim is an unqualified "first" over a four-clause conjunction, and the deltas against POSEIDON and slytHErin are never stated as deltas in the ten pages. | EIC W10, R2 F16, DA N4 | 2/4, corroborated finding | Not a memo item. Table III's POSEIDON row shows model-in-plaintext as no, which each seat cites. |

Two further issues fall below the three-seat threshold and are recorded here because the editor verified them and they are decision-bearing. Neither is a consensus item and neither is presented as one.

- **No bit-security level is stated for any parameter set.** Raised by R2 F14 as MAJOR and by R1 F12 as a reproducibility failure. Verified, memo item 8: the string 128 occurs zero times in the submission and three times in the report. R2's judgement is that this is the single thing a reader needs in order to believe the cryptography.
- **The serving circuit's scaling constant was fixed from the exported plaintext head.** Raised only by DA C2. Verified, memo item 5: the phrase "exported head" occurs once in the report and zero times in the submission, and the report's Scope section states that a deployment cannot fix that constant because the head is a ciphertext.

---

## 3. Adjudication of the Devil's Advocate CRITICAL findings

Five CRITICAL findings were filed. Each is adjudicated visibly below. None is dropped. Three are validated in full, two are validated in part, and none is rejected. A validated or unresolved CRITICAL blocks a silent Accept, which is consistent with the Major Revision recorded above.

### C1. Theorem 1 is not instantiated by any configuration the authors offer, and a key recovery sits inside the stated threat model. VALIDATED.

**Corroboration.** R2 F1, filed independently and also at CRITICAL, reaches the same conclusion from the cryptographer's seat and adds the citation gap. R2 F2 independently reaches DA's third component, the rogue key-generation share. No seat disputes it. EIC, R1 and R3 are silent, and two of the three disclaimed the cryptographic remit explicitly, so the silence carries no weight either way.

**Ruling.** Validated on its documentary core, which is proven from the two texts. The report states that the simulation step of Theorem 1 rests on a hypothesis the measured configuration does not satisfy, and states of the recommended 2^25 value that it does not meet the 2^(lambda/2) rule and that the authors do not claim it does. The submission's Theorem 1 names IND-CPA as its only hypothesis and contains no occurrence of smudging, flooding, Micciancio or Checri. The editor verified all four occurrence counts, memo item 4. A referee holding ten pages would accept a theorem whose hypothesis the authors know is unmet in the configuration that produced every figure in Section V-E.

**Scope of the validation.** The repetition key-recovery attack is the authors' own analysis. R2 judged it correct and marked the 5e5 constant heuristic, and did not reproduce it. This package validates the disclosure defect and the unmet hypothesis as proven, and records the attack's practicality as the authors' own stated result rather than as an independently confirmed one. The claim that the required duplicate-query control must be enforced by a party Definition 1 permits the adversary to corrupt is proven from Definition 1 as printed.

**Consequence.** The phrase "the first cryptographically secure" in the abstract is not currently earned by the measured configuration. That is R2's wording and this package adopts it.

### C2. The correctness and latency measurements use a serving constant taken from the plaintext head, which the protocol forbids. VALIDATED.

**Corroboration.** None. This is a single-seat finding. No seat disputed it, and no seat raised it.

**Ruling.** Validated. The editor confirmed the textual basis, memo item 5. The finding has two parts and they have different status. That the constant came from the exported head is proven, on the authors' own statement in the report's Scope section, and that this limitation is absent from the submission's Section V-H is verified by reading the three limitations there. That is enough to validate the finding, because DA's charge is that the paper's title property is contradicted by the one experiment linking the cryptography to the accuracy table and that the contradiction is undisclosed. Both halves hold.

**What is not validated.** The magnitude. DA labels it open and the report says the cost of a public norm bound is not measured. Whether a looser constant costs precision or depth, and how much, is unknown to the panel. The roadmap therefore separates the disclosure, which is a sentence, from the re-measurement, which is a run.

**Note on surface form.** This finding arrived in the adversarial register of the Devil's Advocate seat. It is validated on the documents and would be validated identically in any other wording.

### C3. The headline cost quantity is not derivable from any table, and the reconstruction contradicts the stated range on two of five tasks. PARTLY VALIDATED.

**Corroboration.** R1 F2 derived the same five-row table independently and found the same two non-reconciling tasks. R3 W10(b) independently found the CIFAR-100 discrepancy. This is the best-corroborated of the five.

**Validated.** The arithmetic. Section V-G states that A_dis minus A_sel runs from 0.029 to 0.136 across the five tasks. Table I's own printed columns give 0.090 on AG-News and 0.010 on CIFAR-100, so neither endpoint of the stated range is reachable from the table a referee is reading. The editor confirmed this and confirmed that the reconciling values 0.669 and 0.756 occur zero times in the submission, memo item 3. The defect is real and it sits under a number the abstract quotes.

**Not validated.** The framing. DA's section heading and summary say the quantity is not derivable from any table in either document. That overreaches. Table II, the CIFAR-10 peer comparison, carries an explicit A_sel column with the values 0.949, 0.952, 0.950 and 0.953. DA's own finding body states the narrower and correct form, that A_sel is never tabulated for the five main tasks, so the overreach is in the summary rather than in the analysis. The correct statement is that Table I lacks the column. This package uses the narrow form throughout and directs the authors to answer the narrow form.

**Also not validated.** The suggestion that a referee will read the implied AG-News value of 0.668 as the selection rule acting as an oracle. DA supplies the benign explanation itself, per-seed selection over a seed on which the shared head falls to 0.402, and R1 reaches the same explanation independently. The finding is a reporting defect, not evidence that the selection rule was given information it does not have. No seat claims otherwise.

### C4. The channel enumeration is incomplete in the direction that defeats the encrypted reciprocal, and Theorem 2's delta is instantiated by a measurement that holds the relevant variable fixed. PARTLY VALIDATED.

**Corroboration.** None on the coverage channel. R1 F8 independently found that the membership design's shadow federations do not vary the partition and that the submission carries the conclusion without the limit, which corroborates the second half of DA's finding from a different seat and a different argument.

**Validated.** The algebra, which the editor checked against equation (1) as printed. The shared head is theta_0 plus the count-weighted sum of displacements over the vector of per-class totals, and Section III-B(c) states that rows no client covers remain at the public initialiser. For a class held by exactly one client h, the numerator row is n_hc times Delta_hc and the denominator row is n_hc, so the merged row minus the initialiser is exactly that client's own displacement. Encrypting the denominator buys nothing for that row. Section V-B's own sentence, that with 77 classes each head row is decided by few clients or none, establishes that the case occurs inside the paper's own grid. Section V-F's sentence that the only remaining channel is the sequence of answers is therefore incomplete as printed, because the support of the coverage pattern is recoverable from an extracted head and the encrypted reciprocal was justified on protecting exactly that class of information.

**Validated.** The measurement limit. The report states that its shadow federations vary who trains on what while holding the coverage pattern fixed and that they say nothing about how leakage moves when the partition moves, and then concludes that measuring the strongest adversary the proposition admits bounds every adversary the protocol admits. DA is right that the second sentence does not follow from the first, and R1 F8 reaches the same place by way of the power calculation.

**Not validated.** The magnitude, and the claim that Theorem 2 is satisfied vacuously. DA marks the coverage-inference advantage open and states that nobody has measured it. The Definition 2 counterexample is constructed rather than run. This package therefore requires the authors to answer the finding, by measurement or by an explicit restriction of Theorem 2's scope to matched class support, and does not record a proven break of Theorem 2.

### C5. The submission gives a deployment a rule for setting the parameter its operational security rests on, and the companion says the rule is derived from the wrong side. VALIDATED.

**Corroboration.** R2 F8 and R3 W1 independently found the missing numeric allowance, from the cryptography seat and the deployment seat. R1 F7 independently found the dropped caveat, and adds two defects DA did not raise: the exponent on d is not identified because every extraction cell uses d = 768, and the residuals on C change sign so the law is not reliably conservative. The three seats reach one conclusion by three routes.

**Ruling.** Validated in full. The submission carries the recipe, "a deployment can therefore set its allowance from C, d and the fidelity it concedes", and drops the report's own sentence that the measured figures bound the allowance from the wrong side because a cryptanalytic route costs a factor logarithmic in the precision demanded rather than linear in it. The editor verified that no numeric allowance appears in the submission, memo item 2. Giving an operational rule while withholding the authors' own judgement that the rule over-estimates the safe value is the defect, and it is the one place where the panel is unanimous that the omission changes what a deployer would do.

**Count.** Three CRITICALs validated in full (C1, C2, C5), two validated in part (C3, C4), none rejected.

---

## 4. Disagreements between seats, and the rulings

### D1. Whether to reject. DA against the other four.

DA recommends Reject on the ground that C1 and C2 require measurement campaigns whose outcomes would move the numbers in the abstract, and that C1 cannot be repaired by editing because a conforming configuration needs a larger scale and modulus and every cost in Section V-E would move with them. EIC, R1, R2 and R3 recommend Major Revision, and each states that nothing found invalidates the construction.

**Ruling: Major Revision.** The DA rationale is not insufficient and it is not dismissed. It is the reason two roadmap items carry a measurement requirement and the reason the abstract's "cryptographically secure" cannot survive unchanged. It does not reach Reject because the panel is unanimous that the construction, the implementation and the selection rule are sound, because R2 owns the cryptographic seat and rated the same material CRITICAL while recommending Major Revision with a stated repair, and because the standards reserve Reject for a fundamental unfixable failure. **Condition attached.** If re-measurement at a conforming smudging parameter and under a public norm bound moves the Section V-E figures materially, the abstract, the cost discussion and the comparison paragraph all change, and the revision will be handled as a substantially new submission rather than as a response letter. The authors should plan for that outcome rather than discover it.

### D2. Severity of the smudging gap. R2 and DA at CRITICAL, three seats silent.

**Ruling: the finding stands at CRITICAL, and silence is not dissent.** R1 states that it defers the cryptographic merits to R2. R3 states that it does not assess proofs. EIC states that the proofs belong to other seats and that it did not adjudicate them. Expertise-first arbitration places this squarely with R2, which is the cryptography seat and which filed it at CRITICAL with the citations. The panel's counting rule would record it as a single-reviewer finding, and that label would misdescribe it, so it is recorded here instead as an in-remit finding by the owning seat, corroborated by the Devil's Advocate.

### D3. Whether A_sel is tabulated. R1 and DA against the manuscript.

R1's summary states that A_sel appears in no table of the submission. DA's summary states that it is not derivable from any table in either document. Table II carries an explicit A_sel column with four values.

**Ruling: the memo governs and both summaries are corrected to the narrow form.** Table I, the five-task headline table from which the abstract's range is drawn, has no A_sel column. Table II has one. The corrected statement is narrower and equally damaging, because the abstract's range is a five-task range and Table I is where a referee will look. R1's finding body and DA's finding body both state the narrow form correctly, so the correction touches the summaries and not the analysis. The roadmap item is written against the narrow form and the authors are asked to answer the narrow form.

### D4. Whether the level-restoration ambiguity is a reporting defect or a correctness defect. R1 and R3 against R2.

R1 F9 and R3 W2 treat it as a disclosure and cost-reporting failure. R2 F3 treats it as a correctness failure, because Section IV-D's provenance argument requires deterministic level restoration, collective refresh is interactive and injects fresh randomness from every participant, and the submission's own Figure 2(d) is captioned under collective refresh.

**Ruling: R2's reading governs and subsumes the others.** Expertise-first. The repair therefore has to do more than label the figures. Section III-C must state which mechanism the protocol specifies, and Section IV-D's determinism claim must be made conditional on it. Labelling the numbers alone would leave a printed argument that is false under the mechanism the paper's only cost figure was measured with.

### D5. The remedy for the extraction law. R1 against R2, R3 and DA.

R1 F7 requires a new sweep at a second feature dimension, because with d fixed at 768 the exponent on d is assumed rather than estimated and the formula's whole purpose is transfer to a deployment's own d. R2 F8, R3 W1 and DA C5 require the existing numbers and the existing caveat to be carried into the submission and do not require a new sweep.

**Ruling: the remedies are ordered, not exclusive, and the split resolves as a choice the authors make.** Moving the two allowance numbers and the wrong-side caveat into Section V-F is blocking, because it is the operational half of the paper's own two-part security claim. Identifying the exponent on d is not blocking, because the authors have a cheaper alternative that answers R1's objection: restrict the stated scope of the law to the range in which it was validated, one backbone at d = 768 and three tasks, and drop the unrestricted phrase "a deployment can therefore set its allowance from C, d". What the paper may not do is keep the unrestricted operational rule without either the sweep or the restriction. R1's third point, that the residuals on C change sign so the law is not reliably conservative, is unresolved on the evidence before the panel and the authors must answer it.

### D6. Venue fit and its remedy. EIC and R3, no conflict on the finding, different remedies.

EIC judges scope PARTLY_MEETS, notes that TNSE's practice is more permissive than its scope text, and offers two remedies: promote the client-scaling and threshold-availability material into a first-class contribution, or take the paper to IEEE TIFS or PoPETs. R3 judges TNSE value PARTLY_MEETS and asks for one measured point at t < N and a latency model naming the round trips. R1, R2 and DA do not assess venue.

**Ruling: the remedies are compatible and the reframing needs R3's measurement to be substantive.** Author autonomy on the venue itself. If the authors stay at TNSE, the material EIC names is already measured in the report and the reframing is honest rather than cosmetic, and R3's single t < N point is what turns it from a restatement into a result. If they decline the reframing, EIC's alternative venues are on the record and the editor does not overrule that judgement.

### D7. Whether the deployment framing should change. R3 alone, unopposed.

R3 W6 argues that the AI Act obligations on a high-risk system pull against an unreadable model, and that the design's clean case is the commercial consortium. R3 marks its own reading heuristic and states it is not a lawyer. EIC W12 raises the adjacent question of whether the delivered accuracy is deployable in the settings the introduction names. No seat disputes either.

**Ruling: author autonomy on the framing, with one obligation.** The paper may keep the regulatory motivation. If it does, it must answer in two sentences what a deployer does about auditability and human oversight when no party can read the model, because that is the first question a referee from that world asks and R3's point is unanswered in either document. This is SHOULD FIX, not blocking.

---

## 5. Revision roadmap

Ordered by what blocks the submission. Each item names what is wrong, the seat that found it, the severity that seat assigned, and the smallest change that answers it.

Two markers are attached to every item and they are independent. The obligation marker is BLOCKING, SHOULD FIX, or OPTIONAL. The effort marker says what kind of work the fix is, and this is the distinction the authors should read first:

- **WRITING.** New or corrected text in the submission. No number changes and nothing is measured.
- **MOVE.** A number or a sentence that already exists in the technical report and must be carried into the ten pages. No new work at all.
- **RE-ANALYSIS.** Recomputation from result records that already exist. No new runs.
- **MEASURE.** A new experimental run.

### BLOCKING

The paper cannot go out with any of these unresolved. Every one of the twelve is a case in which a printed statement in the ten pages is false, unsupported, or missing a caveat the authors have already written.

| # | What is wrong | Seat and severity | Smallest fix | Effort |
|---|---|---|---|---|
| B1 | Theorem 1 names IND-CPA as its only hypothesis. The collective key-switch and collective-refresh simulators are not implied by IND-CPA, they need smudging noise dominating the ciphertext noise, and the report states that the measured configuration does not satisfy that and that the recommended 2^25 value does not either. The submission contains no occurrence of smudging, flooding, Micciancio or Checri. | R2 F1 CRITICAL, DA C1 CRITICAL, editor-verified memo 4 | Add the simulatability hypothesis to Theorem 1 and state the smudging parameter as a number. Disclose the gap in three or four sentences in Section IV. Cite Li and Micciancio (EUROCRYPT 2021) and Checri et al. (CRYPTO 2024) in the ten pages. Qualify "cryptographically secure" in the abstract to what the measured configuration supports. | WRITING |
| B2 | The duplicate-query check that the report calls a required control is not in Algorithm 1 or Functionality 1, and Definition 1 permits the adversary to corrupt the server that would enforce it. | R2 F1 point 3, DA C1 point 3 | Put the check into Algorithm 1 and into Functionality 1 step 3, and state who enforces it against an adversary that includes the server. | WRITING |
| B3 | Definition 2 grants the adversary arbitrary deviation in the shares its clients contribute, which on a natural reading includes key-generation shares. A party that publishes last subtracts the others and holds the collective secret alone, so its advantage is 1/2 and Theorem 2 fails inside its own game. The standard commitment round is not in the protocol. | R2 F2 MAJOR | One sentence adding the commit-then-open round to Section II-A or Section III, or an explicit exclusion of key-generation deviation from Definition 2. State which. | WRITING |
| B4 | The abstract states 48.9 to 176.6 s with GPU acceleration in the same clause and the same form as the measured range. Nothing in the ten pages supports it. The report derives it by substituting one H100 bootstrap timing of 2.28 s and leaving the dominant local evaluation unported. | EIC W2 Major, R1 F9(4) MAJOR, R3 W3 Major, DA M5 MAJOR, editor-verified memo 1 | Delete it from the abstract, or mark it a projection there and add the substitution, the hardware and the report's own caveat to Section V-E in two sentences. | WRITING, or MOVE if the derivation is carried over |
| B5 | Section V-G states that A_dis minus A_sel runs from 0.029 to 0.136 and the abstract inherits it as 0.03 to 0.14. Table I has no A_sel column and its own columns give 0.090 and 0.010 on the two endpoint tasks. | R1 F2 MAJOR, R3 W10(b) Minor, DA C3 CRITICAL partly validated, editor-verified memo 3 | Add an A_sel column to Table I with the per-task values, and one caption sentence saying that selection is made per seed so A_sel can differ from either column mean. | MOVE, the five values are in the report's Section V-G |
| B6 | The level-restoration mechanism is never named. Section V-E's 400.8 s and 1468.3 s are server-side bootstrapping, Figure 2 panel (d) is captioned under collective refresh, and the two differ by a factor of thirteen. The parameter sentence names 2^14 and 2^15 while the headline circuit runs at 2^16. Section IV-D's provenance argument holds only under the deterministic mechanism. | R1 F9(1)(2) MAJOR, R2 F3 MAJOR, R3 W2(1)(2) Major, DA M6 MAJOR | Name server-side bootstrapping under collectively generated keys as the specified mechanism in Section II-A or III-C. Say which mechanism produced each quoted figure. Relabel or redraw Figure 2(d). Correct the ring-degree sentence to include 2^16. Make the Section IV-D determinism claim conditional on the specified mechanism. | WRITING plus MOVE, the report's Table VII carries both columns |
| B7 | Section IV-D describes the provenance check in the present indicative, immediately after Proposition 1 opens the gap. The report says "we implement neither". The sampling argument that makes the check affordable is also dropped, which leaves a reader assuming a full re-execution per query. | R2 F3 MAJOR, R3 W5 Major, DA M11 MAJOR | Restore "we implement neither". Add the p = 0.01 sampling clause with its escape probability, and one clause naming the deviation class it does not catch. | MOVE, all three sentences exist in the report |
| B8 | Section V-F gives an operational rule for setting the allowance and never gives the allowance a number, and drops the report's own statement that the measured figures bound the allowance from the wrong side. | R2 F8 MAJOR, R3 W1 Major, DA C5 CRITICAL validated, R1 F7 MAJOR, editor-verified memo 2 | Two numbers into Section V-F, roughly 1.3e3 per client on AG-News and 2.2e4 on Banking77 at N = 10, plus the one-sentence wrong-side caveat. Either restrict the law's stated scope to the validated range or drop the unrestricted "set its allowance from C, d" phrasing. | MOVE plus WRITING |
| B9 | Section V-A states that every number is the mean over three seeds, and the report's own captions say Figure panels (a) and (c) are single-seed. Section V-B(a) gives 0.789 and 0.803 for DBpedia at the same default configuration in adjacent sentences. The Table I caption asserts N = 10 while the report discloses an effective federation of seven on AG-News and nine on TREC on one seed, and 17 to 19 rather than 20 at the Table II alpha = 0.04 row. | EIC W3 Major, R1 F3 MAJOR, DA M2 and M3 MAJOR, editor-verified memo 7 | Restore both caption sentences verbatim. Correct Section V-A so the three-seed claim is scoped. Mark the single-seed panels in the Figure 2 caption. State the sample-count drop rule and its threshold in Section V-A. | MOVE plus WRITING |
| B10 | No bit-security level, total modulus, or secret distribution is stated for any parameter set. Every theorem is stated with negl(lambda) and lambda is never instantiated. | R2 F14 MAJOR, R1 F12 MAJOR, editor-verified memo 8 | One line per chain: ring degree, log Q, scale, secret distribution, claimed classical bit security, and the standard table or estimator used. Say which of these moves if B1's smudging fix needs a larger scale. | WRITING if the parameters already meet a published table, otherwise a short estimator run |
| B11 | Section II-A states that any t clients form a quorum so serving does not require every client online, and the same page states that the implementation instantiates t = N, under which one absent client blocks every query. Availability is not among the three limitations. | EIC W4 Major, R2 F7 MAJOR, R3 W4 Major, DA M4 MAJOR | One sentence in Section V-H in the report's own words, and one clause in Section II-A saying the measured configuration is t = N. Correct the per-query traffic formula from N to t. Cite Mouchet, Bertrand and Hubaux (Journal of Cryptology 2023) for the t-out-of-N structure rather than the PoPETs 2021 paper. | MOVE plus WRITING |
| B12 | The serving circuit's scaling constant was fixed from the exported plaintext head, which the deployed protocol cannot do because the head is a ciphertext. Every latency figure, the 7.3e-5 correctness figure and the thirty-two-query agreement were obtained under that calibration. The submission's Section V-H does not list it. | DA C2 CRITICAL validated, editor-verified memo 5 | Add it to Section V-H as a fourth limitation, in the report's own words, saying that a deployment needs a public bound on the head's norm instead and that the cost of a loose one is not measured. | MOVE |

### SHOULD FIX

A referee will raise each of these. None of them makes a printed statement false, which is why they sit below the line.

| # | What is wrong | Seat and severity | Smallest fix | Effort |
|---|---|---|---|---|
| S1 | Every accuracy is a three-seed mean reported to three decimals with no standard deviation, no interval and no test, and named conclusions ride on differences of 0.026 and 0.003. | R1 F1 MAJOR | Report mean with standard deviation or min-max for every cell of Tables I and II. Report each asserted difference as a paired seed-level difference. | RE-ANALYSIS from existing per-cell records. MEASURE only for the recommendation to raise the seed count to five, or ten where a difference is below 0.05 |
| S2 | Table I is captioned "accuracy on the global test set" and the measurement is an undisclosed subsample, at most 5,000 test examples per text task and 2,000 per vision task, on the same page as a Table II caption announcing the whole 10,000-image test set. | R1 F4 MAJOR | State the test-set size per task in Section V-A or the Table I caption. | WRITING to disclose, MEASURE to evaluate DBpedia, AG-News and CIFAR-100 on their full test sets |
| S3 | The selection rule's only baseline is arithmetically the constant rule "always serve the personal adapter", the complementary constant is never reported and scores 19 of 27 on the report's own counts, and the 27 cells are 9 settings at 3 seeds with the choice stable across seeds. | R1 F5 MAJOR | Add both constant rules with their regret, report at the setting level, and add one debiased-vote baseline using the 0.28 bias the report already measured. | RE-ANALYSIS from existing records |
| S4 | Section V-D reports 0.470 and 0.021 as what a wrong choice gives up. The report's Table V caption defines them as sums over nine settings, and the two numbers come from different rules. | R1 F6 MAJOR, DA M8 MAJOR | Restate as summed regret over nine settings and quote one rule's pair, or give the per-error costs. | WRITING |
| S5 | The submission asserts a membership null with no attack named, no candidate count and no power statement. The report's own design resolves nothing below FPR 1e-3 and holds the coverage pattern fixed. | R1 F8 MAJOR, corroborating DA C4 | State the attack, the candidate count and the detectable effect in Section V-F. Report TPR at fixed FPR with intervals. | MOVE for the design, MEASURE to raise the candidate count until FPR 1e-3 resolves a rate |
| S6 | The coverage channel. For a singly covered class the encrypted denominator cancels and the merged row is that client's own displacement, and the support of the coverage pattern is recoverable from an extracted head. Section V-F's "only remaining channel" sentence is incomplete. | DA C4 CRITICAL partly validated, editor-confirmed against equation (1) | Amend the sentence, state what the encrypted reciprocal does and does not buy under single coverage, and either restrict Theorem 2 to matched class support or measure a coverage-inference adversary. | WRITING for the restriction, MEASURE for the adversary |
| S7 | The ideal functionality executes the protocol's training algorithm rather than abstracting the task, and local training is randomized so the ideal experiment is not pinned down by the inputs. | R2 F5 MAJOR | State F over the merged linear map with local training as an input-generation step outside F, or keep the present form and say in one sentence what that costs the reading of Theorem 1. | WRITING |
| S8 | The leakage set omits the per-query pattern that every quorum member observes, so the simulator is unconstructible in the sub-case where the server is honest and only clients are corrupted. | R2 F6 MAJOR | Add the query pattern to L and deliver Done to every party, as the protocol does. One sentence saying why that leakage is acceptable. | WRITING |
| S9 | Proposition 1 proves that content-based gating is impossible and the following sentence concludes that no protocol of this message pattern realizes F, which the paper's own next paragraph refutes. | R2 F10 MAJOR | Weaken the sentence to what is proven and name provenance or verifiable evaluation as the mechanism outside the message pattern. | WRITING |
| S10 | The encrypted reciprocal is under-specified where it is hard. A class no client holds has denominator zero, and the inversion circuit needs a public scaling constant whose bound would have to come from the totals the design refuses to decrypt. | R2 F9, status open | State the floor or masking rule for a zero total, the public scaling constant and the interval, and the range over which the 1.9e-8 relative error was measured. | WRITING |
| S11 | Six cryptographic references required by findings above are absent from the ten pages: Li and Micciancio, Checri et al., Li, Micciancio, Schultz and Sorrell, Mouchet, Bertrand and Hubaux, Viand, Knabenhans and Hithnawi, and Jagielski et al. for the fidelity definition. | R2 F15 MAJOR | Add them. | WRITING |
| S12 | The nearest prior art to the priority claim, the one scheme that is at once one-shot, federated and encrypted, appears only in the companion. | EIC W6 Major | Restore the sentence and the citation to Section VI-C. Two lines. | MOVE |
| S13 | The measured selection cost is report-only and it is the largest one-time cost in the protocol. The measurement was taken under collective refresh, which is not the mechanism the protocol specifies, and the specified mechanism is unmeasured for this step. | EIC W5 Major, R3 W2(4) Major, DA M1 MAJOR, editor-verified memo 6 | Give the measured figures in Section V-E with their configuration, say which mechanism produced them, and say that the specified mechanism was not measured for this step. | MOVE plus WRITING |
| S14 | Setup is reported as 344 MiB per client and omits the 8.70 GiB of bootstrapping keys the specified design requires, understating one-time federation cost by roughly 3.5 times. | R3 W2(3) Major | Add the bootstrapping keys to the setup line. | MOVE |
| S15 | No point other than t = N was measured, and the availability against allowance trade is a clean result the paper does not own. | EIC question 6, R3 W4 Major, DA question 11 | One measured point at t < N, for instance t = 7 at N = 10, with per-query traffic and the resulting allowance beside the t = N figures. | MEASURE |
| S16 | The extraction scaling law fixes d at 768 in every cell, so the exponent on d is assumed rather than estimated, and the residuals on C change sign so the law is not reliably conservative. | R1 F7 MAJOR | Either run the sweep at a second feature dimension, or restrict the law's stated scope to the validated range and derive the allowance from a conservative multiple. Answer the sign-change point either way. | MEASURE, or WRITING for the restriction |
| S17 | Timings are single-run wall clock with no processor model, no clock, no memory and no Lattigo version, and are quoted to four significant figures in the abstract. | R1 F9(3) MAJOR, R3 W9 Minor | Name the processor and its clock, pin the library version, report the median and spread of at least five runs, and drop to three significant figures. | MEASURE, a repeat of existing runs |
| S18 | An independent group could not rerun this. Neither document states the optimizer, learning rate, batch size, what a step is, the LoRA scaling factor, how theta_0 is produced, how the adapters are aggregated for A_dis, the pooled training budget, or any artifact availability statement. | R1 F12 MAJOR | A hyperparameter table in the technical report with a pointer from Section V-A, and a code and data availability statement. | WRITING |
| S19 | The claim that the backbone cancels in the cross-paper comparison is asserted, the quantity the paper contributes to that comparison is zero by construction rather than by measurement, and Table II carries no peer column. | R1 F11 MAJOR | Put the peers' published numbers in Table II. State that the cryptographic protection cost is zero by construction and is therefore not an empirical finding. Retire "the backbone cancels" or support it. | WRITING, plus MEASURE for the one ResNet-18 run that would support it |
| S20 | The per-query cost is given with no comparative anchor, and every omitted comparator latency is faster than this protocol's. | EIC W9 Minor, DA M7 MAJOR | One sentence in Section V-E naming slytHErin's figure and the conditions that separate the systems. | MOVE |
| S21 | Fit to TNSE is thin as written, and the results that would earn the venue, client scaling and the threshold availability trade, exist and were cut. | EIC W4 Major, R3 venue judgement | Promote the client-scaling and threshold-availability material into a first-class contribution and say in Section I what the protocol costs as the federation grows and as parties go offline. Depends on S15. | MOVE plus WRITING |
| S22 | The submission's Section III-C(c) uses the hard-label extraction citation to imply a hardness whose scope excludes a single linear map, and the paper's own Section V-F measures three to five queries per parameter. | R2 F4 MAJOR | Replace "markedly harder" with what Section V-F measures. The honest claim is available and is not weak. See section 6 below. | WRITING |
| S23 | The federation is closed after key generation. Neither document contains join, leave, revoke or re-key, and the key material and the encrypted head are bound to one fixed party set. | R3 W7 Minor | One sentence in Section V-H with the cost of a fresh setup and re-aggregation. Cite proactive secret sharing if it applies. | WRITING |
| S24 | The introduction motivates with three deployments whose regulatory obligations pull against an unreadable model, and never names the commercial-consortium case the design fits cleanly. | R3 W6 Major | Either lead with the consortium case, or add two sentences on what a deployer does about auditability and human oversight when no party can read the model. | WRITING |
| S25 | The design space is restricted without argument. A trusted execution environment and a secret-sharing comparison both answer the same requirement, and the comparison is 97 to 99 per cent of the query cost. | DA M10 MAJOR | One paragraph in Section III-A or Section VI stating why threshold CKKS rather than a TEE and rather than a secret-sharing comparison. | WRITING |
| S26 | The decoder vocabulary projection is named as an instance of the construction and the paper's own cost scaling forbids it at present cost. | DA M9 MAJOR | Drop the instance or state the scaling that rules it out. | WRITING |
| S27 | Theorem 2's proof sketch lists four items, declares all four independent of b, and then says the fourth is what remains. | R2 F11 MINOR | One word. | WRITING |
| S28 | Functionality 1 specifies an exact argmax and the protocol realizes an approximate one, with no correctness-error term in Theorem 1. | R2 F12 MINOR | Add the correctness error to the theorem as an additive term and report the minimum observed top-two logit gap beside the 7.3e-5. | WRITING plus RE-ANALYSIS |
| S29 | "The per-client sample counts n_j" in the leakage set is ambiguous against the notation g_{j,c} = n_{j,c}, and the reading decides whether the encrypted reciprocal protects anything. | R2 F13 MINOR | Write the leakage as the totals explicitly, and add the report's sentence explaining why the equal-size restriction in Definition 2 exists. | WRITING |
| S30 | The report gives 2.0 MiB per participating client for key-switch traffic in one place and 0.5 MiB implied by 8.5 + 0.5N in another, a fourfold disagreement that doubles the per-query total. | R3 W10(a) Minor | Reconcile, or state the condition that separates them at both sites. | RE-ANALYSIS |

### OPTIONAL

| # | What is wrong | Seat and severity | Effort |
|---|---|---|---|
| O1 | The title names no distinguishing property and fits equally the protocol the paper spends ten pages declining to build. | EIC W7 Minor | WRITING |
| O2 | The abstract's accuracy figures do not name the partition, which is the hardest configuration in the paper, so the headline is the pessimistic end of a measured range. | EIC W8 Minor | WRITING |
| O3 | The "first" is a four-clause conjunction and the deltas against POSEIDON and slytHErin are never stated as deltas. | EIC W10 Minor, R2 F16 MINOR, DA N4 MINOR | WRITING |
| O4 | Table III has a blank cell whose explanation was cut from the caption. | EIC W11 Minor | MOVE |
| O5 | The pooled column of Table I is inert. Section V-A promises the A_pool minus A_dis comparison and the submission never reports it, and the CIFAR-100 pooled cell is a bare em dash with its explanation cut. | EIC W12 Minor, R1 F13 MINOR, DA N1 MINOR | MOVE, or MEASURE for the one CIFAR-100 pooled run |
| O6 | Accuracies are reported to three decimals on a 500-example test set, and latencies to four significant figures from single runs. | R1 F14 MINOR | WRITING |
| O7 | One numeric range, 0.61 to 0.79, names A_sel in the abstract and the shared-head column in Section V-B. | R1 F15 MINOR | WRITING |
| O8 | Fidelity is not normalised against the free majority-class baseline, which differs sixfold across the extraction tasks. | R1 F16 MINOR | RE-ANALYSIS |
| O9 | Extraction, randomised response, LiRA and OSLO are measured on text only, and Section V-F states its claims without that scope. | R1 F17 MINOR | WRITING for the scope note, MEASURE to add CIFAR-100 |
| O10 | d is never given a value in the submission although the allowance formula is presented as operational guidance. | R1 F18 SUGGESTION | WRITING |
| O11 | Table II's printed differences do not equal the differences of its printed columns, which is correct practice with no note. | R1 F19 SUGGESTION | WRITING |
| O12 | "Multiparty computation" is an index term and no MPC construction appears in the paper. | DA N2 MINOR | WRITING |
| O13 | Section V-C opens "the protocol gives up no accuracy for protecting the contributions" one paragraph before Section V-G reports 0.029 to 0.136 given up. | DA N3 MINOR | WRITING |
| O14 | Metering a logits interface rather than withholding it is never considered, although the report shows exact recovery at 769 logit queries against 1.2e4 to 2.0e5 label queries. | DA ignored alternative 4 | WRITING |

**Counts.** Twelve BLOCKING, thirty SHOULD FIX, fourteen OPTIONAL. Of the twelve blocking items, eight are pure WRITING or MOVE and need no new number, and none requires a new experimental run to reach the blocking standard. The two measurement campaigns the Devil's Advocate identified, re-measuring Section V-E at a conforming smudging parameter and re-running the serving path under a public norm bound, sit behind the strength of the claims rather than behind the disclosure, which is why they appear as the condition attached to ruling D1 and as items S6 and B12 rather than as blockers in their own right. The authors should read that as a choice, not as a reprieve. Keeping the unqualified claim requires the runs.

---

## 6. What the panel got right about a deliberate choice

Six findings are cases where the panel is probably describing a decision rather than an oversight. The technical report exists precisely so that ten pages can carry the argument and the companion can carry the proof, and the pattern of what was cut is consistent with a deliberate page budget rather than with concealment. The Devil's Advocate says as much in its own observations: the report states the smudging gap, the key recovery, the public constant, the availability cost, the wrong-side caveat, the dropped clients and the single-seed rows, so almost every finding is about what the ten pages omit and not about what the authors do not know.

That does not discharge the cost, and the referee's view is stated in each case, because a reviewer holding ten pages does not have the reasoning and cannot supply it.

1. **The two-document split itself.** Deliberate, and it is the reason the submission is ten pages. Referee's view, and this is the panel's only CONSENSUS-4 item: a referee is asked to accept Theorem 1, Theorem 2, a membership null and an extraction rate on sketches and bare sentences, and the paper's central security claims are exactly the ones a ten-page reader cannot check (EIC W1). The split is defensible. Deferring the proofs, the caveats and the numbers that qualify the headline is what costs.

2. **The arXiv placeholder.** The sequencing is deliberate, the report goes first and its identifier replaces the placeholder. Referee's view: the review happens before the placeholder resolves, so during review the companion does not exist for the referee, and every deferral is unavailable at the moment it is being tested (EIC W1). The cost falls entirely inside the review window, which is the one window the sequencing does not cover.

3. **The hard-label extraction claim, where the two documents differ on purpose.** The report explains that the cited hard-label results carry a factor exponential in hidden neurons which a single linear map does not have, and the submission keeps the shorter claim. Referee's view: R2 F4 read the submission's "markedly harder" as a citation used beyond the scope of the result it cites, and named the paper's own Section V-F measurement of three to five queries per parameter as the counterexample. A cryptography referee will reach the same place, because the shorter claim reads as an appeal to a hardness result rather than as a bounded statement. R2 also notes that the honest claim is available and is not weak, which is the cheapest path out.

4. **The selection cost, omitted rather than reported under the wrong mechanism.** The measurement exists only under collective refresh and the protocol specifies server-side bootstrapping, so neither pair is measured for the mechanism that is specified. Omitting it rather than reporting a mismatched number is a defensible instinct. Referee's view: three seats read the omission as selective, because the same paragraph reports a cost four hundred times smaller in mebibytes (EIC W5, R3 W2(4), DA M1). Reporting the measured pair with an explicit statement that the specified mechanism was not measured for this step is strictly better than silence, and it costs one clause.

5. **The GPU projection in the abstract.** It is the paper's honest answer to the obvious objection that twenty-four minutes a query is unusable, and R3 says so directly. Referee's view: four seats read it as a reporting fault regardless of intent, because the projected range sits in the same clause and the same grammatical form as the measured one, with nothing in the body to discover (EIC W2, R1 F9, R3 W3, DA M5). R3's remedy keeps the number and the benefit, by labelling it a projection and giving the substitution in Section V-E.

6. **Choosing the slower level-restoration mechanism for the headline latency.** The Devil's Advocate credits this explicitly as a choice against the paper's own interest, and so does its report on the negative disclosure charge at N = 20, alpha = 0.04. Referee's view: the credit is real and it survives, but the credit is destroyed by leaving Figure 2(d) captioned under the faster mechanism with no marker, because a referee reading page 7 against page 8 sees a thirteenfold contradiction and does not see the choice (R1 F9, R2 F3, R3 W2, DA M6). Naming both mechanisms converts a contradiction into the honest disclosure it already is.

---

## 7. Questions to the authors

Answer each in the response letter, at the location named. Every question traces to the seat given.

1. What does Theorem 1 prove about the system you measured, given that the implementation smudges at eight times the fresh-encryption noise and that you state the recommended 2^25 value also fails the 2^(lambda/2) rule? If a conforming configuration needs a larger scale and modulus, what happens to every figure in Section V-E and to the abstract? (R2 question 2, DA question 1)

2. Is the duplicate-query check part of the protocol? Definition 1 corrupts the server together with t-1 clients, so who enforces the check against that adversary? (R2 question 3, DA question 2)

3. Does Definition 2 admit deviation in key-generation shares? If it does, what prevents the last-publisher attack, and if the commitment round is intended, why is it not in the protocol description? (R2 F2)

4. On what basis does the abstract state 48.9 to 176.6 s beside a measured figure, given that the local evaluation was not ported and becomes the larger half of a query above four classes? Do you intend that clause to be read as reporting a measurement? (EIC question 2, R1 question 11, R3 W3, DA question 12)

5. Publish the per-task and per-seed A_sel values for Table I. How does a reader get from Table I's printed columns, which give 0.090 on AG-News and 0.010 on CIFAR-100, to the stated range of 0.029 to 0.136? (R1 question 1 and F2, DA questions 4 and 5, R3 question 10)

6. Which level-restoration mechanism produced 400.8 s and 1468.3 s, which produced Figure 2 panel (d), at what ring degrees, and how many runs is each latency the summary of? Does Section IV-D's determinism argument hold under the mechanism the protocol specifies? (R1 question 10, R2 question 1, R3 question 3, DA question 8)

7. What allowance Q do you recommend per evaluated task, in queries per client? Given your own statement that a cryptanalytic extractor costs logarithmically in the precision demanded, by what factor do you believe the measured allowance is too generous, and what safety factor should a deployment apply? (R1 question 8, R2 question 8, R3 question 2, DA question 7)

8. What is the classical bit security at each of the three ring degrees, at what log Q and secret distribution, and against which standard table or estimator? Which of those numbers moves if the smudging fix requires a larger scale? (R1 question 12, R2 question 7)

9. What is the sample-count threshold below which a client is dropped, where does it come from, and what were the effective federation sizes per task per seed in Table I and per row in Table II? (R1 question 3, EIC question 4, DA M3)

10. Section V-A says every number is the mean over three seeds and your own report says the client-count and local-step rows are one seed. Which sentence survives, and does the N = 10 to N = 50 scaling claim survive with it? (EIC question 4, DA question 9)

11. What is the standard deviation over seeds for each cell of Tables I and II? Specifically, does the CIFAR-100 shared-versus-personal difference of 0.026 hold on all three seeds, and does the alpha = 0.04 charge of -0.003 have a consistent sign? (R1 question 1)

12. How does the constant rule "always serve the shared head" score on the 27 cells and on regret, and how does the held-out vote score once the personal arrangement's measured accuracy is debiased by the 0.28 you already measured? Is 0.470 the summed regret over nine settings, and if so what does a single wrong choice actually cost? (R1 questions 5 and 6, DA M8)

13. Rerun the end-to-end correctness and latency measurements with the serving circuit's scaling constant derived from a public norm bound rather than from the exported head. What is the resulting precision and latency? (DA question 3)

14. For a class held by exactly one client the denominator cancels and the merged row is that client's own displacement. What does encrypting the reciprocal buy for that row, and what is the coverage-inference advantage of a coalition that extracts the head on shadow federations that vary the partition rather than holding it fixed? (DA question 6, corroborated by R1 F8)

15. How does the aggregation circuit behave when a class total is zero, what public constant scales the denominator into the inversion circuit's domain, and over what range of per-class totals was the 1.9e-8 relative error measured? (R2 question 4)

16. When the server is honest and only clients are corrupted, where does the simulator learn how many honest-client queries occurred, given that F sends Done to the server alone while the real protocol requires a quorum key switch per query? (R2 question 6)

17. Have you run any point at t < N? At t = N a single unavailable client blocks every query. What are the traffic, the allowance and the availability at a threshold that tolerates churn, and will you state the t = N availability in Section V-H in your report's own words? (EIC question 6, R3 question 6, DA question 11)

18. What is the total one-time setup cost of a ten-client federation including the 8.70 GiB of bootstrapping keys, and what is the measured selection cost under the mechanism the protocol specifies? (R3 questions 4 and 5, EIC question 3, DA question 8)

19. How does a member join or leave, and how is a compromised key share rotated? Does the query allowance reset when the federation retrains, given that a second run over the same partition produces a correlated head? (R3 questions 7 and 8)

20. Why threshold CKKS rather than a trusted execution environment, and why an encrypted argmax rather than a secret-sharing comparison, given that the comparison is 97 to 99 per cent of your query cost? (DA question 10)

21. What does the extraction law predict at a feature dimension other than 768, and on what evidence? Has the fit been validated at any d other than 768? (R1 question 7)

22. What true-positive rate at a false-positive rate of 1e-3 would the membership experiment have detected, and has the LiRA AUC been shown to saturate at 64 shadow federations? (R1 question 9)

23. Why does the ten-page related work omit the one prior scheme that is at once one-shot, federated and encrypted, and how do you want a referee to test the priority claim without it? (EIC question 5)

24. Would you reframe the paper around client scaling and threshold availability for this venue, and would you reframe the motivation around a consortium that must prevent its own members from taking the model rather than around the AI Act? If not, have you considered whether IEEE TIFS or PoPETs is the better home for the contribution as it stands? (EIC questions 7 and 8, R3 question 9)

25. Will the training code, the Lattigo protocol code, the partition seeds and the per-cell result files be released? (R1 question 13)

---

## Appendix. Seat summaries

| Seat | Recommendation | Confidence | One-sentence position |
|---|---|---|---|
| Journal-Fit (EIC) | Major Revision | 4 | The contribution is a real composition, but the ten pages are not a checkable standalone document and the results that would earn TNSE were cut into the companion. |
| R1 Methodology | Major Revision | not stated per report | The construction is real and the experimental section is not yet reportable: three seeds, no dispersion statistic anywhere, and a referee holding only the submission cannot check a single headline number in the abstract. |
| R2 Domain | Major Revision | 5 on CKKS and simulation-based security, 4 on literature, 3 on the aggregation circuit | The construction is sensible and the security section does not hold up as written, because the companion carries a key-recovery attack inside the stated threat model and an admitted unmet hypothesis that never reach the ten pages. |
| R3 Perspective | Major Revision | 4 | The protocol is a real system and the ten pages do not let a reader work out what running it costs, and the availability posture is the limitation this venue cares about most and the one the Scope section drops. |
| Devil's Advocate | Reject, findings only | not stated per report | The paper is honest in its companion and selective in its submission, and the selection runs in one direction. |
