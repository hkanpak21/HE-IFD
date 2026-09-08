# Reviewer 3 — Perspective Review (cross-disciplinary, deployment and systems)

**Manuscript.** HE-OFT: Privacy-Preserving One-Shot Federated Fine-Tuning under Homomorphic Encryption.
**Venue.** IEEE Transactions on Network Science and Engineering.
**Seat.** Perspective reviewer. My background is distributed systems and the operation of networked privacy systems, not lattice cryptography. I do not assess the proofs, the literature coverage, or the statistics. I assess who could run this, what it costs to run, and whether the paper's account of those things is one an operator could act on.
**Calibration status.** `NOT_CALIBRATED`.
**Confidence.** 4 of 5. Basis: I have built and operated threshold-key and federated systems, and every cost claim below is recomputed from the authors' own reported figures. I did not verify the CKKS implementation.

---

## Summary and recommendation

The protocol is a real system, measured in real Lattigo rather than simulated, and its central design move is the right systems instinct: put the shared trained map after the last nonlinearity so the client runs the public backbone itself and the cryptographic cost never touches the model size. The paper is also unusually honest in the places this literature is usually not, saying plainly that one-shot does not mean the parties stop talking and that clients learn the labels they ask for. What the ten-page submission does not do is let a reader work out what running it costs. The dominant one-time cost (8.70 GiB of bootstrapping keys, and a selection step measured at 7111 s and 145.4 GiB) is absent from the submission, the abstract quotes a GPU latency that nothing in the ten pages measures, and the query allowance that the whole residual-leakage argument rests on is never given as a number, though the report puts it at roughly 1.3 thousand queries per client on a four-class task for the lifetime of the deployment. Separately, the availability posture is the limitation most relevant to this venue and it is the one the Scope section drops.

**Recommendation: Major Revision.** Nothing here invalidates the construction or its security argument. Every finding below is repairable, but repairing them needs page budget, one new measurement at a threshold below `t = N`, and a decision about which deployment the paper is actually for.

---

## Criterion-bound judgements

| Criterion (my remit) | Source | Judgement | Evidence anchor | Rationale | Uncertainty | Decision-bearing |
|---|---|---|---|---|---|---|
| Operability by the named deployers | Panel brief, seat scope | PARTLY_MEETS | `text: §I "A model fine-tuned on confidential records can be a regulated artifact in high-risk domains such as health, biometrics, and credit"` | The three named domains are the ones the design serves worst; the case it serves well is unnamed | I am not a lawyer; the regulatory reading is heuristic | yes, W6 |
| Honest accounting of network and systems cost | Panel brief, seat scope | DOES_NOT_MEET | `absence: §V-E — expected the bootstrapping key cost and the measured selection cost; checked §V-E paragraphs (a)-(c), Fig. 2(d) caption, Table III` | Two of the three largest costs in the system do not appear in the submission | none identified | yes, W2 |
| Evidence for reported latency | Panel brief, seat scope | PARTLY_MEETS | `text: Abstract "or48.9to176.6s with GPU acceleration"` | The submission contains no GPU measurement, method, or hardware | The report supports it as a substitution, not an end-to-end run | yes, W3 |
| Availability and liveness | Panel brief, seat scope | DOES_NOT_MEET | `absence: §V-H — expected availability among the stated limitations; checked §II-A, §V-E, §V-H, §VII` | Every measurement is at `t = N`, where one absent client stops all serving, and the submission never says so | none identified | yes, W4 |
| Enforceability of the query allowance | Panel brief, seat scope | PARTLY_MEETS | `text: §III-C "The server is not trusted with anything."` | The only defence against extraction is a counter the server keeps | Formally consistent under semi-honest; the tension is operational | yes, W1 |
| "One-shot" as used for a networked reader | Panel brief, seat scope | MEETS | `text: §I "In this paper, one-shot does not mean the parties stop communicating."` | Defined explicitly at first use and repeated in the cost section | The abstract and title carry no caveat | no, W9 is Minor |
| Value to a TNSE readership | Venue remit | PARTLY_MEETS | `absence: whole submission — expected one network-side measurement or latency model; checked §V-E, Fig. 2, Table III` | The one genuinely network-shaped result, the threshold-versus-traffic trade, lives only in the report | Venue fit proper is another seat's call | yes, W4 |

