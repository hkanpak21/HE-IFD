# 21. A7 post-release MIA against the decrypted student

Status: ready-for-agent
Label: AFK
Priority: P4 (security check; downstream of grid)
Action-plan: A7
PRD-section: §2.4 (SQ-floor on released student)

## Parent

Action plan A7 (lines 376–390) — locked 2026-05-10.

## What to build

Per cell of issue 18's headline grid (360+ cells) + the 48-cell N-ablation, run two membership inference attacks on the decrypted student and report AUC:

- **LiRA** (Carlini et al. 2022, `carlini2022membership`) — the field-standard individual-record attack.
- **Loss-threshold** (Yeom et al. 2018, `yeom2018privacy`) — the simplest baseline.

This pair was canonical in the rejected paper's training-time MIA; applying it post-decryption keeps the methodology internally consistent.

**Population MIA** (Ye et al., arXiv:2111.09679) as a single-cell ablation on CIFAR-10 α=0.1 N=10. Add to `references.bib` if not present.

**Output:**
- `jobs/mia_lira.sh`, `jobs/mia_loss_threshold.sh` sbatch wrappers.
- `results/mia/<dataset>_<variant>_<alpha>_<seed>_lira.json` and `_lossthr.json` per cell.
- Consolidated `results/A7_mia_auc_table.csv` and `.tex`.
- New §V subsection in `experiments.tex` reporting AUC.

**Compute** per action plan A7 line 387: ≈ 1 day on top of A4.

## Acceptance criteria

- [ ] LiRA + loss-threshold AUC measured per cell of issue 18's scope.
- [ ] Population MIA single-cell ablation on CIFAR-10 α=0.1 N=10.
- [ ] `references.bib` has all three MIA references.
- [ ] §V MIA subsection added to `experiments.tex`.
- [ ] `FL_TDSC/CHANGES.md` logged.
- [ ] No login-node execution.

## Blocked by

- Issue 18 (need decrypted students from grid cells).

## References

- Action plan A7 (lines 376–390).
- PRD §2.4 (SQ-floor framing, lines 53–63).
- Bibkeys: `carlini2022membership`, `yeom2018privacy`.

## Comments

(none yet)
