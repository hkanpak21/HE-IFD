# fa04 — Byzantine-lite robustness via leave-one-out candidates (stage S7)

**Type:** AFK (compute + code). **Status:** 📥 OPEN. **Depends:** fa01.
**PRD:** `docs/prd/he-ifd-freeze-a-improvement.md` addendum §5. **Ops:** `CLAUDE.md`.

## Why

§Scope currently punts malicious clients to future work, and reviewers (R2-Q4) asked. The
multi-candidate machinery makes a *measured* Byzantine-lite defense nearly free: the server can
form all N leave-one-out aggregates at depth 1 (they are linear), clients threshold-decrypt the
N+1 candidates and vote on their local holdouts — a poisoned contribution shows up as the LOO
candidate whose exclusion wins the vote. Moves robustness from future-work to a small measured
subsection. No precedent found for this in MHE-FL (field scan 2026-06-10).

## Task

Add stage S7 to `jobs/finetune_improve.py` (and rebuild the notebook via
`notebooks/build_improve_nb.py`):

- Attack model: 1 of N=10 clients submits a crafted displacement — sweep {sign-flipped Δ,
  large-norm Gaussian, label-flipped training}. Honest-but-curious server, depth-1 only.
- Defense: form plain λ=1 aggregate + N leave-one-out aggregates; client-vote selection over all
  candidates on local holdouts (the existing `run_resumable`/vote machinery generalizes).
- Measure on dbpedia_14 + ag_news, 3 seeds: (a) accuracy of the poisoned plain aggregate,
  (b) accuracy of the vote-selected candidate, (c) whether the vote excluded the attacker.

## Acceptance criteria

- [ ] CSV with poisoned-plain vs vote-selected accuracy + attacker-identified flag per cell.
- [ ] Cost note: N extra candidate decryptions (linear, no extra HE depth) quantified for fa06.
- [ ] One paragraph + small table ready for the paper's robustness subsection; states the
      limitation honestly (single attacker, vote assumes honest majority of holdouts).

## Notes

- Keep the attacks simple and standard; this is "the protocol admits a cheap measured defense,"
  not a robust-aggregation paper.
