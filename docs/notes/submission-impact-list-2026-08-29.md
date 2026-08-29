---
title: "Everything that touches the submission, before we change it"
author: "For Halil, 2026-08-29"
header-includes: |
  \newcommand{\Adis}{A_{\mathrm{dis}}}
  \newcommand{\Asel}{A_{\mathrm{sel}}}
  \newcommand{\Apool}{A_{\mathrm{pool}}}
  \newcommand{\Aloc}{A_{\mathrm{loc}}}
  \newcommand{\thstar}{\theta^{\star}}
  \newcommand{\Cc}{C}
  \newcommand{\Nc}{N}
  \newcommand{\tc}{t}
  \newcommand{\featx}{\varphi}
---

# How to read this

Twenty-two items. Each says what is wrong, where, how I verified it, what the fix
costs, and whether the subsequence rule permits it without your sign-off.

Three classes of permission, because they decide how much of this is my work and
how much is yours.

A **deletion** is always permitted. `check_subseq.py` classifies a paragraph as a
subsequence of what it replaces and passes it.

A **number that changed against its record** is permitted, declared in the
`--number` list in `scripts/gates.sh`.

Anything else is a **new sentence**, which needs an entry in `.subseq-allow` and
your approval, because the PIs read commit `cc1df39` and a new sentence is one
they must read again.

Work that is purely additional in the technical report is excluded, as you asked.
Where a report addition forces a change in the submission, the submission half
appears below.

# A. The submission disagrees with a record or with a source

## A1. The two numbers attributed to Nasr et al., `intro.tex:19-22`

Decided by you. The sentence says an observer reaches $87\%$ where the same
attack on the final model falls to $54.5\%$. The $87\%$ is an active malicious
server that isolates its target, the passive figure is $79.2\%$, and the $54.5\%$
is a black-box attack on a stand-alone model rather than the same attack.

Your instruction is to correct the numbers and add nothing. An agent is searching
for a more recent and more directly on-point citation, which may replace the
sentence's source rather than only its numbers.

Permission: new sentence, but you have already decided it.

## A2. The skew sensitivity figure, `experiments.tex:115-116`

The submission prints $0.971$ at $\alpha=1.0$. Recomputed from
`results/personal_adapter/sensitivity.csv`, the three seeds are $0.9731$,
$0.9737$ and $0.9625$, whose mean is $0.9698$ and rounds to $0.970$. The
report-only table `tab:sens` already prints $0.970$, so the two documents
disagree with each other as well.

Permission: a number against its record. Declare `--number 0.971=0.970`.

## A3. Two of the five prices cannot be derived from the table they cite

`experiments.tex:639-642` says `tab:headline` allows the price of never
disclosing to be read directly, and gives $\Adis-\Asel$ as $0.071$, $0.104$,
$0.136$, $0.075$ and $0.029$.

Those five values are correct against the records. I recomputed them. The
difficulty is that $\Asel$ is a per-seed quantity that the table never prints,
because the estimator selects per seed and the mean of the per-seed selections is
not the selected column.

| task | stated | table subtraction | against the record |
|---|---|---|---|
| AG-News | $0.071$ | $0.739-0.649=0.090$ | $0.739-0.6685=0.070$ |
| TREC | $0.104$ | $0.104$ | $0.104$ |
| DBpedia | $0.136$ | $0.136$ | $0.136$ |
| Banking77 | $0.075$ | $0.074$ | $0.074$ |
| CIFAR-100 | $0.029$ | $0.784-0.774=0.010$ | $0.784-0.7558=0.028$ |

A reviewer who subtracts two printed columns on AG-News gets $0.090$ against our
$0.071$, and on CIFAR-100 gets $0.010$ against our $0.029$. Three of five
reconcile and two do not.

On AG-News the selected accuracy $0.6685$ is higher than either printed column,
because on one seed the estimator picked the personal adapter and won. On
CIFAR-100 it sits between them, because on one seed it picked wrong.

Two fixes. Add an $\Asel$ column to `tab:headline`, which costs table width and
makes every price subtractable, and which also disambiguates the abstract. Or
weaken the word directly, which is a rewrite.

I recommend the column. It is the single change on this list that most reduces
the chance of a reviewer deciding our numbers are unreliable.

