# Reviewer 2 — Domain Review (cryptography, secure computation for machine learning)

Manuscript: HE-OFT: Privacy-Preserving One-Shot Federated Fine-Tuning under Homomorphic Encryption
Venue: IEEE TNSE. Seat: security argument, theoretical framework, literature coverage, domain contribution.
Calibration status: NOT_CALIBRATED. Confidence in this seat's judgements: 5 on the CKKS and simulation-based-security findings, 4 on literature coverage, 3 on the aggregation-circuit gap.

## Summary and recommendation

The construction is sensible and the design chain in Section III-A is the best part of the paper: the requirement that the querier compute its own features does force the shared trained map to sit after the last nonlinearity, and the authors follow that constraint honestly instead of hiding it. The cryptography is real rather than simulated, and the cost figures are the kind of numbers this literature usually omits.

The security section does not hold up as written. The companion technical report contains a concrete key-recovery attack against the measured configuration, mounted by an adversary that Definition 1 explicitly admits, and states in the authors' own words that Theorem 1's simulation step "rests on a hypothesis our measured configuration does not satisfy." None of this appears in the ten pages. The submission asserts Theorem 1 with IND-CPA as its only hypothesis, cites nothing from the Li–Micciancio line, and does not mention smudging, noise flooding, or the duplicate-query control that the report calls "a required control and not a supplementary one."

Three further defects are the submission's alone: a rogue key-generation share breaks Theorem 2 as stated and the standard commitment round is never mentioned; the provenance check in Section IV-D is presented as available when the report says it is not implemented; and the hard-label extraction citation is used to imply a hardness that the report says does not apply to a single linear map.

The functionality has two repairable holes: it executes the training algorithm rather than abstracting the task, and its leakage set omits the per-query pattern that every quorum member necessarily observes, which makes the simulator unconstructible in the sub-case where the server stays honest.

**Recommendation: Major Revision.** The construction, the measurements and the selection rule are worth publishing. The security section needs its hypotheses stated, its known gaps disclosed inside the ten pages, and two protocol-level controls (commitment in key generation, duplicate-query rejection) written into the protocol rather than into a companion.

Integrity note: nothing in either document read as an instruction addressed to a reviewer. The acknowledgment discloses LLM use for copy-editing; I treat that as a disclosure and it does not bear on the assessment.

---

## Findings

### F1. Theorem 1 does not hold for the configuration the paper measures, and the submission does not say so — CRITICAL

**Location.** Submission §IV-B, Theorem 1 and proof sketch (p. 5); Abstract, "the first cryptographically secure one-shot federated fine-tuning protocol" (p. 1). Contradicted by Technical Report §IV-G (pp. 10–11).

**What is wrong.** Theorem 1 names exactly one hypothesis: "Assume the t-out-of-N threshold CKKS scheme is secure under chosen plaintext attack (IND-CPA) against an adversary holding t−1 key shares." The proof then invokes the multiparty scheme's collective key-switch and collective-refresh simulators. Those simulators are not implied by IND-CPA. They are correct only when the smudging noise dominates the noise of the ciphertext being switched, which Mouchet et al. set at 2^{λ/2} times the ciphertext noise. The report states plainly that this is unmet: the implementation "smudges at eight times the fresh-encryption noise, which is the value the library uses in its own tests, and the serving circuit leaves a ciphertext noise several orders of magnitude larger than that. The simulation step of theorem 1 therefore rests on a hypothesis our measured configuration does not satisfy."

This is not a paper defect only in the abstract. The report gives the attack. The serving circuit is deterministic, so a client resubmitting an identical query ciphertext receives the same (c0, c1) with freshly drawn smudging. Averaging repetitions drives the smudging to zero, yields c1·s, and recovers the collective secret by one ring inversion. The report's own estimate is "about 5×10^5 repetitions," against query budgets of 1.2×10^4 to 2×10^5 that the same paper's §V-F treats as in range. The adversary is the server together with t−1 clients, which the report correctly observes is "inside the model rather than outside it." A recovered collective key exposes Enc(θ⋆), the per-class totals whose encryption is the whole justification for the encrypted reciprocal, and every honest client's uploaded displacement. Every claim in Section IV falls with it.

