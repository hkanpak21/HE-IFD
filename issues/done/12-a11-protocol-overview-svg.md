# 12. A11 protocol-overview SVG (figure)

Status: ready-for-agent
Label: AFK
Priority: P2 (figure pre-empts R2-Q6 visually; companion to 11)
Action-plan: A11
PRD-section: §4.1, §4.2

## Parent

Action plan A11 (lines 420–446) with the 2026-05-17 figure-spec update at lines 438–244.

## What to build

Hand-author `FL_TDSC/figures/protocol_overview_v2.svg` per the action plan A11 figure-spec update:

- **Format:** plain SVG, single panel, left-to-right phase progression (0 → 1 → 2a → 2b → 2c → 3). No TikZ.
- **Palette:** Client `#C6A87D`, Server `#8B9EA8` (memory `feedback-colors`).
- **Contents per A11 figure-spec update:**
  - **Phase 0:** DKG glyph at server, $N$ client shares converging into collective $\mathsf{pk}$.
  - **Phase 1:** $N$ client boxes, each emitting `⟨T_i(P)⟩` arrow into server.
  - **Phase 2a:** Server box, plaintext SGD on $(\mathcal{P}, y_\mathcal{P})$, producing $\theta_0^*$.
  - **Phase 2b:** Server box, encrypted ensemble target $\widetilde Y = \sum_i \langle\alpha_i^\beta\rangle \cdot \langle T_i(\mathcal P)\rangle$ at depth ≤ 3.
  - **Phase 2c (the critical visual):** Two parallel tracks inside the phase box:
    - *Top track (plaintext):* labelled `θ (plaintext)`, light-tinted Client beige (lightened ~30 %), `forward pass` glyph inside. `<g id="plaintext-track">`.
    - *Bottom track (encrypted):* labelled `⟨Δ⟩ (encrypted accumulator over ⟨g_t⟩)`, Server grey-blue fill, `accumulate ⟨g_t⟩` glyph inside. `<g id="encrypted-track">`.
  - **Phase 2c → Phase 3 boundary:** `+` composition glyph bridging the two tracks; output labelled `⟨θ_E⟩ = ⟨θ_0*⟩ + ⟨Δ⟩` in Server colour.
  - **Phase 3:** "collective key-switch" → arrows to each client → plaintext $\theta_E$ delivered.
- **Build:** Extend `jobs/build_figures.sh` to convert this SVG to PDF via `rsvg-convert`.

This figure is the figure-level counterpart of A8's R2-Q6 rewrite — anyone reading it sees at a glance that the student forward pass runs in plaintext during training; only the teacher-induced delta is encrypted.

## Acceptance criteria

- [ ] `FL_TDSC/figures/protocol_overview_v2.svg` exists.
- [ ] `xmllint --noout` returns clean.
- [ ] `rsvg-convert --format=pdf` produces `FL_TDSC/figures/protocol_overview_v2.pdf`.
- [ ] Separate `<g id="plaintext-track">` and `<g id="encrypted-track">` groups present (editor-friendly per spec).
- [ ] Composition glyph `⟨θ_E⟩ = ⟨θ_0*⟩ + ⟨Δ⟩` present at Phase 2c → 3 boundary.
- [ ] `FL_TDSC/CHANGES.md` updated.

## Blocked by

- Issue 01 (so PRD §4.3 prose is reconciled with linear-accumulator before the figure is finalised).

## References

- PRD §4.1, §4.2 (phase table + β/λ secure handling, lines 134–168).
- Action plan A11 figure-spec update (lines 238–244).
- Memory: `project-linear-accumulator`, `feedback-colors`.

## Comments

(none yet)
