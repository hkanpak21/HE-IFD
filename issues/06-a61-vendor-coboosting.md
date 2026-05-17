# 06. A6.1 — Vendor Co-Boosting comparator

Status: ready-for-agent
Label: AFK
Priority: P3 (tier-1 no-DP comparator; reusable from May-5)
Action-plan: A6.1 (folded into A4.1)
PRD-section: §3.4 (Co-Boosting as privacy-unaware ceiling)

## Parent

Action plan A6 row "Co-Boosting" (line 165) + PRD §3.4 (lines 124–127).

## What to build

Wrap Co-Boosting (Dai et al. ICLR 2024, `dai2024coboosting`) into our jobs harness. The May-5 implementation at `experiments/coboost_baseline.py` (referenced in action plan line 165 — likely in the legacy archive at `legacy/`) is the reuse base. Two artefacts:

1. **`comparators/coboosting/`** — vendored or pinned implementation. Approach:
   - If May-5's `experiments/coboost_baseline.py` is reusable as-is, copy to `comparators/coboosting/coboost_baseline.py` with no modifications and record provenance in `comparators/coboosting/COMMIT.txt`.
   - Else port from upstream `https://github.com/yuanyuanyuan/Co-Boosting` (or whichever commit the May-5 code was based on); pin commit hash in `COMMIT.txt`.
2. **`jobs/cfd_v2_comp_coboost.sh`** — sbatch wrapper that runs Co-Boosting on our (dataset, α, N=10, seed) grid cell. Arguments: `--dataset $1 --alpha $2 --seed $3`.

Co-Boosting is plaintext; no CKKS involvement. Privacy framing per PRD §3.4: "the privacy-unaware ceiling: the strongest unencrypted one-shot baseline."

## Acceptance criteria

- [ ] `comparators/coboosting/` exists with the implementation and `COMMIT.txt`.
- [ ] `jobs/cfd_v2_comp_coboost.sh` runs end-to-end on MNIST α=0.3 N=10 seed=42 as a smoke check.
- [ ] Smoke output (final student accuracy) written to `results/coboost_smoke_<job_id>.json`.
- [ ] No login-node execution.

## Blocked by

- Issue 02 (Ralph scaffold; jobs harness conventions need to be set).

## References

- Action plan A6 (lines 342–363), A4.1 (lines 244–316).
- PRD §3.4 (lines 124–127).
- Upstream: `https://github.com/yuanyuanyuan/Co-Boosting` (Co-Boosting ICLR 2024).
- Bibkey: `dai2024coboosting`.

## Comments

(none yet)
