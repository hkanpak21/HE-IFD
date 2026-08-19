# Paper TODO, 2026-08-19

This is the work I propose to do on the manuscript, drawn from three sources:
the CryptoKU meeting of 2026-08-07, the writing checklist in
`docs/checklist_for_writing_paper.md`, and the PI comments in
`docs/notes/PI_notes/`.

## How to review this file

Under each item there is a `**Decision.**` line. Write one of `ACCEPT`,
`REJECT`, or `CHANGE`, and a reason. A reason on a rejection matters more than
the rejection, because it tells me what rule to apply to the next item of the
same class.

Nothing in this file has been applied to the manuscript. The only change already
made today is the sync described in T1, which copies the Overleaf state into
`docs/paper/` so that later diffs carry signal.

## Sources, and how items are labelled

| tag | source |
|---|---|
| `AK` | Alptekin Küpçü, Overleaf comments of 11 and 12 August |
| `SS` | Sinem Sav, Overleaf comments of 4 and 17 August |
| `MTG` | CryptoKU meeting, 2026-08-07 |
| `CHK` | `docs/checklist_for_writing_paper.md` |
| `HK` | found while checking something else, no PI comment attached |

## Ground rules I will hold to

1. No number enters the paper without a matching record under `results/`.
2. No citation enters the paper without the claim being checked against the
   source. If a source cannot be checked, the item stays open rather than
   shipping unverified.
3. Replacement text is proposed in chat for pasting into Overleaf. I do not
   edit `docs/paper/` unless told to for a specific item.
4. Register: `academic-ste`. No em dash. No en dash except between numerals.
   One idea per sentence. Active voice with a named actor.

---

# A. Sync and correctness, before anything else

## T1. Sync local to the Overleaf state. DONE

Copied all seven `.tex` files from `temp_current_overleaf/` into `docs/paper/`.
The PI edits of 11 to 17 August are now the local baseline. Without this, every
later diff is noise.

**Decision.**

---

## T2. `AK` `HK` Repair the priority claim in the abstract

The Overleaf edit reads "the first one-shot federated fine-tuning protocol,
where the resulting final model is never disclosed". With that comma the claim
becomes "first one-shot federated fine-tuning protocol", which FedIT and the
other federated adapter works contradict.

Agreed framing from 2026-08-19: the claim is first *cryptographically secure*
one-shot federated fine-tuning. Two candidate sentences, pick one:

```latex
We present HE-OFT, the first cryptographically secure one-shot federated
fine-tuning protocol, in which the final model is never disclosed to any party.
```

```latex
We present HE-OFT, the first one-shot federated fine-tuning protocol in which the
final model is never disclosed to any party.
```

The first states the class the claim lives in. The second is narrower and needs
no defence of what "cryptographically secure" covers. My recommendation is the
first, because "cryptographically secure" is the axis that separates us from the
differentially private one-shot line as well as from the plaintext one.

**Decision.**

---

## T3. `HK` Three defects the Overleaf edits introduced

1. The abstract is now two paragraphs. A blank line was inserted before "We
   present HE-OFT". IEEE abstracts are one paragraph.
2. Table II renames the column to "adapter", and ten sentences in the body still
   say "personal adapter". One name for one thing, which is `CHK` item and the
   `academic-ste` rule. Cheapest repair is to restore the column header.
3. "the updates are themselves the vulnerability: A gradient permits" has a
   capital letter after a colon.

**Decision.**

---

## T4. `HK` Two edits that changed a claim, not only its wording

1. `method.tex` Setting now reads "we do not consider differential privacy due
   to the accuracy loss incurred". Section 5.2 compares against differentially
   private one-shot FL at length, so as written the method contradicts the
   experiments. Proposed: "differential privacy is not accepted as the only
   protection, because of the accuracy it costs".
2. `method.tex` C6 now says the server is "semi-honest" where it said
   "untrusted". This is consistent with Section IV, so I would keep it, but it
   should be flagged because C6's stated reason is "the parties are mutually
   distrustful", which reads oddly next to "semi-honest". Proposed: keep
   semi-honest and change the reason to "no party may hold the decryption key
   alone".

