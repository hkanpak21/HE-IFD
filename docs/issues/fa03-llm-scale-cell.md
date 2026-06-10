# fa03 — LLM-scale feasibility cell (billion-parameter backbone)

**Type:** AFK (compute + code). **Status:** 📥 OPEN. **Depends:** fa01 (winning config).
**PRD:** `docs/prd/he-ifd-freeze-a-improvement.md` addendum §5. **Ops:** `CLAUDE.md`.

## Why

arXiv:2412.04650 establishes that one-shot federated fine-tuning matches multi-round *at
foundation-model scale* — that regime is where our protocol's value is largest (the frozen
backbone never moves; only the adapter is encrypted). One feasibility cell widens the audience
beyond classifier heads and pre-empts "does this only work on toy encoders?"

## Task

One cell, not a grid: freeze-A LoRA one-shot federation on a ~1B-parameter causal LM that fits a
T4/Colab GPU — TinyLlama-1.1B or Qwen2.5-0.5B/1.5B (pick by what loads in fp16 with LoRA on 16GB;
gradient checkpointing if needed). Task: AG-News or DBpedia classification via the LM head-on-
last-token or a sequence-classification head, N=10, α=0.1, the fa01 winning config, 1–2 seeds.

## Acceptance criteria

- [ ] A0 / Astar / A_central row in the canonical improve schema, plus n_trainable and the
      ciphertext count the payload implies (feeds fa06's cost table).
- [ ] Wall-clock per client documented (the "one client's local computation" term of the
      end-to-end latency claim).
- [ ] Verdict: does the one-shot merge hold at this scale (positive increment, no collapse)?
      One paragraph for the paper either way.

## Notes

- This is a feasibility demonstration; do not let it creep into a sweep. If T4 memory blocks the
  1B model, the 0.5B variant is acceptable — the point is "transformer LM at causal-LM scale,"
  not a leaderboard.
- HF prefetch on the login node if run on VALAR; Colab can pull directly.
