# 001 — Consolidate notebook → flat `src/` package  [AFK]

> **STATUS: ✅ DONE** (2026-05-28) — base consolidation + 3 hotfixes.
>
> Flat 10-module `src/` package merged from the notebook (`1eb9c38`); `src/v1` + `src/v2` archived. Three runtime bugs surfaced by the VALAR verify cell and patched: `load_mnist_tensors` module ref (`7e64225`), sweep skipping FAILED cells on resume (`df71076`), `data.py` torch under `TYPE_CHECKING` only (`efea247`). VALAR verify green: raw_union @ α=0.05 / mlp_mnist = 0.90 (matches colab). Foundation for everything downstream — no continuation needed.

**Milestone:** Foundation + headline (M1) · **Blocked by:** none · **Blocks:** all other M1 issues

**Required reading (you are context-zero):**
- [`docs/prd/he-ifd-tnse-resubmission.md`](../prd/he-ifd-tnse-resubmission.md) — the plan + module decomposition + interfaces.
- [`CLAUDE.md`](../../CLAUDE.md) — the method (read "The current method"), ops, repo layout.
- `results/colab_results/results_notebook.ipynb` — **authoritative implementation to port**. Key functions: `local_distill_trajectory`, `server_aggregate`, `build_probe_raw_union`, `build_probe_dp_averaged`, `run_protocol_from_init`, the Section-A/B/C runners.

## What to build

A single **flat `src/` package** (no `v1`/`v2`) that faithfully ports the notebook's protocol into the 10 modules named in the PRD: `data, backbones, teacher, phase0, distill, aggregate, evaluate, protocol, sweep, report`. One thin end-to-end path must run: partition → teachers → Phase 0 → bounded K-step distillation → linear aggregate → evaluate → `results/<case>/` report, for at least one from-scratch cell (MNIST/MLP).

Move the existing `src/v1` and `src/v2` to `archive/` (preserve provenance; do not delete).

**Faithful-port rules:** aggregation is **sample-weighted** (`wᵢ = nᵢ/Σnⱼ`), the encrypted object is the **cumulative displacement `Δᵢ = θᵢ⁽ᴷ⁾ − θ₀`** (the K-step trajectory generates it), `aggregate` uses only additive + plaintext-scalar-multiply ops (FHE-compatible by construction). Do **not** re-describe the method as "weight averaging."

`sweep.py` must be **resumable** (skip already-completed cells by reading existing per-cell JSON) and **chunkable** so a grid can be split across multiple **≤3-hour VALAR jobs** (the cluster job limit) — e.g. cells selected by env vars / job-array index.

## Acceptance criteria

- [ ] All 10 modules exist with the PRD interfaces; `python -c "import ast; ast.parse(...)"` clean (login-node-safe syntax check only).
- [ ] One from-scratch cell runs end-to-end via `sbatch` and writes a valid `results/<case>/` (README + results.csv + partition_diagnostic.jsonl + cell JSON).
- [ ] **Qualitative sanity gate** (NOT colab bit-match): at α=0.05, `raw_union` > `no_phase0`; at α=1.0 (IID), accuracy lands near the single-model ceiling.
- [ ] Aggregation is sample-weighted and provably linear (no non-linear ops in `aggregate`).
- [ ] `sweep.py` is resumable and supports chunked submission within a 3h wall-clock.
- [ ] `src/v1`, `src/v2` moved to `archive/`.

## How to verify

Submit one cell via `sbatch jobs/<case>.sh`; confirm the report appears and the sanity gate holds. Numeric reproduction of colab is **not** required — the notebook is the logic reference, not a numeric oracle (it carries the GPT-2 bug fixed in 002).

## Ops (from CLAUDE.md)

`sbatch` only; never python on the login node. Env `he_ofl`. Datasets cached under `data/` (`download=False`). Slurm `--time` ≤ 03:00:00.
