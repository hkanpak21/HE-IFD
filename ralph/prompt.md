# ISSUES

Local issue files from `issues/` are provided at start of context. Parse them to understand the open issues.

You will work on the **AFK** issues only, not the HITL ones. Read the `Label:` line in each issue's frontmatter; if it is not `AFK`, skip it. HITL issues need human input and are not yours to advance.

You've also been passed a file containing the last few commits. Review these to understand what work has already been done.

If all AFK tasks are complete, output `<promise>NO MORE TASKS</promise>`.

# TASK SELECTION

`issues/00-INDEX.md` is the authoritative priority order. Pick the **lowest-numbered AFK issue whose `Blocked by:` list is fully cleared** (i.e. every blocker has been moved to `issues/done/`). Do not skip ahead.

The index encodes this priority ladder, used to settle ties when blockers permit either branch:

1. PRD-internal staleness fixes (issue 01) — unblock the largest fan-out.
2. Infrastructure (issue 02 — this orchestrator) — unblock everything else.
3. Text-only and figure-only slices that feed the cover letter (05, 11, 12, 13, 16, 17, 26).
4. Prototype work that calibrates the headline grid (04, 14, 22, 25).
5. Compute-heavy vendor reproductions (06–10).
6. The headline accuracy grid (18) and its post-hoc tables / attacks (19, 20, 21, 24).

Tracer-bullet rule still holds: prefer a thin end-to-end slice over a wide refactor.

# EXPLORATION

Explore the repo. At minimum, read the PRD section the issue cites (`PRD-section:` line) and the action-plan section (`Action-plan:` line). Skim `FL_TDSC/CHANGES.md` to see how prior paper edits were logged. If the issue touches code, read the surrounding module before editing.

# IMPLEMENTATION

Use `/tdd` when the issue produces executable code (prototypes/, training scripts, evaluation harnesses). Skip `/tdd` for pure text edits (`.tex`, `.md`), pure figure edits (`.svg`), and one-shot config tweaks — there is nothing to red-green for those.

# GOLDEN RULE — never run heavy work on the login node

Any Python invocation that opens a CKKS context, runs training, generates synthetic data, evaluates a model, or imports `tenseal`/`torch.cuda` goes through `sbatch` or `srun --partition=t4_ai --account=comx29`. **Never on the login node.** This is enforced by §0 of the action plan and by the `valar` memory. A login-node violation is an escalation trigger (PRD §9.5.4); halt and tell the user.

For quick sanity checks (≤ 5 min, ≤ 1 GPU), prefer `srun --partition=t4_ai --account=comx29 --time=00:05:00 --gres=gpu:1 python -c "..."`. For longer work, write a job script under `jobs/` and submit with `sbatch`.

# FEEDBACK LOOPS

Run the gates that apply to what you touched. Run them **before** the commit, not after.

- **Python code touched** (any file under `prototypes/`, `jobs/`, or a new `.py`):
  `pytest prototypes/ -q`
- **CKKS-touching change** (anything that imports `tenseal` or uses a multiparty-CKKS context):
  `srun --partition=t4_ai --account=comx29 --time=00:05:00 python -c "import tenseal; print(tenseal.__version__)"`
  followed by whatever smoke the issue specifies.
- **`.tex` file touched** (anything under `FL_TDSC/`):
  `cd FL_TDSC && pdflatex -interaction=nonstopmode main.tex >/dev/null` then revert the build artefacts (`rm -f main.aux main.log main.out main.toc main.bbl main.blg`). Confirms the paper still compiles. Also append a before/after entry to `FL_TDSC/CHANGES.md` per the `feedback-changes-log` memory.
- **SVG file touched** (anything under `FL_TDSC/figures/*.svg`):
  `xmllint --noout FL_TDSC/figures/<file>.svg`
  and re-export the matching `.pdf` via `rsvg-convert --format=pdf -o <file>.pdf <file>.svg` if the issue commits both.

If a gate fails, fix the cause; do not skip it.

# TWEAK PROTOCOL — peripherals only

Per PRD §9.5.2, you may adjust **peripherals** (probe size, β, λ, epoch budget, seed count, sbatch chunking, library choice, etc.) without asking. For every tweak you apply:

1. Write `reports/2026-MM-DD_tweak_<short-slug>.md` with the five fields from PRD §9.5.3 (motivation, tweak, expected effect, fallback, cross-references).
2. Append a one-line entry to `reports/decision_log.md` in the §9.5.6 format.

Per PRD §9.5.1, you must **never** touch the stable core (binding invariant, multiparty CKKS at $t=N$, linear-accumulator construction, α/γ variant boundaries, $\log N \in \{14, 15\}$, scale $\approx 2^{40}$) without halting and asking the user.

# ESCALATION TRIGGERS — halt immediately

Per PRD §9.5.4, halt and report instead of continuing if any of these fire:

- Proposed change to the stable core (§9.5.1).
- Compute overrun > 50 % vs the issue's stated budget.
- Critical-path slip > 1 week.
- A4-sanity gap < 2 pp (issue 15's gate).
- > 3 pp divergence from the working numbers in `reports/cover_letter_draft.md` §3 (issue 28).
- Both tier-1 DP comparators (FedKT and FedDiff under DP) fail to reproduce.
- Linear-accumulator gradient-norm divergence > 5 % vs plaintext baseline.
- Any login-node violation of the GOLDEN RULE.

When you halt, leave a `Comments` entry in the issue file describing what fired and what you observed, then stop.

# PAPER VOICE

Edits under `FL_TDSC/*.tex` must match the existing register: austere theoretical prose, sceptical-professor reader, no doc-flavour. Anchor on `FL_TDSC/methodology.tex:21` if uncertain. See the `feedback-paper-voice` memory.

# COMMIT

Make a git commit. The commit message must:

1. Include key decisions made.
2. Include files changed.
3. Blockers or notes for next iteration.

# THE ISSUE

If the task is complete, move the issue file to `issues/done/`.

If the task is not complete, add a note under the `## Comments` section of the issue file describing what was done and what remains.

# FINAL RULES

ONLY WORK ON A SINGLE TASK.
