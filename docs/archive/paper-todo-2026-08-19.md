> **Superseded 2026-08-23.** Every item here was carried into
> `docs/notes/plan-submission-2026-08-23.md` or completed. Provenance only.

# Paper TODO, 2026-08-19

Revision 2. Rewritten after the direction of 2026-08-19: make the smallest
change that answers each comment, and do not rewrite anything that works.

Sources: the CryptoKU meeting of 2026-08-07, the checklist in
`docs/checklist_for_writing_paper.md`, and the PI comments in
`docs/notes/PI_notes/`.

## How to review this file

Each item has a `**Decision.**` line. Write `ACCEPT`, `REJECT` or `CHANGE`, and
a reason. The reason matters more than the verdict, because it tells me what
rule to apply to the next item of the same kind.

Each item also carries a size tag, so the cost is visible before the decision:

| tag | means |
|---|---|
| `[word]` | one or two words change |
| `[line]` | one sentence changes |
| `[para]` | one paragraph changes |
| `[move]` | existing text moves, wording untouched |
| `[section]` | a section is reworked. Only two items are this size |

## Ground rules

1. **Smallest change that answers the comment.** Repeated large edits between PI
   passes are what produced the semi-honest inconsistency. A comment on one
   sentence gets one sentence back.
2. **Do not restructure.** No new itemize, enumerate, bold run-in headings or
   subsections unless a comment asks for one. Where the paper already has too
   much of this, remove it rather than add more.
3. **Do not change the voice of passages nobody complained about.** The register
   took a long time to settle.
4. Writing rules, replacing the earlier register note:
   - No metaphor or figure of speech you have seen in print before.
   - Never a long word where a short one works.
   - If a word can go, cut it.
   - Active voice.
   - No jargon where an everyday word exists.
   - Break any of these before writing something ugly.
5. **No em dash, no en dash, no colon used to introduce an explanation.** These
   read as machine writing. Current counts in the manuscript: one `---` in a
   table cell, no en dashes, 46 mid-sentence colons and 27 semicolons, of which
   most are the elaborating kind.
6. No number enters the paper without a record under `results/`. No citation
   enters without the claim being checked against the source.
7. Replacement text goes into the paste list, see the last section. I do not
   edit `docs/paper/` except for sync.

## Labels

| tag | source |
|---|---|
| `AK` | Alptekin Küpçü, Overleaf, 11 and 12 August |
| `SS` | Sinem Sav, Overleaf, 4 and 17 August |
| `MTG` | CryptoKU meeting, 2026-08-07 |
| `CHK` | the writing checklist |
| `HK` | found while checking something else |

## Answers received on 2026-08-19, folded into the items below

1. The overview is a short overview of the **method**, not an overview of the
   paper in the introduction. T7.
2. "Against normal FL" means against cryptographically secure FL, on security,
   privacy and accuracy. It is not a request for new experiments. T13.
3. "Merge train and aggregation" meant **simplify the writing** of the ideal
   functionality. Step 1 already does both, so only the wording changes. T18.
4. Assume the 18 page limit **includes** references. We are at 21. Related work
   is where Küpçü says the length is. T8.
5. For work that is not really related, one sentence carrying every citation at
   once: "Several works do XYZ [c1, c2, ..., cn]". T8.

---

# A. Correctness. Small, and one of them is a claim we cannot defend

## T1. Sync local to Overleaf `[move]` DONE

All seven files copied from `temp_current_overleaf/` into `docs/paper/`.
Committed as `af29f68`.

**Decision.**

---

## T2. `AK` `HK` The abstract claims priority over all one-shot fine-tuning `[line]`

The Overleaf edit reads "the first one-shot federated fine-tuning protocol,
where the resulting final model is never disclosed". With that comma the claim
is "first one-shot federated fine-tuning protocol", which the federated adapter
line contradicts. Agreed on 2026-08-19: the claim is first cryptographically
secure one-shot federated fine-tuning. Text in the paste list.

**Decision.**

---

## T3. `HK` Three defects the Overleaf edits left behind `[word]`

1. The abstract is now two paragraphs. Delete the blank line before "We present
   HE-OFT".
2. Table II says "adapter" and ten sentences in the body say "personal adapter".
   Restore the column header.
3. "the vulnerability: A gradient permits" has a capital after a colon. The
   colon should go anyway under ground rule 5.

**Decision.**

---

## T4. `HK` Two edits that changed a claim, not only wording `[line]`

1. The method now says "we do not consider differential privacy due to the
   accuracy loss incurred". Section 5.2 compares against differentially private
   one-shot FL at length, so the method contradicts the experiments. One clause
   fixes it.
