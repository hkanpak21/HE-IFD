# Editor's checks, round 2, 2026-09-09

Written before the seats reported, so nothing here is anchored on them. Two
parts: a new defect the revision introduced, and the mechanical status of the
twelve blocking items round 1 raised.

## A new defect, verified

**The submission asserts a library limitation that does not exist.**

Section II-A now reads:

> Our implementation instantiates t=N, which is the setting the multiparty CKKS
> library provides, and the measurements of Section V-E are taken there.

Lattigo v6.1.0 provides general t-out-of-N. `fhe/go.mod:5` pins
`github.com/tuneinsight/lattigo/v6 v6.1.0`, and that module ships
`multiparty/threshold.go`, which exports `NewThresholdizer` (line 61) and
`NewCombiner` (line 117) along with `ShamirPolynomial` and `ShamirSecretShare`.
The library's own tests exercise it at thresholds N/4, N/2 and N-1.

Our `fhe/*.go` never calls any of them, so t=N is a choice this implementation
made and not a constraint the library imposed. A referee who knows Lattigo will
check this, and the claim as printed is false. The fix is one clause: say the
implementation instantiates t=N and that the measurements are taken there, and
drop the attribution to the library.

Epistemic status: verified against the pinned module source and against our own
code. Not an inference.

## Round 1 blockers, mechanical status

Checked by string occurrence in the extracted text of both documents, then read
in context. This is the editor's own check and does not bind the seats, who were
not told about round 1.

| # | Round 1 blocker | Status | Evidence |
|---|---|---|---|
| B5 | Table I cannot produce the stated `A_dis - A_sel` range | **CLOSED** | Section V-G now reads "The estimator selects per seed, so A_sel is 0.669 on AG-News and 0.756 on CIFAR-100 rather than the bolded entry of table I." |
| B7 | Section IV-D presented the provenance check as implemented | **CLOSED** | "We implement neither, and Section V-H records it as a limitation." |
| B6 | The level-restoration mechanism was never named | **LIKELY CLOSED** | `bootstrapping` now appears three times and `collective refresh` twice in the submission. The seats should confirm each quoted figure is attributed. |
| B11 | Availability at t=N | **PARTLY CLOSED** | The submission now states both that any t clients form a quorum and that the implementation instantiates t=N. It still does not state the consequence, that at t=N one absent client blocks every query. And the sentence that closes the gap introduces the false library claim above. |
| B9 | Seed and federation-size disclosures dropped in the cut | **OPEN** | `effective federation` 0 in the submission and 1 in the report. `fewer than` 0 and 1. `one seed` 0 and 3. The coverage measurement was added, which is new evidence, but the disclosures round 1 named are still report-only. |
| B1 | Theorem 1's hypothesis, smudging, and the key recovery | **OPEN** | `smudging` 0 in the submission and 9 in the report. `Micciancio` 0 and 3. `Checri` 0 and 1. |
| B2 | The duplicate-query check absent from the specification | **OPEN** | `duplicate` 0 in the submission, 1 in the report. |
| B3 | No commitment round on key generation | **OPEN** | `commit` 0 in the submission, 2 in the report. |
| B4 | The abstract's GPU latency unsupported in the body | **OPEN** | `48.9` occurs once in the submission, on page 1. The wording improved to "once level restoration runs on a GPU", which names what was projected, but no body text supports it. |
| B8 | No numeric query allowance | **OPEN** | Neither 1.3e3 nor 2.2e4 appears in the submission. Both are in the report. |
| B10 | No bit-security level | **OPEN, in both documents** | Neither document states a claimed bit security, a total modulus, or a secret distribution. The justification exists only as a code comment at `fhe/serve.go:106`, QP approx 762 bits at ring degree 2^15. |
| B12 | The serving constant fixed from the exported plaintext head | **OPEN** | `exported head` 0 in the submission, 1 in the report. |

**Four of twelve moved. Seven are open and one is partly closed.** The four that
closed are the ones whose fix was a sentence moved from the report. The seven
still open are, with one exception, the ones that require the authors to print
something they would rather leave in the companion.

## Build state, for the record

The submission is at **eleven pages** against a ten-page target, which is one
IEEE overlength charge. `scripts/gates.sh` reports gate 3 at 78 rewritten
paragraphs in the submission and 139 in the report, because the Method was
restructured and `.subseq-allow` has not been updated for it. Both are decisions
for Halil, not review findings, and they are recorded here so they are not lost.
