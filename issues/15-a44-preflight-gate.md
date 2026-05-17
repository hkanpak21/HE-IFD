# 15. A4.4 paper-existential pre-flight gate (A4-sanity)

Status: ready-for-agent
Label: AFK
Priority: P3 (gates 18; cheap; < 1 % of A4 compute)
Action-plan: A4.4 / A4-sanity
PRD-section: §6 (warm-start), §7 (ablations A1, A2)

## Parent

Action plan A4.4 (lines 280–316).

## What to build

Single A4-cell pre-flight on `t4_ai` (sbatch only — golden rule):

- **Cell:** MNIST, α=0.3, N=10, 1 seed (seed=42 to match May-5).
- **Two variants:**
  - α-warmstart (full CFD with encrypted ensemble target $\widetilde Y$).
  - α-warmstart-no-ensemble (Stage 2 = plaintext SGD on $(\mathcal{P}, y_\mathcal{P})$ only, no encrypted teacher signal — PRD §6.3 ablation A2).
- **Both at 100-epoch teachers** (matching Co-Boosting's reported teacher budget per action plan A4.1).
- **Student schedule:** 30 warm-start epochs + 200 distillation epochs per PRD §7.2.
- **Compute:** half a day on a single T4.

**Output:**
- `jobs/cfd_preflight.sh` sbatch wrapper.
- `results/preflight_<job_id>.json` with the two variants' final student accuracies.
- One-page report at `reports/2026-MM-DD_preflight_a4sanity.md` documenting Expected / Observed / Decision.

**Decision rule per PRD §9.5.4 + action plan A4.4 lines 297–303:**

- **Gap ≥ 5 pp** (α-warmstart wins by 5 pp or more) → proceed with confidence; A4.1 full grid launches (issue 18 unblocked).
- **2 pp ≤ gap < 5 pp** → proceed but flag in issue 17 (A10 abstract) that the headline framing emphasises non-IID / α=0.05 regime where the gap is widest.
- **Gap < 2 pp** → **HALT.** This is an explicit PRD §9.5.4 escalation trigger ("A4-sanity gate failure (gap < 2 pp; per §A4.4 of action plan)"). Ralph must produce the tweak report, escalate, and stop. The user convenes a planning session: pivot contribution narrative or rethink resubmission.

A4.4 is the single most likely way the 26-week plan derails; cost of the gate is < 1 % of A4.1's compute budget.

**Note on labelling:** This issue is AFK per the user's call (issue can run to completion unattended), but if the gap < 2 pp the *next* action is an escalation that requires human input. Ralph halts on the < 2 pp condition.

## Acceptance criteria

- [ ] `jobs/cfd_preflight.sh` exists, partition=t4_ai.
- [ ] Run completes; both variants converge.
- [ ] `results/preflight_<job_id>.json` contains the two accuracies + gap.
- [ ] `reports/2026-MM-DD_preflight_a4sanity.md` exists with Expected / Observed / Decision sections.
- [ ] One-line entry appended to `reports/decision_log.md`.
- [ ] If gap < 2 pp: Ralph writes an escalation note and exits with `<promise>NO MORE TASKS</promise>` (or equivalent).
- [ ] If gap ≥ 2 pp: issue 18 is unblocked.
- [ ] No login-node execution.

## Blocked by

- Issue 04 (TenSEAL smoke validates the protocol primitives first).
- Issue 13 (methodology rewrite — so the preflight references the correct protocol description).

## References

- Action plan A4.4 (lines 280–316).
- PRD §6 (lines 188–209), §7.2 (lines 215–230), §9.5.4 (lines 334–346).

## Comments

(none yet)
