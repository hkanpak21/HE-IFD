# real_query — one query answered end to end, against a real trained head

**Thirty-two queries out of thirty-two agree.** The label the querier decrypts
after the encrypted serving path is the label the plaintext head gives, on every
query of both servable arrangements, at ring degree 2^15 and scale 2^45 with a
ten-party quorum. There were no disagreements. Data in `real_query.csv`.

VALAR jobs, 2026-09-02: **1618537** wrote the exports (GPU, 23 s), **1618540**
answered arrangement A and **1618541** arrangement B (CPU, 11 min each, on the
`ai` partition).

| arrangement | queries | agree | gamma | smallest scaled margin | largest index error |
|---|---|---|---|---|---|
| A, shared head on the bare backbone | 16 | 16 | 0.18076980 | 0.006771 | 4.3e-08 |
| B, shared head over client 0's adapter | 16 | 16 | 0.08636835 | 0.046024 | 3.2e-08 |

Both read the recorded artifact `ag_news_s42.pt` (roberta-base, N=10, alpha=0.1,
K=200, C=4, d=768), sixteen test examples drawn at random per arrangement.

Per query, at N=10: about 5.5 s to apply the encrypted head, about 34 s for the
encrypted argmax at 11 collective refreshes, and about 0.6 s to key-switch the
label to the querier. Forty seconds in total, which is the tracked-index cost of
`argmax_index.csv` plus the head application the earlier benchmarks omitted.

## What the path does

The rest of `results/fhe_serve/` measures the cryptographic cost on synthetic
vectors: a random head, uniform logits, and whatever top-1/top-2 gap the seed
produced. None of it says the encrypted path answers a real query the way the
plaintext model does. This directory is that comparison.

1. `jobs/fhe_export_head.py` rebuilds the served head (W, b) from a recorded
   artifact with `head_of`, computes real test features under the same frozen
   backbone with `features_of`, and writes W, b, the features, the plaintext
   logits and the plaintext argmax to JSON. Computing features needs the
   backbone, so it is a GPU job.
2. `fhe/serve_real.go` (`-serve-real`) reads that file and runs the serving path.
   The client encrypts `[phi(x) | 1]` under the collective public key. The
   serving party applies the encrypted head ciphertext-by-ciphertext, one product
   and one rotate-and-sum per class, gathering the C logits into the first C
   slots of one ciphertext. The argmax index is computed under encryption by the
   tracked tournament of `serve_index.go`, its bootstraps served by collective
   refreshes. A quorum key-switches that index to the querier's public key, and
   the querier alone decrypts it.

Nothing else is decrypted. No logit, no score and no maximum value leaves the
ciphertext domain. The plaintext label the encrypted answer is compared against
comes from the export, computed in float64 by numpy.

## Two public constants, both reported

**The bias rides in homogeneous coordinates.** The head row is `[W_c | b_c]` and
the query is `[phi(x) | 1]`, so the bias costs no second ciphertext.

**The logits are scaled by a public gamma.** The sign circuit is a minimax
approximation on [-1,1], so the logits have to be mapped into that interval. The
argmax is invariant under multiplication by a positive constant, so gamma cannot
change which label is correct. What it does change is the margin the circuit has
to resolve, since gamma multiplies the top-1/top-2 gap as well. gamma is fixed
once, before the run, as `0.4 / max|logit|` over the export, and it is printed on
every row. It is never tuned per query. Setting it in a deployment needs a public
bound on the head norm, which this benchmark takes from the export instead; that
is the one place where the benchmark knows something the serving party would not.

## What the run does and does not establish

It establishes that the circuit resolved every margin it was given. The hardest
case was arrangement A on test example 3257: a plaintext top-1/top-2 gap of
0.037456, which gamma takes to 0.006771, decoded to an index within 3.0e-08 of
the integer. That is tighter than any gap in the synthetic index runs of
`argmax_index.csv`, whose smallest was 0.006242.

It does not establish where the circuit fails, because nothing failed. The
resolution limit is bounded from below by 0.006771 and is not bounded from above
by this run.

The encrypted answers say nothing about accuracy. Arrangement B answers class 2
on thirteen of its sixteen queries and gets half of them right, which is a
plaintext property of client 0's adapter on a Dirichlet shard at alpha=0.1, not a
property of the encryption. Read `plaintext_label` against `true_label` for that,
and `encrypted_label` against `plaintext_label` for what this directory measures.

## Reproducing

```sh
cd /scratch/hkanpak21/HE_IFD
git fetch origin master && git checkout origin/master -- jobs fhe scripts
sbatch jobs/fhe_export_head.sh ag_news 42          # GPU
sbatch jobs/fhe_serve_real.sh \
  /scratch/hkanpak21/HE_IFD/results/fhe_serve/real_query/ag_news_s42_A.json
```

The second job is CPU-only and has no `--gres`, so it schedules beside GPU work.
It exits non-zero if any query disagrees. The exports themselves are not
committed: each is about 0.34 MB of float64 features and regenerates from the
artifact in under a minute.

`mechanism_check_synthetic.csv` is the same path on a random head at the real
shape, run on a laptop before the artifacts were reachable. It is a code check,
not a result. Do not cite it.
