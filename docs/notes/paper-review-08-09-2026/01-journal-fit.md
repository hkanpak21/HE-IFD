# Journal-Fit Review — HE-OFT (IEEE TNSE)

**Seat**: Journal-Fit Reviewer (`EIC`). **Configured identity**: TNSE associate editor, network security and distributed systems.
**Date**: 2026-09-08. **Manuscript**: `SUBMISSION.txt`, ten pages. **Companion consulted**: `TECHNICAL-REPORT.txt`, twenty-four pages.

## Summary and recommendation

1. The paper builds a one-shot federated fine-tuning protocol under multiparty CKKS in which no party ever holds the trained head in plaintext, and it implements the cryptography rather than simulating it.
2. The contribution is a real composition, not a repackaging, but it is narrower than the abstract implies, and the ten-page version withholds the prior work against which its "first" claim would be tested.
3. The submission is not a checkable standalone document: every proof, the whole threat quantification, the closest prior art and the qualifications on the headline table live in a companion cited as `arXiv:XXXX.XXXXX`, which no referee can obtain.
4. Fit to TNSE is defensible on the journal's practice but thin as written, and the results that would earn the venue — traffic and latency scaling in the number of clients, the threshold availability trade-off, the measured selection cost — were cut from the submission and survive only in the report.
5. The abstract states a GPU latency that appears nowhere in the ten pages and that the report shows to be a projection with its dominant component unported.

**Recommendation: Major Revision.**
**Confidence: 4** — journal fit, originality and significance are my remit; the proofs and the statistics belong to other seats and I did not adjudicate them.
**Calibration Status: `NOT_CALIBRATED`.**

Note on BRIEF rule 7: I found nothing inside either document that reads as an instruction to a reviewer. The acknowledgment discloses LLM assistance for shortening sentences and correcting grammar. That is a disclosure IEEE requires, not a defect, and I treated it as neither.

## Criterion-bound judgements

| Dimension / criterion | Criterion source | Judgement | Evidence anchors | Rationale | Uncertainty or scope limit | Decision bearing? |
|---|---|---|---|---|---|---|
| Scope: network science / network engineering / networked systems | TNSE scope statement; panel BRIEF § The venue | PARTLY_MEETS | `absence: SUBMISSION §V-E — expected any result indexed on network structure, topology, or client scaling as a contribution; checked §I contributions list, §V-E Communication, Fig. 2 panels (a)-(d), Table I, Table II` | The security-and-privacy clause of the remit admits the paper; nothing in the ten pages studies a network. The topology is one server and N ≤ 50 clients, and N enters only as a nuisance parameter | TNSE publishes privacy-preserving FL routinely, so precedent is more permissive than the scope text | Yes — sets the framing repair, not a rejection |
| Originality against one-shot FL and encrypted FL | Panel BRIEF § What the paper claims; manuscript Table III | PARTLY_MEETS | `table: Table III, p. 9, rows POSEIDON / slytHErin / HE-OFT` | The four-clause conjunction is genuinely unoccupied, and the deltas over POSEIDON (one-shot, transformer scale, label-only) are real. The ten pages omit FedHEONN, the nearest one-shot-plus-encrypted scheme, which the report cites | I did not independently search beyond the two documents' reference lists | Yes — W6 |
| Standalone checkability of a ten-page submission | IEEE Transactions article-type expectation that a paper support its own claims | DOES_NOT_MEET | `text: p. 5 "Section IV of the technical report [24] gives every proof in full."` | Seven deferrals carry every proof, the δ measurement, every selection cell, the extraction study, the disclosure comparison, all three limitations and the survey, to a reference that does not resolve | The report does support the deferred claims; I verified that. A ten-page referee cannot | Yes — W1 |
| Abstract and introduction promise what the paper delivers | Panel BRIEF § Rules 3-4; manuscript abstract | DOES_NOT_MEET | `text: p. 1 "1468.3s on one core, or48.9to176.6s with GPU acceleration,"` | The GPU half of the headline latency is absent from the body, and the report derives it by substituting one bootstrap timing while leaving the dominant local evaluation unported | Whether the projection is sound is a methodology-seat question; that it is unmarked is mine | Yes — W2 |
| Significance to a TNSE readership | TNSE scope statement; manuscript §I motivation | PARTLY_MEETS | `table: Table I, p. 6, pooled column` | The lift over a client alone is real on all five tasks. The delivered accuracy sits 0.13 to 0.36 below centralised training on the four text tasks, and the paper does not ask whether that is deployable in the regulated settings it names | Whether the gap is acceptable is domain-dependent and no reviewer settles it | Yes — W12 |
| Presentation, structure, title | Journal-Fit seat remit; manuscript title and §VI | PARTLY_MEETS | `text: p. 1 "HE-OFT: Privacy-Preserving One-Shot Federated Fine-Tuning under Homomorphic Encryption"` | Seven-section structure is sound and the prose is disciplined. The title names no distinguishing property; every word of it fits a protocol that decrypts the result at the end | Title preference is partly editorial taste | No — W7 is Minor |

