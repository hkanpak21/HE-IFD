# T35. The introduction and the abstract. Find and replace list

Answers Küpçü's comments of 11 August on the contribution bullets (7:06 and
7:07 pm), on the evaluation paragraph (7:09 pm), on the membership-inference
claim (3:32 pm), and on results in the abstract (3:21 pm). Items T9, T10, T12
and T13 of `docs/plan/paper-todo-2026-08-19.md`.

Nothing here is applied to `docs/paper/`. Every FIND block is verbatim from the
current file and occurs exactly once in it. Paste in file order.

**Two files only**, `sections/intro.tex` and the abstract in `main.tex`. No
number, citation or cross-reference changes anywhere in this list, with one
exception noted at A4, where a sentence is dropped and its two figures stay.

**No collision with the pending pastes.** `T22-communication-corrected.md`
changes the last sentence of the abstract, the one carrying the traffic figure.
No anchor here touches that sentence. `T11-T26-T28-citations-and-audit.md`
adds citations at `intro.tex` line 14 and defers both over-claim sites to this
file, item B14. Order of application does not matter.

## Length

| where | words before | words after |
|---|---|---|
| the three bullets | 181 | 209 |
| the evaluation paragraph, two sentences into one | 29 | 29 |
| the leakage sentences, two into one | 43 | 30 |
| `intro.tex` net | 936 | 951 |
| the abstract | 249 | 251 |

The introduction is a wash. The abstract gains one sentence and pays for it
with two cuts, one of which note 1 of `PI_notes_2026-08-06.md` already named as
the sentence to drop if length binds.

---

# A. `sections/intro.tex`

## A1. Contribution bullet one, around line 81

Küpçü, 11 August 7:06 pm, on "so a coalition of all but one client has nothing
to subtract from": not clear.

The bullet names the subtraction but neither the thing subtracted nor what the
subtraction would achieve, so the reader cannot see the attack being denied.
One clause supplies both. The wording is `method.tex` line 168, shortened.

FIND

```latex
  its own features alone but cannot recognize a class it has never seen. No adapter
  aggregate exists, so a coalition of all but one client has nothing to subtract
  from (\cref{sec:split}).
```

REPLACE

```latex
  its own features alone but cannot recognize a class it has never seen. No adapter
  aggregate exists, so a coalition of all but one client cannot recover the last
  client's adapter by subtracting its own contributions (\cref{sec:split}).
```

Note 16 requires this bullet to keep the property it buys, "no adapter sum to
invert". It does, and it now says what the sum would have been used for.

## A2. Contribution bullet two, around line 87

Küpçü, 11 August 7:06 pm, on "Only a label leaves the protocol, and a label
denies the linear solve that logits would permit": not clear, and never
introduced earlier.

Two undefined terms in one clause. Neither "logits" nor "linear solve" appears
anywhere before this point in the paper. The replacement says the same thing in
plain words and defines the withheld object where it is used.

FIND

```latex
  switches the result to the querier's key. Only a label leaves the protocol, and a
  label denies the linear solve that logits would permit (\cref{sec:serving}).
```

REPLACE

```latex
  switches the result to the querier's key. Only a label leaves the protocol, so a
  client cannot collect the per-class scores that would let it solve for the head
  (\cref{sec:serving}).
```

`method.tex` line 247 argues this at length and keeps the word logits, which is
correct there because the method section has introduced it. The bullet does not
need the word.

## A3. Contribution bullet three, around line 89

Küpçü, 11 August 7:07 pm, on "Two arrangements": not defined clearly earlier.

He is right that the term arrives cold. The definition is one clause, copied
from `method.tex` line 319 with "with no adapter at all" dropped, since "bare"
carries it.

FIND

```latex
\item \textbf{A selection rule that runs under encryption.} Two arrangements are
  servable at the same cost, and which one is better depends on the task. Each
  client scoring both on its own held-out data and voting estimates the wrong
  quantity, and selects wrongly whenever the two differ. The estimator given here
  corrects that, needs no fitted threshold, and reveals only which arrangement won
  (\cref{sec:selection}).
```

REPLACE

```latex
\item \textbf{A selection rule that runs under encryption.} Two arrangements are
  servable at the same cost, the shared head over each client's own adapter and the
  shared head over the bare public backbone. Which one is better depends on the
  task. Each client scoring both on its own held-out data and voting estimates the
  wrong quantity, and selects wrongly whenever the two quantities differ. The
  estimator given here corrects that, needs no fitted threshold, and reveals only
  which arrangement won (\cref{sec:selection}).
```

