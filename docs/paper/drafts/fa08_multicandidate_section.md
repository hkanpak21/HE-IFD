# fa08 draft — encrypted multi-candidate release with client-vote selection
(for HITL review; proposed method subsection + experiments paragraph)

## Method subsection (proposed: after "Encrypted Linear Aggregation")

### The protocol box

Because every candidate below is linear in the encrypted displacements, the
server can produce all of them in one pass at multiplicative depth one:

1. **λ family**: Enc(θ⋆(λ)) = θ₀ + λ·Σⱼ wⱼ·Enc(Δⱼ) for a public grid of λ.
2. **Weighted merges via numerator/denominator**: each client also uploads
   Enc(Fⱼ⊙Δⱼ) and Enc(Fⱼ) (formed client-side before encryption; Fⱼ = local
   diagonal Fisher, or per-class example counts applied to the head rows).
   The server only ADDS: Enc(Σ wⱼFⱼ⊙Δⱼ) and Enc(Σ wⱼFⱼ). After decryption
   the clients divide elementwise in plaintext.
3. **Leave-one-out family**: Enc(θ⋆₋ᵢ) = θ₀ + Σⱼ≠ᵢ w̃ⱼ·Enc(Δⱼ) with public
   renormalized weights w̃.

The clients then jointly decrypt the k candidates (k threshold key-switches —
measured 44 ms each at the headline payload, N=10), each client scores every
candidate on a local holdout (10% of its shard), and the federation releases
the sample-weighted argmax. Selection is post-decryption and client-side:
zero homomorphic cost, no server involvement, no extra round (votes ride the
download/upload of the decryption protocol itself, or a cheap broadcast).

### Why this matters under encryption specifically

A blind server cannot adapt the aggregation rule to the data — encryption
removes exactly the data-dependent control flow that adaptive merging needs.
Multi-candidate release moves the adaptivity to where plaintext exists: the
clients after threshold decryption. Every rule the literature debates
(scaling, curvature weighting, coverage weighting, outlier exclusion) becomes
one more depth-one candidate, and the data picks the winner.

### Leakage accounting (MUST appear in the paper)

- The λ family is collinear — θ⋆(λ) = (1−λ)θ₀ + λθ⋆(1) — so releasing the
  whole grid reveals nothing beyond θ⋆(1) itself.
- The numerator/denominator pair reveals Σ wⱼFⱼ⊙Δⱼ and Σ wⱼFⱼ separately:
  strictly more than their ratio. Admissible under our threat model
  (participants receive the model anyway; the server still sees only
  ciphertexts), and stated as such.
- The leave-one-out family reveals, to participants, each client's
  contribution up to public weights (difference of two candidates isolates
  one Δᵢ). This is the price of the robustness defense; deployments that
  want participant-side contribution privacy should restrict the candidate
  set to the λ family, which leaks nothing extra. The server's view is
  unchanged in all cases (Prop. 1 extends candidate-wise: each candidate is
  a fixed public-coefficient linear map of the same ciphertexts).

## Experiments paragraph (numbers as of 2026-06-11; ⏳ = pending)

- **Selection quality**: across the 39 program cells the vote picked the
  test-best candidate in **34/39**; four of the five misses cost ≤2 points
  (worst case −9.8 on TREC, whose shards give the smallest holdouts).
- **Lift over a fixed rule**: under severe skew (α=0.1) the vote-selected
  model beats the plain average by **+24 (ag_news), +21 (trec), +13
  (dbpedia), +38 (banking77)** points; no single fixed candidate wins
  everywhere (count-head 28/39, Fisher 10/39, λ<1 1/39) — the vote, not any
  one rule, is the robust winner.
- **Byzantine-lite robustness (S7)**: with one poisoning client (largest
  shard; sign-flip / large-Gaussian / label-flip), the vote excluded the
  attacker in **8/8 completed cells (⏳/18 total)**, recovering oracle
  (attacker-free) accuracy exactly, while the undefended plain aggregate
  fell to 0.07–0.70.
- **Cost**: k candidates = k threshold decryptions, measured linear: a
  12-candidate set (λ grid + LOO at N=10 + count-head num/denom) adds ~0.5 s
  total at the headline payload; the count-head denominator is one extra
  ciphertext.

## Contribution bullet (proposed)

> "We introduce encrypted multi-candidate release: the server publishes
> several depth-one aggregates (scaled, curvature-weighted via separate
> numerator/denominator decryption, and leave-one-out), and the clients,
> after threshold decryption, select by a weighted vote on local holdouts.
> This restores data-dependent aggregation choice to a setting whose server
> is cryptographically blind, at zero homomorphic cost; it selects the best
> candidate in 34/39 cells, adds up to +38 accuracy over the fixed average
> under severe heterogeneity, and yields a measured defense that excluded a
> poisoning client in ⏳ of 18 attack cells."