I do not total or average these.

---

## Assumption audit

**Explicit.** Semi-honest server and clients, `t`-out-of-`N` threshold decryption, one frozen public backbone shared by all parties, one public head initialiser, a per-client query allowance `Q`. All are stated. The paper is clean here.

**Implicit, and this is where my seat earns its place.** Four premises are never stated and each one is a deployment gate.

1. *The federation is closed after key generation.* The collective public key and the evaluation keys are functions of all `N` shares, and the shared head is a ciphertext under that key. Neither document says what happens when an eleventh hospital joins, when a member is acquired, or when a key share is compromised. Neither document contains the words join, leave, revoke, or re-key. A consortium in health or credit will change membership within the lifetime of one model.
2. *The allowance is enforceable because someone counts.* Functionality 1 holds `q_j` inside the ideal object. No mechanism in Section III assigns the counter to any real party. By elimination it is the server, which the same paper says is "not trusted with anything" (§III-C).
3. *A query means a real input.* The querying client computes `φ_j(x)` itself, so it can submit any vector. The report grants this explicitly ("may submit an arbitrary vector rather than a real input", §V-F). Nothing binds a metered query to an actual clinical or credit decision, so the meter cannot distinguish use from extraction.
4. *Single-core wall clock is the deployment latency.* Every timing is one core of one node. The key switch is a synchronous barrier across `N` institutions and nothing measures it across a network.

**Paradigmatic.** The paper reasons in the cryptographic protocol paradigm, where the object of study is the message pattern and the adversary is a static corruption set. A distributed-systems paradigm asks instead about the steady state: churn, key rotation, capacity, and what the operator does at 3am when a member's signing service is down. The two paradigms disagree about what `t = N` means. To a cryptographer it is the strongest collusion resistance the structure admits. To an operator it is a system with no redundancy at all, whose availability is the product of ten institutions' uptimes.

---

## Findings, most severe first

### W1. The query allowance the security argument needs is smaller than the query volume that would justify the deployment

**Location.** Submission §V-F ("A deployment can therefore set its allowance from `C`, `d` and the fidelity it concedes"), Functionality 1 step 3, §IV-E. Report §V-F, "holding it below fidelity 0.90 at `N = 10` requires `Q` below roughly `1.3×10^3` per client on AG-News and `2.2×10^4` on Banking77."

**What is wrong.** The submission never states an absolute allowance. A referee reading ten pages learns only that an allowance can be computed. Computing it from the report's own numbers gives a system with a small lifetime budget. At `N = 10` and `t = N`, holding a coalition below fidelity 0.90 caps each client at about 1.3 thousand queries on a four-class task, or roughly 13 thousand for the entire federation, for the life of the model, after which Functionality 1 returns `⊥` and never resumes. A hospital answering 100 questions a day exhausts its share in thirteen days.

Two consequences follow that the paper does not draw. First, the deployment is security-bound rather than compute-bound: at the reported 400.8 s per query, a single 64-core server produces about 13.8 thousand answers per day, so one server can exhaust the whole federation's lifetime allowance on AG-News in under a day. Even at 77 classes (1473.0 s per query, report Table VII) the entire 2.2×10^5 allowance is under two months of one server's continuous output. Second, the binding case is the small label space, which the report states is also the case where the shared arrangement wins, so the deployments that gain most from the federation are the ones that must meter hardest.

There is also no analysis of what happens when the federation retrains. The allowance is a lifetime cap on queries against one head. A second protocol run over the same partition produces a highly correlated head, so the extraction budget does not obviously reset, and neither document says whether it does. Epistemic status: open.

**What would fix it.** State the absolute allowance in the submission, in queries per client, for at least the smallest and largest label space, beside the utility the deployment gets for it. Then argue the case honestly. My reading is that the paper is being harder on itself than it needs to be: a copy at fidelity 0.90 of a model whose own accuracy is 0.649 (AG-News, Table I) is not obviously a commercial loss, and an allowance keyed to *utility* of the copy rather than to *fidelity* would be far less binding. Make that argument or concede the limit.

**Severity**: Major | **Evidence Anchor**: `text: §V-F "A deployment can therefore set its allowance from C, d and the fidelity it concedes."` | **Confidence**: 4 — arithmetic on the authors' own figures; I have sized query budgets for production inference services.