**Epistemic status.** The gap in the hypothesis is proven, from the theorem statement and the cited scheme's requirement. The attack is the authors' own analysis, which I judge correct; I did not reproduce the 5×10^5 figure and treat the constant as heuristic.

**What a ten-page referee sees.** Nothing. The submission has no occurrence of "smudging", "flooding", "IND-CPA-D", "duplicate", or any citation to Li and Micciancio (EUROCRYPT 2021), Checri et al. (CRYPTO 2024), or Li, Micciancio, Schultz and Sorrell (CRYPTO 2022), all three of which the report cites. A referee reading only the submission would accept a theorem the authors know does not apply to their measurements. That is the reason this is Critical rather than Major: the omission is what converts a stateable limitation into a misrepresentation.

**What would fix it.**
1. Add the missing hypothesis to Theorem 1 explicitly: the collective key-switching and collective-refresh protocols are simulatable at the instantiated smudging parameter. State the parameter as a number.
2. Report the gap in the submission, in Section IV, in three or four sentences. Cite Li and Micciancio, and Checri et al., in the ten pages.
3. Make the duplicate-query check part of Algorithm 1 and part of Functionality 1, not a remark in a companion. The report already calls it required.
4. Measure the recommended configuration. The report asserts that moving smudging from 8× to 2^25 "costs nothing in latency, nothing in traffic, and nothing in the accuracy of the served answers." That is an assertion. Every cost figure in §V-E and the correctness figure 7.3×10^-5 were taken at 8×. Re-measure at the configuration you recommend, and report those numbers as the headline.
5. Reconcile the abstract. "Cryptographically secure" should not be claimed for a configuration whose simulation hypothesis is not met.

---

### F2. A rogue key-generation share is a counterexample to Theorem 2 as the submission states it — MAJOR

**Location.** Submission §IV-C, Definition 2 step 3, "A may deviate arbitrarily in the values its clients upload, in the shares they contribute, and in the queries they ask", and Theorem 2 (p. 5). Technical Report §IV-G final paragraph (p. 11).

**What is wrong.** Definition 2 grants the adversary arbitrary deviation in "the shares they contribute". Read naturally, that includes key-generation shares. The report says otherwise, and gives the break: "A party that publishes last, after seeing the others, can subtract their contribution and leave a public key whose secret it holds alone. Every ciphertext uploaded under that key is then readable by that party, and the deviation is detected only later, when the honest decryption shares fail to reconstruct, by which time the uploads have been read." That is a total break of input privacy inside Definition 2's own game: the adversary reads the honest client's head displacement in the clear, so its advantage is 1/2, not negl(λ) + δ(Q_tot). The report concludes "a deployment that omits the commitment round is outside the theorem." The submission omits both the caveat and the remedy.

**Epistemic status.** Proven, given the standard additive collective key generation of the cited scheme. This is the textbook rogue-key attack and the commit-then-open remedy is standard.

**What would fix it.** Put the commitment round into the protocol description in Section III or II-A, one sentence, and note that its cost is one round and independent of the ring parameters. Then either the theorem statement stands as written, or Definition 2 must exclude key-generation deviation explicitly. Do not leave the reader to infer which.

---

### F3. The submission presents the provenance check as an available mechanism; the report says it is not implemented, and the mechanism it describes does not work under the level restoration the submission's own figure measures — MAJOR

**Location.** Submission §IV-D, final paragraph (p. 6): "A mechanism checks provenance. The serving circuit is a deterministic function of the encrypted head, the encrypted query, the evaluation keys and the public parameters, and its level restoration is deterministic as well. A client can therefore recompute the prescribed output ciphertext and compare it as a string." Compare Technical Report §IV-D: "Two mechanisms would remove the assumption, and we implement neither."

**What is wrong.** Two things.

First, "and we implement neither" is deleted. In a section whose stated purpose is to explain why the server must be honest, a paragraph describing a repair without saying it is unbuilt reads as a property of the system.

