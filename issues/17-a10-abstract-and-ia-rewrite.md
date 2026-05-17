# 17. A10 abstract + §I-A challenges rewrite (May-5 working numbers)

Status: ready-for-agent
Label: AFK
Priority: P2 (text-only; the abstract is the resubmission's first impression)
Action-plan: A10
PRD-section: §1, §2, §4

## Parent

Action plan A10 (lines 400–419) + the "Numbers freeze + replacement protocol" (lines 420–230).

## What to build

Two complementary rewrites of `introduction.tex` and `main.tex`:

1. **Abstract — participation incentive paragraph rewrite.** Use the May-5 concrete numbers as the **working text** per the action plan A10's "numbers freeze" protocol:
   - MNIST α=0.3: 0.965 student vs 0.81 mean teacher.
   - CIFAR-10 α=0.3: 0.521 vs 0.408.
   These ship to advisor + co-authors at the week-16 draft handoff. The protocol is byte-identical to May-5 except for the teacher epoch count (30 → 100 to match Co-Boosting); per user judgment 2026-05-17, this should produce near-identical student-vs-mean-teacher ratios. Issue 28 (reconciliation) handles any > 3 pp divergence later.

2. **§I-A "Our Approach" rewrite.** Replace the three legacy challenges (polynomial magnitude explosion, training–distillation gap, scale-aligned loss — all artefacts of the depth-heavy block-wise protocol) with the post-pivot four challenges:
   - **C1:** HE depth budget for end-to-end student SGD (resolved by the linear-accumulator construction; see issue 13).
   - **C2:** β / λ ensemble boost without division under HE (PRD §4.2).
   - **C3:** Binding invariant under $N-1$ collusion (PRD §2.3).
   - **C4:** Post-release SQ-floor mitigation via DP-SGD teachers + per-row Gaussian noise (PRD §2.5).
   Each contribution gets a `\ref{sec:...}` pointer to the section that addresses it — the "linking to chapters" the advisor explicitly flagged in [R3-2].

Voice: austere theoretical register; no "we proudly demonstrate" framing (memory `feedback-paper-voice`).

Log all changes in `FL_TDSC/CHANGES.md`.

## Acceptance criteria

- [ ] Abstract participation-incentive paragraph contains the four May-5 numbers (0.965, 0.81, 0.521, 0.408).
- [ ] §I-A "Our Approach" replaces three legacy challenges with C1–C4 above.
- [ ] Each C1–C4 cites its addressing §§ pointer via `\ref{...}`.
- [ ] No mention of "polynomial magnitude explosion," "training–distillation gap," or "scale-aligned loss" remains in §I-A.
- [ ] `pdflatex` clean.
- [ ] `FL_TDSC/CHANGES.md` updated with before/after entries.

## Blocked by

- Issue 01 (PRD-internal patches first so §I-A's pointers resolve correctly).

## References

- Action plan A10 (lines 400–419) and "Numbers freeze + replacement protocol" (lines 420–230).
- PRD §1, §2.3, §2.5, §4.2.
- May-5 report: [reports/2026-05-05_one_shot_cfd_central_vs_client_update.md](../reports/2026-05-05_one_shot_cfd_central_vs_client_update.md).
- Memory: `feedback-paper-voice`, `feedback-changes-log`.

## Comments

(none yet)
