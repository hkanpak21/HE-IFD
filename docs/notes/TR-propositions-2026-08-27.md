# The technical report, 2026-08-27. What was done, and what needs you

Written overnight while you were away, on the instruction to improve the
technical report. The submission was not touched. Every gate passes.

Read the three decision items in section 3 first. They are the only things
blocking, and two of them are corrections to claims the submission currently
makes.

## 1. What landed, and the evidence

Two commits, `610b3f3` and `d0f2cef`. Both verified against `bash scripts/gates.sh`.

| | baseline | now |
| --- | --- | --- |
| submission pages | 10 | 10 |
| submission prose words | 6583 | 6583 |
| submission rewritten | 0 | 0 |
| submission bibliography | 41 | 41 |
| report pages | 20 | 19 |
| report rewritten | 0 | 0 |
| report bibliography | 110 | 111 |
| both compile | clean | clean |

The submission is unchanged on every measure. That is the point. Everything
below is inside `\tronly` or is a `\paperonly` wrapper that renders in the
submission exactly as the text did before.

### 1.1 The report carried thirty-one paragraphs twice

The largest defect in the report and nobody had seen it. Thirty-one paragraphs
rendered twice in `main-tr.pdf`. In each case a short version sat unwrapped, so
it rendered in both documents, beside a `\tronly` long version that rendered
again in the report. Twelve of them were in Related Work, so most of that
section appeared twice.

Wrapping the short version in `\paperonly` fixes it. The submission is
byte-identical, because `\paperonly` is the identity there. The report loses the
duplicate. This alone took the report from 20 pages to 19.

Two cases were not that pattern and were handled separately. One `\tronly` stub
in `security.tex` restated two sentences of a longer paragraph that already
rendered in both, so the stub is deleted. Two near-identical `\tronly` blocks in
`related.tex` covered the same ground, so the shorter is deleted.

Verified by resolving both views and searching for paragraphs that are
subsequences of each other. Before, 31. After, 0 in the report and 0 in the
submission.

### 1.2 Section IV gained the client-to-client bound

This is the substantive addition and it is what you asked for.

Theorem 2 bounds a deviating coalition by $\negl(\lambda)+\delta(Q_{\mathrm{tot}})$
and never says what $\delta$ is. A reviewer may read it as vacuous, because
nothing in either document rules out $\delta=1$.

The new subsection IV-F, `sec:c2c`, closes that. Proposition 2 says a coalition's
entire view through the label interface is computable by an adversary that simply
holds the head, because every answer is $\arg\max$ of the head applied to a
feature map the corrupt querying client already owns. So
$\delta(Q_{\mathrm{tot}})\le\delta_{\mathrm{wb}}$ at every budget, where
$\delta_{\mathrm{wb}}$ is the advantage of an adversary given $\thstar$ in
plaintext.

Three things follow, and all three are in the report.

What a coalition learns about an honest client is capped by what the shared head
itself reveals. The cap does not depend on the allowance.

The allowance prices the cost of approaching the cap. This is the honest form of
the claim, and it concedes the objection that a small allowance is not a
membership defence, which published label-only attacks make correctly.

The threshold moves the cost, not the cap. That makes the availability discussion
precise for the first time.

It also changes the experiment in P4 below, from an extract-then-attack pipeline
to a white-box attack on the true head, which is a much smaller piece of work for
a strictly stronger claim.

Appended at the end of Section IV so no shared section label changes number,
which `check_split.py` requires and which I verified before writing.

### 1.3 The noise defence, measured, with corrected numbers

`sec:scope` claimed calibrated noise on returned labels "composes with the
protocol without modification" and that "we do not evaluate it".
`results/extraction_defence/results.csv` evaluates it, three tasks, six budgets,
three seeds. The false clause is deleted, which is a pure deletion and so stays
inside the subsequence rule, and the measurement is now reported as Table VII.

**The numbers in `plan-submission-2026-08-23.md` do not match the record.** It
quotes AG-News falling to 0.310 at $\varepsilon=1$, DBpedia to 0.111 and
Banking77 to 0.014. Recomputed from the file, $\varepsilon=1$ gives 0.372, 0.150
and 0.018. The quoted figures mix $\varepsilon=1$ with $\varepsilon=0.5$, and the
Banking77 baseline of 0.196 appears nowhere in the file, where it is 0.206. The
report uses the file. The plan should be corrected.

