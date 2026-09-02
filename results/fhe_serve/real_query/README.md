# real_query — one query answered end to end, against a real trained head

**No real head has been served yet.** VALAR was unreachable on 2026-09-02 (the Koç
VPN was down), and the trained heads live only there, under
`results/personal_adapter/artifacts/`. What is finished is the whole path: the
exporter, the Go serving mode, the two job wrappers, and a mechanism check that
runs the encrypted path start to finish on vectors of the right shape. What is
missing is one `sbatch` on the real artifacts. The two commands are at the bottom.

## What the path does

The rest of `results/fhe_serve/` measures the cryptographic cost on synthetic
vectors: a random head, uniform logits, and whatever top-1/top-2 gap the seed
produced. None of it says the encrypted path answers a real query the way the
plaintext model does. This directory is for that comparison.

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

## Mechanism check, on synthetic vectors — NOT a result

`mechanism_check_synthetic.csv` is the path running end to end on a random head
at the real shape (C=4, d=768) with three random queries, N=3, ring degree 2^15,
scale 2^45, on an Apple-silicon laptop. It exists to show the code works, not to
say anything about the method. **Do not cite it and do not put it in the paper.**

Three of three queries agreed. The index decoded to within 4e-8 of an integer in
every case, including one query whose plaintext margin was 7.1e-4 and whose
scaled margin was 2.6e-4. Head application took about 2.0 s, the encrypted argmax
about 8.2 s and the key switch to the querier about 0.09 s, at 11 collective
refreshes per query.

## To finish it

```sh
# VALAR, once the VPN is up
cd /scratch/hkanpak21/HE_IFD
git fetch origin master && git checkout origin/master -- jobs fhe scripts
sbatch jobs/fhe_export_head.sh ag_news 42          # GPU, minutes
sbatch jobs/fhe_serve_real.sh \
  /scratch/hkanpak21/HE_IFD/results/fhe_serve/real_query/ag_news_s42_A.json
```

The second job is CPU-only and has no `--gres`, so it schedules beside GPU work.
It exits non-zero if any query disagrees. At C=4, N=10 and ring degree 2^15 the
recorded tracked-index cost is about 32 s per query, so sixteen queries is about
nine minutes.

The run writes its CSV to the `.out` log and its JSON to
`<export>_answers.json`. Paste the CSV block into `real_query.csv` here and
replace this section with the count of queries that agreed, out of how many, and
the margin at which any disagreement occurred.
