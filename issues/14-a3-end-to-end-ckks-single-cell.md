# 14. A3 end-to-end CKKS run on a single cell (MNIST α=0.3 N=10 LeNet-5)

Status: ready-for-agent
Label: AFK
Priority: P3 (calibration anchor for A4; locks [R2-Q2])
Action-plan: A3
PRD-section: §4.1 (phases), §4.2 (β/λ), §4.3 (depth budget after linear-accumulator patch)

## Parent

Action plan A3 (lines 209–231) — **committed (locked 2026-05-10)**.

## What to build

A real-HE end-to-end run on one cell of A4's grid (default: MNIST α=0.3, N=10, LeNet-5 student) covering all five phases of PRD §4.1:

- **Phase 0:** DKG (multiparty CKKS, $t=N$).
- **Phase 1:** client logit upload.
- **Phase 2:** β-aggregation + λ variance (PRD §4.2).
- **Phase 3:** linear-accumulator SGD updates on $\langle\theta\rangle$ against $\widetilde Y$ on plaintext probe inputs (per memory `project-linear-accumulator`).
- **Phase 4:** collective key-switch on $\langle\theta_E\rangle$ → plaintext $\theta_E$ at each client.

**Library:** TenSEAL (action plan A3 line 38: locked 2026-05-17). No native bootstrapping needed because per-step depth ≤ 3.

**Reuse base:** port `legacy/toy_ifd_real_he.py` (already-working TenSEAL ops in this codebase) to the CFD four-phase structure.

**Measurements per phase:**
- Wall-clock seconds.
- Rotation counts.
- Memory peak.
- $\langle\theta_E\rangle$-vs-plaintext-$\theta_E$ discrepancy: max-norm and cosine similarity.

**Output:**
- `prototypes/cfd_end_to_end_ckks.py` (the orchestrator).
- `jobs/cfd_end_to_end_single_cell.sh` (sbatch wrapper, partition=t4_ai, time budget per protocol simplicity estimate ~6h).
- `results/cfd_e2e_<job_id>.json` with per-phase measurements + final accuracy.

## Acceptance criteria

- [ ] `prototypes/cfd_end_to_end_ckks.py` exists.
- [ ] `jobs/cfd_end_to_end_single_cell.sh` exists, partition=t4_ai.
- [ ] End-to-end run completes on MNIST α=0.3 N=10 seed=42 LeNet-5.
- [ ] Final $\theta_E$ accuracy on MNIST test ≥ 0.95 (near the May-5 0.965 with 30-epoch teachers; this run uses 100-epoch teachers per A4).
- [ ] $\langle\theta_E\rangle$-vs-plaintext-$\theta_E$ cosine similarity ≥ 0.99.
- [ ] Per-phase wall-clock, rotation counts, memory peak persisted to JSON.
- [ ] No login-node execution; no bootstrapping invoked (assertion in code).

## Blocked by

- Issue 04 (A2 TenSEAL smoke must validate β/λ + linear-accumulator depth-≤-3 first).

## References

- PRD §4.1 (lines 134–148), §4.2 (lines 150–168), §4.3 (post-patch by issue 01).
- Action plan A3 (lines 209–231).
- Memory: `project-linear-accumulator`, `valar`.
- Legacy code: `legacy/toy_ifd_real_he.py`, `legacy/toy_ifd_ckks.py`, `legacy/toy_ifd.py`.

## Comments

(none yet)
