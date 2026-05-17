# 27. A12 pruning ablation — depends on Kerem meeting

Status: ready-for-human
Label: HITL
Priority: P5 (advisor-flagged; gated on Kerem session)
Action-plan: A12
PRD-section: §discussion (potential)

## Parent

Action plan A12 (lines 436–446) + §5 "The 'Pruning? discuss with Kerem' question" (lines 517–520).

## What to build

The advisor's only authored technical suggestion is "Pruning? discuss with Kerem." Two readings per action plan §5:

1. **Block-wise reading (retired by the pivot).** Pruning the polynomial student attacks magnitude-explosion. Mostly retired by the pivot.
2. **CFD reading (current paper).** Pruning could:
   - Shrink the encrypted-student download (modest savings).
   - Reduce per-step depth budget via structured sparsity (channel / block pruning since CKKS has no native sparse primitives).
   - Post-decryption client-side compression per Phase 5.

**HITL action: schedule a Kerem (Küpçü) session** to clarify which reading the advisor intended. Outcome determines AFK follow-up:

- **If reading (1):** Cover letter response — "magnitude-explosion challenge is retired by the pivot; pruning is no longer load-bearing." No experimental work; close this issue.
- **If reading (2a/c):** Add a short paragraph in §discussion / §extensions + a single ablation cell (LeNet-5 student at 50 % structured channel pruning, MNIST α=0.3, plaintext only). Spawn a follow-up AFK issue at that point.

## Acceptance criteria

- [ ] Kerem session scheduled and notes recorded in `reports/2026-MM-DD_kerem_pruning_meeting.md`.
- [ ] Reading-(1)-vs-(2) decision documented in `reports/decision_log.md`.
- [ ] If (1): cover letter paragraph drafted; this issue moved to `issues/done/`.
- [ ] If (2): follow-up AFK issue spawned for the single ablation cell; this issue moved to `issues/done/`.

## Blocked by

- Kerem session scheduling (human action; week 1 prerequisite per action plan §0).

## References

- Action plan A12 (lines 436–446), §5 "Pruning? discuss with Kerem" (lines 517–520).

## Comments

(none yet)
