# 02. Ralph orchestrator scaffold

Status: ready-for-agent
Label: AFK
Priority: P1 (infrastructure; unblocks 04, 06-10, 22, 25)
Action-plan: infra (no Ax mapping)
PRD-section: §9.5 (adaptive execution governs Ralph's behaviour)

## Parent

Reference: [Matt Pocock workshop Ralph pattern](https://github.com/mattpocock/ai-engineer-workshop-2026-project/tree/main/ralph). Three files in the upstream `ralph/` directory: `prompt.md`, `afk.sh`, `once.sh`.

## What to build

Port the Ralph orchestrator to this repo, adapted for a Python + sbatch research codebase (the upstream is TypeScript: `npm run test`, `npm run typecheck`). Create `ralph/` at repo root containing:

1. **`ralph/prompt.md`** — Adapted from upstream:
   - Task-selection priority replaced by HE-IFD's priority order: critical bugfixes → PRD staleness fixes → text/figure deliverables that unblock the cover letter → prototypes → compute-heavy grid. The full priority list lives in `issues/00-INDEX.md`; the prompt references it rather than restating it.
   - "AFK issues only, not HITL" rule kept verbatim — Ralph reads the `Label:` line in each issue's frontmatter.
   - Exploration step kept.
   - Implementation step uses `/tdd` where applicable (text-only and config slices skip it).
   - **Feedback loops** replaced with the project's actual gates:
     - `pytest prototypes/ -q` if Python code touched.
     - `srun --partition=t4_ai --account=comx29 --time=00:05:00 python -c "import tenseal"` if a CKKS-touching change.
     - Latex compile check (`pdflatex -interaction=nonstopmode FL_TDSC/main.tex` then revert artefacts) if a `.tex` touched.
     - SVG validity check (`xmllint --noout FL_TDSC/figures/<file>.svg`) if a figure touched.
   - **Commit message** kept verbatim from upstream.
   - **Issue completion** rule kept: move issue file to `issues/done/` on completion.
   - Add an explicit GOLDEN RULE: every Python invocation that opens a CKKS context, runs training, or generates synthetic data goes through `sbatch` or `srun --partition=t4_ai`. **Never login-node.** (action plan §0 + memory `valar`)
   - Add an explicit "Tweak protocol" section pointing at PRD §9.5.3: any peripheral adjustment must produce `reports/2026-MM-DD_tweak_<slug>.md` + a one-line entry in `reports/decision_log.md`.

2. **`ralph/afk.sh`** — Adapted from upstream `afk.sh`:
   - Replace `docker sandbox run claude .` with a local invocation (this repo has no Docker sandbox available).
   - Inject `cat issues/*.md` (Ralph's task input) — already matches upstream literal.
   - Loop iteration count taken as `$1` per upstream.
   - Termination on `<promise>NO MORE TASKS</promise>` per upstream.

3. **`ralph/once.sh`** — Single-iteration variant per upstream.

4. **`reports/decision_log.md`** — Created with header per PRD §9.5.6 template; initially empty (no tweaks logged yet).

5. **`ralph/README.md`** — One-screen orientation: what Ralph does, how to invoke (`./ralph/once.sh` or `./ralph/afk.sh <N>`), where issues live, how to interpret AFK vs HITL labels, how to add a new issue.

## Acceptance criteria

- [ ] `ralph/prompt.md`, `ralph/afk.sh`, `ralph/once.sh`, `ralph/README.md` exist and are executable where appropriate.
- [ ] `ralph/prompt.md` references `issues/00-INDEX.md` for priority order and PRD §9.5 for tweak / escalation protocol.
- [ ] `reports/decision_log.md` exists with the §9.5.6 header.
- [ ] `ralph/afk.sh` works end-to-end on a test invocation that picks issue 26 (no blockers; smallest text-only slice) — verified by user, not automated.
- [ ] `FL_TDSC/CHANGES.md` is not touched by this issue (no paper edits).

## Blocked by

None — can start immediately.

## References

- Upstream: `https://github.com/mattpocock/ai-engineer-workshop-2026-project/tree/main/ralph`.
- PRD §9.5 (adaptive execution methodology, lines 285–375).
- Action plan §0.05 (adaptive execution restatement) and §0 (golden rule).
- Memory: `feedback-adaptive-execution`, `valar`.

## Comments

(none yet)
