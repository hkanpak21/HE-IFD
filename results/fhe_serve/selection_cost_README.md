# selection_cost

What the selection step costs. The paper states a bound of 2*N*C encrypted
comparisons and gives no time and no traffic, so this measures both. Job 1618539
on VALAR, 2026-09-02, twelve cells over N in {5, 10, 20} and C in {4, 14, 77, 100},
ring degree 2^15.

| N | C | wall clock | traffic | sign circuits | 2NC |
|---|---|---|---|---|---|
| 5 | 4 | 400 s | 3.4 GiB | 31 | 40 |
| 10 | 100 | 2543 s | 36.5 GiB | 161 | 2000 |
| 20 | 100 | 7111 s | 145.4 GiB | 321 | 4000 |

**The federation pays this once, before it answers anything.** No part of it
recurs per query, so it does not enter the per-query figure of Table V.

**The bound is not violated.** At twenty clients and a hundred classes the
implementation evaluates 321 sequential sign circuits where 2NC allows 4000. What
the comparison count does not carry is depth: each comparison is a polynomial
approximation of the sign, every approximation consumes levels, and restoring
them is 99.8 per cent of the traffic. That is the price the current comparison
literature charges, and the alternative is to decrypt the two scores.

**Correct in all twelve cells.** The decoded winner matches the plaintext winner
everywhere, and the per-class totals come back with a relative error near 1e-8.

This run restores levels by collective refresh, where every client sends a share.
The protocol specifies server-side bootstrapping, under which the traffic would
fall sharply and the wall clock would rise. Neither pair has been measured.

Record: `selection_cost.csv`.
