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
