# fhe_serve — Serve-mode encrypted-inference cost

Job 1 of the "price of Serve" microbenchmark for the encrypted-inference threat-model
upgrade (branch `threat-model-encrypted-inference`). Serve mode keeps the aggregated head
in ciphertext and answers queries **under encryption**, so the strong threat model (clients
learn only labels) holds; per query it pays a **collective refresh** (multiparty bootstrap)
— the unit that dominates the encrypted argmax — plus a **threshold decrypt**, neither of
which Release mode pays. Measured with multiparty CKKS in Lattigo v6.1.0 ([fhe/serve.go](../../fhe/serve.go)),
logN=15, 12 multiplicative levels, on VALAR `t4_ai` (CPU path; no GPU used).

| N parties | collective refresh (ms) | threshold decrypt (ms) | rel. L2 |
|-----------|-------------------------|------------------------|---------|
| 5         | 586                     | 135                    | 4e-10   |
| 10        | 1057                    | 192                    | 6e-10   |
| 20        | 2047                    | 361                    | 9e-10   |

The refresh scales ~linearly in N (~100 ms/party); one collective refresh is ~0.6–2 s.
The encrypted argmax over C classes needs **several** refreshes (the minimax sign circuit's
stages × the C-way max-tree), so per-query Serve latency is dominated by how many refreshes
the argmax costs — quantified in **Job 2** (full argmax over C∈{4,6,14,77,100}).

## Job 2 — encrypted argmax (naive sequential fold)

Full encrypted argmax over C classes ([serve_argmax.go](../../fhe/serve_argmax.go), `-serve-argmax`),
N=10, logN=15, 14 levels, **exact** (max abs err 0). Naive C−1 sequential pairwise-`Max` fold with an
accumulator refresh each step — an honest **upper bound**. Data in [argmax_cost.csv](argmax_cost.csv).

| C (task) | comparisons | collective refreshes | argmax latency |
|----------|-------------|----------------------|----------------|
| 4 (AG-News)     | 3  | 14  | 47.0 s |
| 6 (TREC)        | 5  | 24  | 78.5 s |
| 14 (DBpedia)    | 13 | 64  | 3.5 min |
| 77 (Banking77)  | 76 | 379 | 20.4 min |
| 100 (CIFAR-100) | 99 | 494 | 26.5 min |

Per-op costs: **~16.1 s/comparison** (~5 collective refreshes @ ~1.35 s + ~9.3 s local sign eval).

