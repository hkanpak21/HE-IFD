# T34. Shorten the related work. Find and replace list

Answers Küpçü's comment of 11 August, 7:10 pm, "bu bölüm aşırı uzun. özellikle
related work kısmını kısaltmalıyız ve bir özet tablo sunmalıyız", and item T8 of
`docs/plan/paper-todo-2026-08-19.md`. It also closes Sav's notes 17 to 20 of
`PI_notes_2026-08-06.md` where they still stood open, and one checklist item.

Nothing here is applied to `docs/paper/`. Each entry gives the file, the
approximate line, the current text verbatim, and the replacement. Paste in file
order. **The only file touched is `sections/related.tex`.**

## What it measures

| what | before | after |
|---|---|---|
| prose words in `related.tex` | 2026 | 1532 |
| words removed | | 494, or 24 per cent |
| citation keys | 80 | 80 |
| `\cite` commands | 53 | 38, of which 6 are in the new table |
| typeset lines of the section | 233 | 178 plus the table |
| **manuscript page count** | **21** | **20** |

Both numbers in the last row are from a real build. I copied `docs/paper` twice,
pasted this list into one copy, and ran `pdflatex`, `bibtex`, `pdflatex`,
`pdflatex` on each. No errors, no new overfull boxes, no undefined references.

The prose cut is worth about 55 typeset lines, which is one full column. The
table costs 10 tabular lines and a 5-line caption at `\footnotesize`, which is
about a third of a column. Net saving is about two thirds of a column of text.
The manuscript loses a whole page because page 21 held only 18 lines of
references, and two thirds of a column was enough to empty it.

## Two warnings before you paste

1. **The new table becomes Table I and every other table number shifts by one.**
   Table II becomes Table III, and so on. Nothing inside the manuscript breaks,
   because every table is referenced with `\cref` and no section names a table by
   number. But the record map in `CLAUDE.md` is keyed by number and will be one
   out of date until it is updated.
2. **Block B10 overlaps `T25-destructure.md` item C1.** C1 removes "rather than
   re-solve it" from the same sentence. B10 rewrites the whole paragraph and
   removes it as well. If C1 has already gone into Overleaf, the B10 anchor will
   not match, and the fix is to drop the words "rather than\nre-solve it" from the
   FIND block. If neither has gone in, paste B10 and skip C1.

## What was collapsed

The device is one sentence carrying every citation at once. Applied at six sites.

| site | was | now |
|---|---|---|
| 2.1, final-model attacks | five works described in three sentences | one sentence, five keys |
| 2.2, encrypted aggregation | BatchCrypt, FedML-HE, FedSHE, SHE-LoRA and Hyb-Agg named one by one | one sentence, five keys, SHE-LoRA named again only where it carries the key-structure argument |
| 2.2, encrypted transfer learning | eight works in four clauses | one sentence, eight keys |
| 2.3, one-shot methods | eight works in two long sentences | two sentences, eight keys |
| 2.4, adapter merging and task arithmetic | seven works named one by one | two sentences, seven keys |
| 2.5, secure inference systems | four works split into non-interactive and interactive | one sentence, four keys |

Three passages were cut rather than collapsed.

- The opening paragraph of 2.2, which set encryption against differential
  privacy. Section 2.3 makes the same comparison and supports it. B3.
- The ciphertext-by-ciphertext aside in 2.5. `method.tex` already states it in
  `sec:serving`. B10.
- The second closing paragraph, which derived that a model never decrypted must
  answer from public components. `sec:setting` carries that derivation. B14.

## What was preserved, deliberately

- 2.1 still establishes the premise the paper rests on. The measured comparison,
  87 per cent against the update stream falling to 54.5 per cent against the final
  model, sits in `intro.tex` and is untouched.
- POSEIDON keeps its own sentence, and the point that its cost scales with the
  network being trained is now stated here as well as in the introduction. Without
  it, 2.2 does not explain why encrypted training cannot reach a pretrained
  transformer.
- The differentially private one-shot line stays identifiable. FedAUXfdp is still
  named, because it is the peer the experiments run against.
- slytHErin keeps a full paragraph and both differences, that it evaluates the
  whole network and that it returns the score vector.
