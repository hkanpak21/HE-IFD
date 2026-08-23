# T31. Factual corrections in the experiments section. Find and replace list

Answers items 1 to 4 and 6 of the correction brief of 2026-08-20, which came from
the audit in `docs/notes/experiments-assessment-2026-08-20.md`. Item 5 of that
brief moved `docs/PI_comments_on_2026-08-19.md` to
`docs/notes/PI_notes/PI_notes_2026-08-19.md` and is not part of this list.

Nothing here is applied to `docs/paper/`. Every entry gives the file, the
approximate line, the current text verbatim, and the replacement. Paste in file
order. Every number below was recomputed from the record named beside it. No
number was copied from the audit on trust, and the audit was wrong in two places,
recorded under "Corrections to the audit".

Only `sections/experiments.tex` is touched. Eleven edits. Ten are a word, a
number or a clause. One is a deletion, which is item T20 of the TODO.

## Counts

| what | count |
|---|---|
| wrong numbers corrected | 5 |
| claims requalified, no number changed | 2 |
| undisclosed methodology stated | 2 |
| tables deleted | 1 |
| net line change in the section | minus 20, from 710 to 690 |

## Records used

| quantity | record |
|---|---|
| Table V cells and regret | `results/personal_adapter/stratified/results.csv`, `results/personal_adapter_vision/stratified/results.csv` |
| effective federation size | the `n` column of the same two files |
| subsample sizes | `jobs/finetune_improve.py:100`, `jobs/vision_matched.py:62`, confirmed against the accuracy denominators in the two stratified files |
| naive argmax at a hundred classes | `results/fhe_serve/argmax_cost.csv` |
| query allowance | `results/extraction_budget/results.csv` |
| Table VI rows | `results/fhe_serve/cost_grid.json`, `results/fhe_serve/protocol_cost.json`, `results/fhe_serve/argmax_tournament.csv` |

---

# A. Table V is arithmetically wrong

## The recomputation

Each of the fifteen cells has a shared-head accuracy in the `A_headonly` row and a
personal-adapter accuracy in the `B_personal` row. The `sel_federated` and
`sel_fed_balanced` notes record which one the rule picked. Both rules pick the
personal adapter in all fifteen cells, and the personal adapter is genuinely
better in seven of them.

| task | seeds where the personal adapter wins |
|---|---|
| AG-News | seed 44 only, $0.4614$ against $0.4018$ |
| TREC | none |
| DBpedia | none |
| Banking77 | all three |
| CIFAR-100 | all three |

That is $7/15$, not $6/15$. The two rules pick identically in every cell, so both
rows carry the same pair of numbers.

## The regret definition

The definition that reproduces the two printed estimator rows exactly is the sum
over the five tasks of the per-task mean over three seeds of $\max(A,B)$ minus the
accuracy of the arrangement the rule selected. Under it:

| rule | correct | regret |
|---|---|---|
| `sel_federated` | 7/15 | 0.4027 |
| `sel_fed_balanced` | 7/15 | 0.4027 |
| `sel_globalprior` | 12/15 | 0.0268 |
| `sel_gp_rarefill` | 13/15 | 0.0186 |

The last two round to the printed $0.027$ and $0.019$, so the definition is
confirmed. The printed $0.383$ matches no rule in the record. The nearest is
`sel_perclient`, the per-client vote, at $0.3788$, so $0.383$ was most likely
transcribed from a third rule that the table does not report.

The audit's claim that the caption calls a sum an average is correct. The printed
quantity is a sum over the five tasks of a per-seed mean. A true average over
tasks would print $0.081$, $0.081$, $0.005$ and $0.004$.

## A1. Table V, both baseline rows, around line 309

FIND

```latex
majority of held-out accuracies      & 6/15 & 0.383 \\
same, class-balanced within a client & 6/15 & 0.383 \\
```

REPLACE

```latex
majority of held-out accuracies      & 7/15 & 0.403 \\
same, class-balanced within a client & 7/15 & 0.403 \\
```

## A2. Table V caption, around line 300

The regret column is a sum over the five tasks, not an average over them.

FIND

```latex
\caption{Choosing between the two servable arrangements without decrypting either.
Cells are counted over five tasks and three seeds. Regret is the accuracy given up
by a wrong choice, averaged over tasks.}
```

REPLACE

```latex
\caption{Choosing between the two servable arrangements without decrypting either.
Cells are counted over five tasks and three seeds. Regret is the accuracy given up
by a wrong choice, averaged over seeds and summed over the five tasks.}
```

