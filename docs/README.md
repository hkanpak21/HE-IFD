# Documentation

| Directory | Contents |
|---|---|
| `paper/` | the manuscript. Two documents from one source, see below |
| `plan/` | the two PRDs, both with stale headers and both read for reasoning rather than for what to do next |
| `notes/` | the live plan and the PI review |
| `notes/PI_notes/` | every PI comment, why it was made, and the replacement text agreed. Read before editing any section it covers |
| `design/` | design records, why a decision was made |
| `issues/` | task briefs for work not yet done |
| `archive/` | superseded, kept for provenance only, never mined for methodology |

## Start here

`notes/plan-submission-2026-08-23.md` is the live plan. It holds the goal, the
nine gates, the page budget measured off the compiled PDF, the thirteen work
items and what is left.

`CONTEXT.md` is the terminology ledger. One name for one thing, each entry dated
and attributed. Read it before writing a sentence.

`paper/notation-and-terms.md` is where a symbol is looked up. The submission does
not print a notation table, because the table moved to a report-only block on
2026-08-23.

## The paper is two documents from one source

| file | what it is |
|---|---|
| `paper/main.tex` | the TNSE submission, `\submissiontrue`, ten printed pages |
| `paper/main-tr.tex` | the arXiv technical report, `\submissionfalse`, no limit |
| `paper/sections/` | everything else, shared by both |

`\paperonly{...}` and `\tronly{...}` switch content. `\trsee{sec:x}` points the
submission at a section of the report. Both documents carry the same seven
top-level sections in the same order, so a pointer names a section and never a
subsection, and `scripts/check_split.py` enforces that.

Run `bash scripts/gates.sh` before sending anything. Nine gates: length,
prose budget, nothing rewritten in either view, the two documents agreeing,
the bibliography, both compiling clean, the voice linter, the figure text at
the caption size, and the arXiv placeholder that must not survive submission.

## Conventions

Filenames are lowercase kebab-case and carry a date only when the file is itself
a dated record. Figures are drawn in `paper/figures/drawio/` and exported to PDF
beside them, at a font size calibrated with `paper/figures/figfont.py` so the
text lands at the caption size with no width option at include time.

## Where the reasoning the paper compresses now lives

The three notes that used to be listed here moved to `notes/archive/` on
2026-08-21, and most of what they held is in the technical report, which prints
the proofs, the full extraction study, the communication model and the full
survey. Read `main-tr.pdf` first and the archived notes only for provenance.
