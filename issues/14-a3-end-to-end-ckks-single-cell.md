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

### 2026-05-18 -- wave-7 scaffold landed (per-cell pipeline + shared schema)

The scaffold for one HE-IFD cell is in. No sbatch jobs submitted (per
orchestrator protocol; issue 18's fanout will do that). All files are
syntax-clean under `python3 -c "import ast; ast.parse(open(f).read())"` and
`bash -n`. `argparse --help` runs cleanly on the login node without
touching CKKS / data.

**Module map (owned by issue 14):**
- `prototypes/cell_schema.py` -- shared `CellResult` dataclass + JSON I/O.
  Issues 15, 18, 21 all import from here. Stdlib-only, dependency-free.
- `prototypes/heifd_train.py` -- single-cell orchestrator (Phases 1-9).
- `prototypes/heifd_lib/__init__.py` -- package marker + module map.
- `prototypes/heifd_lib/partitions.py` -- deterministic Dirichlet
  partition (seeded `np.random.RandomState`), plus a torchvision label
  loader.
- `prototypes/heifd_lib/teachers.py` -- LeNet-5 (MNIST / FashionMNIST) and
  ResNet-8 (CIFAR-10/100, SVHN) builders, plaintext SGD trainer with
  resume from `results/teachers_v2/<dataset>_a<alpha>_s<seed>/client_<i>.pt`,
  probe-pass + alpha_i computation.
- `prototypes/heifd_lib/encrypted_ensemble.py` -- thin wrapper that
  **reuses `prototypes/cfd_tenseal_smoke.py` primitives** (`create_context`,
  `chunk_rows_to_ciphertexts`, `beta_aggregation`, `lambda_variance`,
  `serialize_bytes`, `serialize_one_bytes`) so the depth audit stays in
  one place.
- `prototypes/heifd_lib/linear_accumulator.py` -- depth-<=3 encrypted SGD
  step, `AccumulatorState`, `compose_theta = <theta_0*> + <Delta>`.
- `prototypes/heifd_lib/evaluation.py` -- decrypt-and-apply,
  `eval_model_accuracy`, `mean_teacher_accuracy`, cached
  `oracle_accuracy`.
- `jobs/cell_heifd.sh` -- sbatch wrapper (`partition=t4_ai`,
  `account=comx29`, `qos=comx29`, env `he_ofl`).

**Variant matrix.**
- `warmstart` -- two-stage init + encrypted distillation (default).
- `randominit` -- skip Stage 1, encrypted distillation only.
- `warmstart-no-ensemble` -- Stage 1 + plaintext-probe-label SGD;
  bypasses the encrypted accumulator (ablation control).
- `epsilon` -- pipeline accepts the variant label and runs the warmstart
  path. Per-cell DP epsilon plumbing into `epsilon_actual` is deferred to
  issue 22 (DP-DDPM profiling); documented in `notes`.
- `gamma` -- **STUBBED**. Raises `NotImplementedError` with a clear
  "requires issue 22's DP-DDPM generators" message; writes a failed
  `CellResult` so the aggregator can audit which variants are stubbed.

**Other explicit stubs (per the issue 14 acceptance gate):**
- Multiparty key-switch (Phase 0 DKG + Phase 4 collective decrypt) is
  approximated by single-key TenSEAL decrypt; multiparty is the production
  target. The smoke records this in `CellResult.notes`.
- The encrypted accumulator updates only the final-layer bias (matches
  what `prototypes/cfd_tenseal_smoke.py` already validated as depth<=3);
  full-parameter tiling across CKKS slots is the production target.

**Per-cell submission command:**
```
sbatch jobs/cell_heifd.sh MNIST 0.3 42 warmstart
```
Result JSON lands at
`results/cells/heifd_MNIST_a0.3_s42_warmstart_<JOBID>.json`.

**Expected wall-clock per cell (T4, defaults `--probe 5000 --E1 30
--E2 200 --T-epochs 30 --N 10`):**
- MNIST / LeNet-5: ~30-45 min (teachers ~10 min if not cached, probe
  pass <1 min, encrypted target ~3-5 min, distillation ~15-20 min,
  eval <1 min).
- CIFAR-10 / ResNet-8: ~60-90 min (teachers dominate).
- CIFAR-100: closer to the wall-clock cap; bump `--time` if needed.
- Re-runs of the same (dataset, alpha, seed) hit the teacher cache
  under `results/teachers_v2/` and skip Phase 2 entirely.

**Coordination notes for siblings.**
- Issue 15 (A4-sanity preflight): reads
  `from cell_schema import CellResult` to validate JSON blobs.
- Issue 18 (fanout/aggregator): the `CellResult.default_path()`
  convention is the on-disk contract; the aggregator can glob
  `results/cells/heifd_*.json` safely.
- Issue 21 (MIA): MIA-specific fields land in `notes` and via additional
  CellResult writes alongside the headline `student_acc`; the dataclass
  is small enough that we can extend in-place if MIA needs structured
  fields (coordinate the schema bump across the four issues).
