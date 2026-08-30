---
title: "The submission, last pass before the PIs"
author: "For Halil, 2026-08-29"
---

# State

Ten pages. Forty-three keys. Nothing rewritten in either view. Both documents
compile with no undefined citation, no undefined reference and no overfull box.
All nine gates pass. The prose budget is 147 words under, so there is room if you
want any of the decisions below to cost words.

# One thing is blocking, and it is three claims that hang together

The submission makes three statements about the serving circuit. Each was
measured, and each was measured on a variant the protocol does not specify.

The abstract says a query takes $31.5$ to $113.2$ seconds for $13.5$ MiB. Those
two figures describe different designs. The traffic prices the design the method
specifies, where the server restores levels alone under collectively generated
keys. The latency was taken on the other design, where a collective refresh does
it. Job 1612017 has now timed the specified one and it runs $400.8$ to $1468.3$
seconds, about thirteen times slower.

Section V says the encrypted argmax is exact, and the cost paragraph repeats it.
That is true of the refresh variant, which reproduced the plaintext maximum
exactly. The specified variant agrees to $7.3\times10^{-5}$.

Neither benchmark computes an argmax index. Both compute the maximum logit. The
index step the method specifies costs a further comparison against each logit and
has never been implemented, so every latency we report is a lower bound for the
circuit the method describes.

The three move together. Whatever you decide about the first fixes the other two.
The choices, as I see them.

Report the specified design, at $400.8$ to $1468.3$ seconds and $13.5$ MiB.
Honest, consistent, and a thirteenfold worse headline.

Report the refresh design, at $31.5$ to $113.2$ seconds and roughly $1.6$ GiB per
query at a hundred classes. Fast, exact, heavy on traffic.

Change what the method specifies to the refresh variant. It is faster and it is
exact, its cost is per-query traffic, and it removes the $8.70$ GiB of
bootstrapping keys from the deployment entirely. This is a method change and not
a wording one, and I think it deserves more than a dismissal.

Label the current numbers and state both. Costs words, and we have them.

# Two you should look at, briefly

The introduction says we implement the protocol in real multiparty CKKS rather
than simulating it. The protocol is implemented. The serving benchmarks run on
synthetic feature vectors rather than a real trained head, and they compute the
maximum rather than the index. Both are true statements sitting next to each
other, and a reviewer who opens the repository will notice.

The priority claim changed wording today, from the final model is never disclosed
to any party, to no party receives the trained result. You asked for it and
`docs/CONTEXT.md` carries the new form with its date. The PIs approved the old
wording on 2026-08-19, so it is worth a sentence to them rather than letting them
find it. The same applies to the merge of C3 and C4, since they read the chain as
seven items and it is now six.

# Three things that look like defects and are not

The linter reports three errors on the submission and all three are false
positives. Two are "the very artifact it releases", where the word means that
exact one and is not an intensifier. One is the system name slytHErin, which the
linter reads as a code identifier. Leave all three.

The bibliography still carries `arXiv:XXXX.XXXXX`. Gate 9 counts it on purpose.
The report goes to arXiv first, its identifier replaces the placeholder, and only
then does the paper go out.

`fig_protocol` reports five of forty-five text spans outside the 8pt tolerance.
Those five are two subscripts and a star glyph, which render smaller by design.
They have read that way since August and your re-export did not change them.
