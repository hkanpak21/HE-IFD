# fa02 — Full MIA suite on the freeze-A released model

**Type:** AFK (compute + code). **Status:** 📥 OPEN. **Depends:** fa01 (winning config).
**PRD:** `docs/prd/he-ifd-freeze-a-improvement.md` addendum §4. **Ops:** `CLAUDE.md`.

## Why (do not soften this)

The response-to-reviewers (R1-W4, R2-Q5) promises "residual leakage is measured with membership
inference — near chance." The existing measurements (021/028) are on the **superseded distillation
method's** released model. The promise must be backed by measurements on THE method being
submitted. User decision 2026-06-10: full suite, not a spot check.

## Task

Extend the existing `mia/` suite to attack the released θ⋆ of the freeze-A LoRA method:

- Targets: all four text tasks (ag_news, trec, dbpedia_14, banking77) at the fa01 winning config,
  3 seeds, plus CIFAR-100/ViT if the S6 vision arm landed.
- Attacks: loss-threshold (Yeom) + LiRA (shadow models, online/offline), and the
  **fellow-client adversary** variant (attacker holds its own shard as a prior — this is the
  adversary our threat model actually permits, so it is the headline attack).
- Surface: the released model only (the displacement surface is cryptographically covered by
  Proposition 1; do not spend compute re-attacking ciphertexts).
- Report: `backbone,N,alpha,method,seed,surface,attack,tpr_at_0.1pct,tpr_at_1pct,auc` rows
  (canonical MIA CSV schema) under `results/heifd_mia_freeze_a/`.

## Acceptance criteria

- [ ] AUC + low-FPR TPR for every (task, attack, seed); shadow count documented.
- [ ] The prior vision deviation (old 028: LiRA AUC 0.85 on ViT) re-checked on the new method —
      if it persists, that goes in the paper honestly with the threat-model framing, not hidden.
- [ ] One paragraph of findings ready to drop into §Residual Leakage, replacing the
      old-method numbers; states clearly what was attacked and under which adversary.

## Notes

- Shadow training rides the same teacher/seed-cache discipline as the protocol runs; budget the
  shadows (e.g., 16–32 per target) and document the choice — reviewers check this.
- LiRA on LoRA-released models: attack the model's loss on candidate points; no need to attack
  adapter weights directly.
