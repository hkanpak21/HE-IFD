---
title: "What each outcome of the four privacy jobs means, decided before the numbers arrive"
author: "For Halil, 2026-08-30"
---

# The verdict this note exists to protect

Four jobs are running. The branches below are fixed now so that when the numbers
land nobody argues with a result. Every branch names what goes in the technical
report and what does not.

| job | what it measures | where it lands |
|---|---|---|
| 1617191 | membership against the AG-News head, three seeds | Section on what a coalition learns |
| 1617192 | the same on DBpedia | the same |
| 1617193 | the same on Banking77 | the same |
| 1617194 | what a shared head's row carries about its holder | the same |

Nothing in the submission depends on any of them.

# Job 1617194, the row test

This is the sharper of the two questions, because the merge is coverage weighted
and a class held by one client has a row equal to that client's displacement.

The smoke run on Banking77, seed 42, already reports: seventeen of seventy-seven
classes held by at most two clients, cosine 0.150 to the class mean, 0.188 to the
best-matching example of the class, 0.179 to the best-matching example of a
different class, against a random-direction baseline of 0.029.

**Branch A. `cos_top1` stays within about 0.02 of `cos_top1_other` across tasks
and seeds.** Then the row carries a direction in the feature manifold and
identifies neither a record nor a class. Report it as a measured negative result,
beside Oz et al.'s own Limitations section and the `C/n` counting argument. This
is the outcome the smoke run points at and it is good for the paper.

**Branch B. `cos_top1` exceeds `cos_top1_other` by more than about 0.05, and the
margin grows as `holders` falls.** Then coverage weighting leaks and the report
must say so. The mitigation is a minimum-coverage rule on a class row, whose
nearest published cost is up to 0.05 accuracy under non-IID data at a threshold
of twenty to thirty contributors, measured at the coordinate level rather than
the class level. State the leak, state the mitigation, do not claim we
implemented it.

**Branch C. `cos_mean` sits at the random baseline everywhere.** Then the ratio
identity does not survive our training recipe at all, which is possible because
the head is trained jointly with an adapter over two hundred steps rather than by
one gradient. Report that the mechanism does not instantiate, and say why.

# Jobs 1617191 to 1617193, the membership chain

Three surfaces per cell. The head in plaintext is the ceiling and, by the
data-processing inequality, an upper bound on the other two for a fixed attack.
The extracted copy is what the protocol admits. The gap attack is free.

The smoke run at eight shadows on AG-News gave 2.2 per cent true positives at
one per cent false positives for the true head, and the same for a copy extracted
from two hundred thousand queries. Eight shadows is too few to trust and the real
runs use sixty-four.

**Branch A. The extracted copy tracks the true head to within a factor of about
two at 0.1 per cent false positives.** Then extraction is not the bottleneck and
the query allowance buys little on this channel. Report the ceiling as the number
that matters, and say the allowance prices the cost of reaching it rather than
bounding what is reachable. This is what the smoke run suggests.

**Branch B. The copy is an order of magnitude weaker than the true head.** Then
the allowance is doing real work and Proposition 2's cap is loose. Report both
curves and the gap between them, which is the quantity no published paper gives.

**Branch C. The true head itself is at chance.** Then delta_wb is small and the
proposition's cap is close to vacuous in the useful direction. Report it plainly.
A linear head on a frozen backbone is not a hard target in the literature, so
this outcome would be worth checking against Tobaben et al.'s law before it is
believed.

**In every branch, report the gap baseline.** The smoke run put it below chance,
at AUC 0.19, which means predicting membership from correct classification is
anti-correlated here. If that survives, say so: it is a fact about a
coverage-weighted merge and it is not what the literature leads one to expect.

# What is not measured, and must be said

`n_candidates` caps the resolvable true-positive rate. With a thousand members
the smallest non-zero rate is one in a thousand, so a reported 0.001 at 0.1 per
cent false positives is one example and not a rate. Say the candidate count
beside every figure.

The shadow federations randomise membership over each client's training and
held-out examples. They do not re-partition the federation, so they hold the
coverage pattern fixed. That is the right conditioning for this question and it
means the numbers say nothing about how leakage moves with the partition.

# What happens next, in order

1. Pull both CSVs, write the numbers into `results/*/README.md`.
2. Take the branch above and write the corresponding paragraphs into the report's
   security section, report only.
3. Then OSLO, which is the attack our serving interface is most exposed to,
   because the client submits an arbitrary feature vector by design.
