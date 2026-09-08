# Seat 5 — Devil's Advocate

## Summary and recommendation

The paper asks a deployment to pay 0.03 to 0.14 accuracy against a disclosed model, 0.20 to 0.36 against a centralised one, 400.8 to 1468.3 seconds per query, and an unstated query allowance, in exchange for one property: no party ever holds the trained head in plaintext.
That property is not established by the measured system. The companion report states that the simulator hypothesis behind Theorem 1 is unmet in the configuration measured, that repeating a query recovers the collective secret key inside the paper's own threat model, and that the serving circuit's scaling constant was taken from the exported plaintext head, which the protocol forbids.
None of that reaches the ten pages. The submission's Scope and Limitations names three limitations; the report names five, plus two more in its Section IV-G.
The headline cost quantity, `A_dis − A_sel`, is not derivable from any table in either document, and the obvious reconstruction from Table I contradicts the stated range on two of five tasks.
The paper is honest in its companion and selective in its submission, and the selection runs in one direction.

**Recommendation: Reject.** Not because the construction is uninteresting, but because two of the five CRITICAL findings require measurement campaigns whose outcomes would move the numbers in the abstract. C1 in particular cannot be repaired by editing: the report says a configuration satisfying the smudging condition "needs a larger scale and modulus, and every cost in section V-E would move with them." A resubmission that instantiates its own theorem, reruns the serving circuit under a public norm bound, and tabulates `A_sel` would be a strong paper.

---

## Findings

### C1 — CRITICAL. The security theorem is not instantiated by any configuration the authors offer, and a key recovery sits inside the stated threat model. The submission says nothing about either.

**Location.** Submission p.5, Theorem 1 and its proof sketch; p.5 §IV-E, "The cryptographic claim is that the protocol adds nothing to the leakage of `F` ... The first rests on IND-CPA." Submission p.6 §IV-D, "The serving circuit is a deterministic function of the encrypted head, the encrypted query, the evaluation keys and the public parameters, and its level restoration is deterministic as well." Report p.10-11 §IV-G.

**What is wrong.** Three things, all documented by the authors, none of them in the manuscript.

1. The report states: "The simulation step of theorem 1 therefore rests on a hypothesis our measured configuration does not satisfy." The multiparty scheme's key-switch simulator is correct when smudging noise dominates the ciphertext noise, at `2^(λ/2)` times it. The implementation smudges at eight times the fresh-encryption noise, and the serving circuit leaves ciphertext noise "several orders of magnitude larger than that." The recommended repair, `2^25`, also fails the rule, and the report says so: "It does not meet the `2^(λ/2)` rule, and we do not claim that it does." So Theorem 1 as printed in the submission has an unmet hypothesis in the configuration that produced every number in Section V-E, and in the configuration the authors recommend instead.

2. The report gives a concrete key recovery. The serving circuit is deterministic, so a client resubmitting an identical query receives the same `(c_0, c_1)` and a freshly drawn smudging term. Averaging `k` repetitions drives the error to zero and converges on `c_0 + c_1·s`; subtracting and rounding yields `c_1·s`, and one ring inversion yields `s`. Cost: about `5×10^5` repetitions at the measured smudging, which the report itself calls "the same order as the query budgets section V-F already contemplates." The adversary is semi-honest, and the server that holds `(c_0, c_1)` is corruptible under Definition 1.

3. The report names a duplicate check as "a required control and not a supplementary one." That control must be enforced by the server. Definition 1 corrupts the server together with `t−1` clients. The required control is therefore enforced by a party the threat model permits the adversary to control, which the report does not observe and the submission does not mention. The same section records a second uncovered deviation: a party that publishes its key-generation share last can subtract the others and hold the collective secret alone, and the standard commitment round is not in the protocol as specified.

The submission presents determinism as a virtue — it is the basis of the provenance repair to Proposition 1 — and never states that the same determinism is what makes the repetition attack work.

**Epistemic status.** Proven for the smudging gap and the recovery arithmetic, on the authors' own statement. Open for exploitability under the recommended `2^25` configuration, again on the authors' statement.

**Fix.** State the smudging condition, the gap, the repetition attack, and the two required controls in the submission's Section IV, not only in the companion. Then either instantiate a configuration that meets the simulator hypothesis and remeasure Section V-E, or restate Theorem 1 with the hypothesis the implementation actually satisfies and say what it then proves. Add the key-generation commitment round to the protocol.

---

