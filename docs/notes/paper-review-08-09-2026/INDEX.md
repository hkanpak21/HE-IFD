# TNSE review panel, 2026-09-08

Run with `academic-paper-reviewer` v1.11.1 in `full` mode, five seats plus an
editorial synthesizer, on `docs/paper/main.pdf` at commit 301d7a2. The skill is
installed at `.claude/skills/academic-paper-reviewer/`, which is gitignored.

**Decision: Major Revision, with re-review.** Four seats said Major Revision.
The Devil's Advocate said Reject. Twelve blocking items, thirty should-fix,
fourteen optional. Eight of the twelve blockers need only writing or moving
text the authors have already written, and none needs a new run to clear the
blocking standard.

## Read in this order

| file | what it is |
|---|---|
| `07-EDITORIAL-DECISION.md` | start here. Decision, consensus table, adjudication of every Devil's Advocate CRITICAL, the disagreements and their rulings, and the roadmap |
| `06-VERIFICATION-MEMO.md` | the eight claims the editor checked against the manuscript directly, and the one place the panel was wrong |
| `05-devils-advocate.md` | the strongest case against the paper, five CRITICALs |
| `03-domain.md` | the cryptography, sixteen findings, one CRITICAL |
| `02-methodology.md` | experimental design, twelve major findings |
| `04-perspective.md` | deployment and operability |
| `01-journal-fit.md` | venue fit and originality |
| `00-PANEL-CONFIGURATION.md` | how the five seats were configured and what rules bound them |
| `BRIEF.md` | what every seat was told |
| `SUBMISSION.txt`, `TECHNICAL-REPORT.txt` | the extracted text the panel read |

## What the panel converged on

Every seat found load-bearing material that lives in the technical report and
was cut from the ten pages. The editor verified eight such omissions. The
pattern, rather than any single defect, is what set the decision.

Three items are already recorded in `CLAUDE.md` as deliberate deferrals: the
smudging discussion, the selection cost measured under collective refresh, and
the hard-label claim. The panel did not know that and flagged them anyway,
which is the useful result. A referee holding ten pages does not know the
reasoning either.

## The one number the panel could not have known

Blocking item B5, the missing `A_sel` column in Table I, was introduced on
2026-09-06 when the per-seed sentence was deleted from that caption and the two
values were not given a new home. The caption fix was correct. Dropping the
numbers was not.

## Caveat on the method

The five seats were dispatched in parallel with no shared state. That is role
separation, not independence: they share a model family and a prompt lineage,
and correlated blind spots are expected. Two seats made the same factual error
about `A_sel` being untabulated, which is what such correlation looks like.
