# 010 — KD hyperparams for pretrained-head regime + 003 pytest re-run  [AFK]

> **STATUS: 📥 OPEN** (2026-05-28) — ready to claim.

**Phase:** M1.5 / α (debug θ₀≥final phenomenon) · **Blocked by:** none · **Blocks:** decision on 011's necessity

**Required reading (you are context-zero):**
1. `docs/prd/he-ifd-tnse-resubmission.md` — especially the "Phase II" section appended 2026-05-28.
2. `CLAUDE.md` — ops, golden rule, 3h VALAR cap.
3. `docs/issues/008-pretrained-headline-sweep.md` STATUS block — describes the θ₀≥final phenomenon being debugged.
4. `src/distill.py`, `src/protocol.py`, `src/sweep.py` — the current KD pipeline.

## Why this issue exists

After M1, raw_union @ α=0.05 / **resnet18 / CIFAR-10** = 0.48 while the warmed init θ₀ alone = **0.74** — distillation actively degrades a strong aligned init by 26pp. This protocol cannot ship with that regime broken. This issue tests whether the gap closes via KD hyperparams (orthogonal to issue **011** which tests trainable-layer capacity).

## What to build

Focused sweep on **resnet18 / CIFAR-10 / α=0.05 / N=10, 3 seeds {42,43,44}**:
- `K ∈ {30, 100, 300, 1000}` — current 300 may overshoot a tiny linear head warmed to 0.74.
- `τ ∈ {1, 4}` — current τ=4 may smooth targets too much for a linear classifier.
- `student-LR ∈ {0.001, 0.01}` — current 0.01 may move too far given θ₀ already strong.

4 × 2 × 2 = 16 configs × 3 seeds = **48 cells** (chunked array, ≤3h per chunk). Case slug: `heifd_010_kd_hparams_resnet18`. Sweep CLI may need a `--Ks` (list) extension, OR submit per-K with the existing `--K`.

If a config beats θ₀ = 0.74 by ≥3pp: run a second mini-sweep on the best (K,τ,LR) varying λ-schedule {current, pure-KD, λ=0.5 fixed} to refine.

**Also (small):** `pip install --quiet pytest` into `he_ofl` on the VALAR login node, then re-submit `jobs/heifd_tests.sh`. This closes issue 003.

## Acceptance criteria

- [ ] `jobs/heifd_010_kd_hparams.sh` (chunked, ≤3h per chunk, resumable).
- [ ] `results/heifd_010_kd_hparams_resnet18/` populated; README has (K,τ,LR) → acc table + best config flagged.
- [ ] Verdict in the case README: does the θ₀→final gap close by hyperparams alone (yes / no / partial)?
- [ ] Pytest installed in `he_ofl`; `jobs/heifd_tests.sh` re-submitted; test job completes with real test outcomes (not a missing-import error).
- [ ] Escalation pointer: if gap *not* closed → recommend issue **011** (capacity) and **013** (KD diagnostic).

## Ops + boundaries (CLAUDE.md)

- `sbatch` only for training; env `he_ofl`; ≤3h per job. Datasets cached; results under `results/<case>/`.
- Permitted login-node `ssh` ONLY for `pip install pytest` + the test re-submit (documented sanctioned exception).
- Do NOT `git push`/`git commit`/`sbatch` from your worktree. Orchestrator merges + submits compute. ast.parse only.

## Report

1. Configs swept (final list).
2. Best (K, τ, LR) and its mean accuracy vs θ₀ = 0.74.
3. Verdict: gap closed / not closed / partial. Recommended next step.
4. Pytest install + test re-submit outcome.
5. Files touched, confirm no push/commit/sbatch other than the sanctioned pytest install.
