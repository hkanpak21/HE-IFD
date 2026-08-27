# Propositions for the technical report, 2026-08-27

For Halil to accept, amend, or reject, one by one. Nothing here is applied.
No `.tex` file was touched this session, and `git status --porcelain docs/paper/`
is empty.

The order of work Halil set on 2026-08-27. The technical report is edited first.
The submission is touched only after these propositions are accepted, and the
submission edits are then derived from the accepted ones. Every proposition below
therefore names the report location it changes, and carries a separate line for
what it would later imply for the paper, which is not a proposal yet.

The ledger for this session is `docs/notes/GATES-privacy-tr-2026-08-27.md`. The
analysis behind the propositions is `docs/notes/privacy-analysis-tr-2026-08-27.md`.

## The constraint that shapes every proposition

`scripts/check_split.py` compares the printed number of every `sec:` label the
two documents share, and both documents currently carry identical section and
subsection structure, 64 shared labels, status OK. Report-only material therefore
lives in `\tronly` paragraphs inside shared subsections. A new report-only
subsection is safe only when it is appended at the end of its section, where it
shifts no shared label. Verified 2026-08-27 by reading `check_split.py` and
running it.

So P1 and P4 append at the end of Section IV and Section V. Nothing is inserted
in the middle.

## Writable now, or blocked on compute

| id | proposition | status |
| --- | --- | --- |
| P1 | Client-to-client privacy, the reduction and the statement | writable now, no compute |
| P2 | The reconstruction half of the channel, from records that exist | writable now, no compute |
| P3 | Correct the noise-defence numbers, which do not reconcile | writable now, no compute |
| P4 | The membership measurement | blocked, needs the W12 rewire and a VALAR run |
| P5 | Retire the current membership suite from the record | writable now, no compute |
| P6 | Protect two bibliography keys from the citation cull | writable now, no compute |
| P7 | Communication scales in the client count | writable now, no compute |
| P8 | The availability cost of the threshold | writable now, no compute |
| P9 | One real end-to-end encrypted query | blocked, needs about a hundred lines of Go |

P4 and P9 are the only two that cannot be written today. Everything else is
prose over records already in the repo.

---

## P1. Client-to-client privacy, stated as a reduction

**Where.** A new subsection appended at the end of Section IV, after
`sec:inherent`, wrapped in `\tronly`. It becomes IV-F in the report and does not
exist in the submission. No shared label moves.

**Why.** Theorem 2 bounds the coalition's advantage by
$\negl(\lambda)+\delta(Q_{\mathrm{tot}})$ and never says what $\delta$ is. As it
stands a reviewer may read $\delta$ as unbounded, in which case Theorem 2 says
nothing. The report can close this today, without any measurement, because
$\delta$ has a ceiling that follows from the structure of the view.

**The content.** A proposition and its proof, which I believe is correct and
which is the substantive new thing in these propositions.

> **Proposition (the query channel is no stronger than the head).** Let
> $\mathcal{A}$ corrupt a coalition of at most $\tc-1$ clients in the content
> game of \cref{def:contentgame}, with the server honest, and let it spend at
> most $Q_{\mathrm{tot}}=(\tc-1)Q$ queries. Then there is an adversary
> $\mathcal{B}$ that receives $\thstar$ in plaintext, makes no queries, and
> satisfies $\mathsf{Adv}(\mathcal{A})\le\mathsf{Adv}(\mathcal{B})+\negl(\lambda)$.
>
> *Proof.* By the proof of \cref{thm:malicious} the view of $\mathcal{A}$ is the
> key-generation transcript, the honest clients' ciphertexts, the values the
> honest server computes, and the answers to its own queries. The first three are
> independent of $b$ up to $\negl(\lambda)$. Each answer is
> $\arg\max_c(\thstar\varphi_j(x_i))_c$ for a query $x_i$ that $\mathcal{A}$
> chooses at one of its own clients $j$. The map $\varphi_j$ is the public
> backbone composed with the adapter of client $j$, which is corrupt, so
> $\mathcal{B}$ holds it. Holding $\thstar$ as well, $\mathcal{B}$ computes every
> answer itself. It runs $\mathcal{A}$, answers its oracle calls, and returns its
> guess. The simulation is perfect outside the negligible event on which the
> first three parts differ. $\square$

