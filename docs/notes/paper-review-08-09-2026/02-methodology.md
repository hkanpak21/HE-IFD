# Reviewer 1 — Methodology

Manuscript: *HE-OFT: Privacy-Preserving One-Shot Federated Fine-Tuning under Homomorphic Encryption*
Venue: IEEE TNSE. Seat: research design, statistical validity, reproducibility.
Read: `SUBMISSION.txt` in full; `TECHNICAL-REPORT.txt` at every point the submission defers to it.
Date: 2026-09-08.

## Summary and recommendation

The construction is real, the cryptography is implemented rather than simulated, and one encrypted query is checked end to end against its plaintext answer. The experimental section that supports it is not yet reportable. Three seeds carry every accuracy claim, no dispersion statistic, interval, or test appears anywhere in either document, and named conclusions ride on differences as small as 0.003 and 0.026. The quantity the abstract reports, `A_sel`, appears in no table of the submission, and two of its five per-task values cannot be reconciled with Table I. The federation size varies silently across tasks and seeds, the "global test set" of Table I is an undisclosed subsample, the selection rule's only baseline is arithmetically the opposite constant rule, and the query allowance — the paper's sole operational privacy control — rests on a fit whose `d` exponent no experiment identifies.

**Recommendation: Major Revision.**

No single finding below is Critical: none of them touches the protocol, the never-disclosed property, or the cryptographic implementation, and every one is repairable with disclosure plus a bounded amount of additional measurement. The recommendation is driven by their number and by the fact that almost all of them are disclosures the technical report makes and the ten-page document drops. A referee holding only the submission cannot check a single headline number in the abstract.

Nothing in either document reads as an instruction addressed to a reviewer. The acknowledgment that Claude was used to shorten sentences and correct grammar (p. 10) is a disclosure, and I treated it as such.

## Strengths, briefly

- **S1.** The cryptographic layer is measured, not modelled. Lattigo, real multiparty CKKS, and TR §V-E(g) runs thirty-two encrypted answers on a recorded AG-News head against the plaintext answers, including two the head gets wrong, and reports that the encrypted path reproduces the errors. That is the right correctness test and few papers in this area run it. *Empirical.*
- **S2.** The selection rule's failure mode is diagnosed rather than observed. TR §V-D quantifies the bias it corrects: the personal arrangement's locally measured accuracy "exceeds its true global accuracy by 0.28 on average", against 0.02 for the shared arrangement. A mechanism plus its magnitude is a stronger result than a win rate. *Empirical.*
- **S3.** Unfavourable results are reported. The randomised-response defence fails (TR Table IX), the bisection extraction variant loses in 13 of 15 cells, the disclosure charge is negative on one CIFAR-10 partition, and TR §IV-G states plainly that the measured smudging does not meet the condition the simulator needs. Papers that report the last of these are rare.
- **S4.** The authors repeatedly decline comparisons they could have claimed: the 0.949 against 0.503 margin ("We do not present that margin as a result", p. 7), no single GPU ratio, no cross-library ratio at unmatched depth. The instinct is right and I want it applied to the accuracy tables too.

---

## Findings

### F1 — Three seeds, and not one dispersion statistic anywhere

**Location.** Table I and its caption (p. 6); Table II (p. 7); §V-A "every number is the mean over three seeds" (p. 6). Also TR Tables II–V, VIII, IX.

**Severity: MAJOR.**

**What is wrong.** Every accuracy in both tables is a three-seed mean reported to three decimals with no standard deviation, no range, no interval, and no test. The paper then reads conclusions off differences that three seeds cannot resolve:

- CIFAR-100, shared head 0.748 against personal adapter 0.774, a difference of 0.026. On a 2,000-example test set the 95 per cent half-width from test sampling alone is 0.018, before any seed variance is counted. This cell is one of the two that support "Neither arrangement dominates the other, so the federation must select between them" (p. 7), the motivation for the third claimed contribution.
- DBpedia, 0.789 against 0.754, a difference of 0.035.
- Table II row 3, `A_dis − A_sel = −0.003`, quoted in §V-C as the lower end of a range. TR §V-C reveals this holds "on two seeds of three" — a sign that flips across the seed set is reported in the submission as a value.

Three seeds also cannot be justified by cost here: the text tasks are capped at 20,000 training examples with a rank-8 adapter over a frozen encoder, which is minutes of GPU time per cell.

**Epistemic status.** The binomial half-widths above are my computation from the test-set sizes the technical report gives (§V-A); the absence of any dispersion statistic is directly verifiable.

