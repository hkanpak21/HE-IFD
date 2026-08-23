# Model extraction against the served head

Working notes, 2026-07-29. Not paper text. The paper reports only the
label-only curve (§5.6); everything about answer formats and output noise lives
here until we decide what, if anything, it should say.

## Why this is the only attack worth running

Every derivative of client material in the protocol is a ciphertext under the
collective key, and by Proposition 1 the server's view is computationally
independent of the private data. Gradients, adapters, head displacements, class
counts and the shared head itself are therefore not attackable by anything short
of breaking RLWE or assembling all `N` key shares.

That leaves exactly one channel: **a client asks the served model a question and
reads the answer.** This is the residual, non-cryptographic surface, and it is
the only thing these experiments study. It is not a weakness of the encryption;
it is the interface the deployment exists to provide.

## What kind of attack this is

**Model extraction (model stealing).** The target is the shared classifier head
`θ* = (W, b)`, with `W` of shape `C × d`. It is *not* membership inference:
we are not asking whether some record was in anyone's training set, we are
asking how cheaply a participant can reconstruct the object the federation
refused to hand out.

The distinction matters for how we talk about it. Membership inference threatens
the *data*; extraction threatens the *asset*. Our threat model already grants
that a participant learns the labels it asks for; the question is whether it can
parlay those labels into the model itself.

## The adversary

A **participating client**, which is the strongest label-only adversary the
protocol admits. Three properties, all forced by the design rather than assumed
for convenience:

1. **It queries in feature space directly.** The client computes `φ_j(x)` with
   its own backbone and adapter and encrypts the result, so nothing constrains
   that vector to be the encoding of a real sentence or image. It can submit any
   point in `R^d`. A server-side attacker restricted to natural inputs would be
   strictly weaker.
2. **It knows `C` and `d`.** Both are public: the label space is agreed and the
   backbone is a public checkpoint.
3. **It is charged one query per answer**, and a coalition of `N−1` clients —
   the largest that cannot decrypt — pools its allowances, so the effective
   budget is `(N−1)Q`.

What it does *not* get: gradients, logits (in the deployed protocol), training
data, or any intermediate of the aggregation.

## The attack

Simpler than the name suggests.

1. Draw a feature vector `x`.
2. Send `Enc(x)`, receive the answer.
3. Repeat to collect `{(x_i, answer_i)}`.
4. Fit a linear model to that set. **That fitted model is the stolen head.**

With **labels** the fit is a multinomial logistic regression: the adversary is
learning a linear classifier from membership queries, which is the classical
setting of Lowd and Meek. With **probabilities** it is not learning at all —
`log p` recovers the logits up to a per-query additive constant, so the head
follows from one least-squares solve and `d+1` queries suffice exactly.

### Fidelity

Agreement between the extracted copy and the true served model on held-out
feature vectors:

    fidelity = P[ argmax(Ŵx + b̂) == argmax(Wx + b) ]

This is **functional equivalence, not task accuracy**. A thief wants the model's
behaviour, not its benchmark score, and fidelity is the standard extraction
metric for that reason (Jagielski et al. separate *accuracy* extraction from
*fidelity* extraction and argue fidelity is the right target for an adversary
who wants a substitute). Reading fidelity against the **majority-class share**
is essential: at `C=77` a copy that always answers the most common label already
scores 0.083, and at `C=4` it scores about 0.49.

### Why the argmax is what makes this expensive

Each answer carries at most `log2 C` bits. The head has `C·d` real parameters.
Extraction is therefore an exercise in reconstructing many parameters through a
very narrow channel, which is precisely why the measured cost tracks `C·d`
rather than anything about the task.

## Known limitations of our setup

- **Queries and evaluation are synthetic.** We draw Gaussian feature vectors and
  measure fidelity on the same distribution, because the stored artifacts keep
  logits but not features. We rescale the synthetic distribution so its logit
  spread matches the real test logits, which puts the attack at the right
  operating point, but fidelity against the true feature manifold could differ.
  Worth fixing if this ever becomes paper material.
- **One arrangement.** All numbers below are the shared-head arrangement (`A`).
- **No adaptive attacker.** The adversary does not re-plan queries using its
  current estimate beyond the boundary variant noted below.

## Result 1: the answer format decides everything

Measured on the deployed protocol (label only), mean over three seeds:

| task | C | majority | 10^3 | 5·10^3 | 2·10^4 | 5·10^4 | 2·10^5 |
|---|---|---|---|---|---|---|---|
| ag_news | 4 | 0.488 | 0.635 | 0.823 | 0.936 | 0.973 | 0.993 |
| dbpedia_14 | 14 | 0.250 | 0.387 | 0.612 | 0.804 | 0.901 | 0.971 |
| banking77 | 77 | 0.083 | 0.174 | 0.355 | 0.592 | 0.755 | 0.900 |

Queries to reach a fidelity target, and the same figure as a multiple of the
head's parameter count `C·d`:

