# The communication cost of serving, measured and modelled

2026-08-20. Records: `results/fhe_serve/comm_grid.json` and
`results/fhe_serve/btp_keys.json`, both written by `jobs/fhe_comm_grid.sh`,
Slurm job 1583184, 63 seconds on the `ai` partition.

## Why the paper's figure was wrong

`runCommCost` called `measureComm(n, 14)` with the ring degree written into the
call, so the `-logn` flag never reached it. It also used the aggregation chain,
which carries eight moduli. That chain is right for the head merge, which is
depth one.

The serving path is not the head merge. `runTournament` builds a chain of
fifteen moduli at ring degree $2^{15}$, because the argmax needs the depth. A
query ciphertext lives in that chain, not in the aggregation chain.

So every byte figure in the paper was a real measurement of a configuration the
protocol does not serve in.

## The model

Per-query traffic has three terms and no others.

```
per query = ct_full + ct_low + N x ks_low
```

- `ct_full`, the query ciphertext the client uploads, at full level because it
  must survive the argmax.
- `ct_low`, the label ciphertext returned, near the bottom of the chain.
- `ks_low`, one key-switching share per client, at the same low level, and the
  quorum needs N of them.

Two properties fall out, and both are worth stating in the paper.

**Per-query traffic does not depend on the number of classes.** The argmax
refreshes are local to the serving party, because the bootstrapping keys were
generated once. A four-class query and a hundred-class query cost the same
bytes. Only time differs.

**Per-query traffic is linear in the number of clients, with a large constant.**
At the serving parameters,

```
per query (MiB) = 8.50 + 0.50 N
```

## Measured, at every configuration

Per-query traffic, MiB.

| ring | chain | N=5 | N=10 | N=20 |
|---|---|---|---|---|
| $2^{14}$ | aggregation | 3.75 | **5.00** | 7.50 |
| $2^{14}$ | serving | 5.50 | 6.75 | 9.25 |
| $2^{15}$ | aggregation | 7.50 | 10.00 | 15.00 |
| $2^{15}$ | serving | 11.00 | **13.50** | 18.50 |
| $2^{16}$ | aggregation | 15.00 | 20.00 | 30.00 |
| $2^{16}$ | serving | 22.00 | 27.00 | 37.00 |

The first bold cell is what the paper prints. The second is what the protocol
runs. **The per-query total is 13.5 MiB, not 5.0 MiB.**

Setup, once, per client, with seven rotation keys.

| ring | chain | public key | relinearization | rotations | total |
|---|---|---|---|---|---|
| $2^{14}$ | aggregation | 1.13 | 27.0 | 63.0 | **91.1** |
| $2^{15}$ | serving | 4.25 | 102.0 | 238.0 | **344.3** |

## What this does to the paper's argument

It strengthens it. The paper justifies generating bootstrapping keys by saying
one key generation of 15.5 MiB replaces 510 MiB of refresh traffic per query.
At the parameters that actually run, the refresh alternative costs

```
34 refreshes x 10 clients x 4,981,181 B = 1,615 MiB
```

So 15.5 MiB replaces 1.6 GiB, not 510 MiB. The design decision is a hundredfold
saving rather than a thirtyfold one.

The bootstrapping key figure itself is confirmed and now has a record.
16,253,192 bytes is 15.50 MiB, exactly what the paper prints. Generation took
50.8 s against the 49 s printed, which is single-run variance on an unrecorded
run. The paper should say 51 s, or round to about 50.

## Expansion over plaintext

The feature vector is 768 doubles, 6,144 bytes.

| quantity | bytes | expansion |
|---|---|---|
| uploaded query ciphertext | 7,864,862 | 1,280x |
| whole query, N=10 | 14,156,892 | 2,304x |

Hyb-Agg reports about 12x, measured on a vector that fills its ciphertext, and
about 24x near dimension 4,095 where unused slots start to dominate.

Two things separate us from their 12x and both should be said plainly.

**Slot occupancy.** At ring degree $2^{15}$ there are 16,384 slots and the query
fills 768 of them, 4.7 per cent. A vector that filled the ring would expand by
about 60x rather than 1,280x.

**Chain depth.** Even filled, we would not reach 12x, because the query must
carry fifteen moduli to survive the argmax while an aggregation-only protocol
carries eight or fewer. Depth costs bytes. That is the honest reason our figure
is larger, and it is a consequence of computing the argmax under encryption
rather than returning a score vector.

**Batching is not measured.** Sixteen thousand slots would hold about twenty-one
768-dimension queries. Whether the tournament argmax can process packed queries
independently is untested, because its rotation structure operates across slots.
Do not claim the amortized figure.

## Scenarios worth putting in the paper

1. **Default, N=10, any class count.** 13.5 MiB per query. Independent of C.
2. **Federation size.** 11.0 MiB at N=5, 18.5 MiB at N=20. Linear in N because
   the quorum sends one key-switching share each.
3. **Security parameter.** 6.75 MiB at $2^{14}$, 13.5 at $2^{15}$, 27.0 at
   $2^{16}$. The serving chain doubles with the ring degree.
4. **Setup amortized.** 344 MiB of key material per client, once. Over a query
   allowance of 1,000 that is 0.34 MiB per query, which is small against 13.5.
   Over 10 queries it dominates.
5. **The refresh alternative.** 1,615 MiB per query at a hundred classes, which
   is what the bootstrapping keys buy out.

## What still has no record

The CUDA microbenchmark figures in Section 5.4, the 30 ms product and the
29.5 ms rotation, and the claim about a mid-range inference card. They carry no
citation and no record. This note does not fix that.
