# Plan: the 10-page TNSE submission and the arXiv technical report

Written 2026-08-23, after the PI meeting of 2026-08-21 and a design interview
with Halil the same day. The PI list is `docs/notes/PI_notes/PI_notes_2026-08-21.md`.
The terminology rulings this plan creates are already in `docs/CONTEXT.md`.

The paper as it stands is `docs/paper`, commit `cc1df39`, taken from the
Overleaf copy the PIs have read. It builds to 20 pages with no undefined
citation, no undefined reference and no overfull box.

## Where this stands, 2026-08-23 end of day

Every work item W1 to W10 is done and committed. The submission is 10 pages with
41 references. The technical report is 20 pages with 110, from the same source.
`bash scripts/gates.sh` runs all nine gates and all nine pass.

| item | done |
| --- | --- |
| W1 build scaffolding | two drivers, `\paperonly` `\tronly` `\trsee`, the split changed no rendered text |
| W2 section reorder | Preliminaries at II, Related Work at VI, the threat model into Security |
| W3 system figure | one draw.io figure, three stages, the server drawn once, 8pt calibrated |
| W4 entity merge | one server everywhere, neither theorem changed |
| W5 abstract | eleven sentences to six, CGI-E |
| W6 security | three statements, one proof sketch, the proofs to the report |
| W7 experiments | 5299 words to 1435, two tables and one four-panel figure |
| W8 method | 3510 words to 1791 |
| W9 related work | 1518 words to 864, grouped |
| W10 citations | 110 keys to 41 in the submission, 110 kept in the report |
| the slop pass | 21 sentences against no-ai-slop and the deck |

Against `cc1df39`, which is what the PIs read: 58 identical paragraphs, 79
deletions-only, 13 allowed by the entity merge, 22 accepted with a written
reason, and 0 rewritten. The report view is the same at 0 rewritten.

Three things remain before anything is sent.

**Overleaf still holds the pre-restructure paper.** The delivery is a whole-file
replacement, decided 2026-08-23, and it has not happened yet.

**The arXiv identifier is a placeholder.** `refs.bib` carries
`arXiv:XXXX.XXXXX` and gate 9 counts it. The report goes to arXiv first, its
identifier replaces the placeholder, then the paper goes out. Confirmed
2026-08-23.

**The membership-inference work is a later session.** Rewire `mia/target.py`,
which still composes the retired distillation pipeline, and open with a fresh
literature search, because the setting changed from a released model to a
label-only interface and heads recovered by extraction.

## The venue, and what the TDSC rejection costs each candidate

Read on 2026-07-29 from the ComSoc TNSE information page, the SPS information
for authors, and the IEEE Computer Society author resources page. Folded here
from `docs/archive/security-program.md`, which is superseded.

| Journal | Society | What the TDSC rejection costs |
| --- | --- | --- |
| IEEE TNSE | ComSoc | Nothing. Its one-resubmission rule covers TNSE's own rejections only |
| IEEE TIFS | Signal Processing | Disclose the rejection and quote every previous review verbatim with a response to each |
| IEEE TDSC | Computer Society | No public policy. Ask the editorial office |

TNSE is the target, reconfirmed 2026-08-23. IEEE bills above ten printed pages
at $220 each, which is where the ten-page target comes from, and the count
includes references and biographies.

One item is still open from that meeting. Nobody has asked the TDSC editorial
office whether a rejected manuscript may return. It does not block TNSE.

## 0. The goal

Two documents from one source, and the submission is cut by deleting and moving.

`main.pdf` fits ten printed pages, references and biographies counted. Every
claim it makes is supported inside it, or by a pointer to a section of
`main-tr.pdf`. `main-tr.pdf` carries everything the submission drops and reads
start to finish with no jump to an appendix.

Done means all seven of these hold at once.

