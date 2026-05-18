# Decision log

Append-only ledger of peripheral tweaks applied during HE-IFD resubmission execution. Format defined by PRD §9.5.6 in [2026-05-05_methodology_pivot.md](2026-05-05_methodology_pivot.md). The cover-letter draft (§3) cites this log as the audit trail for the "what we did during the resubmission" framing.

Stable-core changes (per PRD §9.5.1) do **not** appear here — they require explicit user re-approval and are tracked through the issue-tracker's `Comments` section instead.

Entry template:

```
## YYYY-MM-DD — A<n> — <short slug>

- Tweak: <peripheral> <old> → <new>
- Reason: <one sentence>
- Report: reports/YYYY-MM-DD_tweak_<slug>.md
- Impact: <none / hours / days / weeks>
```

---

## 2026-05-17 — A2 — smoke-memory-budget

- Tweak: sbatch --mem 16G → 64G for `jobs/smoke_tenseal.sh`
- Reason: job 1079639 OOM-killed mid-encryption; TenSEAL key set + ciphertext-mult intermediates exceed 16 GB at logN=14 / N=10 / |P|=5000.
- Report: reports/2026-05-17_tweak_smoke_memory.md
- Impact: none on methodology; ≈ 30 min wall-clock to reconfirm the depth-≤-3 claim.

## 2026-05-17 — A2 — smoke-probe-size

- Tweak: --probe 5000 → 1000 in `jobs/smoke_tenseal.sh` (peripheral per PRD §9.5.2 "Probe size")
- Reason: job 1079768 (64G memory) also OOM-killed at 10 min; consistent with steady TenSEAL ctxt-mult intermediate accumulation in the β-aggregation loop. Depth audit is invariant under probe size.
- Report: reports/2026-05-17_tweak_smoke_probe.md
- Impact: none on methodology; smaller probe still validates depth-≤-3 (the linear-accumulator construction's primitives).