### C2 — CRITICAL. The correctness and latency measurements use a serving constant taken from the plaintext head, which the protocol forbids. The admissible substitute is unmeasured.

**Location.** Report p.19 §V-H-b: "The serving circuit compares logits through a polynomial approximation of the sign, and that approximation resolves a fixed absolute margin ... Our runs fix one such constant from the exported head. A deployment cannot do that, because the head is a ciphertext, so it needs a public bound on the head's norm instead ... we do not measure what a loose one costs." Against submission p.7 §V-E-c: "The encrypted argmax agrees with the plaintext maximum to `7.3×10^-5` ... The accuracy figures of table I are therefore unaffected by the cryptography." Submission p.8 §V-H names three limitations and this is not one of them.

**What is wrong.** The paper's title property is that no party holds the head in plaintext. The experiment that validates the serving path used the head in plaintext to set a circuit parameter. Every latency figure (400.8 s to 1468.3 s, 17 and 62 level restorations) and the correctness figure and the thirty-two real-query agreement were obtained under a calibration the deployed protocol cannot perform. Under a public norm bound the constant is necessarily looser, and a looser constant makes the sign approximation resolve a smaller relative margin, which costs either precision (a wrong argmax, so Table I *is* affected by the cryptography) or depth (more comparisons, more restorations, more latency). Which of the two, and how much, is unmeasured.

This is not a presentation defect. It is the one experiment in the paper that connects the cryptography to the accuracy table, and it was run with the object the protocol exists to withhold.

**Epistemic status.** Proven that the constant came from the exported head, on the authors' statement. Open how much a public bound costs, on the same statement.

**Fix.** Rerun the end-to-end serving measurements with the constant derived from a public norm bound of the kind a deployment would have. Report the resulting precision and latency. Add the limitation to the submission's Section V-H.

---

### C3 — CRITICAL. The paper's headline cost quantity is not derivable from any table, and the obvious reconstruction contradicts the stated range on two of five tasks.

**Location.** Submission abstract, "gives up 0.03 to 0.14 against a disclosed model"; submission p.8 §V-G, "The quantity `A_dis − A_sel` runs from 0.029 to 0.136 across the five tasks"; submission Table I; report p.18 §V-G, "`A_dis − A_sel` is 0.071 on AG-News, 0.104 on TREC, 0.136 on DBpedia, 0.075 on Banking77 and 0.029 on CIFAR-100."

**What is wrong.** Table I reports the two servable arrangements as three-seed column means, with bold marking the better. `A_sel` is defined in §V-A as "the accuracy of the servable arrangement that section V-D selects" and is never tabulated for the five main tasks in either document. Taking the bold cell, which is the only reading Table I supports:

| task | better arrangement | disclosed | difference from Table I | paper's stated figure |
|---|---|---|---|---|
| AG-News | 0.649 | 0.739 | **0.090** | 0.071 |
| TREC | 0.607 | 0.711 | 0.104 | 0.104 |
| DBpedia | 0.789 | 0.925 | 0.136 | 0.136 |
| Banking77 | 0.686 | 0.760 | 0.074 | 0.075 |
| CIFAR-100 | 0.774 | 0.784 | **0.010** | 0.029 |

The stated lower bound of the range, 0.029, is not the minimum of what Table I yields; 0.010 is. And on AG-News the implied `A_sel` is `0.739 − 0.071 = 0.668`, which exceeds **both** servable column means (0.649 and 0.479). A referee checking the arithmetic will read that as the selection rule acting as an oracle.

The benign explanation exists — selection is per-seed, the report's §V-D says the estimator errs on 3 of 15 cells, and the report's §V-B notes one AG-News seed where the shared head falls to 0.402 — so a seed-wise mixture can land above either column mean. But that explanation appears in neither document as an explanation of Table I, and the per-seed numbers that would make the headline verifiable are published nowhere. The abstract's accuracy range (0.61 to 0.79) and cost range (0.03 to 0.14) are therefore unverifiable from the manuscript, from the companion, or from both together, and the reconstruction a reader will actually attempt contradicts them.

**Epistemic status.** Empirical, verified by arithmetic against the paper's own Table I.

**Fix.** Add an `A_sel` column to Table I and publish the per-seed selected accuracies. State in the caption that `A_sel` is selected per seed and can exceed either arrangement's mean.

---

### C4 — CRITICAL. The channel enumeration is incomplete in the one direction that defeats the paper's most expensive mechanism, and Theorem 2's `δ` is instantiated by a measurement that holds the relevant variable fixed.

