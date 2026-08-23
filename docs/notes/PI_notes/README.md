# PI review notes

The PIs read the HE-OFT manuscript on Overleaf and leave margin comments. This
folder is the record of that review and of how each comment was answered.

**Any agent working on the paper must read the current dated file here before
editing any section it covers.** The section text does not explain why it reads
the way it does. This folder does.

## Files

| file | what it holds |
|---|---|
| `PI_notes_<date>.md` | one review round: every comment, why it was made, and the replacement text proposed |

## How a round is recorded

One entry per comment, with four parts:

1. **Location.** The file and the passage the comment sits on.
2. **What the PI wrote.** Quoted, unedited, including the timestamp when the PI
   left one. Never paraphrased.
3. **Why the comment was made.** The reading of the problem, so a later agent
   does not re-solve a different one.
4. **Replacement text.** A LaTeX block, ready to paste into Overleaf.

An entry carries a status: proposed, pasted, or withdrawn.

## Rules that hold across every round

- **Replacement text is not applied to `docs/paper/` in this repository.** The
  PIs read the Overleaf copy. A local edit diverges from what they see. The
  chat gives the block, the user pastes it.
- **No em dash, and no en dash except between numerals.** Overleaf source uses
  `---` for an em dash and it is banned outright.
- **No markdown bold in replacement text.** It is LaTeX, not chat.
- Replacement prose follows the `research` skill's `references/kupcu-writing.md`.
  The active voice, one idea per sentence, and a verb that matches the evidence
  held. The first person is correct where the sentence has an author, and what
  stays out is the agentless form that hides who acted.

  Corrected 2026-08-22. This bullet used to say "no first person". That rule
  came from the retired `academic-ste` register and never from a PI. Note 11 of
  `PI_notes_2026-08-06.md` records the PI dictating the opposite, "In this work,
  we present ... that enables ...".
- **No number enters a replacement without a check against a record under
  `results/`.** Numbers already in the manuscript are re-derived, not trusted.
  Round 1 found the abstract's accuracy floor rounded the wrong way this way.
- **No citation enters a replacement unverified.** Extracted figures live in
  `comparators/REPORTED_RESULTS.md`.

## Scope of the current round

`PI_notes_2026-08-06.md` covers the abstract and the introduction. Later rounds
extend the same file or open a new dated one.
