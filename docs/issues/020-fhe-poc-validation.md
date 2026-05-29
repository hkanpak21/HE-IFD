# 020 — Real-FHE PoC: multiparty CKKS aggregation correctness + cost  [AFK]

> **STATUS: 📥 OPEN** (2026-05-29) — dispatched as background AFK agent. PoC/validation only; not a production system, not required to run on VALAR now.

**Phase:** M2 (rooting) — scoped DOWN to a proof-of-concept that validates the plaintext simulation holds under real CKKS. **Blocked by:** none · **Blocks:** the "real-FHE numbers" paragraph of the Experiments/Method.

**Required reading:**
1. `CLAUDE.md` — the method note (the only server crypto op) + the `fhe/` Lattigo convention.
2. `src/aggregate.py` — the exact plaintext op we must reproduce homomorphically: `θ₀ + Σ_i w_i·Δ_i`, `w_i = n_i/Σ_j n_j`.
3. `docs/prd/he-ifd-tnse-resubmission.md` (M2 scope).

## Why

The paper claims the server aggregation is FHE-compatible **by construction** (plaintext-scalar × ciphertext + ciphertext + ciphertext only; multiplicative depth ≈ 1; multiparty CKKS with DKG + threshold decryption, no single party decrypts). Today that is only a plaintext simulation. We need a **proof-of-concept in real CKKS** that (a) reproduces the plaintext aggregate within CKKS precision, and (b) reports the communication/ciphertext cost — enough to back the claim and kill TDSC R2-2/R2-3 (end-to-end CKKS cost). We do **not** need to train anything, run it at scale, or productionise it.

## What to build (`fhe/`, Go + Lattigo)

A single self-contained Go module under `fhe/` that runs the protocol's one server operation end-to-end under **multiparty CKKS**:

1. **Setup / DKG:** `N` parties jointly generate a CKKS public key + a collective relinearization/Galois key set as needed (Lattigo `multiparty`/`dckks` package). No single party holds the secret key.
2. **Encrypt:** each party `i` encrypts a synthetic displacement vector `Δ_i ∈ R^d` (random floats; `d` configurable — default to a realistic trainable-head size, e.g. `d ≈ 5_130` for a 512→10 linear head, and also test `d ≈ 7_700` for the 768→10 text head). No real training — synthetic vectors are fine and explicitly authorised.
3. **Aggregate (the ONLY server op):** server computes `θ₀ + Σ_i w_i · Δ_i` homomorphically using **plaintext-weight × ciphertext** (`w_i` is a public plaintext scalar) and **ciphertext + ciphertext** additions. `θ₀` is a public plaintext added at the end. Document the multiplicative depth actually consumed (target ≈ 1).
4. **Threshold decrypt:** the parties jointly decrypt the result (collective key-switch to a fresh secret, or the Lattigo threshold-decryption protocol).
5. **Validate correctness:** compute the same `θ₀ + Σ_i w_i·Δ_i` in plaintext (float64) and assert **relative L2 error ≤ 1e-3** (CKKS precision) between decrypted and plaintext results. Print the achieved L2 / max-abs error.
6. **Report cost:** print ciphertext count, serialized bytes per ciphertext, total upload (parties→server) and download (server→parties) bytes, ring degree, scale, and depth used. This is the table the paper cites.

## Acceptance

- [ ] `go build ./...` succeeds under `fhe/`; the program runs locally on the Mac (CPU Go + Lattigo is **not** subject to the VALAR python golden rule — building/running a small Go CKKS PoC locally is fine). If Go is not installed, set it up (`brew install go`) or document the exact build/run command.
- [ ] Running it prints: PASS (L2 ≤ 1e-3) + a cost report (ciphertext count, bytes, depth) for at least `N∈{5,10}` parties and the two `d` head sizes.
- [ ] Depth used is documented and ≈ 1 (matches the "by construction" claim).
- [ ] `fhe/README.md`: what it validates, how to build/run, the achieved L2 + cost numbers, and a note that this is a correctness/cost PoC (no training, mirrors `src/aggregate.py`).

## Hard boundaries

- New code lives under `fhe/` only. Do **NOT** touch `src/`, `comparators/`, `FL_TDSC/`, or any results.
- Pin a recent Lattigo (`github.com/tuneinsight/lattigo/v6` or v5 — whichever the agent verifies has the multiparty/threshold API; document the version).
- No `git push`/`git commit`/`sbatch`/`ssh`. Local `go build`/`go run`/`go test` on the Mac is allowed and expected.

## Report

1. Lattigo version + multiparty/threshold API used.
2. Achieved L2 error + cost numbers (the paper table).
3. Files added under `fhe/`.
4. Any caveat (e.g. threshold-decrypt approximation, parameter choices).
