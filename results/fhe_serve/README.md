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
