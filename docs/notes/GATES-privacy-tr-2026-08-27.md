# GATES: the technical report privacy propositions, 2026-08-27

Acceptance ledger for the work requested on 2026-08-27. Written before the work,
per the completion discipline. The unlazy scripts are not installed on this
machine, so every CHECK below is a command that runs in this repo as it stands,
and every gate is verified by running it and pasting the result.

Scope. The deliverable is a set of proposed edits to the technical report,
`docs/paper/main-tr.tex` and the shared sections, each one reviewable and each
one backed by a record or a citation. Nothing is applied to the submission.
Nothing is applied to any `.tex` file until Halil accepts the propositions.

| id | gate | status |
| --- | --- | --- |
| G1 | Every proposed technical-report edit names its location, its exact proposed text, and the record or citation behind every number in it | met |
| G2 | Every citation proposed for `refs.bib` is verified to exist with the right venue and year, by fetching the record, not by recall | met |
| G3 | The client-to-client analysis names a prior work for each of its three steps, the reconstruction, the membership test, and the defence | met |
| G4 | No number enters a proposition without a file in `results/` that holds it | met |
| G5 | The paper-improvement analysis covers every section of the submission, not only Security and Experiments | met |
| G6 | Nothing is written into any `.tex` file this session | met |
| G7 | The propositions state which of them need compute before they can be written, and which are writable from records that exist today | met |

CHECK G2: every proposed key resolves to a real paper.
  Verified by two reader agents fetching arXiv, dblp, ACM, USENIX, and IEEE
  records on 2026-08-27. Items that failed verification are listed as unusable
  in the propositions file and are not proposed for `refs.bib`.

CHECK G4: grep each proposed number against results/.
  `grep -rn "<number>" results/` for every figure quoted.
  EXPECT: a hit in a `.csv` or `.json` under `results/`.

CHECK G6: `git status --porcelain docs/paper/`
  EXPECT: empty.

CHECK G7: the propositions file carries a table splitting writable-now from
  needs-compute.
  EXPECT: the table exists and every proposition appears in exactly one row.

## Abandoned

None.

## What is deliberately not in scope

Applying any edit to `main-tr.tex` or to the submission. Running the membership
sweep on VALAR. Both wait on Halil.
