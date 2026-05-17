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

(none yet)
