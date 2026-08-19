# Overleaf paste list, 2026-08-19

What to paste into Overleaf, and where.

## The fastest route, and the one I recommend

Local and Overleaf were identical when this session started. Since then the only
local changes are the ones listed below, so **replacing the whole file is safe
and is far less work than 51 separate edits.** For each file, select all in
Overleaf and paste the whole local file over it.

| Overleaf file | local file | what changed | count |
|---|---|---|---|
| `main.tex` | `docs/paper/main.tex` | the abstract, see A below | 1 block |
| `sections/intro.tex` | same path | punctuation only | 4 |
| `sections/related.tex` | same path | punctuation only | 4 |
| `sections/method.tex` | same path | punctuation only | 16 |
| `sections/security.tex` | same path | punctuation only | 1 |
| `sections/experiments.tex` | same path | punctuation only | 20 |
| `sections/conclusion.tex` | same path | punctuation only | 3 |

**One condition.** This works only if nobody edited Overleaf after the export
you gave me this morning. If a PI has edited since, tell me and I will produce
the 51 edits as individual find and replace pairs instead.

The paper compiles at 21 pages with zero undefined references after all of it.

---

## A. The abstract. `main.tex`. This is the only change that is not punctuation

Four things change in one block.

1. The blank line in the middle is gone, so the abstract is one paragraph again.
2. The priority claim is now restrictive. It says first cryptographically secure
   one-shot federated fine-tuning, not first one-shot federated fine-tuning.
3. Two more results are stated, which answers Küpçü's comment of 11 August,
   3:21 pm. The accuracy the protocol reaches against what a client reaches
   alone, and what one query costs in time as well as in traffic.
4. **A number is corrected. The floor is $0.03$, not $0.04$.** See the note at
   the end of this file.

```latex
Organizations adapt large pretrained models to private data by fine-tuning, and parties
holding complementary data over the same task would each gain from a jointly
fine-tuned model, yet cannot pool their data to build one. Federated learning offers collaboration but concentrates its privacy risk at training time. Gradients
and per-round updates permit reconstruction of training data and support
membership inference substantially stronger than any attack on the final model.
A one-shot protocol that exchanges a single encrypted contribution removes that surface,
but it still ends by handing the final model to every participant, which is not
permitted where the model is itself a regulated or proprietary asset. We present
HE-OFT, the first cryptographically secure one-shot federated fine-tuning protocol,
in which the final model is never disclosed to any party.
Each client fine-tunes a low-rank adapter and a classifier head on a
frozen public backbone, retains the adapter locally, and uploads one encrypted
head displacement. The server combines these under multiparty CKKS and never
decrypts the result. Queries are answered under encryption, and a quorum of
clients returns only the predicted label, addressed to the party that asked. The federation also chooses between two servable arrangements without decrypting either. Across four text classification tasks and one vision task, HE-OFT reaches $0.61$ to $0.79$ accuracy where a client training alone reaches $0.20$ to $0.48$, and it gives up $0.03$ to $0.14$ against a disclosed model. One query costs $31.5$\,s at four classes and $113.2$\,s at a hundred, and $5$\,MiB of traffic.
```

Every number here traces to a record.

| number | source |
|---|---|
| $0.61$ to $0.79$ | three-seed means of `sel_gp_rarefill`, `results/personal_adapter/stratified/results.csv` and `results/personal_adapter_vision/stratified/results.csv`. TREC is the floor at $0.607$, DBpedia the ceiling at $0.789$ |
| $0.20$ to $0.48$ | three-seed means of `local` in the same two records. CIFAR-100 is the floor at $0.197$, AG-News the ceiling at $0.475$ |
| $0.03$ to $0.14$ | `current` minus `sel_gp_rarefill`, per task. CIFAR-100 $0.029$, AG-News $0.071$, Banking77 $0.075$, TREC $0.104$, DBpedia $0.136$. These are the five figures already printed in Section 5.7 |
| $31.5$ and $113.2$ seconds | `results/fhe_serve/cost_grid.json` and `argmax_tournament.csv`, already in Section 5.4 |

---

## B. The punctuation pass. Six section files

51 edits in total. Every one removes a colon that introduces an explanation, or
a semicolon, and nothing else changes. No claim, no number and no citation moves.

Examples of the shape, so you can see there is no surprise in the other 48:

```
before   the updates are themselves the vulnerability: A gradient permits
after    the updates are themselves the vulnerability. A gradient permits

before   All of these remain bound to the iterative protocol: the encryption cost
after    All of these remain bound to the iterative protocol. The encryption cost

before   never decrypts the result; queries are answered under encryption
after    never decrypts the result. Queries are answered under encryption
```

Four sites needed more than a period, because a bare split read badly.

```
before   Two further protocols of the same family are used below: a key switch to
         a designated public key, which re-encrypts a result so that one chosen
         party can read it, and a collective refresh, which restores a depleted
         level budget and plays the role bootstrapping plays in the single-key
         setting.
after    Two further protocols of the same family are used below. The first is a
         key switch to a designated public key, which re-encrypts a result so
         that one chosen party can read it. The second is a collective refresh,
         which restores a depleted level budget and plays the role bootstrapping
         plays in the single-key setting.

before   Two things therefore set the attack surface: what a protocol reveals
         while training runs, and how often it reveals it.
after    Two things therefore set the attack surface, namely what a protocol
         reveals while training runs and how often it reveals it.

before   The claims are, in order: that a federated head ...; that its accuracy
         ...; that the federation ...; that the cryptographic layer ...; and that
         what a participant can learn is bounded.
after    the same list with commas instead of the colon and the semicolons

before   cost; we do not attempt it here.
after    cost, and we do not attempt it here.
```

## What I left alone, and why

- `Left:` and `Right:` in the caption of Figure 4. That is a caption label, not
  an explanation, and IEEE captions use it. Say the word and it goes.
- The `\thanks` fields in `main.tex`, which hold `e-mail:` and
  `received XX; revised XX`. Both are required forms.
- One `\Require query $x$ at client $j$; ...` inside an algorithm block, where
  the semicolon separates two preconditions.
- The `\;` in the display equations. Those are spacing commands, not
  semicolons.
- The `---` in the CIFAR-100 pooled cell of Table II. That is a missing value,
  not an em dash in prose. It should probably read `n/a`, which is one edit if
  you want it.

---

## C. Number correction. Please read this one

The abstract has said $0.04$ to $0.14$ since 2026-08-06. **It should say $0.03$
to $0.14$, which is what the conclusion has said all along.**

I made this error. On 2026-08-06 I recomputed the CIFAR-100 charge as $0.037$
and changed the abstract from $0.03$ to $0.04$ on that basis. Rechecked today
against `results/personal_adapter_vision/stratified/results.csv`, the three-seed
mean of the selected arrangement is $0.7558$ and of the disclosed model is
$0.7845$, so the charge is $0.029$. Section 5.7 of the manuscript has printed
$0.029$ correctly the whole time, so the abstract was the only place that was
wrong. The block in A above carries the fix.

`docs/notes/PI_notes/PI_notes_2026-08-06.md` note 1 has been corrected so that
the record does not carry the wrong figure forward.
