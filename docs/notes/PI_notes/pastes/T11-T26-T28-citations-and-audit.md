# T11, T26, T28. Citations and mechanical audit

Prepared 2026-08-20. Nothing under `docs/paper/` was edited. Every block below is
a find and replace pair for Overleaf.

Every citation proposed here was checked against the source. The line after each
proposal says which page was opened and what it says. A reviewer can confirm each
one without opening the manuscript.

Line numbers are against the local copy of 2026-08-20 and are approximate. Match
on the quoted text, not on the number.

---

# Part 1. T11. The two uncited sentences in the introduction

Küpçü, 11 August, 3:29 pm and 3:30 pm.

Both fixes are a citation added to the end of an existing clause. No sentence is
rewritten.

## 1a. "each would obtain a better model from the combination than from its own data alone"

`docs/paper/sections/intro.tex`, line 7 to 8.

One new bibliography entry is needed. `refs.bib` was searched first. The three
candidates already in the file were rejected, see "Why not an existing key"
below.

FIND

```
model from the combination than from its own data alone. They cannot pool that data, because data protection law restricts the sharing of
```

REPLACE

```
model from the combination than from its own data alone~\cite{sheller2020federated}. They cannot pool that data, because data protection law restricts the sharing of
```

**Source checked.** Sheller et al., Scientific Reports 10:12598, 2020, read on
PubMed Central PMC7387485. Results section, verbatim: "Notably, averaging over
institutions, the CDS model performance is 3.17% greater than the single
institution models on their own validation data, and for FL the increase is
2.63%". The same section states the purpose of that comparison verbatim: "we
compare models over the single institutions' local held-out validation sets ...
to determine whether a given institution can improve performance on its own data
by collaborating." That is the claim, measured, over ten institutions, and each
institution is compared against its own data alone rather than against a pooled
model.

**New bibliography entry**, in the checklist's form. No url, no doi, no note,
journal with volume and pages. Author list read from the PMC author block.

```bibtex
@article{sheller2020federated,
  title   = {Federated learning in medicine: facilitating multi-institutional collaborations without sharing patient data},
  author  = {Sheller, Micah J. and Edwards, Brandon and Reina, G. Anthony and Martin, Jason and Pati, Sarthak and Kotrotsou, Aikaterini and Milchenko, Mikhail and Xu, Weilin and Marcus, Daniel and Colen, Rivka R. and Bakas, Spyridon},
  journal = {Scientific Reports},
  volume  = {10},
  pages   = {12598},
  year    = {2020}}
```

**Why not an existing key.**

- `rieke2020future`. npj Digital Medicine. A review, and Küpçü asked for a source
  that measures the gain rather than asserts it.
- `yang2019federated`. ACM TIST. A concept and applications survey. No
  measurement of the local-only baseline.
- `li2022niidbench`. Checked, because a benchmark with a local-only baseline
  would have been the ideal fit. The arXiv text of "Federated Learning on Non-IID
  Data Silos" was searched and contains no local-only or SOLO baseline. It
  compares FedAvg, FedProx, SCAFFOLD and FedNova against each other. It does not
  support this claim and must not be used for it.
- `hsu2019measuring`. Measures the effect of non-identical distributions, not the
  gain over training alone.

**Note for the PIs.** \Cref{tab:headline} measures the same thing on our own
tasks. The best servable arrangement beats the alone column on all five rows,
$0.649$ against $0.475$, $0.607$ against $0.400$, $0.789$ against $0.451$,
$0.686$ against $0.249$ and $0.774$ against $0.197$. If a second support is ever
wanted, a cross-reference to that table is available at no page cost. One
citation is proposed here because the introduction should not forward-reference
Section 5 for a premise.

## 1b. "its privacy risk is concentrated at training time"

`docs/paper/sections/intro.tex`, line 13 to 14. Both keys are already in
`refs.bib`.

FIND

```
and its privacy risk is concentrated at training time. The protocol exchanges model
```

REPLACE

```
and its privacy risk is concentrated at training time~\cite{nasr2019comprehensive,melis2019exploiting}. The protocol exchanges model
```

**Sources checked.**