These judgements are not totalled, weighted, or mapped to the recommendation.

## Strengths

**S1. The never-disclosure requirement is derived into a structural constraint, not asserted.**
`text: p. 3 "The trained quantity that is shared must therefore attach after the last nonlinearity. In a transformer, the only such point is the final linear map."`
Section III-B(b) turns a design choice into a consequence of C6, and §III-B then separates the *position* of the map from the task it serves. This is the paper's best paragraph and it is why the construction reads as forced rather than convenient.

**S2. The selection estimator, and the negative result that motivates it.**
`text: p. 7 "picks correctly in8of27cells"`
Choosing between two arrangements neither of which may be decrypted is a real problem with no obvious answer, and the paper shows the obvious answer is wrong for a structural reason, then supplies a parameter-free rule that decrypts one index. In my judgement this is the most transferable idea in the paper and the one it under-sells.

**S3. Proposition 1 explains why the honest-server assumption is necessary rather than convenient.**
`text: p. 6 "An honest client therefore releases its share for both plain-texts or for neither."`
Work in this area usually asserts a semi-honest server. Deriving the impossibility of a plaintext gate from IND-CPA, and then giving the recomputation mechanism as the available repair, is a stronger and more honest treatment than the norm.

**S4. The cryptography is implemented and measured.**
`text: p. 7 "We do not simulate the cryptography. We imple-ment the protocol in real multiparty CKKS on Lattigo"`
The report adds one end-to-end query on a recorded head with thirty-two encrypted answers matching plaintext (report §V-E(g)). That is the check most papers in this space skip.

**S5. Cross-paper comparison is handled with unusual restraint.**
`text: p. 7 "We do not present that margin as a result."`
Declining a 0.949-against-0.503 headline because the backbones differ, and comparing the accuracy each method concedes for protection instead, is the correct move and is rarely made.

## Findings, most severe first

### W1. The ten-page submission cannot be checked without a companion that does not resolve
**Severity**: Major | **Evidence Anchor**: `text: p. 10 "[24] H. I. Kanpak, S. Sav, and A. K" and p. 10 "arXiv preprint arXiv:XXXX.XXXXX, 2026."` | **Confidence**: 5 — editorial judgement on submission self-containment, squarely my seat.

**Location**: seven deferrals — §IV-B p. 5 (every proof), §IV-C p. 5 (δ and the derivation of Q), §V-D p. 7 (every selection cell), §V-F p. 8 (the extraction study), §V-G p. 8 (the per-task disclosure comparison), §V-H p. 8 (all three limitations "in full"), §VI p. 9 (the survey). Reference [24], p. 10.

**What is wrong**: two things, and only the first is clerical. First, the companion is cited by a placeholder identifier. A referee cannot obtain it and IEEE cannot publish the citation. Second, and not fixed by posting the report, the ten pages ask a referee to accept Theorem 1 and Theorem 2 on proof sketches, to accept "published membership attacks against it and against the head in plaintext both sit at chance" (§V-F, p. 8) on a bare sentence, and to accept the extraction rate of three to five queries per parameter without the table it comes from. The paper's central security claims are exactly the ones a ten-page reader cannot check. I confirmed the report does support each deferred claim, including the likelihood-ratio measurement at AUC 0.49 to 0.53 and the fidelity table; a referee reading ten pages has none of that.

**What would fix it**: post the report and insert the real identifier before the paper goes out. Then repatriate a minimum checkable set into the ten pages — the simulator construction for Theorem 1 in full, the extraction fidelity table, and the selection table — paying for the space by compressing §V-C, which spends most of a column establishing that cross-paper absolute accuracy is uninformative, and by cutting Table III to prose.

I record why I did not call this Critical: the report exists and substantiates what it is asked to substantiate, so the science is not invalidated, and the repair is a restructuring of ten pages rather than new work.