**Decision.**

---

## T5. `HK` File the new PI comments into the review record

`docs/PI_comments_on_2026-08-19.md` sits outside the review folder. I will move
it to `docs/notes/PI_notes/PI_notes_2026-08-19.md` and work it into the same
four-field form the 2026-08-06 file uses: location, comment verbatim, why the
comment was made, replacement text. That form is what lets a context-zero agent
pick the paper up later, which is why `CLAUDE.md` points at the folder.

**Decision.**

---

# B. Küpçü's structural asks. These are the largest items

## T6. `AK` Restructure the introduction: problems first, then one solution

Comment of 11 August, 7:14 pm: state every problem first, then present our
solution, rather than alternating problem and solution. He suggests bold
`Problem 1`, `Problem 2` headings, one per paragraph.

The introduction currently alternates four times: FL leaks at training time,
so one-shot and encryption; both still release the model, so never disclose it;
the query must be built from public parts, so the head is the shared object.

Proposed shape:

1. Setting and motivation, one paragraph.
2. **Problem 1.** Federated learning leaks most at training time.
3. **Problem 2.** Removing that surface still ends with the model disclosed.
4. **Problem 3.** A model that is never disclosed must still answer queries,
   and the querier can only run public parts.
5. Solution overview, with Figure 1, see T7.
6. Contributions, see T9.

This is a rewrite of the whole section, not an edit. It is the item most likely
to need a second pass with the PIs, so I would like it accepted or rejected
before I start rather than after.

**Decision.**

---

## T7. `AK` `MTG` Move Figure 1 and its caption into the introduction as an overview

Comment of 11 August, 7:12 pm. The meeting note asks for an overview at the
start of the methodology. These are the same request pointed at two places, and
they need one answer, because the paper should not carry two overviews.

My recommendation: the overview goes in the introduction, as Küpçü asks, built
around Figure 1 and one worked query from end to end. The method section then
opens with two or three sentences that say what the section covers, not a second
overview. A single running example also answers `CHK` item 1.

If the PIs want the overview in the method section instead, say so here and I
will put it there and leave the introduction with the figure alone.

**Decision.**

---

## T8. `AK` Shorten the related work and add a summary table

Comment of 11 August, 7:10 pm: the section is far too long and needs a summary
table. Section II runs from page 2 to page 4.

Proposed table, one row per system, columns: rounds (one-shot or multi-round),
what is protected (nothing, differential privacy, encryption), whether the model
is disclosed, whether it adapts a pretrained backbone, and what the query
interface returns. HE-OFT is the last row. Every cell traces to
`comparators/REPORTED_RESULTS.md`, which is paper-verbatim, and any cell I
cannot source stays blank rather than guessed.

That table then lets the prose drop most of its per-system description, which is
where the length is.

Note one apparent conflict with the meeting: `MTG` says use plots instead of
tables where possible. That note is about results tables. A comparison matrix in
related work is a different object and I read the two asks as compatible.

**Decision.**

---

## T9. `AK` Rewrite the contribution list so each item is self-contained

Three comments of 11 August, 7:06 to 7:07 pm, one per bullet:

- "a coalition of all but one client has nothing to subtract from" is not clear.
- "a label denies the linear solve that logits would permit" is not clear, and
  the idea was not introduced earlier.
- "Two arrangements" was never defined at that point.

All three are the same defect: each bullet states a consequence that depends on
a fact the reader does not have yet. The fix is to state the mechanism in the
bullet and move the consequence into the section it belongs to, or to give the
one-clause definition inline.

This item depends on T6, because if the problems are stated first then some of
the missing background is already on the page by the time the bullets arrive.

**Decision.**

---

## T10. `AK` The evaluation paragraph repeats, and may itself be a contribution

Comment of 11 August, 7:09 pm, on "Our accounting includes the traffic that
recurs on every query": there is repetition here, and is this not a contribution
in its own right, and why is it not under contributions.

My reading: the honest cost accounting is a contribution, because no peer in the
one-shot line reports per-query traffic at all. I propose it becomes a fourth
bullet, which also removes the repetition Küpçü flags, since the paragraph then
does not restate what the bullets said.

