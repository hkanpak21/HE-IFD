# The three open introduction comments

Küpçü, 11 August 7:12 pm and 7:14 pm, and 12 August 10:47 am. Five blocks.

I applied all five to a scratch copy and built it. **Still 20 pages, zero
undefined citations, zero undefined references, zero overfull boxes.** Figure 1
moves from page 6 to page 3, which puts it beside the paragraph that explains it.

No bold `Problem 1` headings, per your instruction to keep it natural. No new
subsection. The reorder is carried by one added sentence and one changed verb.

---

## A. `intro.tex`. The signpost, so three problems read as three problems

Küpçü's 7:14 pm comment says the section alternates problem and solution and
looks confused. It does not in fact alternate. It runs three problems and then
the solution. What makes it read as alternating is that the third paragraph opens
on a fix before the problems are finished, so the reader loses count.

Two small changes fix that without moving a paragraph. First, tell the reader
that three obstacles are coming.

FIND

```latex
infrastructure raises the same objection~\cite{xiao2023offsite}.
```

REPLACE

```latex
infrastructure raises the same objection~\cite{xiao2023offsite}. Three obstacles
stand between that setting and a protocol these organizations could deploy.
```

## B. `intro.tex`. The same paragraph opens on a requirement, not a fix

FIND

```latex
Two measures remove that surface together. Making the protocol \emph{one-shot}
```

REPLACE

```latex
Removing that surface takes two measures together. Making the protocol \emph{one-shot}
```

One verb. The paragraph then reads as what is needed rather than as what we did,
and the solution arrives once, where it belongs.

---

## C. `intro.tex`. The claim about POSEIDON, which is false

This is not one of the three comments. It is a defect found while answering
them, and it has to go with this edit because it sits in the paragraph the
reorder passes through.

The manuscript says every protocol discussed above hands the participants a
decrypted model. POSEIDON is discussed two paragraphs above and does not.
Its abstract, verbatim, says it employs multiparty lattice-based cryptography
"to preserve the confidentiality of the training data, the model, and the
evaluation data", and that it "enables the resulting encrypted model to be used
for privacy-preserving inference on encrypted evaluation data". So the sentence
asserts something untrue about a paper Sinem Sav wrote, and the parenthetical
added on Overleaf widens its scope rather than narrowing it.

Nothing else breaks. The priority claim rests on one-shot and on fine-tuning,
and both survive.

FIND

```latex
Applying both measures (encrypted, one-shot training) still leaves one artifact exposed, namely the model itself.
Every protocol above ends by handing the final decrypted model to the participants, which is
unacceptable when the model may not be distributed at all.
```

REPLACE

```latex
Applying both measures still leaves one artifact exposed, namely the model itself.
One-shot protocols end by handing the final model to every participant, which is
unacceptable when the model may not be distributed at all. Encrypted training does
withhold it, but the cost just described puts a pretrained backbone out of reach.
```

---

## D. `intro.tex`. The overview, with Figure 1 beside it

Küpçü's 7:12 pm comment asks for Figure 1 and its explanation in the
introduction under an overview heading. This gives him both, without a heading,
because the paragraph is the last thing before the contributions and needs no
label to be found.

Moving `\input{figures/training}` is what makes the figure float to page 3
instead of page 6. Delete that line from `method.tex`, see block E.

FIND

```latex
The querier must build its query from parts it can run itself, so those parts must
```

REPLACE

```latex
\input{figures/training}

\Cref{fig:training} shows how the shared head is built. Every client fine-tunes an
adapter and a classifier head on the same frozen public backbone, keeps the
adapter, and uploads one encrypted head displacement weighted by the classes it
holds. The server adds the ciphertexts and divides by the per-class totals under
encryption, so the shared head exists only as a ciphertext and the server holds no
key to it. A client that wants a prediction computes the features of its query
itself, encrypts them, and sends them to the serving party, which applies the
encrypted head and takes the argmax under encryption. A quorum of clients then
switches the result to that client alone, which decrypts one label.

The querier must build its query from parts it can run itself, so those parts must
```

The overview at the head of Section III stays. It is a roadmap for four
subsections and it names all three figures. This one walks one figure at a
coarser grain. If the PIs find the pair repetitive, cut the first two sentences
of the method overview, not this paragraph, since this is the one Küpçü asked
for.

---

## E. `method.tex`. Remove the figure input, and explain the figure

Two edits in one file. The first is the other half of block D.

FIND

```latex
\input{figures/training}

\paragraph{The construction} Each client uses the same frozen public backbone
```

REPLACE

```latex
\paragraph{The construction} Each client uses the same frozen public backbone
```

The second answers the 10:47 am comment directly. "Shows the arrangement" tells
a reader that a figure exists. It does not tell them what to look at.

FIND

```latex
The adapter is trained locally and never transmitted. \Cref{fig:training} shows
the arrangement.
```

REPLACE

```latex
The adapter is trained locally and never transmitted. In \cref{fig:training} the
adapters stay inside the client boxes, only the head displacement crosses to the
server, and the arrow that would carry an adapter aggregate does not exist.
```

The last clause is the point of the figure and the paper never said it. What a
reader should notice is a missing arrow.

---

## Paste order

A, B, C, D into `intro.tex`, then E into `method.tex`. Block D and the first
half of block E are one move and must both be applied, or the figure is either
duplicated or lost.
