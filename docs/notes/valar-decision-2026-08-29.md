# The serving re-measurement, and what it decides

Written by `scripts/valar_result.sh`. The branches below were fixed
before the numbers arrived.

Index extraction job: **FAILED**.  Bootstrapping job: **COMPLETED**.

## The argmax index

The method reduces the logits to an argmax index. Both shipped
benchmarks compute the maximum logit instead, so the reported latency
omits the index step and the exactness claim is about the max.

**Not measured, state FAILED.** The report says plainly that the
benchmark computes the maximum and that the reported latency is a lower
bound for the specified circuit. Nothing in the submission changes, and
the honest sentence is already written.

## Server-side bootstrapping

The reported latency was measured with collective refresh. The per-query
traffic prices the bootstrapping-key design the protocol specifies. The
specified design has never been timed.

No `results/fhe_serve/argmax_btp.csv`. The job wrote no CSV.

**Act on it.** Both figures now describe one design. If the new latency
is close to the old, the correction paragraph in Section V collapses to
one sentence. If it is materially slower, the abstract's number is wrong
for the specified protocol and must either change or be labelled, which
is Halil's call. Note the ring degree: the timings are at 2^15 and the
bootstrapping keys at 2^16, so say which was used.

## If both failed

Nothing in either document becomes wrong. Both gaps are already stated in
the report as gaps. The cost of leaving them is one paragraph a reviewer
may probe, not a claim that fails.

