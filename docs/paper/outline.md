# TNSE paper — section skeleton (draft order: §4 → §5 → §3 → §6 → §1/§2 last)

Obeys `notation-and-terms.md`. Bar for every paragraph: preempt a reviewer concern · be clear · deliver the result.

1. **Abstract** *(written last)* — gap, claim (crypto-not-DP + shared loss basin + scales to pretrained), headline result, FHE cost.
2. **Introduction** *(written near-last)*
   - The gap: one-shot FL needs either lossy DP (utility hit) or impractical HE (the 460 GB problem). No one delivers *lossless* privacy at one upload on modern model scales.
   - The claim + contributions (numbered).
3. **Related work**
   - One-shot / data-free FL (DENSE, Co-Boosting, FuseFL — plaintext ceiling, no head-to-head).
   - DP one-shot FL (FedAUXfdp, FedDiff, FedKT — the lossy-privacy peer group).
   - HE in FL (POSEIDON anchor + the 460 GB framing we displace).
4. **Preliminaries & threat model**
   - Multiparty CKKS, distributed key generation, threshold decryption (no single party decrypts).
   - Averaging-variant DP on prototypes. **Notation table here.**
   - Threat model: server excluded from Phase 0 (P2P channels); honest-but-curious server for aggregation.
5. **Method**
   - 5.1 Problem setup & overview (frozen backbone φ, trainable head ψ).
   - 5.2 **Phase 0 — shared loss basin construction** (interchangeable sources: public probe / DP prototypes / synthetic / no-probe). The basin's job is *alignment*, not accuracy.
   - 5.3 Local bounded-trajectory distillation → cumulative displacement `Δ_j`.
   - 5.4 Encrypted linear aggregation — the only server crypto op, depth ≈ 1.
   - 5.5 Privacy stack (lossless crypto + DP on prototypes) and why it beats lossy-DP utility.
6. **Experiments**
   - 6.1 Setup (datasets, backbones, heterogeneity α, metrics — reader-friendly names).
   - 6.2 **Both ingredients are necessary** — the 2×2: no-alignment baseline diverges; shared basin enables coherent updates. (Establishes the spine.)
   - 6.3 **Works under FHE guarantee even with a weak/low-leak basin, and a stronger basin lifts it further — up to centralized.** The basin-strength continuum; the no-probe result leads, near-oracle recovery closes. (Your flow steps 1→2.)
   - 6.4 **Scaling to large pretrained backbones** (ViT on CIFAR-100; strong frozen text encoders on AG-News / DBpedia). (Flow step 3.)
   - 6.5 **Privacy is nearly free + practical** — DP frontier flat from ε≈2; real-FHE cost (≈5 MiB/round vs 460 GB), correctness L2 ≈ 1e-9, depth = 1.
   - 6.6 Discussion — incentive (coverage of locally-unseen classes vs the local specialist); comparator table.
7. **Membership inference** *(placeholder — written after the rest)*.
8. **Conclusion.**