**What would fix it.** Report, for every cell of Tables I and II, the mean with either the standard deviation over seeds or the min–max. Raise the seed count to at least five, and to ten for any cell whose asserted difference is below 0.05 (DBpedia shared-versus-personal, CIFAR-100 shared-versus-personal, all four Table II rows). Report every asserted difference as a *paired* seed-level difference with a 95 per cent interval, since the two arrangements share a partition draw and pairing removes most of the variance. State the test-set size per task so a reader can separate test sampling from seed variance.

---

### F2 — `A_sel` is the abstract's headline quantity and appears in no table; two of its five values cannot be reconciled with Table I

**Location.** Abstract (p. 1); §V-A definition of `A_sel` (p. 6); Table I (p. 6); §V-G (p. 8).

**Severity: MAJOR.**

**What is wrong.** Table I reports two column means, "shared head" and "adapter", and bolds "the better one". It does not report `A_sel`, which §V-A defines as "the accuracy of the servable arrangement that section V-D selects" — a per-seed choice. The two are not the same number, because the selection can differ by seed. §V-G then states that `A_dis − A_sel` "runs from 0.029 to 0.136 across the five tasks". Taking the differences of Table I's own printed columns:

| task | `A_dis` | bolded servable | difference from Table I | value the paper uses (TR §V-G) |
|---|---|---|---|---|
| AG-News | 0.739 | 0.649 | 0.090 | **0.071** |
| TREC | 0.711 | 0.607 | 0.104 | 0.104 |
| DBpedia | 0.925 | 0.789 | 0.136 | 0.136 |
| Banking77 | 0.760 | 0.686 | 0.074 | 0.075 |
| CIFAR-100 | 0.784 | 0.774 | 0.010 | **0.029** |

Three reconcile. Two do not, and they are the two endpoints of the range the abstract quotes ("gives up 0.03 to 0.14"). The technical report explains the AG-News case indirectly: on one seed the partition drops three clients, the shared head falls to 0.402, and the estimator switches to the personal adapter. So the discrepancy is arithmetic that is correct and unrecoverable from the submission. The same holds on CIFAR-100, where `A_sel = 0.755` implies the estimator picks the shared head on at least one seed although Table I bolds the adapter.

**Epistemic status.** The arithmetic is verified against the printed tables. The reconstruction of *why* the two differ is mine, from TR §V-D and §V-C; the submission gives a referee no way to reach it.

**What would fix it.** Add an `A_sel` column to Table I, per task, as the seed-level mean of the selected arrangement, and give the per-seed selection alongside it. Then the abstract's range and §V-G derive from the table in front of the reader.

---

### F3 — The federation size varies across tasks and seeds, and the submission does not say so

**Location.** Table I caption (p. 6); §V-A (p. 6); Table II (p. 7). Disclosed only in TR Table II caption and TR §V-C(a).

**Severity: MAJOR.**

**What is wrong.** The technical report's Table II caption states that on one seed the Dirichlet draw "assigns fewer than twenty samples to some clients, which cannot train, so the effective federation is seven on AG-News and nine on TREC", and TR §V-C(a) states that at `N = 20`, `α = 0.04` the effective size is "17 to 19 rather than 20". The submission carries neither sentence. Table I is presented at "N = 10" throughout and Table II at "N = 20".

Three consequences.

1. **The cross-task reading is confounded.** §V-B reads Table I across rows to conclude that "the preferable arrangement changes with the size of the label space". The technical report's own sensitivity analysis (TR §V-B(a)) contradicts the label-space explanation and attributes the crossover to *coverage*: "The crossover is therefore not a property of the label space alone... but of coverage." Coverage is a function of `N` and `α` jointly. Dropping three of ten clients on AG-News moves exactly the variable the explanation turns on, and it flips that cell's outcome — the shared head falls from a 0.649 mean to 0.402 on that seed and the estimator switches arrangement.
2. **The threshold is undocumented and unjustified.** Twenty samples is a property of the training code, not of the protocol. It appears in neither document as a stated rule with a reason, and it discards clients on a quantity correlated with the outcome.
3. **The published-partition claim in §V-C is weakened.** The justification for Table II is "The peer group evaluates on different tasks from ours, so we ran our protocol on theirs" (p. 7). At `α = 0.04` the protocol was run at 17 to 19 clients, not the 20 of the cited configuration. That is not the published partition, and the cell in question is the one the paper singles out for a negative disclosure charge.

**Epistemic status.** *Empirical, and established only by the technical report.* A referee reading the ten pages cannot know the federation size varies.

**What would fix it.** State the drop rule and its threshold in §V-A. Report the effective `N` per task per seed in the Table I caption and per row in Table II. For Table II, either re-run at the published `N` (for example by resampling the Dirichlet draw until every client is trainable, and saying so) or withdraw the claim that the peers' partitions were reproduced. For §V-B, hold coverage fixed — report the mean number of clients per class row alongside `C` — before attributing the crossover to label-space size.