Second, the report's version carries the reason the argument works: level restoration is deterministic "because the protocol restores levels under collectively generated bootstrapping keys rather than by collective refresh." The submission drops that clause, and the caption of Figure 2(d) says panel (d) is measured "under collective refresh." Collective refresh is interactive and injects fresh randomness from every participant, so the output ciphertext is not reproducible bit for bit and cannot be "compared as a string." As printed, the submission asserts determinism while its own figure measures the mechanism under which determinism fails. The submission never tells the reader which of the two mechanisms the protocol specifies, although Table VII of the report shows they differ by a factor of thirteen in latency and by 1.6 GiB of traffic per label at a hundred classes.

Note also the tension this creates with F1, which the paper nowhere states: the determinism that makes the provenance check possible is exactly what makes the repetition attack possible. A randomized serving circuit would frustrate the key recovery and destroy the verifiability argument at the same time. That trade deserves a sentence.

**Epistemic status.** Proven from the two texts and the figure caption for the inconsistency; heuristic for the determinism-versus-repetition trade, which I derive from the report's own attack description.

**What would fix it.** Say which level-restoration mechanism the protocol specifies, in Section III-C, and use its numbers consistently in Section V-E and Figure 2. Restore "we implement neither." Cite Viand, Knabenhans and Hithnawi (IEEE S&P 2023), which the report cites and the submission does not, when raising verifiable evaluation.

---

### F4. The hard-label citation is used to imply a hardness the paper's own measurement contradicts — MAJOR

**Location.** Submission §III-C(c), p. 4: "Returning only the index of the largest entry places an adversary in the hard-label setting, where functionally equivalent extraction is markedly harder [20]." Reference [20] is Chen et al., ASIACRYPT 2024.

**What is wrong.** Chen et al. and Carlini et al. (EUROCRYPT 2025) give hard-label extraction for ReLU networks, and their cost carries a factor exponential in the number of hidden neurons. The object served here is a single linear map with no hidden layer, so that factor is absent. The report says exactly this and the submission deletes it: "Those results carry a factor exponential in the number of hidden neurons, and our shared quantity has none, so the restriction buys less here than they suggest." The submission's own §V-F then measures extraction of the served head at three to five queries per parameter, which is cheap and orderly, not "markedly harder." A citation is being used to support a claim its own scope excludes, and the paper's measurement is the counterexample.

**Epistemic status.** Proven, from the scope of the cited results and from the paper's Table in §V-F.

**What would fix it.** Restore the report's sentence, or at minimum replace "markedly harder" with what §V-F measures. The honest claim is available and is not weak: the restriction removes the linear solve and replaces it with a boundary search whose price the paper measures. Say that.

---

### F5. The ideal functionality executes the protocol's training algorithm instead of abstracting the task — MAJOR

**Location.** Submission Functionality 1, Step 1 (p. 5): "run the local training of section III-B on each D_j in both servable arrangements and store the two shared heads θ⋆_A and θ⋆_B of eq. (1)."

**What is wrong.** An ideal functionality is supposed to name what the parties are entitled to compute, so that "the protocol realizes F" is informative about the task. This one names the protocol. It hardcodes the adapter, the two arrangements, eq. (1), eq. (2) and the coverage weighting, so Theorem 1 reduces to "the ciphertexts are indistinguishable and the server learns nothing it could not have computed", which is true and much less than the framing suggests. The two models the paper says it follows do not do this: ELSA's aggregation functionality abstracts the sum, and FULLSA's placement of the aggregator outside F is a statement about the sum as well. Neither embeds the learning rule.

There is a second, technical consequence. Local training is randomized, so "the two shared heads" are not a function of the inputs, and Definition 1's quantification "for every {D_j}" does not pin the ideal experiment down. The real and ideal worlds must be coupled on that randomness, and nothing says how.

**Epistemic status.** Proven for the second point. For the first, the norm is grounded internally rather than by my prior: the paper names ELSA and FULLSA as its models and those functionalities abstract the computed function, so the criticism is that the paper departs from the standard it cites. Applied PPML papers do vary in this practice, so I do not rate it Critical.

**What would fix it.** Either state F over the merged linear map as a function of the clients' displacements and counts, treating local training as an input-generation step outside F, or keep the present form and say in one sentence that F is stated at the level of the concrete construction and what that costs the interpretation of Theorem 1.

---

