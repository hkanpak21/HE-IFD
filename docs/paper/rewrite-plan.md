# Rewrite plan — HE-OFT, encrypted-serving version

Checkpoint before this pass: `5499e25`. Branch `threat-model-encrypted-inference`.

Decisions locked with the user:

- **Threat model: the model is never revealed.** The aggregate stays encrypted and
  answers queries. Release is discussed in **one brief paragraph** using the
  results we already have, as a reference point, not as a second setting.
- **Blind selection is a full contribution**, with its own method subsection, its
  own algorithm, its own figure, and its own experiment subsection.
- **Three system figures**, drawn in draw.io, 7–8pt Times to match IEEEtran.
- **TÜBİTAK project numbers 124E091 and 124N941 stay in the acknowledgment.**

---

## 1. Voice rules (apply everywhere, including captions and figure labels)

- Write like a mathematician explaining something plainly. Formal, but no ornament.
- **No script or variable names in prose.** Not `agg_count_head`, not `B_personal`.
  Write "the count-weighted head merge" and "the personal-adapter setting".
- **No em dashes.** Use a comma, a semicolon, or a full stop.
- **No rare words.** If a shorter common word exists, use it. Ban list, carried over
  from the earlier pass: *leverage, utilize, paradigm, novel (as filler), seminal,
  elucidate, underscore, delve, myriad, robustly (as filler), pivotal*.
- Say the number, then say what it means. Do not stack adjectives before a result.
- One claim per paragraph. The first sentence of a paragraph states the claim.
- Never write "adds no noise" or "learns nothing at all". Both are false as stated.
- **Use the cryptographic terms, not paraphrases.** Write *plaintext* and
  *ciphertext*, never "in the clear" or "unencrypted". Write *collective public
  key*, *threshold decryption*, *key switching*, *evaluation keys*, *multiplicative
  depth*. The audience is a security venue and expects the vocabulary.

## 2. Flow

The arc is: build a motivation, prove the motivation is real, state what we build,
show each thing works.

### Section 1 — Introduction

Ends with a promise that Section 2 must pay off.

1. Organizations adapt public pretrained models to private data. Several holding
   related data would each get a better model from the combination.
2. They cannot pool the data. Law and competition both forbid it.
3. Federated learning is the standard answer, and its privacy problem sits at
   training time, not at the end.
4. Two levers remove that surface together: do it in one round, and encrypt the
   one thing that is exchanged.
5. One surface remains, and it is the model itself. In some deployments the
   fine-tuned model is a regulated or proprietary asset, and handing it to every
   participant is not allowed.
6. **So we never decrypt it.** The aggregate stays in ciphertext and answers
   queries. A participant gets labels, never weights.
7. That forces a design: the client must run the backbone in plaintext to form a
   query, so the trained adapter cannot live inside the encrypted object. Each
   client keeps its own adapter and only the head is shared.
8. Contributions.

*Transition out:* "Each of these claims rests on a premise about where federated
learning actually leaks. Section 2 establishes it."

### Section 2 — Background and related work

Ends by **validating the motivation from Section 1**, explicitly.

- 2.1 What federated learning leaks, and when. Training-time artifacts versus the
  finished model. This is the premise of the whole design.
- 2.2 Protecting training with cryptography. Secure aggregation, encrypted
  training, encrypted aggregation.
- 2.3 One-shot federated learning, and the cost of protecting it with noise.
- 2.4 Federated fine-tuning and task arithmetic. Where the frozen down-projection
  comes from.
- 2.5 **Secure inference (new subsection).** Needed because serving an encrypted
  model is exactly the problem this literature solves, and we compose with it
  rather than re-solving it.
- Closing paragraph, *Positioning*: state plainly that no existing method is at
  once one-shot, federated, encrypted, and never released, and that the
  training-time evidence in 2.1 is what makes that combination worth having.
  This is the payoff of the promise made in Section 1.

### Section 3 — Method

Every contribution follows the same four-part shape, in this order:

1. **What it is.** One paragraph, plain.
2. **Why it is forced.** What breaks under the alternative.
3. **How it works.** Equations, then an algorithm block.
4. **What it costs.** Depth, ciphertext count, and what each party learns.

Subsections:

- 3.1 Setting, and the constraints that force the design (C1–C6, kept, updated).
- 3.2 Notation.
- 3.3 Multiparty CKKS: chosen for its key structure, not its depth.
- 3.4 **Contribution 1 — the split.** Personal adapter kept local, head federated
  and encrypted. Figure 1. Algorithm 1.
- 3.5 **Contribution 2 — serving without decrypting.** Query path, encrypted
  argmax, label-only output. Figure 2. Algorithm 2.
- 3.6 **Contribution 3 — choosing without seeing.** The global-prior estimator.
  Figure 3. Algorithm 3.
- 3.7 Threat model. What each party holds, what the coalition of N−1 learns.
- 3.8 Security statement and proof sketch.