---

### F4 — Table I says "the global test set"; the measurement is an undisclosed subsample

**Location.** Table I caption, "ACCURACY ON THE GLOBAL TEST SET" (p. 6); §V-A (p. 6); Table II caption, "ON THE WHOLE 10,000-IMAGE TEST SET" (p. 7).

**Severity: MAJOR.**

**What is wrong.** TR §V-A states that "Each text task draws at most 20,000 training and 5,000 test examples under the seed, and each vision task at most 10,000 and 2,000." The submission omits this sentence. So Table I's AG-News and DBpedia figures are on 5,000-example subsamples, CIFAR-100 on 2,000, and TREC on its whole 500-example test set. DBpedia's official test set holds 70,000 examples; 93 per cent of it is discarded for no stated reason, at a direct cost in precision on exactly the differences F1 says are too small to resolve.

The defect is sharpened by the neighbouring table. Table II announces "THE WHOLE 10,000-IMAGE TEST SET" in its caption. A referee reading the two captions together will read Table I's "global test set" as the same commitment. It is not.

**Epistemic status.** *Empirical, and established only by the technical report.*

**What would fix it.** Put the test-set size per task in Table I's caption or in §V-A. Where the full test set is available and cheap — DBpedia, AG-News, CIFAR-100 — evaluate on all of it, as was already done for CIFAR-10 in Table II.

---

### F5 — The selection rule's only baseline is arithmetically the opposite constant rule, and "27 cells" is nine settings

**Location.** §V-D (p. 7), "picks correctly in 8 of 27 cells... picks correctly in 23, or 24"; TR Table V; TR §V-D.

**Severity: MAJOR.**

**What is wrong.** Two problems, both decision-bearing for the third claimed contribution.

**(a) The baseline is a constant.** TR §V-D states that the held-out vote "selects the personal adapter every time" across the fifteen task cells, and "chooses the personal adapter in all twelve" CIFAR-10 cells. The vote is therefore not a rule with a decision boundary. It is the constant rule *always serve the personal adapter*, and its 8 of 27 is the number of cells on which that constant is right. The complementary constant, *always serve the shared head*, is nowhere reported. From the report's own counts it scores 19 of 27: 8 of the 15 task cells (the vote is right on 7 of them, and the counts partition) and 11 of the 12 CIFAR-10 cells ("The shared head over the bare backbone wins in eleven of them"). Against that baseline the estimator's margin is 4 cells out of 27, not 15.

The estimator's real advantage lies elsewhere, and the paper does not make the argument. Always-shared is wrong on Banking77, where TR §V-D says a wrong choice costs 0.48, so its summed regret is roughly 0.53 against the estimator's 0.029. That is the strong case for the encrypted selection machinery — which TR §V-E(i) prices at 7,111 s and 145.4 GiB at twenty clients and a hundred classes — and it is a regret argument, not a cell-count argument. The paper leads with the weaker of the two.

**(b) The unit is inflated.** The 27 cells are 9 settings at 3 seeds. The correct arrangement is a property of the setting, and both rules behave near-identically across seeds within one: TR §V-B(a) reports the estimator's choice is stable "on every seed in each case", and TR §V-D reports it "selects correctly on all three seeds" on Banking77. Seeds are therefore not independent replicates of the decision. Nor are the four CIFAR-10 partitions independent settings: they are four `(N, α)` points on one dataset, one backbone, one task. The honest independent unit is about six, and any comparison at 27 will read as far stronger than the design supports.

**Epistemic status.** *Empirical.* The 19 of 27 figure is derived arithmetically from the report's own stated counts, conditional on the vote selecting the personal adapter in every cell, which TR §V-D asserts twice. I did not have per-cell data to confirm it directly.

**What would fix it.** Add both constant rules to TR Table V, with their regret. Report the comparison at the setting level (9 rows, each a per-setting outcome and per-setting mean regret) and, if a test is wanted, an exact paired sign test over settings. Add at least one intermediate baseline that is neither constant nor the raw vote — the obvious one is the vote with the personal arrangement's measured accuracy debiased by a single constant, since TR §V-D has already measured that bias at 0.28. Without it, the reader cannot tell whether the win comes from the prior weighting the paper argues for or from any bias correction at all.

---

### F6 — The regret sentence in §V-D misreports the statistic and mixes two rules

**Location.** §V-D, p. 7: "A wrong choice gives up 0.470 of accuracy under the vote and 0.021 under the estimator."