### F6. The leakage set omits the per-query pattern, which makes the simulator unconstructible when the server is not corrupt — MAJOR

**Location.** Submission Functionality 1, Step 3 and the Leakage paragraph (p. 5); Definition 1 (p. 5); the proof sketch's sentence "Queries by honest clients are simulated as key switches of encryptions of zero."

**What is wrong.** F sends (Done, query, j) to S only. The leakage set is "the public parameters, the per-client sample counts n_j, the announced index a⋆, and the fact that each Done message was sent." Definition 1 says the adversary corrupts "a set of parties that may contain the server and at most t−1 clients", so the server need not be corrupt.

In the real protocol every query requires a quorum key switch, so every participating client observes that a query occurred and sees the destination public key, which identifies the querier. A corrupted client therefore learns the full sequence of honest clients' query events in the real world. In the ideal world, with the server honest, it learns nothing of the kind. The simulator does not know how many honest-client key switches to produce or when, so it cannot produce the transcript the proof sketch describes. The theorem is not provable in this sub-case as the leakage set stands.

This is also a substantive omission, not only a formal one. In the cross-institution settings the introduction invokes, who queried and how often is itself sensitive, and it is disclosed to every quorum member on every query.

**Epistemic status.** Proven from the functionality's message pattern and the protocol's quorum requirement. The fix is definitional.

**What would fix it.** Add the query pattern to L — the ordered sequence of (query, j) events, or at least the per-client query counts — and deliver the Done signal for a query to every party, since the protocol does. Then say in one sentence what that leakage is and why it is acceptable. Related, and cheaper to fix: F declares S "not part of F", yet S supplies the (Select) input and receives (Done, query, j). A party with an input and an output interface is a party. ELSA and FULLSA handle this by giving the aggregator a defined leakage interface rather than by excluding it.

---

### F7. The t-out-of-N claim is attributed to the wrong construction, and the justification for measuring only t = N is factually wrong — MAJOR

**Location.** Submission §II-A, p. 2: "We use the multiparty variant [15], stated here for a t-out-of-N threshold with 2 ≤ t ≤ N" and "Our implementation instantiates t = N, which is the setting the multiparty CKKS library provides."

**What is wrong.** Reference [15] is Mouchet, Troncoso-Pastoriza, Bossuat and Hubaux, PoPETs 2021, which is the N-out-of-N multiparty scheme. The t-out-of-N access structure is a separate construction: Mouchet, Bertrand and Hubaux, "An Efficient Threshold Access-Structure for RLWE-Based Multiparty Homomorphic Encryption", Journal of Cryptology 2023 (IACR ePrint 2022/780). That paper reaches t-out-of-N by a share re-sharing procedure, and it reports an implementation in Lattigo, the library this paper uses. So the stated reason for measuring only t = N does not stand as written.

This matters beyond attribution. The re-sharing introduces Lagrange coefficients into the parties' shares, which changes the noise the decryption and key-switching protocols carry and therefore changes the smudging requirement, which is the quantity F1 turns on. The paper's claim "Every statement in section IV holds for general t" is asserted without engaging the parameter consequences of general t at all.

**Epistemic status.** Proven for the citation. Heuristic, and stated as such, for the claim that the smudging requirement moves with t; the direction follows from the re-sharing construction but I did not compute the bound.

**What would fix it.** Cite the Journal of Cryptology 2023 paper for the t-out-of-N structure. Either measure one t < N configuration, or say plainly that only t = N was measured and that the parameter consequences of general t are not evaluated. Also correct the per-query traffic formula: the submission writes "8.5 + 0.5N MiB, since the quorum returns one key-switching share each" (§V-E(b), p. 7), and the quorum has t members, so the formula should be in t. It is right only at t = N.

---

### F8. The binding query allowance is computed in the report and omitted from the submission — MAJOR

**Location.** Submission §V-F, p. 8: "A deployment can therefore set its allowance from C, d and the fidelity it concedes." Technical Report §V-F: "holding it below fidelity 0.90 at N = 10 requires Q below roughly 1.3×10^3 per client on AG-News and 2.2×10^4 on Banking77."

