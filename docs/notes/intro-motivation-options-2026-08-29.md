---
title: "The motivation paragraph: three sentences, three decisions"
author: "For Halil, 2026-08-29"
---

# What the search found

A better source exists and it is recent. It also turned up a second problem in the
same paragraph that we had not looked at.

The paragraph is `docs/paper/sections/intro.tex` lines 14 to 22. It makes three
claims and each needs a separate decision. Every proposed sentence below is a
rewrite, so `check_subseq.py` flags all of them and none is mine to apply.

# Sentence 1, line 15. The separation itself

Current: "its privacy risk is concentrated at training
time~\cite{nasr2019comprehensive,melis2019exploiting}".

The claim is fine. The citations can be improved and reduced, which is what the
PI asked for on 2026-08-21.

Bai, Hu, Ye, Li, Wang and Xu, *Membership Inference Attacks and Defenses in
Federated Learning: A Survey*, ACM Computing Surveys 57(4), Article 89, 2025, DOI
10.1145/3704633, states the separation as a table row. Centralised learning is
attacked at the inference phase and the adversary knows the target model.
Federated learning is attacked at the training phase and the adversary knows the
target model and its historical versions.

**Proposal.** Replace the two citations with this one. Two keys become one, and
the survey is the authority the sentence needs. Nothing else changes.

# Sentence 2, line 17 to 18. Gradient reconstruction

Current: "A gradient permits reconstruction of the batch that produced
it~\cite{zhu2019deep}."

**This is a correctness problem and it is new.** Du, Hu, Wang, Sun, Gong, Ren and
Chen, *SoK: On Gradient Leakage in Federated Learning*, USENIX Security 2025,
contradicts the sentence as written. From their abstract, gradient inversion is
"notably constrained, fragile, and easily defensible", and "even simple
post-processing techniques applied to gradients can serve as effective defenses".
Their Theorem 4.3 proves a dimension bound. When the parameter count is smaller
than the batch size times the input dimension, distinct inputs produce identical
gradients, so reconstruction is not merely hard but impossible.

Our sentence states the reconstruction unconditionally and against a semi-honest
adversary. A 2025 SoK at a top venue says that is wrong in that setting.

Two ways out.

Name the actor, which is the honest fix and also the stronger claim. A server
that modifies the model it distributes reconstructs the batch, and does so even
through secure aggregation across a hundred clients. That is LOKI, Zhao et al.,
IEEE S&P 2024, which reports leaking 76 to 86 per cent of samples in a single
round where prior work leaks under one per cent. The cost is that this adversary
deviates from the protocol, and our Section IV assumes a semi-honest server, so
the sentence would motivate the design with an adversary we do not defend
against. If we take this route the sentence must say the server deviates.

Or delete the sentence and let the membership number carry the paragraph.

**Recommendation.** Delete it. It is one sentence, the paragraph does not need it,
deletion is permitted by the subsequence rule, and it removes a claim a reviewer
can refute with a 2025 SoK. Sentence 3 does the work.

**One clause worth having somewhere, later.** The same SoK finds that
late-training models resist inversion while early ones do not. The single artifact
we expose is a fully locally trained displacement, which is the late kind. That is
an argument in our favour and it belongs in the report, hedged, because it is an
inference from their setting to ours.

# Sentence 3, lines 19 to 21. The numbers

Current: "An observer of the per-round updates mounts membership inference at
$87\%$ accuracy on one model and dataset, where the same attack against the final
model alone falls to $54.5\%$."

Both numbers are wrong for what the sentence says, as established. Note that no
pure number substitution repairs it, because the phrase "the same attack" is the
false part, so every option here is a rewrite.

## Option A, stay with Nasr and use its tables

"An observer of the per-round updates mounts membership inference at $79\%$
accuracy on one model and dataset, where a black-box attack against a fully
trained model reaches $68\%$."

Both figures come from tables of the cited paper rather than its introduction.
$79.2$ per cent is the passive global attacker, Table X, which is what the word
observer means. $67.7$ per cent is Table VIII, the stand-alone black-box cell,
which is the number their own tables give for the comparison their introduction
puts at $54.5$.

Honest, and the smallest change. The contrast falls from thirty-three points to
eleven, which is a weak motivation for a paper whose whole design follows from it.

## Option B, use the recent work, which is what the search was for

Zhu, Li, Gu, Yao, Fan and Han, *FedMIA*, CVPR 2025, pages 20643 to 20653, DOI
10.1109/CVPR52734.2025.01922. Its Table 1 carries both halves of our contrast in
one run, one metric, one target.

"An adversary that aggregates a client's per-round updates mounts membership
inference at a true positive rate of $25.3\%$ at a false positive rate of
$0.1\%$, where the same statistic read from a single model snapshot reaches
$0.18\%$."

AlexNet on CIFAR-100, ten clients, three hundred rounds. The ResNet-18 row is
$16.82\%$ against $0.36\%$ if you prefer the more familiar architecture.

Three reasons this is better. Both numbers come from the same table, the same run
and the same statistic, so the comparison is genuinely like for like, which is
exactly what Nasr cannot give us. The metric is true positive rate at a low false
positive rate, which is what the field has used since Carlini et al. 2022 and
which a reviewer now expects. And the contrast is two orders of magnitude rather
than eleven points.

One qualification, and it changes the wording rather than the argument. The
single-round figure is a model snapshot taken during training, not a separately
released final model. So the defensible sentence is that the round sequence leaks
far more than any one snapshot of the same run. It is not a statement about a
released final model. The proposed wording above already says snapshot.

A second qualification in our favour. That $0.18\%$ is the best of thirty
observed snapshots, not an average one, so the gap is a conservative lower bound.

**Recommendation.** Option B. You asked for a more recent work and this is a
better one on every axis that matters.

# What no citation supports, and what we should therefore not write

The conclusion that exchanging a single contribution once removes most of the
attack surface is ours. Nothing measures the residual risk of a one-shot exchange
against a multi-round one on the same task. The surveys assert the principle and
hedge it, and the IJCAI 2025 one-shot survey writes "potentially achieves even
stronger security".

So state the antecedent, which is well supported, and derive the design choice
from it. Do not attribute the conclusion to a citation. Our protocol also
encrypts the single contribution, so the one-shot property is not what protects
confidentiality against the server. It bounds the size of the surface. Keeping
those two arguments apart is what will survive a reviewer from the TDSC pool.

# Summary of the three decisions

Sentence 1: swap two citations for the ACM survey. Reduces the count by one.

Sentence 2: delete it, or name a deviating server and cite LOKI.

Sentence 3: Option A or Option B. I recommend B.
