# Table III now has a record, and it reproduces

The audit of 2026-08-20 found that five cells of Table III traced to nothing
under `results/`. They have now been run. Slurm jobs 1583443 to 1583447 on the
`ai` partition, five configurations at once on A40s, 27 minutes wall clock.
Record: `results/personal_adapter/sensitivity.csv`, 99 rows.

## The finding

**The numbers were real. They had no record, which is a different problem from
being wrong.** Four of the five reproduce to within 0.002.

| cell | paper prints | measured now | difference |
|---|---|---|---|
| skew, $\alpha=0.05$ | 0.812 | 0.8144 | $+0.002$ |
| skew, $\alpha=0.30$ | 0.914 | 0.9150 | $+0.001$ |
| skew, $\alpha=1.00$ | 0.971 | 0.9698 | $-0.001$ |
| local steps, $K=100$ | 0.718 | 0.7098 | $-0.008$ |
| local steps, $K=400$ | 0.870 | 0.8706 | $+0.001$ |

The quantity is the three-seed mean of mode `sel_gp_rarefill` for the skew row
and the seed 42 value for the local-steps row, which is what the caption already
says. The two default cells were not re-run, because $\alpha=0.10$ already
traces to `results/personal_adapter/stratified/results.csv` and $K=200$ to
`results/personal_adapter/nsweep.csv`.

$K=100$ is the one cell that moved by more than 0.002. It is a single seed and
the training is not deterministic on GPU, so 0.008 is ordinary run-to-run
variance. It is not evidence of an error in the original number.

## The change

Print what the record says, so that the table and the record agree exactly.

FIND

```latex
selected arrangement & $0.812$ & $0.789$ & $0.914$ & $0.971$ \\
```

REPLACE

```latex
selected arrangement & $0.814$ & $0.789$ & $0.915$ & $0.970$ \\
```

FIND

```latex
selected arrangement & $0.718$ & $0.803$ & $0.870$ & \\
```

REPLACE

```latex
selected arrangement & $0.710$ & $0.803$ & $0.871$ & \\
```

## One sentence for the caption, optional

The caption already states the seed counts correctly. If the PIs want the
provenance visible, this goes at the end of it.

```latex
The skew and local-step cells come from
\texttt{results/personal\_adapter/sensitivity.csv}.
```

I recommend against it. No other caption in the paper names a file, and one
name in one caption reads as an apology.

## What this closes

The audit listed Table III as the paper's only place printing numbers that trace
to nothing, and said the honest alternative was to delete two rows and lose the
coverage-crossover argument. That is no longer necessary. The rows stay, the
argument stays, and the record exists.