### Section 4 — Experiments

Every subsection opens with **the claim in one sentence**, then the experiment
that tests it, then the result. A reader must be able to point at a claim and at
the table that settles it.

- 4.1 Setup.
- 4.2 **Claim: a federated head over private representations is usable.**
- 4.3 **Claim: the federation can choose without decrypting.**
- 4.4 **Claim: the encrypted layer is cheap.**
- 4.5 **Claim: what a participant can learn is bounded.**
- 4.6 One paragraph: what releasing the model would have bought, with the
  numbers already measured.
- 4.7 Scope and limitations.

### Section 5 — Conclusion

Short. The PIs will rewrite it.

---

## 3. Figure and table standard

**Font rule.** IEEEtran journal sets 10pt Times. Therefore:

| element | size | face |
|---|---|---|
| figure node text | **8pt** | Times |
| figure secondary text, annotations | **7pt** | Times |
| figure caption | 8pt (IEEE default) | Times |
| table body | `\footnotesize` | Times |
| table caption | 8pt (IEEE default) | Times |

No sans-serif anywhere. No color as the only carrier of meaning: encrypted objects
get both a fill and an explicit label.

**Palette** (already in `main.tex`, reuse it so figures match existing plots):

| meaning | color |
|---|---|
| plaintext, client-side | `sanzotanlt` #D4C5A9 |
| encrypted object | `blueC` #7B9BBF, white text |
| never decrypted | `blueD` #5B7FA6, white text |
| server / untrusted | `paperneutrallt` #C7D0D6 |
| output to user | `blueA` #D3DEEA |

**When a figure, when a table.**

| use a figure when | use a table when |
|---|---|
| showing who holds what, and what moves | comparing numbers across conditions |
| showing an order of operations | reporting accuracy, cost, or leakage |
| showing what is encrypted and what is not | comparing against prior work |
| a claim is about structure | a claim is about magnitude |

Rule of thumb: if the caption would contain a number, it is a table.

**Planned figures**

| # | name | shows | section |
|---|---|---|---|
| 1 | training | local fine-tune, what is encrypted, the head merge | 3.4 |
| 2 | serving | query path, encrypted head, argmax, label out | 3.5 |
| 3 | selection | how the choice is made without decrypting | 3.6 |

Existing plots kept: communication comparison, accuracy increment. Both are
already in the paper palette.

**Planned tables**

| # | reports | claim it settles |
|---|---|---|
| 1 | evaluation axes | setup |
| 2 | accuracy per task, both settings, with the price of confidentiality | 4.2 |
| 3 | trainable unit ablation | 4.2 |
| 4 | sensitivity: skew, client count, trajectory | 4.2 |
| 5 | selection: estimator against the naive vote, and the cost of each error | 4.3 |
| 6 | cryptographic cost per operation | 4.4 |
| 7 | comparison against encrypted federated schemes | 4.4 |
| 8 | membership inference | 4.5 |
| 9 | matched partitions of prior one-shot methods | 4.2 |

---

## 4. Experiments that do not exist yet

Ordered by how badly the paper needs them.

| # | experiment | why it is needed | cost |
|---|---|---|---|
| E1 | Cryptographic cost of the new protocol: ciphertext-by-ciphertext head application, encrypted argmax per query, encrypted reciprocal for the head merge, key switch to the querier | Section 4.4 has no numbers at all for the current design. `tab:cost` measures the old one. | one Lattigo job, hours |
| E2 | Cost of blind selection: encrypted scoring over the holdout, batched | Contribution 3 must state its price | folds into E1 |
| E3 | Sensitivity under the new design: skew, client count, trajectory length | `tab:sens` used the aggregated adapter | one VALAR campaign, ~6h |
| E4 | Matched partitions of prior one-shot methods under the new design | `tab:matched` used the aggregated adapter | one campaign, ~4h |
| E5 | Membership inference against the serving oracle, label only | The released model no longer exists, so the current MIA section has no subject | one campaign, ~6h |
| E6 | Robustness with leave-one-out candidates on the head only | `tab:poison` used the aggregated adapter, and selection is now encrypted | one campaign, ~4h |
| E7 | GPU timings for the encrypted argmax | requested; FIDESlib and a built OpenFHE are already on VALAR | uncertain, build risk |

E1 and E2 are blocking: the paper cannot claim a cost it has not measured.
E3 through E6 are re-runs of tables that already exist in the old design.
E7 is an improvement, not a gap.

---

## 5. Order of work

1. Figures 1–3 in draw.io, checked at final print size.
2. Section 3 rewritten around the three contributions.
3. Section 2, with the secure-inference subsection and the closing validation.
4. Section 1, rewritten to set up exactly what Sections 2 and 3 deliver.
5. Section 4 restructured claim by claim, with gaps marked where E1–E6 will land.
6. Abstract and conclusion last.