The finding survives and is sharper than the plan stated it. The mechanism does
not separate the copy from the task. On AG-News the budget that first costs the
copy a fifth of its fidelity is $\varepsilon=1$, where the copy still reaches
0.774 and the served model has fallen to 0.372, below the 0.488 share of its most
common class. On DBpedia accuracy falls by a larger fraction than fidelity at
every budget below $\varepsilon=8$. On Banking77 the copy does degrade faster
below $\varepsilon=4$, and only after accuracy reaches 0.028 against a majority
share of 0.083, so the model the noise protects is already worse than a constant
predictor.

One caveat is in the report. The AG-News baseline has a bad seed, 0.4018 against
0.8086 and 0.7356, so its mean is not a good summary. I reported the measurement
as it stands rather than dropping the seed.

### 1.4 How the protocol scales in the federation

TNSE is a networks venue and neither document said how communication scales in
the number of clients, although `results/fhe_serve/comm_grid.json` answers it.

Verified at 5, 10 and 20 parties, ring degrees $2^{14}$ to $2^{16}$, and both the
aggregation and serving chains: no per-party quantity varies with the client
count. So per-client communication is constant in the federation size, aggregate
key-generation traffic is linear in $\Nc$, at 3.4 GiB for ten clients and 17 GiB
for fifty, and per-query traffic is linear in the quorum size $\tc$ and not in
$\Nc$.

### 1.5 The liveness cost of the threshold

Section II says a quorum means serving does not require every client online.
Section V says the implementation runs $\tc=\Nc$, where it does. Both are true
and the report never put them next to each other. It now states that at
$\tc=\Nc$ one unavailable client blocks every query, and, using Proposition 2,
that lowering $\tc$ buys liveness at the cost of a shorter distance to the same
cap rather than a higher cap.

### 1.6 The stale membership suite is now labelled

`mia/README.md` and a new `results/heifd_021_mia/PRE-PIVOT.md` say plainly that
the suite attacks a released plaintext model and a Phase-0 prototype channel,
neither of which the current method has, and that its numbers may be cited only
as the disclosure counterfactual. `README.md` in that directory is auto-generated
by `mia.report`, so the durable note is the separate file.

## 2. What I corrected in my own analysis

My earlier note proposed grounding the reconstruction argument in Lowd and Meek.
**That was wrong and I withdrew it.** Their polynomial-query result is for
continuous *binary* linear classifiers, and their paper says explicitly that it
does not extend past two classes. Our head is multiclass, four to seventy-seven.
For Boolean features they prove recovering even the signs of the weights is
NP-hard.

The correct anchor was already in the paper. Tramèr et al. 2016, Section 6.2,
"Extraction Given Class Labels Only", extracts multiclass softmax models to above
99.9 per cent agreement in $100c(d+1)$ label queries. The verification also
confirmed, from the USENIX proceedings rather than the extended version, that the
sentence in `experiments.tex` attributing that figure to them is **correct and
needs no change**. I had flagged it as a possible misattribution. It is not one.

`lowdmeek2005` stays in `refs.bib` and stays uncited, so W10's cull would delete
it. That is now the right outcome and no exception is needed for it.
`choquettechoo2021labelonly` is cited by the new subsection, so it is no longer
in the cited-nowhere set.

## 3. Three things that need you

These are claim changes. I did not make them.

### 3.1 The introduction misattributes two numbers to Nasr et al.

`intro.tex:20-22` says an observer of per-round updates mounts membership
inference at 87 per cent "where the same attack against the final model alone
falls to 54.5 per cent". Checked against the paper.

The 87 per cent is 87.3, and it is a *malicious* parameter server that deviates
by isolating the target client, not an observer. Our own threat model is
semi-honest, so the sentence cites a stronger adversary than we defend against.
The passive global attacker on the same cell is 79.2 per cent.

The 54.5 per cent is a black-box attack on a *stand-alone* pretrained model, not
the same attack and not federated. Their own Table VIII gives 67.7 per cent for
that cell, so the number they quote in their introduction is contradicted by
their own table.

This is in the submission. Both spans need substitution, so it is outside the
subsequence rule and it is your call. The honest minimal version uses the passive
number and drops "the same": a parameter server that observes the per-round
updates reaches 79 per cent, where a black-box attack on the fully trained model
reaches 54.5. If you keep 87, the sentence must say "by isolating a target
client".

### 3.2 Theorem 1 assumes IND-CPA where CKKS needs IND-CPA-D

The protocol releases decryptions: the selection index, and a key-switched label
on every query to a party the adversary may control. For approximate schemes that
is the setting where plain IND-CPA is known not to suffice, and the multiparty
CKKS we cite achieves the right notion by smudging the partial decryption shares.

Neither document contains "smudging", "flooding", or IND-CPA-D anywhere, and
`refs.bib` has no entry for the attack. A cryptography reviewer will lead with
this.

