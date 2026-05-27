# 004 — Seed-keyed teacher cache + experiment fusion  [AFK]

**Milestone:** M1 · **Blocked by:** 001 · **Blocks:** 007, 008

**Required reading:** [`docs/prd/...`](../prd/he-ifd-tnse-resubmission.md), [`CLAUDE.md`](../../CLAUDE.md).

## What to build

A **seed-keyed teacher cache** in `teacher.py` so a teacher trained for one cell is reused by every other cell needing the same (dataset, backbone, client partition, seed) instead of being retrained. Cache lives under `cache/` (gitignored, regenerable from seed). Plus experiment fusion in `sweep.py`: at fixed (dataset, seed, α, N), share the client partition, the cached teachers, and the (frozen-backbone) feature cache across all alignment methods and K values in that cell group — only the genuinely new work (distillation + aggregation per method/K) reruns.

This is the cost-control lever: across the headline grid the same teachers/partitions/features are needed by {no-Phase0, raw-proto, DP-avg×ε, ...} × K — they must not be recomputed per method.

## Acceptance criteria

- [ ] Teachers are cached by a key over (dataset, backbone, partition/seed) and loaded from disk on cache hit.
- [ ] A re-run of an overlapping cell group does not retrain teachers or re-extract frozen-backbone features.
- [ ] Cache is keyed so a seed/partition change correctly invalidates (no stale reuse).
- [ ] `cache/` is gitignored.

## How to verify

Run a small two-method cell group twice; confirm (via logs/timing) the second run and the second method skip teacher training + feature extraction.

## Ops

`sbatch` only. `cache/` on VALAR scratch; never commit it.