**Location.** Submission p.7 §V-F: "The protocol exposes no training-time artifact and no model, so the only remaining channel is the sequence of answers the served model returns." Submission p.3 §III-B-d, the justification for the encrypted reciprocal: "Every client knows its own counts, so a coalition of `N−1` clients that learned the totals would subtract its own and read the remaining client's class histogram exactly." Report p.9-10 §IV-F-1 and its two stated limits.

**What is wrong.** The paper spends a deep circuit, two collective refreshes and 4.21 s to keep the per-class totals encrypted, on the stated ground that a coalition must not learn the remaining client's class histogram. The serving interface leaks a version of the same thing, and neither document analyses it.

Rows that no client covers "remain at the public initialiser" (§III-B-c). So an extracted copy of `θ*` reveals which rows moved off `θ_0`, which is the support of the federation's class coverage. A coalition of `N−1` knows its own coverage and subtracts it, obtaining the support of the honest client's class histogram — not the counts, but the support, which is what the encrypted denominator was built to protect. Worse, for a class held by exactly one client the denominator cancels outright: `θ*_c − θ_(0,c) = (n_(h,c) Δ_(h,c))/n_(h,c) = Δ_(h,c)`, so an extracted row at that class is that honest client's own trained displacement, and the encryption of the denominator buys nothing there. Single coverage is not a corner case in this paper: §V-B says "With 77 classes each head row is decided by few clients or none."

Definition 2 admits a concrete counterexample. Let `D_0` be examples all of class 1 and `D_1` examples all of class 2, equal size, on the honest client, with no other client holding either class. Under `D_0` row 1 moves and row 2 stays at `θ_0`; under `D_1` the reverse. A coalition asking a handful of queries near those rows distinguishes `b` with advantage close to 1/2. So `δ(Q_tot)` in Theorem 2 is not small for coverage-differing datasets, and the theorem is satisfied vacuously.

The report then instantiates `δ_wb` only as a record-level membership advantage, using shadow federations that — the report says — "vary who trains on what while holding the coverage pattern fixed. They say nothing about how leakage moves when the partition moves." Having stated that limit, the report nonetheless concludes: "Measuring the strongest adversary the proposition admits therefore bounds every adversary the protocol admits, and the bound is chance." That does not follow. One adversary (LiRA) was measured, on the one axis held fixed by construction. The submission carries only the conclusion — "published membership attacks against it and against the head in plaintext both sit at chance" — and none of the limit.

**Epistemic status.** Proven for the row cancellation under single coverage (algebra from eq. (1)). Proven that the counterexample is admissible under Definition 2. Empirical and acknowledged that the shadow federations hold coverage fixed. Open how large the coverage-inference advantage actually is; nobody has measured it.

**Fix.** Either measure a coverage-inference adversary — shadow federations that vary the partition, and a distinguisher on the support of the extracted head — or restrict Theorem 2's claim explicitly to datasets with matched class support and say so in the submission. Amend the "only remaining channel" sentence. State what the encrypted reciprocal does and does not buy when a class is singly covered.

---

### C5 — CRITICAL. The submission gives a deployment a rule for setting the parameter its operational security rests on, and the companion says that rule is derived from the wrong side.

**Location.** Submission p.7-8 §V-F: "The head has `Cd` parameters ... and in each case fidelity 0.90 costs between three and five times that number of queries. A deployment can therefore set its allowance from `C`, `d` and the fidelity it concedes." Report p.18 §V-F-b: "Neither strategy is the attack a cryptanalyst would mount ... That route costs a factor logarithmic in the precision demanded rather than linear in it, so our figures bound the allowance from the wrong side and should be read as what a straightforward adversary pays."

**What is wrong.** Section IV-E of the submission states the paper's two-part security claim: "The first rests on IND-CPA. The second rests on a measurement." The second — that `F`'s leakage is bounded by the allowance `Q` — is the load-bearing operational defence, and the measurement behind it prices a straightforward learning-based extractor. The authors judge that the correct adversary class is cryptanalytic and costs logarithmically rather than linearly in the precision demanded. An allowance calibrated from a linear-cost curve is therefore an over-estimate of what is safe, by a factor the paper does not bound. The submission carries the recipe and drops the caveat.