The corollary is the sentence the report needs. For every budget,
$\delta(Q_{\mathrm{tot}})\le\delta_{\mathrm{wb}}$, where $\delta_{\mathrm{wb}}$
is the advantage of the best polynomial-time adversary holding $\thstar$ exactly.
What a fellow client can learn about an honest client is capped by what the
merged head itself reveals, and the cap holds at any allowance.

**What this buys, in three parts.**

It makes Theorem 2 non-vacuous without a measurement, because the ceiling is
structural.

It answers the objection that a small allowance is not a defence. Published
label-only membership inference now runs in a single query, so a reviewer can say
the allowance bounds nothing. That is right, and the report should concede it in
those words. The allowance bounds the cost of reaching the ceiling. The ceiling
itself is set by the head.

It changes what the experiment has to be. The quantity to measure is
$\delta_{\mathrm{wb}}$, a white-box membership attack on the true merged head,
which is an upper bound on everything reachable through the interface. The
extract-then-attack pipeline no longer has to be implemented to obtain a bound.
That is the difference between P4 as a large piece of work and P4 as a moderate
one.

**Also in this subsection, one short paragraph.** What a fellow client sees,
enumerated. The public per-client sample counts $\nj$, the announced index
$a^{\star}$, the phase signals, and the labels it asks for. Not the per-class
totals, which are inverted under encryption and never decrypted, and not any
adapter, since no adapter aggregate exists. This is already implied by
Functionality 1's leakage and is worth stating once in the fellow client's own
terms, because that is the reader's question.

**Prior work this rests on.** The reduction is ours. The reason it matters, that
label-only membership inference is cheap in queries, is
`choquettechoo2021labelonly` (already in `refs.bib`), and the single-query result
strengthening it is pending verification, see P6 and the citation table.

**Later, for the paper.** One clause tying $\delta$ to the report's ceiling.
Retargeting a cross-reference is one of the three permitted substitutions under
the subsequence rule, so this is cheap. Not proposed yet.

---

## P2. The reconstruction half, written from records that exist

**Where.** Section V, inside `sec:exp-leak`, extending the existing `\tronly`
blocks. No new subsection, no structural change.

**Why.** Halil's instruction of 2026-08-27 is that the client-to-client channel
may be treated as reconstruction rather than only as membership. The repo
already holds the whole measurement, so this half of the chapter is writable
today and needs no compute at all.

**The content, and every number checked against its record on 2026-08-27.**

The coalition's cost to reach the ceiling of P1 is the cost of reconstructing the
head from labels. Verified from `results/extraction_budget/results.csv`, mean over
six rows per cell:

| task | queries | mean fidelity |
| --- | --- | --- |
| AG-News | $10^4$ | 0.8892 |
| AG-News | $2\times10^4$ | 0.9360 |
| DBpedia | $5\times10^4$ | 0.9011 |
| Banking77 | $2\times10^5$ | 0.9001 |

The paper's existing claim, fidelity 0.90 at about $1.2\times10^4$,
$5.0\times10^4$ and $2.0\times10^5$, reconciles with this. AG-News is bracketed
by the two rows above. The per-parameter ratios are 3.9, 4.7 and 3.4 against
$\Cc d$ at $d=768$, which is the paper's "between three and five".

The point the report should add, and the paper does not make, is that this is
what theory predicts for a linear map rather than a surprise. A linear classifier
is reconstructible from label-only membership queries in polynomially many
queries, which is Lowd and Meek, and the key `lowdmeek2005` is already in
`refs.bib` and cited nowhere. Today `method.tex` supports its hard-label sentence
with `chen2024hardlabel` and `carlini2025hardlabel`, which are results for general
networks. For a linear head those are the wrong shape of citation. They say
extraction of general networks is hard, and the served object here is the one case
where it provably is not. The honest framing, which the measurement supports, is
that the label restriction raises the cost by a factor of roughly fifteen to two
hundred and sixty over the logit interface, from $769$ queries to between
$1.2\times10^4$ and $2\times10^5$, and does not make reconstruction infeasible.

