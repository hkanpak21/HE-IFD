# Ralph orchestrator

A port of [Matt Pocock's Ralph pattern](https://github.com/mattpocock/ai-engineer-workshop-2026-project/tree/main/ralph) adapted for this Python + Slurm research codebase. Ralph reads the issue tracker in `issues/`, picks the next ready AFK ticket, executes it, runs the appropriate feedback gates, commits, and either loops or halts.

## What Ralph does, per iteration

1. Loads the last 5 commits and every file in `issues/`.
2. Reads `ralph/prompt.md` to learn the priority order, feedback loops, golden rule, tweak protocol, and escalation triggers.
3. Picks the lowest-numbered AFK issue whose `Blocked by:` list is clear.
4. Explores, implements (using `/tdd` where code is involved), runs feedback gates, commits, and moves the issue file to `issues/done/`.
5. If all AFK issues are done, emits `<promise>NO MORE TASKS</promise>` and `afk.sh` exits.

## Invoking Ralph

```sh
./ralph/once.sh         # one iteration, interactive, accepts edits but prompts for shell
./ralph/afk.sh 10       # ten iterations, headless, fully autonomous
```

`once.sh` runs in `--permission-mode acceptEdits` and stays in the foreground — you watch each step and approve any bash invocation. Use this the first few times you run Ralph against a new prompt, and any time you change `prompt.md`.

`afk.sh` runs in `--dangerously-skip-permissions` and streams output via `jq`. It will edit files and run shell commands without asking. Read the safety note below before invoking it.

## Safety — read this before running `afk.sh`

The upstream Ralph runs inside `docker sandbox run claude .`, which isolates filesystem and network access. **This repo has no Docker sandbox.** `afk.sh` invokes the local `claude` binary with `--dangerously-skip-permissions`, which means Ralph can:

- write any file under `/scratch/hkanpak21/HE_IFD/`,
- run any shell command (including `sbatch`, `rm`, `git push`),
- read any file readable by your user.

Mitigations in this repo:

- The `GOLDEN RULE` section of `prompt.md` forbids login-node Python; CKKS / training / synthesis go through `sbatch` or `srun --partition=t4_ai`. A violation is an escalation trigger.
- Stable-core touches (PRD §9.5.1) halt Ralph instead of being applied.
- Every peripheral tweak must be logged to `reports/decision_log.md` and a per-tweak report under `reports/`.
- HITL-labelled issues are skipped — Ralph only advances AFK work.

If you are uncomfortable with the autonomy level, use `once.sh` instead and review every diff before approving.

## Issue tracker layout

```
issues/
├── 00-INDEX.md              # priority order, dependency graph, stable-core / escalation cross-refs
├── 01-prd-staleness-patch.md
├── 02-ralph-orchestrator-scaffold.md
├── ...
├── 28-a10-numbers-reconciliation.md
└── done/                    # completed issues land here
```

Each issue file has frontmatter:

```
Status: ready-for-agent
Label: AFK | HITL
Priority: P0 | P1 | P2
Action-plan: A<n>
PRD-section: §X
```

Ralph picks the lowest-numbered file whose `Label:` is `AFK` and whose `Blocked by:` list contains no issue still in `issues/` (i.e. all blockers have moved to `issues/done/`).

## Adding a new issue

1. Pick the next free integer; create `issues/<NN>-<short-slug>.md`.
2. Use the frontmatter above. Set `Status: ready-for-agent` only when the spec is concrete enough for an agent to start.
3. Add a row to `issues/00-INDEX.md` in priority order. Update the `Blocked by` column.
4. If the new issue blocks something already in flight, edit that issue's `Blocked by` line.

## Where things live

- Priority + dependency graph: `issues/00-INDEX.md`.
- Tweak protocol + escalation triggers: PRD §9.5 in `reports/2026-05-05_methodology_pivot.md`.
- Append-only tweak ledger: `reports/decision_log.md`.
- Paper-edit log: `FL_TDSC/CHANGES.md` (every `.tex` change goes here as before/after).
- Slurm cheatsheet: the `valar` memory under `~/.claude/projects/-scratch-hkanpak21/memory/`.

## Why the divergence from upstream

The upstream Ralph (TypeScript workshop project) uses `npm run test` / `npm run typecheck` for feedback loops and `docker sandbox run claude .` for isolation. Neither applies here — this is a Python research repo on a Slurm cluster with no Docker. The feedback loops have been replaced with the equivalents for this stack (`pytest`, `pdflatex`, `xmllint`, `srun python -c "import tenseal"`) and the sandbox has been replaced by the GOLDEN RULE plus escalation triggers. The control flow (`afk.sh` loop with stream-json + `jq`, `<promise>NO MORE TASKS</promise>` termination) is unchanged.