| Gate | Command | Target |
| --- | --- | --- |
| length | `pdfinfo docs/paper/main.pdf` | 10 pages or fewer |
| prose budget | `scripts/budget.py` | 5,563 words or fewer |
| nothing rewritten | `scripts/check_subseq.py --base cc1df39` | 0 REWRITTEN, every acceptance carrying a reason |
| the two documents agree | `scripts/check_split.py docs/paper` | OK |
| bibliography | `lint.py --bib` and a key count | 55 keys or fewer, 0 mechanical errors |
| both compile | `pdflatex` on each driver | 0 undefined citations, 0 undefined references, 0 overfull boxes |
| voice | `lint.py --paper` | no error in any paragraph written now |

The last gate is the one that protects the PIs. The linter runs on what
`check_subseq.py` reports as new, and on nothing else, because the rest is text
they have already approved.

## 1. What was decided

| Question | Ruling |
| --- | --- |
| Page target | 10 printed pages, counting references and biographies |
| Section order | Introduction, Preliminaries, Method, Security, Experiments, Related Work, Conclusion |
| Section II | Preliminaries. Notation, multiparty CKKS and the threat model move in from Method |
| Related work | Moves after the solution, as the deck requires, and shrinks to one grouped page |
| Two documents | One source, two drivers, the same seven top-level sections in both |
| The report | Read start to finish with no appendix jumps. No length limit. Extended in place |
| Order of release | The report goes out first. The paper cites it by a placeholder arXiv id until then |
| The merged entity | The server. "Serving party" is retired |
| The system figure | One figure, three stages, the server drawn once, selection as a branch |
| Experiment floats | Two tables and one four-panel figure |
| Captions | State the comparison and the conditions. Comment and analysis go in the body |
| Plot fonts | 8pt, the caption size, checked with `figfont.py check` |
| Security in the paper | Three statements, one proof sketch. All proofs in the report |
| Running example | None. Formal examples at definitions where they help |
| Citations | Cut by relevance to our story. One citation for common knowledge. Prefer published, recent, better venue |
| A claim and its citation | A claim keeps its citation, or the claim goes to the report or is deleted |
| Delivery | Whole-file replacement into Overleaf |
| The submission text | Remove and rephrase. Never delete a section and write it again |
| MIA | Deferred to the report session, opening with a fresh literature search |

## 2. The page budget

Measured off the compiled PDF, not estimated.

| part | now | paper | prose words now | prose words in the paper |
| --- | --- | --- | --- | --- |
| front matter | 0.34 | 0.30 | 230 | 130 |
| I Introduction | 1.21 | 1.40 | 1085 | 810 |
| II Preliminaries | 0.00 | 0.80 | 1100 arrives from Method | 540 |
| III Method | 5.05 | 2.10 | 3469 less the 1100 | 1890 |
| IV Security | 2.09 | 0.85 | 1756 | 513 |
| V Experiments | 5.97 | 1.90 | 5252 | 1000 |
| VI Related Work | 2.29 | 0.85 | 1499 | 540 |
| VII Conclusion | 0.28 | 0.30 | 300 | 270 |
| body | 17.23 | 8.50 | | |
| references | 2.40 at 110 keys | 1.20 at 55 keys | | |
| biographies | 0.33 | 0.33 | | |
| total | 19.96 | 10.03 | | |

Three facts about this table are worth carrying.

Method needs a 20 per cent cut once notation, CKKS and the threat model leave.
That is clause trimming and a few deleted paragraphs.

Experiments needs 81 per cent, and 72 per cent of it survives the three PI
removals. This is the hard section. If the argument breaks, move 0.20 of a page
from Method, which puts Method at 28 per cent.

The three full-width figures cost 1.44 pages between them. Merging them into
one saves 0.95, which is more than the citation cull and the related work cut
together.

## 3. The build

### Two drivers, one source

