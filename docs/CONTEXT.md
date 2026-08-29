# CONTEXT: terminology ledger for HE-OFT

The `research` skill reads this file before writing or editing prose. One
name for one thing. Entries carry the date of the ruling and who made it.
Symbols live in `paper/notation-and-terms.md`; check that its table matches
the current paper before trusting a row, since part of it predates the
serve-only design.

## claim

The priority claim, approved wording, copied never paraphrased:

> the first cryptographically secure one-shot federated fine-tuning protocol
> in which no party receives the trained result

Ruling: Halil, 2026-08-29, replacing the closing clause of the 2026-08-19 form,
which read "in which the final model is never disclosed to any party". The
qualifiers "cryptographically secure" and "one-shot" are untouched and remain
load-bearing. The change is to how the withheld object is named, from the final
model to the trained result, because the protocol withholds the result of the
federation rather than a model any party ever held.

Note that "never disclosed" survives as the name of the third requirement in
\cref{sec:setting} and in the chain of implications. The claim sentence and the
requirement are two different objects and only the claim changed.

Earlier ruling: Halil, 2026-08-19, after the agent noted that the unqualified form is
broken by FedIT and the federated LoRA line. "Cryptographically secure" and
"one-shot" are both load-bearing. No "first" claim wider than this appears
anywhere (abstract, introduction, related work close, conclusion). Ruling of
2026-06-10 (issue fa07) still holds.

## terms

| Term | Use it for | Never |
| --- | --- | --- |
| confidentiality | what encryption gives a contribution, a head, or a query | "privacy" of a ciphertext |
| privacy | the training data and what an adversary learns about it | the protocol's secrecy guarantee |
| local | a quantity that is never transmitted (the adapter) | "private" as a synonym |
| protection | the word when mechanisms are compared | |
| plaintext, ciphertext | always | "in the clear", "public" for "unencrypted" |
| update | the thing a client sends | "quantity", "fresh quantity", "contribution" as a synonym |
| the two arrangements | the shared head over a client's own adapter, or over the bare public backbone | introducing the phrase before it is defined |
| semi-honest | the threat model term, used consistently in every section | mixing with "honest-but-curious" in some sections |
| the server | the one party that merges the heads and answers queries | "the serving party", "the aggregation server", treating them as two parties |
| Preliminaries | the name of Section II, holding notation, multiparty CKKS and the threat model | "Background", "Background and Related Work" |

Source for the first four rows: T36 paste, 2026-08-20, following the 7 August
meeting note "privacy mi yazıyoruz confidentiality mi". Source for the
"update" row: Sav, 2026-08-04, "what do we mean, fresh quantity". Source for
"semi-honest": Halil, 2026-08-19, on the inconsistency born of changing it in
some sections only. Source for "the server": Halil, 2026-08-23, after the PI
meeting. The aggregation server and the serving party become one entity, which
is what `fhe/main.go` and `fhe/serve_argmax.go` already implement. Neither
theorem changes, because Theorem 1 already permits both to be corrupt and
Theorem 2 already requires both to be honest. Source for "Preliminaries":
Halil, 2026-08-23.

## standing rules for this paper

- Orwell's six rules are the standard. Halil, 2026-08-19.
- Least change between PI rounds. Halil, 2026-08-19.
- No colon, semicolon, em dash, or en dash. Halil, 2026-08-19.
- Related work not really related: one sentence, all citations at once.
  Halil, 2026-08-19.
- "Overview" means a brief overview of the methodology, not of the paper.
  Halil, 2026-08-19.
- "Against normal FL" means one comparison sentence against cryptographically
  secure FL on security, privacy, and accuracy. No new experiments. Halil,
  2026-08-19.

## standing rules added 2026-08-23

- `references/kupcu-writing.md` is the authority for paper voice and shape.
  Where it and any other rule disagree, it wins. Halil, 2026-08-23.
- Emphasis is allowed for structure, so bullets, section headings and an italic
  at a definition. Bold inside running prose stays out. The abstract carries
  none. Source: the deck, via `writing.md` rule 8.
- The abstract is four to six sentences in CGI-E order. The deck's ceiling is
  six.
- A caption states the comparison and the conditions. Comment and analysis go
  in the body text, never in a caption. Halil, 2026-08-23.
- Plot fonts match the caption size of the paper, 8pt, checked with
  `figfont.py check`. Put as little text inside a plot as possible and move the
  rest to the legend or the caption. Halil, 2026-08-23.
- Two documents from one source. `main.tex` is the 10-page TNSE submission and
  `main-tr.tex` is the unbounded arXiv technical report. Both carry the same
  seven top-level sections, so a pointer names a section and never a
  subsection. Halil, 2026-08-23.
- Section order is Introduction, Preliminaries, Method, Security, Experiments,
  Related Work, Conclusion. Related work comes after the solution, which is the
  deck's rule. Halil, 2026-08-23.
- Plain technical English and nothing else, in both documents. No "not X but
  Y". No "load-bearing", "the real question is", "it is worth noting",
  "crucially", "fundamentally". No slogan and no closing sentence whose job is
  to sound good. `scripts/lint.py --paper` is the machine check and
  `references/writing.md` is the standard. Halil, 2026-08-23.
- As little new writing as possible. The current text has been read by the PIs,
  so every new sentence is one they must read again. Delete and move. Write
  only where a deletion leaves a sentence ungrammatical or a claim
  unsupported. Halil, 2026-08-23.
- The linter gates text written now, not text the PIs have approved. A warning
  in a paragraph that survives unchanged is left alone. Halil, 2026-08-23.
- Name who acted. The deck's voice table is four pairs and all four are about
  the agentless form, "34 tests were run" against "We ran 34 tests". A passive
  that names its agent is fine, and so is "The simulator is given $\Leak$",
  which is the fixed idiom of simulation-based proofs. What is forbidden is the
  sentence that hides the actor. Halil, 2026-08-23, acting on the deck.
- Figures stay readable in black and white, which the deck requires. Colour is
  never the only thing separating two series, so a line style carries the
  difference as well. Checked by rendering the PDF with `pdftoppm -gray`.
  2026-08-23, after Figure 2's two central series were found to collapse to the
  same mid-grey.
- No colon reveal. A noun phrase, a colon, then a lowercase dramatic reveal is
  banned by rule 7 above and by the `no-ai-slop` skill independently. A colon
  before a list, a label, or a formal statement is still correct, and so is
  "e-mail:". 2026-08-23.
- The submission is checked as it prints. `scripts/check_subseq.py`,
  `scripts/budget.py` and `scripts/lint_view.py` all resolve `\paperonly` and
  `\tronly` first, and all three read float captions, which they did not until
  2026-08-23. A tool that reads the raw source lies about both documents.

## how a session ends

Update `docs/notes/plan-submission-2026-08-23.md` with what was done, add any
resolved term to the table above with its date and who ruled it, and run
`bash scripts/gates.sh`. A gate that fails and is left failing is recorded in
the plan with the reason, never left for the next session to rediscover.
