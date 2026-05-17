# 08. A6.3 — Vendor FedDiff comparator (primary γ-variant competitor)

Status: ready-for-agent
Label: AFK
Priority: P3 (tier-1 DP comparator; primary γ-variant headline match)
Action-plan: A6.3 (folded into A4.1)
PRD-section: §3.2 (γ-variant), §3.4 (privacy comparison)

## Parent

Action plan A6 row "FedDiff" (line 166) — bold-flagged as primary γ-variant comparator. A4.1 method-row table (lines 257–267) lists FedDiff as tier-1-must-have.

## What to build

Vendor FedDiff (Mendieta–Sun–Chen WACV 2025, `feddiff2024`) under `comparators/feddiff/` and wrap with DP at ε ∈ {1, 10}.

1. **Vendoring:**
   - Upstream: `https://github.com/mendieta/FedDiff`.
   - Clone into `comparators/feddiff/`; pin commit hash in `COMMIT.txt`.
   - FedDiff trains a server-side DP-diffusion model and uses plaintext synthetic samples — this is the direct γ-variant competitor (same problem space, differing only in whether the distillation channel is plaintext or HE).
2. **`jobs/cfd_v2_comp_feddiff.sh`** — sbatch wrapper supporting `--epsilon $4` for ε ∈ {1, 10} per A4.1's DP-floor column.

The γ-vs-FedDiff comparison is the **headline privacy-utility-trade-off table** in the resubmission: same DP regime, same generator family (diffusion), differing in cryptographic protection of the distillation channel.

## Acceptance criteria

- [ ] `comparators/feddiff/COMMIT.txt` pins the upstream commit.
- [ ] `jobs/cfd_v2_comp_feddiff.sh` runs MNIST α=0.3 N=10 seed=42 ε=10 smoke without errors.
- [ ] DP accounting verified end-to-end (Opacus or whichever accountant FedDiff uses).
- [ ] Final student accuracy within ±5 pp of FedDiff's published MNIST number at the equivalent setting (sanity check).
- [ ] No login-node execution.

## Blocked by

- Issue 02.

## References

- Action plan A6 (lines 342–363), A4.1 method-row table (lines 257–267).
- PRD §3.2 (lines 107–119), §3.4 (lines 124–127).
- Upstream: `https://github.com/mendieta/FedDiff`.
- Bibkey: `feddiff2024`.

## Comments

### 2026-05-17 — vendor + wrap (wave-3 worker)

Status: vendored + wrapped; smoke deferred (QoS escalation pending per issue 03; upstream code also not yet populated — see caveat below).

**Vendoring:**
- Cloned `https://github.com/mmendiet/FedDiff` into `comparators/feddiff/`. **Note:** the issue brief originally pointed at `mendieta/FedDiff` (lowercase user), which does not exist. The canonical upstream is `mmendiet/FedDiff` — confirmed from the WACV 2025 PDF ("Code is available at https://github.com/mmendiet/FedDiff").
- Pinned SHA `e7d109dc263d67435c9be8b856d1f13f973da094` (main HEAD, 2024-12-04, "Initial commit") in `comparators/feddiff/COMMIT.txt`.

**Caveat — upstream not yet populated:** `mmendiet/FedDiff` currently ships only `LICENSE` + a placeholder `README.md`. The authors have not yet released the training/distillation code. The pin captures the upstream HEAD at vendoring time so future bumps are auditable; the COMMIT.txt documents the action list for when upstream populates.

**Wrapper — `jobs/cfd_v2_comp_feddiff.sh`:**
- Executable + `bash -n` clean.
- Headers: `--partition=t4_ai --account=comx29 --time=01:00:00 --gres=gpu:1 --mem=24G`; output/error pinned to `results/feddiff_smoke_%j.{out,err}`.
- CLI: `sbatch jobs/cfd_v2_comp_feddiff.sh <DATASET> <ALPHA> <SEED> <EPSILON>`.
- Activates conda env `he_ifd_comparators` (sibling-comparator convention; user creates env).
- Targets the conventional `main.py` entry-point. ε propagated via `--epsilon $4` (single source of truth in `EPS_FLAG` near the top of the wrapper, easy to swap to `--target_epsilon` / `--eps` once upstream argparser is published). Also passes `--delta 1e-5` and the dataset/alpha/seed/n_parties flags.
- DP accountant is **Opacus** (confirmed from the WACV 2025 paper: "employs the Opacus library in PyTorch to track privacy budgets ... Poisson batch sampling"). Wrapper extracts `epsilon` and `delta` lines from the run log into the output JSON.
- If `comparators/feddiff/main.py` is missing (current state), the wrapper writes a stub JSON tagged `status="upstream_not_populated"` and exits non-zero — preferable to a silent no-op smoke that would falsely satisfy the sbatch exit-code gate.
- Output: `results/feddiff_smoke_${SLURM_JOB_ID}.json` with `{student_acc, generator_epsilon_actual, generator_delta_actual, status, ...}`.

**Smoke command (deferred):**
```
sbatch jobs/cfd_v2_comp_feddiff.sh MNIST 0.3 42 10
```
(also `... 42 1` for the ε=1 cell once upstream code lands).

**Sanity expectation:** final student accuracy within ±5pp of FedDiff's published MNIST number at α=0.3, ε=10.

**Ambiguity to flag for HITL:**
1. Upstream code is still embargoed; the wrapper is unrunnable until `mmendiet/FedDiff` publishes. The `main.py` entry-point name and `--epsilon` flag name are best-guesses based on Opacus convention + prior repos by the same authors; reconfirm both once code lands.
2. Original issue URL (`mendieta/FedDiff`) should be corrected to `mmendiet/FedDiff` in any downstream docs / action plan / PRD references.

