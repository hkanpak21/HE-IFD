# Security program and journal plan

Opened 2026-07-29 after the PI meeting. This file holds the work the meeting
set. `docs/plan/paper-rewrite.md` still holds the paper flow and the outstanding
measurements.

## 0. Where the paper stands

The paper is 17 pages and compiles clean. Section 4.7 gives a threat model and
one proposition. The proposition covers an honest-but-curious server that
colludes with up to `N-1` clients. It reduces the server view to IND-CPA of
multiparty CKKS. The meeting judged this too thin for a journal.

## 1. Journal target and the rules that apply

The meeting chose journals over conferences. Three candidates. The rules differ,
and the difference matters because TDSC rejected this work.

| Journal | Society | What the TDSC rejection costs us |
|---|---|---|
| IEEE TNSE | ComSoc | Nothing. The one-resubmission rule covers TNSE's own rejections only. |
| IEEE TIFS | Signal Processing | We must disclose the rejection and quote every prior review verbatim. |
| IEEE TDSC | Computer Society | No public policy. We must ask the editorial office. |

Sources: the ComSoc TNSE information page, the SPS information for authors, and
the IEEE Computer Society author resources page. All three read on 2026-07-29.

**Three consequences.**

1. TNSE stays the cleanest path. A TDSC rejection does not block it.
2. TIFS costs more work. The SPS policy allows one resubmission of a manuscript
   rejected by any journal. It also requires a supporting document with verbatim
   quotations of all previous review reports and our response to each. We must
   find the TDSC reviews before we choose TIFS.
3. TIFS states a 13-page limit and treats a resubmission as a new submission.
   The paper is 17 pages. Confirm whether overlength charges apply before we
   plan a cut.

**Open item.** Ask the TDSC editorial office whether a rejected manuscript may
return. The public pages do not say.

## 2. Semi-honest proof, all parties

The first task, and the easiest. Reduce the whole protocol to the IND-CPA
security of multiparty CKKS under a semi-honest adversary that may corrupt the
server, the serving party, and up to `N-1` clients.

What the current proposition already gives:
- A simulator that outputs encryptions of zero.
- A hybrid over the client ciphertexts.
- The claim that decryption needs a share from every client.

What it does not give:
- A definition. The paper never states the security experiment.
- Coverage of the serving path. The proposition covers aggregation only.
- Coverage of the selection step, which decrypts one value.
- A statement of what the protocol reveals on purpose.

The last point decides the shape of the proof. A simulator must reproduce the
view, and the view contains the answers the served model returns. The simulator
therefore needs those answers as input. This makes the leakage explicit, which
is the correct outcome.

## 3. Ideal functionality

The meeting asked what the bound of privacy is in this setting. Write an ideal
functionality `F` and prove the protocol realizes it.

Draft shape:

    F holds the private datasets.
    F computes the shared head. F gives it to nobody.
    On a query (j, x) from client j, F returns the predicted label to client j.
    F counts the queries of each client and stops at the allowance Q.

Two claims follow, and the second is the interesting one.

1. The protocol realizes `F` against a semi-honest adversary corrupting the
   server and up to `N-1` clients.
2. **Model extraction is a property of `F`, not of our protocol.** A client that
   spends its allowance against `F` recovers the head, because `F` answers
   queries and answers carry information. Section 5.6 measures the rate at
   three to five queries per parameter. Any protocol that realizes `F` inherits
   this. The bound is therefore a property of the task, not a weakness of the
   construction.

Claim 2 is what the meeting asked for. It states the limit of what any protocol
in this setting can achieve.

## 4. Malicious adversary

The PI proposed a game. The adversary corrupts the server and `N-2` clients. Two
clients stay honest. The adversary picks two data distributions. The challenger
assigns them to the two honest clients at random. The adversary guesses the
assignment. We bound its advantage over one half.

**Decisions taken 2026-07-29.**

- The result claims **input privacy only**. A malicious adversary learns nothing
  about honest client data. Correctness stays out of scope, and the paper says
  so. A malicious client can still bias the shared head.
- We prove the **content game**, not the assignment game. The challenger gives
  one honest client either `D_0` or `D_1`. The adversary guesses which.
- The game **constrains the two datasets to equal size**. The per-client sample
  counts stay public, and we state the restriction openly.

**Three problems the decisions answer.**

1. The game measures privacy, not malicious security. A malicious client can
   still bias the shared head. The paper must not call the result malicious
   security without saying which part it covers.
2. The per-client sample counts are public. If the two distributions differ in
   size, the adversary reads the counts and wins. The game needs equal sizes, or
   the protocol must hide the counts.
3. The merge sums over clients. Swapping which honest client holds which dataset
   leaves the sum unchanged. The served model is therefore identical under the
   swap, and the query channel gives the adversary nothing. The advantage
   collapses to distinguishing two individual ciphertexts, which IND-CPA already
   covers. The game may be too easy to be worth a theorem.

A harder game asks about content instead of assignment. The challenger gives one
honest client either `D_0` or `D_1`. The adversary guesses which. Symmetry does
not protect this, so the advantage comes from the query channel, and our
extraction numbers bound it.

## 5. Scope beyond classification

The paper says classifier head everywhere. The construction needs less than
that. It needs a trained linear map that sits after the last nonlinearity, and a
client able to compute the features itself.

An autoregressive language model has such a map. The vocabulary projection is
linear and sits after the final layer norm. The client generates the tokens, so
it can compute the features for the next step.

Three caveats, and the second is serious.

1. Each generated token costs one query. The allowance of Section 5.6 buys far
   fewer sentences than it buys classifications.
2. Sampling needs the distribution over the vocabulary. Returning that
   distribution restores the linear solve and destroys the argument of
   Section 4.6. Greedy decoding returns one token and keeps it. The method
   therefore covers deterministic decoding, unless we sample under encryption.
3. Extraction cost grows with the size of the shared map. A vocabulary
   projection is far larger than a classifier head, so extraction gets harder,
   not easier.

Write this as scope, not as a result. We have not run it.

## 6. Experiments for the generation claim

Decided 2026-07-29. All four parts, in this order.

1. **Structure.** State that the construction needs a trained linear map after
   the last nonlinearity. Name the vocabulary projection as such a map. State
   the greedy-decoding caveat.
2. **Extraction at vocabulary scale.** Confirm the three-to-five queries per
   parameter law holds as the label space grows, then read off the cost for a
   vocabulary projection. Reuse `jobs/extraction_budget.py` on a synthetic head.
   No training.
3. **Communication per generated token.** Each token costs one query. Multiply
   the measured per-query traffic by the token count. Report the cost of one
   sentence, not one token, because the token figure hides the total.
4. **Perplexity against a baseline.** Federate an adapter and a language-model
   head on a small model. Compare against a client that trains alone, and
   against the pooled model. This is a new pipeline and the largest cost.

Parts 2 and 3 need no GPU and no training. Start there.

## 7. Outstanding measurements, carried over

- Pooled ceiling. The job timed out. Resubmit with a shorter budget.
- N=50 sensitivity cell. Running.
- N=20 sensitivity cell and the matched partitions. Landed, not yet collected.
