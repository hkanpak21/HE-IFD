# real_query — one query answered end to end on a real trained head

Every other serving benchmark here runs on synthetic vectors: a random head,
uniform logits, and whatever top-1/top-2 gap the seed produced. None of them say
the encrypted path answers a real query the way the plaintext model does. This is
that comparison. VALAR jobs 1618537 (the export, GPU, 23 s), 1618540 (arrangement
A) and 1618541 (arrangement B), 2026-09-02, both CPU, 11 min each.

**Result: 32 of 32 encrypted answers equal the plaintext answers**, sixteen on
each servable arrangement. There were no disagreements. Record: `real_query.csv`.

| arrangement | queries | agree | gamma | smallest scaled margin | largest index error |
|---|---|---|---|---|---|
| A, shared head on the bare backbone | 16 | 16 | 0.18076980 | 0.006771 | 4.3e-08 |
| B, shared head over client 0's adapter | 16 | 16 | 0.08636835 | 0.046024 | 3.2e-08 |

Configuration: AG-News seed 42, the recorded artifact `ag_news_s42.pt`
(roberta-base, N=10, alpha=0.1, K=200), four classes, feature dimension 768, ten
parties, ring degree 2^15, plaintext scale 2^45, sixteen test examples drawn at
random per arrangement.

Two of arrangement A's sixteen are queries the head itself gets wrong, and the
encrypted path reproduces those errors. That is the correct behaviour: the
protocol is faithful to the plaintext computation, not to the ground truth.
Arrangement B answers class 2 on thirteen of its sixteen and gets half right,
which is a property of client 0's adapter on a Dirichlet shard at alpha=0.1 and
not a property of the encryption. Read `plaintext_label` against `true_label` for
accuracy, and `encrypted_label` against `plaintext_label` for what this measures.

## What the path does

`jobs/fhe_export_head.py` rebuilds the served head (W, b) from a recorded
artifact with `head_of`, computes real test features under the same frozen
backbone with `features_of`, and writes W, b, the features, the plaintext logits
and the plaintext argmax to JSON. Computing features needs the backbone, so it is
a GPU job.

`fhe/serve_real.go` (`-serve-real`) reads that file and serves it. The client
encrypts `[phi(x) | 1]` under the collective public key. The serving party
applies the encrypted head ciphertext-by-ciphertext, one product and one
rotate-and-sum per class, gathering the C logits into the first C slots of one
ciphertext. The argmax index is computed under encryption by the tracked
tournament of `serve_index.go`. A quorum key-switches that index to the querier's
public key, and the querier alone decrypts it. Nothing else is decrypted: no
logit, no score and no maximum value leaves the ciphertext domain. The plaintext
label the encrypted answer is compared against comes from the export, computed in
float64 by numpy.

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
the integer. That is tighter than any gap in `argmax_index.csv`, whose smallest
was 0.006242.

It does not establish where the circuit fails, because nothing failed. The
resolution limit is bounded from below by 0.006771 and is not bounded from above
by this run.

**The timing is not the paper's headline.** Per query, mean over sixteen at N=10:
head application 5.5 s, argmax 34.4 s at eleven collective refreshes, key switch
to the querier 0.59 s, 40.7 s in total. This run restores levels by collective
refresh, and the paper specifies server-side bootstrapping, so 40.7 s is the cost
of the mechanism this run used and not of the one Table V reports. What carries
across mechanisms is the agreement, because that is a statement about the circuit
rather than about how its levels are restored.

## Reproducing

```sh
cd /scratch/hkanpak21/HE_IFD
git fetch origin master && git checkout origin/master -- jobs fhe scripts
sbatch jobs/fhe_export_head.sh ag_news 42          # GPU
sbatch jobs/fhe_serve_real.sh \
  results/fhe_serve/real_query/ag_news_s42_A.json  # CPU, no --gres
```

The serving job exits non-zero if any query disagrees. The exports are not
committed: each is about 0.34 MB of float64 features and regenerates from the
artifact in under a minute. They live on VALAR under
`results/fhe_serve/real_query/`, together with the answer JSONs.