**What is wrong.** The submission tells the reader that an allowance exists and can be computed, and never computes it. The number matters, and it is not comfortable: on a four-class task, a federation of ten must cap every client at roughly thirteen hundred predictions for the life of the protocol, because a coalition of nine pools its allowances against a shared head with only C·d parameters. Re-keying does not reset it, since the object being extracted is the head and not the key. The report also states the sting, which the submission drops: "the deployments that gain most from the federation are the ones that must meter queries most tightly."

The abstract and conclusion assert that "no party receives the trained result" without qualification. That is literally true and, at these budgets, materially incomplete. Section III-C and Section V-H are honest about the allowance being operational rather than cryptographic; the abstract is where the qualification is missing.

**Epistemic status.** Empirical, on the paper's own extraction measurements over three tasks and three seeds. The arithmetic (1.2×10^4 divided by t−1 = 9) is checkable.

**What would fix it.** Move the two allowance numbers into the submission, one sentence in §V-F. Add a clause to the abstract that bounds what a coalition can reconstruct at a stated query price.

---

### F9. The encrypted reciprocal is under-specified at exactly the two points where it is hard — MAJOR

**Location.** Submission §III-B(d), p. 3: "The reciprocal is therefore evaluated under encryption, using an inversion circuit over the positive domain whose refreshes are collective." §III-B(c): "rows that no client covers remain at the public initialiser." §III-B(e): "The server performs one ciphertext addition per client per ciphertext, one encrypted reciprocal, and one multiplication."

**What is wrong.** Two cases are not addressed.

A class no client holds has denominator zero. An inversion circuit "over the positive domain" is not defined there, and a Newton or Goldschmidt iteration on zero does not return anything that multiplies the zero numerator back to the public initialiser. Detecting the zero under encryption requires a comparison, which is not in the stated cost and is the paper's own expensive primitive. The paper asserts the desired behaviour without a mechanism. Section V-B's own explanation of the Banking77 collapse — "each head row is decided by few clients or none" — says the case arises.

The dynamic range is the second. An inversion circuit needs its input scaled into a known interval by a public constant, so the server needs a public upper bound on the per-class totals. The one available bound is the sum of the public n_j, which puts a class held by a single client with a handful of examples several orders of magnitude below the top of the interval. The report measures 4.21 s and two collective refreshes at N = 10 with relative error 1.9×10^-8, which is a good result and does not by itself tell the reader over what range it holds. Since the totals are the quantity the design refuses to decrypt, how the range is fixed without leaking them is a load-bearing detail.

**Epistemic status.** Open. I cannot exhibit a failure without the implementation. What I can state is that the specification as printed does not determine the behaviour in either case, and that both cases occur in the paper's own experimental grid.

**What would fix it.** State the floor or the masking rule that handles a zero total, state the public scaling constant and the interval, and say what the reported relative error was measured over. If the fix is adding one to every class total before inversion, say so; it is a good answer and it leaks nothing beyond what is already public.

---

### F10. Proposition 1 is correct but the conclusion drawn from it is broader than the proposition supports — MAJOR

**Location.** Submission §IV-D, Proposition 1 and the sentence following its proof (p. 6): "An honest client therefore releases its share for both plaintexts or for neither. No protocol of this message pattern realizes F against a malicious server, which is why theorem 2 places the server among the honest parties."

**What is wrong.** The proposition assumes "the rest of that view be independent of the underlying plaintext" and concludes that a predicate on the ciphertext cannot distinguish. That is right, and it is a two-line consequence of IND-CPA. What it establishes is that *content-based* gating is impossible. The paper then concludes that *no* protocol of this message pattern realizes F, which is a different and stronger statement, and the paper refutes it itself two paragraphs later by describing a provenance check that gates on whether the presented ciphertext is the prescribed output of the serving circuit. That check does not read the plaintext, so it does not fall to the proposition, and the report puts a probability on its coverage. A malicious-server protocol built on verifiable evaluation is also not excluded.

**Epistemic status.** Proven. The proposition's hypothesis is what limits its reach, and the paper's own next paragraph is the witness.

**What would fix it.** Weaken the sentence to what is proven: no gate that depends only on the plaintext can work, so realizing F against a malicious server requires a provenance or correctness mechanism outside the message pattern, and the paper implements neither. That is a clean statement and it keeps the proposition's value.

