# Overleaf paste list, 2026-08-19

One entry per change that is ready to go into Overleaf. Each entry says which
file, what to search for, and what to do. Paste the block inside the fenced
LaTeX, nothing else.

Entries are added here as items in `docs/plan/paper-todo-2026-08-19.md` are
accepted. Anything still marked PENDING below is waiting on a decision in that
file, so do not paste it yet.

Rules that every block here follows: no em dash, no en dash, no colon used to
introduce an explanation, no markdown bold, active voice.

## Status

| # | item | file | status |
|---|---|---|---|
| P1 | abstract, priority claim and paragraph break | `main.tex` | READY |
| P2 | Table II column header | `experiments.tex` | READY |
| P3 | capital letter after a colon | `intro.tex` | READY |
| P4 | differential privacy clause in the Setting | `method.tex` | READY |
| P5 | C6 reason clause | `method.tex` | READY |
| P6 | the membership inference claim, two sites | `main.tex`, `intro.tex` | PENDING T12 |

---

## P1. `main.tex`, the abstract

**Find** the abstract, which currently has a blank line in the middle of it and
ends its fourth sentence with "where the resulting final model is never
disclosed to any party."

**Replace the whole abstract body** with the block below. Two things change and
nothing else. The blank line before "We present HE-OFT" is gone, so the abstract
is one paragraph again. And the priority claim is now restrictive, so it says
first cryptographically secure one-shot federated fine-tuning rather than first
one-shot federated fine-tuning.

```latex
Organizations adapt large pretrained models to private data by fine-tuning, and parties
holding complementary data over the same task would each gain from a jointly
fine-tuned model, yet cannot pool their data to build one. Federated learning offers collaboration but concentrates its privacy risk at training time: gradients
and per-round updates permit reconstruction of training data and support
membership inference substantially stronger than any attack on the final model.
A one-shot protocol that exchanges a single encrypted contribution removes that surface,
but it still ends by handing the final model to every participant, which is not
permitted where the model is itself a regulated or proprietary asset. We present
HE-OFT, the first cryptographically secure one-shot federated fine-tuning protocol,
in which the final model is never disclosed to any party.
Each client fine-tunes a low-rank adapter and a classifier head on a
frozen public backbone, retains the adapter locally, and uploads one encrypted
head displacement; the server combines these under multiparty CKKS and never
decrypts the result. Queries are answered under encryption, and a quorum of
clients returns only the predicted label, addressed to the party that asked. The federation also chooses between two servable arrangements without decrypting either. Across four text classification tasks and one vision task, HE-OFT costs $0.04$ to $0.14$ accuracy against a disclosed model, and $5$\,MiB of traffic per query.
```

Why the comma matters. Without the restrictive "in which", the sentence claims
we are the first one-shot federated fine-tuning protocol of any kind. The
federated adapter line already holds that ground. With it, the claim is about
the class we can defend.

---

## P2. `experiments.tex`, Table II header

**Find** the header row of Table II:

```latex
Task & $\Cc$ & shared head & adapter & alone & disclosed & pooled \\
```

**Replace with:**

```latex
Task & $\Cc$ & shared head & personal adapter & alone & disclosed & pooled \\
```

Ten sentences in the body call this arrangement the personal adapter, and one
name per thing is a checklist rule. If the column is too narrow at that width,
tell me and I will rename the arrangement everywhere instead, which is ten
edits rather than one.

---

## P3. `intro.tex`, capital letter after a colon

**Find:**

```latex
updates instead of data, but the updates are themselves the vulnerability: A
gradient permits reconstruction of the batch that produced
```

**Replace with:**

```latex
updates instead of data, but the updates are themselves the vulnerability. A
gradient permits reconstruction of the batch that produced
```

The colon introduced an explanation, which is one of the patterns we are
removing, and it left a capital letter mid-sentence.

---

## P4. `method.tex`, the Setting, the differential privacy clause

**Find:**

```latex
available in plaintext to any other party, and we do not consider differential privacy due to the accuracy loss incurred. (3) The resulting model is
```

**Replace with:**

```latex
available in plaintext to any other party, and differential privacy alone is not
enough, because of the accuracy it costs. (3) The resulting model is
```

As it stands the method says we do not consider differential privacy, and
Section 5.2 then compares against differentially private one-shot FL for two
pages. The new clause says what we mean, which is that we do not accept it as
the only protection.

---

## P5. `method.tex`, constraint C6

**Find:**

```latex
\item[\textbf{C6}] \emph{No single party may be able to decrypt.} The parties are
  mutually distrustful and the server is semi-honest. \emph{Therefore}, the secret
```

**Replace with:**

```latex
\item[\textbf{C6}] \emph{No single party may be able to decrypt.} No party may hold
  the decryption key alone, and the server is semi-honest. \emph{Therefore}, the secret
```

The old reason clause said the parties are mutually distrustful, which reads
oddly next to semi-honest. Section IV says semi-honest, so the new word stays
and the reason changes to match it.

---

## P6. PENDING. The membership inference claim

Küpçü's comment of 11 August, 3:32 pm, says the claim is too strong. It appears
twice, once in the abstract and once in the introduction. Waiting on the
decision at T12 before the text is written, because the fix changes a claim and
not only a phrasing.