- `nasr2019comprehensive`. Nasr, Shokri and Houmansadr, IEEE S&P 2019, abstract
  read on arXiv 1812.00910. Verbatim: "We measure the privacy leakage through
  parameters of fully trained models as well as the parameter updates of models
  during training." This is the one cited work that measures both sides, so it is
  the source that supports the word "concentrated", which is a comparison and not
  an assertion that the final model is safe. The measured gap it reports is
  already quoted seven lines further down.
- `melis2019exploiting`. Melis, Song, De Cristofaro and Shmatikov, IEEE S&P 2019,
  abstract read on arXiv 1805.04049. Verbatim: "We demonstrate that these updates
  leak unintended information about participants' training data and develop
  passive and active inference attacks to exploit this leakage", where "these
  updates" are the model updates exchanged periodically during training. It
  establishes that the exchanged object, not the trained model, is what leaks.

**Not used.** `kairouz2021advances` already sits on the first half of the same
sentence, and `related.tex` line 32 already uses it for the adversary taxonomy,
so adding it again here would carry no new support. `carletti2025sok` would suit
the claim as a survey but the USENIX page returns 403 and the abstract could not
be read, so it is left out under the no-unverified-citation rule.

---

# Part 2. T26. Section 5.6 and the extraction literature

## 2.1. Which published attack matches our interface

Our interface is a multiclass linear map, $\Cc \ge 4$, applied to features the
client computes itself, returning $\arg\max_i (w_i \cdot \varphi(x) + b_i)$, one
label per query, under a per-client allowance, with the weights held under
encryption.

**The match is Tramèr et al., USENIX Security 2016, Section 6.2.** Read from the
paper PDF. Three verbatim sentences establish it.

1. The model class and the answer format are ours exactly. "We focus on softmax
   models here, as softmax and one-vs-rest models have identical output behaviors
   when only class labels are provided: in both cases, the class label for an
   input x is given by argmax_i(w_i · x + β_i)."
2. Their query budget is normalised the way ours is. "We again vary the query
   budget as a factor α of the number of model parameters, namely α · c · (d +
   1)."
3. They report a cost at that normalisation. "For all models, 100 · c · (d + 1)
   queries resulted in extraction accuracy above 99.9%. This represents 26,000
   queries on average, and 65,000 at the most".

Since a softmax model with a bias has exactly $c(d+1)$ parameters, their figure
is 100 queries per parameter. Ours is 3.4 to 4.6 per parameter for fidelity
$0.90$ and 9.2 to 10.5 for $0.95$, re-derived below. The two agree once the
fidelity target is matched, which is the comparison worth printing.

**What was checked and rejected.**

- `lowdmeek2005`, currently uncited. Tramèr et al. describe it verbatim as an
  attack "on any linear classifier, assuming black-box oracle access with
  membership queries that return just the predicted class label", which is our
  answer format, but they also state verbatim that "This attack only works for
  linear binary models" and "The Lowd-Meek attack is not applicable in multiclass
  (c > 2) settings, even when the decision boundary is a combination of linear
  boundaries". Our smallest label space is $\Cc = 4$. **Do not cite it as though
  it covered our head.** Leave it uncited, or cite it only beside Tramèr as the
  binary ancestor.
- `chen2024hardlabel`. Abstract read on ePrint 2024/1403. It targets "ReLU neural
  networks" and reports wall-clock time, "for a neural network consisting of
  $10^5$ parameters, our attack only requires several hours on a single core",
  not a query count. No comparable query figure.
- `carlini2025hardlabel`. Abstract read on ePrint 2024/1580. It targets
  ReLU-based deep networks, demonstrated on "832 neurons in four hidden layers",
  and claims "a polynomial number of queries" without a constant we could place
  beside ours. No comparable query figure.
  Both are already cited at the right place, `method.tex` line 259, for the claim
  that hard-label extraction of a general network is recent and hard. Adding them
  to Section 5.6 would suggest our single linear layer inherits their difficulty,
  which `docs/notes/extraction-attack.md` explicitly warns against. **Recommend
  no change there.**
- Otto, Kurtz, den Hertog and Birbil, "Linear Model Extraction via Factual and
  Counterfactual Queries", arXiv 2602.09748, 2026. Checked because it is recent
  and about linear models. Its interface is counterfactual queries, and its
  headline result is that "the full model can be recovered using just a single
  counterfactual query when differentiable distance measures are employed". Our
  protocol returns an index and nothing else, so the interface does not match.
  **Rejected. Do not cite.**
