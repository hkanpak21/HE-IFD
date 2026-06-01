# 021 — Membership-inference suite (3 surfaces, LiRA + GLiRA + threshold)  [AFK]

> **STATUS: ✅ DONE (MNIST) → extended by [028](028-mia-second-backbone-family.md)** (2026-05-30) — `mia/` suite built + landed clean on MNIST/MLP (2 cells, 3 attacks × 3 surfaces, 64 shadows): released model θ⋆ **near-chance** (AUC 0.49–0.57 across Yeom/LiRA/GLiRA × external/fellow); prototype channel leaks raw (AUC→0.80 @ α=1.0) but **DP ε≤8 collapses it to chance**, validating the averaging-variant accounting. Second backbone family (ViT/CIFAR-100 + RoBERTa/AG-News) is issue 028.

**Phase:** M2 (privacy validation) · **Blocked by:** none · **Blocks:** the empty §VI (Residual Leakage) of the paper.

**Required reading:**
1. `CLAUDE.md` (VALAR/sbatch/3h cap; never python on login node).
2. `docs/paper/sections/mia.tex` — the placeholder section this fills, and the threat framing.
3. `docs/paper/sections/prelim.tex` §Threat Model + `method.tex` §Security Analysis — the two leakage channels.
4. `src/protocol.py`, `src/evaluate.py` — how a global model θ⋆ is produced and evaluated (reuse to make target/shadow models).

## Why

The paper protects client *contributions* cryptographically, but every party receives the decrypted global
model θ⋆ in the clear. §VI must *measure* what that released model (and the Phase-0 prototypes) leak. This
is the most-cited TDSC rejection demand (R1-W4 / R2-Q5).

## What to build (`mia/`, Python; reuse `src/` to train models)

A self-contained `mia/` suite implementing three attacks and three adversary surfaces, producing
TPR@0.1%FPR + ROC/AUC.

**Attacks (cite + match the published algorithms; prefer public reference implementations):**
1. **Loss/confidence threshold** — Yeom et al. 2018 (`yeom2018privacy`). Cheap interpretable floor.
2. **LiRA** — Carlini et al. 2022 (`carlini2022membership`), the likelihood-ratio shadow-model attack.
   Reference impl: `github.com/tensorflow/privacy/.../mi_lira_2021` (port the algorithm; ~64 shadow models).
3. **GLiRA** — Galichin et al. 2025 (`galichin2025glira`), distillation-guided black-box LiRA — the natural
   fit for the external black-box adversary on θ⋆. Implement from the paper (no public repo found).

**Adversary surfaces (per the grill):**
- **External** on the released θ⋆ (black-box): GLiRA + LiRA + threshold.
- **Fellow-client**: an honest-but-curious participant attacking θ⋆ with its own data + the shared Phase-0
  prototypes as auxiliary (a stronger prior than external).
- **Prototype channel**: membership inference directly on the Phase-0 per-class prototype release —
  empirically validates the averaging-variant DP accounting (run at raw and at ε∈{2,8}).

**Cells:** `mnist_mlp` and `vit_b32_cifar100`, N=10, α∈{0.05, 1.0}, ~64 shadow models per target.

## Acceptance
- [ ] `mia/` runs the three attacks × three surfaces and emits TPR@0.1%FPR + ROC/AUC (+ ROC arrays for plots).
- [ ] Shadow-model training reuses `src/` (no duplication of the protocol).
- [ ] A results writer producing `results/heifd_021_mia/` (per-cell JSON + a summary the paper table reads).
- [ ] `jobs/heifd_021_mia_*.sh` wrappers (CLAUDE.md template, ≤3h, resumable; shadow-model training chunked).
- [ ] README documenting the attacks, surfaces, metrics, and the expected comparison (HE-IFD released-model
      leakage should be ≤ a matched DP one-shot baseline, since DP perturbs the released model).

## Hard boundaries
- New code under `mia/` + `jobs/heifd_021_mia_*.sh`. May add a *small* read-only export hook to `src/` only
  if unavoidable (document it); do NOT change `src/` training/aggregation semantics.
- No `git push`/`git commit`/`sbatch`/`ssh`. ast.parse for syntax check (Mac has no torch). Local logic only.

## Report
1. Attacks implemented + their citations/algorithms + any port decisions.
2. Files added; any `src/` hook.
3. The wrapper grid + how shadow-model training is chunked under the 3h cap.