Permission: a new column is new content and needs your approval.

# B. Typography and grammar, all pure deletions

## B1. Four paragraph breaks fall inside a sentence

A blank line in LaTeX ends a paragraph. These four render as a paragraph break
mid-sentence on the printed page.

`intro.tex:8-10`, after "restricts the sharing of", before "confidential records
across institutions". This one is in the first column of page one.

`method.tex:16-18`, after "The clients want a classifier", before "that works
across the whole label space".

`method.tex:91-93`, after "the same frozen public backbone", before
"$\featx$, and trains two things".

`experiments.tex:209-211`, after "since every paper measures", before "that
against its own unprotected baseline".

Fix: delete the blank line. Four characters each.

Permission: deletion.

## B2. An article before a name, `related.tex:58-59`

"and the Kerkouche et al. show that". The same error is in the report at line
69-70, where it reads "and the Kerkouche et al. and So et al. show that".

Fix: delete "the".

Permission: deletion.

# C. Claims that say more than we prove or than the citation supports

## C1. Theorem 1's assumption, `security.tex:113-115`

The theorem assumes IND-CPA. The protocol releases decryptions, which is the
setting where an approximate scheme needs the stronger notion. An agent is
checking whether the concern genuinely applies to a threshold scheme whose key
holders are the clients themselves, which is your objection and a good one. I
will not touch this until that comes back.

Our implementation does smudge, at `fhe/main.go:337` and `fhe/serve.go:193`, so
if the change is needed it is a statement of what we already do.

Permission: new sentence, pending the verification.

## C2. "cannot recover the last client's adapter", `intro.tex:99-100`

The full sentence says no adapter aggregate exists, so a coalition of all but one
client cannot recover the last client's adapter. The premise is true and the
conclusion overreaches. No aggregate means the subtraction attack does not exist.
It does not mean recovery is impossible, and no theorem in `security.tex` covers
adapter recovery. Theorem 2 bounds distinguishing two datasets of equal size,
which is a different statement.

Fix: weaken to what the construction gives, which is that no aggregate exists
from which a coalition can subtract its own contributions.

Permission: new sentence.

## C3. Proposition 1 is applied without its hypothesis being checked

`security.tex:254-256` concludes that no protocol of this message pattern
realizes the functionality against a malicious server. Proposition 1 proves that
only for a predicate whose rest of the view is independent of the plaintext,
which is an explicit hypothesis at lines 239-240. An honest client's view
includes its own dataset and its own ciphertext, both correlated with the head.

Three lines later the submission exhibits a mechanism of that message pattern
which does defeat a malicious server, namely recomputation. In the report the
framing sentence resolves this. In the submission the two paragraphs sit adjacent
with nothing between them and read as a contradiction.

Fix: either restore one framing sentence from the report, or narrow the
conclusion to what Proposition 1 proves.

Permission: new sentence.

## C4. A citation that does not cover the claim, `related.tex:92-97`

"Several works train a classifier head, a linear or logistic model, or a low-rank
adapter on frozen features under CKKS~\cite{lee2023hetal}." HETAL trains a
classifier head. It is not a low-rank-adapter work. The other citations were cut
and the prose still describes them.

Fix: delete the clause the surviving citation does not support.

Permission: deletion.

## C5. Two works collapsed into one citation, `related.tex:140-142`

"related approaches protect a diffusion-generated surrogate or a teacher
ensemble~\cite{feddiff2024}". The teacher-ensemble citation was cut, so the
sentence now attributes both to FedDiff.

Fix: delete "or a teacher ensemble".

Permission: deletion.

## C6. The selection phase has no cost anywhere, `experiments.tex:459-462`

The submission says selection "costs a bounded exchange". There is no number, no
record, and no bound. `method.tex:317` says each client evaluates both
arrangements on its held-out data entirely under encryption, and the encrypted
argmax is measured at $31.2$ to $113.0$ seconds. At roughly two thousand held-out
examples across the federation that is tens of CPU-hours per selection.

This is the objection on this list that no rewording survives. Two ways out. State
a probe cap in the method, for instance one held-out example per class per client,
which makes the cost arithmetic on numbers we already hold. Or state that the
per-class accuracies are computed locally on plaintext logits with only the counts
encrypted, which is a change to what the method claims and needs checking against
the code.

