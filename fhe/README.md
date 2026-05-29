# `fhe/` — Real multiparty-CKKS validation of the HE-IFD server operation

This is a self-contained Go + Lattigo proof-of-concept that runs the **only**
cryptographic operation in the HE-IFD protocol — the server-side sample-weighted
linear combination

```
θ = θ₀ + Σ_i w_i · Δ_i ,    w_i = n_i / Σ_j n_j
```

**end-to-end under multiparty CKKS** (DKG → encrypt → aggregate → threshold
decrypt) and validates the decrypted result against the plaintext `float64`
computation. It is a one-shot correctness + cost demonstration (PRD M2 / User
Stories 29–31), **not** production crypto.

It exists to answer two reviewer questions precisely:

1. *Does the plaintext simulation in `src/aggregate.py` actually equal the
   encrypted result?* — Yes, to a **relative L2 error of ~1e-9** (the bar was
   ≤ 1e-3), because the server step is purely linear (depth 1).
2. *What does the protocol actually cost on the wire?* — see the cost table
   below; this replaces the rejected paper's 460 GB figure with a real number
   (a few MiB per round for a classifier head).

## What it validates (and does NOT)

- It validates the **server aggregation** — the linear combine over encrypted
  per-client displacements `Δ_i`, then collective decryption — which is the only
  homomorphic computation in the method.
- It does **not** train, distill, or touch real data. The `Δ_i`, `θ₀`, and
  per-client sample sizes `n_i` are synthetic random vectors at realistic head
  dimension and magnitude. Correctness of the crypto is independent of where the
  numbers come from; the point is the homomorphic arithmetic, not the ML.

## The four protocol phases (mapped to the code in `main.go`)

1. **DKG (distributed key generation).** `N` parties each sample a secret key
   `sk_i`; the ideal secret is `s = Σ_i sk_i` and is **never reconstructed in the
   clear**. They jointly build a **collective public key** with Lattigo's
   `multiparty.PublicKeyGenProtocol` (CKG) over a shared common-reference
   polynomial. Clients encrypt to this collective key.
2. **Encrypt.** Each client encodes its length-`d` displacement `Δ_i` into
   `⌈d / slots⌉` CKKS ciphertexts (`slots = ring_degree / 2`) and encrypts under
   the collective public key. These are the uploads.
3. **Aggregate (server — the only crypto op).** The server computes
   `θ₀ + Σ_i w_i·Δ_i` using **only**:
   - **plaintext-scalar × ciphertext** — the `w_i` scaling (`Evaluator.MulNew`
     by a `float64`, then one `Rescale`), and
   - **ciphertext + ciphertext** — accumulation across clients, and adding the
     known `θ₀` as an encoded plaintext.

   **No ciphertext × ciphertext, no relinearization, no bootstrapping.** The
   evaluator is constructed with `nil` evaluation keys precisely to make the
   absence of relinearization structural. **Multiplicative depth used = 1** (one
   level consumed by the scalar multiply, asserted in the test).
4. **Threshold decrypt.** The parties run a **collective key-switch**
   (`multiparty.KeySwitchProtocol`, CKS) from the joint key to a **zero target
   key**: each party contributes a share built from its `sk_i` plus smudging
   noise; the aggregated share switches the ciphertext to be decryptable under
   `sk = 0`, i.e. the result decodes directly. No single party (the server
   included) can decrypt alone — this PoC uses the **N-out-of-N** access
   structure (all parties contribute a share). Lattigo also offers a
   `t`-out-of-`N` Shamir threshold variant; N-out-of-N is the simplest faithful
   instantiation of "a threshold of clients jointly decrypts."

## Build & run

Requires Go ≥ 1.21 (developed on 1.26) and internet on first build (Go fetches
Lattigo). On macOS: `brew install go`.

```sh
cd fhe
go test ./...                 # asserts rel-L2 ≤ 1e-3 and depth == 1 for all scenarios
go run .                      # runs the default suite, prints the cost table
go run . -json results.json   # also dumps the numbers as JSON
go run . -d 5130 -n 5         # one scenario: head dim d, N clients
go run . -d 7700 -n 10 -logn 14
```

`results.json` (machine-readable cost/accuracy dump) is produced by `-json`;
it is regenerable and not load-bearing.

## Results — correctness

Relative L2 error of the decrypted aggregate vs. the plaintext `float64`
reference, across the headline scenarios (head dims `d≈5130` for a 512→10 head,
`d≈7700` for a 768→10 head; `N ∈ {5,10}`). Measured on this Mac (Apple silicon,
CPU), `logN = 14`, `seed = 20260529`:

