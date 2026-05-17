# 25. A13 ViT-tiny / ViT-small feasibility extension

Status: ready-for-agent
Label: AFK
Priority: P4 (downstream extension; user-added 2026-05-17)
Action-plan: A13
PRD-section: §9.5.2 row "Student architecture"

## Parent

Action plan A13 (line 467) — "Modern-architecture feasibility extension (ViT-tiny / ViT-small; user-added 2026-05-17)".

## What to build

Feasibility analysis + small-scale measurement of running the CFD protocol on a modern transformer student rather than LeNet-5. Scope:

**Phase A — Feasibility scoping (no compute):**
- Document the depth-and-parameter implications of DeiT-tiny / ViT-tiny (5M params, 12 transformer blocks, MHSA) under the linear-accumulator construction.
- Verify per-step depth ≤ 3 still holds — since the construction uses plaintext student forward pass, network architecture is irrelevant to HE depth budget.
- Verify communication cost: ViT-tiny @ ~5M params → student download ~5M × 4B × 32× CKKS expansion ≈ 640 MB/client (vs LeNet-5's 8 MB). This is the key trade-off — utility gain vs comm cost.
- Document findings in `reports/2026-MM-DD_a13_vit_feasibility.md`.

**Phase B — Single-cell smoke (compute, ~2–4 GPU-h):**
- Run α-warmstart CFD on MNIST α=0.3 N=10 with DeiT-tiny student.
- Compare final accuracy + wall-clock vs LeNet-5 baseline from issue 14.
- Decision rule per PRD §9.5.2 row "Student architecture": **never run a student requiring > 50 M params under HE** — DeiT-tiny at 5M is well within budget.

**Phase C — Extension into A4.1 (conditional):**
- If Phase B shows ≥ 2 pp accuracy lift over LeNet-5 AND wall-clock stays within 4× LeNet-5: add a single "Architecture: DeiT-tiny" row to issue 18's grid at the most stringent non-IID setting (α=0.05).
- Otherwise: report Phase B numbers as a discussion paragraph in §V, no grid inclusion.

## Acceptance criteria

- [ ] Phase A feasibility report exists with the depth + comm + utility trade-off table.
- [ ] Phase B smoke run completes; `results/a13_vit_smoke_<job_id>.json` records final accuracy + wall-clock.
- [ ] Phase C decision documented in `reports/decision_log.md`.
- [ ] No login-node execution.

## Blocked by

- Issue 04 (A2 TenSEAL smoke must validate the linear-accumulator primitives on a non-trivial student first).

## References

- Action plan A13 (line 467).
- PRD §9.5.2 row "Student architecture", §9.5.6 (decision log).

## Comments

(none yet)
