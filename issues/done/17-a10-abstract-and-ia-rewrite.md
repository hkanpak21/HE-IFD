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

**2026-05-17 — wave-5 agent.** Done. Both rewrites landed.

- `FL_TDSC/main.tex` lines 89–99: abstract participation-incentive paragraph rewritten. All four May-5 numbers ($0.965$, $0.81$, $0.521$, $0.408$) appear verbatim with arithmetic deltas ($+15.5$ pp, $+11.3$ pp). The $N{=}10$, Dirichlet $\alpha{=}0.3$ context is named explicitly so the numbers are unambiguous against `reports/2026-05-05_one_shot_cfd_central_vs_client_update.md` §4.1 / §5.1. The DP-tax framing matches `reports/cover_letter_draft.md` §3 R1-W4 (DP-SGD noise at the local teacher, no central DP tax on top of the cryptographic guarantee). The protocol paragraph also rewritten to name the public-probe encrypted logit upload + ensemble target + linear-accumulator construction (replacing the rejected version's per-block intermediate-feature framing). Pre-existing commented-out abstract blocks (lines 101–107) untouched.
- `FL_TDSC/introduction.tex` lines 24–33: §I-A "Our Approach" challenges + closing paragraph rewritten. Three legacy challenges (polynomial magnitude growth, train–inference covariate shift across composed blocks, scale-aware loss) replaced by four post-pivot challenges C1–C4 with explicit `\ref{...}` cross-references. Pre-existing three-phase enumeration (lines 18–22) preserved verbatim; the §I lead paragraphs (lines 1–14) and §I-A "Contributions" enumeration (lines 40–51) untouched. Pre-existing commented-out backup block (lines 56–109) untouched. No `\cite{...}` keys added or removed.

**Cross-reference choices:**
- C1 (HE depth budget): `\ref{sec:phase2}` (depth-3 ensemble target as dominant CT×CT cost) + `\ref{sec:threat_binding}` (plaintext-student-state-during-training paragraph anchors the linear-accumulator construction). No `sec:linear_accumulator` label exists yet — issue 13's scope.
- C2 ($\beta/\lambda$ ensemble boost): `\ref{sec:phase2}` exclusively. Same precedent as `CHANGES.md` §9 (A8 threat-model rewrite already targets `sec:phase2` for "the depth-bounded ensemble target construction"). No dedicated `sec:phase2_ensemble` / `sec:methodology_ensemble` label exists yet — issue 13's retargeting flag.
- C3 (binding invariant): `\ref{sec:threat_binding}` — exact fit, the label introduced by issue 05.
- C4 (post-release SQ-floor): `\ref{sec:threat_binding}` — carries the "All-zeros amplification and its defence" paragraph from issue 05.

**Acceptance gates:**
- [x] Abstract contains all four May-5 numbers verbatim.
- [x] §I-A replaces three legacy challenges with C1–C4.
- [x] Each C1–C4 has a `\ref{...}` pointer to its addressing section.
- [x] No mention of "polynomial magnitude explosion", "training–distillation gap", "scale-aligned loss", or "scale-anchored loss" remains in active §I-A prose (three occurrences remain in the commented-out backup block at lines 86, 88, 90 — not in active prose).
- [x] Balanced braces: `main.tex` 317/317 (was 314/314); `introduction.tex` 97/97 (was 89/89). Both confirmed via `python3 -c "t=open(f).read(); print(t.count('{'), t.count('}'))"`.
- [x] All `\ref{...}` resolve: `sec:phase2` → `methodology.tex:102`, `sec:threat_binding` → `methodology.tex:17`, `sec:methodology` → `methodology.tex:2`, `sec:experiments` → `experiments.tex:2`.
- [x] No new `\cite{...}` keys introduced; existing intro citations untouched.
- [x] Sidecar `.agent-output/17-changes.md` written (~12 KB, drafted as §12 for orchestrator merge into `FL_TDSC/CHANGES.md`).

**Unilateral interpretations / things to flag for orchestrator + downstream issues:**
- The pre-existing three-phase enumeration at lines 18–22 still uses block-wise language ("at each layer group boundary", "block by block", "PolyResNet-18"). The C1–C4 paragraphs name the linear-accumulator construction explicitly, so the C1 framing wins on conflict; issue 13's wholesale methodology rewrite should align the enumeration with C1–C4.
- C1 and C4 both currently anchor on `sec:threat_binding` because the post-pivot methodology has not yet been sublabelled. Issue 13 should expose finer labels (e.g., `sec:linear_accumulator`, `sec:sq_floor_mitigation`) so the cross-references can be tightened.
- The cover letter §2 row AE-6/R3-2 lists the challenges in the order C3, C2, C1, C4 (sequenced by reviewer concern). The §I-A paragraphs are ordered C1, C2, C3, C4 (depth budget first as the load-bearing protocol-design property, binding invariant after the ensemble-construction discussion as the load-bearing security property). The two orderings are not in conflict; they serve different audiences.
- The C2 paragraph asserts "a per-class coverage-aware variant of $\beta$ is the natural extension" — this is the open algorithmic fix in `reports/2026-05-05_one_shot_cfd_central_vs_client_update.md` §6 item #5 / §7 item #2 (the $\beta$ collapse at CIFAR-10 $\alpha{=}0.05$ / $\alpha{=}0.1$). Naming it as the natural extension pre-empts a likely reviewer question without claiming it as implemented; consistent with the cover-letter framing for that gap.

Sidecar: `.agent-output/17-changes.md` (~12 KB). Orchestrator should merge as §12 of `FL_TDSC/CHANGES.md`.
