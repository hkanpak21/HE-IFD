# This case measures the pre-pivot protocol. Read this before using its numbers.

Written 2026-08-27. It lives in its own file because `README.md` in this
directory is overwritten by `mia.report.write_report` on every run.

## What these numbers are

Membership inference against a **released plaintext model** θ⋆ and against the
**Phase-0 prototype channel**, both produced by the distillation pipeline the
project retired on 2026-07-26. The three surfaces are the released model seen by
an external querier, the same model seen by a participating client, and the
prototype release itself.

## What they are not

They are not leakage of the current method. The current method releases no model
at any point and builds no prototype channel. No party holds θ⋆ in plaintext, and
the only adversary-facing object is a label-only query interface to an encrypted
head. Nothing in `mia/attacks.py` can run against that interface, because every
attack there consumes a per-example loss, confidence, or distance to a released
prototype.

## The one use that is still sound

As the **disclosure counterfactual**. The report compares never disclosing the
model against disclosing it, and today it makes that comparison on accuracy
alone. These numbers make it on the privacy axis, and they are the strongest form
of the argument, because they are what the alternative design would have leaked.
Used that way they must carry the label "the pre-pivot released-model pipeline".

The headline contrast, from `README.md` in this directory, ViT-B/32 on CIFAR-100,
external LiRA: AUC 0.8518 at alpha 0.05 and 0.8597 at alpha 1.0, with TPR at
0.1 per cent FPR of 0.1282 and 0.1645. The prototype channel at raw release
reaches AUC 1.0. Against those, the current method exposes no such object.

## What replaces it

`docs/notes/TR-propositions-2026-08-27.md`, proposition P4, specifies the
measurement for the current interface. `docs/notes/privacy-analysis-tr-2026-08-27.md`
gives the reasoning and the literature. Proposition 2 in
`docs/paper/sections/security.tex` is what makes the replacement cheap: the
coalition's whole view through the label interface is computable by an adversary
that holds the head, so a white-box attack on the true merged head is a ceiling on
what any budget reaches, and the extract-then-attack pipeline does not have to be
built to obtain a bound.
