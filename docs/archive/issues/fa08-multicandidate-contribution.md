# fa08 — Multi-candidate threshold decryption as a named protocol contribution (HITL)

**Type:** HITL (analysis + writing). **Status:** 📥 OPEN. **Depends:** fa01 (selection-quality
data), fa04 (LOO data), fa06 (decryption-scaling cost). **PRD:** addendum §5.

## Why

Field scan 2026-06-10: no precedent in MHE-FL for "server emits several depth-1 candidate
aggregates; clients threshold-decrypt all and select by vote on local data." Combined with the
relaxed threat model (participants receive the model anyway), this is promotable from an eval
trick to a protocol-level contribution: it converts every aggregation-rule debate (λ, weighting,
LOO robustness) into a post-decryption *empirical* choice at zero HE depth.

## Task

1. **Write the protocol box**: candidate set construction (λ grid, weighting variants, N
   leave-one-out), k threshold decryptions, sample-weighted client vote, release of argmax.
2. **Leakage analysis (must be in the paper)**:
   - λ candidates are collinear — θ⋆(λ) = (1−λ)θ₀ + λθ⋆(1) — so revealing the grid reveals
     nothing beyond θ⋆ itself.
   - LOO candidates reveal each ΔWᵢ up to the public weights (the difference of two candidates
     isolates one client's contribution) — this IS the per-client update, exposed to
     participants. State that this is admissible under our threat model (participants may infer
     from one another; the server still sees only ciphertexts) and is the price of the
     robustness defense; deployments wanting participant-side privacy should restrict the
     candidate set to the λ family.
   - Fisher/count-head num/denom reveals the two aggregates separately — more than θ⋆ alone,
     same admissibility argument.
3. **Selection quality**: from fa01 data, how often does the client vote pick the test-best
   candidate (or within ε of it)? That's the empirical claim that the vote works.

## Acceptance criteria

- [ ] A method subsection draft (protocol + leakage analysis) and an experiments paragraph
      (selection quality + fa04 robustness numbers + fa06 cost).
- [ ] Contribution bullet drafted; user approves the naming and placement.
