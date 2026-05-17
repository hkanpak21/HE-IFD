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

(none yet)
