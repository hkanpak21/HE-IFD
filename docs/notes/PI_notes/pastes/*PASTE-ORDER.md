# Paste order, 2026-08-20

Read this before opening Overleaf. It exists so you do not have to work out
which blocks conflict.

**Order matters for exactly seven blocks out of 87.** Paste the files in the
order below and skip the seven listed. If you paste in a different order, some
anchors will not be found, because another block already changed that text.

I applied all of this to a scratch copy in exactly this order and built it.
Result: **20 pages, zero undefined citations, zero undefined references, zero
overfull boxes.** The conclusion moves from page 18 to page 17, so the body is a
page shorter than it was.

## Step 0. The bibliography, first

Replace the whole of `refs.bib` with `docs/notes/PI_notes/pastes/refs-cleaned.bib`.

138 entries, down from 140. All 107 cited keys resolve. Two duplicates removed
on 2026-08-20: `kerkouche2023property`, which duplicated the cited
`kerkouche2023client`, and `shao2023selective`, which duplicated
`shao2024selective`. Both pairs were byte-identical after the cleanup, so they
were the same paper twice.

This step alone takes the paper from 21 pages to 20.

## Steps 1 to 8. The section files

| step | file | blocks | files touched |
|---|---|---|---|
| 1 | `T31-factual-corrections.md` | 11 | experiments |
| 2 | `T33-security-comments.md` | 18 of 19 | security, method, experiments |
| 3 | `T32-method-comments.md` | 7 of 8 | method, experiments |
| 4 | `T34-related-work.md` | 14 | related |
| 5 | `T35-intro-abstract.md` | 9 | intro, main |
| 6 | `T22-communication-corrected.md` | 4 | experiments, main |
| 7 | `T37-table3-record.md` | 2 | experiments |
| 8 | `T25-destructure.md` | 22 of 27 | experiments, method, related, security |

## The seven blocks to skip, and why

**In step 2, `T33`.** Skip the block whose FIND begins
`% UNCITED ON PURPOSE. This paper was read as the format precedent`. That is a
comment in `refs.bib`, and step 0 already carries the change, including the new
`rathee2023elsa` entry.

**In step 3, `T32`.** Skip the block whose FIND begins
`This section states what the protocol guarantees.` That block changes the word
"fixes" that Sav marked at 11:19. Step 2 deletes the whole sentence when it moves
the threshold subsection out of Section IV, so the repair is no longer needed.
Both agents predicted this collision independently.

**In step 8, `T25`.** Skip five blocks, each because an earlier step already
rewrote the sentence it targets and already removed the antithesis it was there
to remove. I checked the final build and none of the five patterns survives.

- `all three seeds, by margins of $0.13$ to $0.24$.` Step 1 changed this sentence.
- `setting of \cref{sec:serving} affordable, and we compose with it rathe`
- `can be measured against it. The server and the serving party are entit`
- `clients deviate. The server and the serving party remain honest, and`
- `The equal-size restriction is necessary rather than cosmetic.`

The last four were rewritten by step 2, which reported removing five antithesis
sites of its own.

## Step 9. By hand, last

`T36-privacy-confidentiality.md` is an inventory rather than paste blocks,
because it touches sentences that five other files also change. Apply its eight
sites after everything above has landed. The file names which other item owns
each overlapping sentence.

The one that matters is `method.tex`, "Privacy is cryptographic", which
contradicts Theorem 2. Theorem 2 bounds what a malicious coalition learns by
$\negl(\lambda)+\delta(Q_{\mathrm{tot}})$, and the paper itself says $\delta$
rests on a measurement and on metering. One word closes it.

## Not in this batch

- `T27-bibliography.md` is the report behind step 0, not a paste.
- `T11-T26-T28-citations-and-audit.md` holds citations and an abbreviation audit
  that were not folded into the eight files above. Paste it whenever you like,
  its anchors are independent.
- `T22-T23-cost-comparables.md` is superseded in its communication half by
  step 6. Its latency half, the slytHErin comparison, is still live and still
  optional.
- `overleaf-paste-2026-08-19.md` entries P1 to P5 are already in the manuscript.

## What is still not fixed

Two defects nobody has closed, both recorded in `CLAUDE.md` under the reminders.
The CUDA microbenchmarks in Section 5.4 have no record and no citation. The
noise-defence sentence in Section 5.8 says we did not evaluate it, and
`results/extraction_defence/results.csv` evaluates it.
