# T25. Remove structure, do not add it. Find and replace list

Answers the meeting note of 2026-08-07, "Takeaway basliklarini cikar", and the
banned antithesis that Sinem Sav called "very AI smelly" in note 10 of
`PI_notes_2026-08-06.md`.

Nothing here is applied to `docs/paper/`. Each entry gives the file, the
approximate line, the current text verbatim, and the replacement. Paste in file
order. No number, citation or cross-reference changes anywhere in this list.

## Counts

| what | count |
|---|---|
| `\paragraph{Claim}` takeaway headings removed | 5 of 5 |
| other run-in headings removed | 6 |
| run-in headings before and after | 49 to 38 |
| antithesis sites fixed | 16 |
| sites looked at and left alone | 24, listed at the end |

The 5 takeaway headings all sit in `experiments.tex`. The claim sentence
survives in every case. Only the label goes, and the sentence joins the
paragraph below it.

The 6 other removals are the headings that comment on the paper's own argument
instead of naming what follows. Every heading that names content stays,
including `Communication`, `Correctness`, `The argmax`, `Cost`, `Sensitivity`
and the four limitation labels in `sec:scope`.

---

# A. `sections/experiments.tex`

## A1. Takeaway heading, `sec:exp-split`, around line 54

Current:

```latex
\paragraph{Claim} Sharing only the classifier head, over representations that
each client adapts privately, yields a model usable across the whole label space,
and the preferable arrangement depends on the size of the label space.

\Cref{tab:headline} reports both servable arrangements and both reference points.
```

Replacement:

```latex
Sharing only the classifier head, over representations that
each client adapts privately, yields a model usable across the whole label space,
and the preferable arrangement depends on the size of the label space.
\Cref{tab:headline} reports both servable arrangements and both reference points.
```

## A2. Antithesis, third observation, around line 107

Current:

```latex
Third, the two failure modes are complementary rather than ordered by severity. The shared head
```

Replacement:

```latex
Third, the two failure modes are complementary. The shared head
```

The cut half is already carried four sentences later by "Neither arrangement
dominates the other".

## A3. Takeaway heading, `sec:exp-peers`, around line 164

Current:

```latex
\paragraph{Claim} The protocol gives up no accuracy for protecting the
contributions, where the differentially private one-shot methods give up an amount
that grows as their budget tightens, and it withholds the model at a cost those
methods do not incur because they do not offer the property.

The peer group evaluates on different tasks from ours, so we ran our protocol on
```

Replacement:

```latex
The protocol gives up no accuracy for protecting the
contributions, where the differentially private one-shot methods give up an amount
that grows as their budget tightens, and it withholds the model at a cost those
methods do not incur because they do not offer the property.
The peer group evaluates on different tasks from ours, so we ran our protocol on
```

## A4. Run-in heading, around line 197

Current:

```latex
\paragraph{Why absolute accuracy does not settle the comparison} At $\Nc=5$ and
```

Replacement:

```latex
At $\Nc=5$ and
```

The heading argues with the reader before the paragraph does. The paragraph
closes on "Absolute accuracy across papers therefore measures the backbone",
which states the same thing from the evidence.

## A5. Run-in heading, around line 207

Current:

```latex
\paragraph{The comparison that does hold} What compares across papers is the
```

Replacement:

```latex
What compares across papers is the
```

Paired with A4 as a rhetorical set piece, "does not settle" against "does hold".
The first sentence already opens on the subject.

## A6. Antithesis, around line 228

Current:

```latex
accuracy, by construction rather than by measurement, since the decrypted result
```

Replacement:

```latex
accuracy, by construction, since the decrypted result
```

The `since` clause that follows already says why no measurement was needed.

## A7. Takeaway heading, `sec:exp-select`, around line 264

Current:

```latex
\paragraph{Claim} The direct procedure for choosing between the two
arrangements fails systematically, and the estimator of \cref{sec:selection}
corrects it while disclosing only the index of the selected arrangement.

We first establish that the direct procedure fails, since this is what motivates
the estimator. Each client measures both arrangements on data held back
```

Replacement:

```latex
The direct procedure for choosing between the two
arrangements fails systematically, and the estimator of \cref{sec:selection}
corrects it while disclosing only the index of the selected arrangement.
We establish the failure first, since it is what motivates the estimator.
Each client measures both arrangements on data held back
```

This is the one fold that needed more than a join. Joining alone leaves "fails
systematically" and "the direct procedure fails" in consecutive sentences. The
second clause is shortened to remove the repeat. Say the word and I will paste
the plain join instead.

## A8. Antithesis, around line 276