**Boundary.** Three seeds per cell, two arrangements, one feature dimension
$d=768$. Not measured at any other $d$. `results/extraction_scale/results.csv`
carries the $\Cc d$ scaling separately.

**Later, for the paper.** Nothing. The paper's sentence is already correct and
survives unchanged.

---

## P3. The noise-defence numbers do not reconcile, and the report must not inherit them

**Where.** Section V, `sec:exp-leak` and the `sec:scope` paragraph on extraction
bounds, both `\tronly`.

**Why.** This is a correction, and it is the reason to check before writing.
`docs/notes/plan-submission-2026-08-23.md`, item W7, states that the defence
takes AG-News from 0.649 to 0.310 at $\varepsilon=1$, DBpedia from 0.788 to
0.111, and Banking77 from 0.196 to 0.014. Recomputed from
`results/extraction_defence/results.csv` on 2026-08-27, mean over three seeds:

| task | $\varepsilon=\infty$ | $\varepsilon=1$ | $\varepsilon=0.5$ |
| --- | --- | --- | --- |
| AG-News | 0.6487 | 0.3723 | 0.3029 |
| DBpedia | 0.7888 | 0.1500 | 0.1027 |
| Banking77 | 0.2061 | 0.0176 | 0.0149 |

The plan's figures mix $\varepsilon=1$ with $\varepsilon=0.5$, and its Banking77
baseline of 0.196 matches nothing in the file. The direction of the finding is
unchanged and the argument survives. The numbers do not, and under the standing
rule that a number enters only with its record opened, the report takes the table
above.

**A second correction that rides with it.** The AG-News baseline has a bad seed.
At $\varepsilon=\infty$ the three seeds are 0.8086, 0.7356 and 0.4018, so the
mean of 0.6487 is not a summary of anything. The report either reports the spread,
drops the seed with a reason, or reruns it. My recommendation is to report the
spread, because it costs nothing and hiding it is the kind of thing a reviewer
finds.

**The argument these numbers support, unchanged.** Calibrated noise on returned
labels is not a usable defence at this operating point, because it destroys the
task at the same rate it slows the copy. That is the case for metering queries
rather than perturbing answers, and it is the report's answer to the reviewer who
asks why differential privacy is not applied to the interface. Grounding for
label-level noise as the named mechanism is `mcsherry2007mechanism`, already
cited, and label differential privacy proper is a pending citation, see the
table.

**Later, for the paper.** The `sec:scope` sentence still says the mechanism
"composes with the protocol without modification" and that "we do not evaluate
it", and the second half is false. A one-clause correction is already on the
plan's list. Not proposed yet.

---

## P4. The membership measurement. Blocked, and specified so it can be run

**Where.** Section V, a new subsection appended at the end after `sec:scope`,
`\tronly`, plus a pointer from IV-F.

**Why blocked.** There is no record. The suite in `mia/` measures a released
plaintext model and a Phase-0 prototype channel, and the current method has
neither. Details in `docs/notes/privacy-analysis-tr-2026-08-27.md`, section 1.
Nothing about membership may be written into the report until this runs.

**What P1 changes about the experiment.** Because the ceiling is white-box, the
measurement is a white-box membership attack on the true merged head. The
extraction-then-attack pipeline is not needed for the bound. This is a large
reduction in the work.

**The specification.**

The object under attack is the merged head produced by the real pipeline, the
frozen backbone, the local adapter, the encrypted head displacement, and the
coverage-weighted merge. Shadow heads are trained through that same pipeline on
resampled splits, which is the LiRA recipe the suite already implements.

The adversary is the coalition of $\tc-1$ clients, holding its own clients'
data as the prior, attacking one honest client's records.

The attacks are LiRA and RMIA. RMIA is the one that makes this cheap, because it
retains power with few reference models and a shadow linear head over cached
frozen features costs seconds.

The metric is TPR at 0.1 and 1 per cent FPR, and AUC alongside. That is the
metric LiRA fixed and it is what a reviewer expects.