| task | C·d | 0.80 | 0.90 | 0.95 | 0.90 as ×(C·d) |
|---|---|---|---|---|---|
| ag_news | 3 072 | 4 380 | 12 311 | 31 473 | 4.0× |
| dbpedia_14 | 10 752 | 19 563 | 49 655 | 117 925 | 4.6× |
| banking77 | 59 136 | 75 616 | 199 912 | >200 000 | 3.4× |

**Rule of thumb: fidelity 0.90 costs three to five queries per parameter.** A
deployment can set its allowance from `C` and `d` without rerunning this.

**The binding case is the small label space.** A head with four rows is cheap to
copy, so AG-News needs a tighter allowance than Banking77 — and AG-News is
exactly where the shared arrangement wins. Counterintuitive, and worth saying out
loud rather than hoping a reviewer misses it.

**Returning probabilities collapses the whole thing.** Fidelity 1.0000 at 1 000
queries, because `d+1 = 769` suffice for an exact solve. The gap between the
deployed protocol and the obvious alternative is not a factor of two; it is a
search versus a solve.

## Result 2: output noise is not a usable defence

Two mechanisms, both applied to the answer rather than to the training data:

- **label**: randomised response, a clean `ε`-local-DP randomiser — return the
  true label with probability `e^ε/(e^ε+C−1)`, else uniform among the other
  `C−1`.
- **probs**: logits clipped to the 99th percentile and perturbed by the Gaussian
  mechanism at `(ε, δ=10⁻⁵)`.

`task_acc` is what an honest user gets from the **defended** model. Both columns
must be read together: a defence that stops extraction by destroying the model is
not a defence. Mean over three seeds.

| task | access | ε | task_acc | fid @2·10⁴ | fid @5·10⁴ | fid @10⁵ |
|---|---|---|---|---|---|---|
| ag_news (C=4) | label | ∞ | 0.649 | 0.946 | 0.978 | 0.989 |
| | label | 8 | 0.648 | 0.914 | 0.975 | 0.986 |
| | label | 4 | 0.620 | 0.892 | 0.938 | 0.954 |
| | label | 2 | 0.494 | 0.775 | 0.852 | 0.889 |
| | label | 1 | 0.372 | 0.594 | 0.702 | 0.774 |
| | label | 0.5 | 0.303 | 0.427 | 0.518 | 0.598 |
| | probs | ∞ | 0.649 | **1.000** | 1.000 | 1.000 |
| | probs | 8 | 0.266 | 0.349 | 0.416 | 0.484 |
| | probs | 2 | 0.250 | 0.266 | 0.283 | 0.307 |
| dbpedia (C=14) | label | ∞ | 0.789 | 0.806 | 0.914 | 0.956 |
| | label | 8 | 0.785 | 0.728 | 0.895 | 0.946 |
| | label | 4 | 0.640 | 0.629 | 0.768 | 0.831 |
| | label | 2 | 0.297 | 0.321 | 0.458 | 0.571 |
| | label | 1 | 0.150 | 0.146 | 0.208 | 0.268 |
| | probs | ∞ | 0.787 | **1.000** | 1.000 | 1.000 |
| | probs | 8 | 0.085 | 0.128 | 0.164 | 0.211 |
| banking77 (C=77) | label | ∞ | 0.206 | 0.444 | 0.642 | 0.777 |
| | label | 8 | 0.203 | 0.387 | 0.425 | 0.722 |
| | label | 4 | 0.092 | 0.101 | 0.243 | 0.364 |
| | label | 2 | 0.028 | 0.025 | 0.037 | 0.052 |
| | probs | ∞ | 0.185 | **1.000** | 1.000 | 1.000 |
| | probs | 8 | 0.012 | 0.017 | 0.020 | 0.023 |

### Reading it

**Returning a distribution is indefensible, with or without noise.** Undefended,
fidelity is 1.000 at every budget — one least-squares solve. Add enough noise to
bring extraction down and the model goes with it: on DBpedia `ε=8` leaves the
honest user at 0.085 against an undefended 0.787, which is below the majority
class. The Gaussian mechanism on a `C`-dimensional logit vector has L2
sensitivity growing as `√C`, so the noise needed scales with the label space
while the signal does not. There is no operating point where probabilities are
worth returning.

**Randomised response on labels buys a real reduction at a bad exchange rate.**
On AG-News, `ε=2` costs 0.155 of accuracy and moves the adversary from 0.989 to
0.889. The honest user pays about one accuracy point per point of fidelity
denied, and pays it on *every* query, while the adversary averages the noise away
over tens of thousands. Noise on an i.i.d. channel is precisely what a large
sample defeats.

**The damage grows with the label space**, because randomised response keeps the
true label with probability `e^ε/(e^ε+C−1)`. At `C=4, ε=4` that is 0.95, so the
cost is mild; at `C=77, ε=4` it is 0.42, so most answers are wrong and accuracy
falls from 0.206 to 0.092 — while fidelity is still 0.364, well above the 0.083
majority baseline. The model is destroyed before extraction is stopped.

**No configuration is attractive.** Across all eighteen (task, mechanism, ε)
cells there is none that pushes fidelity near the majority baseline while
retaining usable accuracy. The cheap settings (`ε=8`) barely move the adversary;
the settings that move the adversary are not deployable.

