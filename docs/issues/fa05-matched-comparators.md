# fa05 — Matched-setup comparator runs

**Type:** AFK (compute). **Status:** 📥 OPEN. **Depends:** fa01 (winning config).
**PRD:** `docs/prd/he-ifd-freeze-a-improvement.md` (Solution + addendum §3). **Ops:** `CLAUDE.md`.

## Why

R2-1/R3-5: comparing our numbers at our setup against others' numbers at their setups was a
rejection driver. Repo rule: never re-run vendor code — run HE-IFD on *their* published setup and
place the numbers side by side. User decision: multiple matched setups, select for the table later.

## Task

Configure HE-IFD (fa01 winning config) to reproduce the published evaluation setup (dataset,
N, partition, model class as close as the protocol allows) of, in priority order:

1. **FedAUXfdp** (arXiv:2205.14960) — the DP one-shot peer; their CIFAR-10 N/α split.
2. **FedKT** (li2021fedkt) — DP one-shot; their MNIST-class setup (use our from-scratch-free
   analogue honestly: frozen backbone + head on the same data/partition; document the deviation).
3. **FedSD2C** (NeurIPS 2024, arXiv:2412.05186) — plaintext one-shot SOTA; their Tiny-ImageNet
   α=0.1 split if feasible with a frozen ViT.
4. (Stretch) **SHE-LoRA** (arXiv:2505.21051) — match one of their federated LoRA tasks so the
   cost-table contrast (fa06) also carries an accuracy point.

Every setup gets a `results/<case>/` dir with the partition documented
(`partition_diagnostic.jsonl`) and explicit notes on any unavoidable deviation.

## Acceptance criteria

- [ ] ≥2 matched setups run with 3 seeds; per-setup README states the source paper's reported
      number verbatim (from `comparators/REPORTED_RESULTS.md` discipline — quote, never recall).
- [ ] A draft "matched comparison" table fragment: ours-at-their-setup vs theirs-verbatim, with
      privacy-target footnote (DP protects the released artifact against everyone; we protect
      contributions cryptographically and release the model to participants by design).
- [ ] Recommendation: which matches go in the paper (user selects).