The cells are the five tasks of the headline table at the default $\Nc$ and
$\alpha$, three seeds.

The reported quantity is $\delta_{\mathrm{wb}}$, and the report states it as the
ceiling of P1 rather than as an attack result.

**What must be honest in the writing.** The claim that the coverage-weighted merge
attenuates per-record signal has no direct citation. The nearest support is a
fitted power law in the transfer-learning setting, pending verification. So the
report supports it with the measurement and calls it open. Do not write a
near-chance sentence before the number exists.

**One caveat that belongs in the same subsection.** The two arrangements are not
symmetric. When the served head sits over a client's own adapter, querying it can
leak about that client, which is the fine-tuned-model membership setting. The
strong statement should be confined to the shared arrangement.

**Compute.** AFK on VALAR, new case slug `heifd_mia_served`, resumable per shadow
model as the suite already is. This is the W12 rewire and it is a session of its
own.

---

## P5. Retire the current membership suite from the record

**Where.** `results/heifd_021_mia/README.md`, `results/heifd_mia_freeze_a/README.md`,
and `mia/README.md`. Not a paper edit at all.

**Why.** Those files describe attacks on a released model and a prototype channel
as measurements of "the HE-IFD protocol". Under the current method that is wrong,
and the next reader, including a context-zero agent, will believe them. The repo's
own rule is that a stale document is corrected, not left.

**The content.** A dated header on each, saying the case measures the pre-pivot
disclosed-model protocol, that it is retained as the counterfactual for what
disclosure would have leaked, and that it is not a measurement of the current
method. Same shape as the existing correction on `jobs/vision_matched.py` in
`CLAUDE.md`.

**The one place these numbers stay useful.** As the disclosure counterfactual.
The report's comparison with model disclosure currently argues from accuracy
alone, that a participant holding the model has fidelity 1 at zero queries. The
membership numbers make the same comparison on the privacy axis, at
`results/heifd_021_mia/README.md`, ViT on CIFAR-100, external LiRA AUC 0.8518 at
$\alpha=0.05$ and 0.8597 at $\alpha=1.0$, against the near-chance figures on
RoBERTa. If they are used that way, they must be labelled as the pre-pivot
pipeline, which is what P5 makes possible.

---

## P6. Protect two keys from the citation cull

**Where.** `docs/paper/refs.bib` and the W10 cull rule in the plan.

**Why.** `lowdmeek2005` and `choquettechoo2021labelonly` are both in `refs.bib`
and cited in no section, verified 2026-08-27. W10 deletes the 29 entries cited
nowhere. These two are the anchors of P1 and P2, so the cull would delete exactly
the citations the privacy chapter needs. `kanpak2024cure` already has a written
exception; these need the same.

**The content.** Add both to the exception list with the reason, and cite them in
the report where P1 and P2 land, which removes them from the cited-nowhere set
by construction.

---

## P7. Communication scales in the client count, and the report can say so

**Where.** Section V, `sec:exp-cost`, `\tronly`.

**Why.** TNSE is a networks venue. The submission compresses communication to
three numbers in a sentence and never states how it scales in the number of
clients, which is the question that venue asks. The record answers it and nobody
has written it down.

**The content, verified 2026-08-27 from `results/fhe_serve/comm_grid.json`.**
Across client counts 5, 10 and 20, ring degrees $2^{14}$, $2^{15}$ and $2^{16}$,
and both the aggregation and serving chains, every per-party quantity is constant
in the client count. The public key share, the relinearization key share, the
Galois key share per rotation, the ciphertext sizes, the key-switch share and the
collective refresh share do not vary with $\Nc$ at fixed ring degree and chain.

So the statement is that per-client communication is independent of the
federation size, aggregate key-generation traffic is linear in $\Nc$, and a
query costs the quorum $\tc$ key-switch shares and nothing that grows with $\Nc$.
That is a scalability result, it is measured, and it is currently invisible.

**Boundary.** Three client counts, not a fit. The constancy is exact rather than
approximate, which is expected from the structure of the scheme, so three points
suffice to state it and it should be stated as structure confirmed by
measurement rather than as an empirical trend.