- The section still says what each line of work achieves before it says what it
  leaves open. Secure aggregation is lossless. POSEIDON loses no accuracy. The
  one-shot line established that one round is enough. The encrypted argmax
  literature is faster than ours. None of that was cut.

## Three checks the brief asked for

1. **"Read that way the peer group separates into three cases", Sav, 17 August.**
   It is not in `related.tex`. It is `sections/experiments.tex` line 210, in
   `sec:exp-peers`. Out of scope for this file and it needs its own item.
2. **"adds no noise".** Not present anywhere under `docs/paper/`. The nearest
   wording in 2.2 was "the model loses no accuracy", which is a different claim
   and is correct. Nothing to fix.
3. **Unbacked "most".** Two sites, both fixed. 2.5 said "Most of these systems
   evaluate a plaintext model on encrypted inputs" over four cited works, and the
   claim is wrong for the secret-sharing ones. The sentence is gone with B10. 2.2
   said "Most are also single-party" over eight cited works. B6 makes it "Several
   of them are also single-party", which is what the sources support.

## Orphaned citations

**None.** All 80 keys in the section survive. Checked by extracting every key from
the section before and after and comparing the sets. No key in this section is the
sole support for a claim elsewhere, because the six keys that appear in more than
one file all keep their occurrence here.

## Sourcing for every cell of the new table

`comparators/REPORTED_RESULTS.md` section numbers are given. No cell is inferred.

| cell | source |
|---|---|
| DENSE, one round | §4 cheatsheet, "One-shot? yes" |
| DENSE, protection none | §4 cheatsheet, "plaintext, data-free" |
| GH-OFL, one round | §20 cheatsheet, "yes" |
| GH-OFL, protection none | §20, "none, uploads per-class sufficient statistics in plaintext" |
| FedAUXfdp, one round | §12 cheatsheet, "yes" |
| FedAUXfdp, protection DP | §12, "(ε, δ)-DP" |
| POSEIDON, many rounds | §8 cheatsheet, "no (multi-round)" |
| POSEIDON, protection HE | §8, "HE (multiparty CKKS, Mouchet 2021)" |
| slytHErin, rounds blank | §16 cheatsheet, "n/a, inference only, no training" |
| slytHErin, protection HE | §16, "HE + multiparty CKKS" |
| slytHErin, model not in the clear | §16, "Scenario 3 = model AND data encrypted, model never decrypted" |
| slytHErin, querier receives scores | §16, "the querier receives the prediction result, i.e. the score vector, NOT a label" |
| CryptPEFT, rounds blank | §17 cheatsheet, "n/a, inference only" |
| CryptPEFT, protection 2PC | §17, "MPC (2-party), not HE" |
| CryptPEFT, model in the clear to the provider | §17, "adapter is the provider's plaintext secret" |
| CryptPEFT, querier receives label | §17, "client receives the label" |
| the four "yes" cells in the model column | §16, "it is the only prior system found that serves a model held under a multiparty key and never decrypted" |
| HE-OFT row, every cell | `docs/paper/sections/method.tex` and `results/fhe_serve/` |

**FedHEONN is not in the table**, although it is the closest single prior scheme
and the positioning paragraph still cites it. It has no entry in
`REPORTED_RESULTS.md`, so its cells cannot be sourced. If you want the row, the
paper has to be read and transcribed first.

**Hyb-Agg is not in the table** either. It is a protocol-only paper with no model
and no query interface, so four of its five cells would be empty (§15).

---

# `sections/related.tex`

## B1. `sections/related.tex`, 2.1, around line 11

Two paragraphs become one.

FIND