**Decision.**

---

## T11. `AK` Two missing citations in the introduction

Comments of 11 August, 3:29 and 3:30 pm.

1. "each would obtain a better model from the combination than from its own data
   alone" carries no citation. This is an empirical claim about federated
   learning and needs one.
2. "its privacy risk is concentrated at training time" carries no citation. Note
   3 of the 2026-08-06 file added citations to the first half of that sentence,
   and the second half is still bare.

I will pick sources that state each claim directly rather than reusing the
nearest key in the file.

**Decision.**

---

## T12. `AK` "membership inference far stronger than anything possible against the final model" is too strong

Comment of 11 August, 3:32 pm: either support it with evidence or do not write
it this strongly.

He is right, and the paper already has the evidence in a weaker form. Nasr et
al. report 87 percent against the update stream falling to 54.5 percent against
the final model on the same model and dataset. That supports "stronger on the
settings that have been measured". It does not support "than anything possible",
which quantifies over all attacks. Proposed repair: bind the claim to the
measurement.

This also touches the abstract, where the same phrasing appears.

**Decision.**

---

## T13. `AK` Put more results in the abstract

Comment of 11 August, 3:21 pm: could we put more about results, performance
during fine-tuning, against normal FL.

What we can add without a new run: the pooled reference, which is what normal
centralised training reaches on the same setup, and the disclosed reference,
which is what a released model reaches. Both are in
`results/personal_adapter*/stratified/results.csv` already and both are already
in Table II.

What we cannot add without a new run: a comparison against multi-round federated
learning on our own tasks. We do not have that arm. If the PIs want it, it is an
experiment, see T21.

**Decision.**

---

# C. The method and security asks

## T14. `AK` Move the Dirichlet sentence out of the method

Comment of 12 August, 10:33 am: if it does not affect the method, its place is
the start of the experiments section.

Correct. The partition is an experimental choice and the protocol does not
depend on it. I will move the sentence and check that nothing in Section III
refers back to alpha.

**Decision.**

---

## T15. `AK` `SS` C3 and C4 read as contradictory

Küpçü, 12 August, 10:39 am. Sav, 17 August, 11:16 am: C4 is fine, C3 needs to be
clearer so the two do not look contradictory.

C3 says independently trained models do not combine linearly. C4 says the
aggregation is a linear combination. Both are true and the resolution is that C3
is about models trained from different starting points, while C4 applies after
C3 has forced one common starting point. The text does not say that. Proposed
repair: state the resolution in C4 explicitly, and tighten C3 to name the
condition it depends on.

**Decision.**

---

## T16. `AK` "everything the client runs is public" and four other unclear spots

Four separate comments, each small:

1. 12 August, 10:40 am. "everything the client runs is public" and does that
   mean plaintext. Yes. The word should be plaintext, since public and plaintext
   are being used for one property.
2. 12 August, 10:47 am. Figure 1 is not explained in the text. Every figure
   needs a sentence in the prose that walks the reader through it.
3. 12 August, 10:49 am. The generation-scope sentence leaves the reader unsure
   whether we evaluate generation. We do not. The sentence needs to say so
   first and hedge second.
4. 12 August, 10:50 am. "both halves of this claim" does not name its halves.

**Decision.**

---

## T17. `SS` Move the threshold assumption out of the security section

Comment of 17 August, 11:20 am: this is more like a preliminary, why give it
here.

Agreed. The threshold assumption is scheme background, and it belongs with the
multiparty CKKS subsection in the method. Section IV then opens on the ideal
functionality, which is what the section is for. The `\tc` notation is used in
the method and the experiments already, so moving it earlier also fixes the
order in which the reader meets it.

**Decision.**

---

## T18. `SS` `MTG` Fix the form of the ideal functionality, and cite the work it follows

Three things that are one item.

1. Sav, 17 August, 11:22 am: "No party receives theta star" is a requirement,
   not an output, and she asks us to check the convention with Küpçü. She is
   right that it sits in the wrong field. In the functionality form used by the
   secure aggregation literature, that fact belongs in the description of what
   the functionality stores, not under Outputs.