The prose above the table needs no change. It says the baseline "selects the
personal adapter every time", which the record confirms, and it does not print
$6/15$ anywhere.

---

# B. The subsampling is not disclosed

## The call chain, verified

`jobs/personal_adapter_test.py:236` calls `fi._data(task, BACKBONE, seed)`.
`_data` at `jobs/finetune_improve.py:329` calls `load_text(task, seed=seed)` with
no size overrides, and `load_text` at `jobs/finetune_improve.py:100` defaults to
`max_train=20000, max_test=5000`. Its `take` helper clamps with
`n = min(n, len(split))`, so a split smaller than the cap is used whole.

`jobs/personal_adapter_vision.py:209` calls `vm.load_vision(ds, seed=seed)`.
`load_vision` at `jobs/vision_matched.py:62` defaults to
`max_train=10000, max_test=2000`, with the same clamp.

## The sizes actually used

The test denominators were confirmed against the record. For each candidate size
$n$, every accuracy in the `A_headonly`, `current`, `B_personal` and `local` rows
of the two stratified files was checked for consistency with some integer count
over $n$ at four decimal places. AG-News admits $5{,}000$ and rejects $7{,}600$.
Banking77 admits $3{,}080$ and rejects $5{,}000$. The rest are consistent with the
cap.

| task | training used | test used | full train | full test | cut |
|---|---|---|---|---|---|
| AG-News | 20,000 | 5,000 | 120,000 | 7,600 | both |
| TREC | 5,452 | 500 | 5,452 | 500 | neither |
| DBpedia | 20,000 | 5,000 | 560,000 | 70,000 | both |
| Banking77 | 10,003 | 3,080 | 10,003 | 3,080 | neither |
| CIFAR-100 | 10,000 | 2,000 | 50,000 | 10,000 | both |
| CIFAR-10, Table IV | 10,000 | 2,000 | 50,000 | 10,000 | both |

The training figure is the pool before the Dirichlet partition and before each
client carves a tenth of its shard into a holdout. At $\Nc=10$ on AG-News a client
therefore holds about $2{,}000$ examples.

One caveat on that table. The two columns headed "used" come from the code and, for
the test split, from the check above. The two headed "full" are the published sizes
of the corpora, because no dataset cache exists on the machine this was checked on.
Only Banking77 is settled by the record alone, where the check rejects $5{,}000$ and
admits $3{,}080$. TREC rests on the published $5{,}452$ and $500$, both far below the
caps.

TREC and Banking77 are used whole on both splits, so the sentence must not claim
they are subsampled. "At most" carries that, and the second sentence names them.

## B1. Setup, around line 26

FIND

```latex
$77$, using a frozen RoBERTa-base encoder~\cite{liu2019roberta}, and on CIFAR-100
with a frozen ViT-B/16~\cite{dosovitskiy2021vit}. Data are partitioned across
```

REPLACE

```latex
$77$, using a frozen RoBERTa-base encoder~\cite{liu2019roberta}, and on CIFAR-100
with a frozen ViT-B/16~\cite{dosovitskiy2021vit}. Each text task draws at most
$20{,}000$ training and $5{,}000$ test examples under the seed, and each vision
task at most $10{,}000$ and $2{,}000$. Only TREC and Banking77 fall below these
caps and are used whole. Data are partitioned across
```

Two sentences, thirty-six words. It states the cap rather than six pairs of
numbers, which is shorter and covers Table II and Table IV at once, and it says
that the draw is keyed to the seed, which is the fact a reviewer needs in order to
read the three-seed spread correctly.

---

# C. Two cells ran with fewer clients than the caption states

## Confirmed from the record

`MIN_SHARD = 20` at `jobs/personal_adapter_test.py:83` drops any client whose
Dirichlet shard holds fewer than twenty examples. The `n` column of
`results/personal_adapter/stratified/results.csv` reads $7$ for AG-News seed 44
and $9$ for TREC seed 44 on every multi-client row. Every other cell in both
stratified files reads $10$. Both affected cells are seed 44.

AG-News seed 44 is also the cell whose shared head reads $0.402$, which the
selection subsection calls "an unlucky partition". The two statements describe the
same event, so C1 discloses it and C2 names it.

## C1. Table II caption, around line 69

FIND

```latex
the threat model of \cref{sec:threat}. We did not run the pooled reference on
CIFAR-100.}
```

REPLACE

