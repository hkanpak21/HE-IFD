# T36. Privacy against confidentiality. Site inventory

Answers T24 of `docs/plan/paper-todo-2026-08-19.md`, which records the meeting
question of 2026-08-07.

**This file is an inventory, not a paste list.** Five other passes are proposing
edits to the same seven files. Find and replace blocks from this pass would
collide with theirs, so every site below is given as a verbatim search string
with a verdict. Apply this pass last, after T4, T8 and T25 have landed, and
search for the string rather than trusting the line number.

Line numbers are as of `20d2be7`. Nothing here is applied to `docs/paper/`.

---

## 1. Counts

Every whole-word occurrence of `privacy`, `private`, `privately`, `confidential`
and `confidentiality` in `main.tex` and `sections/*.tex`.

| where | occurrences |
|---|---|
| total whole-word matches | 43 |
| inside a commented-out line, `related.tex:4` | 1 |
| author biographies in `main.tex` | 3 |
| **live in the manuscript** | **39** |

By word, live sites only.

| word | count |
|---|---|
| privacy | 21 |
| private | 12 |
| privately | 4 |
| confidential | 2 |
| confidentiality | 0 |

Two cite keys, `yeom2018privacy` and `frery2025private`, look like matches to a
substring search and are not prose. They are excluded above.

## 2. Counts by sense

| sense | what it means here | sites | verdict |
|---|---|---|---|
| term of art, differential privacy family | `differential privacy`, `differentially private`, `private learning` | 14 | leave |
| term of art, field name | the title, the running head, the IEEE keyword | 3 | leave |
| term of art, MPC | `input privacy`, the heading and the theorem name in `security.tex` | 2 | leave |
| **P**, privacy of training data | what can be inferred about a client's data or the people in it | 10 | leave |
| **C**, confidentiality | what a bounded adversary can read from a ciphertext | 1 | **change** |
| **L**, local | a quantity that is simply never transmitted | 5 | **change** |
| **UMB**, umbrella | methods with different mechanisms compared | 2 | **change** |
| **REG**, regulated records | records the law protects, not a protocol claim | 2 | leave |

**39 sites. 8 change. 31 stay.** One of the 31 keeps its word and needs its
sentence fixed for a separate reason, see gap 2.

The split in the T24 proposal survives the test, with one correction. The word is
doing **three** jobs, not two. The third is `privately` used to mean *locally*,
and it is five of the eight changes.

## 3. The rule

Short form, for `CLAUDE.md`.

> Encryption gives **confidentiality**, and its objects are the contribution, the
> head and the query. The threat model is about **privacy**, and its object is the
> training data.

Long form, with the two riders the inventory turned up.

> **Confidentiality against privacy.** Encryption gives confidentiality, and its
> objects are the contribution, the head and the query. The threat model is about
> privacy, and its object is the training data. Do not write privacy for a
> property IND-CPA delivers. Do not write private for a quantity that is never
> transmitted, because that quantity is local and no mechanism protects it. Model
> extraction attacks the confidentiality of the head, and the bound on it is
> economic rather than cryptographic. Where methods with different mechanisms are
> compared, write protection.

The paper already writes the rule correctly once, in `experiments.tex` at the end
of `sec:scope`.

> The protocol protects the contributions cryptographically, and differential
> privacy would protect the answers statistically.

That sentence is the model for the whole pass. Nothing in this inventory improves
on it.

## 4. Where model extraction belongs

Extraction through the query interface is a **confidentiality** question, about
the head, bounded by an economic argument rather than a cryptographic one.

Three reasons.

1. The object is the shared head, a trained linear map over public features. It is
   not an individual's record and not a client's dataset, so it is not privacy in
   the sense the threat model uses.
2. The property at risk is whether an unauthorised party can read the head. That
   is confidentiality by definition.
3. The bound is not cryptographic, and `sec:inherent` already says so. It rests on
   a measurement and on a deployment's ability to meter queries. Calling the
   bound a privacy guarantee would attach it to IND-CPA, which does not carry it.

The paper should keep calling this **extraction**, and should not reach for either
of the two words. It already does. `sec:exp-leak` uses `fidelity`, `extraction`
and `queries` throughout, and the paragraph headed `What a copy does not give`
draws the confidentiality against privacy line without using either noun.

> It does not follow that the adversary has learned any client's data. The
> recovered object is a linear map over a public feature space, fitted from labels
> the adversary requested at points it chose itself, and no client record enters
> the attack at any stage.

That is the separation the two words exist to protect. Keeping them apart is what
lets that paragraph stand without a reader asking which guarantee it belongs to.

