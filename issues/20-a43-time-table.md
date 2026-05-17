# 20. A4.3 time table (triple-axis Pareto: time axis)

Status: ready-for-agent
Label: AFK
Priority: P4 (companion to 19)
Action-plan: A4.3
PRD-section: §4.3 (HE depth budget per encrypted SGD step)

## Parent

Action plan A4.3 (lines 332–340).

## What to build

Same structure as issue 19, but for wall-clock per phase:

- **Ours wall-clock per phase:** from issue 14 (A3 single cell) + per-cell measurements in issue 18.
- **HE multi-round wall-clocks:** cited from each paper (no re-runs).
- **Plaintext comparators wall-clocks:** measured during issue 18.

**Honest-framing caption** per action plan A4.3 lines 336–338: "HE-IFD is order-of-magnitude slower than any plaintext one-shot baseline because of CKKS arithmetic overhead. The relevant comparison is against other HE-protected FL systems, where HE-IFD's one-shot design eliminates the multi-round bootstrap cascade and amortises the DKG cost across exactly one protocol execution."

**Output:**
- `results/A4_3_time_table.csv` and `.tex`.
- `\input{...}` reference from `experiments.tex`.

## Acceptance criteria

- [ ] Table covers all five method families.
- [ ] HE multi-round wall-clocks cited with bibkeys.
- [ ] Ours-α wall-clock per phase consistent with issue 14's measurements (within 30 % — single-cell vs grid-averaged is allowed to drift).
- [ ] Honest-framing caption present.
- [ ] `experiments.tex` updated.
- [ ] `FL_TDSC/CHANGES.md` logged.

## Blocked by

- Issue 14, Issue 18.

## References

- Action plan A4.3 (lines 332–340).
- PRD §4.3 (post-issue-01 patch, linear-accumulator terms).

## Comments

(none yet)