---

### W2. The submission does not report what the system costs to set up or to select, and its one cost figure is labelled with the wrong mechanism

**Location.** Submission §V-E(a) and (b), Fig. 2 panel (d) caption, §II-A. Report §V-E(j), (k), Tables VI and VII.

**What is wrong.** Four separate gaps, all in the same paragraph, and together they make the ten-page document unusable for a cost decision.

1. *The level-restoration mechanism is never named.* §II-A introduces exactly one primitive, collective refresh ("A collective refresh restores a spent level budget"). §V-E then reports "the server restoring levels", which is server-side bootstrapping under collectively generated keys, a mechanism the submission never introduces. The report's Table VII shows the two differ by 13× in latency (400.8 s against 31.2 s at four classes) and by roughly two orders of magnitude in traffic (about 1.6 GiB per query under refresh, against 13.5 MiB under bootstrapping). A referee cannot tell which system was measured.
2. *Figure 2(d) is labelled with the other one.* Its caption reads "at `N = 10` and ring degree `2^15` under collective refresh", so the submission's only cost figure is drawn under the mechanism the protocol does not specify, sitting on the same page as latencies from the mechanism it does.
3. *The bootstrapping keys are omitted.* §V-E states "Setup costs 344 MiB per client, once." The report adds 8.70 GiB of bootstrapping keys, generated collectively in 46 s, which the specified design requires for the latency the submission reports. Total one-time cost at `N = 10` is therefore about 12 GiB, not 3.4 GiB. The submission understates federation setup by roughly 3.5×.
4. *The selection cost is given as a count, not a cost.* §V-E(b) says "selection costs at most `2NC` encrypted comparisons, once". The report measures it at 7111 s and 145.4 GiB at twenty clients and a hundred classes, under collective refresh, with 99.8 per cent of that traffic being the refreshes. Under the mechanism the protocol actually specifies the traffic would fall and, at the report's own 13× factor, the wall clock would rise to something near a day. Neither pair is measured, and neither number appears in the submission. This is the single largest cost in the protocol and it is invisible in the ten pages.

**What would fix it.** One sentence in §II-A introducing server-side bootstrapping under collectively generated keys as the specified mechanism. Relabel Fig. 2(d), or redraw it under the specified design. Add the 8.70 GiB to the setup line. Replace "at most `2NC` encrypted comparisons" with the measured selection cost and say which mechanism produced it. This costs perhaps sixty words and it is the difference between a cost paragraph and a cost claim.

**Severity**: Major | **Evidence Anchor**: `text: §V-E "Setup costs344MiB per client, once."` | **Confidence**: 5 — the discrepancy is between two documents by the same authors and is arithmetic.

---

### W3. The abstract quotes a GPU latency that the submission does not measure, does not derive, and does not qualify

**Location.** Submission abstract, "answers one query in 400.8 to 1468.3 s on one core, or 48.9 to 176.6 s with GPU acceleration". The string "GPU" occurs exactly once in the ten pages, in that sentence.

**What is wrong.** A reader of the submission alone has an accelerated end-to-end latency in the abstract with no hardware named, no method, no table, and no caveat. The report earns it, and does so carefully: it measures one level restoration under Phantom on an H100 at 2.28 s, substitutes that for the 23.1 s CPU restoration, leaves the local evaluation on the processor, and notes that the local half then dominates above four classes. That is a projection from one substituted primitive, not an end-to-end measurement, and the report even says it declines to project a single ratio against Phantom's published primitives. None of that reaches the abstract. Presenting a projected figure in the same clause and the same grammatical form as a measured one is the kind of thing a systems referee treats as a reporting fault regardless of intent.

**What would fix it.** Either drop the GPU figure from the abstract, or write "projected at 48.9 to 176.6 s by substituting a measured GPU bootstrap" and add two sentences in §V-E giving the substitution and the hardware. The second is better, because the projection is the paper's honest answer to the obvious objection that 24 minutes per query is unusable.

**Severity**: Major | **Evidence Anchor**: `text: Abstract "or48.9to176.6s with GPU acceleration, for13.5MiB of traffic."` | **Confidence**: 5 — verified by exhaustive search of the submission text.

---

### W4. Availability is the limitation this venue cares about most and it is the one the Scope section drops