---

## 5. The inventory

Sense codes. **C** confidentiality. **P** privacy of training data. **L** local,
meaning never transmitted. **TOA** term of art. **UMB** umbrella, methods with
different mechanisms compared. **REG** regulated records.

### 5.1 Sites to change, 8

In the search strings, `\n` marks a line break in the LaTeX source.

| # | file | line | current phrase, verbatim | sense in use | correct sense | proposed word |
|---|---|---|---|---|---|---|
| 1 | `sections/method.tex` | 19 | `(2) Privacy is \emph{cryptographic}` | P asserted | C | `Confidentiality` |
| 2 | `sections/experiments.tex` | 6 | `a federated head over private representations is a usable model` | P asserted | L | `local representations` |
| 3 | `sections/experiments.tex` | 55 | `over representations that\neach client adapts privately,` | P asserted | L | `adapts locally` |
| 4 | `sections/experiments.tex` | 61 | `the shared head over its own privately adapted representation` | P asserted | L | `locally adapted representation` |
| 5 | `sections/experiments.tex` | 103 | `A privately adapted representation improves separability` | P asserted | L | `A locally adapted representation` |
| 6 | `sections/experiments.tex` | 675 | `what a privately adapted\nrepresentation gives up` | P asserted | L | `locally adapted` |
| 7 | `sections/experiments.tex` | 208 | `the accuracy each method gives up for its privacy mechanism` | P asserted | UMB | `for protecting the contribution` |
| 8 | `sections/experiments.tex` | 212 | `DENSE and FedDF report no accuracy cost for privacy, because neither sets out to protect the contribution.` | P asserted | UMB | see note below |

**Site 1 is the flagship, and it collides with two other passes.** The current
sentence reads

> (2) Privacy is \emph{cryptographic}: a client's contribution is never available
> in plaintext to any other party, and we do not consider differential privacy due
> to the accuracy loss incurred.

T4 owns the differential privacy clause. T25 and ground rule 5 own the colon,
which introduces an explanation, and requirements (1) and (3) carry the same colon.
This pass owns one word. Whoever lands last should produce a sentence that starts
`(2) Confidentiality is \emph{cryptographic}.` and keeps the rest to the other two
items. `differential privacy` in the same sentence is a term of art and does not
change under this pass.

**Site 7 restores the paper's own wording.** The claim sentence four paragraphs
above, at line 164, already says `gives up no accuracy for protecting the
contributions`. Line 208 drifts to `privacy mechanism` and thereby files our own
mechanism, which is encryption, under a heading that misdescribes it. Three
paragraphs below, the same subsection says `Our contribution is protected
cryptographically, and that protection costs no accuracy`. That zero belongs to a
confidentiality mechanism, and the heading over it should not say privacy.

**Site 8, two options.** Minimal is `no accuracy cost for protection`. Plainer,
and one word shorter, is `DENSE and FedDF report no such cost, because neither
sets out to protect the contribution.` The second reads back to site 7 and cuts
the repetition that the minimal option leaves. Either satisfies the vocabulary
rule. Pick one.

### 5.2 Sites to leave, 31

**Terms of art from the differential privacy literature, 14 sites.** A term of art
is one name for one thing and must not be split.

| file | line | phrase | note |
|---|---|---|---|
| `intro.tex` | 36 | `protects it\nwith differential privacy` | TOA |
| `method.tex` | 20 | `we do not consider differential privacy` | TOA. The clause belongs to T4 |
| `method.tex` | 455 | `differentially private\none-shot federated learning` | TOA |
| `related.tex` | 50 | `in contrast to differential privacy, which perturbs` | TOA. The antithesis belongs to T25 |
| `related.tex` | 99 | `\subsection{One-Shot Federated Learning and Differential Privacy}` | TOA, section title |
| `related.tex` | 124 | `use differential privacy` | TOA |
| `related.tex` | 125 | `under a differentially private mechanism` | TOA |
| `related.tex` | 129 | `noise-free differential\nprivacy` | TOA |
| `related.tex` | 132 | `Differential privacy proves a\nstatistical bound` | TOA |
| `related.tex` | 136 | `differentially private transfer learning` | TOA |
| `related.tex` | 141 | `a good substrate for private learning` | TOA in that literature, where private learning means learning under a differential privacy budget. The sentence names the DP transfer learning papers two lines above, so the reading is fixed by context |
| `related.tex` | 158 | `multi-round differentially private\ntuning` | TOA |
| `experiments.tex` | 165 | `the differentially private one-shot methods` | TOA |
| `experiments.tex` | 686 | `differential privacy would protect the answers\nstatistically` | TOA, and the exemplar sentence of section 3 |