- A search for a 2024 to 2026 hard-label extraction paper reporting a per-parameter
  query cost for a linear or last-layer map returned nothing usable. The recent
  hard-label line is cryptanalytic and aimed at deep ReLU networks.
  **This is left open.** If the PIs know of one, it belongs at site 2.2 below.

## 2.2. Where the citation belongs, and what it supports

### Site A. The per-parameter rule. Highest value

`docs/paper/sections/experiments.tex`, line 589 to 590. This is the sentence the
meeting asked for, a published query cost beside our own.

FIND

```
allowance from $\Cc$ and $d$ without repeating this experiment.
```

REPLACE

```
allowance from $\Cc$ and $d$ without repeating this experiment. A published
measurement of the same interface agrees. Extracting a softmax model from class
labels alone costs $100$ queries per parameter for agreement above $99.9$ per
cent~\cite{tramer2016stealing}, and the curve here reaches $0.993$ at $65$
queries per parameter on AG-News.
```

**Source checked.** Tramèr, Zhang, Juels, Reiter and Ristenpart, USENIX Security
2016, Section 6.2, verbatim: "For all models, 100 · c · (d + 1) queries resulted
in extraction accuracy above 99.9%." A softmax model with a bias has $c(d+1)$
parameters, so that is 100 queries per parameter.

**Our number checked.** `results/extraction_budget/results.csv`, `random`
strategy, mean over three seeds and both arrangements. AG-News, $\Cc d = 3072$,
$2\times10^5$ queries gives fidelity $0.9928$, and $2\times10^5 / 3072 = 65.1$.
The value $0.993$ is already printed in \cref{tab:extract}, so this adds no new
number to the paper.

**The rest of Section 5.6 was re-derived from the same record and it is correct.**
Fidelity $0.90$ costs $3.8\times$ the parameter count on AG-News, $4.6\times$ on
DBpedia and $3.4\times$ on Banking77, so "between three and five times" holds.
Fidelity $0.80$ costs $1.3$, $1.8$ and $1.2$ times, so "roughly $1.5$ times"
holds. Fidelity $0.95$ costs $9.2$ and $10.5$ times on AG-News and DBpedia and is
not reached on Banking77 within $2\times10^5$, so "roughly ten times" holds.

### Site B. The boundary-search paragraph. Currently cites nothing

`docs/paper/sections/experiments.tex`, line 616 to 617. Our own finding has a
published precedent with the same explanation, and saying so costs one clause.

FIND

```
gains less from them than from the same number of independent ones. The two
```

REPLACE

```
gains less from them than from the same number of independent ones. A published
multiclass measurement reports the same ordering, where a line search does not
improve on uniform queries, and suggests the same reason, that the searches split
across several decision boundaries~\cite{tramer2016stealing}. The two
```

**Source checked.** Tramèr et al., Section 6.2, verbatim: "We observe that the
adaptive strategy clearly performs best and that the line-search strategy does not
improve over uniform retraining, possibly because the line-searches have to be
split across multiple decision-boundaries." Their hedge is "possibly", which is
why the replacement says "suggests the same reason" rather than attributing it.

**Our number checked while here, and it is right.**
`results/extraction_budget/results.csv`, Banking77 at $5\times10^4$ queries,
`boundary` gives $0.6755$ and `random` gives $0.7546$, so the printed "$0.675$
against $0.755$" is correct. Over the five budgets in \cref{tab:extract} and the
three tasks, `boundary` loses in 13 of 15 cells, and the two exceptions are
AG-News at the two largest budgets, which is what the paragraph says.

### Site C. Optional, only if the PIs want the vocabulary named

`experiments.tex` line 551 to 554 already explains that a label denies the linear
solve, and `method.tex` line 250 already carries `tramer2016stealing` for that.
Adding it a second time in Section 5.6 would be a duplicate. **No change
proposed.**

---

# Part 3. T28. The two mechanical audits

## 3a. Abbreviations at first use

Reading order is `main.tex`, then intro, related, method, security, experiments,
conclusion. Comment lines, the preamble, the colour definitions, the
acknowledgement and the author biographies are excluded, since none of them is
body text. Line numbers are local as of 2026-08-20.

