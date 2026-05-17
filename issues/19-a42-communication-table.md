# 19. A4.2 communication table (triple-axis Pareto: comm axis)

Status: ready-for-agent
Label: AFK
Priority: P4 (downstream of 18; consumes its per-cell bytes measurements)
Action-plan: A4.2
PRD-section: §5

## Parent

Action plan A4.2 (lines 318–328).

## What to build

Produce the communication-axis comparison table:

| Method family | Comparator | What to report | Source |
|---|---|---|---|
| Ours (HE-IFD α) | — | Total bytes/client to convergence; per-phase breakdown | Issue 14 (A3 single cell) + issue 18 (grid) |
| Ours (HE-IFD γ) | — | Same + encrypted-synthetic upload bytes | Issue 14 + issue 24 (γ cells) |
| HE multi-round FL | POSEIDON, CURE, FedSHE, BatchCrypt | Bytes/client per round × rounds-to-convergence | Cited from each paper at closest matching dataset / model |
| No-DP one-shot FL | FedMD, DENSE, FedDF, Co-Boosting, FuseFL | Total bytes/client (one round each) | Measured during issue 18 |
| DP one-shot FL | FedKT, FedMD-NFDP, FedDM | Total bytes/client (one round each) | Measured during issue 18 |

**No re-runs of HE multi-round comparators** per action plan A4.2 line 327: published numbers are sufficient and reproducible; re-running POSEIDON/CURE/FedSHE/BatchCrypt at our settings would consume the entire compute budget for marginal accuracy on numbers their authors already report.

**Honest-framing caption** must include the action plan's verbatim note (lines 322–323): "HE multi-round FL solves standard federated averaging under HE; HE-IFD solves one-shot federated distillation under HE. The comparison is asymmetric in protocol scope but matched in cryptographic regime."

**Output:**
- `results/A4_2_communication_table.csv` and `.tex`.
- A `\input{...}` reference from `experiments.tex` per CHANGES.md convention.

## Acceptance criteria

- [ ] Table covers all five method families above.
- [ ] HE multi-round numbers cited with bibkey at the closest matching (dataset, model) pair.
- [ ] Ours-α bytes/client matches PRD §5 estimate (~8 MB/client at MNIST/CIFAR-10 N=10) to within 20 % (sanity check; if drift > 20 %, investigate).
- [ ] Honest-framing caption present.
- [ ] `experiments.tex` `\input{...}` updated.
- [ ] `FL_TDSC/CHANGES.md` logged.

## Blocked by

- Issue 14 (A3 single cell provides the per-phase bytes/client for ours).
- Issue 18 (grid provides comparator bytes/client).

## References

- Action plan A4.2 (lines 318–328).
- PRD §5 (lines 171–186).

## Comments

(none yet)
