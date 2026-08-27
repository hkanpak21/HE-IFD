# GATES: the technical report privacy work, 2026-08-27

Acceptance ledger, written before the work and closed after it. The unlazy
scripts are not installed on this machine, so every CHECK below is a command that
runs in this repo and every result was obtained by running it.

Scope as it ended. The first half of the session produced propositions. Halil
then went AFK with the instruction to improve the technical report, so the
report-only propositions were applied. The submission was not touched.

## Result

11 gates. 11 met. 0 abandoned. 0 deferred.

| id | gate | check | result |
| --- | --- | --- | --- |
| G1 | Every report edit names its location and the record or citation behind every number | by hand, recorded in `TR-propositions-2026-08-27.md` | met |
| G2 | Every citation is verified against a fetched record, not recall | two reader agents, arXiv, dblp, ACM, USENIX, IEEE, PMLR | met |
| G3 | The client-to-client analysis names a prior work for each step | reconstruction, membership, defence, all cited | met |
| G4 | No number enters without a file in `results/` holding it | recomputed from the CSVs on 2026-08-27 | met |
| G5 | The improvement analysis covers every section, not only Security and Experiments | all eight section files read | met |
| G6 | The submission is unchanged | `scripts/gates.sh` gates 1, 2, 3, 5, 7, 8 | met |
| G7 | The propositions say what needs compute and what does not | section 4 of the propositions file | met |
| G8 | No paragraph renders twice in either document | `scratchpad/dupscan.py report` and `paper` | met |
| G9 | Both documents compile with no undefined citation, reference, or overfull box | `scripts/gates.sh` gate 6 | met |
| G10 | Nothing is rewritten in either view | `scripts/gates.sh` gates 3 and 3b | met |
| G11 | Every new report paragraph carries a dated reason | `docs/paper/.subseq-allow` | met |

## The evidence

CHECK G6: `bash scripts/gates.sh`, submission columns, against the baseline taken
before any edit.
EXPECT: identical on every measure.
RESULT: 10 pages then and now. 6583 prose words then and now. 0 rewritten then and
now. 41 bibliography keys then and now. 4 lint errors then and now. `fig_protocol`
5 of 45 spans out of tolerance then and now. Met.

CHECK G8: `python3 <scratchpad>/dupscan.py report` and the same on `paper`.
EXPECT: `0 duplicate paragraph pair(s)` in both.
RESULT: 31 before, 0 after, in the report. 0 in the submission throughout. Met.
Positive control: the detector found 31 real cases before the fix and each was
confirmed by reading the source, so a zero afterwards is not a broken detector.

CHECK G9: `grep -c 'Overfull' docs/paper/main-tr.log`.
EXPECT: 0.
RESULT: 1 after the defence table was first added, caused by a table declaring
nine columns and using eight. Restructured to eight columns with the majority
shares moved into the caption. 0 after. Met.

CHECK G10: `scripts/check_subseq.py --base cc1df39` in both views.
EXPECT: `REWRITTEN 0`.
RESULT: 0 in the submission at every point. In the report, 10 then 8 new
paragraphs were flagged as written, each was read, each was given a dated reason
in `.subseq-allow`, and the final run reports 0 with 39 accepted. Met.

CHECK G4: every quoted figure recomputed from its CSV.
RESULT: the extraction figures reconcile with `extraction_budget/results.csv`.
The defence figures did **not** reconcile with the numbers in
`plan-submission-2026-08-23.md`, which mixes two budgets and carries a baseline
that is not in the file. The report uses the file. Met, and the discrepancy is
recorded.

CHECK G2: every proposed key fetched.
RESULT: all sixteen resolved. One claim I had flagged as a possible
misattribution, the `tramer2016stealing` figure in `experiments.tex`, was
confirmed **correct** against the USENIX proceedings. One citation I had
*proposed* was found **wrong** and withdrawn before use: Lowd and Meek is a
binary-classifier result and does not cover a multiclass head. Two numbers the
submission attributes to `nasr2019comprehensive` were found misattributed, and
are recorded as a decision for Halil rather than changed. Met.

## Abandoned

None.

## Deliberately out of scope, and why

Applying anything to `docs/paper/main.tex` or to text that renders in the
submission. Halil's order of work is the report first, then the submission.

Running the membership sweep on VALAR. It needs the `mia/` rewire and is a
session of its own.

The three claim changes in section 3 of the propositions file. Each alters a
statement the PIs have read, and two of them alter a security claim.
