# Documentation

| Directory | Contents |
|---|---|
| `paper/` | the manuscript: `main.tex`, `sections/`, `figures/`, `refs.bib` |
| `plan/` | what we intend to do: the paper rewrite plan and the PRDs |
| `design/` | design records, why a decision was made |
| `issues/` | task briefs for work not yet done |
| `notes/` | walkthroughs and session records |
| `archive/` | superseded, kept for provenance only |

Conventions: filenames are lowercase kebab-case, and carry a date only when the
file is itself a dated record. Figures are drawn in `paper/figures/drawio/` and
exported to PDF beside them.

Start at `plan/paper-rewrite.md`, which holds the current flow, the figure and
table standard, the voice rules, and the outstanding experiments.

**The paper is with the PIs on Overleaf as of 2026-08-02.** Do not edit
`paper/` without explicit direction. Local edits will diverge from the copy they
are reading.

The three notes that carry reasoning the paper compresses:

| file | what it holds |
|---|---|
| `notes/malicious-security.md` | why the strict functionality is unrealizable, the functionality that is realizable, and the two extensions that recover it |
| `notes/extraction-attack.md` | the attack, the four defence cases, and the two attacks that looked clever and were not |
| `notes/generation-scope.md` | how far the construction reaches past classification, per-token cost, and sampling under encryption |