```latex
Federated learning (FL) began as an iterative procedure in which a server repeatedly
broadcasts a model, clients train it on their own data, and the server averages
the returned updates~\cite{mcmahan2017communication}. In every round each client sends a new update computed on its private data. Several
attacks have shown that these updates leak more than anything else the protocol
reveals.

A gradient allows reconstruction of the batch that produced it, pixel-accurate on
images~\cite{zhu2019deep} and at high resolution even from trained networks, where
averaging over a hundred images or a hundred local steps still leaves individual
inputs recoverable~\cite{geiping2020inverting}. An observer of the per-round
updates in FL infers membership and unintended properties of another client's
data~\cite{nasr2019comprehensive,melis2019exploiting}, and the repetition of those
updates is what makes the attack strong. Accuracy grows with the number of rounds observed~\cite{zari2021efficient}. A server that chooses the weights it broadcasts does not need inference at all.
Crafted weights make clients return verbatim copies of their own inputs, even
through a secure-aggregation layer~\cite{boenisch2023curious,fowl2022robbing}. Several works use federated distillation to avoid this, sharing predictions instead
of gradients. The predictions leak too. Attacks recover images from shared
logits~\cite{takahashi2023breaching} and infer membership from distillation
outputs~\cite{yang2023fdleaks,gu2023ldia,shi2025unveiling}.
```

REPLACE

```latex
Federated learning (FL) began as an iterative procedure in which a server
repeatedly broadcasts a model, clients train it on their own data, and the server
averages the returned updates~\cite{mcmahan2017communication}. In every round each
client sends a new update computed on its private data, and several attacks have
shown that these updates leak more than anything else the protocol reveals. A
gradient allows reconstruction of the batch that produced
it~\cite{zhu2019deep,geiping2020inverting}. An observer of the per-round updates
infers membership and unintended properties of another client's data, and the
repetition of those updates is what makes the attack
strong~\cite{nasr2019comprehensive,melis2019exploiting,zari2021efficient}. A server
that chooses the weights it broadcasts does not need inference at all, since
crafted weights make clients return verbatim copies of their own inputs, even
through a secure-aggregation layer~\cite{boenisch2023curious,fowl2022robbing}.
Several works share predictions instead of gradients, and the predictions leak
too~\cite{takahashi2023breaching,yang2023fdleaks,gu2023ldia,shi2025unveiling}.
```

## B2. `sections/related.tex`, 2.1, around line 31

Two paragraphs become one.

FIND

```latex
Attacks that see only the final model are consistently weaker. The field survey
separates adversaries who watch the intermediate updates from those who see only
the final model~\cite{kairouz2021advances}. Membership inference against a final model is a mature
literature~\cite{shokri2017membership,yeom2018privacy,salem2019ml}. Against models
that generalise well it identifies few members, and only at very low false-positive
rates~\cite{carlini2022membership}. Model inversion
needs released confidences and strong priors~\cite{fredrikson2015model,hitaj2017deep}.

The reason is simple. An update is a detailed view of one client's data, and the
protocol sends a new one every round. The final model is a single average, and
generalisation moves it away from any one training example. Our design follows. A
protocol that never sends an update, and that sends anything only once, leaves
every adversary with the weaker attack.
```

REPLACE

```latex
Attacks that see only the final model are consistently weaker, and the field
survey draws that separation explicitly~\cite{kairouz2021advances}. Several works
infer membership from a released model, or invert it from released
confidences~\cite{shokri2017membership,yeom2018privacy,salem2019ml,fredrikson2015model,hitaj2017deep},
and against models that generalise well they identify few members, and only at
very low false-positive rates~\cite{carlini2022membership}. The reason for the gap
is simple. An update is a detailed view of one client's data and arrives every
round, where the final model is a single average that generalisation moves away
from any one training example. A protocol that never sends an update, and that
sends anything only once, therefore leaves every adversary with the weaker
attack.
```

## B3. `sections/related.tex`, 2.2, around line 49

Deletion. The framing paragraph goes, because 2.3 makes the same comparison with evidence.

FIND

```latex
The cryptographic line protects training-time quantities without altering the
model, in contrast to differential privacy, which perturbs the quantities
themselves and pays for the guarantee in accuracy.

Secure aggregation lets the server learn only the sum of the clients' updates,
using masks that cancel in the aggregate~\cite{bonawitz2017practical}.
```

REPLACE

```latex
Secure aggregation lets the server learn only the sum of the clients' updates,
using masks that cancel in the aggregate~\cite{bonawitz2017practical}.
```

## B4. `sections/related.tex`, 2.2, around line 57

FIND