### W2. The abstract's GPU latency is a projection, stated as a measurement, and absent from the body
**Severity**: Major | **Evidence Anchor**: `text: p. 1 "1468.3s on one core, or48.9to176.6s with GPU acceleration,"` | **Confidence**: 5 — the word "GPU" occurs exactly once in the submission, in the abstract.

**Location**: abstract, p. 1. Section V-E, p. 7, where the body reports per-query cost and never mentions a GPU.

**What is wrong**: the abstract presents two latency ranges in one clause, joined by "or", with nothing distinguishing their epistemic status. The first is measured wall clock. The second is not measured at all. The report (§V-E(f)) derives it by substituting one H100 bootstrap timing of 2.28 s for the 23.1 s CPU level restoration and states plainly that "The local evaluation, which we did not port, is then the larger half of a query above four classes." So the projected 176.6 s is dominated by a component nobody ran on a GPU. The ten-page body never mentions the projection, so a referee cannot discover this, and the abstract is where the number will be read and quoted.

**What would fix it**: either drop the GPU range from the abstract, or mark it as a projection there and give the one-sentence derivation and its caveat in §V-E. The report's own wording — that no GPU library restores levels under collectively generated keys, so the figure has no published counterpart — belongs in the ten pages if the number does.

### W3. The ten-page cut removed caption qualifications that change how the headline numbers read
**Severity**: Major | **Evidence Anchor**: `table: Table I caption, p. 6, "THREE SEEDS,N= 10,α= 0.1"` | **Confidence**: 4 — I verified the two captions against each other; the statistical consequence belongs to the methodology seat.

**Location**: Table I caption, p. 6. Also Fig. 2 caption, p. 8, against §V-A, p. 6.

**What is wrong**: the report's corresponding Table II caption discloses that on one seed the Dirichlet draw assigns fewer than twenty samples to some clients, so the effective federation is seven on AG-News and nine on TREC. The submission's caption asserts N = 10 and drops the note. Separately, §V-A states "every number is the mean over three seeds", while the report's Fig. 4 caption discloses that panels (a) and (c) are a single seed; the submission's Fig. 2 caption drops that too, leaving §V-A's sentence false for two of the four panels. Both are qualifications the authors themselves wrote and then removed in the shorter document. A referee reading ten pages is given a cleaner table than the one that was measured.

**What would fix it**: restore both caption sentences verbatim. They cost two lines and they are the difference between a table a referee can read and a table a referee is misled by.

### W4. Fit to TNSE is thin as written, and the material that would establish it was cut
**Severity**: Major | **Evidence Anchor**: `absence: SUBMISSION §I contributions and §V — expected one result in which network structure, client scaling, or availability is the object of study rather than a parameter; checked the three bulleted contributions p. 1-2, §V-A setup, §V-E Communication, Fig. 2 panels (a)-(d)` | **Confidence**: 4 — scope judgement against the venue's remit is my seat; venue practice is more permissive than venue text.

**Location**: §I contributions, pp. 1-2. §V-E(b) Communication, p. 7. Fig. 2, p. 8.

**What is wrong**: the paper is applied cryptography plus federated learning. It contains no network science: no topology, no graph, no dynamics over structure, no communication-network model. The word "network" in the manuscript almost always means "neural network". TNSE's remit reaches this work through its security-and-privacy and distributed-computation clauses, and TNSE does publish privacy-preserving FL, so I do not call it out of scope. But the submission is the version of this paper *least* suited to TNSE, because the results that would earn the venue exist and were cut: the report separates the two axes that set the cost and shows per-query arithmetic answers to the ring degree alone while the key switch and its traffic answer to both, at 2.0 MiB per participating client; the report gives the t-out-of-N availability analysis, including that at t = N a single unavailable client blocks every query, and that lowering t buys liveness against a proportionate reduction in the query allowance; the report measures the selection cost across the client grid. Each of those is a networked-systems result about how the protocol behaves as a system of parties. None survives into the submission, where N appears only inside "8.5 + 0.5N MiB" and as an x-axis on Fig. 2(a).

**What would fix it**: promote the client-scaling and threshold-availability material into a first-class contribution and say in §I what the protocol costs as the federation grows and as parties go offline. That is an honest reframing, not a cosmetic one, because the material is already measured. If the authors decline, the honest answer is a different venue: IEEE TIFS or PoPETs is the natural home for the security contribution, and IEEE TPDS for the distributed-systems one. Given the shared reviewer pool noted in the panel brief, the reframing is also the response most likely to disarm a returning TDSC referee.

