# HE-OFT → IEEE TNSE: submission TODO

Ordered by "could get it rejected" first, not by effort. Reviewers may overlap
with the TDSC pool, so every prior-rejection concern (R*) is live.

## Decisions locked 2026-06-10 (grilling session)

1. **Freeze-A (FFA) LoRA is the method** — exact task arithmetic; all re-runs on
   this config. 2. **Vision arm**: one task, CIFAR-100/ViT-B/16, in the re-run
   wave; modality claim conditional on the data. 3. **MIA**: grounded in
   prior-work studies (LiRA etc.) for now; final shape discussed after.
   4. **Comparators**: multiple matched setups run, selection later.
   5. **Headline claim deferred** until the method-improvement program lands —
   "improve the method as much as possible, claim accordingly."
   6. **Threat model sharpened**: clients may infer from one another via the
   released θ⋆ (intra-client inference is permitted by design — MHE position);
   protection target = server + sub-threshold coalitions. This admits
   post-decryption tricks (num/denom merges, client-vote selection).
   7. **New levers in the program** (`results/finetune_improve/`,
   `notebooks/improve_program.ipynb`, `jobs/finetune_improve.{py,sh}`):
   semantic head init (zero-shot public θ₀ from class names), Fisher +
   count-head num/denom aggregation at depth 1, λ grid + client-vote selection,
   SWA/prox/logit-calibration flags, rank compensation.

## Tier 1 — correctness / completeness blockers (must fix)

- [x] **Make the linear-aggregation claim true: freeze LoRA A (train only B).**
  DECIDED 2026-06-10: freeze-A. Implemented in `jobs/finetune_improve.py` (s1
  A/B-tests it against both-A-B on the unstable tasks). Both-A-B runs are
  superseded.
- [ ] **Re-run E1 + sweep + vision on the chosen LoRA config** once (1) is decided;
  fill every `\tbd` from real numbers.
- [ ] **Fix payload-size numbers.** LoRA r=8 ≈ ~300k scalars (not "a few thousand"),
  ~tens of ciphertexts (not one). Correct method.tex overview + cost.tex; the
  head-only number is the only "few thousand."
- [ ] **Re-measure FHE cost for the actual encrypted object** (LoRA+head, or
  freeze-A B+head), not the old MLP. Update tab:cost-comm / tab:cost-time.
  Verify the Lattigo run matches the headline payload.
- [ ] **Vision results (CIFAR-100 / ViT) for the new method**, or delete the
  "across vision and language" / modality-agnostic claim. (FGVC failed; no vision
  data exists yet.)
- [ ] **Terminology sweep: "distillation" → "fine-tuning" for ours.** related.tex
  lines ~40, 94 still say "distillation displacement" / "one-shot federated
  distillation." Keep "distillation" only for prior work.
- [ ] **Make the two hero figures** (fig:increment, fig:robust) from real data;
  verify fig:protocol matches the no-public-data / LoRA method.

## Tier 2 — reviewer-risk (strongly recommended)

- [ ] **MIA: reconcile discussion-only with R2-5/R1-W4.** At minimum cite the
  earlier MIA results (021/028); ideally a small MIA on the *new* released model.
  Asserting the residual-leakage floor without measuring re-opens the rejection.
- [ ] **One matched-setup comparator** (FedAUXfdp / FedKT DP one-shot on a shared
  task) so the privacy-utility claim is evidence, not others' numbers at others'
  setups. Addresses R2-1/R3-5.
- [ ] **Report std over seeds**, not bare means (collapsing seeds make means
  misleading). Should resolve once freeze-A lands.
- [ ] **Calibrate "close to centralized."** ~18–20pp DBpedia gap; keep the body
  honest and confirm freeze-A narrows it before finalizing wording.
- [ ] **Banking77 (77-class) number** — confirm it supports the coverage-gap
  limitation rather than undercutting "works across tasks."

## Tier 3 — polish / consistency

- [ ] Fix title typo: stray "ß" in `Fine-Tuningß`.
- [ ] Fill the comparison-table "ours" row with the real headline A\*.
- [ ] Cross-ref + label pass (cref targets, table/figure numbers).
- [ ] Hyperparameter / reproducibility note (LoRA rank, K, lr, seeds, datasets).
- [ ] Final privacy-spine consistency read end-to-end (abstract ↔ intro ↔
  method ↔ experiments ↔ conclusion).
- [ ] Scope-fit: TNSE flags generic FL+crypto; PIs decide venue (known risk).

## Pending data (gates Tier 1 fills)

- Colab E1 (head vs LoRA, 4 tasks) — partial: ag_news + dbpedia done; trec +
  banking77 pending (resume cell).
- VALAR `finetune_increment_e3` (N=10/20/50; N=100 dropped) + `_sweep`
  (e2/e4/e5/e1b) — running, ~24h on the one T4.
- Vision (CIFAR-100/ViT) — not yet run.
- FHE cost re-measurement for the LoRA payload — not yet run.