**Severity: MAJOR.**

**What is wrong.** TR Table V's caption defines regret as "THE ACCURACY GIVEN UP BY A WRONG CHOICE, AVERAGED OVER SEEDS AND SUMMED OVER THE NINE SETTINGS". 0.470 is therefore a sum over nine settings, not what a wrong choice gives up. The largest single wrong choice under the vote is TREC, at 0.607 − 0.429 = 0.178; AG-News is 0.170 and DBpedia 0.035. No wrong choice under the vote gives up anything close to 0.470, and the sentence as written inflates the harm by roughly a factor of three against the worst case and nine against the typical one.

The same sentence pairs "23" — TR Table V's zero-fill row, whose regret is 0.029 — with "0.021", which is the rare-class-fill row. The two numbers come from different rules.

**Epistemic status.** *Verified.* The per-setting regret ceiling follows from Table I's own columns; the row mixing follows from TR Table V.

**What would fix it.** Write it as the summed regret over nine settings and quote one rule's pair of numbers, or report the mean per-setting regret and say so. Either is one sentence.

---

### F7 — The extraction scaling law does not identify `d`, asserts the `ε` exponent, and the report says it bounds the allowance from the wrong side

**Location.** §V-F (p. 7–8), "A deployment can therefore set its allowance from `C`, `d` and the fidelity it concedes"; §IV-E (p. 5), "The second rests on a measurement"; TR §V-F(a) and TR §V-F(b).

**Severity: MAJOR.**

**What is wrong.** The allowance `Q` is the paper's only non-cryptographic privacy control. TR §V-F(a) fits `Q ≈ 0.4·C·d/ε` on three tasks and licenses transfer: "without repeating this experiment". Three problems.

1. **`d` never varies.** Every extraction cell uses RoBERTa-base, `d = 768`. With one value of `d` the data cannot distinguish `Q ∝ d` from `Q ∝ d²` or from no dependence at all. The exponent on `d` is not estimated; it is assumed. Since the formula's whole purpose is to be applied at a deployment's own `C` and `d`, this is the load-bearing term, and it is unidentified.
2. **The `ε` exponent is asserted, not fitted.** TR §V-F(a) reports fidelity 0.80 at "roughly 1.5 times" `Cd`, 0.90 at "between three and five times", and 0.95 at "roughly ten times". A log–log fit through the two endpoints gives an exponent of 1.37 on `1/ε`, not 1.0. Extrapolated to fidelity 0.99 the stated law gives 40·`Cd` where the measured trend gives about 90·`Cd`.
3. **The residuals on `C` change sign.** At `ε = 0.1` the law predicts 12,288 / 43,008 / 236,544 queries against measured 1.2×10⁴ / 5.0×10⁴ / 2.0×10⁵, ratios of 0.98, 1.16 and 0.85. On Banking77 the law overstates the adversary's cost by 18 per cent, so an allowance set from it permits the adversary past the target fidelity. The law is not reliably conservative, which is the only property a privacy control needs.

Fourth and most serious for the submission specifically: TR §V-F(b) states that neither measured strategy "is the attack a cryptanalyst would mount", that published constructions cost "a factor logarithmic in the precision demanded rather than linear in it", and that "our figures bound the allowance from the wrong side". The submission drops that sentence and keeps "A deployment can therefore set its allowance from `C`, `d` and the fidelity it concedes."

**Epistemic status.** The exponent fit and the residuals are my arithmetic on the report's stated multipliers and query counts, and the multipliers are given as "roughly", so the 1.37 is indicative rather than an estimate with an interval. The `d` identification problem and the wrong-side admission are *proven* from the documents as they stand.

**What would fix it.** Run the extraction sweep at a second feature dimension — a distilled encoder at `d = 384` or ViT-L at `d = 1024` costs nothing cryptographic, since the attack is a linear fit on cached features. Fit the law with residuals and an interval on both exponents and state the range of `C`, `d` and `ε` in which it was validated. Carry the "wrong side" caveat into the submission's §V-F, and derive the allowance from a conservative multiple of the measured `Q` rather than from `Q` itself.

---

### F8 — The membership null carries no power statement in the submission

**Location.** §V-F, p. 8: "published membership attacks against it and against the head in plaintext both sit at chance." TR §IV-F1.

**Severity: MAJOR.**

**What is wrong.** The submission asserts a null with no number, no attack description, no candidate count, and no power statement. A null result is a claim about the *detection floor*, and the submission gives a referee nothing with which to locate that floor.

