# T32. The method section comments. Find and replace list

Answers the PI comments on `sections/method.tex` recorded in
`docs/PI_comments_on_2026-08-19.md`, items T7, T14, T15 and T16 of
`docs/plan/paper-todo-2026-08-19.md`.

Nothing here is applied to `docs/paper/`. Each entry gives the file, the
approximate line, the current text verbatim, and the replacement. Paste in file
order.

`sec:mhe` is not touched. No number, citation or cross-reference target changes
anywhere in this list, except that three existing figure labels gain a reference
in the new overview paragraph.

## Which comment each entry answers

| entry | comment | item |
|---|---|---|
| A1 | Küpçü 11 Aug 7:12 pm, and 12 Aug 10:47 am | T7 |
| A2, C1 | Küpçü 12 Aug 10:33 am | T14 |
| A3 | Küpçü 12 Aug 10:39 am, Sav 17 Aug 11:16 am | T15 |
| A4 | Küpçü 12 Aug 10:40 am | T16.1 |
| A5 | Küpçü 12 Aug 10:49 am | T16.3 |
| A6 | Küpçü 12 Aug 10:50 am | T16.4 |
| D1 | Sav 17 Aug 11:19 am | T16.4 note, see D |

## Effect on length

| entry | net |
|---|---|
| A1 | plus 12 lines |
| A2 | minus 2 lines |
| A3 | zero |
| A4 | plus 1 line |
| A5 | minus 1 line |
| A6 | plus 2 lines |
| C1 | plus 2 lines |

Net about plus 14 lines, which is the overview. Everything else is flat or
shorter.

## Ordering against T25

Three of the T25 anchors sit in the same paragraphs as entries here, and none
of them overlaps a `FIND` block in this file. T25 B1 is at line 26, T25 B2 is
the run-in heading at line 149, T25 B3 is at line 161. A5 starts at line 155 and
A6 is line 166, both below B2 and clear of B3. The two lists can be pasted in
either order.

---

# A. `sections/method.tex`

## A1. The overview, at the head of Section III, lines 1 to 7

Küpçü asks for an overview and separately notes that \cref{fig:training} is
never explained. One paragraph answers both. It walks the protocol from the
local fine-tune to the label the querier decrypts, and it names all three
figures at the step each one draws, so the figures stop being unexplained. It
states no result and repeats none of the constraint list below it.

The stale `% Add overview in beginning` comment on line 1 goes with the paste.

FIND

```latex
% Add overview in beginning

\section{Method}
\label{sec:method}

\subsection{Setting}
\label{sec:setting}
```

REPLACE

```latex
\section{Method}
\label{sec:method}

The protocol runs in two phases. In the first, each client fine-tunes an adapter
and a classifier head on the same frozen public backbone, keeps the adapter, and
uploads its head displacement once, weighted by its own per-class counts and
encrypted. The server adds the ciphertexts and divides by the per-class totals
under encryption, so the shared head exists only as a ciphertext
(\cref{fig:training}). In the second, a client computes the features of its query
itself, encrypts them, and sends them to the serving party, which applies the
encrypted head and reduces the encrypted logits to the index of the largest
(\cref{fig:serving}). A quorum of clients switches that index to the querying
client, which decrypts one label. The federation also chooses between two servable
arrangements under encryption, and decrypts only which one it adopts
(\cref{fig:selection}). The subsections below derive each step.

\subsection{Setting}
\label{sec:setting}
```

Checks made against the section before writing it. The weighting is formed on
the client before encryption, per the sentence after \cref{eq:aggregate}, so the
paragraph says the client weights and the server adds. The division is the
encrypted reciprocal of \cref{eq:aggregate}, paid once. The serving party
receives encrypted features, never plaintext features. The quorum key-switches
rather than decrypts collectively. The selection decrypts exactly one value.

## A2. The Dirichlet sentence leaves the Setting, around line 10

Küpçü is right that the partition is an experimental choice. Nothing in the
protocol reads $\alpha$. What the method does need is the fact behind the
partition, that clients hold different classes and some hold none of a class,
because the coverage argument at line 162 and the estimator of
\cref{sec:selection} both rest on it. One short sentence carries that fact and
the experimental parameter goes.

FIND

```latex
of $\Cc$ classes. Client $j$ holds data $\Dj$ of size $\nj$. In our experiments, the data are
heterogeneous. Each client's class proportions are drawn from a Dirichlet
distribution of concentration $\alpha$, so a smaller $\alpha$ leaves each client a
few dominant classes and almost none of the rest. The clients want a classifier
```

REPLACE

```latex
of $\Cc$ classes. Client $j$ holds data $\Dj$ of size $\nj$. The class proportions
differ across clients, and a client may hold no example of a class. The clients want a classifier
```

## A3. C3, around line 38

Sav asks for C3 to be clearer so that it does not read against C4. C3 is about
models with different starting points and C4 applies after C3 has forced one
common start. The lead sentence now carries the condition, and the closing
clause names the join. C4 is not touched.

FIND

```latex
\item[\textbf{C3}] \emph{Independently trained models do not combine linearly.}
  In the parameter space of a deep network, models trained from different
  starting points occupy incomparable regions. \emph{Therefore}, every client
  starts its trainable unit from one public initializer on one frozen public
  backbone.
```

REPLACE

```latex
\item[\textbf{C3}] \emph{Models trained from different starting points do not
  combine linearly.} In the parameter space of a deep network they occupy
  incomparable regions. \emph{Therefore}, every client starts its trainable unit
  from one public initializer on one frozen public backbone, and the linear
  combination of \textbf{C4} applies only after that common start.
```

## A4. C7, plaintext rather than public, around line 56