---

### F11. Theorem 2's proof sketch contradicts itself in one line — MINOR

**Location.** Submission §IV-C, proof sketch of Theorem 2 (p. 5): "The adversary's view consists of the key-generation transcript, the honest clients' uploaded ciphertexts, the values the server computes, and the answers to its own queries. The first four are independent of b up to negl(λ). What remains is the answers."

**What is wrong.** Four items are listed, all four are declared independent of b, and the fourth is then said to be what remains and to depend on b. The intended word is "three". The same sentence appears in the report, so it is not an extraction artifact. It sits inside the proof of one of the paper's two theorems, which is where a referee reads most carefully.

**What would fix it.** One word.

---

### F12. The protocol realizes an approximate argmax; the functionality specifies an exact one — MINOR

**Location.** Submission Functionality 1, Step 3, "return ŷ = arg max_c (θ⋆_{a⋆} φ^{a⋆}_j(x))_c" (p. 5), against §V-E(c), p. 7: "The encrypted argmax agrees with the plaintext maximum to 7.3×10^-5, which is far below the gap between adjacent logits, so it selects the same class."

**What is wrong.** Theorem 1 carries no correctness-error term. Where the approximation and the exact argmax disagree, the real view differs from the ideal view in a way that depends on the honest clients' logits, and that is a distinguisher. The measured agreement is the right evidence but it belongs in the theorem as a term, not only in the experiments. Separately, "far below the gap between adjacent logits" is asserted, not measured as a minimum over the evaluation set; on Banking77 with 77 classes near-ties are ordinary.

**What would fix it.** Add the correctness error to the theorem statement as an additive term, and report the minimum observed top-two logit gap alongside the 7.3×10^-5.

---

### F13. The leakage set's "per-client sample counts n_j" collides with the notation g_{j,c} = n_{j,c} — MINOR

**Location.** Submission Functionality 1, Leakage (p. 5), and §IV-A, "The sample counts sit in the leakage because the protocol uses them as public scalars"; against §III-B(c), "g_j ∈ R^C collect client j's per-class example counts, g_{j,c} = n_{j,c}".

**What is wrong.** With n_{j,c} defined for the per-class counts, "the per-client sample counts n_j" in the leakage set is ambiguous between the scalar total and the vector. The reading matters absolutely: if the per-class counts are public, the encrypted reciprocal of §III-B(d) protects nothing, since a coalition of N−1 that knows every g_j knows the totals. §III-B makes clear that the intended reading is the scalar, but the reader has to reconstruct it.

**What would fix it.** Write the leakage as the totals n_j = Σ_c n_{j,c} explicitly, and add the sentence the report has: the equal-size restriction in Definition 2 exists because these totals are public. The submission states the restriction without its reason.

Related and worth one line somewhere: leaking each client's dataset size is not obviously free in the settings the introduction names, where patient or customer volume is commercially sensitive. The paper asserts the leakage and never argues it is acceptable.

---

### F14. No security level is stated for any parameter set — MAJOR

**Location.** Submission §V-E, p. 7: "All figures use ring degree 2^14 for the shallow operations and a deeper chain at ring degree 2^15 for the circuits that need it." Technical Report §V-E, Table VI and Table VII (ring degrees 2^14, 2^15, 2^16; plaintext scale 2^45; an eight-modulus chain for aggregation and a fifteen-modulus chain for serving).

**What is wrong.** Neither document states a bit-security level, a total ciphertext modulus, a secret distribution, or the source of the parameter choice. Every theorem is stated with negl(λ) and λ is never instantiated. A referee cannot check whether ring degree 2^14 with an eight-modulus chain at scale 2^45 sits inside the accepted parameter envelope; by the published tables it is close enough to the boundary that it must be stated rather than assumed. This is the one thing a reader needs in order to believe the cryptography and the one thing that is missing.

**Norm grounding.** The expectation is not my prior. The community's own parameter standard is the Homomorphic Encryption Security Standard (Albrecht et al., HomomorphicEncryption.org, 2018), whose tables fix the maximum log Q per ring degree per security level and per secret distribution, and the Albrecht–Player–Scott lattice estimator (Journal of Mathematical Cryptology, 2015) is the tool the field uses to check a parameter set outside those tables.