**The field name, 3 sites.** These are the paper's address, not a claim.

| file | line | phrase | note |
|---|---|---|---|
| `main.tex` | 91 | the title, `Privacy-Preserving One-Shot Federated Fine-Tuning under Homomorphic Encryption` | leave |
| `main.tex` | 105 | the running head, same string | must match the title |
| `main.tex` | 131 | keyword, `privacy-preserving machine learning` | an IEEE keyword and a field name |

The title is the site a reader of this note will ask about first, so the reasoning
is recorded. `Privacy-preserving machine learning` names a research area, not a
property of this protocol. Renaming the paper `Confidentiality-Preserving` would
file it away from the reviewers and the searches that should find it, and it would
be the only paper in the area so named. The title is also supported by the ten P
sites that survive this pass, which are about the privacy risk of federated
learning and are correct. Leave the title alone.

**MPC term of art, and the correct sense as well, 2 sites.**

| file | line | phrase | note |
|---|---|---|---|
| `security.tex` | 165 | `\subsection{Input Privacy Against Malicious Clients}` | leave |
| `security.tex` | 194 | `\begin{theorem}[Input privacy]` | leave |

Both reasons hold at once here, which is why these are the safest sites in the
paper. `Input privacy` is a standard name in secure computation. It is also the
right word under the split, because `def:contentgame` hands an honest client one
of two datasets and asks what the coalition can tell about it. That is a statement
about a client's dataset, so it is privacy and not confidentiality. Changing these
would be the single worst edit available in this pass.

**Privacy of training data, plain and correct, 10 sites.**

| file | line | phrase | note |
|---|---|---|---|
| `main.tex` | 110 | `adapt large pretrained models to private data by fine-tuning` | P. Ordinary English for data that may not be shared |
| `main.tex` | 112 | `concentrates its privacy risk at training time` | P. The premise the paper is built on |
| `intro.tex` | 14 | `its privacy risk is concentrated at training time` | P. Same premise |
| `method.tex` | 9 | `clients holding private labeled data` | P |
| `method.tex` | 410 | `may try to infer private\ninformation from what they observe` | P. Loose but not wrong, and it sits in the threat model where P is the right register |
| `related.tex` | 13 | `a new update computed on its private data` | P |
| `related.tex` | 124 | `The one-shot methods that do address privacy` | P. A statement about prior work |
| `related.tex` | 130 | `their privacy is lossy` | P. About the DP peers |
| `experiments.tex` | 549 | `computationally independent of the private data` | P. The word is right. **The sentence overclaims, see gap 2** |
| `conclusion.tex` | 6 | `federated learning's privacy risk is concentrated in the quantities a protocol exposes` | P |

**Regulated records, 2 sites.**

| file | line | phrase | note |
|---|---|---|---|
| `intro.tex` | 9 | `data protection law restricts the sharing of\nconfidential records` | leave |
| `intro.tex` | 52 | `A model fine-tuned on\nconfidential records can be a regulated artifact` | leave |

These are the paper's only two uses of `confidential`, and both describe data
rather than the protocol. That cuts against a rule that reserves the word for the
cryptographic property, so the judgement is recorded rather than assumed.

Leave them. Both sentences sit before the protocol is introduced, both are about
what the law says, and `confidential records` is the ordinary collocation in that
setting. No reader takes them as a claim about what HE-OFT protects. If a PI
disagrees, one word each settles it, `protected records`, and nothing else moves.

## 6. What this pass does not add

The word `confidentiality` appears zero times, and after this pass it appears
once. That is the whole introduction of the noun, and it is deliberate.

The paper is not missing the concept. It states it with plain verbs everywhere,
and under the writing rules those verbs beat the abstract noun.

- `a client's contribution is never available in plaintext to any other party`
- `the serving party cannot read the query`
- `the server combines these under multiparty CKKS and never decrypts the result`
- `no party, client or server, ever holds the trained classifier in plaintext`

None of these should become a sentence about confidentiality. The noun earns its
place once, at the point where the requirement is named, because that is the one
place the paper labels the property instead of describing it. Everywhere else the
description is better than the label.

That is the restraint in this pass. Eight sites out of thirty-nine, one new noun,
and no sentence rewritten that was not already wrong.

---

## 7. Claim gaps

### Gap 1. `Privacy is cryptographic` contradicts the paper's own Section IV

**Site.** `sections/method.tex` line 19. Change 1 above.

Section IV proves two things, and neither is that privacy is cryptographic.