| abbreviation | first use | defined there | action |
|---|---|---|---|
| HE-OFT | main.tex:118, abstract | no, and neither HE nor OFT is expanded anywhere | see note 1 |
| CKKS | main.tex:122, abstract | no in the abstract, yes at intro:63 | see note 2 |
| FL | intro:13 | **yes**, "Federated learning (FL)" | none |
| ViT | intro:99 | **no** | **fix, see below** |
| POSEIDON | intro:42 | product name, cited | none |
| RoBERTa | intro:99 | model name, cited | none |
| LoRA | related:71, inside "SHE-LoRA" | no | see note 3 |
| GPUs, GPU | related:171, experiments:402 | no | none, IEEE treats it as a word |
| IND-CPA | security:117 | **no** | **fix, see below** |
| CPU | experiments:347 | no | none, IEEE treats it as a word |
| RNS | experiments:396 | **no** | **fix, see below** |
| CUDA | experiments:461 | product name | none |
| MiB | main.tex:124 | no | none, IEC unit |
| FedML-HE, FedSHE, SHE-LoRA, HETAL, FedAUXfdp, FedIT, FLoRA, FlexLoRA, HetLoRA, FedSA-LoRA, FFA-LoRA, slytHErin, CryptPEFT, DENSE, FedDF | related and experiments | system names from the cited papers | none |
| AG-News, TREC, DBpedia, Banking77, CIFAR-10, CIFAR-100 | experiments:25 to 171 | dataset names | none |

Three real defects. Each is fixed by an inserted phrase, not a rewrite.

### ViT

`docs/paper/sections/intro.tex`, line 99.

FIND

```
frozen RoBERTa~\cite{liu2019roberta} and ViT~\cite{dosovitskiy2021vit} backbones,
```

REPLACE

```
frozen RoBERTa~\cite{liu2019roberta} and vision transformer (ViT)~\cite{dosovitskiy2021vit} backbones,
```

### IND-CPA

`docs/paper/sections/security.tex`, line 117. This is the first of five uses.

FIND

```
Assume the $\tc$-out-of-$\Nc$ threshold CKKS scheme is IND-CPA secure against an
```

REPLACE

```
Assume the $\tc$-out-of-$\Nc$ threshold CKKS scheme is secure under chosen
plaintext attack (IND-CPA) against an
```

### RNS

`docs/paper/sections/experiments.tex`, line 396. Used once, so expanding it in
place is enough.

FIND

```
instead, across the residue moduli of the RNS decomposition, and our
```

REPLACE

```
instead, across the residue moduli of the residue number system decomposition, and our
```

### Notes

1. **HE-OFT.** The title, "HE-OFT: Privacy-Preserving One-Shot Federated
   Fine-Tuning under Homomorphic Encryption", glosses both halves in the reader's
   line of sight, and IEEE accepts a coined system name without a letter-by-letter
   expansion. **No change proposed.** Flagged because Küpçü may read it as an
   abbreviation. If he does, the fix is four words in the abstract.
2. **CKKS.** The body case is already handled at intro:63, "multiparty
   CKKS~\cite{cheon2017ckks,mouchet2021multiparty}, a homomorphic encryption
   scheme whose secret key is split across the parties". The abstract still uses
   the four letters bare at main.tex:122, and IEEE treats the abstract as
   standing alone. **No change proposed**, since the PIs have called this one
   closed, but it is recorded here so it is not rediscovered.
3. **LoRA.** The manuscript never uses "LoRA" on its own. It writes "low-rank
   adapter" in prose and the letters appear only inside the proper names of cited
   systems. A proper name does not require expansion. **No change proposed.**
   Recorded because the strict reading of checklist item 12 would flag it.

## 3b. Unbacked quantifiers and banned intensifiers

Checklist items 5 and 6. Every instance in the manuscript, with a verdict. The
mathematical "at most" in `security.tex` at lines 19, 97, 120, 197, 262 and 283
is excluded, as is "as many queries as", "how many shares" and the "majority"
column of \cref{tab:extract}, which is the majority-class baseline and a
technical term.

### Cannot be backed. A replacement is proposed

**B1. `experiments.tex:89`. "the federation accounts for most of the resulting accuracy"**