| scenario        | rel. L2 error | max abs error | bound | pass |
|-----------------|---------------|---------------|-------|------|
| d=5130,  N=5    | 1.4e-09       | 2.3e-09       | 1e-3  | ✅   |
| d=5130,  N=10   | 2.7e-09       | 5.9e-09       | 1e-3  | ✅   |
| d=7700,  N=5    | 1.4e-09       | 2.9e-09       | 1e-3  | ✅   |
| d=7700,  N=10   | 2.7e-09       | 5.8e-09       | 1e-3  | ✅   |

The error is **~6 orders of magnitude below the 1e-3 acceptance bound**, set by
CKKS encoding/rescale rounding plus the threshold-decrypt smudging noise — and
is independent of `d`. This is the empirical justification for treating the
entire plaintext simulation in `src/aggregate.py` as the encrypted result for
accuracy purposes.

## Results — cost (the table the paper cites)

Per round (one upload, one download), `logN = 14`, scale `2^45`, depth 1.
A fresh CKKS ciphertext at `MaxLevel` is **~512.3 KiB** (524 622 B). One
ciphertext holds `slots = 8192` parameters, so a single classifier head
(`d ≤ 8192`) is **1 ciphertext per client**.

| d (head)     | ciphertexts/client | N  | total upload | total download | dec-share traffic |
|--------------|--------------------|----|--------------|----------------|-------------------|
| 5130 (512→10)| 1                  | 5  | 2.50 MiB     | 2.50 MiB       | 0.63 MiB          |
| 5130 (512→10)| 1                  | 10 | 5.00 MiB     | 5.00 MiB       | 1.25 MiB          |
| 7700 (768→10)| 1                  | 5  | 2.50 MiB     | 2.50 MiB       | 0.63 MiB          |
| 7700 (768→10)| 1                  | 10 | 5.00 MiB     | 5.00 MiB       | 1.25 MiB          |

Definitions:
- **total upload** = `N × ⌈d/slots⌉ × bytes_per_ct` (every client uploads its
  encrypted `Δ_i` once).
- **total download** = same volume broadcast back (the result ciphertext(s) to
  all `N` clients) — one download.
- **dec-share traffic** = total bytes of the `N` collective-key-switch shares
  exchanged during threshold decryption (`N × ⌈d/slots⌉ × bytes_per_share`).
- Ciphertexts scale linearly with `d`: e.g. `d = 20000` → 3 ciphertexts/client
  (covered by the test). For larger trainable scopes (LoRA / last-N blocks) the
  ciphertext count grows with the trainable-parameter count; depth stays 1.

Timings (CPU, indicative, single process simulating all parties): client
encryption ~10–25 ms total, server aggregation ~2–4 ms, threshold decryption
~1.5–3 ms per round. These are PoC numbers on a laptop, not a benchmark.

## Crypto parameters (pinned)

| parameter            | value                                   |
|----------------------|-----------------------------------------|
| library              | `github.com/tuneinsight/lattigo/v6` **v6.2.0** |
| scheme               | CKKS, multiparty (CKG + CKS)            |
| ring degree `N`      | `2^14 = 16384` (`logN = 14`)            |
| slots / ciphertext   | `8192`                                  |
| modulus chain `logQ` | `{55, 45}` (one mult level for depth 1) |
| key-switch prime `logP` | `{61}`                               |
| default scale        | `2^45`                                  |
| multiplicative depth | **1** (PT×CT once, then Rescale)        |
| decrypt access struct| N-out-of-N collective key-switch        |
| smudging noise       | `8 × rlwe.DefaultNoise`                  |

The `{55,45}` chain is deliberately minimal: the protocol consumes exactly one
multiplicative level, so two primes suffice. A 128-bit-security parameter set
would widen `logQ`/`logP` (and the per-ciphertext byte cost) but does not change
the depth-1 structure or the correctness argument; this PoC prioritises a
faithful, auditable demonstration of the arithmetic over a hardened parameter
set.

## Caveats

- **N-out-of-N threshold.** Decryption here requires all `N` parties' shares,
  the simplest faithful "joint decryption." Lattigo's Shamir `t`-out-of-`N`
  variant (see `examples/multiparty/int_pir`) drops in if a true `t`-of-`N`
  quorum is wanted; it changes the key-setup step, not the linear server op or
  the correctness/cost story.
- **Single-process simulation.** All parties run in one process (the standard
  Lattigo multiparty example pattern). Network transport is not modelled; the
  reported byte counts are the on-the-wire payload sizes (`BinarySize()` of the
  actual ciphertexts/shares), which is what matters for the comm-cost claim.
- **Parameters are PoC-grade, not security-audited.** See the note above on
  `logQ`/`logP`.
- **Smudging noise** is the library-canonical `8 × DefaultNoise`; an earlier draft
  used an over-large `2^30` smudge which (correctly) blew the L2 error to ~2e-2,
  confirming the bound is sensitive and the chosen value is the right one.
