# 13. A1 wholesale methodology rewrite (replace methodology.tex §3 onwards)

Status: ready-for-agent
Label: AFK
Priority: P2 (the methodology section reviewers will read; large but mechanical)
Action-plan: A1
PRD-section: §1 (motivation), §4 (protocol)

## Parent

Action plan A1 (lines 193–199) + PRD deprecation note at lines 8–10 ("the PRD wins").

## What to build

Wholesale replacement of `FL_TDSC/methodology.tex` §3 onwards with PRD §4 content. The PRD's "Deprecation note for downstream builder LLMs" (lines 8–10) is explicit: the existing `methodology.tex` describes the **block-wise HE-IFD** protocol; that content is deprecated; do not propagate block-wise terminology, per-block ciphertext upload, bridge construction, or magnitude-regularisation loss.

**Specifically replace:**

1. **§methodology §3 onwards** with PRD §4 (Encrypted CFD protocol):
   - §4.1 phase table (DKG → key-switch).
   - §4.2 β / λ secure handling (un-normalised aggregation + temperature absorption; uniform-weight per-row variance).
   - §4.3 HE depth budget per encrypted SGD step (in the **linear-accumulator** terms set by issue 01's patch).
2. **§6 Two-stage initialisation** from PRD §6 (variant α only).
3. **§5 Communication complexity** from PRD §5.
4. **Operator-replacement / magnitude-regularisation discussion** dropped per the PRD deprecation note.

**Voice** per memory `feedback-paper-voice`: austere theoretical register, sceptical-professor reader, no documentation-flavoured prose.

**CHANGES.md logging:** Wholesale replacement is logged as a single bulk-replacement entry in `FL_TDSC/CHANGES.md` per PRD §9 item 6, with a pointer to PRD §4 as the authoritative new content. Memory `feedback-changes-log` requires every edit be appended in before/after form for Overleaf replay; for a wholesale replacement, the "before" is "see git HEAD~1:methodology.tex §3 onwards" and the "after" is "see PRD §4 + the new methodology.tex content".

## Acceptance criteria

- [ ] `methodology.tex` §3 onwards mirrors PRD §4 + §5 + §6 in the paper's prose register.
- [ ] No block-wise terminology remains (no "per-block ciphertext," "bridge construction," "magnitude regularisation," "$K{+}1$ block boundaries").
- [ ] §4.3 reads in linear-accumulator terms (presupposes issue 01 has patched the PRD).
- [ ] Operator-replacement details moved out (only the "released student inference compatibility" framing per A8 R2-Q6 paragraph survives).
- [ ] `pdflatex -interaction=nonstopmode FL_TDSC/main.tex` completes; `methodology.tex`'s new content parses.
- [ ] `FL_TDSC/CHANGES.md` updated with the bulk-replacement entry per PRD §9 item 6.

## Blocked by

- Issue 01 (PRD §4.3 must read in linear-accumulator terms before quoting into the paper).
- Issue 05 (A8 threat-model rewrite — methodology.tex §threat-model is upstream of methodology §3 in the file; the rewriter needs both before it can produce a coherent file).

## References

- PRD §4 (lines 131–168), §5 (lines 171–186), §6 (lines 188–209), §9 item 6 (line 279).
- Action plan A1 (lines 193–199).
- Memory: `feedback-paper-voice`, `feedback-changes-log`, `project-linear-accumulator`, `project-he-ifd-pivot`.

## Comments

(none yet)
