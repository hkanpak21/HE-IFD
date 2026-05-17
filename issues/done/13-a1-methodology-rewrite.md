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

### 2026-05-17 — landed (Ralph wave 4)

Wholesale rewrite of `FL_TDSC/methodology.tex` lines 32–674 (642 lines pre-edit) completed in a single pass. The threat-model subsubsection `\label{sec:threat_binding}` from issue 05 (lines 1–31) is preserved verbatim and is the load-bearing security backbone for the new content. The result is 228 lines total (a 446-line net reduction), 286 balanced braces (down from 779).

**New top-level structure (lines 32–228 of post-edit `methodology.tex`):**

1. `\par\noindent\textbf{Protocol overview.}` paragraph + `\par\noindent` binding-invariant paragraph + `Table~\ref{tab:cfd_phases}` carrying the PRD §4.1 phase table (Phase / Who / What / HE cost) verbatim as a LaTeX tabular.
2. `Algorithm~\ref{alg:cfd}` "Encrypted CFD (one round)" replaces the rejected Algorithm 1; the 20 `\STATE` lines cover Phase 1 client-side parallel teacher training + encrypted logit/confidence upload, Phase 2a plaintext warm-start, Phase 2b ensemble target at depth ≤ 3, Phase 2c encrypted SGD as linear accumulator, Phase 3 collective key-switch, Phase 4 optional personalisation.
3. `\subsubsection{Phase~1: Client-Side Teacher Training and Encrypted Upload}` `\label{sec:phase1}`.
4. `\subsubsection{Phase~2: Encrypted Ensemble Target and Encrypted Student SGD}` `\label{sec:phase2}` (retained label that the introduction, threat-model, background all cross-reference), with `\paragraph{β/λ secure handling}` `\label{sec:ensemble_target}` (un-normalised aggregation + temperature absorption; uniform-weight per-row variance; total loss-side depth ≤ 3) and `\paragraph{Linear-accumulator construction}` `\label{sec:linear_accumulator}` (new label; carries Eq.~`linear_accumulator` $\langle\theta_E\rangle = \langle\theta_0^\star\rangle + \sum_t \eta \cdot \langle g_t\rangle$, per-step depth ≤ 3 walkthrough, no-bootstrapping parameter sketch at logN=14, scale ≈ 2^40, ring 16384, and the released-student inference-compatibility framing per cover-letter R1-W2).
5. `\subsubsection{Phase~3: Collective Threshold Key-Switch}` `\label{sec:phase3}` — DKG, encrypted upload + computation, collective key-switch, $t{=}N$ trust assumption. Citation set: Mouchet et al. + Lattigo + RLWE.
6. `\subsubsection{Phase~4: Optional Client-Side Personalisation}` `\label{sec:phase4}` — head-only fine-tuning, on-device, post-processing reduction.
7. `\subsection{Two-Stage Initialisation}` `\label{sec:twostage_init}` — Stage 1 plaintext warm-start, Stage 2 encrypted SGD, hypothesis, A1 + A2 ablations, γ-variant remark, training-stability remark.
8. `\subsection{Communication Complexity}` `\label{sec:complexity}` — `Table~\ref{tab:comm_complexity}` per PRD §5 (5-row per-message table); concrete numbers at the headline cell.
9. `\subsection{Privacy Analysis}` `\label{sec:privacy_proof}` — brief, points to `\ref{sec:threat_binding}`.
10. `\subsection{Architecture-Specific Instantiations}` `\label{sec:architecture}` with `\subsubsection{Convolutional Networks}` `\label{sec:arch_cnn}` and `\subsubsection{Transformer and Vision Transformer Architectures}` `\label{sec:arch_transformer}` — brief stubs that preserve external label resolution from `experiments.tex:31`.

**Forbidden terms grep (acceptance gate):** zero matches in scope (lines 32+) for any of `per-block ciphertext`, `block-wise training`, `magnitude regularisation`, `magnitude regularization`, `TrainableBridge`, `scale-aligned loss`, `block boundary`, `bridge construction`, `K{+}1 block`, `MagReg`, `NormMSE`, `PolyBasicBlock`, `scale-anchored`, `per-channel collaborative normalisation`.

**Cross-reference resolution:** every `\ref{...}` in `methodology.tex` resolves to a `\label{...}` paper-wide; every `\cite{...}` resolves to `references.bib`; every external `\ref{...}` pointing into `methodology.tex` continues to resolve (`sec:phase2`, `sec:phase3`, `sec:arch_transformer`, `sec:privacy_proof`, `sec:methodology`, `sec:framework`).

**Sidecar:** `.agent-output/13-changes.md` (orchestrator merges as §13 of `FL_TDSC/CHANGES.md`).

**Open follow-ups for downstream issues (not in this commit):**

- The figure on lines 4–9 of `methodology.tex` (`HE-IFD_sysFigure.pdf` with caption describing the rejected block-wise protocol) is inside the preserve region; the stale caption is the only remaining "block-wise" surface in `methodology.tex` and belongs to a figure-replacement issue (11/12 territory).
- The introduction §I-A C1/C2 cross-refs (`introduction.tex:26, 28`) currently target `\ref{sec:phase2}` (less specific) instead of the new `\ref{sec:linear_accumulator}` / `\ref{sec:ensemble_target}`. Both targets resolve correctly as-is; retargeting belongs to a follow-up issue 17 patch.
