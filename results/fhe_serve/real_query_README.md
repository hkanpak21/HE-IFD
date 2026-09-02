# real_query

One query answered end to end on a real trained head, rather than on the
synthetic vectors every other serving benchmark uses. Job 1618540 on VALAR,
2026-09-02. Arrangement B is job 1618541.

**Result: 16 of 16 encrypted answers equal the plaintext answers.** The tightest
plaintext margin that still decided correctly is 0.037, and the decoded index is
exact to 4.3e-08 in the worst case. Two of the sixteen are queries the head gets
wrong, and the encrypted path reproduces those errors, which is the correct
behaviour: the protocol is faithful to the plaintext computation and not to the
ground truth.

Configuration: AG-News, seed 42, arrangement A, four classes, feature dimension
768, ten parties, ring degree 2^15, plaintext scale 2^45.

**The timing here is not the paper's headline.** This run restores levels by
collective refresh, eleven per query, and the paper specifies server-side
bootstrapping. So 40.7 s per query on average is the cost of the mechanism this
run used, not of the one Table V reports. What carries across mechanisms is the
agreement, because it is a statement about the circuit rather than about how its
levels are restored.

Per-query breakdown, mean over sixteen: head application 5.5 s, argmax 34.4 s,
key switch to the querier 0.59 s, total 40.7 s.

Record: `real_query.csv`. Produced by the serving path added in commit 20394e0.