The technical report supplies the design — the LiRA attack of Carlini et al., 64 shadow federations per cell, 2,000 candidates, 18 cells, AUC 0.49 to 0.53, TPR 0.008 to 0.023 at FPR 0.01 — and then states the limits itself: "A thousand members resolve a true-positive rate no finer than 0.001. Every figure we report at a false-positive rate of 0.001 counts two to four examples rather than a rate." It also notes that "the shadow federations vary who trains on what while holding the coverage pattern fixed", so the design says nothing about how leakage moves with the partition, which for a coverage-weighted merge is the interesting axis. None of this reaches the submission.

What the counts actually cap. With 1,000 members, an observed TPR of 0.008 at FPR 0.01 has a 95 per cent Wilson interval of roughly [0.004, 0.016], and 0.023 gives [0.015, 0.034]. The experiment therefore cannot exclude a true-positive rate of about 0.03 at a false-positive rate of 0.01 — a threefold enrichment over chance, which in the literature this paper cites is a reportable signal, not a null. Below FPR 0.001 the design resolves nothing at all, and Carlini et al. argue precisely that MIA should be judged at FPR 10⁻³ and below. 64 shadow models is also at the low end for LiRA, whose per-example Gaussian fits sharpen with shadow count; the report does not show that the attack has saturated.

**Epistemic status.** The intervals are my computation from the counts in TR §IV-F1. The power limits themselves are the report's own words.

**What would fix it.** State in the submission what attack was run, at how many candidates, and what true-positive rate the design could have detected. Report TPR at fixed FPR of 10⁻², 10⁻³ and 10⁻⁴ with Clopper–Pearson intervals, and state the minimum detectable effect at each. Raise the candidate count until FPR 10⁻³ resolves a rate rather than two to four examples, and show the attack's AUC against shadow count so a reader can see it has converged. Then the null is a result. As written it is an absence of evidence.

---

### F9 — The cryptographic cost figures mix two mechanisms, are single-run, and the abstract's GPU number has no text behind it

**Location.** §V-E (p. 7); Figure 2 panel (d) and caption (p. 8); abstract (p. 1).

**Severity: MAJOR.**

**What is wrong.** Four separate defects in the measurement reporting.

1. **Two mechanisms, one section, no marker.** §V-E prose reports 400.8 s at four classes and 1468.3 s at a hundred. TR Table VII shows these are the *server-bootstrap* design. Figure 2 panel (d) is captioned "under collective refresh", for which TR Table VII gives 31.2 s and 113.0 s. So the same subsection carries a prose figure of 400.8 s and a panel whose four-class point is about 31 s, a thirteenfold difference, with nothing saying they are different mechanisms. A referee reading page 7 and page 8 together will conclude one of the two is wrong.
2. **The parameter statement omits the ring degree that produces the headline number.** §V-E states that "All figures use ring degree 2¹⁴ for the shallow operations and a deeper chain at ring degree 2¹⁵ for the circuits that need it." TR Table VII says the specified design restores levels at ring degree 2¹⁶. The submission's own communication figures then quote a value "at 2¹⁶", contradicting its own parameter sentence two paragraphs earlier.
3. **Single-run wall clock.** §V-E: "Timings are single-run wall clock on one core of a VALAR CPU node." A number reported to four significant figures in the abstract, from one unreplicated run on a shared cluster node, is not a measurement a reader can rely on.
4. **The abstract's GPU figure has no support in the submission.** The abstract claims "48.9 to 176.6 s with GPU acceleration". The words *GPU*, *Phantom*, *H100* and *acceleration* appear nowhere else in the ten pages. TR §V-E(f) shows the figure is a substitution: one bootstrap measured under Phantom on an H100 at 2.28 s, dropped into the CPU pipeline, "leaving the local evaluation on the processor", which the report then says "is the larger half of a query above four classes". No end-to-end GPU query was run.

**Epistemic status.** *Verified* against both documents by text search.

**What would fix it.** Report both mechanisms in one small table in the submission, as TR Table VII does, and say which produced each quoted latency. Correct the parameter sentence to name every ring degree in use. Report the median and spread of at least five runs per configuration, and drop to three significant figures. Either label the abstract's GPU range as a projection with its two components named, or remove it from the abstract until an end-to-end GPU query is measured.

---

### F10 — The four reference quantities are under-defined, and `A_dis − A_sel` is not the price it is named after

**Location.** §V-A (p. 6); §V-G (p. 8); Table I (p. 6); Table II (p. 7).

**Severity: MAJOR.**

**What is wrong.** Taking the four in turn.

