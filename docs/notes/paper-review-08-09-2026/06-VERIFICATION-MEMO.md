# Editor's verification memo, 2026-09-08

The five seats committed independently. Before synthesis I checked the claims
that carry the decision, against `SUBMISSION.txt` and `TECHNICAL-REPORT.txt`
directly. This memo is binding on the synthesizer: where it disagrees with a
seat, the memo governs.

## Verified true

1. **The abstract's GPU latency has no support in the submission.** The abstract
   reads "400.8 to 1468.3 s on one core, or 48.9 to 176.6 s with GPU
   acceleration". The strings `48.9` and `176.6` each occur exactly once in the
   ten pages, in that sentence. `400.8` and `1468.3` occur twice each, abstract
   and body. The word `GPU` occurs once in the whole submission, in the same
   sentence. The report carries both pairs and one mention of an H100.

2. **The query allowance Q is never given a value in the submission.** The word
   `allowance` occurs seven times. No numeric bound on Q appears. The only
   figure is in the report: holding a coalition below fidelity 0.90 at N=10
   needs Q under roughly 1.3e3 per client on AG-News and 2.2e4 on Banking77.

3. **The headline cost range cannot be reconstructed from Table I.** Section V-G
   states "A_dis - A_sel runs from 0.029 to 0.136 across the five tasks". Table I
   has no A_sel column. Subtracting the bolded servable value gives 0.010 on
   CIFAR-100 and 0.090 on AG-News, so neither endpoint of the stated range is
   reachable. The reconciling values 0.669 and 0.756 occur zero times in the
   submission.

4. **The smudging condition is absent from the submission and admitted in the
   report.** Occurrences, submission then report: `smudging` 0 then 8,
   `flooding` 0 then 3, `Micciancio` 0 then 3, `Checri` 0 then 1. The report
   states "the simulation step of theorem 1 therefore rests on a hypothesis our
   measured configuration does not satisfy", and of the recommended 2^25 value,
   "It does not meet the 2^(lambda/2) rule, and we do not claim that it does".
   The submission's Theorem 1 states IND-CPA as its only hypothesis.

5. **The serving circuit's scaling constant.** `exported head` occurs once in
   the report and zero times in the submission. The report's Scope section says
   the runs fix that constant from the exported head and that a deployment
   cannot, because the head is a ciphertext.

6. **The selection cost is report-only.** `145.4` and `7111` each occur once in
   the report and zero times in the submission.

7. **Two accuracies for one configuration.** Section V-B-a reads "Accuracy falls
   with skew, from 0.970 at alpha=1.0 to 0.789 at alpha=0.1. Longer local
   training helps. Accuracy rises with the size of the federation, from 0.803 at
   N=10 to 0.882 at N=50." Both sentences describe DBpedia at the default
   N=10, alpha=0.1, and Section V-A says every number is a three-seed mean.

8. **No bit-security level in either document.** The string `128` occurs zero
   times in the submission. Its three occurrences in the report are all the
   citation `[128]` for CryptPEFT, not a security level. Corrected 2026-09-08:
   an earlier form of this item implied the report states a level. It does not.
   Neither document states a claimed bit security, a total modulus, or a secret
   distribution for any parameter set.

## Corrected

**A_sel is tabulated, in Table II.** Two seats wrote that A_sel appears in no
table, or in no table in either document. Table II, the peer comparison on
CIFAR-10, carries an explicit A_sel column with values 0.949, 0.952, 0.950 and
0.953. The accurate statement is narrower and still damaging: **Table I**, the
five-task headline table the abstract's range is drawn from, has no A_sel
column. The synthesizer must use the narrow form.

## Provenance the panel did not have

The two PDFs under `docs/paper/` show as modified with an mtime of 12:40 on
2026-09-08. Three seats flagged this. It was the editor's own rebuild, run to
produce the extracted text the panel read, because commit 301d7a2 had changed
`security.tex` after the previous build. No seat touched the manuscript, and
the rule against it held.
