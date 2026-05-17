# 22. A5 DP-DDPM profiling micro-task (γ-scope gate)

Status: ready-for-agent
Label: AFK
Priority: P3 (closes γ-variant scope conditional path)
Action-plan: A5 profiling micro-task
PRD-section: §3.2

## Parent

Action plan A5 "Profiling micro-task" (lines 327–331) — gates §8 item 10; the gate closes end of week 2.

## What to build

`prototypes/dpdm_profile.py` — a single-client DP-DDPM training run to measure $h$, the wall-clock hours to train one DP-DDPM on a single client's partition on T4. Plus `jobs/dpdm_profile.sh` sbatch wrapper.

**Profiling spec per A5:**
- 1 client, MNIST partition (~5–6k samples at N=10 with α=0.3).
- ε=10 (Dockhorn et al. TMLR 2022 headline budget).
- Single `t4_ai` node.
- Captures: wall-clock to FID-plateau convergence, GPU memory peak, samples/sec.
- Target wall-clock: ≤ h hours by definition (the measured value *is* h).
- Reference implementation: `github.com/nv-tlabs/DPDM`. U-Net ~2–3M params.

**Conditional paths based on profiling result (PRD §8 item 10 + action plan A5 lines 333–339):**
- **h ≤ 3 h → full-grid path.** γ becomes the 4th column in A4's headline grid. Issue 23 (generators) executes in weeks 5–6 in parallel with teacher re-training.
- **3 h < h ≤ 8 h → subset path.** γ runs as separate table at 1 α per dataset (5 pairs). Issue 23 executes in weeks 11–14.
- **h > 8 h → CIFAR-100/SVHN exclusion.** γ runs subset only on MNIST + FashionMNIST + CIFAR-10 (3 pairs). Drop SVHN + CIFAR-100 from γ scope per PRD §9.5.2 row "Dataset set". Log the drops in `reports/decision_log.md` per §9.5.3.

The result of this profiling sets the γ-scope for issues 23 and 24. Write the gate decision in `reports/decision_log.md` with a one-page tweak report at `reports/2026-MM-DD_tweak_gamma_scope.md`.

## Acceptance criteria

- [ ] `prototypes/dpdm_profile.py` exists.
- [ ] `jobs/dpdm_profile.sh` exists, partition=t4_ai, time budget 12h (cap).
- [ ] sbatch run completes; FID plateau reached or wall-clock cap hit (whichever first).
- [ ] `results/dpdm_profile_<job_id>.json` records: wall-clock hours, peak GPU memory MB, samples/sec, final FID.
- [ ] One-page tweak report at `reports/2026-MM-DD_tweak_gamma_scope.md` declaring the conditional path chosen.
- [ ] One-line entry in `reports/decision_log.md`.
- [ ] No login-node execution.

## Blocked by

- Issue 02 (Ralph scaffold + decision log infrastructure).

## References

- Action plan A5 (lines 317–341), particularly the profiling micro-task at lines 327–339.
- PRD §3.2 (lines 107–119), §8 item 10, §9.5.2 (peripherals).
- Upstream: `https://github.com/nv-tlabs/DPDM`.
- Bibkey: `dockhorn2022dpdm`.

## Comments

### 2026-05-17 — wave-5 scaffolding (worker agent, AFK)

**Scaffolded this commit (no GPU run):**

- Cloned upstream `nv-tlabs/DPDM` into `comparators/dpdm_upstream/`. HEAD SHA
  `29bb94d92bb5440a664dbaa915c06a7397ea9ff3` ("updated TMLR"), pinned in
  `comparators/dpdm_upstream/COMMIT.txt`.
- Authored `prototypes/dpdm_profile.py`. Imports the upstream
  `runners.train_dpdm_base.training` entry point and:
    - Monkey-patches `torchvision.datasets.MNIST.__init__` so the dataset
      returned to the trainer is restricted to client-0 indices from a
      Dirichlet(α=0.3) label partition (N=10 clients, seed=42). Matches the
      HE-IFD Hsu-et-al-style non-IID convention.
    - Loads `configs/mnist_28/train_eps_10.0.yaml` and overrides
      `setup.n_gpus_per_node=1`, `train.batch_size=2048`,
      `dp.max_physical_batch_size=256`, `dp.n_splits=8`,
      `train.fid_freq=2000`, `train.fid_samples=5000`, `dp.epsilon=10.0`,
      `dp.delta=1e-5`. (Upstream defaults assume 8× A100 80 GB; T4 16 GB
      requires the smaller batch + larger split.)
    - Installs a `logging.Handler` plateau watcher that parses the upstream's
      `FID %d at iteration %d: %.6f` log lines and raises `PlateauReached`
      when the best FID over the last 4 evaluations has not improved by
      more than 1.0 relative to the best before that window (eval cadence
      K=2000 iters → ≥ 8000 unimproved iters before exit).
    - Installs a `SIGALRM` watchdog at 12.0 h so the wrapper exits cleanly
      against the SLURM time cap.
    - Writes the summary to `results/dpdm_profile_${SLURM_JOB_ID}.json`
      (defaults to `local` if unset) with fields: `wall_clock_hours`,
      `peak_gpu_memory_mb`, `samples_per_sec`, `final_fid`,
      `termination_reason`, `fid_history`, plus a snapshot of the profile
      config.
- Authored `jobs/dpdm_profile.sh` sbatch wrapper. Headers per spec:
  `--partition=t4_ai --account=comx29 --time=12:00:00 --gres=gpu:1 --mem=24G`.
  Activates conda env `he_ifd_gamma` (user creates; install command in
  wrapper comment block).

**Deferred (cannot be done on the login node):**

- The actual 12 h sbatch run.
- The `results/dpdm_profile_<job_id>.json` deliverable.
- The γ-scope conditional-path decision in `reports/decision_log.md`
  (one-line entry).
- The one-page tweak report at
  `reports/2026-MM-DD_tweak_gamma_scope.md` per PRD §9.5.3.
- Conda env `he_ifd_gamma` creation. Wrapper assumes it exists; install
  block is documented inline.

**User's next step (single command):**

```bash
sbatch jobs/dpdm_profile.sh
```

When the job completes, decide the γ-scope from the measured
`wall_clock_hours` (= h) per PRD §8 item 10 + action plan A5 lines
333–339:

- `h ≤ 3` → **full-grid path.** γ becomes the 4th column in A4's headline
  grid. Issue 23 (generators) runs in weeks 5–6 in parallel with teacher
  re-training.
- `3 < h ≤ 8` → **subset path.** γ runs as a separate table at 1 α per
  dataset (5 pairs). Issue 23 runs in weeks 11–14.
- `h > 8` → **CIFAR-100/SVHN exclusion.** γ runs subset only on
  MNIST + FashionMNIST + CIFAR-10 (3 pairs); drop SVHN + CIFAR-100 from γ
  scope per PRD §9.5.2 row "Dataset set"; log the drops in
  `reports/decision_log.md` per §9.5.3.

After deciding, append the one-line entry to `reports/decision_log.md`
and write the tweak report at
`reports/2026-MM-DD_tweak_gamma_scope.md`. Then this issue can be moved
to `issues/done/`.