- **`A_sel`** — see F2. Defined but not tabulated.
- **`A_loc`**, "the accuracy a client obtains alone". No aggregation rule over the `N` clients is given: mean, median, best, or the mean of a single seed's clients are all consistent with the text, and they differ substantially at `α = 0.1`. No dispersion across clients is reported either. This is half of the abstract's headline comparison ("0.61 to 0.79 accuracy where a client training alone reaches 0.20 to 0.48"), and the comparison is also partly structural: a client holding one or two of 77 classes cannot score well on a uniform global test set whatever it learns, so part of the reported gap is the partition and not the federation. Nothing in the paper separates the two.
- **`A_pool`**, "one model trained on the union of the clients' data". No training budget is stated. If pooled training uses the same 200 steps on ten times the data it sees ten times the examples, so `A_pool − A_dis`, which §V-A names "the price of the partition", confounds partition with compute.
- **`A_dis`**, "the merged model in which the adapter and the head are both aggregated and decrypted". `A_dis` differs from `A_sel` in two ways at once: the adapters are aggregated, and the result is decrypted. The paper states elsewhere that decryption costs nothing — §V-C, "that protection costs no accuracy, by construction". So the entire measured difference is caused by aggregating the adapters, not by disclosure. Calling `A_dis − A_sel` "the price of never disclosing a model" (§V-A) names a causal chain rather than the contrast that was measured. The paper's own data prove the point: at `N = 20`, `α = 0.04` the quantity is **negative** (Table II, −0.003), and TR §V-C(a) explains why in exactly these terms — aggregating the adapters "moves the representation toward every local task at once and improves none of them". A price that goes negative is not a price.

**Epistemic status.** The definitional gaps are *verified* by absence across both documents. The causal reading of `A_dis − A_sel` is *proven* from the paper's own §V-C claim that encryption is lossless plus the negative cell.

**What would fix it.** Name the aggregator and report the spread for `A_loc`. State the pooled training budget. Rename `A_dis − A_sel` to what it measures — the cost of retaining the adapters locally — and keep the derivation from the never-disclose requirement in §III-B where it belongs. Add one reference the paper is missing: each client's accuracy on the classes it actually holds, which would separate "the federation supplies coverage" (which is near-tautological under `α = 0.1`) from "the federation supplies quality".

---

### F11 — The CIFAR-10 cross-paper comparison is not like-for-like, and the quantity compared is zero by construction

**Location.** §V-C (p. 7); Table II (p. 7).

**Severity: MAJOR.**

**What is wrong.** The paper is admirably direct that absolute accuracy does not transfer: "Those methods train a ResNet-18 from scratch, whereas every client here fine-tunes a frozen public ViT-B/16. Absolute accuracy across papers therefore measures the backbone." It then claims a quantity that does transfer: "What compares across papers is the accuracy each method gives up for protecting the contribution... and the backbone cancels."

That claim is asserted, not established, and it does not hold in general. FedAUXfdp's cost is measured against a 0.752 baseline; HE-OFT's `A_dis` on the same partitions is 0.947 to 0.966. A method operating near ceiling has far less headroom to lose than one at 0.75, so a loss of 0.006 at 0.752 and a loss of 0.013 at 0.963 are not the same quantity even in ratio. The privacy–utility cost of a DP mechanism also depends on the sensitivity and dimension of the artifact it protects, which differ between a distilled logit vector and a head displacement.

More fundamentally, the quantity the paper contributes to this comparison is zero by definition, not by measurement: "that protection costs no accuracy, by construction, since the decrypted result matches the plaintext computation to the encoding precision of the scheme." A tautology placed beside three measured values is not a comparison, and presenting it as the outcome of a three-case taxonomy ("Read that way the peer group falls into three cases") over-reads it. The paper is right that no peer incurs the withholding charge; that is a scope difference, and it should be stated as one rather than tabulated as a comparison.

Table II compounds this by carrying no peer column at all, so the comparison exists only in prose, and by running the `α = 0.04` partition at 17 to 19 clients rather than the cited 20 (see F3).

**Epistemic status.** *Heuristic* on the headroom argument — I have not measured the interaction, and the direction is a standard property of accuracy differences near ceiling. *Proven* on the tautology point, from the paper's own sentence.

**What would fix it.** Put the peers' published numbers in Table II next to the matched HE-OFT rows so the reader sees what is and is not compared. State explicitly that HE-OFT's cryptographic protection cost is zero by construction and therefore is not an empirical finding. Retire "the backbone cancels" or support it — the cheap support is to run the protocol once with a ResNet-18 backbone at the peers' partition and show the withholding charge is stable across backbones. That single run would convert an assertion into evidence.

---

### F12 — An independent group could not rerun this

**Location.** §V-A (p. 6); §V-E (p. 7); TR §V-A. Absence checked across both documents.

**Severity: MAJOR.**

**What is wrong.** Neither document states any of the following:

