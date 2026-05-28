# 011 — Trainable-layer scope: head / LoRA / last-N-blocks  [AFK, methodology-shaping — HITL review touchpoint]

> **STATUS: 📥 OPEN** (2026-05-28) — ready to claim.

**Phase:** M1.5 / α (debug θ₀≥final via capacity; also fixes CNN-5) · **Blocked by:** none · **Blocks:** 014 (CNN-5 grid), 018 (LoRA recipe for big models)

**Required reading:**
1. `docs/prd/he-ifd-tnse-resubmission.md` — locked methodology framing: layer-scope adjustments OK iff server aggregation stays linear.
2. `CLAUDE.md`.
3. `docs/issues/008-pretrained-headline-sweep.md` STATUS — resnet18 θ₀≥final.
4. `docs/issues/007-from-scratch-headline-sweep.md` STATUS — CNN-5 hyperparam gap.
5. `src/backbones.py`, `src/protocol.py` (`BACKBONES`, `run_cell`), `src/aggregate.py` (linear-only invariant).

## Why

Two related M1 findings to address:

**(a)** Head-only distillation may be too capacity-constrained for the resnet18/low-α regime — the linear head can only *re-weight* a near-optimal θ₀, and the only direction is *down*. More trainable parameters (LoRA on the last 1–2 blocks, or thin last-block FT) should let distillation learn *on top of* θ₀ rather than overwrite it — without breaking FHE-friendliness (more ciphertexts; depth unchanged).

**(b)** CNN-5/CIFAR-10 IID raw_union = 0.48 vs oracle 0.75 = under-trained at 10 teacher epochs.

## What to build

### Part 1 — Trainable-scope plumbing

1. Add `trainable_scope` (or per-cell override via sweep CLI) to `BACKBONES` entries with modes:
   - `head_only` (current default).
   - `lora_<rank>` — LoRA adapters (rank 4, 8) on the last 1–2 transformer/residual blocks + head. Use `peft` (try `pip install peft` in `he_ofl`) OR hand-roll low-rank A·B matrices on selected Linear layers.
   - `last_n_blocks` — full FT of last 1–2 blocks + head.
2. Ensure `local_distill_trajectory` and `aggregate.aggregate` work transparently with the larger trainable set. **Critical invariant** (assert in a new unit test): aggregate uses only `+` and scalar `*` on tensors — linearity preserved regardless of parameter count.
3. `Δᵢ = θᵢ⁽ᴷ⁾ − θ₀` now spans more parameters; that's fine — aggregation is element-wise linear.

### Part 2 — Focused comparison run

resnet18 / CIFAR-10 / α=0.05 / N=10, 3 seeds, methods `no_phase0` + `raw_union_K20`:
- `head_only` (sanity reference; should match the 008 result)
- `lora_8` (rank 8, last 2 blocks + head)
- `last_block` (full FT of last residual block + head)

= 2 × 3 × 3 = **18 cells**. Case slug `heifd_011_scope_resnet18`.

### Part 3 — CNN-5 hyperparam fix

Update `BACKBONES["cnn5_cifar10"]`: `teacher_epochs=30, oracle_epochs=50, teacher_lr=0.005, warmup_epochs=10`. Re-run `jobs/heifd_fromscratch_verify.sh`. Sanity gate: CNN-5 IID raw_union ≥ 0.60.

## Acceptance criteria

- [ ] LoRA + last_n_blocks modes runnable for resnet18 + vit_b32 + distilbert (skip gpt2 — deferred).
- [ ] New unit test asserting `aggregate` linearity even with larger parameter sets (in `tests/test_aggregate.py`).
- [ ] `results/heifd_011_scope_resnet18/` shows whether gap closes per scope; recommend new default if so.
- [ ] CNN-5 re-verify produces IID raw_union ≥ 0.60.
- [ ] **HITL touchpoint**: a one-paragraph "methodology-impact" note in the case README — does the paper's "tiny head suffices" claim shift to "small adapter suffices"? Orchestrator will route to the user for the framing decision.

## Hard boundaries

- Touch `src/backbones.py`, `src/protocol.py` (BACKBONES), `src/sweep.py` (CLI arg if needed), new tests in `tests/test_aggregate.py`.
- Do NOT touch `src/distill.py` or `src/aggregate.py` semantics.
- New jobs: `jobs/heifd_011_trainable_scope.sh`.
- No push/commit/sbatch/ssh. ast.parse only.

## Report

1. LoRA implementation choice + rationale (peft vs hand-rolled).
2. Trainable-scope comparison table for resnet18.
3. Methodology-impact paragraph for the HITL review.
4. CNN-5 re-verify result.
5. Files touched.
