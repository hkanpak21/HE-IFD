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

### 2026-05-17 — A11 R3-3 + R3-6 structural moves landed (worker, wave 5b)

Both R3 mechanical moves complete. Figure-replacement portion of A11 (R3-4) was already out of scope for this issue and is being landed by separate issues.

**Move 1 (R3-3).** Source `FL_TDSC/background.tex:68-75` (the three `\par\noindent\textbf{Motivation for One-Shot Communication and Homomorphic Encryption.}` paragraphs marked with the dead commented-out `% \label{sec:bg_motivation}`). Target `FL_TDSC/introduction.tex:15-22` as a new `\subsection{Motivation}\label{sec:intro_motivation}` placed BEFORE `\subsection{Our Approach}` (the issue-17-finalised subsection at post-edit `:24`). The §I structure now renders as §I-A Motivation, §I-B Our Approach, §I-C Contributions per LaTeX auto-numbering — placement choice (before vs after §I-A) explained in the sidecar's "voice/structural decisions" block. The dead `sec:bg_motivation` label had four references in `FL_TDSC/*.tex`, all in commented-out legacy blocks, so it was retired without any live `\ref` rename. Forward-references from the moved-in paragraphs to `sec:bg_he_fl`, `sec:bg_server_inference`, `sec:ckks_prelim` still resolve at the second pdflatex pass (main.tex includes introduction.tex before background.tex).

**Move 2 (R3-6).** Source `FL_TDSC/experiments.tex:136` (the `\textbf{Future directions.}` paragraph at the end of §V-F "Encrypted Arithmetic Feasibility"). Target `FL_TDSC/conclusion.tex:17-18` placed adjacent to but BEFORE the issue-26 malicious-clients out-of-scope paragraph at post-edit `:20`. Conclusion's future-work region now reads in-scope (line 15) → extensions (lines 17-18) → out-of-scope (line 20). A bare `\label{sec:conclusion_extensions}` anchors the moved paragraph; no `\subsection` was introduced because §VI is a single un-subdivided section. The other three §V-F paragraphs (`\textbf{Numerical precision}`, `\textbf{SIMD packing}`, `\textbf{Multiplicative depth}` at pre-edit lines 130-134) remain in place because they describe genuine measurement results, not forward-looking discussion. The `\label{sec:ckks_validation}` is preserved (referenced from `experiments.tex:7`).

**Prose modification.** One pointer fix: the source paragraph in Move 1 contained the phrase "as shown above", which anchored on the adjacent §II-B inference-attack discussion. After the move, "above" would mis-point to the §I preamble. Retargeted to `Section~\ref{sec:bg_server_inference}` (the canonical label for that discussion). All other prose carried byte-verbatim.

**Acceptance gate.** All seven self-check boxes pass:
- §II motivation paragraphs lifted into §I-B (LaTeX renders as §I-A Motivation).
- §V-F future-directions paragraph moved to §VI; other §V-F measurement paragraphs preserved.
- All `\ref{sec:*}` in `FL_TDSC/*.tex` resolve to a live `\label{sec:*}` (cross-tally script reports zero orphans).
- Balanced braces in all four touched files: `introduction.tex` 109/109, `background.tex` 337/337, `experiments.tex` 512/512, `conclusion.tex` 17/17 (pre- and post-edit difference matches the lifted prose).
- No double-removal of motivation paragraph: 1 live instance in `introduction.tex`, 0 in `background.tex`/`experiments.tex`/`conclusion.tex` (three `%`-prefixed residues in `background.tex` legacy-rewrite blocks have no compile impact).
- No double-insertion of future-directions paragraph: 1 live instance in `conclusion.tex`, 0 elsewhere.
- Issue-17 §I-A "Our Approach" prose at `introduction.tex:24-35` untouched; issue-26 malicious-clients paragraph at `conclusion.tex:20` untouched.

**Sidecar.** `.agent-output/16-changes.md` (123 lines, 20 KB) ready for orchestrator merge as `FL_TDSC/CHANGES.md` §14. Two before/after entries (one per move), each with file:line-range header for both source and target, plus voice/structural decisions and syntactic-check evidence.

**Compile gate.** Not run — cluster pdflatex.fmt missing per `ralph/prompt.md`. Syntactic checks substituted (brace balance + cross-reference tally as above).

Status: ready for orchestrator to merge sidecar and move issue to `issues/done/`.
