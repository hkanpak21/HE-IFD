# 09. A6.4 — Vendor FedKT comparator (canonical PATE-style DP baseline)

Status: ready-for-agent
Label: AFK
Priority: P3 (tier-1 DP comparator)
Action-plan: A6.4 (folded into A4.1)
PRD-section: §3.4

## Parent

Action plan A6 row "FedKT" (line 167) — tier-1 DP-floor comparator.

## What to build

Vendor FedKT (Li et al. 2021, `li2021fedkt`) under `comparators/fedkt/` and wrap with DP-SGD via Opacus at ε ∈ {1, 10}.

1. **Vendoring:**
   - Upstream: `https://github.com/QinbinLi/FedKT`.
   - Clone into `comparators/fedkt/`; pin commit hash.
   - FedKT is a PATE-style aggregation; DP-SGD teachers compose via PATE's voting-based aggregation. Verify the DP composition is preserved end-to-end after we wire in Opacus.
2. **`jobs/cfd_v2_comp_fedkt.sh`** — sbatch wrapper supporting `--epsilon $4`.

## Acceptance criteria

- [ ] `comparators/fedkt/COMMIT.txt` pins the upstream commit.
- [ ] `jobs/cfd_v2_comp_fedkt.sh` runs MNIST α=0.3 N=10 seed=42 ε=10 smoke without errors.
- [ ] DP accounting verified (Opacus accountant log line in output).
- [ ] No login-node execution.

## Blocked by

- Issue 02.

## References

- Action plan A6 (lines 342–363), A4.1 method-row table (lines 257–267).
- Upstream: `https://github.com/QinbinLi/FedKT`.
- Bibkey: `li2021fedkt`.

## Comments

(none yet)