**What would fix it.** One table, or one sentence per chain: ring degree, log Q, scale, secret distribution, claimed classical bit security, and the estimator version or standard table used. Say which of these numbers changes if F1's smudging fix requires a larger scale, because the report says a conforming configuration "needs a larger scale and modulus, and every cost in section V-E would move with them."

---

### F15. Literature coverage in the submission — MAJOR for the cryptographic gaps, MINOR for the rest

**Location.** Submission §VI, pp. 8–9, and the reference list.

The report's Section VI is genuinely thorough, with 131 references covering HETAL, Iron, BOLT, PUMA, FLoRA, HetLoRA, task arithmetic, the IND-CPA-D line and verifiable FHE. My comments are about the ten pages, which is what a TNSE referee judges.

**Must be added to the submission.**

- Li and Micciancio, "On the security of homomorphic encryption on approximate numbers", EUROCRYPT 2021. Required by F1. A CKKS protocol that decrypts and key-switches outputs to parties cannot omit the approximate-decryption attack line.
- Checri, Sirdey, Boudguiga and Bultel, "On the practical CPA-D security of 'exact' and threshold FHE schemes and libraries", CRYPTO 2024. Required by F1 and directly on point, since it treats threshold schemes.
- Li, Micciancio, Schultz and Sorrell, "Securing approximate homomorphic encryption using differential privacy", CRYPTO 2022. This is the source of the noise-budget accounting the report uses ("half a bit for each doubling of q") and of the recommended mitigation.
- Mouchet, Bertrand and Hubaux, "An Efficient Threshold Access-Structure for RLWE-Based Multiparty Homomorphic Encryption", Journal of Cryptology 2023. Required by F7.
- Viand, Knabenhans and Hithnawi, "SoK: Fully homomorphic encryption compilers and verifiable computation", IEEE S&P 2023. Required by F3 and F10, since Section IV-D's whole discussion is about what a client can verify.
- Jagielski, Carlini, Berthelot, Kurakin and Papernot, "High Accuracy and High Fidelity Extraction of Neural Networks", USENIX Security 2020. Section V-F defines "fidelity" as a term of art and uses the accuracy-versus-fidelity distinction throughout without citing where it comes from. Neither document cites it.

**Should be added, positioning rather than correctness.**

- HETAL (Lee, Lee, Kim, Shin and Lee, ICML 2023) is the closest existing construction to this one and receives one clause inside a paragraph: "Several works train a classifier head, a linear or logistic model on frozen features under CKKS [34]." It is not in Table III. HETAL trains the head under encryption in a two-party arrangement where the data owner holds the key and ends up with the trained model. Those are the two distinctions that matter here and neither is stated. A reader is entitled to see HETAL on the axes of Table III.
- The secure transformer inference line is represented by one citation. Section III-C(f) and Section VI-E both claim composition with that literature "at that literature's cost", which is a cost claim with no anchor. Name two or three systems with numbers: Iron (Hao et al., NeurIPS 2022), BOLT (Pang, Zhu, Möllering, Zheng and Schneider, IEEE S&P 2024), PUMA (Dong et al.). All three are in the report.
- Federated LoRA is represented by FedIT and FFA-LoRA. The heterogeneity line is the one that would break the shared public initialiser this construction depends on: FLoRA (Wang et al., NeurIPS 2024) and HetLoRA (Cho, Liu, Xu, Fahrezi and Joshi, EMNLP 2024). Both are in the report.
- Secure aggregation is represented by Bonawitz and by Kerkouche et al. Two additions would strengthen §VI-B: Pasquini, Francati and Ateniese, "Eluding secure aggregation in federated learning via model inconsistency", ACM CCS 2022, which shows a malicious server defeating the aggregation guarantee and supports the paper's own argument better than the leakage-across-rounds citation does; and Flamingo (Ma, Woods, Angel, Popa and Devadas, IEEE S&P 2023) as the current single-server multi-round baseline. Neither is in either document. [Existence attested; relevance is my judgement.]

---

### F16. The domain contribution is a composition, and the paper claims more than that — MINOR