`docs/paper/main.tex` sets `\submissiontrue`. `docs/paper/main-tr.tex` sets
`\submissionfalse`. Everything else lives in `docs/paper/sections/` and is
shared. The preamble moves to `sections/preamble.tex` so a package added once
reaches both documents.

```latex
% sections/preamble.tex, after \newif\ifsubmission is set by the driver
\ifsubmission
  \newcommand{\paperonly}[1]{#1}
  \newcommand{\tronly}[1]{}
  \newcommand{\trsee}[1]{Section~\ref{#1} of the technical
                         report~\cite{heoft2026tr}}
\else
  \newcommand{\paperonly}[1]{}
  \newcommand{\tronly}[1]{#1}
  \newcommand{\trsee}[1]{\cref{#1}}
\fi
```

### The invariant that makes `\trsee` sound

Both documents carry the same seven `\section` commands in the same order, so
`\ref{sec:security}` yields the same numeral in both. A pointer therefore names
a section and never a subsection, because subsections do differ between the two.

`scripts/check_split.py` enforces it. It parses both drivers, extracts the
ordered list of `\section` labels each one produces, and fails if they differ.
It runs before every push.

### The placeholder identifier

```bibtex
@article{heoft2026tr,
  title   = {{HE-OFT}: Privacy-Preserving One-Shot Federated Fine-Tuning
             under Homomorphic Encryption (Technical Report)},
  author  = {Kanpak, Halil \.{I}brahim and Sav, Sinem and
             K\"up\c{c}\"u, Alptekin},
  journal = {arXiv preprint arXiv:XXXX.XXXXX},
  year    = {2026}
}
```

`XXXX.XXXXX` is greppable. Nothing is submitted while it is still there.

### The subsequence rule and its checker

For the submission, the text of every surviving paragraph is a subsequence of
the text it replaces. Deletions only. Three exceptions and no others.

1. A number that changed, against its record.
2. "The serving party" becoming "the server".
3. A cross-reference retargeted at the report.

`scripts/check_subseq.py` takes the old file and the new one, aligns paragraphs,
and reports each as identical, deletions-only, or rewritten. Anything in the
third bucket is a decision for Halil, with the reason stated. This is the gate
that keeps the PIs from having to read the paper again.

The corollary is that the cut works at paragraph granularity. Most of the 8.5
pages comes from deleting whole paragraphs and moving them to the report, not
from shortening sentences.

### The plot style

Every plot in either document goes through `docs/paper/figures/heoft_plot.py`.
One import, one palette, one figure size, so a font size is decided once and
never in a plotting script.

```python
import sys; sys.path.insert(0, "docs/paper/figures")
import heoft_plot as hp

fig, ax = hp.panels(4)          # full width, four panels, 12.7% of a page
ax[0].plot(x, y, color=hp.SERIES["selected"], label="selected")
hp.label(ax[0], "a")            # panel letter, top left, caption size
hp.save(fig, "fig_trends.pdf")  # saves and reports whether the fonts match
```

Sizes come from `docs/paper/.paper-meta.yml`, measured off IEEEtran with the
journal option rather than guessed. `\the\columnwidth` is 252.0pt,
`\the\textwidth` is 516.0pt, `\the\textheight` is 696.0pt.

Three rules the module enforces, all of them Halil's ruling of 2026-08-23.

**Every glyph is 8pt, the caption size.** The skill's `paper.mplstyle` drops
ticks and legends to 7, which is the usual convention. Nothing in one of our
plots is smaller than the caption beneath it. `figfont.py check <pdf> --target 8`
verifies it and the smoke test passes with 0 of 33 spans outside tolerance.

**The figure is saved at its final width and included with no width option.**
Never `width=\linewidth` on one of these and never `\resizebox`. Both rescale
the fonts and the plot stops matching the paper.

**As little text inside a plot as possible.** A panel carries its axis labels
and its data. Everything else goes to the legend or the caption. The caption
states the comparison and the conditions and stops. Comment and analysis are
body text.