2. C6 now says the server is semi-honest where it said untrusted. Section IV
   says semi-honest, so keep the new word and change the reason clause, which
   still says the parties are mutually distrustful. This is the exact class of
   inconsistency ground rule 1 exists to prevent.

**Decision.**

---

## T5. `HK` File the new comments into the review record `[move]`

Move `docs/PI_comments_on_2026-08-19.md` into
`docs/notes/PI_notes/PI_notes_2026-08-19.md` and put it in the same four field
form as the 2026-08-06 file. No paper text involved.

**Decision.**

---

# B. Küpçü's introduction comments

## T6. `AK` The introduction alternates problem and solution `[move]`

Comment of 11 August, 7:14 pm. He suggests bold `Problem 1`, `Problem 2`
headings. **I propose not to use them**, per the direction to keep it natural
and per ground rule 2. The paper already has too many run-in headings, see T25.

The complaint is about order, and the order can be fixed by moving two existing
paragraphs rather than rewriting them. Today the section runs: leak, fix, leak,
fix, leak, fix. Moving the two solution paragraphs down groups the problems
without touching a sentence, and one transition sentence carries the join.

If the PIs want the bold headings after all, say so here and I will add them,
but I would rather show them the reordered version first.

**Decision.**

---

## T7. `AK` `MTG` A short overview at the head of the method `[para]`

Küpçü's 7:12 pm comment suggests moving Figure 1 and its caption into the
introduction under an overview heading. The direction of 2026-08-19 is that the
overview belongs at the start of the method and should be brief.

Proposal, which answers three comments with one paragraph: leave Figure 1 where
it is, and open Section III with a short paragraph that walks one query from end
to end and points at the figure. That covers the overview Küpçü asks for, the
overview the meeting asked for, and his 12 August 10:47 am comment that the
figure is never explained.

**Decision.**

---

## T8. `AK` Shorten the related work `[section]`

Comment of 11 August, 7:10 pm. This section is the reason we are three pages
over. It runs from page 2 to page 4.

Two devices, both from the direction of 2026-08-19:

1. Work that is not really related collapses into one sentence carrying every
   citation at once. Candidates: the general attack literature in 2.1 beyond the
   three results we actually use, the task arithmetic background in 2.4, and the
   secure inference systems in 2.5 that are two party.
2. A small summary table, since Küpçü asked for one. Five or six rows, four
   columns: rounds, what is protected, whether the model is disclosed, what the
   query returns. Every cell traceable to `comparators/REPORTED_RESULTS.md`, and
   any cell I cannot source stays blank. The table costs a third of a column and
   should let the prose drop more than it costs.

This is one of the two `[section]` items. I will bring it as a diff against the
current text, sentence by sentence, so nothing changes that does not need to.

**Decision.**

---

## T9. `AK` Three contribution bullets are unclear `[line]` each

Comments of 11 August, 7:06 and 7:07 pm, one per bullet: "nothing to subtract
from" is unclear, "a label denies the linear solve that logits would permit" is
unclear and was never introduced, and "two arrangements" was never defined.

All three are the same defect. Each bullet ends on a consequence that needs a
fact the reader does not have. The minimal fix is one clause per bullet, either
a short definition inline or the consequence dropped. Not a rewrite of the list.

**Decision.**

---

## T10. `AK` The evaluation paragraph repeats itself `[line]`

Comment of 11 August, 7:09 pm, which also asks whether the cost accounting is
itself a contribution and why it is not in the list.

**I propose the smaller answer**: delete the repeated sentence and leave the
list at three items. Adding a fourth bullet adds structure, which is what ground
rule 2 and the direction of 2026-08-19 both push against. If Küpçü presses, the
accounting can be named in one clause inside the third bullet.

**Decision.**

---

## T11. `AK` Two sentences in the introduction carry no citation `[word]`

Comments of 3:29 and 3:30 pm on 11 August: "each would obtain a better model
from the combination than from its own data alone", and "its privacy risk is
concentrated at training time". Both need a source that states the claim
directly.

**Decision.**

---

## T12. `AK` "far stronger than anything possible against the final model" `[line]`

Comment of 11 August, 3:32 pm: support it or do not write it this strongly. He
is right. Nasr et al. measured 87 percent against the update stream falling to
54.5 percent against the final model on one model and dataset. That supports a
claim about what has been measured. It does not support a claim over all
possible attacks. Bind the claim to the measurement. Same phrasing sits in the
abstract, so this is two sentences in two places.

**Decision.**

---

## T13. `AK` More about results in the abstract `[line]`

Comment of 11 August, 3:21 pm, clarified on 2026-08-19: against
cryptographically secure normal FL, what do we add on security, privacy and
accuracy. No new experiments.