**Location.** Submission §V-H, which names three limitations: linearity of the shared quantity, the allowance as an operational control, and semi-honest parties. §II-A: "Any `t` clients form a quorum, so serving does not require every client to be online" followed by "Our implementation instantiates `t = N`". Report §V-H(e): "in the configuration we measured a single unavailable client blocks every query until it returns."

**What is wrong.** The submission states the reassurance and the fact that undercuts it two sentences apart, and never joins them. The joined statement, which the report makes plainly, is that the system as measured has zero availability redundancy. Its serving availability is the product of `N` institutions' uptimes. At ten members each independently up 99.5 per cent of the time, that is about 95 per cent, or nearly eighteen days of unavailability a year, and every outage is total. For clinical decision support or credit adjudication that is not a footnote, it is the deciding operational fact.

The paper's discussion of lowering `t` is one paragraph in the report and nothing in the submission. It is also incomplete in a way that matters here. It says lowering `t` tightens the allowance because `Q_tot = (t-1)Q`, which is correct, and that per-query traffic falls with `t`, which is also correct. It does not say what lowering `t` does to accuracy or to correctness, which is nothing, so the trade is purely availability against allowance, and that is a clean result the paper should own. No point other than `t = N` is measured anywhere.

There is a second, related gap. Every latency is single-node. The serving path is client to server, server to `t` clients for the key switch, back to the server, back to the client, and it is a synchronous barrier across institutions. Nothing measures or models a round trip, a link budget, or a retry. The traffic is 13.5 MiB against 400 s of compute, an effective 34 KiB/s, so I do not expect the network to change the headline number, and the authors should say that outright because it is a real result. What the network does change is the failure model, and that is unaddressed.

**What would fix it.** Add availability as a fourth limitation in §V-H in one sentence, in the report's own words. Measure one point at `t < N`, for instance `t = 7` at `N = 10`, and report the per-query traffic and the resulting allowance beside the `t = N` figures. Give one paragraph with a latency model that names the round trips, so a reader can add their own RTT. Together these are the most TNSE-shaped material in the work and they currently live outside the submission.

**Severity**: Major | **Evidence Anchor**: `absence: §V-H — expected availability and the t = N liveness cost among the stated limitations; checked §II-A, §V-E, §V-H, §VII` | **Confidence**: 5 — the omission is verifiable by reading the section.

---

### W5. The repair for the malicious-server impossibility is stated as a working mechanism, and it is neither implemented nor costed

**Location.** Submission §IV-D, final paragraph: "A mechanism checks provenance. The serving circuit is a deterministic function of the encrypted head, the encrypted query, the evaluation keys and the public parameters, and its level restoration is deterministic as well. A client can therefore recompute the prescribed output ciphertext and compare it as a string." Report §IV-D: "Two mechanisms would remove the assumption, and we implement neither."