2. `MTG`: find a prior work that gives an ideal functionality in the form ours
   needs. Found. The FULLSA paper of Karakoç, Küpçü and Önen says, verbatim:
   "Similar to [18], we present an ideal functionality for secure aggregation
   that is fault-tolerant... Unlike [18], we also present the aggregator as an
   entity other than the functionality so that one can consider a malicious
   aggregator as well." Putting the aggregator outside the functionality is
   exactly what we do with the server and the serving party. Their [18] is ELSA,
   Rathee, Shen, Wagh and Popa, IEEE S&P 2023.
3. So we cite ELSA for the functionality form and FULLSA for the
   outside-the-functionality construction. This also settles the question from
   last session about whether to cite Karakoç et al. at all. The earlier use was
   decorative and was withdrawn. This use is substantive.
4. `MTG` also asks to merge training and aggregation in the functionality. Step 1
   already does both. I need one sentence from the PIs on whether the comment
   meant the functionality or the figures, which are still separate.

**Decision.**

---

## T19. `SS` Shorten Section IV and rename its headings

Comment of 17 August, 11:23 am: shorten everything up to that point and rephrase
the "Why blabla makes blabla" headings.

Two subsection titles are questions in disguise: "Why the Serving Party Is
Assumed Honest" and the one before it. Our own voice rules say headings are noun
phrases. Proposed: "Assumption on the Serving Party" and similar.

Also in scope, three smaller comments of the same morning:

- 11:19 am, "fixes" is unclear.
- 11:20 am, "describes what a trusted party would do" is informal.
- 11:21 am, the justification of the phase signals may not be needed where it
  sits.
- 11:24 am, "Read that way the peer group separates into three cases" is
  unclear.

**Decision.**

---

# D. Meeting items not covered above

## T20. `MTG` Convert three result tables to plots

Section V holds eight tables and one figure. The three that are naturally plots:

1. The cost grid over ring degree and client count. Table VI and `fig:cost` say
   overlapping things, so the table goes and the figure carries it.
2. The sensitivity sweep on DBpedia, which is a line plot over alpha.
3. The extraction budget, which is a fidelity against queries curve.

Every one of these reads better as a plot and each returns some page.

**Decision.**

---

## T21. `MTG` Assess the experiments, and say what is missing

I propose to write this as a note under `docs/notes/`, not as paper text, so the
PIs can decide what to run before anything is drafted. It will cover: every
number checked against its record, the controls a reviewer will look for, and
the arms we do not have.

Two weaknesses I already know:

1. Table IV's CIFAR-10 uses a 10,000 image subsample, because
   `vm.load_vision` defaults to `max_train=10000`. The paper does not say so.
   This must be disclosed or the run must be redone at full size.
2. The client-count row has one seed. Everything else has three.

Küpçü's abstract comment, T13, also lands here: we have no multi-round federated
learning arm on our own tasks.

**Decision.**

---

## T22. `MTG` Communication cost, and a published number to sit beside it

The 5 MiB per query looks unmotivated on its own. Two published comparables are
already extracted verbatim in `comparators/REPORTED_RESULTS.md`:

- Hyb-Agg reports a communication expansion factor of about 12 times over
  plaintext, and 6.3 MB of client uplink for a 65,536 dimension vector of
  doubles.
- POSEIDON reports 0.38 GB, with units still needing caption confirmation.

Proposed repair: state our expansion factor against the plaintext feature
vector, in the same form Hyb-Agg uses, so the reader sees a property of the
encryption scheme rather than an artifact of our protocol.

**Decision.**

---

## T23. `MTG` Latency, and the one peer that is genuinely comparable

slytHErin is the closest published system: multiparty CKKS, model never
decrypted, key switch only to the querier. Its Table 2 reports 245.58 seconds at
3 parties rising to 354.17 at 20, and about 0.95 seconds per sample amortized at
10 parties, batched, on 12 cores. Ours is 31.5 seconds per query at 4 classes
and 113.2 at 100 classes, single threaded and unbatched.