**One word in that block is not Küpçü's comment and can be reverted.** "whenever
the two quantities differ" was "whenever the two differ". Naming the two
arrangements immediately above gives "the two" a second possible antecedent, and
the sentence is about two quantities rather than two arrangements. The word
closes the ambiguity my own edit opens. Say the word and I will paste the block
without it.

## A4. The over-strong membership-inference claim, around line 17

Küpçü, 11 August 3:32 pm, on "membership inference far stronger than anything
possible against the final model": too strong, support it or weaken it.

He is right, and the sentence cannot be supported as written. Nasr et al.
measured $87\%$ against the update stream and $54.5\%$ against the final model
on one model and one dataset. That is a measurement, not a statement about every
attack that could exist. The paper also contradicts the strong reading itself,
since Section 5.6 measures an attack on the served head.

The next sentence already carries the measurement, so the claim and its evidence
are stated twice. Folding them into one sentence binds the claim to the number
and removes thirteen words.

FIND

```latex
it~\cite{zhu2019deep,geiping2020inverting}. An observer of the per-round updates
mounts membership inference far stronger than anything possible against the
final model. On the same model and dataset, an attack that reaches $87\%$
accuracy against the update stream falls to $54.5\%$ against the final model
alone~\cite{nasr2019comprehensive}.
```

REPLACE

```latex
it~\cite{zhu2019deep,geiping2020inverting}. An observer of the per-round updates
mounts membership inference at $87\%$ accuracy on one model and dataset, where the
same attack against the final model alone falls to
$54.5\%$~\cite{nasr2019comprehensive}.
```

Both figures survive and the citation is unchanged. This is the same fix note 4
of `PI_notes_2026-08-06.md` applied to "rather than in the model it produces",
where the agreed reason was that the measured number two sentences later carries
the comparison on its own.

## A5. The evaluation paragraph repeats itself, around line 101

Küpçü, 11 August 7:09 pm, on "Our accounting includes the traffic that recurs on
every query": there is repetition here, and is this not a contribution in its
own right.

The repetition is inside the paragraph. The sentence before it already says the
accounting covers communication, and traffic is communication, so the flagged
sentence adds only the word "recurring". The paragraph also restates, in
accounting terms, the point line 30 makes in definitional terms, that one-shot
does not mean the parties stop communicating.

Note 15 of `PI_notes_2026-08-06.md` marks the recurring-traffic guard as load
bearing and says not to drop it. The guard therefore survives as a trailing
clause, and the separate sentence goes.

FIND

```latex
real multiparty CKKS rather than simulating it. We report what withholding the model costs, in accuracy against a disclosed model
and in added communication and computation. Our accounting includes the traffic
that recurs on every query.
```

REPLACE

```latex
real multiparty CKKS rather than simulating it. We report what withholding the model costs, in accuracy against a disclosed
model and in the communication and computation it adds, including the traffic that
recurs on every query.
```

**On the second half of his comment, whether the accounting is a contribution.**
My answer is no, and the list stays at three items. The three contributions are
parts of the protocol, and a reader can point at each one. A measurement is what
Section V does with them. A fourth bullet would also add structure, which ground
rule 2 and the direction of 2026-08-19 both push against.

**Optional, if Küpçü presses.** One sentence at the end of the third bullet,
inside the existing item, which names the accounting without adding a fourth.

```latex
  which arrangement won (\cref{sec:selection}). We measure all three in real
  multiparty CKKS, including the traffic every query costs (\cref{sec:exp-cost}).
```

I recommend against it. It makes the selection bullet carry a claim about the
other two, and A5 above already states it one paragraph later.

---

# B. `main.tex`, the abstract

## B1. The same over-strong claim, around line 112

The phrasing Küpçü flagged in the introduction sits in the abstract as
"substantially stronger than any attack on the final model". Same defect, same
quantifier over all attacks. The abstract carries no numbers here, so the fix
binds the claim to the attacks that have been published rather than to a figure.

FIND

```latex
Gradients
and per-round updates permit reconstruction of training data and support
membership inference substantially stronger than any attack on the final model.
```

REPLACE

```latex
Gradients
and per-round updates permit reconstruction of training data, and published
attacks infer membership from them far more accurately than from the final model.
```

Two words longer. Note 4 of `PI_notes_2026-08-06.md` judged this site comparative
and left it alone, and item B14 of `T11-T26-T28-citations-and-audit.md` reopened
it and deferred it here. This is the only proposal for it.

## B2. What the protocol adds over encrypted multi-round learning, around line 117

Küpçü, 11 August 3:21 pm, asks for more about results and about the comparison
with normal FL, clarified on 2026-08-20 as cryptographically secure FL, on
security, privacy and accuracy, with no new experiments.