```latex
rounds~\cite{so2023securing,kerkouche2023client}. Homomorphic encryption goes
further by computing on contributions that stay encrypted. In its most ambitious
form it trains a network entirely under encryption. POSEIDON runs encrypted
stochastic gradient descent under multiparty CKKS, with activations replaced by
polynomial approximations so that they can be evaluated
homomorphically~\cite{sav2021poseidon}. The guarantee is strong and the model loses no accuracy. The approach is iterative,
and encrypted nonlinearity costs a deep multiplicative circuit, repeated
bootstrapping, and hours of wall-clock time. The
delicacy of polynomial activations is documented by a substantial line of
work~\cite{garimella2021sisyphus,baruch2022methodology,agamennone2025polynomial,alhossain2025training,ibarrondo2021fhebn}.
```

REPLACE

```latex
rounds~\cite{so2023securing,kerkouche2023client}. Homomorphic encryption goes
further by computing on contributions that stay encrypted. POSEIDON runs encrypted
stochastic gradient descent under multiparty CKKS, with activations replaced by
polynomial approximations so that they can be evaluated
homomorphically~\cite{sav2021poseidon}. The guarantee is strong and the model
loses no accuracy, but the approach is iterative and encrypted nonlinearity costs
a deep multiplicative circuit with repeated bootstrapping. Several works measure
how delicate those polynomial activations
are~\cite{garimella2021sisyphus,baruch2022methodology,agamennone2025polynomial,alhossain2025training,ibarrondo2021fhebn}.
That cost scales with the network being trained, so adapting a pretrained
transformer by this route is out of reach.
```

## B5. `sections/related.tex`, 2.2, around line 68

Five systems collapse into one sentence.

FIND

```latex
A lighter line encrypts only the aggregation of an otherwise plaintext training
loop. BatchCrypt, FedML-HE and FedSHE develop packed and quantised encrypted
summation for cross-silo
training~\cite{zhang2020batchcrypt,jin2023fedml,wei2025fedshe}, SHE-LoRA
selectively encrypts a sensitivity-chosen subset of a low-rank adapter each
round~\cite{li2025shelora}, and hybrid multi-key schemes reduce a round of secure
summation to one client-to-server transmission~\cite{kemmaka2025hybagg}. All of
these remain bound to the iterative protocol. The encryption cost is paid on every
round, and what is protected is a per-round sum rather than a complete
contribution. SHE-LoRA also shows why key structure matters. It uses single-key
homomorphic encryption and therefore has to assume that the server and the clients
do not collude, since any client that revealed its key to the server would undo
the protection. The threshold structure of \cref{sec:mhe} removes the need for that assumption.
```

REPLACE

```latex
Several works encrypt only the aggregation step of an otherwise plaintext training
loop~\cite{zhang2020batchcrypt,jin2023fedml,wei2025fedshe,li2025shelora,kemmaka2025hybagg}.
All of them remain bound to the iterative protocol, so the encryption cost is paid
on every round and what is protected is a per-round sum rather than a complete
contribution. One of them also shows why key structure matters, since single-key
homomorphic encryption forces the assumption that the server and the clients do
not collude~\cite{li2025shelora}. The threshold structure of \cref{sec:mhe} removes
that assumption.
```

## B6. `sections/related.tex`, 2.2, around line 83

Eight systems collapse into one sentence.

FIND

```latex
Transfer learning itself has been placed under encryption. HETAL trains a softmax
classifier head on frozen features entirely under CKKS~\cite{lee2023hetal},
following a longer line that runs linear and logistic training
homomorphically~\cite{kim2018securelr,kim2018logistic,chiang2025cnn}. A federated
variant encrypts the fine-tuned last layer across many
rounds~\cite{privfedtl2026}, a concurrent scheme averages encrypted feature tokens
under a single decryption key~\cite{alamin2025vit}, and recent schemes run
low-rank-adapter fine-tuning under encryption between a model owner and data
owners~\cite{li2024privtuner,frery2025private}. These share our structural niche,
a frozen public backbone with a small trainable unit, but they run an optimiser on
ciphertexts, so multiplicative depth grows with the step count and every
nonlinearity must be approximated. Most are also single-party, one data owner
outsourcing computation rather than a collaboration of mutually distrustful
parties. They solve a different problem. A party that cannot train on its own outsources the
work. Our parties train on their own and must protect what they trained.
```

REPLACE

