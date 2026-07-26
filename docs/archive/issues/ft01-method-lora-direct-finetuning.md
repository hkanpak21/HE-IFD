# ft01 — Method: LoRA + direct fine-tuning trajectory (distillation as ablation)  [AFK]

> **STATUS: 📥 OPEN** (2026-06-01) — the method change at the heart of the fine-tuning pivot. The server `aggregate` is UNTOUCHED; only the local-step path + trainable-parameter set change.

**Phase:** Foundation · **Blocked by:** none · **Blocks:** every headline/ablation experiment (ft04–ft09).

**Required reading:**
1. `docs/prd/he-ifd-finetuning.md` — the plan (method section + the thesis spine).
2. `CLAUDE.md` — ops; the method note (task arithmetic, depth-1 aggregate).
3. `src/distill.py` (current `local_distill_trajectory`), `src/backbones.py` (frozen extractors + trainable units), `src/aggregate.py` (depth-1 task arithmetic — DO NOT change), `src/protocol.py` (`run_cell`).

## Why

The headline local step pivots from teacher→student **distillation** to **direct supervised fine-tuning** of a **LoRA-adapter (+ head)** trainable unit, started from the shared basin `θ₀` and run for a bounded K-step trajectory; the cumulative displacement `Δᵢ = θᵢ⁽ᴷ⁾ − θ₀` is aggregated by the *existing* depth-1 linear combine (task arithmetic). LoRA makes "fine-tuning" credible (vs. linear probing) while staying HE-cheap (few extra ciphertexts, depth still 1). Distillation is kept as a switchable ablation.

## What to build

1. **LoRA trainable unit** in `src/backbones.py`: attach low-rank adapters (rank `r`, α scaling) to the last block(s) of the frozen backbone, plus the classifier head. Expose the flattened trainable-parameter vector (LoRA A/B matrices + head) as the object the protocol fine-tunes and aggregates — same flatten/reshape contract the head currently uses, so `aggregate` is byte-compatible. Keep `head` and `last_n_blocks` as alternative trainable units (for ft07).
2. **Direct fine-tuning trajectory** in `src/distill.py` (or a new `src/finetune.py`): `local_finetune_trajectory(...)` — bounded K-step supervised fine-tuning (cross-entropy on local hard labels) of the trainable unit from `θ₀`, returning `Δ = θ_K − θ₀`. Same signature/return contract as `local_distill_trajectory` so `protocol.run_cell` can switch on a `local_step ∈ {finetune, distill}` argument (default `finetune`).
3. **Thread `local_step` + `trainable_unit`** through `protocol.run_cell` and `sweep.py` (new axes). `local_step=distill` reproduces the current behaviour byte-identical; `trainable_unit=head` reproduces the current head-only path.
4. **Tests** (`tests/`): (a) `aggregate` on a LoRA+head displacement vector behaves identically to a head displacement of the same flattened length (task-arithmetic invariant preserved); (b) a regression that LoRA fine-tuning exceeds the head-only linear-probe IID accuracy on a small hard-task subset (i.e. LoRA actually fine-tunes).

## Acceptance
- [ ] LoRA(+head) trainable unit selectable; flattened vector aggregates through the unchanged `aggregate`.
- [ ] `local_finetune_trajectory` produces `Δ = θ_K − θ₀`; `local_step=finetune` is the default, `distill` byte-identical to today.
- [ ] `--local-step` and `--trainable-unit` threaded through `sweep.py`/`protocol.run_cell`; recorded per cell.
- [ ] Tests pass; ast.parse clean on touched `src/` files.

## Hard boundaries
- Touch `src/backbones.py`, `src/distill.py`/new `src/finetune.py`, `src/protocol.py`, `src/sweep.py`, `tests/`. **Do NOT change `src/aggregate.py` semantics** (depth-1 task arithmetic is the crypto contract). No `git push`/`commit`/`sbatch`/`ssh`. Mac has no torch — ast.parse only.

## Report
1. The LoRA unit + the flatten/reshape contract that keeps `aggregate` byte-compatible.
2. `local_finetune_trajectory` design; confirmation `distill` + `head` paths are unchanged.
3. The two tests + how the trainable-unit / local-step axes thread through the sweep.