```latex
the threat model of \cref{sec:threat}. We did not run the pooled reference on
CIFAR-100. On one seed the Dirichlet draw assigns fewer than twenty samples to some
clients, which cannot train, so the effective federation is seven on AG-News and
nine on TREC.}
```

The wording copies the disclosure the paper already makes for Table IV at
$\Nc=20$ and $\alpha=0.04$, so the two read the same way.

## C2. The unlucky partition sentence, around line 320

FIND

```latex
On the AG-News seed where an unlucky partition
leaves the shared head at $0.402$ and the personal adapter genuinely better, it
```

REPLACE

```latex
On the AG-News seed where the partition drops three
clients and leaves the shared head at $0.402$ and the personal adapter genuinely
better, it
```

This replaces a judgement with the mechanism, and it matches C1. Note that T25
item A9 edits the two lines above this anchor. The anchor still matches after
T25 is pasted, because A9's replacement keeps the line break before "On the
AG-News seed".

---

# D. Smaller mismatches

## D1. The naive argmax at a hundred classes, around line 417

Real. `results/fhe_serve/argmax_cost.csv` gives $1{,}587{,}433.7$\,ms at $C=100$,
which is $26.5$ minutes. The $20.4$ minute figure in that file is the $C=77$ row
at $1{,}225{,}902.9$\,ms. The paper's own arithmetic already disagrees with its
own word, since $16$\,s times $99$ comparisons is $26.4$ minutes.

FIND

```latex
$16$\,s per comparison, which is roughly twenty minutes at a hundred classes.
```

REPLACE

```latex
$16$\,s per comparison, which is roughly twenty-six minutes at a hundred classes.
```

The fourteenfold reduction quoted two lines later is right, at
$1{,}587{,}433.7$ over $112{,}969.6$ equal to $14.05$, and "under two minutes"
is right at $1.88$ minutes. Neither changes.

## D2. The query allowance on AG-News, around line 594

Real. The three-seed, two-arrangement mean of the `random` strategy in
`results/extraction_budget/results.csv` crosses fidelity $0.90$ between the
$10{,}000$ point at $0.8892$ and the $20{,}000$ point at $0.9360$, at about
$1.2\times10^4$, which is what the paragraph above already prints. Divided by nine
that is $1.3\times10^3$. The printed $1.4\times10^3$ is looser than the record
supports and contradicts the paper's own $1.2\times10^4$.

FIND

```latex
$\Nc=10$ requires $Q$ below roughly $1.4\times10^3$ per client on AG-News and
```

REPLACE

```latex
$\Nc=10$ requires $Q$ below roughly $1.3\times10^3$ per client on AG-News and
```

The Banking77 figure is right. The curve crosses $0.90$ at $2.0\times10^5$ and
$2.0\times10^5$ over nine is $2.2\times10^4$.

## D3. The optimism of the local holdout, around line 282

Real, and smaller than printed. The held-out measurement of the personal
arrangement is the `B=` value in the `sel_federated` note, and its true global
accuracy is the `B_personal` row. The mean difference over the fifteen cells is
$0.2848$, which rounds to $0.28$, not $0.29$. The range runs from $0.0199$ on
CIFAR-100 seed 42 to $0.5715$ on TREC seed 43.

FIND

```latex
accuracy exceeds its true global accuracy by $0.29$ on average. A client's
```

REPLACE

```latex
accuracy exceeds its true global accuracy by $0.28$ on average. A client's
```

## D4. "To within 0.02" reads as a bound and is a mean, around line 278

Real. The same comparison for the shared arrangement gives a mean absolute error
of $0.0194$ over the fifteen cells and a worst cell of $0.1148$, on TREC seed 44.
The sentence two lines below it says "on average" and is correct, so only this one
moves.

FIND

```latex
held-out measurements estimate its accuracy on the global distribution to within
$0.02$. The personal arrangement is $\Nc$ different models, and client $j$'s
```

REPLACE

```latex
held-out measurements estimate its accuracy on the global distribution to within
$0.02$ on average. The personal arrangement is $\Nc$ different models, and client $j$'s
```

The estimator's own calibration sentence, "within $0.019$ on average", is right.
Recomputed from the `E_A=` values of the `sel_gp_rarefill` notes against the
`A_headonly` rows, the mean is $0.0185$ and the worst cell is $0.1227$. It already
says "on average", so it stays.

---

# E. Table VI becomes a deletion

Item T20. Recommendation: delete it. The figure carries it.

## What each carries