```latex
Transfer learning itself has been placed under encryption. Several works train a
classifier head, a linear or logistic model, or a low-rank adapter on frozen
features under
CKKS~\cite{lee2023hetal,kim2018securelr,kim2018logistic,chiang2025cnn,privfedtl2026,alamin2025vit,li2024privtuner,frery2025private}.
These share our structural niche, a frozen public backbone with a small trainable
unit, but they run an optimiser on ciphertexts, so multiplicative depth grows with
the step count and every nonlinearity must be approximated. Several of them are
also single-party, one data owner outsourcing computation rather than a
collaboration of mutually distrustful parties. Our parties train on their own and
must protect what they trained.
```

## B7. `sections/related.tex`, 2.3, around line 102

Three, then five systems collapse.

FIND

```latex
A parallel line collapses the many rounds into a single
exchange~\cite{guha2019oneshot,wang2025towards}. Early knowledge-transfer methods
had clients exchange predictions on a shared public
set~\cite{li2019fedmd,itahara2021dsfl}, in practice repeating the exchange, and
ensemble distillation trains a server model against aggregated client predictions
over many rounds~\cite{lin2020feddf}. Genuinely single-round methods arrived with
data-free distillation, in which the server distils the clients' models through a
generator or synthesised inputs~\cite{zhang2022dense,dai2024coboosting}, and with
fusion methods that aggregate client models through a layer-wise
posterior~\cite{liu2024fedlpa,zhang2024fedsd2c} or stitch them together in stages
whose total cost the authors account as a single round~\cite{tang2024fusefl}.
These establish that one round can produce a usable model, but they work in
plaintext. Each client sends one contribution, an entire model or a synthetic
distillate of its data, and by the evidence of \cref{sec:related-leakage} that is
what an adversary would target. A recent method removes the model from the
exchange altogether, having each client run a frozen pretrained encoder and upload
per-class sufficient statistics once, from which the server fits a closed-form
head~\cite{turazza2026ghofl}. That is one round and it sends no model, but the
statistics travel in plaintext, and per-class totals are exactly what
\cref{sec:split} keeps encrypted.
```

REPLACE

```latex
A parallel line collapses the many rounds into a single
exchange~\cite{guha2019oneshot,wang2025towards}. Several works exchange predictions
on a shared public set, which in practice repeats the
exchange~\cite{li2019fedmd,itahara2021dsfl,lin2020feddf}. Genuinely single-round
methods distil the clients' models through a generator or synthesised inputs, or
fuse the models directly, in one round or in stages the authors account as
one~\cite{zhang2022dense,dai2024coboosting,liu2024fedlpa,zhang2024fedsd2c,tang2024fusefl}.
These establish that one round can produce a usable model, but they work in
plaintext, and each client sends an entire model or a synthetic distillate of its
data. By the evidence of \cref{sec:related-leakage} that is what an adversary would
target. A recent method sends no model at all, having each client run a frozen
pretrained encoder and upload per-class sufficient statistics
once~\cite{turazza2026ghofl}. Those statistics travel in plaintext, and per-class
totals are exactly what \cref{sec:split} keeps encrypted.
```

## B8. `sections/related.tex`, 2.3, around line 124

FedAUXfdp stays named. The DP transfer-learning tail collapses.

FIND

```latex
The one-shot methods that do address privacy use differential privacy. FedAUXfdp
releases client contributions under a differentially private mechanism after
distillation through a pretrained extractor~\cite{hoech2022fedauxfdp}, and related
approaches protect a diffusion-generated~\cite{feddiff2024} or
teacher-ensemble~\cite{li2021fedkt} surrogate, or add noise-free differential
privacy to the distillation itself~\cite{sun2021fedmdnfdp}. These are our natural
quantitative peers, and their privacy is lossy. The noise a meaningful budget
requires is added to the very artifact that is released, so accuracy falls as the
budget tightens. The guarantee also differs in kind. Differential privacy proves a
statistical bound on how much a released artifact can reveal and buys that bound
with accuracy. Encryption makes a contribution computationally indistinguishable
from random to every party without the key and costs the model nothing. The same
trade-off structures differentially private transfer learning, where noisy
gradient descent on frozen features reaches strong accuracy at moderate
budgets~\cite{tramer2021features,mehta2022dpfeatures,yu2022dpft,li2022dplearners},
extended to federated low-rank adaptation~\cite{liu2023dplora,xu2024dpdylora}.
Those methods share our backbone-and-adapter structure and confirm that frozen
public features are a good substrate for private learning, but they pay a
budget-dependent accuracy tax on the model they release, and they are centralised
or multi-round.
```

