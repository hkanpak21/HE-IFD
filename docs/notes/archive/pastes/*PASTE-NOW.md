# Paste this, top to bottom

Every block below was checked against the exact text you have in Overleaf right
now. Each FIND string occurs once and only once in the file named above it.

Work top to bottom. Do not skip a part, and do not reorder.

## Why there is more here than you expected

I made two mistakes and this file corrects both.

The paste order I gave you said the round of 2026-08-19 was already in the
manuscript. It was not. That round held the abstract rewrite and 51 punctuation
edits, and none of it ever reached Overleaf. I asserted it rather than checking.

Then when you sent the folder back this morning I said it was byte perfect. The
directory I compared it against had been cleared overnight, `diff` failed
silently, and I read the empty output as a match. It was not a match.

What you pasted yesterday is correct and complete for the round it covered.
Parts 1 and 2 below are the earlier round that was missed. Parts 3 and 4 are the
new work.

One thing you did that I had not asked for is right and I have kept it: adding
`sheller2020federated` to `refs.bib`. The citation pass needed it.

---

# Part 1. The abstract, one block

`main.tex`. Four things are wrong in the current version. It claims to be the
first one-shot federated fine-tuning protocol, which the federated adapter line
contradicts. It says the accuracy charge is $0.04$ when the record says $0.03$.
It says $5$ MiB per query, measured at a ring degree the serving path does not
use, where the real figure is $13.5$ MiB. And it carries a semicolon and a
colon.

FIND

```latex
permitted where the model is itself a regulated or proprietary asset. Multi-round
encrypted training also withholds the model, but it pays a cryptographic cost on
every round and cannot adapt a pretrained backbone. We present HE-OFT, the first one-shot federated fine-tuning protocol, where the resulting final model is
never disclosed to any party.
Each client fine-tunes a low-rank adapter and a classifier head on a
frozen public backbone, retains the adapter locally, and uploads one encrypted
head displacement; the server combines these under multiparty CKKS and never
decrypts the result. Queries are answered under encryption, and a quorum of
clients returns only the predicted label, addressed to the party that asked. Across four text classification tasks and one vision task, HE-OFT costs $0.04$ to $0.14$ accuracy against a disclosed model, and $5$\,MiB of traffic per query.
```

REPLACE

```latex
permitted where the model is itself a regulated or proprietary asset. Multi-round
encrypted training also withholds the model, but it pays a cryptographic cost on
every round and cannot adapt a pretrained backbone. We present HE-OFT, the first
cryptographically secure one-shot federated fine-tuning protocol, in which the
final model is never disclosed to any party.
Each client fine-tunes a low-rank adapter and a classifier head on a
frozen public backbone, retains the adapter locally, and uploads one encrypted
head displacement. The server combines these under multiparty CKKS and never
decrypts the result. Queries are answered under encryption, and a quorum of
clients returns only the predicted label, addressed to the party that asked. Across four text classification tasks and one vision task, HE-OFT reaches $0.61$ to $0.79$ accuracy where a client training alone reaches $0.20$ to $0.48$, and it gives up $0.03$ to $0.14$ against a disclosed model. One query costs $31.5$\,s at four classes and $113.2$\,s at a hundred, and $13.5$\,MiB of traffic.
```

Also in `main.tex`, one colon in the opening sentence.

FIND

```latex
 Federated learning offers collaboration but concentrates its privacy risk at training time: gradients
```

REPLACE

```latex
Federated learning offers collaboration but concentrates its privacy risk at training time. Gradients
```

---

# Part 2. The punctuation pass, 38 blocks

Every one removes a colon that introduces an explanation, or a semicolon joining
two sentences. Nothing else changes. No claim, number or citation moves.

These are grouped by file. Inside a file the order does not matter.


## `sections/intro.tex` — 3 edits

### intro.1

FIND

```latex
updates instead of data, but the updates are themselves the vulnerability: A
```

REPLACE

```latex
updates instead of data, but the updates are themselves the vulnerability. A
```

### intro.2

FIND

```latex
outright~\cite{boenisch2023curious,fowl2022robbing}. Two things therefore set the attack surface: what a protocol reveals while training
runs, and how often it reveals it.
```

REPLACE

```latex
outright~\cite{boenisch2023curious,fowl2022robbing}. Two things therefore set the attack surface, namely what a protocol reveals while
training runs and how often it reveals it.
```

### intro.3

FIND

```latex
circuit~\cite{sav2021poseidon,xu2022hercules,pirillo2025reboot}. That cost scales with the network being trained: POSEIDON trains a three-layer
```

REPLACE

```latex
circuit~\cite{sav2021poseidon,xu2022hercules,pirillo2025reboot}. That cost scales with the network being trained. POSEIDON trains a three-layer
```


## `sections/method.tex` — 15 edits

### method.1

FIND

```latex
The three contributions of this paper follow from these constraints: a partition of the
```

REPLACE

```latex
The three contributions of this paper follow from these constraints, a partition of the
```

### method.2

FIND

```latex
used below: a key switch to a designated public key, which re-encrypts a result so
that one chosen party can read it, and a collective refresh, which restores a
depleted level budget and plays the role bootstrapping plays in the single-key
setting.
```

REPLACE

```latex
used below. The first is a key switch to a designated public key, which re-encrypts
a result so that one chosen party can read it. The second is a collective refresh,
which restores a depleted level budget and plays the role bootstrapping plays in
the single-key setting.
```

### method.3

FIND

```latex
$\featx$, and trains two things on its own data: a low-rank adapter $A_j$ that
```

REPLACE

```latex
$\featx$, and trains two things on its own data, a low-rank adapter $A_j$ that
```

### method.4

FIND

```latex
where sharing is necessary. The distinction follows from coverage: a client
```

REPLACE

```latex
where sharing is necessary. The distinction follows from coverage. A client
```

### method.5

FIND

```latex
  \State \textbf{keep} $A_j$; it is never transmitted
```

REPLACE

```latex
  \State \textbf{keep} $A_j$, which is never transmitted
```

### method.6

FIND

```latex
them because features are invertible: a party holding $\varphi_j(x)$ and the public
```

REPLACE

```latex
them because features are invertible. A party holding $\varphi_j(x)$ and the public
```

### method.7

FIND

```latex
dimension~\cite{tramer2016stealing}. This is not a hypothetical concern: the same
```

REPLACE

```latex
dimension~\cite{tramer2016stealing}. This is not a hypothetical concern. The same
```

### method.8

FIND

```latex
result. None of this is particular to the multiparty setting: homomorphic
```

REPLACE

```latex
result. None of this is particular to the multiparty setting. Homomorphic
```

### method.9

FIND

```latex
re-solve it. One difference should be noted: those systems evaluate a plaintext
```

REPLACE

```latex
re-solve it. One difference should be noted. Those systems evaluate a plaintext
```

### method.10

FIND

```latex
\paragraph{The construction} Two arrangements are servable at the same cost: the
```

REPLACE

```latex
\paragraph{The construction} Two arrangements are servable at the same cost, the
```

### method.11

FIND

```latex
one value is decrypted: which arrangement the federation adopts.
```

REPLACE

```latex
one value is decrypted, which arrangement the federation adopts.
```

### method.12

FIND

```latex
measured alternative. There is no fitted threshold anywhere: the rule compares two
```

REPLACE

```latex
measured alternative. There is no fitted threshold anywhere. The rule compares two
```

### method.13

FIND

```latex
The per-client per-class accuracies are not decrypted, and must not be: together
```

REPLACE

```latex
The per-client per-class accuracies are not decrypted, and must not be. Together
```

### method.14

FIND

```latex
honest-but-curious: they follow the protocol and may try to infer private
```

REPLACE

```latex
honest-but-curious. They follow the protocol and may try to infer private
```

### method.15

FIND

```latex
\cref{sec:scope}; we do not evaluate it, and the accuracy figures we report assume
```

REPLACE

```latex
\cref{sec:scope}. We do not evaluate it, and the accuracy figures we report assume
```


## `sections/experiments.tex` — 17 edits

### experiments.1

FIND

```latex
that tests it, and reports the result. The claims are, in order: that a federated
head over private representations is a usable model; that its accuracy is
competitive with one-shot federated learning on that literature's own partition;
that the federation can choose between arrangements without decrypting either;
that the cryptographic layer is affordable, including the traffic that recurs; and
```

REPLACE

```latex
that tests it, and reports the result. The claims are, in order, that a federated
head over private representations is a usable model, that its accuracy is
competitive with one-shot federated learning on that literature's own partition,
that the federation can choose between arrangements without decrypting either,
that the cryptographic layer is affordable, including the traffic that recurs, and
```

### experiments.2

FIND

```latex
never transmitted; the head displacement is encrypted and uploaded once. No
```

REPLACE

```latex
never transmitted. The head displacement is encrypted and uploaded once. No
```

### experiments.3

FIND

```latex
adapter wins, and on Banking77 it wins decisively: the shared head collapses to
```

REPLACE

```latex
adapter wins, and on Banking77 it wins decisively. The shared head collapses to
```

### experiments.4

FIND

```latex
coverage: the personal adapter is preferable once each client sees enough of the
```

REPLACE

```latex
coverage. The personal adapter is preferable once each client sees enough of the
```

### experiments.5

FIND

```latex
Banking77, where choosing wrongly costs $0.48$; the estimator selects correctly on
```

REPLACE

```latex
Banking77, where choosing wrongly costs $0.48$. The estimator selects correctly on
```

### experiments.6

FIND

```latex
accuracies are not decrypted, which matters: together with the count matrix they
```

REPLACE

```latex
accuracies are not decrypted, and this matters. Together with the count matrix they
```

### experiments.7

FIND

```latex
are single-run wall clock on a commodity CPU and are reported as indicative;
communication figures are exact.
```

REPLACE

```latex
are single-run wall clock on a commodity CPU and are reported as indicative.
Communication figures are exact.
```

### experiments.8

FIND

```latex
Neither is the cost of a query: the encrypted argmax between them takes $31$\,s at
```

REPLACE

```latex
Neither is the cost of a query. The encrypted argmax between them takes $31$\,s at
```

### experiments.9

FIND

```latex
gives our figures: $39.0$, $82.5$ and $174.9$\,ms for a ciphertext-by-ciphertext
```

REPLACE

```latex
gives our figures, $39.0$, $82.5$ and $174.9$\,ms for a ciphertext-by-ciphertext
```

### experiments.10

FIND

```latex
encrypted argmax is exact: over label spaces from four to a hundred classes it
```

REPLACE

```latex
encrypted argmax is exact. Over label spaces from four to a hundred classes it
```

### experiments.11

FIND

```latex
\caption{Label-only extraction of the served head: mean fidelity over three seeds
```

REPLACE

```latex
\caption{Label-only extraction of the served head. Mean fidelity over three seeds
```

### experiments.12

FIND

```latex
the task: the head has $\Cc d$ parameters, and in each case fidelity $0.90$ costs
```

REPLACE

```latex
the task. The head has $\Cc d$ parameters, and in each case fidelity $0.90$ costs
```

### experiments.13

FIND

```latex
labels would be nearly as generous: the head is linear in features the client
```

REPLACE

```latex
labels would be nearly as generous. The head is linear in features the client
```

### experiments.14

FIND

```latex
can substitute for: after the protocol ends, there is no plaintext model anywhere.
```

REPLACE

```latex
can substitute for. After the protocol ends, there is no plaintext model anywhere.
```

### experiments.15

FIND

```latex
cost; we do not attempt it here.
```

REPLACE

```latex
cost, and we do not attempt it here.
```

### experiments.16

FIND

```latex
without modification, and it is orthogonal to it: the protocol protects the
```

REPLACE

```latex
without modification, and it is orthogonal to it. The protocol protects the
```

### experiments.17

FIND

```latex
future work: an upload-time norm bound enforced by a zero-knowledge proof, which
```

REPLACE

```latex
future work, an upload-time norm bound enforced by a zero-knowledge proof, which
```


## `sections/conclusion.tex` — 3 edits

### conclusion.1

FIND

```latex
multiparty CKKS and never decrypts the result; queries are answered under
```

REPLACE

```latex
multiparty CKKS and never decrypts the result. Queries are answered under
```

### conclusion.2

FIND

```latex
nonlinearity of the network. This is the source of the design's three parts: the
```

REPLACE

```latex
nonlinearity of the network. This is the source of the design's three parts, the
```

### conclusion.3

FIND

```latex
contribution remains open; an upload-time norm bound enforced by a zero-knowledge
```

REPLACE

```latex
contribution remains open. An upload-time norm bound enforced by a zero-knowledge
```


---

# Part 3. The three open PI comments, 6 blocks

Küpçü, 11 August 7:12 pm and 7:14 pm, and 12 August 10:47 am. Blocks 1 to 4 go
into `intro.tex` and blocks 5 and 6 into `method.tex`.

**Blocks 4 and 5 are one move.** Block 4 adds the figure to the introduction and
block 5 removes it from the method. Do both or Figure 1 is duplicated or lost.

Block 3 also corrects a claim about POSEIDON that is false, and it has to travel
with these because it sits in the paragraph they pass through.


### 1. intro.tex, the signpost so three problems read as three

FIND

```latex
infrastructure raises the same objection~\cite{xiao2023offsite}.
```

REPLACE

```latex
infrastructure raises the same objection~\cite{xiao2023offsite}. Three obstacles
stand between that setting and a protocol these organizations could deploy.
```

### 2. intro.tex, the paragraph opens on a requirement not a fix

FIND

```latex
Two measures remove that surface together. Making the protocol \emph{one-shot}
```

REPLACE

```latex
Removing that surface takes two measures together. Making the protocol \emph{one-shot}
```

### 3. intro.tex, the POSEIDON claim, which is false as written

FIND

```latex
Applying both measures (encrypted, one-shot training) still leaves one artifact exposed, namely the model itself.
Every protocol above ends by handing the final decrypted model to the participants, which is
unacceptable when the model may not be distributed at all.
```

REPLACE

```latex
Applying both measures still leaves one artifact exposed, namely the model itself.
One-shot protocols end by handing the final model to every participant, which is
unacceptable when the model may not be distributed at all. Encrypted training does
withhold it, but the cost just described puts a pretrained backbone out of reach.
```

### 4. intro.tex, the overview paragraph, and Figure 1 moves here

FIND

```latex
The querier must build its query from parts it can run itself, so those parts must
```

REPLACE

```latex
\input{figures/training}

\Cref{fig:training} shows how the shared head is built. Every client fine-tunes an
adapter and a classifier head on the same frozen public backbone, keeps the
adapter, and uploads one encrypted head displacement weighted by the classes it
holds. The server adds the ciphertexts and divides by the per-class totals under
encryption, so the shared head exists only as a ciphertext and the server holds no
key to it. A client that wants a prediction computes the features of its query
itself, encrypts them, and sends them to the serving party, which applies the
encrypted head and takes the argmax under encryption. A quorum of clients then
switches the result to that client alone, which decrypts one label.

The querier must build its query from parts it can run itself, so those parts must
```

### 5. method.tex, remove the figure input, the other half of block 4

FIND

```latex
\input{figures/training}

\paragraph{The construction} Each client uses the same frozen public backbone
```

REPLACE

```latex
\paragraph{The construction} Each client uses the same frozen public backbone
```

### 6. method.tex, say what to look at in the figure

FIND

```latex
The adapter is trained locally and never transmitted. \Cref{fig:training} shows
the arrangement.
```

REPLACE

```latex
The adapter is trained locally and never transmitted. In \cref{fig:training} the
adapters stay inside the client boxes, only the head displacement crosses to the
server, and the arrow that would carry an adapter aggregate does not exist.
```

---

# Part 4. The vocabulary pass, 8 blocks

Encryption gives confidentiality, of the contribution, the head and the query.
The threat model is about privacy, of the training data. One word was doing both
jobs, and a third: `privately` where the plain word is `locally`. Nothing makes
the adapter private, it is simply never transmitted.

The first block is the one that matters. The other seven are accuracy.


### 1. `method.tex`

Theorem 2 bounds what a malicious coalition learns by a negligible term plus a
measured one, and the paper says the measured term rests on metering queries. So
Section IV says privacy is not cryptographic while Section III says it is. This
also removes the colon.

FIND

```latex
exchange. (2) Privacy is \emph{cryptographic}: a client's contribution is never
```

REPLACE

```latex
exchange. (2) Confidentiality is \emph{cryptographic}. A client's contribution is never
```

### 2. `experiments.tex`

FIND

```latex
head over private representations is a usable model
```

REPLACE

```latex
head over local representations is a usable model
```

### 3. `experiments.tex`

FIND

```latex
each client adapts privately, yields a model usable across the whole label space,
```

REPLACE

```latex
each client adapts locally, yields a model usable across the whole label space,
```

### 4. `experiments.tex`

FIND

```latex
each client the shared head over its own privately adapted representation.
```

REPLACE

```latex
each client the shared head over its own locally adapted representation.
```

### 5. `experiments.tex`

FIND

```latex
with. A privately adapted representation improves separability for every class the
```

REPLACE

```latex
with. A locally adapted representation improves separability for every class the
```

### 6. `experiments.tex`

FIND

```latex
\cref{tab:headline} shows on the small label spaces what a privately adapted
```

REPLACE

```latex
\cref{tab:headline} shows on the small label spaces what a locally adapted
```

### 7. `experiments.tex`

FIND

```latex
accuracy each method gives up for its privacy mechanism, since every paper measures
```

REPLACE

```latex
accuracy each method gives up for protecting the contribution, since every paper measures
```

### 8. `experiments.tex`

FIND

```latex
DENSE and FedDF report no accuracy cost for privacy, because neither sets out to
protect the contribution.
```

REPLACE

```latex
DENSE and FedDF report no such cost, because neither sets out to protect the
contribution.
```

---

# When you are done

Recompile and tell me three things: the number of undefined citations, the page
count, and which page Figure 1 lands on. If anything looks wrong, send the log.

