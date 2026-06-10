# fa01 — Run the improvement program (S1–S6) and write the decision memo

**Type:** AFK (compute) + user-run Colab. **Status:** 📥 OPEN. **Blocks:** fa02–fa08 partially.
**PRD:** `docs/prd/he-ifd-freeze-a-improvement.md`. **Ops:** `CLAUDE.md`.

## Task

Execute the staged program in `notebooks/improve_program.ipynb` (Colab, primary) or
`sbatch jobs/finetune_improve.sh` (VALAR, array index = stage s1–s5; s6 vision is notebook-only).
Collect each section's CSV into `results/finetune_improve/<section>.csv`.

## Acceptance criteria

- [ ] S1 (freeze-A vs both-A-B, ag_news + trec, 3 seeds): per-config seed std reported; verdict on
      whether freeze-A removes the collapses (ag_news s44, trec s43).
- [ ] S2 (semantic init, 4 tasks): banking77 A0 (zero-shot floor) and Astar/acc_counthead vs the
      sem_init=0 baseline; verdict on whether semantic init joins the headline method.
- [ ] Candidate columns analyzed across all cells: does any of {fisher, count_head, λ<1} beat
      plain λ=1, where, and does the client-vote `selected` track the test-best candidate?
- [ ] S4/S5 fix K, lr, r for the headline config. S3 runs only if S1 leaves instability.
- [ ] S6 (CIFAR-100/ViT): positive increment or the modality claim is flagged for removal.
- [ ] A short decision memo appended to `results/finetune_improve/README.md`: winning config
      (freeze_a / sem_init / agg rule / λ-rule / K / lr / r), to be consumed by fa02–fa06.

## Notes

- Per-cell JSONs make every stage resumable; a 3h VALAR kill or Colab disconnect costs one cell.
- VALAR prefetch on the login node first: roberta-base + ag_news/dbpedia_14/trec/banking77.