- the optimizer, learning rate, batch size, or weight decay;
- what a "step" is, although "the local trajectory is 200 steps" is a stated default and local steps is a studied axis in Figure 2(c);
- the LoRA scaling factor, or how the shared public head initialiser `θ₀` is produced;
- how the adapters are aggregated for the `A_dis` reference;
- the pooled reference's training budget;
- the Dirichlet minimum-samples rule and its threshold (F3);
- the test-set sizes (F4);
- any statement of code, data, or artifact availability;
- the security level of the CKKS parameters. §V-E gives ring degrees and TR §V-E(g) gives a scale of 2⁴⁵, and TR §V-E(e) says "The ring degree is the security parameter", which is not correct on its own — the level depends on the ring degree and the total modulus together. With a fifteen-modulus chain at ring degree 2¹⁵ a reader cannot determine whether the measurement was taken at 128-bit security, and every latency and traffic figure is a function of that choice.

The last point is R2's territory on the cryptographic merits; I raise it only as reproducibility. Without it the reported costs are not comparable to any other system's, including the slytHErin, POSEIDON and NEXUS figures the technical report sets them beside.

**Epistemic status.** *Verified* by text search over both documents.

**What would fix it.** A hyperparameter table in the technical report and a pointer to it from §V-A; the security level and modulus chain stated once; and a code and artifact availability statement. For a TNSE systems paper with a real Lattigo implementation, the last is close to expected.

---

### F13 — The pooled reference is missing on CIFAR-100 with no explanation, and §V-A promises a comparison the submission never makes

**Location.** Table I, CIFAR-100 pooled cell (p. 6); §V-A, "Two differences follow, and the paper reports both" (p. 6); §V-G (p. 8).

**Severity: MINOR.**

**What is wrong.** The CIFAR-100 pooled cell is a bare em dash. TR Table II's caption says "WE DID NOT RUN THE POOLED REFERENCE ON CIFAR-100"; the submission's caption drops it. Separately, §V-A defines `A_pool − A_dis` as "the price of the partition" and says "the paper reports both", but the submission never reports that quantity for any task — the analysis lives only in TR §V-G. So the pooled column of Table I is inert in the submission, and its gap is undocumented.

On the substantive question: the paper draws no conclusion in the submission that needs the CIFAR-100 pooled value, so the missing cell does not license anything false. It does mean the vision task carries no partition reference, and the report's finding that "on three of the four text tasks `A_pool − A_dis` exceeds `A_dis − A_sel`" — which is the paper's strongest defence of its accuracy cost — cannot be checked on vision at all.

**What would fix it.** Run it; it is one centralised training run and it strengthens the paper's own argument. Failing that, mark the cell "not run" in the caption and delete "and the paper reports both" from §V-A, or report `A_pool − A_dis` per task in §V-G as the sentence promises.

---

### F14 — Over-precision

**Location.** Table I, TREC row (p. 6); §V-E latencies (p. 7); abstract (p. 1).

**Severity: MINOR.**

**What is wrong.** TREC's whole test set is 500 examples. At an accuracy of 0.607 the 95 per cent half-width from test sampling alone is 0.043, and the paper reports three decimals and derives `A_dis − A_sel = 0.104` from them. Latencies are reported to four significant figures (400.8 s, 1468.3 s, 7111 s) from single runs (F9). Reported precision should not exceed measured precision.

**What would fix it.** Two decimals on accuracies whose test set is under 1,000 examples, with the interval alongside. Three significant figures on latencies, with a spread.

---

### F15 — One numeric range names two different quantities

**Location.** Abstract (p. 1), "reaches 0.61 to 0.79 accuracy"; §V-B (p. 6), "the federated head reaches 0.61 to 0.79 on four of the five tasks".

**Severity: MINOR.**