This is false on three of the five rows. Reading \cref{tab:headline}, the share of
the better servable arrangement's accuracy that a client does not already reach
alone is $0.174/0.649 = 27$ per cent on AG-News, $0.207/0.607 = 34$ per cent on
TREC, $0.338/0.789 = 43$ per cent on DBpedia, $0.437/0.686 = 64$ per cent on
Banking77 and $0.577/0.774 = 75$ per cent on CIFAR-100. A client alone already
holds more than half of the accuracy on three tasks. What the table does support
on every row is that the federation raises accuracy.

FIND

```
Three observations follow. First, the federation accounts for most of the
resulting accuracy. A client alone
```

REPLACE

```
Three observations follow. First, the federation raises accuracy on every task. A client alone
```

**B2. `conclusion.tex:30`. "is the most direct route"**

A superlative over routes the paper has not surveyed. One word fixes it.

FIND

```
proof is the most direct route.
```

REPLACE

```
proof is one route.
```

**B3. `experiments.tex:468`. "on which published figures are substantially better"**

Neither backed nor cited. The clause claims something about published figures and
names none. The smallest fix is to drop it.

FIND

```
GPU homomorphic-encryption libraries are tuned for current datacentre parts, on
which published figures are substantially better.
```

REPLACE

```
GPU homomorphic-encryption libraries are tuned for current datacentre parts.
```

**Adjacent finding, and it is larger than the word.** The four sentences before
this one carry a full microbenchmark, "a CUDA implementation of CKKS, at ring
degree $2^{16}$, put the product at $30$\,ms and the rotation at $29.5$\,ms", the
claim that those numbers sit at a deeper level budget than ours, and the claim
that they were taken on a mid-range inference card. **None of it carries a
citation.** `yang2024phantom` is in `refs.bib`, is a CUDA CKKS library, and is
cited nowhere in the manuscript, so it may be the intended source, but I could
not confirm that the three numbers come from it and will not guess. **Open. The
authors should name the source or drop the paragraph.**

**B4. `related.tex:94`. "Most are also single-party"**

Of the eight works the sentence covers, `privfedtl2026` and `alamin2025vit` are
federated by the manuscript's own description two sentences earlier, and
`li2024privtuner` and `frery2025private` are described there as running "between a
model owner and data owners", which is two parties. So at most four of the eight
can be single-party and "most" is not supported by the paragraph's own text. I did
not read all eight to settle it, so a hedge is safer than a count.

FIND

```
nonlinearity must be approximated. Most are also single-party, one data owner
```

REPLACE

```
nonlinearity must be approximated. Several are also single-party, one data owner
```

**B5. `experiments.tex:101`. "most head rows are decided by very few clients or none"**

No record under `results/` reports per-class coverage for this configuration.
`results/personal_adapter/stratified/` holds `results.csv` only, and no
`partition_diagnostic.jsonl` exists for the Banking77 run. The claim is plausible
and it is the stated mechanism for the collapse, but nothing in the paper or the
records backs the word "most", and "very" is banned outright.

FIND

```
failure. With $77$ classes and this skew most head rows are decided by very few
clients or none, and a head over the bare public backbone has nothing else to work
```

REPLACE

```
failure. With $77$ classes and this skew each head row is decided by few clients
or none, and a head over the bare public backbone has nothing else to work
```

If the PIs would rather keep the quantifier, the fix is a record. A short CPU job
that writes the per-class client counts for that cell would settle it, and the
count could then be printed.

**B6. `experiments.tex:651`. "Most of the distance"**

The two sentences before it give the numbers for four tasks and name DBpedia as
the exception, so the claim holds on three of four and the sentence generalises
past its own evidence. Four words fix it.

FIND

```
Banking77. DBpedia is the exception, at $0.063$ against $0.136$. Most of the
distance between a servable arrangement and a centralised model is therefore
attributable to the partition of the data, and not to the decision never to
decrypt.
```

REPLACE

```
Banking77. DBpedia is the exception, at $0.063$ against $0.136$. On those three
tasks most of the distance between a servable arrangement and a centralised model
is therefore attributable to the partition of the data, and not to the decision
never to decrypt.
```

### Banned intensifier, claim is backed. Deletion only

Checklist item 6 bans these words whether or not the claim holds. Each is a
deletion of one word and nothing else changes.

**B7. `intro.tex:37`.** `adds noise to the very artifact it releases.` becomes
`adds noise to the artifact it releases.`