Compounding this, the submission never states a numerical allowance. The number is in the report: holding a coalition below fidelity 0.90 at `N = 10` requires `Q` below roughly `1.3×10^3` per client on AG-News. A referee reading ten pages learns that the protocol has a query allowance, that everything rests on it, and never learns that it is about a thousand queries per institution for the lifetime of the model on the small label spaces — which the report notes are precisely the deployments where the federation helps most: "the deployments that gain most from the federation are the ones that must meter queries most tightly."

**Epistemic status.** Heuristic on the authors' own statement that a cryptanalytic route costs logarithmically; open how much lower the true allowance is. Empirical for the `1.3×10^3` figure.

**Fix.** Put the allowance numbers in the submission, in Section V-F, per task. Carry the "wrong side" caveat with them. Do not give a deployment a closed-form allowance rule that the authors believe over-estimates the safe value.

---

### M1 — MAJOR. The one-time selection cost is omitted from the submission while a cost four hundred times smaller is reported.

**Location.** Submission p.7 §V-E-b: "selection costs at most `2NC` encrypted comparisons, once ... Setup costs 344 MiB per client, once." Report p.15-16 §V-E-i: "At five clients and four classes it takes 400 s and moves 3.4 GiB. At twenty clients and a hundred classes it takes 7111 s and moves 145.4 GiB."

**What is wrong.** Every other cost in the submission's Section V-E is given in seconds and mebibytes. The selection step alone is given as a comparison count with no time and no traffic, and it is the largest one-time cost in the protocol by more than two orders of magnitude. The paper argues in §III-D and §V-B that selection is mandatory, because neither arrangement dominates. So 145.4 GiB and two hours at `N = 20, C = 100` is a required cost of the protocol at a configuration inside the paper's own experimental range (it evaluates `C = 77`, `C = 100`, and `N = 50`). A further gap: the report says level restoration is "99.8 per cent of the traffic above," which places that measurement under collective refresh, while §III-D and §V-E specify server-side bootstrapping. Under the specified mechanism the traffic falls and, by the thirteenfold factor of the report's Table VII, the wall clock rises toward a day. Neither pair is reported anywhere.

**Fix.** Report the measured selection cost in the submission, say which restoration mechanism produced it, and state what the specified mechanism would cost.

---

### M2 — MAJOR. An internal numerical contradiction inside the submission, and a false statement about the experimental protocol.

**Location.** Submission p.6 §V-A: "every number is the mean over three seeds." Submission p.7 §V-B-a: "Accuracy falls with skew, from 0.970 at `α = 1.0` to 0.789 at `α = 0.1` ... Accuracy rises with the size of the federation, from 0.803 at `N = 10` to 0.882 at `N = 50`."

**What is wrong.** Both sentences describe DBpedia at the default configuration `N = 10, α = 0.1, 200` steps. One gives 0.789 and the next gives 0.803, with no explanation, in adjacent sentences. The reconciliation is in the report's Table III caption: "THE SKEW ROW IS THE MEAN OVER THREE SEEDS. THE LOCAL-STEPS AND CLIENT-COUNT ROWS ARE A SINGLE SEED." The report's Figure 4 caption says the same: "Panels (a) and (c) are one seed and panel (b) is the mean over three." The submission's Figure 2 caption omits it, and §V-A's blanket claim makes the contradiction unresolvable from the ten pages. So the scaling claim — one of only three sensitivity results, and the one that argues the protocol improves with federation size — rests on `n = 1` per point, while the paper states otherwise.

**Fix.** Correct §V-A, mark the single-seed rows in the figure caption, and either run the remaining seeds or drop the scaling claim to an observation.

---

### M3 — MAJOR. Table I is captioned with a client count its cells do not have, and the one favourable cell in Table II has a caveat the submission drops.

**Location.** Submission Table I caption, "THREE SEEDS, `N = 10`, `α = 0.1`", against report Table II caption, "ON ONE SEED THE DIRICHLET DRAW ASSIGNS FEWER THAN TWENTY SAMPLES TO SOME CLIENTS, WHICH CANNOT TRAIN, SO THE EFFECTIVE FEDERATION IS SEVEN ON AG-NEWS AND NINE ON TREC." Submission Table II row `N = 20, α = 0.04` against report §V-C-a, "we measure `A_sel > A_dis`, by 0.003 on average, on two seeds of three ... the effective federation size is 17 to 19 rather than 20."

**What is wrong.** Two of the five main tasks were measured with a fifth to a third of the federation missing on one seed, and the submission does not say so. The cell where the paper's charge is negative — the single most favourable result in Table II, and one the submission highlights — has 17 to 19 effective clients and holds on two seeds of three. The submission reports the negative charge, which is to its credit, and omits both caveats, which is not.

