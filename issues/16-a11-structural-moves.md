# 16. A11 motivation move + future-directions move

Status: ready-for-agent
Label: AFK
Priority: P2 (mechanical .tex edits; no compute)
Action-plan: A11
PRD-section: §I-B / §V-F / §VI (paper structure)

## Parent

Action plan A11 (lines 420–446); resolves [R3-3] (motivation §II-C → §I-B) and [R3-6] (§V-F → §VI / §discussion).

## What to build

Two localised .tex restructurings called for in R3:

1. **Motivation move (R3-3).** Move the motivation paragraphs currently in §II-C ("Background") to §I-B ("Introduction → Motivation"). The advisor flagged motivation-too-late as a structural problem; the fix is to lift it earlier in the paper so the reader sees the *why* before the *what*.
2. **Future-directions move (R3-6).** Move §V-F ("Discussion of extensions") out of §V (Experiments) and into §VI (Discussion) or a dedicated §future-work section. Currently buried inside Experiments where reviewers miss it.

Both moves are mechanical: cut text from one section, paste into another, fix cross-references (`\ref{sec:motivation}` → `\ref{sec:intro_motivation}`, etc.), update the TOC if explicitly hand-managed.

Log both moves in `FL_TDSC/CHANGES.md` per the established before/after format.

## Acceptance criteria

- [ ] §II-C motivation paragraphs lifted to §I-B in `introduction.tex`.
- [ ] §V-F discussion moved to §VI / `conclusion.tex` (or a new file `discussion.tex` if cleaner).
- [ ] All `\ref{...}` / `\label{...}` cross-references in `*.tex` resolve.
- [ ] `pdflatex -interaction=nonstopmode FL_TDSC/main.tex` completes without `\ref` warnings (excluding pre-existing ones).
- [ ] `FL_TDSC/CHANGES.md` updated with two before/after entries.

## Blocked by

- Issue 01 (PRD-internal patches first so the rewriter has the corrected reference points).

## References

- Action plan A11 (lines 420–446), particularly R3-3 + R3-6 mappings.
- Memory: `feedback-paper-voice`, `feedback-changes-log`.

## Comments

(none yet)