**What is wrong.** In the abstract the range is `A_sel` over five tasks (0.607 to 0.789, using the report's per-task values). In §V-B it is the shared-head column over four of five tasks. The same two numbers denote two different quantities two pages apart, and the "four of the five" qualifier appears in one place and not the other.

**What would fix it.** Use `A_sel` in both, with the same scope, once F2's column exists.

---

### F16 — Fidelity is not normalised against the free baseline, which differs sixfold across the extraction tasks

**Location.** §V-F (p. 7–8); TR Table VIII, "majority" column.

**Severity: MINOR.**

**What is wrong.** TR Table VIII gives the majority-class share a copy achieves at zero cost: 0.488 on AG-News, 0.250 on DBpedia, 0.083 on Banking77. A common target of fidelity 0.90 therefore represents different amounts of learning per task — normalised as `(f − maj)/(1 − maj)` it is 0.805, 0.867 and 0.891. The scaling law of F7 is fitted in raw `ε`, which folds a task-dependent free baseline into the exponent it estimates, and the allowance a deployment sets from it inherits that.

**What would fix it.** Report normalised fidelity alongside raw, and fit the law on the normalised quantity. The free baseline is already in the table.

---

### F17 — Extraction and membership are measured on text only

**Location.** §V-F (p. 7–8); TR Tables VIII and IX; TR §IV-F1, "three tasks".

**Severity: MINOR.**

**What is wrong.** All extraction, all randomised-response, all LiRA and all OSLO cells use AG-News, DBpedia and Banking77 over RoBERTa-base. The vision tasks appear in the accuracy tables and nowhere in the leakage study, and §V-F's claims are stated without scope. Since a ViT feature space has different geometry from a RoBERTa one, and the paper's whole leakage argument is about a linear map over public features, the omission is not obviously harmless.

**What would fix it.** Add CIFAR-100 to the extraction sweep, or state the scope restriction in §V-F.

---

### F18 — `d` is never instantiated in the submission

**Location.** §V-F, p. 8: "The head has `Cd` parameters, where `d` is the feature dimension... A deployment can therefore set its allowance from `C`, `d` and the fidelity it concedes."

**Severity: SUGGESTION.**

**What is wrong.** The submission never gives `d` a value. A knowledgeable reader infers 768 from RoBERTa-base and ViT-B/16, but the allowance formula is presented as operational guidance and cannot be applied without it.

**What would fix it.** Six words in §V-A.

---

### F19 — Table II's printed differences do not equal the differences of its printed columns

**Location.** Table II, `A_dis − A_sel` column (p. 7).

**Severity: SUGGESTION.**

**What is wrong.** Rows 1, 2 and 4 print 0.013, 0.015 and 0.007, while their columns give 0.014, 0.014 and 0.008. This is the signature of differencing before rounding, which is correct practice, but a referee checking the table meets three mismatches with no note.

**What would fix it.** One sentence in the caption saying differences are computed before rounding.

---

## Methodological fallacies checked

Ecological inference, reverse causation, endogeneity, multicollinearity: not applicable to this design. Overfitting: the selection rule is fitted on no data and has no threshold, and I found no evidence of tuning against the test set. P-hacking and multiple comparisons: no p-value appears anywhere, so there is nothing to correct, but F1 and F5(b) are the same disease in a different form — many small differences read as findings with no correction for how many were inspected. Selection bias: **present**, in the undocumented client-dropping rule of F3, which removes units on a quantity correlated with the outcome. Confirmation bias: **not found** — the paper reports its failures (S3), including one that undermines its own defence-in-depth story.

## Questions for the authors

1. What is the standard deviation over seeds for each cell of Tables I and II? Specifically, does the CIFAR-100 shared-versus-personal difference of 0.026 hold on all three seeds, and does the `α = 0.04` charge of −0.003 have a consistent sign? (TR §V-C(a) says it does not.)
2. What is the aggregation rule for `A_loc` over the `N` clients, and what is its spread?
3. What is the sample-count threshold below which a client is dropped, where does it come from, and what were the effective federation sizes per task per seed in Table I and per row in Table II?
4. Why were AG-News, DBpedia and CIFAR-100 evaluated on subsamples when Table II evaluates CIFAR-10 on the full test set, and what do Table I's numbers become on the full test sets?
5. How does *always serve the shared head* score on the 27 cells and on regret, and how does the vote score once the personal arrangement's measured accuracy is debiased by the 0.28 that TR §V-D reports?
6. In §V-D, is 0.470 the summed regret over nine settings? If so, what does a single wrong choice actually cost under the vote?
7. What does the extraction law predict at a feature dimension other than 768, and on what evidence? Has the fit been validated at any `d ≠ 768`?
8. Given TR §V-F(b) — "our figures bound the allowance from the wrong side" — what safety factor should a deployment apply to `Q ≈ 0.4Cd/ε`, and why does that caveat not appear in the submission?
9. What true-positive rate at a false-positive rate of 10⁻³ would the membership experiment have detected, and has the LiRA AUC been shown to saturate at 64 shadow federations?
10. Which level-restoration mechanism produced the 400.8 s and 1468.3 s figures, which produced Figure 2 panel (d), and at what ring degrees? How many runs is each latency the summary of?
11. What supports the abstract's "48.9 to 176.6 s with GPU acceleration" inside the submission, given that no end-to-end GPU query was measured?
12. What is the security level of the CKKS parameters used for every reported cost?
13. Will the training code, the Lattigo protocol code, the partition seeds, and the per-cell result files be released?