**Fix.** Move both caption notes into the submission.

---

### M4 — MAJOR. The submission advertises availability the measured configuration does not have.

**Location.** Submission p.2 §II-A: "Two consequences follow, and the protocol uses both. Any `t` clients form a quorum, so serving does not require every client to be online." Same page: "Our implementation instantiates `t = N`." Report p.19 §V-H-e: "in the configuration we measured a single unavailable client blocks every query until it returns."

**What is wrong.** At `t = N` the quorum property is vacuous, and the submission never retracts the sentence for the configuration it measures. It also never states the trade: the report says lowering `t` "tightens the query allowance, because the bound of section V-F scales with the largest coalition that cannot decrypt," and no point other than `t = N` was measured. A reader of ten pages concludes the system tolerates churn. It does not, as built. This bears directly on deployability in the cross-silo settings the introduction names.

**Fix.** State in §II-A that the measured configuration is `t = N` and that one offline client blocks every query, and carry the `t` trade-off into the submission's limitations.

---

### M5 — MAJOR. The abstract states a performance figure that appears nowhere in the ten pages.

**Location.** Submission abstract: "or 48.9 to 176.6 s with GPU acceleration". The strings "GPU", "accelerat", "Phantom", "H100" appear nowhere else in the submission.

**What is wrong.** The number's only basis is report §V-E-f, which substitutes one measured primitive (a single level restoration at 2.28 s on an H100) into an otherwise-CPU pipeline. The same section says "We give no single ratio against those figures ... a cross-library ratio at unmatched depth is not a measurement," and §V-E-b says the authors "decline to project a single number" — before projecting three. An abstract figure with no experiment, no method sentence, and no caveat in the body, whose companion disclaims the comparison it rests on, is not reportable as measured. It is also the number that makes the latency look deployable.

**Fix.** Remove it from the abstract, or add the projection, its method, and its caveat to §V-E and label it a projection in the abstract.

---

### M6 — MAJOR. Figure 2(d) and the prose beside it measure the same quantity under different mechanisms and differ by a factor of thirteen, unexplained.

**Location.** Submission Figure 2 caption, "Panel (d) gives the cost of one encrypted argmax against the label space, at `N = 10` and ring degree `2^15` under collective refresh"; submission §V-E-a, "On one core a query takes 400.8 s at four classes and 1468.3 s at a hundred ... The tournament needs `⌈log_2 C⌉` rounds against the `C−1` of the sequential fold it replaces (fig. 2)." Report Table VII: collective refresh 31.2 s to 113.0 s; server bootstrap 400.8 s to 1468.3 s.

**What is wrong.** The prose points the reader at panel (d) for the argmax cost while quoting numbers from the other mechanism. The panel's own axis is consistent with 31.2 to 113.0 s. The submission never says the end-to-end figures are under server-side bootstrapping, never says a thirteen-times-faster alternative exists and was measured, and never explains why the phrase "under collective refresh" is in the caption. A referee sees a figure that contradicts the text by an order of magnitude.

**Fix.** Say in §V-E which mechanism produced which figure, and report both, as the report's Table VII does.

---

### M7 — MAJOR. The submission contains no competing system's latency, and every omitted figure is faster.

**Location.** Submission §VI-E, the slytHErin and CryptPEFT paragraphs, neither carrying a number. Report §V-E-h: POSEIDON 0.38 s per query at ten parties; slytHErin 245.58 s; NEXUS 54 s over a 30,522 label space; report §VI-E: CryptPEFT "reports one inference in 2.26 s on CIFAR-100."

**What is wrong.** The paper's own closest serving comparator answers a CIFAR-100 query in 2.26 s where this protocol takes 1468.3 s, and the submission's ten pages contain neither number in comparison. The report explains the gap fairly (two-party, no ciphertext-by-ciphertext product, no level restoration), and that explanation is exactly what a referee needs and does not get. Deferring every unfavourable comparator latency to a companion while promoting a favourable GPU projection into the abstract is a directional editorial choice, whatever its cause.

**Fix.** Put one comparison sentence with numbers into §V-E, with the conditions that separate the systems.

---

### M8 — MAJOR. A summed statistic is described as a per-error cost, which flatters the selection rule.