`thm:semihonest` gives simulation security relative to leakage, against an
adversary holding at most `t-1` key shares. That is **confidentiality** of the
contribution against a bounded adversary.

`thm:malicious` bounds what a deviating coalition learns about an honest client's
data by `negl(lambda) + delta(Q_tot)`. The second term is not negligible. It is
measured in `sec:exp-leak` and turned into a bound on the query allowance.

`sec:inherent` then states the point in as many words.

> The cryptographic claim is that the protocol adds nothing to the leakage of
> $\Fhe$. The operational claim is that $\Fhe$'s own leakage is bounded by the
> query allowance $Q$. The first rests on IND-CPA. The second rests on a
> measurement and on a deployment's ability to meter queries.

So Section IV says privacy is bounded by a measurement, and Section III says
privacy is cryptographic. This is not an unsupported claim, which a reviewer might
let pass. It is the paper contradicting itself across two sections, which a
reviewer will not. It is also the same class of defect as the semi-honest
inconsistency that ground rule 1 was written to prevent.

The one-word change closes it exactly. `Confidentiality is cryptographic` is what
`thm:semihonest` proves, and it leaves the `delta(Q_tot)` term where Section IV
puts it.

**Confidence.** High. Both halves are quoted above from the current source.

### Gap 2. `computationally independent of the private data` overstates Theorem 1

**Site.** `sections/experiments.tex` line 548 to 549. The word `private` is
correct and does not change. The claim does.

Current text.

> The first is cryptographic and is stated in \cref{thm:semihonest}: the
> protocol's messages are computationally independent of the private data.

`thm:semihonest` does not say independent. It says the corrupted parties' view is
computationally indistinguishable from a simulation built out of the leakage, and
the leakage contains the per-client sample counts, which are a function of the
data. `sec:ideal` says so directly.

> The sample counts sit in the leakage because the protocol uses them as public
> scalars, and we prove security relative to that.

The experiments sentence cites the theorem by label and then states it without the
relative clause the theorem carries. A reviewer who follows the cross reference
finds the gap in one step.

**Smallest fix.** Name the leakage in the same sentence, so the claim matches the
theorem it cites. The colon also has to go under ground rule 5, so this is one
sentence either way. Suggested shape, for whoever lands T25 in this paragraph.

> The first is cryptographic and is stated in \cref{thm:semihonest}. The
> protocol's messages reveal nothing about the clients' data beyond the public
> sample counts.

**Confidence.** High.

### Gap 3. `never disclosed` carries no threat model in the abstract

**Site.** `main.tex` abstract, and `intro.tex`. Not a privacy or confidentiality
word, so this pass does not act on it. Recorded because it is the same defect on
the same claim and it will reach the same reviewer.

The abstract says the final model is never disclosed to any party. `sec:malicious-ext`
proves that no protocol of this message pattern realizes the strict functionality
against a **malicious serving party**, and that an honest client cannot tell a
label from a row of the head. So a deviating serving party can pull the head out
one slot at a time, and `thm:malicious` therefore places the serving party among
the honest parties.

The claim holds under the paper's threat model. The abstract does not state the
threat model, and a security journal reviewer will ask under what assumption.

**Owner.** T2 is rewriting that sentence already, so the qualifier costs nothing
if it is folded in there. This pass proposes no text for it.

**Confidence.** Medium. This is normal practice for an abstract, and it is a risk
rather than an error.

### Gap 4. `privately adapted` names a mechanism that does not exist

**Sites.** Changes 2 to 6 above.

Nothing makes the adapter private. It is never transmitted. Under the paper's own
vocabulary, calling it private sends the reader looking for the guarantee that
covers it, and there is none, because there is nothing to protect. `locally
adapted` is accurate, is shorter, and is what the introduction already says.

> Each client keeps its own adapter and never transmits it.

**Confidence.** High that the word is wrong. Low that a reviewer would catch it.
The fix is worth making because it is plainer English, not because it is risky.

### No gap in the other direction

The two `confidential` sites claim nothing about the protocol, and no site in the
paper claims confidentiality where only privacy is proved. The error runs one way.

---

## 8. Order of application

1. Land T4 and T25 first. Both touch requirement (2) of `sec:setting`, which is
   change 1 here.
2. Land T25 in `sec:exp-leak` before gap 2, since that paragraph has an
   elaborating colon in the same sentence.
3. Then apply the eight sites. Six are one word. Two are a short phrase.
4. Add the rule of section 3 to `CLAUDE.md` under the existing
   `Describe it faithfully` note, so the next pass does not reopen this.