Current:

```latex
The failure is structural rather than statistical. The shared arrangement is one
```

Replacement:

```latex
The failure is structural. The shared arrangement is one
```

The cut half is stated with evidence at the end of the same paragraph, "it does
not become correct with more held-out data".

## A9. Antithesis, around line 319

Current:

```latex
all three seeds, by margins of $0.13$ to $0.24$. And the estimator responds to the
data rather than to the label space. On the AG-News seed where an unlucky partition
```

Replacement:

```latex
all three seeds, by margins of $0.13$ to $0.24$. And the estimator responds to the
data. On the AG-News seed where an unlucky partition
```

The cut half is the closing clause of the very next sentence, "which a rule keyed
to the number of classes would not do".

## A10. Takeaway heading, `sec:exp-cost`, around line 338

Current:

```latex
\paragraph{Claim} The cryptographic cost of the protocol is dominated by
one-time setup, and the recurring per-query traffic is a few megabytes.

We do not simulate the cryptography. The protocol is implemented in real
```

Replacement:

```latex
The cryptographic cost of the protocol is dominated by
one-time setup, and the recurring per-query traffic is a few megabytes.
We do not simulate the cryptography. The protocol is implemented in real
```

## A11. Antithesis, around line 470

Current:

```latex
and the reason is the shape of the circuit rather than the quality of the
measurement. Serving a query is a fixed sequence, one ciphertext-by-ciphertext
```

Replacement:

```latex
and the reason is the shape of the circuit. Serving a query is a fixed sequence, one ciphertext-by-ciphertext
```

## A12. Takeaway heading, `sec:exp-leak`, around line 536

Current:

```latex
\paragraph{Claim} The protocol exposes no training-time artifact and no model,
so the only remaining channel is the sequence of answers the served model returns,
and that channel is bounded by the query allowance rather than eliminated.

The training-time surface is removed by construction. No gradient, update, or
```

Replacement:

```latex
The protocol exposes no training-time artifact and no model,
so the only remaining channel is the sequence of answers the served model returns,
and that channel is bounded by the query allowance rather than eliminated.
The training-time surface is removed by construction. No gradient, update, or
```

"bounded by the query allowance rather than eliminated" stays. It is the
distinction the paper cannot afford to lose.

## A13. Antithesis, around line 595

Current:

```latex
$2.2\times10^4$ on Banking77. The binding case is the small label space, not the
large one, which is worth stating plainly because it runs against intuition. A
```

Replacement:

```latex
$2.2\times10^4$ on Banking77. The binding case is the small label space, which is
worth stating plainly because it runs against intuition. A
```

There are two label-space sizes, so naming one names the other.

## A14. Run-in heading, around line 601

Current:

```latex
\paragraph{What a copy does not give} Fidelity measures agreement with the
```

Replacement:

```latex
Fidelity measures agreement with the
```

## A15. Run-in heading, around line 647

Current:

```latex
\paragraph{The partition costs more than the disclosure does} The last column of
```

Replacement:

```latex
The last column of
```

A conclusion used as a label. The paragraph reaches it with three measured
comparisons and states it at the end.

## A16. Antithesis, around line 658

Current:

```latex
Disclosing the model changes the threat model
rather than the operating point. A participant that holds the model in plaintext
```

Replacement:

```latex
Disclosing the model changes the threat model. A participant that holds the model in plaintext
```

The sentence before it already says the disclosed model is not an alternative
configuration of this protocol.

---

# B. `sections/method.tex`

## B1. Antithesis, around line 26

Current:

```latex
rest of this section can be read as consequences of the requirements rather than
as independent design preferences.
```

Replacement:

```latex
rest of this section can be read as consequences of the requirements.
```

## B2. Run-in heading, around line 149

Current:

```latex
\paragraph{What the argument fixes, and what it leaves open} The requirement
```

Replacement:

```latex
The requirement
```

Named in the brief as the kind that should go. The paragraph opens on its
subject without it.

## B3. Antithesis, around line 161

Current:

```latex
The adapter is relocated rather than discarded. Each client retains its own, so the
```

Replacement:

```latex
The adapter is relocated. Each client retains its own, so the
```

"Each client retains its own" is the next clause and says the adapter is not
discarded.

## B4. Antithesis, around line 330

Current:

```latex
measure the accuracy of both arrangements on its held-out data and vote. This is
not a matter of noise. The procedure estimates the wrong quantity. The arrangement without an
```

Replacement:

```latex
measure the accuracy of both arrangements on its held-out data and vote. The
procedure estimates the wrong quantity. The arrangement without an
```