The palette is the SANZO block already in `sections/preamble.tex`, the same hex
values, so a plot and a draw.io diagram on the same page use the same blue. One
name for one thing extends to colour, so `selected` is `paperblue` in every
panel of every figure, `alone` is the tan, `disclosed` is the sage and `pooled`
is the blue-grey.

### What the linter gates

`scripts/lint.py --paper` runs on the paragraphs `check_subseq.py` classifies as
rewritten, and on nothing else. The current text carries 13 errors and 165
warnings, and 99 of the warnings are agentless passives that sit inside proofs
and float captions the PIs have read and accepted. Fixing those is new writing,
which is the thing this plan exists to avoid. A warning in text that survives
unchanged is left alone. A warning in text I write is an error.

The one exception is the 13 errors, which are mechanical and cheap. Five
intensifiers, four identifiers in prose, one semicolon, one banned phrase, one
filler, and one table that nothing references. Those are word-level fixes and
they go in wherever the surrounding paragraph is already being touched.

## 4. The work, in order

Sizes are `[word]`, `[line]`, `[para]`, `[move]`, `[section]`, `[figure]`.

### W1. Build scaffolding `[move]`
Create `main-tr.tex`. Move the preamble into `sections/preamble.tex`. Add the
toggle macros and the placeholder bib entry. Write `check_split.py` and
`check_subseq.py`. No prose changes. Both documents compile and are identical
in content at this point.

### W2. The section reorder `[move]`
`related.tex` splits. Notation, multiparty CKKS and the threat model move out of
`method.tex` into a new `preliminaries.tex`. The survey becomes Section VI. Only
`\input` order and file boundaries change. No sentence is rewritten. This alone
takes 0.80 of a page off Method.

### W3. The merged system figure `[figure]`
Draw.io, three stages left to right, the server drawn once spanning stages 2 and
3, selection as a branch off stage 2. Replaces `fig_training`, `fig_serving` and
`fig_selection` in the paper. The report keeps all four. Saves 0.95 of a page.
Uses `drawio-skill` and the SANZO palette already in `main.tex`.

### W4. The entity merge `[word]`
"The serving party" becomes "the server" everywhere. The sentences that named
two parties collapse to one. Neither theorem changes, because Theorem 1 already
permits both to be corrupt and Theorem 2 already requires both to be honest.
Functionality 1's parameter list loses one party. `fhe/main.go` and
`fhe/serve_argmax.go` already implement one server, so the code needs nothing.

### W5. The abstract `[para]`
Eleven sentences to six, in CGI-E order. "Queries are answered under encryption"
is the one passive sentence and it goes active. No emphasis, per the deck.

### W6. Security `[section]`
Keep Functionality 1, Definition 1, Theorem 1 with a sixteen-line sketch,
Theorem 2 as a statement with one sentence, Proposition 1 as a statement with
one sentence, and six lines on inherent leakage. Everything else into `\tronly`.
"Two mechanisms would remove the assumption, and we implement neither" is
deleted from the paper by name, on the PI's instruction. The two mechanisms
belong in the report, where recomputation and spot-checking can be stated as
what they are, which is a design the traffic-saving choice already permits.

### W7. Experiments `[section]`
Remove to `\tronly`: the accuracy of the selection rule, residual leakage, and
the comparison with model disclosure. Rebuild the floats to Table II
(accuracy), Table III (CIFAR-10 against the published partitions) and Figure 2,
a four-panel `figure*` carrying accuracy against client count, against skew,
against local steps, and query cost against ring degree. Every panel already has
a record, and every panel is drawn through `heoft_plot.py` at 12.7 per cent of
a page for the four together. Communication drops to three numbers in a sentence. Cryptographic cost
goes from 1.46 pages to 0.60.

Two corrections ride with this work.

