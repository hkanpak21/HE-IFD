# 05. A8 threat-model rewrite — binding invariant + IND-CPA + SQ-floor

Status: ready-for-agent
Label: AFK
Priority: P2 (high cover-letter value; unblocks 13)
Action-plan: A8
PRD-section: §2.3, §2.4, §2.5

## Parent

Action plan A8 (lines 378–391 of action plan).

## What to build

Rewrite `methodology.tex` §threat-model (currently describing the block-wise HE-IFD threat model) and the relevant §discussion paragraphs to import PRD §2 verbatim where appropriate. Specifically:

1. Replace §threat-model with PRD §2.1 (parties + trust), §2.2 (multiparty CKKS at $t=N$), §2.3 (binding invariant), §2.4 (adversary's view table), §2.5 (all-zeros amplification + (P1)/(P2) defence), §2.6 (out-of-scope adversaries).
2. Drop the existing block-wise-protocol-specific threat-model prose (per the PRD's "deprecation note" at lines 8–10).
3. Insert the R2-Q6 plaintext-student-weights paragraph from action plan A8 (lines 396–398) verbatim into the appropriate methodology subsection. This pre-empts R2-Q6 in the response document.
4. Cite `mouchet2021multiparty` for the multiparty CKKS scheme (already in `references.bib` per CHANGES.md §3).
5. Log all changes in `FL_TDSC/CHANGES.md` per the established before/after format (memory `feedback-changes-log`).

Voice: austere theoretical register matching `methodology.tex:21` (memory `feedback-paper-voice`). No documentation-flavoured prose, no "we proudly demonstrate," no bullet sprawl in body text. Sceptical-professor reader.

## Acceptance criteria

- [ ] `methodology.tex` §threat-model contains §2.1–§2.6 of PRD, in the paper's prose register.
- [ ] R2-Q6 paragraph (linear-accumulator + CT×PT vs CT×CT framing) lands in the appropriate subsection.
- [ ] `mouchet2021multiparty` cited for the threshold-decryption scheme.
- [ ] No mention of "per-block ciphertexts," "block-wise training," "magnitude regularisation," or "bridge construction" remains in the rewritten section.
- [ ] `FL_TDSC/CHANGES.md` updated with before/after entries for every replaced paragraph, line-numbered.

## Blocked by

- Issue 01 (PRD-internal staleness patch) — so the rewriter is reading the corrected PRD §4.3 prose before quoting §2.

## References

- PRD §2 (lines 30–94).
- Action plan A8 (lines 378–391), particularly the R2-Q6 paragraph at lines 396–398.
- Memory: `feedback-paper-voice`, `feedback-changes-log`, `project-linear-accumulator`.

## Comments

(none yet)