The accuracy half is already answered. The abstract of 2026-08-19 carries $0.61$
to $0.79$ against $0.20$ to $0.48$ for a client alone, the $0.03$ to $0.14$
charge against a disclosed model, and the per-query time. What is missing is one
sentence on encrypted multi-round learning.

FIND

```latex
A one-shot protocol that exchanges a single encrypted contribution removes that surface,
but it still ends by handing the final model to every participant, which is not
permitted where the model is itself a regulated or proprietary asset. We present
```

REPLACE

```latex
A one-shot protocol that exchanges a single encrypted contribution removes that surface,
but it still ends by handing the final model to every participant, which is not
permitted where the model is itself a regulated or proprietary asset. Multi-round
encrypted training also withholds the model, but it pays a cryptographic cost on
every round and cannot adapt a pretrained backbone. We present
```

**What this sentence does not say, and why.** It does not say that encrypted
training discloses the model. POSEIDON's abstract, read on arXiv 2009.00349 on
2026-08-20, states that it employs multiparty lattice-based cryptography "to
preserve the confidentiality of the training data, the model, and the evaluation
data". Writing that encrypted training hands over the model would be false, and
it would be false in front of a PI who wrote POSEIDON. Conceding the point costs
nothing, because the priority claim rests on one-shot and on fine-tuning, which
is exactly where note 1 and note 9 put it.

**What supports the two claims it does make.** The per-round cost is stated in
the introduction at line 38 and in `related.tex` line 66, "The encryption cost is
paid on every round". The reach claim is note 9 of `PI_notes_2026-08-06.md`,
already pasted into the introduction at line 42, where POSEIDON's own figure
carries it, a three-layer network of sixty-four neurons per layer on handwritten
digits at ten parties in $1.4$ hours. The backbones here hold on the order of one
hundred million parameters.

**Fuller alternative, if the reason should be in the abstract too.** Ten words
longer, which puts the abstract at $261$.

```latex
Multi-round
encrypted training also withholds the model, but it pays a cryptographic cost on
every round, and that cost grows with the network it trains, so it cannot adapt a
pretrained backbone.
```

## B3. First payment, around line 124

The new sentence is twenty-two words. This cut is eleven of them.

Note 1 of `PI_notes_2026-08-06.md` already named this sentence as the one to
remove if length binds, and kept it only because there was room. There is no
longer room. It also uses "arrangements" without defining the term, which is the
same defect Küpçü flagged at 7:07 pm in the introduction, so the cut answers his
comment in a second place.

FIND

```latex
asked. The federation also chooses between two servable arrangements without decrypting either. Across four
```

REPLACE

```latex
asked. Across four
```

This anchor is inside the long final line of the abstract and stops well before
the traffic figure, so it does not collide with C4 of
`T22-communication-corrected.md`.

## B4. Second payment, around line 110

The other eleven words. The opening clause states that organizations fine-tune
pretrained models, which the rest of the sentence implies with "a jointly
fine-tuned model" and which B2 now states directly with "a pretrained backbone".

FIND

```latex
Organizations adapt large pretrained models to private data by fine-tuning, and parties
holding complementary data over the same task would each gain from a jointly
fine-tuned model, yet cannot pool their data to build one.
```

REPLACE

```latex
Organizations holding complementary data over the same task would each gain from a
jointly fine-tuned model, yet cannot pool their data to build one.
```

**This one touches a sentence nobody complained about**, so it is the item to
drop if the rule against re-opening settled text outweighs the word count.
Without it the abstract stands at $262$ words with B2, or at $272$ with the
fuller alternative. With it, $251$.

---

# C. What I looked at and left alone

| site | why |
|---|---|
| `intro.tex` line 30, "one-shot does not mean the parties stop communicating" | note 6, agreed with the PIs and load bearing |
| `intro.tex` line 49, "Every protocol above ends by handing the final decrypted model to the participants" | **flagged, not fixed.** POSEIDON keeps the model confidential, so "every protocol above" is not exact, and the paragraph reads POSEIDON into it. The fix belongs with T6, which reorders these paragraphs, and it is one word, "most". Raising it here would change a paragraph nobody commented on |
| the three bullet headings | note 16 settled them as noun phrases naming artifacts |
| "In this work, we present HE-OFT" | note 11, the PI dictated the template and the first person |
| the abstract's mechanism sentences | Sav reviewed them on 4 August and did not comment |
| `intro.tex` line 74, "which, in a transformer, is a single place" | note 13 wrote it and the PIs accepted it |
