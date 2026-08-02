# Paper expansion backlog — closing the gap to a full TNSE submission

The compiled draft (~10pp) is a lean skeleton. This is the prioritized list of what to add, mapped to the
TDSC reviewer concerns it answers. Most items need only writing + replotting from data already in
`results/`; only the MIA study needs new compute.

## A — have the data, needs writing + a plot/table

| # | Item | Answers | Source |
|---|------|---------|--------|
| 1 | N-scalability figure (N∈{5,10,20,50}) | R1-W1 | results.csv (N already swept) |
| 2 | Bounded-trajectory K-sweep figure (shows long K reintroduces conflict) | methodology rigor | K-sweep cells |
| 3 | Alignment-source comparison table (raw / DP / synthetic / no-probe) | R3-1, novelty | 016/017 + headline |
| 4 | Numeric baseline table vs DP one-shot peers + POSEIDON | R2-Q1, R3-5, AE-7 | comparators/REPORTED_RESULTS.md |
| 5 | Communication & computation complexity analysis (subsection) | R1-W1, R2-Q2 | fhe/ PoC + analysis |
| 6 | Reproducibility / setup expansion (hyperparameters, archs, K, τ, probe sizes) | general | src/ defaults |

## B — needs new work

| # | Item | Answers | Note |
|---|------|---------|------|
| 7 | Membership-inference study (the empty §6) | R1-W4, R2-Q5, AE-5 | AFK experiment |
| 8 | Formal security argument (server CT-view; released-model leakage) | R2-Q6 | writing only |
| 9 | Malicious-clients future-work paragraph | R2-Q4, AE-4 | writing only |

## C — deliberately out of the paper

Failure envelope (CNN-5/CIFAR-10, GPT-2, high-heterogeneity fighting updates) → `notes-open-items.md`.
