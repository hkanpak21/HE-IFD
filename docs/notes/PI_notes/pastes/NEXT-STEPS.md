# What to do next, 2026-08-21

Step by step. Everything in steps 1 and 2 is verified against the current
Overleaf state, which local now matches byte for byte.

## Already done, no action needed

Your paste of 2026-08-21 landed perfectly. All eight files plus `refs.bib` are
identical to the state I built and checked. The manuscript is at **20 pages,
zero undefined citations, zero undefined references, zero overfull boxes**, with
the conclusion on page 17.

Applied and confirmed present in the manuscript: the cleaned bibliography, the
factual corrections, the security pass, the method comments, the related-work
shortening, the introduction and abstract edits, the communication correction,
the Table III record, the de-structuring pass, and the citations and
abbreviations pass.

---

# Step 1. Paste `T38-intro-overview.md`

Six blocks. This answers the three Küpçü comments you listed as unresolved, plus
one defect that has to travel with them.

File: `docs/notes/PI_notes/pastes/T38-intro-overview.md`

Order: blocks A, B, C, D into `intro.tex`, then block E into `method.tex`.

**Block D and the first half of block E are one move.** Block D adds
`\input{figures/training}` to the introduction and block E removes it from the
method. Apply both, or Figure 1 is either duplicated or lost.

What each block does:

- **A** adds one sentence so the reader knows three obstacles are coming.
- **B** changes one verb so the third paragraph opens on a requirement instead of
  a fix. A and B together answer the 7:14 pm comment. No bold `Problem 1`
  headings, as you asked.
- **C** corrects the claim that every protocol above hands the participants a
  decrypted model. POSEIDON does not, and it is discussed two paragraphs above.
- **D** puts Figure 1 and a paragraph that walks it into the introduction, which
  is the 7:12 pm comment. Figure 1 moves from page 6 to page 3.
- **E** removes the figure input from the method and replaces "shows the
  arrangement" with a sentence saying what to look at, which is the 10:47 am
  comment.

I applied all six to a scratch copy and built it. Still 20 pages, no new
overfull boxes.

---

# Step 2. Apply the eight vocabulary sites by hand

These are not paste blocks, because they touch sentences that other files also
changed. Every phrase below was checked against the current source this morning
and each occurs exactly once.

Full reasoning: `docs/notes/PI_notes/pastes/*T36-privacy-confidentiality.md`.

### 2.1 `method.tex`, the one that matters

Find `Privacy is \emph{cryptographic}` and change the word to
`Confidentiality`.

This is not a style preference. Theorem 2 bounds what a malicious coalition
learns by a negligible term plus a measured term, and the paper itself says the
measured term rests on metering queries. So Section IV says privacy is not
cryptographic and Section III says it is. One word closes the contradiction.

### 2.2 `experiments.tex`, seven sites

Nothing makes the adapter private. It is simply never transmitted, which is
local, not private.

| find this | change to |
|---|---|
| `over private representations is a usable model` | `over local representations is a usable model` |
| `each client adapts privately` | `each client adapts locally` |
| `its own privately adapted representation` | `its own locally adapted representation` |
| `A privately adapted representation improves separability` | `A locally adapted representation improves separability` |
| `what a privately adapted` | `what a locally adapted` |
| `gives up for its privacy mechanism` | `gives up for protecting the contribution` |
| `report no accuracy cost for privacy` | `report no such cost` |

The last one needs the rest of its sentence trimmed to read
`DENSE and FedDF report no such cost, because neither sets out to protect the
contribution.`

---

# Step 3. Build and check

After steps 1 and 2, recompile and confirm three things.

1. Zero undefined citations and zero undefined references.
2. Figure 1 sits on page 3, near the paragraph that explains it.
3. The page count is still 20.

If any of those is wrong, send me the log and I will find it.

---

# Step 4. Two decisions only you can make

### 4.1 The page limit

We are at **20 pages against a limit of 18**, and your main body is 16. The
difference is entirely references and biographies.

**Send one email to the TNSE editorial office asking whether the 18 pages counts
references and biographies.** If it does not, we are finished on length. If it
does, the cheapest two pages are the reference list, which runs to 107 entries
over about two pages, and cutting to roughly 70 is normal for a journal paper.

Do this before cutting anything, because the alternative cuts all cost
something we would rather keep.

### 4.2 The latency comparison, optional

`docs/notes/PI_notes/pastes/*T22-T23-cost-comparables.md` holds two sentences
placing our per-query time beside slytHErin, the closest published system.

It is honest and it is not flattering. Their reported latency covers a batch of
about 292 samples, so their real per-sample cost at ten parties is about
0.95 seconds against our 31.5. The sentences concede that and rest our case on
the interface, since we return a label and they return a score vector, and by
our own Section 5.6 a label costs an adversary between 16 and 260 times more to
exploit.

Include it or drop it. If we include it we must concede the batching, and if we
quote their headline number without conceding it, a reviewer who knows that paper
will catch us.

---

# Step 5. Housekeeping, whenever

- **`temp_current_overleaf/` is still on disk.** Say the word and I delete it.
- **The paste files have a `*` at the start of their filenames**, except
  `T38-intro-overview.md`. Something in the sync added it. It makes them awkward
  to open from a shell. Say the word and I rename them.

---

# Not now, but do not lose

Recorded in `CLAUDE.md` under "Carried forward, not started". Raise these once
the PIs have finished the current pass.

1. **The noise defence.** Section 5.8 says we do not evaluate it, and
   `results/extraction_defence/results.csv` evaluates it over three tasks and
   five budgets. The defence destroys the task, which is the argument for the
   query allowance rather than against it. Costs no compute. Highest value here.
2. **The CUDA microbenchmarks in Section 5.4** have no record and no citation.
   Attribute them or cut the passage.
3. **Full test sets for the CIFAR tables.** Under two hours now. Table IV argues
   from a 0.005 gap, which is smaller than the standard error of a 2,000 image
   test set.
4. **One real end-to-end encrypted query**, which would connect the accuracies to
   the cryptographic costs for the first time.
5. **Fold the twelve CIFAR-10 cells into Table V**, free, and 13/15 becomes 24/27.
6. **T30, membership inference to an appendix**, deferred by you, and moot until
   the page question is settled.