Any comparison must state two differences: they batch and we do not, and they
return the score vector while we return only the label. By our own Section 5.6
record, a score vector is a much cheaper extraction target than a label, so the
interface difference cuts in our favour and should be said out loud.

**Decision.**

---

## T24. `MTG` Settle privacy against confidentiality

Counts today: privacy 25, private 12, confidential 2, confidentiality 0. One
word is doing two jobs.

Proposed split: the cryptography provides *confidentiality* of the head and of
the query. The threat model is about the *privacy* of the training data. I will
apply the split once, everywhere, and list the sites.

**Decision.**

---

## T25. `MTG` Remove the takeaway headings and the differentiator pattern

Two counts, both measured:

1. There are 49 run-in `\paragraph{}` headings, of which the five
   `\paragraph{Claim}` blocks are the takeaway headings the meeting asked to
   remove.
2. There are about 20 instances of the "X, not Y" differentiator, which our own
   voice rules already ban and which Sav flagged as AI smell in the
   introduction.

Passive voice is not actually a problem. There are 9 agentive passives in 2,000
lines, so I propose to leave that alone rather than churn the text for it.

**Decision.**

---

## T26. `MTG` Look for attack papers that match our interface

Section 5.6 measures label-only extraction and stands alone. There are three
hard-label extraction papers in the bibliography already that are barely used.
I propose one focused pass to see whether any of them, or a newer one, matches a
label-only encrypted interface, and to cite it where 5.6 argues.

**Decision.**

---

# E. Checklist compliance

## T27. `CHK` Bibliography surgery

Against the rules in the checklist, `refs.bib` today has 140 entries with 23
`url`, 20 `doi`, 23 `note`, 15 `publisher`, 5 `series` and 2 `organization`
fields, all of which the checklist says to remove. Twelve `@article` entries
carry no volume and no pages. About 30 booktitles are in long form where the
checklist asks for the short form, so "Proceedings of the 22nd ACM SIGSAC
Conference on Computer and Communications Security" becomes "ACM CCS". Fourteen
`@misc` entries need checking, because most are probably published by now and
belong as `@article` or `@inproceedings`.

This needs nothing from the PIs and it is a thing they will check directly. I
would like to start here.

**Decision.**

---

## T28. `CHK` Abbreviations, unbacked quantifiers, and orphan sentences

Three mechanical passes from the checklist:

1. Every abbreviation defined at first use. CKKS was one such case and note 12
   fixed it. I will check the rest.
2. No "most" or "majority" that we cannot back. Section 2.5 already had one of
   these corrected to "Most of these systems".
3. Checklist item 8: every sentence must have a goal. I will mark the candidates
   rather than delete them, so the PIs choose.

**Decision.**

---

## T29. `CHK` Acknowledgements and submission rules

The acknowledgement already lists both TÜBİTAK projects and the AI use
statement. Two things to confirm with the PIs rather than decide:

1. TNSE states a submission limit of 18 pages and says an appendix may be
   included inside it. Our main body is 18 pages and the references and
   biographies add 3. Confirm with the editorial office whether the limit counts
   references and biographies.
2. TNSE's one-resubmission rule applies to manuscripts rejected by TNSE. Ours
   was rejected by TDSC, so the rule does not bind us. Worth stating to the PIs
   once so nobody re-litigates it.

**Decision.**

---

# F. Deferred by decision

## T30. Membership inference to an appendix

Deferred at the meeting. The page situation makes it moot for now. Recorded here
so it is not lost.

**Decision.**

---

# Order I propose to work in

1. T1 to T5. Sync and correctness. Small, and T2 repairs a claim we cannot
   defend as written.
2. T27. Bibliography. Needs nothing from anyone and is checked directly.
3. T5, then T14 to T19. The method and security comments, which are local edits
   with clear answers.
4. T6, T7, T9, T10. The introduction restructure, once accepted.
5. T8. Related work and its summary table.
6. T20, T22, T23, T24, T25. Presentation and vocabulary.
7. T21. The experiments assessment, written as a note for the PIs to act on.

Items that need a PI answer before I can start: T6, T7, T13, T18 point 4, T29.