Permission: yours either way.

## C7. The abstract prices two different designs in one sentence

`frontmatter.tex:31` says one query takes $31.5$ to $113.2$ seconds for $13.5$
MiB. The report now states that the latency was measured with collective refresh
and the traffic prices the bootstrapping-key design the protocol specifies.

Fix: either one qualifying clause in the abstract, or run the measurement so both
numbers describe the specified design. I recommend the measurement.

Permission: new sentence, or no change if we measure.

# D. Definitions and support that left with the cuts

You are right that the material moved for space. In each of these the submission
keeps a claim and does not say where its support went. The fix is a pointer, which
is a permitted substitution and costs a few words.

## D1. Theorem 2's operational content points at nothing

`security.tex:221` says Section V-E measures $\delta$ and turns it into a bound on
$Q$. In the submission it does not. The paragraph deriving $Q$ below roughly
$1.3\times10^3$ per client on AG-News is report-only.

Fix: retarget the cross-reference with `\trsee`.

## D2. A promise the submission does not keep

`experiments.tex:53` says two differences follow "and the paper reports both". The
paragraph reporting $\Apool-\Adis$ is report-only. The submission prints a pooled
column of $0.921$ to $0.988$ beside servable values of $0.607$ to $0.789$ and
never explains that most of that gap is the partition rather than the encryption.

This is the most damaging of the four, because the unexplained gap is the first
thing a reviewer sees in the table.

Fix: a pointer, or restore the one paragraph.

## D3. "fidelity" is used and never defined

`experiments.tex:568` reports a fidelity curve. The definition is report-only at
lines 544-546.

## D4. "$d$" is used and never defined

`experiments.tex:570` says the head has $\Cc d$ parameters. The submission has no
notation table, because `tab:notation` is report-only, and the value $768$ appears
only in a report-only block.

## D5. The novelty claim's counterexample is only in the report

`frontmatter.tex:25-27` claims the first cryptographically secure one-shot
federated fine-tuning protocol. The one prior scheme that is at once one-shot,
federated and encrypted is named only in a report-only sentence in `related.tex`.
Given the shared TDSC reviewer pool, the reviewer who raised it before will look
for it.

Fix: restore that sentence and its row in `tab:related`, about twenty-five words.

# E. The ideal functionality has a defect

`security.tex:69-71`, step 3, returns $\arg\max_c(\thstar\varphi_j(x))_c$ whatever
the selected arrangement $a^{\star}$ is. If selection chose the bare-backbone
arrangement the served function is $\thstar\varphi(x)$, without the client's
adapter. So the functionality does not depend on its own selection output.

Fix: make step 3 branch on $a^{\star}$. One clause.

Permission: new sentence, and it is a formal object, so it is yours.

# F. Reproducibility detail a reviewer will ask for

`experiments.tex:343-344` says timings are single-run wall clock on "a commodity
CPU". No processor, no core count, no library version in the text, no repetition
and no variance. The record says Lattigo v6.1.0 on VALAR `t4_ai`, CPU path.

Fix: name the hardware and the version. It is new text and it is short.

# G. Gate housekeeping, no action needed but do not let anyone "fix" these

The prose budget is three words over, $6583$ against $6580$. It has been so since
before this session.

`fig_protocol` has five of forty-five text spans outside the 8pt tolerance. Also
pre-existing.

The four linter errors in the submission view are all false positives. Two are
"the very artifact it releases", where "very" means that exact one and is not an
intensifier. Two are the system name slytHErin, which the linter reads as a code
identifier. Leave all four.

# What I recommend doing, in order

Do B1, B2, C4 and C5 now. They are deletions, they need no decision, and they are
the kind of defect that costs credibility for nothing.

Do A2 now. It is a number against its record.

Decide A3. I would add the $\Asel$ column.

Decide D1 to D5 together. They are five pointers and they are cheap.

Hold A1 and C1 for the two agents.

Decide C6 before anything is sent. It is the one a reviewer cannot be talked out
of.

C2, C3, C7, E and F are one sentence each and can go in one pass once you have
ruled on them.
