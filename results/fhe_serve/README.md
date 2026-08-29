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
