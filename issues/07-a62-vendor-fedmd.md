# 07. A6.2 — Vendor FedMD comparator

Status: ready-for-agent
Label: AFK
Priority: P3 (tier-1 no-DP comparator)
Action-plan: A6.2 (folded into A4.1)
PRD-section: §3.1 (FedMD's 5000-sample probe convention)

## Parent

Action plan A6 row "FedMD" (line 165).

## What to build

Vendor FedMD (Li & Wang 2019, `li2019fedmd`) under `comparators/fedmd/` and wrap into our jobs harness.

1. **Vendoring:**
   - Upstream: `https://github.com/diogenes0319/FedMD_clean`.
   - Clone into `comparators/fedmd/`; pin commit hash in `comparators/fedmd/COMMIT.txt`.
   - Apply minimal adapter shim if FedMD's public-probe size or partition convention differs from our N=10 + 5000-probe setup.
2. **`jobs/cfd_v2_comp_fedmd.sh`** — sbatch wrapper, partition=t4_ai, `--dataset $1 --alpha $2 --seed $3`.

FedMD is plaintext one-shot federated distillation; the original 5000-sample probe convention is precisely what PRD §3.1 anchors our α-variant to.

## Acceptance criteria

- [ ] `comparators/fedmd/COMMIT.txt` pins the upstream commit.
- [ ] `jobs/cfd_v2_comp_fedmd.sh` runs MNIST α=0.3 N=10 seed=42 smoke without errors.
- [ ] Final student accuracy ≥ 0.9 on MNIST (sanity check; FedMD's published number).
- [ ] No login-node execution.

## Blocked by

- Issue 02.

## References

- Action plan A6 (lines 342–363).
- PRD §3.1 (lines 99–106).
- Upstream: `https://github.com/diogenes0319/FedMD_clean`.
- Bibkey: `li2019fedmd`.

## Comments

### 2026-05-17 — vendor + wrapper landed (wave 3, agent-07); smoke deferred

- Cloned `https://github.com/diogenes0319/FedMD_clean` into `comparators/fedmd/`.
- Upstream HEAD pinned in `comparators/fedmd/COMMIT.txt`:
  `ab7a07b02c978f4c7871841bd68d2b776705bd97` ("Update README.md").
- Probe / party convention: upstream `conf/EMNIST_balance_conf.json` and
  `conf/CIFAR_balance_conf.json` already set `N_parties=10` and
  `N_alignment=5000`. Matches PRD §3.1 exactly — **no probe-size or
  party-count adapter shim needed**.
- Partition convention: upstream uses BALANCED `N_samples_per_class` (not
  Dirichlet α). The wrapper accepts `--alpha` for CLI parity and exports it
  as `FEDMD_ALPHA`, but the upstream code path ignores it. A proper Dirichlet
  shim against `data_utils.generate_bal_private_data` is left as a follow-up;
  for the canonical sanity smoke (which only needs to reproduce the upstream
  ≥0.9 student accuracy) the balanced partition is correct.
- Seed: upstream offers no seed CLI; we export `FEDMD_SEED` for future use
  and otherwise rely on the global TF/Keras default. Deterministic reseeding
  deferred.
- Dataset mapping in wrapper:
  - `MNIST` / `FEMNIST` / `EMNIST` → `FEMNIST_Balanced.py` +
    `conf/EMNIST_balance_conf.json` (this is FedMD's canonical "MNIST" smoke:
    MNIST is the *public probe*, EMNIST-letters is the *private* training
    set; matches the README demo invocation and the published 0.99+
    accuracy).
  - `CIFAR` / `CIFAR10` / `CIFAR100` → `CIFAR_Balanced.py` +
    `conf/CIFAR_balance_conf.json`.
- Wrapper: `jobs/cfd_v2_comp_fedmd.sh`. `chmod +x` set; `bash -n` clean.
  Writes `results/fedmd_smoke_${SLURM_JOB_ID}.json` with key `student_acc`
  (parsed from the last `acc: <float>` line in the run log).
- Conda env `he_ifd_comparators` does NOT exist yet on Valar
  (`conda env list` 2026-05-17). Wrapper activates it; env creation is a
  prerequisite for the smoke and is called out in the wrapper header.
- **Smoke status: DEFERRED.** Submission gated on creation of the
  `he_ifd_comparators` conda env (TF/Keras + numpy + scipy stack for FedMD).
  Smoke command, ready to fire once env exists:

  ```
  sbatch jobs/cfd_v2_comp_fedmd.sh MNIST 0.3 42
  ```

  Sanity expectation: final `student_acc` ≥ 0.9 on MNIST (FedMD paper
  reports >0.99 on the FEMNIST-balanced config whose public probe is MNIST).
