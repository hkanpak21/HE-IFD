# fhe_freeze_a — fa06 Lattigo re-measurement at the real freeze-A payloads

Multiparty CKKS (Lattigo v6.2.0, ring 2^14, scale 2^45, depth 1), Apple M4
single core, real trainable-param counts from the fa01 program:

| scenario | params | cts | MiB/client | enc/client | aggregate | threshold dec | rel L2 |
|---|---|---|---|---|---|---|---|
| freeze-A r8 (ag_news) N=10 | 150,532 | 19 | 9.5 | 40 ms | 76 ms | 44 ms | 2.7e-9 |
| freeze-A r8 (ag_news) N=100 | 150,532 | 19 | 9.5 | 40 ms | 717 ms | 430 ms | 2.6e-8 |
| freeze-A r8 (banking77) N=10 | 206,669 | 26 | 13.0 | 56 ms | 101 ms | 61 ms | 2.7e-9 |
| Qwen2.5-0.5B LoRA (fa03) N=100 | 209,166 | 26 | 13.0 | 56 ms | 956 ms | 582 ms | 2.6e-8 |
| both-A-B r8 (superseded) N=10 | 297,988 | 37 | 18.5 | 80 ms | 145 ms | 89 ms | 2.7e-9 |

Freeze-A halves the encrypted payload (19 vs 37 cts). Multi-candidate
decryption (fa08): k candidates cost k x the decrypt column (linear in
ciphertext count; e.g. a 12-candidate set at N=10 ~= 0.5 s). count_head's
denominator adds 1 ciphertext (per-class counts, C <= 8192 slots).
Replaces tab:cost-comm / tab:cost-time inputs.