**What is wrong.** The submission places this immediately after Proposition 1 proves that no protocol of this message pattern realizes `F` against a malicious server. In that position, in the present indicative, it reads as a closure of the gap the proposition just opened. Three things are dropped in the cut to ten pages: that it is unimplemented, that it needs only a sampled fraction of queries (the report's `p = 0.01` argument, which is what makes it affordable), and what recomputation costs a client. Without the sampling argument an operator has to assume the check costs each client a full re-execution of a 400 to 1468 s circuit for every query, which multiplies federation compute by `N` and would make the mechanism unusable. With it, the cost is about 10 per cent of one query's compute spread across ten checkers, which is entirely practical. The submission gives the reader the discouraging reading.

**What would fix it.** Two clauses. "We do not implement it. Checking a random one per cent of queries suffices, because a deviating campaign of the length extraction requires escapes a single checker with probability below `10^-13`." That converts an overstatement into a genuinely attractive design note.

**Severity**: Major | **Evidence Anchor**: `text: §IV-D "A mechanism checks provenance."` | **Confidence**: 4 — I am reading the compression against the report; the security judgement itself belongs to another seat.

---

### W6. The introduction motivates with the three deployments the design serves worst, and never names the one it serves well

**Location.** Submission §I: "A model fine-tuned on confidential records can be a regulated artifact in high-risk domains such as health, biometrics, and credit [13]", citing Regulation (EU) 2024/1689.

**What is wrong.** As an outsider to this literature and not a lawyer, I read the cited regulation as pushing the other way. The AI Act's obligations on a high-risk system are documentation of the model (Annex IV), logging (Art. 12), transparency to the deployer (Art. 13), human oversight (Art. 14), and accuracy and robustness with post-market monitoring (Art. 15). A system in which no party holds the model, no party can inspect its weights, the interface returns a bare label with no score and no confidence, and the model cannot be revalidated without rerunning the protocol, is harder to bring into that regime, not easier. GDPR Art. 22 on automated decisions and its explanation duties point the same way. Biometric identification is Annex III high-risk precisely because it must be auditable. Epistemic status: heuristic, and I flag that I am reading regulatory structure rather than case law.

The design does have a clean deployment, and the paper never names it. It is the commercial consortium: several firms with complementary data who want a joint model and who specifically must prevent each other, or a hosting provider, from walking away with the asset. There the "never disclosed" requirement is the whole point, the parties are few and known, membership is stable, admission control makes the query meter enforceable, and a lifetime budget of thousands of queries is plausible because the model is a strategic asset rather than an operational service. Reading the paper from that starting point, every design decision looks obvious and well-judged. Reading it from the hospital, several of them look like obstacles.

**What would fix it.** Lead §I with the proprietary-asset case and keep the regulatory sentence as a secondary note, qualified. If the authors want to keep the health and credit framing, add two sentences saying what the deployer does about auditability and human oversight when the model is unreadable, because a referee from that world will ask. This is the smallest change that makes the paper's answer to "who runs this" survive contact with the setting it names.

**Severity**: Major | **Evidence Anchor**: `text: §I "which is not permitted where the model is itself a regulated or proprietary asset."` | **Confidence**: 3 — I have deployed systems into regulated environments, but I am not a lawyer and the reading of the AI Act is structural rather than authoritative.

---

### W7. The federation is closed after key generation and neither document says so

**Location.** `absence`. Submission §II-A and §V-E; report §V-H. Neither document contains join, leave, revoke, re-key, or churn other than one use of "churn" in report §V-H(e).

**What is wrong.** The collective public key, the evaluation keys, the 344 MiB of per-client shares, the 8.70 GiB of bootstrapping keys and the encrypted head are all bound to one fixed set of `N` parties. Adding a member, removing one, or rotating a compromised share requires regenerating the key material and, because the head is a ciphertext under the old collective key, redoing the aggregation and the selection. The paper's own numbers put that at roughly 12 GiB of key material plus a selection step it measured at 7111 s and 145.4 GiB. A consortium of ten hospitals or banks will change membership more than once in the deployed life of one model. The threshold literature has standard answers here and the paper gestures at none of them.

**What would fix it.** One sentence in §V-H stating that membership is fixed at key generation and that changing it requires a fresh setup and aggregation, with the cost. If proactive resharing applies, say so and cite it. Do not leave it to the reader to discover.

**Severity**: Minor | **Evidence Anchor**: `absence: submission and report — expected treatment of member join, leave, or key rotation; checked §II-A, §III, §V-E, §V-H of both documents by keyword and by reading` | **Confidence**: 4 — verified by exhaustive keyword search plus reading of both scope sections.

---

### W8. "One-shot" is defined correctly in the body and not in the abstract or the title

**Location.** Submission title and abstract, against §I ("In this paper, one-shot does not mean the parties stop communicating. It means that no intermediate training artifact is ever exposed") and §V-E(b) ("It is not silent").

**What is wrong.** The in-body handling is exemplary and I credit it below as a strength. The problem is that a networked-systems reader meets the term first in the title and the abstract, where "one-shot" against a background of one-shot FL means one round of communication, full stop. What the protocol actually asks of a member is a permanent commitment: hold a key share, stay online, and contribute a key-switching share to every query anyone asks, forever. That is the opposite of the operational posture "one-shot" suggests, and it is the single most important thing for an operator to know before signing up.

**What would fix it.** One clause in the abstract. "One-shot refers to the single training contribution; the parties remain online to serve." Six words of page budget for the misreading it prevents.

**Severity**: Minor | **Evidence Anchor**: `text: Abstract "the first cryptographically secure one-shot federated fine-tuning protocol in which no party receives the trained result"` | **Confidence**: 5 — the caveat is present in §I and absent from the abstract.

---

### W9. The measurement environment is under-specified for a systems claim

**Location.** Submission §V-E: "Timings are single-run wall clock on one core of a VALAR CPU node."

**What is wrong.** No processor model, no clock, no memory, no library version pinned beyond "Lattigo [27]", and single-run with no repetition or variance. The headline latency of the paper rests on this sentence. A reader cannot tell whether 400.8 s is a fast core or a slow one, and a factor of two in single-core performance is entirely ordinary across the machines a reviewer might have in mind.

**What would fix it.** Name the processor and its clock, state the Lattigo version, and say how many runs. One sentence.

**Severity**: Minor | **Evidence Anchor**: `text: §V-E "Timings are single-run wall clock on one core of a V ALAR CPU node."` | **Confidence**: 5 — verified in text.

---

### W10. Two reported numbers I could not reconcile, both of which change a deployment figure

**Location.** (a) Report §V-E(e), "Traffic follows the same law, at 2.0 MiB per participating client", against report Table VI and submission §V-E, which give `8.5 + 0.5N` MiB and therefore 0.5 MiB per key-switching share. (b) Submission §V-G, "The quantity `A_dis − A_sel` runs from 0.029 to 0.136 across the five tasks", against Table I, where CIFAR-100 gives `0.784 − 0.774 = 0.010` and no task gives 0.029.

**What is wrong.** (a) is a 4× disagreement on the per-query key-switching traffic within one document, which moves the headline per-query total at `N = 10` between 13.5 MiB and 28.5 MiB. It may be a ring-degree or modulus-chain difference, in which case say so at both sites. (b) The stated lower bound on the price of never disclosing the model cannot be reproduced from the table on the facing page, and the abstract inherits it as "0.03 to 0.14". If `A_sel` is the per-seed selected arrangement rather than the better column mean, say so in the caption.

**What would fix it.** Reconcile both, or state the condition that separates them.

**Severity**: Minor | **Evidence Anchor**: `text: report §V-E "Traffic follows the same law, at2.0MiB per participating client"` | **Confidence**: 4 — arithmetic; the accuracy discrepancy may have an explanation the table does not carry.

---

## Strengths

1. **The term is defined honestly and the honesty is repeated where it costs something.** §I says "In this paper, one-shot does not mean the parties stop communicating", and §V-E(b) opens "It is not silent" before reporting the per-query traffic. Most papers in this area let the reader believe the stronger thing. `text: §V-E "It is not silent. Key generation precedes it"`

2. **The cost is measured, not simulated, and the encrypted path is checked against the plaintext one.** §V-E states "We do not simulate the cryptography" and §V-E(c) reports the encrypted argmax agreeing with the plaintext maximum to `7.3×10^-5`. The report goes further and runs thirty-two real answers on a recorded head. For a protocol paper this is well above the norm and it is what makes the cost findings above possible at all. `text: §V-E "We do not simulate the cryptography."`

3. **The architectural move is derived from the deployment constraint rather than asserted.** §III-B derives the position of the shared map from the requirement that the querier build its own query, and the consequence, that the cryptographic cost is independent of the backbone size, is the reason the system is buildable at all. This is the right systems instinct and the paper reasons to it rather than from it. `text: §III-B "The trained quantity that is shared must therefore attach after the last nonlinearity."`

4. **The residual channel is named and priced instead of denied.** §V-F treats extraction as the remaining channel, gives a scaling in `C` and `d`, and §V-F(a) states that a released model "is subject to no allowance because there is nothing to meter". Naming the channel you cannot close is the correct posture and it is rare. `text: §V-F "bounded by the query allowance rather than eliminated"`

5. **Table III positions the work on the axes an operator would use.** Rounds, protection mechanism, whether any party holds plaintext, and what the querier receives. Those four columns are exactly the decision variables, and the table makes the paper's niche legible in ten seconds. `table: Table III`

---

## Cross-disciplinary connections

**Parallel work the paper does not use.** Kairouz et al., *Advances and Open Problems in Federated Learning*, FnT ML 2021, is already cited as [29] but only for the training-time versus final-model attack separation. Its systems material on client availability and participation is directly on point for W4 and costs no new citation slot. Bonawitz et al., *Towards Federated Learning at Scale: System Design*, MLSys 2019, is the canonical measurement of what availability and dropout actually look like in a deployed federated system, and it is the natural anchor for a `t < N` argument.

**Borrowing opportunities.** Two, and both would strengthen the weakest seam.

*Making the meter adaptive.* The paper's defence against extraction is a fixed counter. The model-stealing defence literature moved past counters some years ago. Juuti, Szyller, Marchal and Asokan, *PRADA*, IEEE EuroS&P 2019, detects extraction from the distribution of the query stream rather than its volume, which is exactly the right shape here because the paper's own report says the adversary submits arbitrary feature vectors rather than real inputs. Adversarial feature vectors and real clinical features do not look alike. A distributional check would let a deployment raise `Q` substantially, which directly relieves W1, and it costs nothing cryptographically because the server already sees which client asked and how often.

*Binding a query to a real input.* Tramèr and Boneh, *Slalom*, ICLR 2019, splits a network between a trusted enclave and an untrusted accelerator and verifies the outsourced linear algebra. The same idea applied at the client, attesting that `φ_j(x)` came from a real input through an attested feature extractor, closes assumption 3 in my audit and turns the meter from a counter into a genuine usage bound. The paper's threat model has no trusted hardware and I am not asking it to adopt one, but a paragraph saying what an attested client would buy would answer the first question any deployer asks.

*Membership change.* For W7, proactive secret sharing (Herzberg, Jarecki, Krawczyk and Yung, CRYPTO 1995) is the standard reference for refreshing threshold shares without reconstructing the secret, and is the obvious place to point when saying what a long-lived deployment would need.

**Methodological borrowing.** The paper reports single-node wall clock. Network measurement practice would ask for a WAN-emulated run, which on Linux is a `tc netem` profile with a plausible inter-institution RTT and link budget, plus one run with a member artificially unavailable to show what serving does. That is a day of work, needs no new cryptography, and would convert the venue-fit question from a judgement call into a measurement. Epistemic status of my expectation that it would not move the headline latency: heuristic, based on the 34 KiB/s effective rate computed above.

---

## Practical impact

**Real-world application.** In plain terms: a query takes between 6.7 and 24.5 minutes on one core, or a projected 49 seconds to 2.9 minutes on a GPU, and moves 13.5 MiB at ten clients. The traffic is nothing. The latency is the whole story, and it puts the system firmly in the batch and offline-decision class. Nobody serves an emergency department or a point-of-sale credit decision at 24 minutes a query. What this is usable for is periodic adjudication where an hour of latency is acceptable and the value is in the joint model existing at all. The paper should say which class of application it is aiming at, because a reader who assumes interactive serving will reject it on the latency alone and a reader told it is batch adjudication will find the numbers reasonable.

**Implementation feasibility.** The barriers, in the order an operator hits them: agreeing one public backbone and initialiser across institutions with different legal and procurement postures; standing up an always-on threshold signing service at every member, since `t = N` means every member is on the critical path of every query; a one-time setup of roughly 12 GiB of key material at ten clients; a selection step that the report measures in hours and hundreds of gigabytes and that the submission does not mention; and a lifetime query budget in the thousands. None of these is fatal and none is hidden by bad faith. All of them are invisible to a reader of the ten pages.

**Stakeholders the paper does not consider.** The server operator, who must be honest for Theorem 2, must hold the allowance counter, must be trusted for availability, and gets no analysis of its capacity or its incentives. The end user or data subject, who receives a decision from a model that no party can inspect and no party can explain. And the member that wants to leave, whose exit is not modelled at all. The paper's own line "The server is not trusted with anything" (§III-C) is the sentence I would most want revised, because in the deployment it is trusted for availability, for metering, and for honest evaluation under Theorem 2, and the report says two of those three plainly.

---

## Broader implications

**Ethical.** The design's central property, that no party can read the model, is also the property that makes the decisions it produces unauditable. A wrongly refused credit application or a missed diagnosis cannot be traced to a weight, a score, or a confidence, because the interface returns one integer. That is a genuine tension between two privacy goods and the paper is well placed to discuss it, since it has thought harder than most about what the interface reveals. Discussing it would also strengthen the paper against the objection in W6.

**Social.** The construction's utility comes from coverage, and the parties that gain most are the ones with the least class coverage, which in practice means the smaller institutions. Table I supports this: a client alone reaches 0.20 to 0.48 while the federation reaches 0.61 to 0.79. That is a real equity argument for the design and the paper makes it only as a technical observation. It is worth one sentence in §I as motivation, and it is more defensible than the regulatory one.

**Future directions from my seat.** Measure at `t < N`. Make the meter distributional rather than a counter. Model membership change. And state the application class the latency admits.

---

## Reading recommendations

All four below are references I can attest exist. I have not re-verified page numbers.

- Bonawitz et al., *Towards Federated Learning at Scale: System Design*, MLSys 2019. For W4. The reference point for what client availability looks like in a deployed federated system, and the argument for why `t = N` is not an operating point.
- Juuti, Szyller, Marchal, Asokan, *PRADA: Protecting Against DNN Model Stealing Attacks*, IEEE EuroS&P 2019. For W1. Detecting extraction from the query distribution rather than the count, which is the lever that would let a deployment raise `Q`.
- Tramèr, Boneh, *Slalom: Fast, Verifiable and Private Execution of Neural Networks in Trusted Hardware*, ICLR 2019. For assumption 3 of my audit. The same split-the-work architecture, with attestation, and the natural way to bind a metered query to a real input.
- Herzberg, Jarecki, Krawczyk, Yung, *Proactive Secret Sharing Or: How to Cope With Perpetual Leakage*, CRYPTO 1995. For W7. Threshold share refresh across a long deployment life.
- Regulation (EU) 2024/1689, Articles 12 to 15 and Annex IV, and GDPR Article 22. Both regulations are already cited as [13] and [3]. For W6, the specific provisions are what a deployer in the named domains must satisfy, and the paper should engage with them rather than cite the regulations as a premise.

No `[UNVERIFIED]` leads. I omitted the ones I could not attest.

---

## Questions for the authors

1. Who holds the query counter `q_j` in the real protocol, and what happens to the extraction bound if that party misbehaves? §III-C says the server is not trusted with anything, while Functionality 1 makes the allowance the only bound on the residual channel. Since `t = N` means every client already participates in every key switch, could the quorum itself count, and would that be a stronger story than trusting the server?
2. State the allowance as a number in the submission. At `N = 10` on AG-News the report gives roughly 1.3 thousand queries per client for the life of the model. Is that the figure a deployment should plan against, and what application does the federation have in mind that fits inside it?
3. Which level-restoration mechanism produced the submission's 400.8 s and 1468.3 s, and why is Figure 2(d) labelled with the other one? §II-A introduces only collective refresh.
4. What is the total one-time setup cost of a ten-client federation, including the 8.70 GiB of bootstrapping keys the report reports and the submission does not?
5. What does the selection step cost under the mechanism the protocol specifies? The report measures 7111 s and 145.4 GiB at twenty clients and a hundred classes under collective refresh, and states that the specified design was not measured for this step.
6. Have you run a single point at `t < N`? If not, what stops it beyond library support, and would you state the availability of the `t = N` configuration in §V-H in the report's own words?
7. How does a member join or leave, and how is a compromised key share rotated? Neither document addresses it, and the cost of a fresh setup plus re-aggregation appears substantial.
8. Does the query allowance reset when the federation retrains? A second run over the same partition produces a correlated head, so it is not obvious that the extraction budget composes as a fresh budget.
9. Would you reframe the motivation around a commercial consortium that must prevent its own members from taking the model, rather than around the AI Act? The design fits that case cleanly and the regulatory obligations on high-risk systems seem to pull against an unreadable model.
10. Does `A_dis − A_sel` reach 0.029 anywhere in Table I? CIFAR-100 gives 0.010 on the printed figures.
11. Is the key-switching share 0.5 MiB or 2.0 MiB per participating client? Report Table VI and report §V-E(e) disagree, and it doubles the per-query total.

---

## Integrity note

Per rule 7 of the brief, I checked the manuscript for text addressed to a reviewer. I found none. The acknowledgment discloses that the authors used an assistant to shorten sentences and correct grammar, which I read as a disclosure and not as an instruction, and which I did not weigh in any judgement above.

## Coverage receipt

Not required. Both the strengths and the weaknesses lists are non-empty.