`docs/paper/figures/make_cost_fig.py` draws `fig:cost` from
`results/fhe_serve/cost_grid.json` alone. Its left panel plots the
ciphertext-by-ciphertext product, the rotation, the plaintext-by-ciphertext
product and the addition at $\Nc=10$ over ring degrees $2^{14}$, $2^{15}$ and
$2^{16}$. Its right panel plots the key switch for $\Nc=5$, $10$ and $20$ over the
same degrees. Every bar is annotated with its value, and the label formatter
prints exactly the strings the table prints.

| Table VI row | in the figure | otherwise in the text |
|---|---|---|
| head applied to an encrypted query, 39.0 ms | yes | "Cost of query encryption" and "Hardware acceleration" |
| head applied to a plaintext query, 5.4 ms | yes | "Cost of query encryption" |
| ciphertext addition, 0.7 ms | yes | nowhere |
| rotation, 33.1 ms | yes | "Hardware acceleration" |
| selection mask and accumulate, 1.1 ms | no | nowhere, but it is inside the $0.24$\,s the end-to-end paragraph states |
| key switch to the querier, 198 ms | yes | the prose gives its span, $103$\,ms to $1.73$\,s |
| encrypted argmax, $C=4$, 31.2 s | caption | "What one query costs" |
| encrypted argmax, $C=100$, 113.0 s | caption | "What one query costs" |
| reciprocal, 4.21 s | no | "The encrypted reciprocal", with $3.16$ and $6.30$\,s beside it |

One measured number leaves the paper, the selection mask at $1.1$\,ms. It is a
component of the $0.24$\,s of arithmetic and key switch that the end-to-end
paragraph already states, so no claim loses its support.

## What the deletion also fixes

The audit's M7 and M8 are both real, and both are properties of the table alone.

M7, two runs mixed. Six rows come from `results/fhe_serve/cost_grid.json` at
$\Nc=10$ and $\log N=14$, which reads $39.0123$, $5.38215$, $0.71105$, $33.1246$,
$1.1495$ and $197.663$\,ms. The reciprocal row comes from
`results/fhe_serve/protocol_cost.json`, because `cost_grid.json` records
`encrypted_reciprocal_ms` as $0$ in all nine of its entries. The two runs disagree
on what they share. `protocol_cost.json` reads $35.0177$\,ms for the product
against $39.0123$, which is $11.4$ per cent, and $181.094$\,ms for the key switch
against $197.663$, which is $9.1$ per cent. `CLAUDE.md` already warns that these
two single-run measurements do not agree, and its source-of-truth table maps
Table VI to `cost_grid.json` alone. Deleting the table leaves the two runs in
separate paragraphs, each reporting one thing, which is the honest arrangement
until one run measures both.

M8, the caption's ring degree. The caption says $2^{14}$. The two argmax rows were
measured at $\log N=15$, per `results/fhe_serve/argmax_tournament.csv`. The prose
above the table already discloses the deeper chain, so deleting the caption
removes the contradiction without adding a word.

## E1. Delete the table, around line 350

FIND

```latex
\begin{table}[t]
\centering
\caption{Per-operation cost at the default setting, $\Nc=10$ and ring degree
$2^{14}$. The first two rows are the same operation with the query encrypted and
left in plaintext, which is what encrypting the query costs. One query at four
classes takes $31.5$\,s in total and one query at a hundred classes takes
$113.2$\,s. The argmax is more than $99$ per cent of both.}
\label{tab:cost}
\footnotesize
\begin{tabular}{lc}
\toprule
Operation & cost \\
\midrule
head applied to an encrypted query & $39.0$\,ms \\
head applied to a plaintext query & $5.4$\,ms \\
ciphertext addition & $0.7$\,ms \\
rotation & $33.1$\,ms \\
selection mask and accumulate & $1.1$\,ms \\
key switch to the querier & $198$\,ms \\
\midrule
encrypted argmax, $\Cc=4$ & $31.2$\,s \\
encrypted argmax, $\Cc=100$ & $113.0$\,s \\
reciprocal under encryption, once per aggregation & $4.21$\,s \\
\bottomrule
\end{tabular}
\end{table}

\paragraph{Cost of query encryption} Applying the head to an encrypted
```

REPLACE

```latex
\paragraph{Cost of query encryption} Applying the head to an encrypted
```

## E2. The figure caption, which is the only cross-reference to the table, around line 451

FIND

```latex
four classes and $113$\,s at a hundred, and \cref{tab:cost} states the total.}
```

REPLACE

