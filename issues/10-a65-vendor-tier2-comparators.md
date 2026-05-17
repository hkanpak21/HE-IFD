# 10. A6.5 — Vendor tier-2 comparators (FedDF, DENSE, FuseFL, FedMD-NFDP, FedDM)

Status: ready-for-agent
Label: AFK
Priority: P3 (tier-2 comparators; conditional inclusion)
Action-plan: A6.5 (folded into A4.1)
PRD-section: §3.4

## Parent

Action plan A6 rows for tier-2 comparators (lines 168–172). Tier-2 inclusion is conditional on weeks 5–6 vendoring landing cleanly per action plan A4.1 lines 263–267.

## What to build

Vendor five tier-2 comparators in parallel, one subdirectory each. Each has its own sbatch wrapper.

| Comparator | Bibkey | Upstream | Privacy regime |
|---|---|---|---|
| FedDF | `lin2020feddf` | `github.com/epfml/federated-learning-public-code` | no-DP |
| DENSE | `zhang2022dense` | `github.com/zj-jayzhang/DENSE` | no-DP |
| FuseFL | `tang2024fusefl` | `github.com/wizard1203/FuseFL` | no-DP (verify M=5 → N=10 mapping) |
| FedMD-NFDP | `sun2021fedmdnfdp` | `github.com/MingruiSun2019/FedMD-NFDP` | DP at ε ∈ {1, 10} |
| FedDM | `xiong2023feddm` | `github.com/yuanhaoxiong/FedDM` | DP optional; adapt to single-round per A6 note |

For each:
1. Clone under `comparators/<method>/`; pin commit hash in `COMMIT.txt`.
2. Author `jobs/cfd_v2_comp_<method>.sh` sbatch wrapper.
3. Smoke-run on MNIST α=0.3 N=10 seed=42 (DP variants at ε=10).

Per the action plan's three-strike debug protocol (PRD §9.5.5): if vendoring fails twice consecutively for any one comparator, drop it and replace with the most-recent untried tier-2 alternative in the same privacy regime (per PRD §9.5.2 row "Comparator set"). Log every drop / replacement in `reports/decision_log.md`.

## Acceptance criteria

- [ ] All five `comparators/<method>/COMMIT.txt` files exist with pinned hashes.
- [ ] All five sbatch wrappers exist and smoke on MNIST α=0.3 N=10 seed=42 without error.
- [ ] Any drops/replacements logged in `reports/decision_log.md` with a tweak report per PRD §9.5.3.
- [ ] No login-node execution.

## Blocked by

- Issue 02.

## References

- Action plan A6 (lines 342–363), A4.1 (lines 244–316).
- PRD §3.4, §9.5.2 (peripheral row "Comparator set"), §9.5.5 (three-strike debug).

## Comments

(none yet)