"Estimates the wrong quantity" already excludes noise, and the paragraph closes
on "systematically optimistic".

## B5. Antithesis, around line 353

Current:

```latex
\cref{eq:aggregate}. Two asymmetries follow from the setting rather than from
choice. For the shared arrangement there is one model, so per-class evidence from
```

Replacement:

```latex
\cref{eq:aggregate}. Two asymmetries follow from the setting. For the shared
arrangement there is one model, so per-class evidence from
```

## B6. Run-in heading, around line 451

Current:

```latex
\paragraph{Protection without perturbation} The aggregation of
```

Replacement:

```latex
The aggregation of
```

The heading states the conclusion of the paragraph it labels. This is the last
paragraph of the threat model and reads as a closing paragraph without a label.

---

# C. `sections/related.tex`

## C1. Antithesis, around line 175

Current:

```latex
setting of \cref{sec:serving} affordable, and we compose with it rather than
re-solve it. The map served here is linear in the features.
```

Replacement:

```latex
setting of \cref{sec:serving} affordable, and we compose with it. The map served here is linear in the features.
```

Composing with a literature is not re-solving it. `method.tex` already states
"We do not re-solve it" as its own sentence in `sec:serving`, so the point is not
lost.

---

# D. `sections/security.tex`

## D1. Antithesis, around line 36

Current:

```latex
can be measured against it. The server and the serving party are entities outside
the functionality rather than part of it, so that either may be considered
corrupt.
```

Replacement:

```latex
can be measured against it. The server and the serving party are entities outside
the functionality, so that either may be considered corrupt.
```

Outside and part of are the only two options, so the second half is the first
half inverted.

## D2. Antithesis, around line 169

Current:

```latex
clients deviate. The server and the serving party remain honest, and
\cref{sec:malicious-ext} explains why that assumption is necessary rather than
convenient. We bound what a deviating coalition learns about the data of a
```

Replacement:

```latex
clients deviate. The server and the serving party remain honest, and
\cref{sec:malicious-ext} explains why that assumption is necessary. We bound what
a deviating coalition learns about the data of a
```

## D3. Antithesis, around line 190

Current:

```latex
The equal-size restriction is necessary rather than cosmetic. The per-client
```

Replacement:

```latex
The equal-size restriction is necessary. The per-client
```

The two sentences that follow prove necessity, which is what removes cosmetic.

## D4. Antithesis, around line 237

Current:

```latex
\Cref{thm:malicious} keeps the serving party honest. That assumption is not a
convenience, and the reason is worth stating, because it marks the boundary of
what this message pattern can achieve.
```

Replacement:

```latex
\Cref{thm:malicious} keeps the serving party honest. That assumption is necessary,
and the reason is worth stating, because it marks the boundary of what this
message pattern can achieve.
```

This is the same claim as D2, stated twice in the same section. Both now say it
positively, and the subsection proves it.

---

# E. Sites looked at and left alone

## Run-in headings kept, and why

| file, heading | why it stays |
|---|---|
| `method.tex` `The construction`, three times | one per method subsection, the same label in the same position each time, so it navigates |
| `method.tex` `Necessity of the partition` | names the argument that follows |
| `method.tex` `The aggregation`, `The division`, `Cost` | content names, and a reader looks for each one |
| `method.tex` `Encryption of the query`, `Restriction to the predicted label`, `Directed decryption` | the three design decisions of `sec:serving`, each named for what it is |
| `method.tex` `Cost and the role of the serving party`, `Scope` | content names |
| `method.tex` `Inadequacy of the held-out vote` | a noun phrase naming the procedure the paragraph rejects, not a comment on the argument |
| `method.tex` `A prior-weighted estimator`, `Requirements on the held-out split`, `Cost and disclosure` | content names |
| `method.tex` `View of the server and the serving party`, `Collusion among clients`, `Extraction through the query interface`, `Outside the guarantee` | the threat model reads as a checklist and the labels are what a reviewer scans |
| `experiments.tex` `Sensitivity` | names the table that follows |
| `experiments.tex` `A partition at which the charge is negative` | flags an anomaly a reviewer will look for. Claim shaped, but the label is how they find it |
| `experiments.tex` `Selection on these partitions`, `Disclosure of the estimator` | content names |
| `experiments.tex` `Cost of query encryption`, `The encrypted reciprocal`, `The argmax`, `The two axes that set the cost`, `Hardware acceleration`, `Communication`, `Correctness` | the operation-by-operation labels of `sec:exp-cost`. Removing any one of these makes the section harder to read |
| `experiments.tex` `What one query costs, end to end` | a wh-clause, so it is the shape Sav objected to, but the paragraph opens "We state the total plainly, because the per-operation rows invite the wrong sum", which needs the label above it. Rephrasing it to a noun phrase belongs with T19, not here, because that adds words rather than removing them |
| `experiments.tex` `Cost of extraction`, `Comparison with a released model` | content names |
| `experiments.tex` `Linearity of the shared quantity`, `Bounds on model extraction`, `Malicious participants`, `Availability` | the four limitations. A reviewer checks limitations as a list and these are the list |