**Later, for the paper.** Possibly one sentence, because it is the TNSE-facing
claim and it is cheap. Not proposed yet.

---

## P8. The availability cost of the threshold

**Where.** Section V, the `\tronly` availability paragraph that already exists at
the end of `sec:scope`.

**Why.** Every measurement is at $\tc=\Nc$. At that setting one unavailable
client stops every query, which for a networks venue is the first systems
question. The existing paragraph states the trade-off in one direction, that
lowering $\tc$ admits larger coalitions and tightens the allowance. It does not
say what $\tc=\Nc$ costs in availability, and P1 now lets it be said precisely,
because the ceiling $\delta_{\mathrm{wb}}$ does not depend on $\tc$ at all. Only
the cost of reaching it does, through $Q_{\mathrm{tot}}=(\tc-1)Q$.

**The content.** One paragraph. At $\tc=\Nc$ serving requires every client
online, which is the strongest collusion resistance and the weakest availability.
Lowering $\tc$ leaves the ceiling of P1 unchanged and raises the coalition's
budget toward it linearly. The deployment therefore chooses $\tc$ against
availability, and the privacy cost of that choice is a cost in queries rather
than in what is ultimately learnable. No new measurement is needed to say this,
because it follows from P1 and from the definition of $Q_{\mathrm{tot}}$.

---

## P9. One real end-to-end encrypted query. Blocked, small

**Where.** Section V, `sec:exp-cost`, `\tronly`.

**Why.** The introduction says the cryptographic protocol is implemented in real
multiparty CKKS rather than simulated. That is true of the protocol, and the
serving benchmarks nonetheless run on synthetic feature vectors, because
`fhe/main.go` has no flag that loads a real head. A reviewer who reads both will
call it a gap. It is a small one and it is worth closing in the report.

**What it needs.** A Python exporter for a head out of
`results/personal_adapter/artifacts/`, and about a hundred lines of Go. The
compute is minutes. Already on the carried-forward list and unstarted.

**What it would say.** One query, end to end, on a real trained head, agreeing
with the plaintext argmax. That is a correctness statement, not a timing one, and
the timings stay as they are.

---

## The citation table

Keys already in `refs.bib`, usable today with no verification risk.

| key | role in the privacy chapter |
| --- | --- |
| `lowdmeek2005` | reconstruction of a linear classifier from label queries. The anchor of P2. Cited nowhere today |
| `choquettechoo2021labelonly` | the label-only membership threat class. The anchor of P1's motivation. Cited nowhere today |
| `carlini2022membership` | LiRA, the attack and the low-FPR metric for P4 |
| `nasr2019comprehensive`, `melis2019exploiting` | the federated channels this construction denies |
| `tramer2016stealing` | extraction through a prediction interface |
| `chen2024hardlabel`, `carlini2025hardlabel` | hard-label extraction of general networks. Keep, but P2 notes they are the wrong shape for a linear head |
| `carlini2024stealing` | the deployed final-projection recovery |
| `mcsherry2007mechanism` | the noise mechanism of P3 |
| `yeom2018privacy`, `shokri2017membership`, `salem2019ml` | the released-model membership line, used in the P5 counterfactual |

Keys proposed for addition are held back pending verification, and are listed in
`docs/notes/privacy-analysis-tr-2026-08-27.md` section 5. Two reader agents were
verifying them against arXiv, dblp, ACM, USENIX and IEEE records when this file
was written. Nothing is added to `refs.bib` on recall. Anything that fails
verification is not proposed.

One verification matters more than the others and is called out here. The paper
currently attributes to `tramer2016stealing` the claim that extracting a softmax
model from class labels alone costs 100 queries per parameter for agreement above
99.9 per cent, at `experiments.tex` lines 580 to 584, inside a `\tronly` block.
If that paper's result is for confidence outputs rather than labels, the sentence
misattributes it and the report must not ship it. That check was in flight when
this file was written and its outcome is recorded in the session report.

## What is not proposed

Any edit to `docs/paper/main.tex` or to any section as it renders in the
submission. Any run on VALAR. Any addition to `refs.bib` before verification.
