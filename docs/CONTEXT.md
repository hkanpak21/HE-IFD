# CONTEXT: terminology ledger for HE-OFT

The `research` skill reads this file before writing or editing prose. One
name for one thing. Entries carry the date of the ruling and who made it.
Symbols live in `paper/notation-and-terms.md`; check that its table matches
the current paper before trusting a row, since part of it predates the
serve-only design.

## claim

The priority claim, approved wording, copied never paraphrased:

> the first cryptographically secure one-shot federated fine-tuning protocol
> in which the final model is never disclosed to any party

Ruling: Halil, 2026-08-19, after the agent noted that the unqualified form is
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