REPLACE

```latex
The one-shot methods that do address privacy use differential privacy. FedAUXfdp
releases client contributions under a differentially private mechanism after
distillation through a pretrained extractor~\cite{hoech2022fedauxfdp}, and related
approaches protect a diffusion-generated surrogate or a teacher
ensemble~\cite{feddiff2024,li2021fedkt}, or apply a noise-free mechanism to the
distillation itself~\cite{sun2021fedmdnfdp}. These are our natural quantitative
peers, and their privacy is lossy, because the noise a meaningful budget requires
is added to the very artifact that is released. Differential privacy proves a
statistical bound on how much a released artifact can reveal and buys that bound
with accuracy. Encryption makes a contribution computationally indistinguishable
from random to every party without the key and costs the model nothing. Several
works apply the same trade-off to transfer learning, running noisy gradient descent
on frozen features or on a low-rank
adapter~\cite{tramer2021features,mehta2022dpfeatures,yu2022dpft,li2022dplearners,liu2023dplora,xu2024dpdylora}.
They share our backbone-and-adapter structure, but they pay a budget-dependent
accuracy tax on the model they release, and they are centralised or multi-round.
```

## B9. `sections/related.tex`, 2.4, around line 148

Four adapter variants and three task-arithmetic results collapse.

FIND

```latex
round~\cite{zhang2024fedit}, but per-factor averaging is biased. A client learns a
product of two factors, and averaging the factors separately does not give the
average of the products. FLoRA removes the discrepancy by stacking
factors~\cite{wang2024flora}, FlexLoRA by reconstructing full products and
re-factoring~\cite{bai2024flexlora}, HetLoRA by reconciling heterogeneous
ranks~\cite{cho2024hetlora}, and FedSA-LoRA by sharing only one
factor~\cite{guo2025fedsalora}. FFA-LoRA freezes the randomly initialised
down-projection and trains only the up-projection, so that averaging the trained
factor is exact. It was introduced to stabilise multi-round differentially private
tuning~\cite{sun2024ffalora}. Algebraically, combining displacements from a shared
initialiser is task-vector merging~\cite{ilharco2023editing}, which has been shown
equivalent to one-shot federated averaging~\cite{tao2024taskarith}, and that one
round of fine-tuning suffices for foundation models is established in
plaintext~\cite{malinovsky2024oneround}. What none of this line provides is any
protection of the contributions, which is our subject.
```

REPLACE

```latex
round~\cite{zhang2024fedit}, but per-factor averaging is biased, because a client
learns a product of two factors and averaging the factors separately does not give
the average of the products. Several works correct that bias by stacking factors,
by reconstructing full products, by reconciling heterogeneous ranks, or by sharing
one factor
only~\cite{wang2024flora,bai2024flexlora,cho2024hetlora,guo2025fedsalora}.
FFA-LoRA instead freezes the randomly initialised down-projection and trains only
the up-projection, so that averaging the trained factor is
exact~\cite{sun2024ffalora}. Combining displacements from a shared initialiser is
task-vector merging, which is equivalent to one-shot federated averaging, and one
round of fine-tuning suffices for foundation models in
plaintext~\cite{ilharco2023editing,tao2024taskarith,malinovsky2024oneround}. None
of this line protects the contributions, which is our subject.
```

## B10. `sections/related.tex`, 2.5, around line 169

Four secure-inference systems collapse. The ciphertext-by-ciphertext aside goes, because method.tex already states it.

FIND

