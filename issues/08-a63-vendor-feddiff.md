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

(none yet)
