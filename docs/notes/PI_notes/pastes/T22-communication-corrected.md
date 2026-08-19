# Communication, corrected and made precise

Supersedes Part 2 of `T22-T23-cost-comparables.md`, which reasoned from the old
records. The measurement behind it is `results/fhe_serve/comm_grid.json` and
`results/fhe_serve/btp_keys.json`, Slurm job 1583184. Working in
`docs/notes/communication-model-2026-08-20.md`.

**Read this before pasting.** Three numbers in the paper change, and one of them
is in the abstract. The per-query total goes from 5.0 MiB to 13.5 MiB, because
every byte figure was measured on the aggregation chain at ring degree $2^{14}$
while the serving path runs on a fifteen-modulus chain at $2^{15}$. Nothing was
fabricated and nothing was sloppy in the measurement itself. The wrong
configuration was measured.

The correction is not all bad news. The refresh figure the design argument rests
on goes from 510 MiB to 1,615 MiB, so the case for generating bootstrapping keys
gets three times stronger.

---

## C1. `experiments.tex`. Table VII, the whole table

FIND

```latex
\caption{Communication at $\Nc=10$, ring degree $2^{14}$. Share sizes do not
depend on the number of clients, so only the totals scale. The recurring row is the
one that matters for a deployment.}
\label{tab:comm}
\footnotesize
\begin{tabular}{llc}
\toprule
When & Item & Per client \\
\midrule
setup, once & collective public key share & $1.13$\,MiB \\
            & relinearization key share & $27.0$\,MiB \\
            & rotation keys, seven of them & $63.0$\,MiB \\
\midrule
training, once & encrypted head displacement & a few MiB \\
\midrule
per query & encrypted features, uploaded & $2.0$\,MiB \\
          & encrypted label, returned & $0.5$\,MiB \\
          & key-switching shares, ten & $2.5$\,MiB \\
\cmidrule(l){2-3}
          & \textbf{total per query} & $\mathbf{5.0}$\,\textbf{MiB} \\
\bottomrule
\end{tabular}
```

REPLACE

```latex
\caption{Communication at $\Nc=10$, on the fifteen-modulus chain at ring degree
$2^{15}$ that the encrypted argmax requires. Share sizes do not depend on the
number of clients. The per-query total does, because the quorum returns one
key-switching share each, and it does not depend on the number of classes,
because the level restorations are local to the serving party.}
\label{tab:comm}
\footnotesize
\begin{tabular}{llc}
\toprule
When & Item & Per client \\
\midrule
setup, once & collective public key share & $4.25$\,MiB \\
            & relinearization key share & $102.0$\,MiB \\
            & rotation keys, seven of them & $238.0$\,MiB \\
\midrule
training, once & encrypted head displacement & a few MiB \\
\midrule
per query & encrypted features, uploaded & $7.5$\,MiB \\
          & encrypted label, returned & $1.0$\,MiB \\
          & key-switching shares, ten & $5.0$\,MiB \\
\cmidrule(l){2-3}
          & \textbf{total per query} & $\mathbf{13.5}$\,\textbf{MiB} \\
\bottomrule
\end{tabular}
```

---

## C2. `experiments.tex`. The scaling sentence, an insertion

Insert after the table's paragraph, before the sentence beginning "One design
decision governs the recurring figure". Two sentences, and they answer the
question a reader asks next, which is what moves the figure.

```latex
The per-query total is $8.5 + 0.5\Nc$\,MiB, since the quorum returns one
key-switching share each. It is $11.0$\,MiB at $\Nc=5$ and $18.5$\,MiB at
$\Nc=20$, and it is $6.8$\,MiB at ring degree $2^{14}$ and $27.0$\,MiB at
$2^{16}$. It does not vary with the number of classes.
```

---

## C3. `experiments.tex`. The refresh argument, three numbers

FIND

```latex
classes amounts to roughly $510$\,MiB of traffic for a single label. Generating
```

REPLACE

```latex
classes amounts to roughly $1.6$\,GiB of traffic for a single label. Generating
```

FIND

```latex
degree $2^{16}$, generated collectively in $49$\,s. One key generation of
$15.5$\,MiB therefore replaces $510$\,MiB on every subsequent query.
```

REPLACE

```latex
degree $2^{16}$, generated collectively in $51$\,s. One key generation of
$15.5$\,MiB therefore replaces $1.6$\,GiB on every subsequent query.
```

The 1.6 GiB is $34$ refreshes for a hundred classes, times ten clients, times
the $4{,}981{,}181$ byte refresh share on the serving chain. The 15.5 MiB is
exact, $16{,}253{,}192$ bytes, and now has a record where it had none. The 51 s
replaces 49 s because the recorded run took $50.8$ s.

---

## C4. `main.tex`. The abstract

FIND

```latex
$113.2$\,s at a hundred, and $5$\,MiB of traffic.
```

REPLACE

```latex
$113.2$\,s at a hundred, and $13.5$\,MiB of traffic.
```

---

## C5. Optional. The comparison with Hyb-Agg

This is the T22 paste rewritten against the true numbers. It is optional,
because the honest version is less flattering than the earlier draft. My
recommendation is to include it, since a reader who wonders whether 13.5 MiB is
reasonable has nothing else to anchor on, and the reason for the gap is a design
choice we are proud of rather than an inefficiency.

Insert after C2.

```latex
The expansion over plaintext is large. A $768$ dimension feature vector occupies
$6{,}144$ bytes and its ciphertext occupies $7.5$\,MiB, and Hyb-Agg reports a
factor of about twelve for a vector that fills its
ciphertext~\cite{kemmaka2025hybagg}. Two things separate the two figures. The
query fills $768$ of the $16{,}384$ slots the ring provides, and it carries
fifteen moduli rather than the eight an aggregation-only protocol needs, because
the argmax consumes levels. Returning a score vector instead of a label would
remove the second, at the cost \cref{sec:exp-leak} measures.
```

---

## What I did not write, and why

**No batched figure.** Sixteen thousand slots would hold about twenty-one
queries of this width, which would cut the uploaded ciphertext per query to
about $0.36$\,MiB. Whether the tournament argmax can process packed queries
independently is untested, because its rotation structure works across slots.
Claiming the amortized number would be claiming a protocol we have not run.

**No amortized setup figure in the paper.** The $344$\,MiB of key material per
client divided by a query allowance is easy arithmetic and the note records it,
but the allowance is a deployment parameter and putting a number on it in the
paper would invent one.

**The CUDA microbenchmarks in Section 5.4 still have no record and no citation.**
That is a separate defect and this paste does not touch it.