```latex
inference. Non-interactive systems evaluate a transformer under CKKS on
GPUs~\cite{zhang2025nexus}, and interactive protocols combine homomorphic
encryption with secret sharing to evaluate transformers between two or three
parties~\cite{hao2022iron,pang2024bolt,dong2023puma}, with the nonlinearities of
attention as the dominant cost. This literature is what makes the disclosure
setting of \cref{sec:serving} affordable, and we compose with it rather than
re-solve it. The map served here is linear in the features. Serving a trained map
that sits inside the backbone instead would reduce to exactly the problem these
systems address. One difference should be stated. Most of these systems evaluate a
plaintext model on encrypted inputs, whereas the shared weights here are encrypted
as well, so each site would carry a ciphertext-by-ciphertext product rather than a
ciphertext-by-plaintext one. Since the dominant cost in that literature is the
nonlinearities, which are unchanged, the difference is an additive term rather
than a change of order.
```

REPLACE

```latex
inference. Several works evaluate a transformer under encryption, either
non-interactively under CKKS or between two or three parties with secret sharing,
and in each case the nonlinearities of attention dominate the
cost~\cite{zhang2025nexus,hao2022iron,pang2024bolt,dong2023puma}. This literature
is what makes the disclosure setting of \cref{sec:serving} affordable, and we
compose with it. The map served here is linear in the features, so serving a
trained map that sits inside the backbone instead would reduce to exactly the
problem these systems address.
```

## B11. `sections/related.tex`, 2.5, around line 185

slytHErin keeps both differences.

FIND

```latex
Two systems sit closer, and both deserve a full statement. slytHErin evaluates a
network under CKKS in three arrangements, an encrypted input against a plaintext
model, a plaintext input against an encrypted model, and both
encrypted~\cite{intoci2023slytherin}. The last holds the model under a multiparty
key and key-switches the prediction to the querier, which is the serving setting
of \cref{sec:serving}, and the same group built the encrypted training scheme of
\cref{sec:related-crypto}, so the pair is the closest existing route to a model
that no party decrypts. Two properties separate it from what follows. It evaluates
the whole network homomorphically, which is why the models it reports are a
twenty-layer and a fifty-layer network on a handwritten-digit task rather than a
pretrained encoder. And it returns the prediction vector, so the querier receives
scores. A score vector is a materially cheaper target for the extraction attack of
\cref{sec:exp-leak} than a label is.
```

REPLACE

```latex
Two systems sit closer. slytHErin evaluates a network under CKKS with the model
held under a multiparty key, and it key-switches the prediction to the querier,
which is the serving setting of \cref{sec:serving}~\cite{intoci2023slytherin}. The
same group built the encrypted training scheme of \cref{sec:related-crypto}, so
the pair is the closest existing route to a model that no party decrypts. Two
properties separate it from what follows. It evaluates the whole network
homomorphically, which is why the models it reports are a twenty-layer and a
fifty-layer network on a handwritten-digit task rather than a pretrained encoder.
And it returns the prediction vector, so the querier receives scores, which
\cref{sec:exp-leak} shows is a materially cheaper target for extraction than a
label is.
```

## B12. `sections/related.tex`, 2.5, around line 199

FIND

```latex
alone~\cite{xia2026cryptpeft}. The motivation is the one that forces our design.
Confining encrypted computation to a small trained unit placed after the
representation avoids evaluating every nonlinearity of a backbone homomorphically.
It is a two-party protocol between one client and one provider, the trained unit is
that provider's plaintext, and there is no training protocol, so it establishes
that the serving arrangement is practical without addressing how mutually
distrustful parties would build the unit at all.
```

REPLACE

```latex
alone~\cite{xia2026cryptpeft}. Confining encrypted computation to a small unit
after the representation is the motivation for our design as well. It is a
two-party protocol, the trained unit is the provider's plaintext, and there is no
training protocol, so it establishes that the serving arrangement is practical
without addressing how mutually distrustful parties would build the unit at all.
```

## B13. `sections/related.tex`, 2.5, around line 211

The two argmax primitives collapse.

FIND

```latex
The encrypted maximum is a primitive with its own literature, and constructions
faster than the tournament of \cref{sec:serving} exist. Ranking and order
statistics under CKKS have been given at constant comparison
depth~\cite{mazzone2025ranking}, and a decoding method for language models returns
an encrypted indicator of the maximum without decrypting the scores that produced
it~\cite{avitan2025cutmax}. Both are single-key and neither carries the collective
refreshes that the threshold setting requires, so neither transfers unchanged.
```

REPLACE

