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

Source for the first four rows: T36 paste, 2026-08-20, following the 7 August
meeting note "privacy mi yazıyoruz confidentiality mi". Source for the
"update" row: Sav, 2026-08-04, "what do we mean, fresh quantity". Source for
"semi-honest": Halil, 2026-08-19, on the inconsistency born of changing it in
some sections only.

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
