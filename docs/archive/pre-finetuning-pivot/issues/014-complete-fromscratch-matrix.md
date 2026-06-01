# 014 — Complete the 3-dataset from-scratch matrix (LeNet/FMNIST + N=1 + CNN-5/CIFAR-10)  [AFK]

> **STATUS: ✅ DONE** (2026-05-29) — LeNet/FMNIST full grid 450/450 (defensible: α=0.05 raw_union 0.55 > no_phase0 0.24, m4 0.47; α=1.0 0.79 → oracle 0.88). MLP/MNIST N=1 baseline added (degenerate floor). CNN-5/CIFAR-10 grid ran but the backbone is **outside the basin-coherence envelope at low α** (see 016b distill-debug + 016b verdict) — teacher-bound, not a 014 defect. phase0 flatten-bridge bug (extreme-α dp_avg) fixed mid-flight. Verdict: `results/heifd_lenet_fmnist_headline/README.md`.

**Phase:** M1.5 / β (complete the from-scratch headline) · **Blocked by:** 011 for CNN-5 part · **Blocks:** 015 (DP-ε frontier on the full from-scratch matrix)

**Required reading:**
1. `docs/prd/he-ifd-tnse-resubmission.md` (Phase II — N grid is now {1, 5, 10, 20, 50}).
2. `CLAUDE.md`.
3. `docs/issues/007-from-scratch-headline-sweep.md` STATUS — MNIST/MLP done, FMNIST clean, CNN-5 needs 011.
4. `jobs/heifd_headline_fromscratch.sh` — template wrapper.

## What to build

Three sub-tasks, two runnable now and one blocked:

### Sub-task A — LeNet/FMNIST full grid (runnable NOW)

New wrapper `jobs/heifd_014_lenet_fmnist.sh` (based on `heifd_headline_fromscratch.sh`). Config:
```
--backbones lenet_fmnist
--Ns 1,5,10,20,50
--alphas 0.01,0.05,0.1,0.3,1.0
--methods no_phase0,warmup_only_labelled,labelled_probe_warmup,raw_union_K20,dp_avg_eps2_K20,dp_avg_eps8_K20
--seeds 42,43,44
--K 300
--case heifd_lenet_fmnist_headline
--num-chunks 8 (array)
```
= 450 cells across 8 chunks, ≤3h each.

### Sub-task B — Add N=1 to existing MNIST/MLP grid (runnable NOW)

Re-submit `jobs/heifd_headline_fromscratch.sh` with `HEIFD_NS=1`. Resumability means only the 90 new N=1 cells run. Same case slug `heifd_mlp_mnist_headline` — extends in place.

### Sub-task C — CNN-5/CIFAR-10 full grid (BLOCKED on 011)

Once issue 011 lands and `cnn5_cifar10` re-verify produces IID raw_union ≥ 0.60: new wrapper `jobs/heifd_014_cnn5_cifar10.sh`, config mirrors A with `--backbones cnn5_cifar10 --case heifd_cnn5_cifar10_headline`. 450 cells. **DO NOT submit until 011's verify gate passes.**

## Acceptance criteria

- [ ] LeNet/FMNIST full grid completes. Sanity gate: raw_union > no_phase0 and raw_union ≥ θ₀ at α=0.05 (or, if not, document the gap and escalate).
- [ ] N=1 cells emitted across all from-scratch backbones; expected behaviour: raw_union ≈ θ₀ at N=1 (no federation gain when there's one client), serves as a degenerate-case sanity floor.
- [ ] CNN-5/CIFAR-10 full grid queued post-011 (or noted as still blocked if 011 not yet landed).
- [ ] Results land under `results/heifd_lenet_fmnist_headline/`, `results/heifd_mlp_mnist_headline/` (extended), `results/heifd_cnn5_cifar10_headline/`.

## Hard boundaries

- Three new sbatch wrappers; minor `sweep.py` adjustments only if the existing CLI doesn't support what's needed (avoid changes if possible).
- No push/commit/sbatch/ssh.

## Report

1. LeNet/FMNIST headline numbers (concise: raw_union @ α=0.05 N=10 vs vs θ₀ + IID).
2. N=1 reference numbers (one-line per backbone).
3. CNN-5/CIFAR-10 status (queued? results?).
4. Files touched.