The CUDA microbenchmarks in the cost subsection, 30 ms for a product and 29.5 ms
for a rotation, carry no record and no citation. Under the rule that a claim
keeps its citation or the claim goes, they leave the paper. The report either
attributes them to `yang2024phantom` after checking, or drops them.

The scope subsection says calibrated noise on returned labels "composes with the
protocol without modification" and that "we do not evaluate it".
`results/extraction_defence/results.csv` evaluates it, thirty runs per cell over
three tasks and five budgets, and the defence destroys the task. AG-News falls
from 0.649 to 0.310 at eps=1, DBpedia from 0.788 to 0.111, Banking77 from 0.196
to 0.014. That is the argument for the query allowance being the right control.
The paper corrects the sentence in one clause. The report gives the measurement.

### W8. Method `[para]`
A 20 per cent cut at paragraph granularity over what remains after W2. The
derivations, the cost arguments and the necessity argument for the partition
move to `\tronly`. Survivors keep their wording.

### W9. Related Work `[section]`
1499 words to 540, grouped as the deck requires, in the form "there are works
doing XYZ [c1...cn]". Table I stays, because it is the positioning and it is
what a reviewer reads. The full survey lives in the report. Be generous to the
competition. Describe what each work does and where it says so, and do not
judge it.

### W10. Citations `[bib]`
Delete the 29 entries cited nowhere. `kanpak2024cure` is the exception. It is
the authors' own CURE, the rule would delete it, and it should be cited
instead. Cut the used keys
from 110 to about 55 by relevance to our story. One citation where a group gives
common knowledge, chosen as the most recent and the best placed. Collapse the
five regulation citations in the first paragraph to two. Run `lint.py --bib` for
the mechanical items, which are editors, URLs, DOIs, notes, and the
`@inproceedings` short booktitle form. The report cites all 110, and the extra
keys ride inside the report-only blocks, so IEEEtran prints the right
bibliography for each document without further work.

### W11. The report's own material `[section]`
Beyond the restored cuts, the report gains what has a record and no home. The
noise-defence measurement. The communication model with its scenarios, which is
in `docs/notes/archive/communication-model-2026-08-20.md`. The full cost grid
over ring degree and client count. The extraction scaling law. The full related
work survey. A reproducibility appendix naming the record behind every number.

### W12. MIA, a later session
Rewire `mia/target.py`, which still composes `src.phase0`, `src.distill` and
`src.aggregate` and attacks a released model that no longer exists. The attacks
in `mia/attacks.py` are published and stay. Open the session with a literature
search, because the setting changed from a released model to a label-only query
interface and heads recovered by extraction. `choquettechoo2021labelonly` is
already in `refs.bib`, cited nowhere, and is the published attack that fits the
interface as it is. The paper carries one paragraph and a pointer.

### W13. Gates, before anything is sent
`check_split.py`, `check_subseq.py`, `lint.py --paper`, `lint.py --bib`,
`check-layout.sh`, `figfont.py check` on every figure, a grep for
`XXXX.XXXXX`, and both documents compiling with zero undefined citations, zero
undefined references and zero overfull boxes. Page count reported for each.

## 5. The checklist, filled

Source: `references/checklist-paper.md`, the advisor's own list. Run once now, at
plan time, and again on the finished draft.

