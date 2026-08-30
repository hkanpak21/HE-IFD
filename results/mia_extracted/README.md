# mia_extracted

How much membership signal survives extraction of the served head. Measures the
cap that Proposition 2 introduces and that nobody had measured. Jobs 1617191 to
1617193 on VALAR, 2026-08-30, three tasks and three seeds, LiRA with 64 shadow
federations and 2000 candidates per cell.

**Result: at chance, on every task, both arrangements, every surface.** The head
handed over in plaintext gives AUC 0.49 to 0.53 and a true-positive rate of 1.3
to 2.3 per cent at a 1 per cent false-positive rate, which is the false-positive
rate itself. A copy extracted from 200,000 label-only queries gives the same.
With 1000 members the smallest resolvable rate is 0.001, so every figure at 0.1
per cent is two to four examples and not a rate.

| task | C | arrangement | surface | TPR@0.1% | TPR@1% | AUC |
|---|---|---|---|---|---|---|
| AG-News | 4 | A | head in plaintext | 0.0023 | 0.0127 | 0.515 |
| AG-News | 4 | A | extracted, 2e5 queries | 0.0020 | 0.0133 | 0.501 |
| DBpedia | 14 | A | head in plaintext | 0.0010 | 0.0080 | 0.502 |
| DBpedia | 14 | A | extracted, 2e5 queries | 0.0020 | 0.0093 | 0.498 |
| Banking77 | 77 | A | head in plaintext | 0.0030 | 0.0227 | 0.528 |
| Banking77 | 77 | A | extracted, 2e5 queries | 0.0020 | 0.0173 | 0.493 |

Arrangement B is within 0.01 AUC of A throughout.

**The gap baseline is confounded and must not be read as a membership result.**
`split_parts` reserves at least one example of every class a client holds for its
holdout, so non-members are enriched in rare classes by construction. The gap
attack keys on whether the head classifies an example correctly, so on Banking77
arrangement A it reports AUC 0.72 while measuring that enrichment rather than
membership. LiRA is unaffected because it calibrates each example against its own
shadow distributions.

**What this does not say.** The shadow federations randomise membership over each
client's pool but hold the coverage pattern fixed, so nothing here says how
leakage moves with the partition. The head trains for 200 steps, which is short,
and the literature's law for a linear head on a frozen backbone predicts leakage
falling as the inverse square root of the examples per class; ours has thousands.

Produced by `jobs/mia_extracted_head.py`, submitted with `jobs/mia_extracted_head.sh`.
The three parallel jobs each overwrite `results.csv`, so the committed file is
merged from the CSV blocks in `runs/mia_16171*.out`, which are authoritative.