**B8. `related.tex:131`.** `requires is added to the very artifact that is released, so accuracy falls as the`
becomes `requires is added to the artifact that is released, so accuracy falls as the`

**B9. `experiments.tex:283`.** `held-out set also contains only the classes that client holds, so the very`
becomes `held-out set also contains only the classes that client holds, so the`

**B10. `related.tex:35`.** `that generalise well it identifies few members, and only at very low false-positive`
becomes `that generalise well it identifies few members, and only at low false-positive`
Backed by `carlini2022membership`, which is the paper that argues for reporting
at low false-positive rates. "Low" survives, "very" does not.

**B11. `method.tex:47`.** `surface.} Each exposed round is a fresh training-time artifact, far more`
becomes `surface.} Each exposed round is a fresh training-time artifact, more`
Backed by the cross-reference to \cref{sec:related-leakage} and the Nasr
measurement quoted there. Same overclaim family as T12, so the two should be
decided together.

**B12. `conclusion.tex:22`.** `substantially stronger than any client obtains alone, at a cost of $0.03$ to`
becomes `stronger than any client obtains alone, at a cost of $0.03$ to`
Backed by \cref{tab:headline}, $0.61$ to $0.79$ against $0.20$ to $0.48$.

**B13. `method.tex:258`.** `equivalent extraction is markedly harder and has only recently been achieved for`
becomes `equivalent extraction is harder and has only recently been achieved for`
Backed by Section 5.6, $769$ queries with logits against $1.2\times10^4$ to
$2.0\times10^5$ with labels, and by the two cited papers.

### Under T12 already, listed for completeness

**B14. `main.tex:114`** and **`intro.tex:18`**, "substantially stronger than any
attack on the final model" and "far stronger than anything possible against the
final model". Both quantify over all attacks and neither can be backed. T12 owns
both and proposes binding them to the Nasr measurement. **No separate proposal
here**, so the two items do not collide in Overleaf.

### Checked and left alone

| site | text | why |
|---|---|---|
| `related.tex:58` | "In its most ambitious form" | describes one end of a range the paragraph sets out, not a claim about the world |
| `experiments.tex:402` | "where a GPU implementation helps most" | backed by the caption of \cref{tab:cost}, "The argmax is more than $99$ per cent of both" |
| `experiments.tex:598` and `:599` | "gain most from the federation", "meter queries most tightly" | backed by \cref{tab:headline}, the shared head wins by $0.17$ and $0.18$ on the two small label spaces, and by \cref{tab:extract}, where AG-News is the cheapest head to copy |
| `experiments.tex:270`, `:309`, `:567`, `:568`, `:574` | "majority" | the majority vote and the majority-class baseline, both technical terms |
| `related.tex:178` | "Most of these systems evaluate a plaintext model on encrypted inputs" | three systems are cited and I did not read all three, so I will not call it unbacked. If the authors confirm all three, "These systems" is the smallest fix. **Open** |
| `related.tex:87`, `:102`, `:107`, `experiments.tex:214`, `:400`, `:428`, `:542`, `:553`, `:616`, `method.tex:105`, `:250`, `intro.tex:38` | "many rounds", "many queries", "many real slots", "as many queries as" | plain counts, not quantifier claims |
| `experiments.tex:109` | "drifts far enough that" | a degree clause with its own threshold, not an intensifier |
| `related.tex:133` | "how much a released artifact can reveal" | a noun phrase, not a quantifier |
| `security.tex:19`, `:97`, `:120`, `:197`, `:262`, `:283` | "at most" | mathematical |

---

# What is still open

1. The CUDA microbenchmark in `experiments.tex` lines 461 to 464 has no citation
   for three numbers and two claims about the hardware. Named source needed, or
   the paragraph goes.
2. `related.tex:178`, "Most of these systems", needs the three cited systems
   checked before the word is kept or dropped.
3. `experiments.tex:101` needs a per-class coverage record if the PIs want the
   original quantifier back.
4. No 2024 to 2026 hard-label extraction paper was found that reports a
   per-parameter query cost for a linear or last-layer map. If one exists, it
   belongs at Site A in Part 2.
5. `carletti2025sok` could support T11b as a survey, but the USENIX page returns
   403 and the abstract was not read, so it is not proposed.