### Conclusion for the paper

This supports the wording already in §Scope rather than changing it: **the query
allowance is the control, and output perturbation is not a substitute for it.**
Differential privacy remains orthogonal and compatible — it protects the training
data, which is a different problem from protecting the model.

One framing is worth promoting into §5.6 if we want it: with an `ε`-LDP answer
and `Q` queries, composition gives `Qε`, so **the query allowance and a privacy
budget are the same quantity in different units.** That is a better justification
for metering than "set it below the extraction cost".

## Result 3: the clever attack is worse

A boundary-search variant spends half its budget bisecting toward the decision
boundary, on the theory that near-boundary points are more informative for a
linear model. It is consistently *worse* — 0.592 against 0.755 on Banking77 at
`5·10^4` — because a bisection chain returns a dozen nearly identical points and
a least-squares fit gains far less from those than from a dozen independent ones.
We report the uniform attack, which is both stronger and simpler.

(An earlier version of this experiment reconstructed each decision hyperplane
separately by SVD over collected boundary points and reported fidelity around
0.30 at `7·10^4` queries. That attack is broken: with `C > 2` the segment between
two points can cross a third class's region so the points do not lie on one
hyperplane, and each hyperplane is recovered only up to an independent scale
which the argmax does not preserve. It made the protocol look far safer than it
is. Discarded.)

## Literature basis

The correct term for our setting is the **hard-label** setting: the adversary
sees only the predicted class. That vocabulary is worth adopting throughout,
because it is what the current literature uses and it locates our design
precisely.

### The load-bearing citation

**Carlini et al., *Stealing Part of a Production Language Model*, ICML 2024**
(Best Paper; arXiv:2403.06634). They recover **the final projection layer of a
production transformer** — structurally the same object as our head — from
OpenAI's Ada and Babbage for under \$20, and estimate under \$2 000 for
gpt-3.5-turbo.

The detail that matters for us is the access their attack needs: **log
probabilities of top tokens together with a logit bias**. It is not a hard-label
attack. And the deployed response by OpenAI and Google was to **restrict the
ability to supply logprobs and logit bias together**, which raises the attack's
cost without eliminating it.

So the strongest published attack on exactly our object required an interface
richer than a label, and industry's mitigation was to withdraw that richness.
Our protocol never offers it in the first place — not as policy, which can be
relaxed, but as a property of the construction. Our `probs` measurement is the
same point from the other side: hand back a distribution and fidelity is 1.000
at 1 000 queries.

### Hard-label extraction, current state

- **Chen, Dong, Guo, Shen, Wang and Wang**, *Hard-Label Cryptanalytic Extraction
  of Neural Network Models*, **ASIACRYPT 2024** — the first functionally
  equivalent extraction in the hard-label setting, for ReLU networks. Confirms
  that hard-label extraction of a *deep* network is recent and hard.
- **Carlini, Chávez-Saab, Hambitzer, Rodríguez-Henríquez and Shamir**,
  *Polynomial Time Cryptanalytic Extraction of Deep Neural Networks in the
  Hard-Label Setting*, **EUROCRYPT 2025**.
- **Canales-Martínez et al.**, *Polynomial Time Cryptanalytic Extraction of
  Neural Network Models*, **EUROCRYPT 2024** — the non-hard-label predecessor.

Honest caveat to keep in view: those results concern deep ReLU networks, where
hard-label extraction is genuinely difficult. **Our shared object is a single
linear layer**, for which hard-label extraction is not a cryptanalytic problem at
all but an ordinary learning problem — which is exactly why our measured costs
are modest (three to five queries per parameter) and why the allowance, not the
hardness, is what carries the guarantee. We should not let the cryptanalytic
citations imply that our head inherits their difficulty.

### Already cited in the paper

- **Tramèr et al.**, *Stealing Machine Learning Models via Prediction APIs*,
  USENIX Security 2016 — equation-solving extraction from confidences. Older, but
  it is the canonical statement of the solve-versus-search distinction and our
  `probs` case reproduces it exactly.
- **McSherry and Talwar** — the output-perturbation family the noise cases sit in.

### Optional, only if a reviewer forces it

- **Jagielski et al.**, *High Accuracy and High Fidelity Extraction of Neural
  Networks*, USENIX Security 2020 — source of the accuracy/fidelity distinction.
  Note `refs.bib` already contains `jagielski2023students`, a *different* paper.
- Query-pattern detection as an alternative to metering. A reviewer may ask why
  we rate-limit rather than detect; the answer is that detection is a heuristic
  and the allowance is not, but we have not measured detection and should not
  claim anything about it.

## Files

- `jobs/extraction_budget.py` — the label-only curve (paper §5.6).
- `jobs/extraction_defence.py` — answer formats and output noise (this note).
- `jobs/ext_report.py` — summariser.
- `results/extraction_budget/results.csv`, `results/extraction_defence/results.csv`.

Both run from stored artifacts on CPU: no backbone, no adapter, no GPU, no
training or inference pass.