### W5. One one-time cost is reported in MiB and the other, two orders of magnitude larger, only as a comparison count
**Severity**: Major | **Evidence Anchor**: `text: p. 7 "selection costs at most2N Cencrypted comparisons, once, and serving costs traffic per query."` | **Confidence**: 4 — the asymmetry is visible in one paragraph of the submission and the withheld figure is in the report.

**Location**: §V-E(b), p. 7, which ends "Setup costs 344 MiB per client, once."

**What is wrong**: the same paragraph reports one one-time cost as a measured 344 MiB and the other as an upper bound on a comparison count. The report measures that second cost: 400 s and 3.4 GiB at five clients and four classes, rising to 7111 s and 145.4 GiB at twenty clients and a hundred classes, of which level restoration is 99.8 per cent of the traffic. A reader of the ten pages will take 344 MiB as the setup burden. The actual one-time burden at the paper's own upper configuration is over four hundred times that, and the paper's own report says so. For a networked-systems readership this is the most consequential number in the paper and it is the one withheld.

**What would fix it**: give the measured selection cost in §V-E with its configuration, and state whether it was measured under collective refresh or under the server-side bootstrapping the protocol specifies, since the report shows those differ by more than an order of magnitude in absolute latency for the related index measurement. One sentence and one clause. Reporting it also strengthens W4's case for the venue.

### W6. The nearest prior art to the novelty claim appears only in the companion
**Severity**: Major | **Evidence Anchor**: `absence: SUBMISSION §VI-C p. 8-9 — expected a citation of the one-shot, federated and homomorphically encrypted prior scheme the companion names; checked §VI-B Protecting Training with Cryptography, §VI-C One-Shot Federated Learning and Differential Privacy, §VI-E Secure Inference, Table III, and the full reference list pp. 9-10` | **Confidence**: 5 — I checked both reference lists directly.

**Location**: §VI-C, pp. 8-9, and the Positioning paragraph, p. 9.

**What is wrong**: the report's Positioning paragraph states that "A single prior scheme is at once one-shot, federated and encrypted, but only for a single-layer closed-form learner that cannot adapt a deep representation", citing FedHEONN. The submission's Positioning paragraph drops that sentence and the citation. The abstract claims "the first cryptographically secure one-shot federated fine-tuning protocol in which no party receives the trained result". A referee reading the ten pages is asked to accept a priority claim while the one prior work that occupies three of its four clauses has been removed from the document. The authors clearly know the distinction and state it well; withholding it from the shorter paper is the defect, not the claim.

**What would fix it**: restore the sentence and the citation to §VI-C. It costs two lines and it converts an unqualified "first" into a claim a referee can test, which is worth more to the authors than the space.

### W7. The title names none of the paper's distinguishing property
**Severity**: Minor | **Evidence Anchor**: `text: p. 1 "HE-OFT: Privacy-Preserving One-Shot Federated Fine-Tuning under Homomorphic Encryption"` | **Confidence**: 4 — editorial judgement on titling, partly taste.

**What is wrong**: every word of the title applies equally to a protocol that decrypts the trained result and hands it to the participants, which is precisely the design the paper spends ten pages declining to build. A reader scanning a table of contents cannot tell this paper from the one it argues against.

**What would fix it**: put the never-disclosure in the title. "One-Shot Federated Fine-Tuning Without Disclosing the Model" carries the contribution and drops nothing that matters.

### W8. The abstract's accuracy figures do not name the partition they were measured at
**Severity**: Minor | **Evidence Anchor**: `text: p. 1 "HE-OFT reaches0.61to0.79accuracy where a client training alone reaches0.20to0.48"` | **Confidence**: 4 — the partition is in the Table I caption, so the body is not misleading; the abstract is under-specified.

**What is wrong**: the figures are at N = 10 and α = 0.1, the hardest configuration in the paper. The report's sensitivity shows DBpedia moving from 0.789 at α = 0.1 to 0.970 at α = 1.0, so the headline is the low end of a range the paper measured. The traffic figure, 13.5 MiB, likewise resolves 8.5 + 0.5N at N = 10 without saying so.

**What would fix it**: add "at ten clients under a Dirichlet partition at α = 0.1" to the abstract. It makes the numbers better, not worse, because it tells the reader they are the pessimistic end.

### W9. The per-query cost is given without any comparative anchor
**Severity**: Minor | **Evidence Anchor**: `text: p. 7 "On one core a query takes400.8s at four classes and1468.3s at a hundred."` | **Confidence**: 4.

