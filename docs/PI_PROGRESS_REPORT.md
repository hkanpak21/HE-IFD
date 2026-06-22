# HE-IFD — progress note

Status 2026-06-22. Numbers are from the runs in `results/`; the membership-inference suite is in its final scoring pass and is marked where it appears.

## Where the method stands now

The protocol is unchanged in spirit from what we discussed: each client fine-tunes a small LoRA adapter + head on a frozen public backbone from a shared init θ₀, uploads the encrypted displacement Δⱼ = θⱼ − θ₀, and the server computes θ⋆ = θ₀ + Σⱼ wⱼΔⱼ under multiparty CKKS — depth-one, no bootstrapping, threshold decryption. The substantive change this period is that we made the "linear / task-arithmetic" claim *actually true*, and built two things on top of it.

The central claim was false as written. With standard LoRA (both A and B trained) the update BⱼAⱼ is bilinear, so averaging the factors separately is not the average of the updates — the spine of the paper ("the encrypted aggregation is linear in the transmitted quantities") did not hold, and it showed up empirically as seed collapses under heterogeneity (AG-News falling to ~0.27 on one seed, which made the means meaningless). We now **freeze A at the shared public init and train only B** (FFA-LoRA, cited — not ours). Then Σⱼ wⱼ Bⱼ A₀ = Σⱼ wⱼ ΔWⱼ exactly, the claim is literally true, the encrypted payload halves, and the merge is stable. Head-to-head it wins on both mean and variance, and the gain concentrates on exactly the collapse seeds (e.g. AG-News 0.75±0.09 vs 0.68±0.15, TREC 0.72±0.05 vs 0.57±0.13; collapse-seed 0.65 vs 0.48). This is now a correct claim instead of a refutable one, and the novelty is no longer freeze-A itself but what it buys under one-shot encryption.

On top of that, the second new piece is **encrypted multi-candidate release with client-side vote selection**. A blind server can't adapt the aggregation rule to the data, so we restore that adaptivity after decryption at zero extra HE cost. Every useful rule is itself linear, so the server emits several depth-one candidates in one pass — a λ-scaling family, Fisher- and class-count-weighted merges (depth-one via a numerator/denominator trick: clients upload Enc(F⊙Δ) and Enc(F), server only adds, clients decrypt both and divide in plaintext), and leave-one-out aggregates — and the clients jointly decrypt them and pick the winner by a sample-weighted vote on local holdouts. The vote picks the test-best candidate in 34/39 cells; no single fixed rule wins everywhere (count-head best in 28/39, Fisher in 10/39), and under severe skew (α=0.1) the selected model beats the plain weighted average by +24 / +21 / +13 / +38 points on AG-News / TREC / DBpedia / Banking77. We found no precedent for multi-candidate threshold decryption + post-decryption selection in HE-FL, so this is a clean protocol contribution; the leakage accounting is explicit (the λ family reveals nothing beyond θ⋆; leave-one-out exposes per-client contributions to participants, which our threat model already permits).

A direct payoff is the **coverage gap under extreme skew**, which was our weakest spot. On Banking77 (77 classes, α=0.1) the gap to centralized was 0.52; with freeze-A + count-head aggregation + the vote the released model reaches 0.77, gap 0.11 — closed with no extra communication and no privacy budget. DBpedia reaches 0.94 (within 0.05 of centralized) at K=400.

## Experiments and what they show

Text (frozen RoBERTa, AG-News / TREC / DBpedia / Banking77, N=10, α=0.1, 3 seeds) is summarized above. Three other arms landed:

**Vision** (frozen ViT-B/16) was previously a negative result — on CIFAR-100 the adapter added −0.01 over a linear probe. Under the new method it's positive: CIFAR-100 reaches 0.78 selected vs 0.87 centralized, restoring the cross-modality claim with evidence. We also ran the method at the **published partitions** of the comparators (answering the prior-round complaint about mismatched setups): CIFAR-10 N=5 (DENSE) → 0.96 vs their 0.50/0.60; CIFAR-10 N=20 α=0.04 (FedAUXfdp, DP) → 0.94 vs their 0.75 at ε=0.5; Tiny-ImageNet N=10 α=0.1 (FedSD2C) → 0.73. Model class is ours (frozen ViT + adapter), which we state; the controlled axes are dataset / N / α.

**LLM scale**: the protocol carries to a frozen Qwen2.5-0.5B — DBpedia 0.87–0.88 selected (plain average collapses to 0.44), AG-News 0.71–0.72 — with the encrypted object still only 26 ciphertexts / 13 MiB, because only the adapter is encrypted, not the 0.5B backbone. This is the point that the cost is set by the adapter, not the model behind it.

**Cryptographic cost**, measured end-to-end in Lattigo at the real freeze-A payload (~150k params): 19 ciphertexts / 9.5 MiB per client (half the old both-A-B object), one round; server aggregation 76 ms (N=10) to 0.72 s (N=100), threshold decrypt 44 ms to 0.43 s, no bootstrapping; decrypted result matches plaintext to relative ℓ₂ ≈ 10⁻⁹. Multi-candidate release adds k decryptions, linear (~0.5 s for a 12-candidate set). For contrast, encrypting the full RoBERTa would move ~7.5 GiB/client/round over many rounds; the closest current adapter-HE work (SHE-LoRA, ICLR'26) is multi-round and still carries the bilinear aggregation noise that freeze-A removes.

**Membership inference** is now measured on the freeze-A released model rather than asserted — shadow-model loss-threshold + LiRA, under both an external adversary and the fellow-client adversary (a participant using its own data as a prior, the strongest our threat model admits). The first scored cell (AG-News) sits at chance: AUC 0.49–0.51, TPR ≈ 1% at 1% FPR for both adversaries. The remaining 11 cells are finishing their scoring pass on the cluster (shadows ~all trained); the full table folds in shortly.

A field scan also settled the positioning: "first one-shot federated fine-tuning" is taken (arXiv:2412.04650) and freeze-A is FFA-LoRA's, but "first one-shot federated *learning* under multiparty HE" is open — all HE-FL is multi-round, all one-shot FL is plaintext or DP — and the co-design (freeze-A → exact, depth-one encrypted merge) plus the multi-candidate release are unoccupied. The revised claim, related-work paragraphs, and the multi-candidate section are drafted in `docs/paper/drafts/`.

Net: the method is internally consistent now (the claim is true), stronger (collapses fixed, coverage gap 0.52→0.11, vision positive, half the payload), broader (LLM scale, matched comparators), and the privacy claim is measured.

## Venues

- **IEEE TNSE** — current target, in flight.
- **IEEE TIFS** — arguably the best fit: HE + measured MIA + threat model is squarely its scope.
- **PoPETs/PETS** — strong fit for the privacy-by-construction + MIA framing, fast rolling deadlines.
- **IEEE TDSC** — natural home, but where v1 was rejected (shared reviewer pool is the risk; method is now substantially different).
- **USENIX Security / CCS / NDSS / IEEE S&P** — if we want to aim the novel protocol + end-to-end Lattigo + MIA at a top conference; NDSS/USENIX have the friendliest cadence.
- **NeurIPS / ICML / TMLR** — secondary; the freeze-A co-design + multi-candidate selection is ML-publishable but the HE-cost argument is valued less there.

My recommendation: keep TNSE in flight; if repositioning, TIFS or PoPETs are the best-matched homes, NDSS/USENIX if we want to aim higher with the protocol contribution.