```latex
Constructions for the encrypted maximum faster than the tournament of
\cref{sec:serving} exist, both for ranking and order statistics at constant
comparison depth and for decoding a language model without decrypting the
scores~\cite{mazzone2025ranking,avitan2025cutmax}. Both are single-key and neither
carries the collective refreshes that the threshold setting requires, so neither
transfers unchanged.
```

## B14. `sections/related.tex`, 2.5, around line 221

The summary table goes in here, and the two closing paragraphs become one.

FIND

```latex
\medskip
\noindent\emph{Positioning.}
The evidence of \cref{sec:related-leakage} says that the decisive attack surface is
the one exposed while training runs, and the four lines that follow each remove
part of it. The multi-round cryptographic line protects every round but pays on
every round, and what it protects is a per-round sum. The one-shot line exposes its
single contribution in plaintext, or noises it and pays in accuracy. The
fine-tuning line communicates a small object but protects nothing. Every one of
them, moreover, ends by handing the finished model to the participants, so the
model itself remains a disclosed artifact. A single prior scheme is at once
one-shot, federated and encrypted, but only for a single-layer closed-form learner
that cannot adapt a deep representation~\cite{fedheonn2023}.

What remains unaddressed is a protocol that exposes no training-time quantity, that
exchanges anything at all only once, and that never discloses the model even to
the parties that built it. The third changes what can be shared, because a model that is never decrypted must
still answer questions from public components alone. \Cref{sec:method} works out what that forces, and the rest of the
paper measures what it costs.
```

REPLACE

```latex
\begin{table}[t]
\centering
\caption{The closest systems on the four axes this paper turns on, as each paper
reports them. Model in the clear says whether any party ends up holding the
trained model in plaintext, and \emph{provider} means one party does while the
querier does not. slytHErin and CryptPEFT serve a model they do not train, so
their rounds cell is empty.}
\label{tab:related}
\footnotesize
\setlength{\tabcolsep}{4pt}
\begin{tabular}{lcccc}
\toprule
System & Rounds & Protection & \shortstack{Model in\\the clear} & \shortstack{Querier\\receives} \\
\midrule
DENSE~\cite{zhang2022dense}          & one  & none & yes      & the model \\
GH-OFL~\cite{turazza2026ghofl}       & one  & none & yes      & the model \\
FedAUXfdp~\cite{hoech2022fedauxfdp}  & one  & DP   & yes      & the model \\
POSEIDON~\cite{sav2021poseidon}      & many & HE   & yes      & the model \\
slytHErin~\cite{intoci2023slytherin} &      & HE   & no       & scores \\
CryptPEFT~\cite{xia2026cryptpeft}    &      & 2PC  & provider & label \\
\midrule
HE-OFT                               & one  & HE   & no       & label \\
\bottomrule
\end{tabular}
\end{table}

\medskip
\noindent\emph{Positioning.}
\Cref{tab:related} places the closest systems on the axes that separate them. The
multi-round cryptographic line protects every round but pays on every round, and
what it protects is a per-round sum. The one-shot line exposes its single
contribution in plaintext, or noises it and pays in accuracy. The fine-tuning line
communicates a small object but protects nothing. Every one of them ends by
handing the finished model to the participants, so the model itself remains a
disclosed artifact. A single prior scheme is at once one-shot, federated and
encrypted, but only for a single-layer closed-form learner that cannot adapt a deep
representation~\cite{fedheonn2023}. What remains unaddressed is a protocol that
exposes no training-time quantity, that exchanges anything at all only once, and
that never discloses the model even to the parties that built it. \Cref{sec:method}
works out what that forces, and the rest of the paper measures what it costs.
```

---

## If the PIs want more

Three further cuts are available in this section and were not taken, because each
drops something a reviewer might want.

1. **The encrypted-maximum paragraph, B13, about 60 words.** It concedes that
   faster constructions exist than the one we measure. Cutting it makes the cost
   section look less honest.
2. **The first paragraph of 2.5, about 75 words after B10.** It says we compose
   with the secure-inference literature rather than compete with it. Cutting it
   invites the reviewer question it answers.
3. **The CryptPEFT paragraph, about 90 words after B12.** It is an NDSS 2026 paper
   that arrived at our serving architecture independently, which is the strongest
   external support the design has. I would keep it.

Together those are about 225 more words, half a column.
