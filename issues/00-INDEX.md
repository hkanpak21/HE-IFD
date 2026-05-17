# HE-IFD issue index

Source PRD: [reports/2026-05-05_methodology_pivot.md](../reports/2026-05-05_methodology_pivot.md)
Action plan: [reports/2026-05-10_tdsc_rejection_action_plan.md](../reports/2026-05-10_tdsc_rejection_action_plan.md)
Generated: 2026-05-17 by `/to-issues` against the PRD.

## Headline objective driving priorities

The resubmission's headline contribution is showing **HE-IFD's accuracy does not degrade vs prior one-shot FL work** while adding cryptographic privacy guarantees. The critical path therefore terminates at issue 18 (A4.1 accuracy grid), with every prerequisite ordered before it. Text-only and figure-only slices are interleaved so Ralph never idles while compute is queued.

## Priority order (Ralph picks lowest-numbered ready-for-agent issue with all blockers cleared)

| # | Title | Label | Action-plan | Blocked by | Notes |
|---|---|---|---|---|---|
| 01 | PRD-internal staleness patch | AFK | — | none | Unblocks 04, 13, 14, 15 |
| 02 | Ralph orchestrator scaffold | AFK | infra | none | Bootstrap; without this Ralph cannot iterate |
| 03 | QoS escalation ticket (P0) | HITL | infra | none | Admin ticket; unblocks 18, 23 |
| 04 | A2 TenSEAL smoke prototype | AFK | A2 | 01, 02 | Validates linear-accumulator depth ≤ 3 |
| 05 | A8 threat-model rewrite | AFK | A8 | 01 | Pure text; high cover-letter value |
| 06 | A6.1 Vendor Co-Boosting | AFK | A6.1 | 02 | Reusable from May-5 |
| 07 | A6.2 Vendor FedMD | AFK | A6.2 | 02 | — |
| 08 | A6.3 Vendor FedDiff | AFK | A6.3 | 02 | Primary γ-variant comparator |
| 09 | A6.4 Vendor FedKT | AFK | A6.4 | 02 | DP via Opacus, ε ∈ {1, 10} |
| 10 | A6.5 Vendor tier-2 comparators | AFK | A6.5 | 02 | FedDF, DENSE, FuseFL, FedMD-NFDP, FedDM |
| 11 | A11 threat-model SVG | AFK | A11 | 01 | Pure figure |
| 12 | A11 protocol-overview SVG | AFK | A11 | 01 | Pure figure; pre-empts R2-Q6 visually |
| 13 | A1 wholesale methodology rewrite | AFK | A1 | 01, 05 | Replace methodology.tex §3 onwards |
| 14 | A3 end-to-end CKKS single cell | AFK | A3 | 04 | Calibration anchor for A4 |
| 15 | A4.4 pre-flight gate (A4-sanity) | AFK | A4.4 | 04, 13 | < 2 pp gap → halt-and-escalate |
| 16 | A11 motivation / future-directions moves | AFK | A11 | 01 | Localised .tex edits |
| 17 | A10 abstract + §I-A challenges rewrite | AFK | A10 | 01 | May-5 working numbers |
| 18 | A4.1 accuracy grid execution | AFK | A4.1 | 03, 06, 07, 08, 09, 10, 15 | **The headline deliverable** |
| 19 | A4.2 communication table | AFK | A4.2 | 14, 18 | Triple-axis Pareto: comm |
| 20 | A4.3 time table | AFK | A4.3 | 14, 18 | Triple-axis Pareto: time |
| 21 | A7 MIA on decrypted students | AFK | A7 | 18 | LiRA + loss-threshold |
| 22 | A5 DP-DDPM profiling micro-task | AFK | A5 | 02 | Closes γ-scope conditional path |
| 23 | A5 DP-DDPM generators (per-client) | AFK | A5 | 03, 22 | Conditional path per 22's h |
| 24 | A5 γ-variant cells in A4.1 | AFK | A5 | 14, 18, 23 | Encrypted synthetic probe protocol |
| 25 | A13 ViT-tiny / ViT-small feasibility | AFK | A13 | 04 | Modern-architecture extension |
| 26 | A9 future-work malicious clients ¶ | AFK | A9 | none | Half-page text; no dependencies |
| 27 | A12 pruning ablation | HITL | A12 | Kerem meeting | Interpretation needed first |
| 28 | A10 numbers reconciliation pass | HITL | A10 | 18 | > 3 pp Δ → halt-and-diagnose |

## Stable core (per PRD §9.5.1; do NOT touch without re-approval)

- Binding invariant (PRD §2.3): only $\theta_E$ is ever threshold-decrypted.
- Multiparty CKKS at $t=N$.
- Linear-accumulator construction (per memory `project-linear-accumulator`).
- α-vs-γ variant boundaries (PRD §3).
- CKKS at logN ∈ {14, 15}, scale ≈ 2⁴⁰, multiparty per Mouchet et al.

## Adjustable peripherals (per PRD §9.5.2; Ralph may tweak with logged rationale)

Probe size, β, λ, $E_1$/$E_2$, seed count, dataset / α subsetting, comparator drop, student architecture within constraints, DP-DDPM scope, N, library, sbatch chunking. Each tweak → `reports/2026-MM-DD_tweak_<slug>.md` + one-line ledger entry in `reports/decision_log.md`.

## Escalation triggers (per PRD §9.5.4; Ralph must halt)

Stable-core touch · compute overrun > 50 % · critical-path slip > 1 week · A4-sanity gap < 2 pp · > 3 pp divergence from A10 working text · both tier-1 DP comparators fail · linear-accumulator gradient-norm divergence > 5 % · any login-node violation.