**Location.** Submission §V-D: "A wrong choice gives up 0.470 of accuracy under the vote and 0.021 under the estimator." Report Table V caption: "REGRET IS THE ACCURACY GIVEN UP BY A WRONG CHOICE, AVERAGED OVER SEEDS AND SUMMED OVER THE NINE SETTINGS."

**What is wrong.** 0.470 and 0.021 are totals over nine settings, not the cost of one wrong choice. The report gives the actual per-error costs elsewhere: "The decisive case is Banking77, where choosing wrongly costs 0.48," and the estimator's CIFAR-10 error "costs 0.006." As written, the submission tells the reader that an estimator error costs 0.021 of accuracy, when 0.021 is the sum of all its errors across nine settings and no single error has that value.

**Fix.** Restate as summed regret, or give the per-error costs.

---

### M9 — MAJOR. The generalisation to a decoder vocabulary projection is contradicted by the paper's own cost scaling.

**Location.** Submission p.1, contributions; p.3 §III-B-b: "A classifier head is one such map. The vocabulary projection of an autoregressive decoder is another ... We evaluate classification only." Submission p.10, Conclusion, which repeats the position-not-task framing.

**What is wrong.** The instance named is ruled out by the paper's own numbers, not merely unevaluated. From the report's §V-E-i the training upload is `⌈769C/16,384⌉` ciphertexts at 4.0 MiB each per arrangement, which at `C ≈ 50,000` is roughly 9.4 GiB per client per arrangement. From §V-E-i the selection step costs at most `2NC` encrypted comparisons and was measured at 145.4 GiB and 7111 s for `C = 100`. The coverage-weighted merge, whose entire justification is that "clients holding a class decide its row," has no evident meaning over a vocabulary that every client's corpus covers. The paper is entitled to say the construction fixes a position; it is not entitled to name an instance whose cost its own scaling laws forbid without saying so. One sentence of scope disclaimer does not discharge that, because the extrapolation is load-bearing in the framing of the contribution.

**Fix.** Either drop the decoder instance or state the scaling that rules it out at present cost.

---

### M10 — MAJOR. The design space is restricted without argument, and the excluded alternatives are strongest exactly where this design is weakest.

**Location.** `absence`. Searched the submission for "TEE", "enclave", "trusted execution", "confidential comput", "secret shar", "garbled", "MPC" — no hit outside the index terms and the CryptPEFT sentence. The report has one hit, an aside in §VI-E.

**What is wrong.** The paper's requirement is a model no party holds in plaintext. Three families answer that requirement and none is discussed.

- **A trusted execution environment.** Confidential computing is the deployed answer to "the model may not be distributed", at roughly plaintext speed, unlimited queries, and full accuracy. Its cost is a hardware trust assumption and a side-channel history. That is a real argument to make against it, and the paper does not make it.
- **Secret-sharing MPC among the silos.** The dominant cost here is the encrypted argmax, 97 to 99 per cent of a query, which is comparison — the operation secret sharing does in milliseconds and CKKS does worst. A hybrid that computes the linear map under CKKS and the comparison under secret sharing is standard practice, and the paper neither adopts nor rejects it. Given that this single choice sets the entire latency headline, its absence is the largest unexamined fork in the design.
- **Centralisation under contract.** The paper's own Table I gives `A_pool` at 0.921 to 0.988 against `A_sel` at 0.607 to 0.789, a gap of 0.199 to 0.360. The paper's decomposition assigns most of that to "the price of the partition," which is true as arithmetic and misleading as accounting: a deployment choosing between this protocol and a data-processing agreement faces the whole gap, not the part the paper keeps on its own ledger.

**Fix.** Add a paragraph to §VI or §III-A that states why threshold CKKS rather than a TEE and rather than secret sharing, and give the argmax-under-secret-sharing comparison a number.

---

### M11 — MAJOR. The repair to Proposition 1 is unpriced and partial.

**Location.** Submission p.6 §IV-D: "A client can therefore recompute the prescribed output ciphertext and compare it as a string." Report p.8-9: "Checking a random fraction `p` of queries suffices ... at `p = 0.01` is below `10^-13` on the smallest of our tasks."

**What is wrong.** Recomputation means the checking client evaluates the full serving circuit, at 400.8 to 1468.3 s per query on one core, on top of the query cost itself. The submission gives the mechanism as a clean repair with no price at all. The report's sampling argument prices it down, but the bound it gives is against a campaign of `Cd` deviating requests; a server whose goal needs one crafted decryption — the report's own example is "a row of `θ*`" — escapes a `p = 0.01` check with probability 0.99. The submission presents the mechanism without either the cost or the limit of the argument that makes it affordable.