## Antithesis sites judged and left alone

| file, text | why it stays |
|---|---|
| `intro.tex` "one-shot does not mean the parties stop communicating. It means that no intermediate training artifact is ever exposed" | note 6, already agreed with the PIs and already pasted. Load bearing against a reviewer who reads one-shot as silence |
| `intro.tex` "The protocol exchanges model updates instead of data" | a fact about federated learning, not a rhetorical contrast |
| `intro.tex` "in real multiparty CKKS rather than simulating it" | the negative half is a real methodological claim. Many papers simulate |
| `method.tex` "constrains the position of the shared map, not the task it serves" | this is the repository's own scope wording and both halves carry weight |
| `method.tex` "imposed by construction rather than by policy" | anchored to the sentence before it, which reports that the operators of a deployed interface responded with policy |
| `method.tex` "as a bound on queries rather than a cryptographic hardness claim" | the distinction the paper must not lose |
| `method.tex` "This is a bound on queries, not a cryptographic guarantee" | same, in the threat model |
| `method.tex` "ciphertext by ciphertext rather than ciphertext by plaintext" | a technical fact with two named alternatives |
| `method.tex` "the low-rank product per site rather than a different order of magnitude" | a size claim, and both halves are quantities |
| `experiments.tex` "we ran our protocol on theirs rather than restate numbers from incomparable setups" | states what we declined to do, which a reviewer will want to know |
| `experiments.tex` "raises throughput rather than lowering latency" | two different quantities, both real |
| `experiments.tex` "paid once per aggregation rather than per query" | a fact |
| `experiments.tex` "the result is exact rather than approximate" | a fact, and under CKKS it is worth saying |
| `experiments.tex` "carries through to the whole rather than being absorbed by effects that dominate in deep encrypted inference" | the negative half names the failure mode the reader is worried about |
| `experiments.tex` "stop at the ratio rather than quoting an end-to-end accelerated latency" | states what we declined to do |
| `experiments.tex` "bounded by the query allowance rather than eliminated" | the distinction the paper must not lose |
| `experiments.tex` "Returning only the label rather than the logits" | a fact about the interface |
| `experiments.tex` "track the size of the head rather than the task" | the finding itself. Head size against task difficulty is exactly what the measurement separates |
| `experiments.tex` "attributable to the partition of the data, and not to the decision never to decrypt" | a quantitative attribution between two named causes, with numbers on both |
| `experiments.tex` "The contrast is not a matter of degree" | see the note below. I was not sure about this one |
| `experiments.tex` "a calibrated accuracy estimate, not only a ranking" | additive rather than oppositional. The second half is what a reader expects and the first half exceeds it |
| `related.tex` "Differential privacy proves a statistical bound ... Encryption makes a contribution computationally indistinguishable" | a two-sentence comparison of two mechanisms, both halves carrying content |
| `security.tex` "The bound scales with the corruption threshold rather than with the federation" | two scalings, and which one holds is the point |
| `security.tex` "checks provenance rather than content" | distinguishes the first mechanism from the second, which certifies the function |
| `security.tex` "a property of the functionality, not of our instantiation of it" | a scope claim. The next sentence builds on the negative half, "Any protocol that realizes $\Fhe$ inherits it" |

## Two things I noticed and did not touch

1. `experiments.tex`, around line 621, "The contrast is not a matter of degree."
   This is a bare negative with no positive half in the sentence, so it does not
   fit the pattern, but it does read as rhetorical setup. Deleting it would drop
   a claim, that a released model differs in kind. Rewriting it would be a new
   sentence rather than a removal. Left alone, flagged.
2. `security.tex`, around line 294, "the answer is not nothing." This is
   understatement rather than antithesis, so it belongs to the figure-of-speech
   rule and not to this pass. Left alone, flagged.

## What this pass does not touch

The opening paragraph of `sec:experiments` still says "Each subsection below
states a claim in one sentence, describes the experiment that tests it, and
reports the result." That stays true after the five labels come off, because
every claim sentence survives in place. No edit needed.
