# Paper — internal notes: deferred / out-of-scope items (NOT in the paper)

This is our own tracker for things we deliberately keep **out** of the TNSE submission to avoid
delving into what doesn't work. Decide next steps from here later. Nothing here is paper text.

## Kept out of the paper (by decision, 2026-05-29)

- **CNN-5 / CIFAR-10 from-scratch — outside the basin-coherence envelope.** Distillation lift does
  not reliably materialize; sits outside the working regime. Do NOT present as a failure section.
  Next-step candidates: bigger/longer-trained teacher, a different from-scratch backbone, or simply
  drop CIFAR-10-from-scratch from the headline (FMNIST/LeNet + MNIST/MLP carry the from-scratch story).
- **GPT-2 (small & medium) as a frozen extractor — weak.** Causal-LM features aren't linearly
  separable for topic classification (oracle ~0.40–0.67). Replaced by roberta-base + all-mpnet
  (issue 019). GPT-2 stays out of the headline; at most a one-line "causal-LM features underperform
  for frozen classification" aside if a reviewer pushes. Not a section.
- **High-heterogeneity "fighting updates" failure boundary.** The 013 cosine diagnostic shows ~60%
  anti-correlated client displacements without a shared basin. The *positive* half of this — "the
  aligned basin makes updates coherent, which is why aggregation works" — is a supporting argument
  we MAY use. The *negative* half — mapping exactly where it breaks — stays here, not in the paper.

## Open items to revisit after the draft

- MIA section (placeholder in the paper) — design + run the 3-surface suite after the rest is written.
- Real-FHE PoC is done (issue 020, `fhe/`): L2~1e-9, depth=1, ~5 MiB/round at N=10. 128-bit-secure
  parameter set + a proper t-of-N threshold (vs the current N-of-N) are nice-to-haves, not blockers.
- DBpedia-14 text headline finishing (richer-OOD analogue of CIFAR-100).
- 018 Part-B (ViT-L protocol run) is still HITL-gated; decide whether the scaling story needs it or
  whether ViT-B/32 CIFAR-100 + the big-backbone *sanity* numbers suffice.