**What is wrong**: 1468.3 s is twenty-four minutes for one classification, and the ten pages give a reader nothing against which to judge it. The report supplies three anchors — slytHErin at 245.58 s for a twenty-layer network batched on twelve cores, POSEIDON at 0.38 s at ring degree 2^13 returning the prediction vector, and NEXUS at 54 s for the same argmax primitive single-key on thirty-two threads — together with the reason the comparisons size the setting rather than rank the systems. All three were cut.

**What would fix it**: restore one sentence naming slytHErin's figure and the observation that a system returning a label would pay the reduction that is ninety-seven per cent of this query. That sentence turns an alarming number into an interpretable one.

### W10. The "first" is a four-clause conjunction and the deltas are not stated as deltas
**Severity**: Minor | **Evidence Anchor**: `table: Table III, p. 9, POSEIDON row, "Model in plaintext: no"` | **Confidence**: 4.

**What is wrong**: the paper's own Table III shows POSEIDON already achieves a model no party holds in plaintext, and slytHErin already key-switches a prediction to the querier. The genuinely new part is the conjunction — one shot, at pretrained-transformer scale, with label-only output — and the paper never states it that way in the ten pages. §VI-B gives the POSEIDON delta in passing, as a cost argument. A reader assembles the claim rather than being handed it.

**What would fix it**: one sentence in §I or in the Positioning paragraph stating the three deltas against POSEIDON and the one against slytHErin explicitly. A precisely bounded first is more persuasive than an unqualified one.

### W11. Table III has a blank cell whose explanation was cut from the caption
**Severity**: Minor | **Evidence Anchor**: `table: Table III caption, p. 9, ending "providerMEANS ONE PARTY DOES WHILE THE QUERIER DOES NOT."` | **Confidence**: 3 — I read this from extracted text and cannot fully exclude a layout artifact, but the report's caption carries an explanatory sentence the submission's does not.

**What is wrong**: the report's caption for the same table explains that slytHErin and CryptPEFT serve a model they do not train, so their Rounds cell is empty. The submission's caption stops before that sentence, leaving an unexplained gap in a table whose purpose is to position the work.

**What would fix it**: restore the sentence.

### W12. The paper does not confront whether the delivered accuracy is deployable in the settings it invokes
**Severity**: Minor | **Evidence Anchor**: `table: Table I, p. 6, TREC row, servable 0.607 against pooled 0.967` | **Confidence**: 4 — significance judgement, my seat; the domain threshold is not mine to set.

**What is wrong**: §I motivates the work with health, biometrics and credit, where a regulated model may not be distributed. Table I shows the servable arrangement 0.13 to 0.36 below centralised training on the four text tasks. §V-A defines A_pool − A_dis as the price of the partition and then the submission never uses the decomposition in prose, so the pooled column sits in the table unread. The report does use it, and shows that on three of four text tasks the partition costs more than the never-disclosure does — which is the reassuring reading, and it was cut.

**What would fix it**: restore the two-sentence decomposition from the report's §V-G into §V-G of the submission. It answers the question a practitioner asks first and it exonerates the design for most of the gap.

## Questions for the authors

1. When will the technical report be posted, and will the ten-page paper carry a resolvable identifier at the time referees are asked to check Theorems 1 and 2? If the report is not posted, which proofs move into the paper?
2. On what basis is 48.9 to 176.6 s stated in the abstract alongside a measured figure? The report says the local evaluation was not ported and becomes the larger half of a query above four classes. Do you intend the abstract to be read as reporting a measurement?
3. What is the measured one-time selection cost, in time and in bytes, at each configuration the paper evaluates, and was it measured under collective refresh or under the server-side bootstrapping the protocol specifies? Why does §V-E report 344 MiB for setup and only a comparison count for selection?
4. Why were the effective-federation note on Table I and the single-seed note on Fig. 2 panels (a) and (c) removed, given that §V-A states every number is a three-seed mean?
5. Why does the ten-page related work omit FedHEONN, and how do you want a referee to test the priority claim without it?
6. The threshold is set to t = N in every measurement, so a single unavailable client blocks every query. What does the protocol cost at t < N, and would you make the availability-against-allowance trade-off a stated contribution rather than a limitation in the companion?
7. Would you reframe the paper around client scaling and threshold availability for this venue? If not, have you considered whether IEEE TIFS or PoPETs is the better fit for the contribution as it stands?
8. The title distinguishes the work from nothing. Would you name the never-disclosure in it?
