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

### 2026-05-18 -- preflight gate scaffolding landed (wave-7 resubmission worker)

Owned files:

- `prototypes/preflight_a4sanity.py` -- orchestration-only Python (no torch /
  tenseal on login node; submits two sbatch jobs and polls).
- `jobs/preflight_a4sanity.sh` -- plain bash wrapper (not sbatch) that
  exec's the python script with `--`-prefixed args.

Invocation pattern (canonical, unattended):

```
nohup bash jobs/preflight_a4sanity.sh \
    --dataset MNIST --alpha 0.3 --seed 42 \
    > results/preflight_a4sanity.nohup.log 2>&1 &
disown
```

Direct python invocation (equivalent) for interactive runs:

```
python prototypes/preflight_a4sanity.py \
    --dataset MNIST --alpha 0.3 --seed 42 \
    [--comparator coboost|fedmd]   # default fedmd (smaller wall-clock)
    [--threshold-pp 2.0]           # gap threshold for halt
    [--timeout-sec 7200]           # max wait for both jobs (default 2h)
```

Polling cadence: `sacct -j <id> -X -n -P -o State` every 30 s until both
jobs reach a terminal state (`COMPLETED|FAILED|TIMEOUT|CANCELLED|OUT_OF_MEMORY|
NODE_FAIL|BOOT_FAIL|PREEMPTED|DEADLINE`) or `--timeout-sec` elapses. A
preflight-watchdog timeout is reported as the synthetic state
`TIMEOUT_PREFLIGHT` so it is distinguishable from a SLURM `TIMEOUT` (the job
itself blew its `--time=` budget).

gap_pp interpretation (PRD section 9.5.4 + action plan A4.4 lines 297-303):

- `gap_pp = (heifd_acc - comparator_acc) * 100`
- `gap_pp >= --threshold-pp` (default 2 pp): PASS -- A4.1 grid is safe to launch.
- `gap_pp < --threshold-pp`: FAIL -- HALT AND ESCALATE; user decides whether
  to pivot the contribution narrative or rethink resubmission.

Exit codes:

- `0`  PASS  -- `gap_pp >= threshold_pp`.
- `2`  FAIL  -- `gap_pp < threshold_pp`; escalate per PRD 9.5.4.
- `3`  INCONCLUSIVE -- at least one cell did not produce a usable accuracy
  (sbatch state != COMPLETED, or cell `status` != "success", or accuracy
  field missing). No verdict is rendered; the user must investigate.
- `1`  orchestration error (sbatch missing, scripts missing, argparse error).

JSON summary location: `results/preflight_a4sanity_<UTC-timestamp>.json`
(UTC stamp formatted `%Y%m%dT%H%M%SZ`). Always written, including on the
inconclusive path and on submission failures, so there is a permanent
record regardless of outcome. Contents: invocation args, both job_ids,
the sacct state for each, the full cell-result payloads, the parsed
accuracies, gap_pp (when defined), the verdict label
(`PASS|FAIL|INCONCLUSIVE|ERROR_SUBMIT`), and a human-readable diagnostic
for the inconclusive path.

Dependency: imports `prototypes.cell_schema.CellResult` lazily inside
`_load_cell_result_cls()`. If issue 14 has not landed `cell_schema.py` yet
the script still imports / `--help`s cleanly; a runtime `ImportError` with
a clear "owned by issue 14" message fires only when a cell JSON is parsed.
For backward compatibility with the existing comparator wrappers
(`cfd_v2_comp_fedmd.sh`, `cfd_v2_comp_coboost.sh`) which today write
`student_acc` / `final_student_acc` rather than the CellResult schema, the
parser falls back through those keys so the gate is usable end-to-end
even before issue 14 retrofits the comparators.

Not exercised in this scaffolding session: no `sbatch` was invoked; the
script was only smoke-tested via `--help` and `python -c "import ast;
ast.parse(...)"` under `he_ofl`. `bash -n jobs/preflight_a4sanity.sh`
also clean.

Issue NOT moved to `issues/done/` per coordination protocol -- scaffolding
only; actual preflight run is the next manual step once issues 14 and the
companion grid fanout (issue 18) have landed.