| Item | Status | Reason |
| --- | --- | --- |
| An overall story, examples wherever possible, a running example if one exists | Partly | Ruled 2026-08-23 that there is no running example. The checklist hedges with "if one exists". Formal examples appear at definitions where they help |
| The introduction cites the most relevant work to introduce the gap, then a bulleted list of contributions | Met | The list is there, three items, each refutable and each forward-referenced to a section |
| Paragraphs and sentences flow | To check | `check_subseq.py` guarantees no new sentence enters. Flow across a deletion boundary is the one thing it cannot check, so it is read by hand |
| Every claim backed by a citation or a result inside the paper | At risk, W10 | The cull is the risk. The rule is that a claim keeps its citation or the claim goes. `lint.py --paper` `cite` check runs after |
| No "majority" or "most" without backing | To check | `lint.py` `unbacked` |
| No "very", no "strongly", no informal word | To check | `lint.py` `intensifier` |
| No vague statement | To check | By hand, at W13 |
| Every sentence useful | Addressed by W5 to W9 | The whole exercise is this item. 13,361 words to about 5,700 |
| Active rather than passive | One known failure | The abstract's "Queries are answered under encryption". Fixed at W5. `lint.py` `passive` for the rest |
| No technical detail stands alone | To check | By hand. The risk is the cut, since an intuition sentence is cheaper to delete than the detail it explains. Flagged at W6 and W8 |
| Related work grouped, not only saying bad things | W9 | Grouping is the instruction. "Prior work is described, not judged" is already a standing rule |
| Every abbreviation defined at first use | To check | `lint.py` `undefined`. The section reorder moves definitions, so this must run after W2 |
| Every submission rule met | Open | 10 printed pages is the target. TNSE's supplementary-file limit is unchecked and matters for whether the report can ride along |
| Submission details and dates known before talking to the advisor | Open | TNSE submission window and the editorial office question about the resubmission policy |
| Grammar and spelling checked strictly | To do at W13 | |
| KOLT or the Writing Center consulted | Replaced by the linter | `references/writing.md` is the standard and `scripts/lint.py --paper` is the machine check. It decides dashes, semicolons, explanatory colons, banned words, intensifiers, filler, identifiers in prose, antithesis, agentless passives and unbacked quantifiers. Baseline on the current text is 13 errors and 165 warnings |
| Plain technical English, no LLM register | Standing rule, W5 to W11 | Standard technical English and nothing else. No "not X but Y". No "load-bearing", "the real question is", "it is worth noting", "crucially", "fundamentally". No slogan and no closing sentence whose job is to sound good. `lint.py` catches antithesis, intensifiers, filler and the banned list. The rest is read by hand at W13 |
| As little new writing as possible | Standing rule, W5 to W11 | The current text has been read by the PIs. Every new sentence is a sentence they must read again and answer questions about. The cut therefore deletes and moves, and writes only where a deletion leaves a sentence ungrammatical or a claim unsupported. `check_subseq.py` names every paragraph that needed a new sentence and each one is Halil's decision, not mine |
| Acknowledgements checked | Met | TÜBİTAK 124E091 and 124N941 are in `main.tex`, and the LLM-use sentence is there |
| Author version PDF per the copyright rules | Not yet | `references/copyright.md` at acceptance |

Bibliography items are W10 and are all mechanical.

## 6. Carried forward

Not started, decided, easy to lose.

The full CIFAR test sets are running as jobs 1593568 to 1593571 on the `ai`
partition, three seeds each of the four matched cells at `max_test=10000`. Table
IV argues from a margin of 0.005, which on 2,000 test images is ten images. This
resolves it on five times the data with no retraining.

One real end-to-end encrypted query. `fhe/main.go` has no flag that loads a real
head, so this needs a Python exporter and about a hundred lines of Go. The
compute is minutes. It belongs in the report session.

Fold the twelve CIFAR-10 cells into the selection table. Free, and it turns the
selection result from 13/15 into 24/27. The table is leaving the paper, so this
is report work.

`temp_current_overleaf/` is deleted. Its content is commit `cc1df39`.

## 7. What could break this plan

Experiments at 81 per cent is the one number that could fail. If four results,
five tasks and the cryptographic cost cannot be argued in 1,000 words, the
correction is 0.20 of a page from Method, and the fallback after that is a
second table moving to the report.

The 10-page target counts references and biographies. If the PIs meant 10 pages
of body, the whole budget loosens by 1.5 pages and several of these cuts become
unnecessary. It costs one email to the editorial office to be sure, and that
email also settles the TDSC resubmission question that has been open since
2026-07-29.