We can answer that from what we already have. Encrypted multi-round FL protects
the updates but discloses the model at the end, pays the cryptographic cost on
every round, and cannot reach a pretrained backbone because the circuit grows
with the network. POSEIDON's own numbers carry the last point, and they are
already quoted in the introduction after note 9. One sentence in the abstract
states the gain, and the accuracy references in Table II are already there.

**Decision.**

---

# C. The method and security comments

## T14. `AK` The Dirichlet sentence belongs in the experiments `[move]`

Comment of 12 August, 10:33 am. Correct. The partition is an experimental choice
and the protocol does not depend on it. The sentence moves and its wording does
not change.

**Decision.**

---

## T15. `AK` `SS` C3 and C4 look contradictory `[line]`

Küpçü 12 August 10:39 am, Sav 17 August 11:16 am, who says C4 is fine and C3
needs to be clearer.

C3 says independently trained models do not combine linearly. C4 says the
aggregation is linear. Both hold, because C3 is about models trained from
different starting points and C4 applies after C3 has forced one common start.
One clause in C3 naming that condition removes the contradiction. C4 is not
touched, per Sav.

**Decision.**

---

## T16. `AK` Four small unclear spots `[word]` or `[line]` each

1. 10:40 am. "everything the client runs is public". Yes, we mean plaintext. One
   word.
2. 10:47 am. The figure is never explained. Covered by T7.
3. 10:49 am. Do we evaluate generation. We do not. The sentence hedges before it
   answers, so it reads as though we might. Reverse the order.
4. 10:50 am. "both halves of this claim" never names the halves. Name them.

**Decision.**

---

## T17. `SS` The threshold assumption is a preliminary `[move]`

Comment of 17 August, 11:20 am. Agreed. It is scheme background, so it moves to
the multiparty CKKS subsection in the method, where `\tc` is first used anyway.
The wording does not change, only the location. Section IV then opens on the
ideal functionality, which is what the section is for.

**Decision.**

---

## T18. `SS` `MTG` Simplify the ideal functionality, and cite what it follows `[para]`

1. Sav, 11:22 am. "No party receives $\thstar$" sits under Outputs and is a
   requirement, not an output. She asks us to check the convention with Küpçü.
   It belongs in what the functionality stores.
2. The meeting's "merge train and aggregation" meant simplify the writing.
   Step 1 already does both, so this is a wording pass over the functionality
   body and nothing structural.
3. The meeting also asked whether a prior work gives an ideal functionality in
   the form we need. Found, and it is Küpçü's own. FULLSA states verbatim:
   "Similar to [18], we present an ideal functionality for secure aggregation
   that is fault-tolerant... Unlike [18], we also present the aggregator as an
   entity other than the functionality so that one can consider a malicious
   aggregator as well." Placing the aggregator outside the functionality is what
   we do with the server and the serving party. Their [18] is ELSA, Rathee,
   Shen, Wagh and Popa, IEEE S&P 2023.
4. So one sentence cites ELSA for the form and FULLSA for the construction. This
   also settles last session's question about citing Karakoç et al. The earlier
   use was decorative and I withdrew it. This one is substantive.

**Decision.**

---

## T19. `SS` Shorten Section IV and fix four spots `[para]`

Comment of 17 August, 11:23 am: shorten everything up to that point, and the
"Why blabla makes blabla" headings should be rephrased. Two headings are
questions in disguise. They become noun phrases.

Four smaller comments the same morning, one line each: "fixes" is unclear
(11:19), "describes what a trusted party would do" is informal (11:20), the
justification of the phase signals may not belong there (11:21), and "the peer
group separates into three cases" is unclear (11:24).

**Decision.**

---

# D. Meeting items

## T20. `MTG` One table becomes a plot `[para]`

Section V holds eight tables and one figure. **I propose converting one, not
three**, because the other two work as tables and converting them is churn.

The one that should go is the cost grid. Table VI and `fig:cost` already say
overlapping things, so the table goes and the figure carries it. That is a
deletion, which also helps the page count.

The sensitivity sweep and the extraction budget stay as tables unless the PIs
ask otherwise.

**Decision.**

---

## T21. `MTG` Assess the experiments, as a note, not as paper text `[none]`

Written under `docs/notes/` so the PIs decide what to run before anything is
drafted. Two weaknesses I already know:

1. Table IV's CIFAR-10 uses a 10,000 image subsample, because `vm.load_vision`
   defaults to `max_train=10000`. The paper does not say so. Either disclose it
   or redo the run at full size.
2. The client-count row has one seed. Everything else has three.