**Fix.** State the sampling scheme, its cost per checked query, and the class of deviations it does not catch.

---

### N1 — MINOR. The pooled reference for CIFAR-100 is a dash in the submission and an explanation in the report ("WE DID NOT RUN THE POOLED REFERENCE ON CIFAR-100"). Say so in the caption.

### N2 — MINOR. "Multiparty computation" is an index term, and no MPC construction appears in the paper.

### N3 — MINOR. §V-C opens "The protocol gives up no accuracy for protecting the contributions" one paragraph before §V-G reports 0.029 to 0.136 given up. Both are true of different things, and the adjacency invites conflation.

### N4 — MINOR. The novelty claim is a four-way conjunction — first, cryptographically secure, one-shot, federated fine-tuning, no party receives the result — and the paper's own Table III shows POSEIDON already achieving "model in plaintext: no". The claim is defensible and thin.

---

## Strongest counter-argument

Suppose I hold the opposite view: that this protocol is the wrong answer to the question it poses. The case is this.

The paper's entire value is one property, and the paper's own evidence shows the property is (a) partially surrendered, (b) defended by a control the paper will not quantify, and (c) not present in the system that was measured.

Surrendered: a participating client copies the served head to fidelity 0.90 for three to five queries per parameter. The report's own `Q ≈ 0.4Cd/ε` fit says fidelity 0.99 is reachable at ten times that. A copy at 0.99 reproduces the served model's decisions and is the participant's plaintext, with no allowance on it, and it is obtained by using the protocol exactly as designed. The property "no party ever holds the model" degrades, at a price, to "no party holds it for free."

Unquantified: the allowance that prices this appears in the submission as a symbol `Q` and never as a number. The report's number, about a thousand queries per institution on AG-News, makes the system a curiosity rather than a service. And the report says its own extraction measurements "bound the allowance from the wrong side," so the true safe allowance is lower by an unbounded factor.

Not present: §IV-G of the report says the simulator hypothesis behind Theorem 1 is unmet in the configuration measured and in the one recommended; that repeating a query recovers the collective key; and that the required duplicate check must be enforced by a party Definition 1 permits the adversary to corrupt. §V-H-b says the serving circuit's scaling constant was taken from the exported plaintext head. So the system that produced 400.8 s, `7.3×10^-5`, and thirty-two correct real answers is not the system the theorems describe.

Set that against the price. Against pooling, 0.199 to 0.360 accuracy. Against a disclosed model, 0.029 to 0.136 (as stated; 0.010 to 0.136 as Table I reads). Against any plaintext or TEE service, four orders of magnitude in latency and a hard query cap. One offline client blocks every query. A mandatory one-time selection step of 145.4 GiB.

The parsimonious alternative is that a deployment which cannot disclose a model should put it in an enclave, or keep the data central under contract, or run the comparison — 99 per cent of this protocol's cost — under secret sharing. The paper does not argue against any of these, because it does not mention them. Its contribution is real: a coherent design, a genuinely correct diagnosis that the shared map must sit after the last nonlinearity, an estimator that beats the natural vote 23 cells to 8, and an implementation in real multiparty CKKS rather than a simulation. But the paper as submitted asks a referee to accept a cost-benefit argument whose benefit is disclaimed in the companion and whose cost is reported selectively.

---

## Ignored alternatives

1. **Trusted execution.** Answers the same requirement at plaintext speed with no query cap. Rejecting it needs an argument about hardware trust and side channels, which the paper could make and does not.
2. **Secret-sharing MPC for the comparison.** The argmax is 97 to 99 per cent of a query under CKKS and is cheap under secret sharing. This is the single largest unexamined fork, and it decides the paper's headline latency.
3. **Contractual centralisation.** `A_pool` exceeds `A_sel` by 0.199 to 0.360 on the paper's own tasks. Some deployments that cannot pool legally can pool contractually.
4. **A logits interface with a much tighter allowance.** The report shows logits give exact recovery at 769 queries against `1.2×10^4` to `2.0×10^5` for labels. A deployment metering at 100 logit queries may be strictly better than one metering at `1.3×10^3` label queries, at a fraction of the cost, since the argmax is what costs. The paper never considers metering the richer interface instead of withholding it.
5. **A public labelled head initialiser.** "We use no labelled public data anywhere" is a self-imposed constraint. Where public labelled data exists, a strong public head shrinks the federation's marginal value and should be a baseline.

