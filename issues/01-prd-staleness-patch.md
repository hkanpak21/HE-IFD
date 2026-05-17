# 01. PRD-internal staleness patch

Status: ready-for-agent
Label: AFK
Priority: P1 (bootstrap; unblocks 04, 13, 14, 15)
Action-plan: PRD-side (no Ax mapping)
PRD-section: §2.7, §4.3, §8, §10

## Parent

PRD: [reports/2026-05-05_methodology_pivot.md](../reports/2026-05-05_methodology_pivot.md). Precedent for PRD-side patches: `FL_TDSC/CHANGES.md` §6 "References audit (2026-05-17)" finding 2 patched PRD-only prose typos in the same pass as the bib audit.

## What to build

Three internal-consistency patches to the PRD plus one re-ordering:

1. **§4.3 — Linear-accumulator reality.** Current prose ("plaintext-times-ciphertext at each layer (depth +1 per multiplied weight matrix)", "expected 1k–5k bootstraps per protocol run") describes a full encrypted forward+backward chain. The 2026-05-17 user clarification (memory `project-linear-accumulator`, action plan A3 "Depth budget clarification") establishes that the student forward pass runs on **plaintext** weights and only the gradient accumulator ⟨Δ⟩ is encrypted, with per-step depth ≤ 3. Replace §4.3 with the linear-accumulator description; drop the bootstrapping cost discussion.

2. **§2.7 — SVG vs TikZ.** §2.7 says "I will produce this figure as `FL_TDSC/figures/threat_model_v2.pdf` from a TikZ source." Appendix A "Closed" says the figure is plain SVG at `FL_TDSC/figures/threat_model_v2.svg`, converted to PDF via `rsvg-convert --format=pdf`, no TikZ. §2.7 is stale; rewrite to match Appendix A.

3. **§8 — Smoke-test scope.** §8 step 5 implies encrypted student forward+backward + bootstrapping deferral to Lattigo. Under the linear-accumulator construction, no bootstrapping is needed and the smoke test stays entirely in TenSEAL. Rewrite §8 step 5 + the "Forgetting points" point (a) accordingly.

4. **§10 — Re-order open items.** §10 predates the 2026-05-17 priority reframe (action plan §0). Re-order to mirror action-plan priorities: P1 = A4-tri-axis grid, P2 = A3, P3 = A7, then text/figure work, then γ-variant.

All four patches are logged in `FL_TDSC/CHANGES.md` under a new §7 "PRD staleness patch (2026-05-17)" with the same before/after format used in §6 fact-check finding 1.

## Acceptance criteria

- [ ] PRD §4.3 reads in linear-accumulator terms; no "1k–5k bootstraps" or "depth +1 per multiplied weight matrix" prose remains.
- [ ] PRD §2.7 reads SVG, `rsvg-convert`, no TikZ.
- [ ] PRD §8 step 5 + §8 forgetting points reflect linear-accumulator depth budget.
- [ ] PRD §10 reordered to A4 → A3 → A7 → text/figure → γ.
- [ ] `FL_TDSC/CHANGES.md` §7 contains four before/after entries with PRD line numbers.

## Blocked by

None — can start immediately.

## References

- PRD §4.3 (lines 161–167), §2.7 (lines 82–93), §8 (lines 245–256), §10 (lines 379–387).
- Memory: `project-linear-accumulator`, `feedback-paper-voice`, `feedback-changes-log`.
- Action plan A3 §"Depth budget clarification" (lines 32–34) and §"Action item — update PRD §4.3" (line 42).

## Comments

(none yet)
