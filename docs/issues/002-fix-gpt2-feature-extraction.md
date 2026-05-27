# 002 — Fix GPT-2 feature extraction + regression test  [AFK]

**Milestone:** M1 · **Blocked by:** 001 · **Blocks:** 003 (backbones test), 008 (pretrained sweep)

**Required reading:** [`docs/prd/...`](../prd/he-ifd-tnse-resubmission.md), [`CLAUDE.md`](../../CLAUDE.md), and the notebook's `extract_text_features` (the buggy function).

## What to build

Fix the GPT-2 sentence-embedding bug in `backbones.py`. The notebook mean-pools `last_hidden_state` over a **right-padded causal-attention** sequence with `pad_token = eos_token`, which produces degenerate features — every GPT-2 / AG-News cell sits at ~25% (chance for 4 classes), *including IID α=1.0 with no protocol*. That is a feature-extraction bug, not a method limitation.

Fix: for GPT-2, set `tokenizer.padding_side = "left"` and take the **last token's** hidden state (`last_hidden_state[:, -1, :]`), or equivalently index the last non-pad position. DistilBERT (bidirectional) mean-pooling stays as-is.

## Acceptance criteria

- [ ] GPT-2 text features come from the last real token under left-padding (not a mean-pool over padded causal states).
- [ ] DistilBERT extraction unchanged.
- [ ] **Regression test** (in `backbones`): GPT-2 on a small AG-News subset, IID/no-protocol, yields **non-trivial accuracy (≥ ~0.80, well above the 0.25 chance floor)**. The test must fail on the old mean-pool code and pass on the fix.

## How to verify

Run the regression test (tiny subset, fast enough for a short `srun` sanity check or a small `sbatch`). Confirm GPT-2 IID accuracy is in the ~0.90 band, not ~0.25.

## Ops

`sbatch`/`srun` for any model load; never on the login node. GPT-2 weights must be **pre-fetched on the login node** (compute nodes lack internet) — see CLAUDE.md networking note; load with `HF_HUB_OFFLINE=1`.