## Missing stakeholder perspectives

- The party that must be online for every query under `t = N`, and pays a key-switching share and 400 to 1468 s of server time per answer it did not ask for.
- The querying client, which under Section IV-D is told to recompute the serving circuit to verify provenance, at the cost of the query itself.
- The regulator invoked in the introduction via the AI Act, who would need to know that a participant can copy the served model to fidelity 0.90.
- The operator who must enforce the duplicate check that the report calls a required control, and who is the party Definition 1 permits to be corrupt.

## Unexamined premise

That the binary "model disclosed / model not disclosed" is the right axis. The paper's own extraction result makes disclosure continuous: fidelity is a dial that queries turn, and the protocol sets its position by an economic control rather than a cryptographic one. Once that is admitted, the honest comparison is not "disclosed versus not disclosed" but "what fidelity, at what query price, at what accuracy and latency cost", and on that comparison a differentially private release with a stated `ε` and a TEE with a rate limiter are both on the same axis rather than in different categories. The paper's framing places its own construction in a category of one, and the extraction section quietly dissolves the category.

## Observations, not defects

- The report is a better document than the submission. It states the smudging gap, the key recovery, the public constant, the availability cost, the "wrong side" caveat, the dropped clients, the single-seed rows, and one result it explicitly declines to treat as a result. Almost every finding above is a finding about what the ten pages omit, not about what the authors do not know. That is a fixable class of defect, and it is also why the paper as submitted cannot be assessed on its own.
- Reporting the negative charge at `N = 20, α = 0.04` was against the paper's interest and the paper reports it. So is choosing the slower level-restoration mechanism for the headline latency. Both are credited.
- The diagnosis in §III-B-b — that withholding the model forces the shared map to sit after the last nonlinearity — is correct and is the paper's best idea.
- Per the brief's rule 7: the acknowledgment discloses that Claude was used to shorten sentences and correct grammar. That is a disclosure, not an instruction to a reviewer, and I found nothing in either document that reads as an instruction directed at me.

---

## Questions to the authors

1. Theorem 1's simulator requires smudging at `2^(λ/2)` times the ciphertext noise. Your implementation smudges at eight times the fresh-encryption noise, and you recommend `2^25`, which you say also fails the rule. What does Theorem 1 prove about the system you measured? If a compliant configuration needs a larger scale and modulus, what happens to every figure in Section V-E?
2. The duplicate check you call "a required control" is enforced by the server. Definition 1 corrupts the server together with `t−1` clients. Who enforces it against that adversary?
3. Section V-H-b says the serving circuit's scaling constant was fixed from the exported head. Rerun the end-to-end correctness and latency measurements with a constant derived from a public norm bound. What is the precision, and what is the latency?
4. Publish the per-seed `A_sel` values for Table I. On AG-News the implied `A_sel` of 0.668 exceeds both arrangement means. Is that seed-wise selection, and can a reader see it?
5. Table I's stated charge range is 0.029 to 0.136. Table I as printed yields 0.010 on CIFAR-100 and 0.090 on AG-News. Which is right, and how does a reader get from the table to your number?
6. For a class held by exactly one client, `θ*_c − θ_(0,c) = Δ_(h,c)` and the denominator cancels. What does encrypting the reciprocal buy for that row? What is the coverage-inference advantage of a coalition that extracts the head, on shadow federations that vary the partition rather than holding it fixed?
7. State the query allowance in the submission, per task, in queries per client. Given that a cryptanalytic extractor costs logarithmically in the precision demanded, by what factor do you believe your measured allowance is too generous?
8. What is the measured selection cost, under which restoration mechanism, and what would the specified mechanism cost?
9. Section V-A says every number is the mean over three seeds. Table III of the report says the client-count and local-step rows are one seed. Which sentence survives, and does the `N = 10` to `N = 50` scaling claim survive with it?
10. Why threshold CKKS rather than a trusted execution environment, and why an encrypted argmax rather than a secret-sharing comparison, given that the comparison is 97 to 99 per cent of your query cost?
11. At `t = N` a single unavailable client blocks every query. What is the accuracy, latency and allowance at a threshold that tolerates churn, and did you measure any point other than `t = N`?
12. The abstract reports 48.9 to 176.6 s with GPU acceleration. Where in the ten pages is that measured, and does the companion's own statement that "a cross-library ratio at unmatched depth is not a measurement" apply to it?