### Optimization estimate (our per-op costs × literature op counts)
Naive is a loose upper bound. Log-depth **SIMD tournament** (= NEXUS QuickMax, NDSS'25; Lee–Choi–Lee 2023)
→ ⌈log₂C⌉ sequential comparisons instead of C−1 (one SIMD round = one comparison cost, all pairs in parallel;
rotations use one-time collective Galois keys, no bootstrap):
- **#1 tournament:** C=100 → 7 × 16.1 s ≈ **1.9 min (~14×)**; tuned (~1 refresh/round) ≈ 1.2 min.
- **#1 + minimax-composite sign** (Cheon ASIACRYPT'20 / Lee TDSC'22, ~0.55×/comparison) ≈ **1 min (~26×)**.
- **#3 cutmax** (arXiv 2509.08383, comparison-free, ~constant in C) ≈ sub-minute, pending accuracy validation.
- Single-key **GPU (NEXUS)**: sub-second.

Threshold CKKS changes **only** keygen + decrypt (evaluation is identical), so these single-key results
transfer. Paper: textual only (no table) in `sec:serve` "Cost, and who serves".

## Job 3 — encrypted argmax via log-depth SIMD tournament (QuickMax), MEASURED

The optimized alternative ([serve_tournament.go](../../fhe/serve_tournament.go), `-serve-tournament`): pack
the C logits into one ciphertext and reduce with a ⌈log₂C⌉-round rotate-and-Max tournament (power-of-2
Galois rotations, collective-refresh-backed sign). Same N=10, logN=15, **exact**. Data in
[argmax_tournament.csv](argmax_tournament.csv).

| C (task) | rounds | refreshes | latency | vs naive fold |
|----------|--------|-----------|---------|---------------|
| 4 (AG-News)     | 2 | 9  | 31.2 s   | 1.5× |
| 6 (TREC)        | 3 | 14 | 47.3 s   | 1.7× |
| 14 (DBpedia)    | 4 | 19 | 63.7 s   | 3.3× |
| 77 (Banking77)  | 7 | 34 | 1.87 min | **10.9×** |
| 100 (CIFAR-100) | 7 | 34 | **1.88 min** | **14.0×** |

Measured **14.0× at C=100** (494 → 34 collective refreshes), exact — confirms the estimate. This is the
multiparty-CKKS realization of NEXUS QuickMax; single-key GPU (NEXUS) is sub-second.

## Job 4 — the argmax INDEX, not the maximum value, MEASURED

Jobs 2 and 3 both reduce the encrypted logits to the largest **value**. Algorithm 2
specifies the **index**. Two constructions produce it
([serve_index.go](../../fhe/serve_index.go), `-serve-index`), both at N=10, logN=15,
on the same fifteen-modulus chain and the same seeded logits, so the `tournament_max`
rows reproduce [argmax_tournament.csv](argmax_tournament.csv) as a control. Data in
[argmax_index.csv](argmax_index.csv). Job 1611889 on VALAR `ai`, CPU only.

**one-hot.** Broadcast the maximum from slot 0 across the label slots, evaluate one
step circuit on `(l_c - M + tau)/2` to obtain an encrypted one-hot vector, then take
an inner product with the plaintext index vector. One extra sign evaluation. Correct
whenever the top-1/top-2 gap exceeds `tau` and `tau` exceeds the smooth-max error.

**tracked.** Carry an index ciphertext through the tournament, updated each round by
`i <- b(i_a - i_b) + i_b` where `b` is the comparison bit the value update already
computed. No extra sign evaluation, no threshold.

| C | control (max only) | one-hot, total | tracked, total | control refreshes | one-hot | tracked |
|---|---|---|---|---|---|---|
| 4   | 31.0 s | 46.9 s (+51%) | 32.3 s (+4.1%)  | 9  | 14 | 10 |
| 6   | 46.3 s | 62.1 s (+34%) | 49.8 s (+7.6%)  | 14 | 19 | 16 |
| 14  | 62.8 s | 79.0 s (+26%) | 68.0 s (+8.3%)  | 19 | 24 | 22 |
| 77  | 110.9 s | 127.7 s (+15%) | 120.6 s (+8.7%) | 34 | 39 | 40 |
| 100 | 110.9 s | 127.8 s (+15%) | 121.1 s (+9.2%) | 34 | 39 | 40 |

**Every decoded index is exactly the plaintext argmax**, at every C and at both
`tau` values (1e-4 and 1e-3). The decoded one-hot mass is 1.000000 in all ten one-hot
cases, so exactly one slot carries the indicator. Index absolute error runs from
2.7e-09 at C=4 to 3.0e-06 at C=100, against a rounding margin of 0.5.

The threshold condition is satisfied with room at every measured C. The smooth-max
error is 1.1e-09 to 1.6e-08 and the top-1/top-2 gap is 0.0062 to 0.087, so the
required ordering `error < tau < gap` holds by four orders of magnitude on each side.
It is a condition on the data, not a proof: a query whose top two logits fall within
`tau` of each other would break the one-hot route. The tracked route has no `tau` and
degrades only where the maximum itself does.

**The tracked route is the one to use.** It is cheaper (+4% to +9% over the value-only
control, against +15% to +51%), it needs no threshold, and it needs no extra rotation
keys. The one-hot route needs Galois keys for the negative power-of-two steps as well
as the positive ones, which doubles the rotation-key setup, seven keys to fourteen.

## Job 5 — one real query, end to end, against a real trained head

Everything above runs on synthetic vectors, so none of it says the encrypted path
answers a real query the way the plaintext model does. `real_query/` does.
`jobs/fhe_export_head.py` rebuilds the served head from the recorded artifact
`ag_news_s42.pt` and computes real test features under the same frozen backbone;
`fhe/serve_real.go` (`-serve-real`) encrypts a feature vector, applies the
encrypted head, takes the argmax index under encryption and key-switches the
label to the querier, who alone decrypts it.

**Thirty-two of thirty-two queries agree with the plaintext label**, sixteen on
each servable arrangement, at N=10, ring degree 2^15 and scale 2^45. VALAR jobs
1618537 (export), 1618540 and 1618541. The hardest margin resolved was 0.006771
after the public logit scale, tighter than any gap in `argmax_index.csv`. Per
query: about 5.5 s to apply the head, 34 s for the argmax at 11 collective
refreshes, 0.6 s to reach the querier, which is the cost of the refresh mechanism
and not of the server-side bootstrapping Table V reports. Data in
[real_query.csv](real_query.csv), written up in
[real_query_README.md](real_query_README.md).

## Job 6 — the cost of the selection step, MEASURED

The paper states that selection "costs at most 2NC encrypted comparisons, once"
and gives no measurement. This measures it
([protocol_cost.go](../../fhe/protocol_cost.go), `-selection-cost`), over N in
{5,10,20} and C in {4,14,77,100} at ring degree 2^15, on the same fifteen-modulus
chain the argmax uses, with level restoration by collective refresh. Data in
[selection_cost.csv](selection_cost.csv). Job 1618539 on VALAR `ai`, CPU only,
44:54 wall clock.

Each client scores both arrangements on its held-out data under encryption:
reduce every held-out example's logits to their maximum by the serving
tournament, test with one step circuit whether the true label's logit is that
maximum, mask that slot with the client's own public label, and fold the
per-example indicators into one encrypted per-class count vector. The server sums
the N count vectors, applies the prior-weighted estimator with public scalars at
depth one, compares the two encrypted scores, and the quorum decrypts one value.

**A client's whole held-out set fits in one ciphertext.** One example per class
occupies C blocks of 2^ceil(log2 C) slots, which is at most 16,384 slots at every
class count the paper reports, so a client scores its entire held-out set with one
tournament and one step circuit. Selection costs 2N encrypted argmaxes, not 2NC.

| N | C | one client, one arrangement | selection, all 2N | refreshes | traffic |
|---|---|---|---|---|---|
| 5  | 4   | 38.8 s  | 6.7 min   | 144  | 3.4 GiB |
| 5  | 100 | 103.7 s | 17.5 min  | 394  | 9.2 GiB |
| 10 | 4   | 45.7 s  | 15.5 min  | 284  | 13.3 GiB |
| 10 | 100 | 126.4 s | 42.4 min  | 784  | 36.5 GiB |
| 20 | 4   | 63.9 s  | 42.9 min  | 564  | 52.6 GiB |
| 20 | 100 | 177.3 s | 118.5 min | 1564 | 145.4 GiB |

The score circuit is measured once per arrangement for one client and the 2N
figure is computed from that rate, which is how the other per-operation costs in
`protocol_cost.go` are reported. The server combine (0.16 to 0.50 s per
arrangement), the final comparison (11.1 to 18.7 s) and the single threshold
decryption (0.08 to 0.18 s) happen once for the federation and are measured as
they stand.

**Every cell decrypts the right winner**, indicator 1.000000 against a plaintext
score gap of 0.33 to 0.75, and the encrypted per-class counts match the plaintext
counts to a relative L2 error of 2.0e-09 to 1.2e-08.

**The traffic is the refresh traffic.** Collective refresh shares are 98.2 to 99.8
per cent of every cell's bytes, because each of the 2N score circuits refreshes 14
to 39 times and each refresh collects a 4.75 MiB share from every client. The
traffic therefore grows as N^2: 3.4 GiB at five clients and four classes, 145 GiB
at twenty clients and a hundred. The count vectors themselves are 5.5 MiB each
because the circuit leaves them near the top of the chain; a client that drops the
level before uploading, which costs nothing since the server only sums them, would
send 1.0 MiB instead.

**Against the paper's count.** Read as the number of pairwise comparisons, 2NC is
short by a factor of 2^ceil(log2 C): the equality test is one comparison per
held-out example, but the maximum it compares against costs C-1 more. At N=20 and
C=100 the circuit performs 512,001 pairwise comparisons where 2NC is 4,000. Read
as the number of sequential sign circuits, 2NC is long: the comparisons within a
round are packed across slots and across held-out examples, so the circuit
evaluates 321 of them, not 4,000. Neither count is the cost. The cost is two hours
and 145 GiB, once, at the largest configuration measured.
