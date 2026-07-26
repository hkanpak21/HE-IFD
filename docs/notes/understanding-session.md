# HE-IFD — Understanding Session (running checklist)

Legend: ⬜ not yet · 🔄 in progress · ✅ demonstrated mastery

## Part 1 — The Problem (why this project exists)
- ✅ 1.1 The setting: one-shot FL = single round; removes communication, NOT the per-contribution leakage
- ✅ 1.2 Three branches: plaintext=exposed; DP=lossy+statistical; HE=accuracy-free+cryptographic (the key axis)
- ✅ 1.3 Blind server (no read/compare/branch, finite mult-budget) → training under HE = deep/slow → prior work multi-round
- ✅ 1.4 Empty slot = one-shot × multiparty-HE (all HE-FL multi-round; all one-shot FL plaintext/DP)

## Part 2 — The Solution (what we built and why this way)
- ✅ 2.1 Learning is client-side/plaintext; server's only move = sample-weighted linear sum (depth-1)
- ✅ 2.2 Linear sum needs a shared frame; frozen backbone + common θ₀ supply it free; comparable≠identical; bounded K keeps in-frame
- ✅ 2.3 From-scratch has no frame (needs leaky alignment HE forbids); frozen backbone = frame free; no aux data
- ✅ 2.4 Both-A-B bilinear → (ΣB)(ΣA)≠Σ(BA) cross-terms → claim false + seed collapses; freeze A₀ → factors out → exact (cite FFA-LoRA; ours = the HE-cheapness link)
- ✅ 2.5 Blind server can't adapt → emit depth-1 candidates, vote post-decryption; num/denom pushes division past decryption; vote not an FHE op; +13–38pp, no single rule wins
- ✅ 2.6 Crypto protects CONTRIBUTIONS (server+sub-threshold see only ciphertexts); released model inherently shared → measured, not prevented; vs DP which perturbs the artifact
- ✅ 2.7 Coverage gap = property not failure (Banking77 0.52→0.11); leakage tiers λ<Fisher<LOO; MIA gap & leak share one root cause (per-class memorization)

## Part 3 — Why It Matters (context & impact)
- ✅ 3.1 Borrowed brick, original building: freeze-A=FFA-LoRA (cited), one-shot FT=2412.04650 (plaintext); OURS = one-shot×MHE protocol + freeze-A↔depth-1 co-design + multi-candidate vote
- ✅ 3.2 Reversal thesis: don't force deep training to survive HE; design learning to fit cheap depth-1 HE → 9.5MiB/1 round/no bootstrap by construction
- ✅ 3.3 Honest limits: skew gap contained-not-erased; N=100 over 3h cap (show N≤50); Banking77 MIA elevated; multi-candidate FHE validated-by-construction but extrapolated (crypto-hardening to-do)

---
**Status: COMPLETE ✅ — all 14 items demonstrated + capstone synthesis assembled (problem → solution → significance, with the causal chain intact).**

## Canonical elevator pitch (gold-standard reference)
We build the **first one-shot federated learning protocol under multiparty homomorphic
encryption**. One-shot is the hard part: under encryption the server is *blind* — it can't
read, compare, or branch, and depth is expensive — so it can only afford a single **depth-1
linear sum**, which is why prior HE-FL ran many costly rounds. We make that one sum *enough*
by giving every client the **same frozen pretrained backbone and start**: that shared frame
puts their **bounded** fine-tuning updates in one coordinate system, so they **add to a real
model instead of cancelling**, and **freezing the LoRA down-projection** (FFA-LoRA, cited)
makes the sum **exact at depth-1**. Because the blind server can't pick the best merge, it
emits several depth-1 candidates and **clients vote** post-decryption — recovering accuracy
under heavy skew and defending against a poisoning client. The deeper point is the
**reversal**: instead of forcing deep training to survive encryption (POSEIDON: polynomials,
bootstrapping, hours), we designed the learning to fit what encryption does cheaply — so
**one round, 9.5 MiB, no bootstrapping** by construction. We're scrupulous that freeze-A is
borrowed and that the **released model inherently leaks to participants — which we measure,
not hide**; what's *ours* is the one-shot×HE protocol, the freeze-A↔depth-1 insight, and the
encrypted vote.