Two consequences. The claim that only a label leaves the protocol is not
established by Theorem 1 alone, because the returned ciphertext carries noise
that depends on the logits. And "the encrypted argmax is exact" was measured on
an implementation that does not smudge, so adding smudging costs precision that
has not been re-checked.

The fix is two clauses in the theorem and two citations, which is an addition
rather than a rewrite. It is a change to a security claim, so it is yours.

### 3.3 The latency and the traffic describe two different protocols

The 31.5 and 113.2 second figures come from `argmax_tournament.csv`, whose README
records 9 to 34 collective refreshes per query. The 13.5 MiB per-query figure
prices the other design, where the server restores levels alone under
collectively generated bootstrapping keys and refresh traffic is zero. The
document states that the protocol specifies the second design, in a `\tronly`
block.

So the specified protocol has never been timed, and the recomputation defence
against a malicious server depends on the bootstrapping-key design, because
collective refresh injects fresh client randomness and is not deterministic.

Either re-measure the tournament under server-side bootstrapping keys, which is a
day or two of Go, or say in one clause that the reported latency is a lower bound
for the specified protocol. I did not choose for you.

## 4. Still proposed, not done

**P4, the membership measurement.** Blocked on compute and on the `mia/` rewire.
Proposition 2 makes it a white-box LiRA and RMIA attack on the true merged head,
reported as TPR at 0.1 and 1 per cent FPR, swept over the budget so the output is
$\delta$ against spent queries. New case `heifd_mia_served`. Do not write a
near-chance sentence before the number exists. The two arrangements are not
symmetric and the strong claim should be confined to the shared one.

**P9, one real end-to-end encrypted query.** `fhe/main.go` has no flag that loads
a real head, so every serving benchmark runs on synthetic vectors while the
introduction says the protocol is implemented rather than simulated. A Python
exporter and about a hundred lines of Go.

**The selection phase has no cost number.** The reviewer's strongest objection and
I could not resolve it from the records. `method.tex` says each client evaluates
both arrangements on its held-out data "entirely under encryption", and the
encrypted argmax is measured at 31.2 to 113.0 seconds. At roughly two thousand
held-out examples across the federation that is tens of CPU-hours per selection,
and the only statement in the submission is that selection "costs a bounded
exchange", with no number and no record. Either cap the probe at a stated number
of examples per client, which makes the cost arithmetic on numbers we already
have, or state that the per-class accuracies are computed locally on plaintext
logits with only the counts encrypted. The second is a method change and is
yours.

## 5. Verified citation metadata, for when you want it

All fetched from the record on 2026-08-27, not from recall. Nothing was added to
`refs.bib`.

Choquette-Choo et al., label-only membership inference, PMLR 139, 1964-1974,
ICML 2021. Li and Zhang, CCS 2021, 880-895. Carlini et al., LiRA, S&P 2022,
1897-1914. Zarifzadeh et al., RMIA, PMLR 235, 58244-58282, ICML 2024, and note
the arXiv v1 carried a different title. Karmakar and Basu, Marich, NeurIPS 2023,
which extracts in about 1,000 to 8,500 queries and then reaches 84 to 96 per cent
membership accuracy on the copy. Peng et al., OSLO, NeurIPS 2024, single-query
label-only membership inference at 7 times the TPR at 1 per cent FPR and 22 times
at 0.1 per cent. Ngo et al., secure aggregation is not private, ECML PKDD 2024,
180-198. Abascal et al., TMI, PoPETs 2024(3), 202-223, which is published and not
arXiv-only. Tobaben et al., NeurIPS 2025. Juuti et al., PRADA, EuroS&P 2019,
512-527, and cite the four-author conference version. Ghazi et al., label
differential privacy, NeurIPS 2021. Jagielski et al., USENIX Security 2020,
1345-1362.

## 6. The morning conversation

You said we would talk about the structure across the two documents. The three
things I would put on that agenda, in order.

The submission cites the report for the proofs, the selection table and the
extraction study. Those pointers are sound now that the report no longer prints
paragraphs twice.

Several cuts left holes rather than gaps. The submission asserts that Theorem 2's
$\delta$ is turned into a bound on $Q$ by Section V-E, and the paragraph that
does it is report-only. It defines a pooled column and promises to report both
differences, and the paragraph reporting the second is report-only. It reports a
fidelity curve while the definition of fidelity is report-only. Each is one
paragraph moving back, and each costs words the budget does not have, which is
the real subject of the conversation.

The novelty claim's one counterexample, the prior scheme that is at once one-shot,
federated and encrypted, is stated only in the report. The submission makes the
claim and the document that qualifies it is the other one.