Küpçü asks whether we mean plaintext. We do, and as written the sentence is
also false. The client runs the public backbone and its own adapter, and the
adapter is private to that client, so "everything the client runs is public"
overstates it. What is true is that the client runs both in the clear.

`public` stays everywhere else in the section, because every other use is
correct as it stands, the public backbone, the public initialiser, the public
per-client counts, the public scalars of \cref{eq:estimator} and the public
plaintext mask of \cref{alg:select}. This is the only site that changes.

FIND

```latex
  queries.} A query is formed from features, and the client that asks the query must be able
  to compute those features itself. \emph{Therefore}, everything the client runs is
  public, and the trained quantity that is shared cannot sit inside the backbone.
```

REPLACE

```latex
  queries.} A query is formed from features, and the client that asks the query must be able
  to compute those features itself. \emph{Therefore}, the client runs the backbone
  and its own adapter in plaintext, and the trained quantity that is shared cannot
  sit inside the backbone.
```

## A5. Generation scope, the answer first, around line 155

Küpçü reaches the end of the paragraph and asks whether we evaluate generation.
We do not. The paragraph reaches the vocabulary projection of a decoder before
it says so, so the scope statement moves ahead of the claim it qualifies.
`therefore` becomes `itself` because the intervening sentence breaks the
inference chain.

FIND

```latex
features the client can compute from a prefix it generated itself. The
construction therefore does not depend on the label space being a set of
classes. We evaluate classification only, and \cref{sec:scope} records what a
generation setting would additionally require, including the restriction to
greedy decoding that \cref{sec:serving} imposes.
```

REPLACE

```latex
features the client can compute from a prefix it generated itself. We evaluate
classification only. The construction itself does not depend on the label space
being a set of classes, and \cref{sec:scope} records what a generation setting
would additionally require, including the restriction to greedy decoding that
\cref{sec:serving} imposes.
```

## A6. Name the two halves, around line 166

The halves are the two clauses of "A client can improve its own representation
alone, but it cannot learn to recognise a class it has never observed". Both are
measured in \cref{sec:exp-split}, the first by the personal adapter arrangement
against the shared head on the large label spaces, the second by the alone
column of \cref{tab:headline} against the federated head.

FIND

```latex
the federation supplies. \Cref{sec:exp-split} measures both halves of this claim.
```

REPLACE

```latex
the federation supplies. \Cref{sec:exp-split} measures both halves, how far a
client gets with its own representation and how much the shared head adds on the
classes it does not hold.
```

---

# B. What still depends on $\alpha$ in Section III after A2

Checked by searching the whole section for `alpha`, `Dirichlet`, `heterogen` and
`skew`.

| site | status |
|---|---|
| line 10, the sentence itself | removed by A2 |
| line 86, the `$\alpha$` row of \cref{tab:notation} | remains, see below |
| anything else in Section III | none. No equation, algorithm, figure caption or paragraph reads $\alpha$ |

The notation table is the paper's symbol list and $\alpha$ is used throughout
Section V, so I recommend leaving the row where it is. Sitting in a section that
no longer mentions the symbol is a smaller defect than defining a live symbol
nowhere. If the PIs would rather the table hold only symbols the method uses,
this is the deletion, and no other line changes.

Optional, only if asked.

FIND

```latex
$\alpha$ & Dirichlet concentration, the label-skew parameter \\
```

REPLACE

```latex
```

---

# C. `sections/experiments.tex`, the other half of T14

## C1. Where the moved text lands, around line 32

The Setup subsection already defines the partition, with citations the method
sentence did not carry. Only the reading of small $\alpha$ is new, so only that
clause moves. Pasting the method sentence whole would state the Dirichlet
partition twice on the same page.

It goes between the sentence ending "holds the feature distribution fixed across
clients" and the sentence beginning "Unless stated otherwise there are
$\Nc=10$ clients".

FIND

```latex
skew in the usual taxonomy~\cite{kairouz2021advances} and holds the feature
distribution fixed across clients. Unless stated otherwise there are $\Nc=10$
```

REPLACE

```latex
skew in the usual taxonomy~\cite{kairouz2021advances} and holds the feature
distribution fixed across clients. A smaller $\alpha$ leaves each client a few
dominant classes and almost none of the rest. Unless stated otherwise there are $\Nc=10$
```

---

# D. Sav's "fixes", 17 August 11:19 am. Not in my section

`fixes` appears once in `sections/method.tex`, in the run-in heading
`\paragraph{What the argument fixes, and what it leaves open}` at line 149, and
T25 B2 already deletes that heading. Nothing further is needed in the method.

The comment is almost certainly on `sections/security.tex` line 4. Sav's
comments that morning run in document order, and the 11:19 comment sits
immediately before her 11:20 comment on `\subsection{The Threshold Assumption}`,
which is line 13 of the same file. Line 4 is the only other `fixes` in the
manuscript. T19 also lists this comment under Section IV, so it belongs to
whoever owns `security.tex`.

The one-word repair, if `sec:threshold` stays where it is.

FIND

```latex
This section states what the protocol guarantees. \Cref{sec:threshold} fixes the
threshold assumption. \Cref{sec:ideal} gives an ideal functionality.
```

REPLACE

```latex
This section states what the protocol guarantees. \Cref{sec:threshold} defines the
threshold assumption. \Cref{sec:ideal} gives an ideal functionality.
```

If T17 lands and `sec:threshold` moves into `sec:mhe`, this sentence is deleted
with the move and the repair is moot. Do not paste both.

---

# E. Comments in the method that this list does not answer

None. The five Küpçü comments and the one Sav comment that fall inside
`sections/method.tex` are all covered above. Küpçü's 10:47 am comment on the
unexplained figure is answered by A1 rather than by an edit at the figure, since
the figure is now named at the step it draws.
