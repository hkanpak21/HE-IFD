# row_leakage

What a shared head's row carries about the client that decided it. The merge is
coverage weighted, so a class held by one client has a row equal to that client's
displacement with no dilution over the federation, and for a linear layer with a
bias the ratio of the row displacement to the bias displacement is a weighted
mean of that client's features (Phong et al., IEEE TIFS 2018, observation O1).
Job 1617194 on VALAR, 2026-08-30, three tasks and three seeds, 570 class rows.

**Result: negative. The row points into the feature manifold and identifies
neither a record nor a class.** Cosine to the best-matching example of the class
exceeds cosine to the best-matching example of a different class by 0.012 where
one client holds the class, and by 0.006 where six or more do. Both are small
beside the absolute figure of 0.16, and the coverage trend is almost flat.

| clients holding the class | rows | to class mean | to best same-class | to best other-class | margin | random |
|---|---|---|---|---|---|---|
| 1 | 16 | 0.128 | 0.160 | 0.148 | 0.012 | 0.029 |
| 2 | 82 | 0.127 | 0.160 | 0.152 | 0.008 | 0.029 |
| 3 to 5 | 408 | 0.119 | 0.156 | 0.148 | 0.008 | 0.029 |
| 6 or more | 64 | 0.115 | 0.159 | 0.153 | 0.006 | 0.029 |

The ratio does lie in the manifold: 0.16 against a random-direction baseline of
0.029. It carries a direction and not an identity.

**Why the mechanism does not deliver what the algebra promises.** The identity is
exact for one gradient step on one example. Our clients take 200 steps over their
whole local dataset, and every example contributes to the row-c gradient through
its own softmax residual, so the ratio is a weighted mean over the client's data
rather than any one record.

Produced by `jobs/row_leakage.py`, submitted with `jobs/row_leakage.sh`.
