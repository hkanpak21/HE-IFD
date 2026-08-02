# fa06 — FHE cost re-measurement for the freeze-A payload + comparator rows

**Type:** AFK (compute, Lattigo/Go, CPU). **Status:** 📥 OPEN. **Depends:** fa01 (final
n_trainable), fa03/fa04 (payload + candidate counts). **PRD:** addendum §3. **Ops:** `CLAUDE.md`.

## Task

Re-run the Lattigo multiparty-CKKS measurement (`fhe/`) for the **actual encrypted objects** of
the final method, replacing the old MLP-era numbers in tab:cost-comm / tab:cost-time:

1. Freeze-A payload: B matrices + head at the fa01 winning rank (count from the runner's
   `n_trainable`) — expect roughly half the both-A-B ciphertext count (~10 MiB at r=8; verify).
2. Num/denom variants: Fisher/count-head double the upload (Enc(F⊙Δ) + Enc(F)) — measure the
   actual ciphertext counts and times if fa01 selects one of them.
3. Multi-candidate decryption: k candidates (λ grid + LOO from fa04) ⇒ k threshold decryptions —
   measure decryption scaling so the robustness/selection cost claim is backed.
4. LLM-scale payload (fa03's adapter size) as one more row.
5. Same correctness check: relative ℓ2 vs plaintext aggregate, N ∈ {5, 10, 100}.

## Acceptance criteria

- [ ] Updated measured rows for tab:cost-comm and tab:cost-time (same ring/scale parameters as
      the current section unless there's a reason to change; document if changed).
- [ ] SHE-LoRA + FedShield-LLM comparison rows drafted for tab:hecomm: their per-round encrypted
      object × rounds vs ours × 1 (cite their reported numbers verbatim; mark estimates).
- [ ] The method-section payload sentence ("a few tens of ciphertexts") checked against reality.