```latex
four classes and $113$\,s at a hundred, so one query totals $31.5$\,s and
$113.2$\,s, of which the argmax is more than $99$ per cent.}
```

The totals move into the figure caption, which is where the reader now needs them.
Both were recomputed. The tournament argmax at $C=4$ is $31{,}243.5$\,ms and at
$C=100$ is $112{,}969.6$\,ms, and the arithmetic and key switch add $238.5$\,ms,
giving $31.5$ and $113.2$\,s and shares of $99.2$ and $99.8$ per cent.

---

# F. Corrections to the audit

Two statements in `docs/notes/experiments-assessment-2026-08-20.md` did not
survive recomputation.

1. M8 says "the three argmax rows and the reciprocal row were measured at
   $\log N=15$". Table VI has two argmax rows, not three, and the reciprocal was
   measured at $\log N=14$. Every entry of `results/fhe_serve/protocol_cost.json`
   carries `"log_n": 14`, and the $4.21$\,s figure is its $\Nc=10$ entry. Only the
   two argmax rows sit at $2^{15}$.
2. M1 says the record gives $0.403$ for both baseline rows. It does, but only under
   a definition M1 states later in the same entry. The definition is recorded above
   as part of A2 so that the caption and the column agree.

---

# G. Sites checked and left alone

| site | why it stays |
|---|---|
| Table II, all nineteen filled cells | every one reproduces to the printed precision from the two stratified files and `results/centralised_ceiling/results.csv` |
| "the personal adapter is $0.17$ and $0.18$ worse" | the three-seed means give $0.170$ on AG-News and $0.178$ on TREC |
| "selects the personal adapter every time" | all fifteen `sel_federated` notes read "federation picked B" |
| $12/15$ and $13/15$ | correct under the same recomputation that gives $7/15$ |
| "within $0.019$ on average" | $0.0185$, and it already says on average |
| "a fourteenfold reduction" and "under two minutes" | $14.05$ and $1.88$ minutes |
| "more than $99$ per cent" | $99.2$ per cent at $C=4$ and $99.8$ at $C=100$ |
| Banking77 allowance $2.2\times10^4$ | $2.0\times10^5$ over nine |
| "margins of $0.13$ to $0.24$" | the zero-fill margins in the notes are $0.1296$, $0.1790$ and $0.2368$. The rare-class fill gives $0.4554$ to $0.5347$, and the paper does not say which variant it quotes, so the sentence is true as written and only ambiguous |
| Table IV, all twenty-four cells | recomputed as three-seed means from `results/personal_adapter_vision/cifar10_matched.csv`, giving $0.384$, $0.948$, $0.962$, $0.013$, then $0.569$, $0.950$, $0.964$, $0.014$, then $0.212$, $0.948$, $0.943$, $-0.005$, then $0.399$, $0.952$, $0.959$, $0.007$ |
| Table VII, every row | every cell recomputes from `results/fhe_serve/comm_cost.json` at $\Nc=10$, giving $1.13$, $27.0$, $63.0$, $2.0$, $0.5$, $2.5$ and a total of $5.0$\,MiB, and the $510$\,MiB alternative is $34$ refreshes times ten clients times $1{,}573{,}253$ bytes. That record measured the aggregation chain, not the serving chain, and `pastes/T22-communication-corrected.md` replaces the whole table from `results/fhe_serve/comm_grid.json`. T31 proposes nothing on it |

---

# H. Paste order and one collision

Paste in file order: B1, C1, D4, D3, A2, A1, C2, D1, E1, E2, D2.

One ordering constraint and one warning.

- C2 overlaps the two lines that T25 item A9 edits. Paste T25 first, or paste C2
  first and then take A9's anchor from the edited file. The C2 anchor is written so
  that it matches in either order.
- B1 sits on the sentence that T14 moves into the setup subsection. If T14 lands
  first, its insertion point is the same paragraph. Paste B1 before T14, or check
  the anchor after T14 lands.

`pastes/T22-communication-corrected.md` also edits this file, at Table VII and the
two paragraphs under it. Its anchors were checked against these eleven and none of
them overlap, so the two lists can be pasted in either order.

---

# I. What this list does not fix

The audit raises seven further defects in this section that need either a run or a
decision the PIs must make, and none of them is a find and replace. They are M4,
the two rows of Table III with no record, M5 and M6, three numbers in Section 5.4
with no record, M11, the two key-switching traffic figures that differ by a factor
of eight, and U4 to U16. They stay in the assessment note.
