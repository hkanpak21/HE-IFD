# Scope beyond classification

Working notes, 2026-07-29. Not paper text yet. The meeting asked how far the
construction reaches past classification, and what a generation claim would
cost.

## What the construction actually needs

The paper says classifier head in every section. The construction needs less.
It needs two things.

1. A trained linear map that sits after the last nonlinearity of the backbone.
2. A client that can compute the features that enter that map, by itself, in
   plaintext.

Requirement 2 is the one that forced the design (constraint C7). A shared map
inside the backbone would make the features depend on it, and the client would
have to evaluate every nonlinearity under encryption.

Nothing in either requirement mentions classification.

## An autoregressive model has such a map

The vocabulary projection of a decoder is linear and sits after the final layer
norm. The client generates the tokens, so it holds the prefix and can compute
the features for the next step with the public backbone and its own adapter.

The structure therefore carries over without change. Three caveats follow, and
the second one restricts the method rather than costing it.

### 1. Each token costs one query

Classification asks once per input. Generation asks once per token. Every cost
in Section 5.4 multiplies by the length of the answer.

### 2. Sampling, and why it does not have to break the argument

Section 4.6 returns the index of the largest logit because returning the scores
lets a client solve for the map in `d+1` queries. Sampling from a
temperature-scaled distribution appears to need those scores. The method as
built therefore covers **greedy decoding**, and the paper states that.

There are two ways to add sampling. They differ in what they cost.

**Route A, return the distribution.** The serving party returns the softmax
vector and the client samples locally. This is simple and it forfeits three
things at once.

1. Extraction returns to a linear solve. The map falls in `d+1` queries, which
   is 769 here, instead of the order of `C*d` that Section 5.6 measures.
2. The query allowance stops being a usable control. It would have to sit below
   769 queries in total, which is not a deployment.
3. The measured bound of Section 5.6 no longer applies at all, because it is a
   bound on label-only extraction.

**Route B, sample under encryption by the Gumbel-max trick.** Adding independent
Gumbel noise to the logits and taking the argmax draws exactly from the softmax
distribution. The serving party already computes an encrypted argmax. Adding an
encrypted noise vector before it costs one ciphertext addition, measured at
about 1 ms. The interface still returns one index, so **the security argument of
Section 4.6 carries over unchanged**.

Route B has one condition, and it decides whether the route is sound. The noise
must be unknown to the querying client. If the client supplies its own encrypted
noise, it knows `g` and receives `argmax(logits + g)`. Choosing `g` lets it
isolate pairwise comparisons and binary-search the logit gaps, which is a
stronger attack than plain label access. The noise must therefore be generated
collectively, in the same way the keys are, so that no single party knows it.
That is a distributed randomness protocol per token, and we have not built or
costed it.

**Summary for the paper.** Greedy decoding is what we have. Temperature sampling
is available without giving up the label-only interface, through Gumbel-max with
collectively generated noise. State Route B as a design that follows from the
construction, and state clearly that we did not implement or measure it.

### 3. The map is much larger, which cuts both ways

A vocabulary projection has far more parameters than a classifier head. This
raises the cost of every operation. It also raises the cost of extraction by the
same factor, as Section 5.6 measures.

## What it costs, from measured numbers

Per token, at `N=10` and ring degree `2^14`, using the per-query figures of
Section 5.4:

| item | size |
|---|---|
| uploaded encrypted features | 2.0 MiB |
| returned encrypted token | 0.5 MiB |
| key-switching shares, ten of them | 2.5 MiB |
| **total per token** | **5.0 MiB** |

Traffic for one answer:

| tokens | traffic |
|---|---|
| 1 | 5 MiB |
| 20 | 100 MiB |
| 100 | 500 MiB |
| 1000 | 4.9 GiB |

**The traffic is the binding constraint, not the computation.** The encrypted
argmax needs `ceil(log2 C)` sequential comparison rounds. That is 7 rounds at a
hundred classes and 16 rounds at a vocabulary of 50 257. Compute grows by a
factor of about two. Traffic grows by the number of tokens, without limit.

A hundred-token answer costs half a gigabyte. That number decides whether this
setting is worth writing up as a deployment or only as a structural result.

## Extraction gets much harder

A GPT-2 vocabulary projection at `d = 768` holds 38 597 376 parameters. Section
5.6 measures extraction at three to five queries per parameter for fidelity
0.90. If that law holds at this size, a copy costs:

| rate | tokens | traffic |
|---|---|---|
| 3 queries per parameter | 116 million | 552 TiB |
| 5 queries per parameter | 193 million | 920 TiB |

Both are out of reach for any client under a query allowance. The security
argument of Section 5.6 therefore gets stronger in the generation setting, for
exactly the same reason the serving cost gets worse. The shared map is bigger.

**The law needs a check before we print these.** `jobs/extraction_scale.py`
tests whether cost really tracks the parameter count as the label space grows.
It spends a budget of `m * C * d` queries and varies `m`. If fidelity depends on
`m` alone, the curves for different `C` fall on top of each other and the
arithmetic above holds. Job 1416275.

## Experiments the meeting asked for

1. **Structure.** Written above. No cost.
2. **Extraction at vocabulary scale.** Running. No training, no GPU.
3. **Communication per token.** Done, above. Arithmetic on measured figures.
4. **Perplexity against a baseline.** Not started. This needs a new pipeline.

### What part 4 needs

A federated language-model head, and the same three reference points the
classification tables use.

- **Backbone.** A small public decoder, frozen. GPT-2 small keeps the vocabulary
  realistic at 50 257 and fits the existing job template.
- **Trainable unit.** A low-rank adapter with the down-projection frozen, plus
  the vocabulary projection. Only the projection is federated.
- **Partition.** Dirichlet over a label proxy. Plain text has no labels, so the
  split needs a topic or a source field. A corpus with document categories gives
  the same skew the classification experiments use.
- **Metric.** Perplexity on a held-out set, under greedy decoding.
- **Baselines.** A client alone, the pooled model, and the frozen backbone with
  no adaptation.

**One open question.** The vocabulary projection of GPT-2 is tied to the input
embedding. Training it as a separate federated map unties them. Untying changes
the model and costs perplexity on its own, which would confound the federation
effect. Decide whether to untie, or to federate a smaller adapter and leave the
projection frozen. The second choice is cheaper but no longer matches the
classification design, where the shared object is the final map.