**Location.** Abstract and §I, "the first cryptographically secure one-shot federated fine-tuning protocol in which no party receives the trained result"; §VI Positioning, p. 9.

**What is wrong.** On the cryptographic axis every component is off the shelf: threshold CKKS from Mouchet et al., the comparison circuit from Cheon, Kim and Kim, key switching to the querier from the same serving pattern slytHErin uses, and the frozen down-projection from FFA-LoRA. The security argument is a standard hybrid over IND-CPA with no new proof technique. That is not a criticism of the work; composition papers are how this field advances, and the composition here is not obvious, because the design chain C1 to C6 is a real derivation and the encrypted selection rule of §III-D is, so far as I can find, new.

The criticism is the framing. "First cryptographically secure" invites a cryptographer to look for a new primitive or a new proof and to find neither, and after F1 the qualifier "cryptographically secure" is not currently earned by the measured configuration. The defensible claim is narrower and still worth stating: the first protocol that is simultaneously one-shot, encrypted end to end, and never discloses the trained map to any party, together with a selection rule that runs under encryption. The report's Table X already argues that position well.

**What would fix it.** State the contribution as the composition plus the selection rule, and let the axes table carry the novelty argument.

---

## Strengths, stated once each

1. **The design chain C1 to C6 (§III-A, p. 3) is the paper's best idea.** It derives the placement of the shared map from the requirement that the querier compute its own features, rather than asserting an architecture. The consequence — that any trained linear map after the last nonlinearity qualifies, and that the construction fixes the position and not the task — is correctly stated and correctly scoped ("We evaluate classification only", §III-B(b)).

2. **Refusing to decrypt the per-class totals is the right call and the reason is given correctly** (§III-B(d), p. 3): a coalition of N−1 that learned the totals subtracts its own and reads the remaining client's class histogram. Many papers in this line would have taken the public denominator and not noticed.

3. **Section IV-E separates the cryptographic claim from the operational one explicitly**: "The first rests on IND-CPA. The second rests on a measurement." That distinction is the one most papers in this literature blur, and the paper is right to make it a sentence of its own.

4. **The cryptography is implemented rather than simulated,** on Lattigo, with communication figures the authors call exact and a measured argmax agreement of 7.3×10^-5. Reporting 400.8 to 1468.3 seconds per query rather than an extrapolation is the honest choice and it costs the paper something to make.

5. **Proposition 2 in the technical report** (the query channel is no stronger than handing over both heads) is a clean reduction and the right way to bound the residual channel. It deserves to be in the submission more than Proposition 1 does.

---

## Questions for the authors

1. Which level-restoration mechanism does the protocol specify — collective refresh or server-side bootstrapping under collectively generated keys? Section V-E's per-query latencies and Figure 2(d)'s caption appear to answer differently, and Section IV-D's provenance argument only holds for one of them.

2. What smudging parameter do you claim, and what does the measured cost become at it? If a conforming configuration requires a larger scale and modulus, as the report says, do the headline numbers in the abstract survive?

3. Is the duplicate-query check part of the protocol? If yes, it belongs in Algorithm 1 and in Functionality 1's Step 3. If no, what prevents the repetition attack the report describes at 5×10^5 repetitions?

4. How does the aggregation circuit behave when a class total is zero, and what public constant scales the denominator into the inversion circuit's domain? Over what range of per-class totals was the 1.9×10^-8 relative error measured?

5. Lattigo implements the t-out-of-N access structure of Mouchet, Bertrand and Hubaux (JoC 2023). What prevented measuring one t < N configuration, and does the re-sharing change the smudging requirement?

6. When the server is honest and only clients are corrupted, where does the simulator learn how many honest-client queries occurred, given that F sends (Done, query, j) to S alone?

7. What classical bit security do you claim at each of the three ring degrees, at what log Q and secret distribution, and against which standard table or estimator?

8. What allowance Q do you recommend for each evaluated task, and does a deployment that needs more than roughly 1300 predictions per client on a four-class task have any option other than accepting a 0.90-fidelity copy in the hands of a coalition?

9. The determinism that makes the provenance check possible is what makes the repetition attack possible. Have you considered whether a randomized serving circuit trades one for the other, and which side of that trade a deployment should take?
