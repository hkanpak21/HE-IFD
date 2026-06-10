# fa07 — Claim + related-work rewrite (HITL)

**Type:** HITL (paper writing, with the user). **Status:** 📥 OPEN. **Depends:** fa01 verdicts;
fa02/fa04/fa06 numbers for the affected sections. **PRD:** addendum §§1–3, 6.

## The rewrite list (all user-confirmed 2026-06-10)

1. **Core claim**: contributions and abstract move to **"the first one-shot federated learning
   protocol under (multiparty) homomorphic encryption"** — the "first" rides on the crypto side.
   Supporting co-design argument: fine-tuning + freeze-A (FFA-LoRA, cite) is what makes one-shot
   HE possible and cheap — exact task arithmetic ⇒ depth-1, no per-round re-encryption, no
   bilinear cross-terms under encryption. Cite arXiv:2412.04650 (one round suffices for FM
   fine-tuning — supports the premise) and arXiv:2411.18607 (task arithmetic ≡ one-shot FedAvg —
   legitimizes the framing).
2. **Related work, two new paragraphs**:
   - Federated-LoRA aggregation family: FedIT (arXiv:2305.05644), SLoRA (2308.06522), HetLoRA
     (2401.06432), FlexLoRA (2402.11505), FLoRA (2409.05976), **FFA-LoRA (2403.12313 — the
     freeze-A origin)**, FedSA-LoRA (2410.01463), LoRA-FAIR (2411.14961). Frame: the bilinearity
     problem is established; freeze-A is the known fix; we show what it buys *under encryption*.
   - One-shot FT + task arithmetic: 2412.04650, 2411.18607, plus FedSD2C (2412.05186) and FuseFL
     as the current plaintext one-shot frontier.
   - Crypto side: SHE-LoRA (2505.21051, ICLR 2026) + FedShield-LLM (2506.05640) + PrivTuner
     (2410.00433) — multi-round / outsourced; we are one-shot threshold-CKKS.
3. **Semantic-init lineage** (only if fa01-S2 promotes it): dataless classification (Chang 2008),
   DeViSE, BERT head-init (2203.05676); FL differentiators FedAlign (2301.00489, KDD 2023) and
   FedTSP (2503.13543) — both multi-round anchoring vs our zero-communication public init.
4. **Terminology sweep**: "distillation" → "fine-tuning" for ours (intro l.16; related l.41, 95);
   distillation remains only for prior work and the ablation.
5. **Fix the dangling λ promise** in the experiments intro (restore the λ/candidate subsection
   from fa01 data, or cut the promise).
6. **Threat-model subsection**: state explicitly that participants receive θ⋆ by design, so
   inter-client inference via the released model is permitted, not a vulnerability; DP one-shot
   baselines protect a different target (footnoted in every comparison table).
7. Title typo ("Fine-Tuningß"), cross-ref pass, seed-std reporting everywhere.

## Acceptance criteria

- [ ] Every `% PROVISIONAL` marker resolved with fa-series numbers.
- [ ] No "first" claim broader than the user-approved phrasing anywhere (abstract, intro,
      related close, conclusion).
- [ ] Response-to-reviewers updated to match (especially R1-W4/R2-Q5 once fa02 lands).
