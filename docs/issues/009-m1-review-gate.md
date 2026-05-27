# 009 — M1 review gate  [HITL]

**Milestone:** M1 · **Blocked by:** 006, 007, 008 · **Blocks:** all of M2/M3

**Required reading:** [`docs/prd/...`](../prd/he-ifd-tnse-resubmission.md), [`CLAUDE.md`](../../CLAUDE.md).

## What to build

The human checkpoint. Once the headline experiments (006 coherence ablation, 007 from-scratch, 008 pretrained) have landed, **assemble and summarize**, then **STOP for the user to parse the numbers** before any M2 (real-FHE, MIA) or M3 (paper) work begins. This is the one HITL slice in M1 — by design, so downstream effort never sits on headline numbers that might still shift.

## What to produce for the review

- A consolidated summary across `results/<case>/`: headline IID accuracy tables (from-scratch + pretrained), M3 (incentive) and M4 (OOD) findings, the alignment-strategy ablation (value vs feature-weakness × heterogeneity), the K-sweep result (does longer K help?), and the coherence-ablation outcome.
- HE-IFD numbers placed beside the DP-one-shot peers from `comparators/REPORTED_RESULTS.md` (sanity, not a polished table yet).
- A short list of anomalies / surprises / cells that look off, flagged for discussion.

## Acceptance criteria

- [ ] All M1 results present under `results/<case>/` per the convention.
- [ ] A single summary document/message covering the bullets above.
- [ ] Open questions surfaced (e.g. does M3 go negative for dominant clients? does the DP frontier flatten? did GPT-2 recover?).
- [ ] **Explicit STOP** — do not create or start M2/M3 issues until the user reviews.

## How to verify

The user reads the summary, parses the numbers, and decides what M2/M3 issues to cut. This issue closes only on the user's say-so.

## Ops

Reading/summarizing results is login-node-safe (no torch). Any re-run of a flagged cell goes through `sbatch` (≤3h).
