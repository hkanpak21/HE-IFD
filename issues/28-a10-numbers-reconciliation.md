# 28. A10 numbers reconciliation pass (week 14)

Status: ready-for-human
Label: HITL
Priority: P5 (downstream gate; > 3 pp Δ → halt-and-diagnose)
Action-plan: A10 numbers freeze + replacement protocol
PRD-section: §10 item 6, §9.5.4 escalation triggers

## Parent

Action plan A10 "Numbers freeze + replacement protocol" (lines 420–230) — specifically the week-14 replacement check.

## What to build

After issue 18 (A4.1 grid) lands its 2026-07-01 partial results (MNIST α=0.3 + CIFAR-10 α=0.3 ours-row + mean-teacher), compare the live numbers against issue 17's May-5 working text in the abstract:

- MNIST α=0.3: 0.965 student vs 0.81 mean teacher.
- CIFAR-10 α=0.3: 0.521 vs 0.408.

**Replacement diff rule per action plan A10 lines 226–229:**

- **|Δ| ≤ 1 pp** on both ratios → keep May-5 text; footnote "consistent with our re-run at 100-epoch teachers."
- **1 pp < |Δ| ≤ 3 pp** → silently update abstract to A4.1 numbers; no narrative change.
- **|Δ| > 3 pp** → **STOP and diagnose**. Per PRD §9.5.4: "Number divergence > 3 pp from A10's working text" is an explicit escalation trigger. Likely root cause: epoch-100 teacher overfitting in non-IID, or hyperparameter drift in the re-implementation.

Why HITL: the > 3 pp branch is a halt-and-decide gate. The ≤ 3 pp branches can be automated, but a human should sign off the abstract update before it ships in week 14.

**Output:**
- `reports/2026-MM-DD_a10_reconciliation.md` with before/after numbers + decision.
- One-line entry in `reports/decision_log.md`.
- If ≤ 3 pp: PR or commit to `introduction.tex` / `main.tex` updating abstract.
- If > 3 pp: escalation note + halt.

A second reconciliation pass at 2026-08-01 (end-week 12, full A4.1 consolidation) follows the same protocol.

## Acceptance criteria

- [ ] Reconciliation report exists with the live and working-text numbers side by side.
- [ ] Decision logged (keep / silent update / halt).
- [ ] If halt: PRD §9.5.4 escalation triggered; downstream issues paused.
- [ ] Decision log appended.

## Blocked by

- Issue 18 (grid produces the live numbers).
- Issue 17 (the May-5 working text exists in the abstract for comparison).

## References

- Action plan A10 "Numbers freeze + replacement protocol" (lines 420–230).
- PRD §9.5.4 (escalation triggers, lines 334–346).

## Comments

(none yet)