Also open, and visible in the paper: Table II's CIFAR-100 pooled cell is a dash.

**Decision.**

---

## T22. `MTG` The 5 MiB needs a published number beside it `[line]`

Two comparables are already extracted verbatim in
`comparators/REPORTED_RESULTS.md`. Hyb-Agg reports about 12 times expansion over
plaintext and 6.3 MB of client uplink for a 65,536 dimension vector of doubles.
POSEIDON reports 0.38 GB, units still to be confirmed from the caption.

One sentence stating our expansion factor in the same form makes 5 MiB read as a
property of the encryption scheme rather than something our protocol chose.

**Decision.**

---

## T23. `MTG` Latency, against the one genuinely comparable system `[line]`

slytHErin is the closest published peer: multiparty CKKS, model never decrypted,
key switch only to the querier. Its Table 2 reports 245.58 seconds at 3 parties
and 354.17 at 20, about 0.95 seconds per sample amortized at 10 parties, batched
on 12 cores. Ours is 31.5 seconds per query at 4 classes and 113.2 at 100
classes, single threaded and unbatched.

Two differences must be stated in the same sentence. They batch and we do not.
They return the score vector and we return only the label, which by our own
Section 5.6 record is a much harder extraction target.

**Decision.**

---

## T24. `MTG` Privacy against confidentiality `[word]`

Counts today: privacy 25, private 12, confidential 2, confidentiality 0. One
word is doing two jobs. Proposed split, applied once and listed site by site:
the cryptography gives **confidentiality** of the head and the query, and the
threat model is about the **privacy** of the training data.

**Decision.**

---

## T25. `MTG` Remove structure, do not add it `[para]`

Measured: 49 run-in `\paragraph{}` headings, of which five are the
`\paragraph{Claim}` takeaway headings the meeting asked to remove. About 20
instances of the "X, not Y" pattern, which our own rules ban and which Sav
called AI smell.

This item is the one that most directly serves the "too wordy, too much AI" note
and it removes structure rather than adding it, so it sits well with ground rule
2. Passive voice is not a real problem here. There are nine agentive passives in
2,000 lines, so I propose to leave those alone.

Also in this pass, under ground rule 5: the elaborating colons and the
semicolons.

**Decision.**

---

## T26. `MTG` Attack papers that match our interface `[line]`

Section 5.6 measures label-only extraction and cites nothing recent. Three hard
label extraction papers already sit unused in the bibliography. One focused pass
to see whether any matches a label-only encrypted interface, then one citation.

**Decision.**

---

# E. Checklist

## T27. `CHK` Bibliography surgery `[none, bib only]`

`refs.bib` has 140 entries. Against the checklist rules it carries 23 `url`, 20
`doi`, 23 `note`, 15 `publisher`, 5 `series` and 2 `organization` fields to
strip. Twelve `@article` entries have no volume and no pages. About 30
booktitles are long form where the checklist wants short, so "Proceedings of the
22nd ACM SIGSAC Conference on Computer and Communications Security" becomes
"ACM CCS". Fourteen `@misc` entries need checking, since most are probably
published by now.

No paper text changes. The PIs check this directly. I would like to start here.

**Decision.**

---

## T28. `CHK` Abbreviations and unbacked quantifiers `[word]`

Two mechanical passes: every abbreviation defined at first use, and no "most" or
"majority" we cannot back. I will list the sites rather than change them
silently.

**Decision.**

---

## T29. `CHK` Page count and the resubmission rule `[none]`

Assume references count, per the direction of 2026-08-19. We are at 21 and the
limit is 18, so three pages come out. The savings are in T8, T20 and T25, and
none of them is a rewrite.

TNSE's one-resubmission rule covers manuscripts rejected by TNSE. Ours was
rejected by TDSC, so it does not bind us. Recorded so nobody re-opens it.

**Decision.**

---

# F. Deferred

## T30. Membership inference to an appendix

Deferred at the meeting, and moot while we are cutting pages.

**Decision.**

---

# Order

1. T2, T3, T4, T5. Correctness. T2 repairs a claim we cannot defend.
2. T27. Bibliography. Needs nothing from anyone.
3. T14 to T19. Method and security. Small edits with clear answers.
4. T6, T7, T9, T10, T11, T12, T13. The introduction comments.
5. T8. Related work, which is where the three pages are.
6. T20, T22, T23, T24, T25, T26. Presentation.
7. T21. The experiments note.

Two items are `[section]` size and everything else is a word, a line, a
paragraph or a move.

# Paste list

Replacement text lands in
`docs/notes/PI_notes/overleaf-paste-2026-08-19.md`, one entry per accepted item,
each saying which file, which sentence to search for, and what replaces it.
