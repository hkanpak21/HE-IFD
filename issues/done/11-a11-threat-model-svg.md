# 11. A11 threat-model SVG (figure)

Status: ready-for-agent
Label: AFK
Priority: P2 (figure for the response document; pre-empts R3-4)
Action-plan: A11
PRD-section: §2.7, Appendix A "Closed"

## Parent

Action plan A11 (lines 420–446) + PRD §2.7 (the figure specification).

## What to build

Hand-author `FL_TDSC/figures/threat_model_v2.svg` per PRD §2.7's spec + Appendix A "Closed" item:

- **Format:** plain SVG, single panel, minimal decoration. No TikZ. (PRD Appendix A "Closed" overrides PRD §2.7's stale "TikZ" reference; fixed by issue 01.)
- **Palette:** Client fill `#C6A87D`, Server fill `#8B9EA8` (memory `feedback-colors`). Method lines from ColorBrewer Dark2.
- **Contents (per PRD §2.7):**
  - $N$ client boxes, each containing $\mathcal{D}_i, T_i, \mathsf{sk}_i$. Up to $N-1$ highlighted as "may collude with server"; one shaded as "honest" with note "as long as one such client exists, privacy holds."
  - Central server box, shaded as "may collude," holding collective public key $\mathsf{pk}$, public probe $\mathcal{P}$, encrypted student $\langle\theta\rangle$ during training.
  - One arrow per client (client → server): `⟨T_i(P)⟩ (encrypted)`.
  - One arrow per client (server → client): `⟨θ_E⟩ (encrypted, then collectively key-switched)`.
  - Dashed boundary around the server's compute: "everything inside is ciphertext under pk, IND-CPA-hidden."
  - Threshold-decryption gate inset: $N$ key-share inputs → one plaintext output ($\theta_E$ only).
  - Side panel listing adversary's plaintext view (Subset 2 of PRD §2.4).
- **Build:** Add a one-liner in `jobs/build_figures.sh` (or extend if it exists): `rsvg-convert --format=pdf FL_TDSC/figures/threat_model_v2.svg -o FL_TDSC/figures/threat_model_v2.pdf`. The `.pdf` artefact is what `\includegraphics{...}` resolves to in the paper.

The Closed item explicitly forbids design-MCP detours; this is hand-authored SVG.

## Acceptance criteria

- [ ] `FL_TDSC/figures/threat_model_v2.svg` exists.
- [ ] `xmllint --noout FL_TDSC/figures/threat_model_v2.svg` returns clean.
- [ ] `rsvg-convert --format=pdf` produces `FL_TDSC/figures/threat_model_v2.pdf` without warnings.
- [ ] All eight elements from PRD §2.7's spec are present.
- [ ] Client / server colour fills match `#C6A87D` and `#8B9EA8` exactly.
- [ ] `FL_TDSC/CHANGES.md` updated with a note that the new figure is referenced from `methodology.tex` §threat-model.

## Blocked by

- Issue 01 (PRD-internal staleness patch) — so §2.7's prose is reconciled with the SVG decision before the figure is built.

## References

- PRD §2.7 (lines 82–93), Appendix A "Closed" (lines 421–422).
- Memory: `feedback-colors`.
- Action plan A11 (lines 420–446).

## Comments

(none yet)
