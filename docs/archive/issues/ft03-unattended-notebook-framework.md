# ft03 — Start-once unattended notebook framework  [AFK]

> **STATUS: 📥 OPEN** (2026-06-01) — the operational backbone of the pivot. The researcher starts a notebook ONCE, it asks for everything up front, then runs the whole grid to completion unattended (they sleep). Every headline/ablation experiment (ft04–ft10) is produced as one of these.

**Phase:** Foundation · **Blocked by:** ft01 (method), ft02 (datasets) for a live run; the framework itself can be built in parallel against the existing `src/`.

**Required reading:**
1. `docs/prd/he-ifd-finetuning.md` (notebook framework section — the hard requirement).
2. `CLAUDE.md` (Colab/VALAR ops; results `<case>/` convention; offline caches).
3. `src/sweep.py`, `src/protocol.py`, `src/report.py` (the grid runner + per-cell JSON + README writer the notebook drives).
4. The archived Colab notebooks `notebooks/colab_028_mia.ipynb` etc. for the clone/pull/prefetch setup pattern.

## Why

The researcher runs on Colab and will **start a task then sleep**. Interactivity must be **front-loaded into a single configuration cell**; after that the notebook must run the entire grid with **zero further interaction**, survive transient errors, and be **resumable** if the VM restarts.

## What to build (`notebooks/` + a thin `src/notebook_runner.py` helper)

1. **A reusable template notebook** `notebooks/template_finetune_sweep.ipynb` with this fixed structure:
   - **Cell 1 — Setup (no input):** clone/pull the repo, `pip install` deps, prefetch the chosen backbone weights + HF datasets into the cache (the one sanctioned download step), set offline env vars.
   - **Cell 2 — Config (THE ONLY interactive cell):** an `ipywidgets` form collecting EVERY choice — dataset(s), backbone(s), trainable unit {head,LoRA,last-N}, local step {finetune,distill}, N list, α list, K, λ-sweep on/off, alignment methods, seeds (default 42,43,44), `case` name, output dir, resume on/off — with sensible defaults and a single **"Confirm config"** button that freezes the choices to a dict. Fall back to a plain `input()`/dict block if `ipywidgets` is unavailable (headless).
   - **Cell 3 — Run (no input):** `run_unattended(config)` builds the full cell grid and executes it autonomously.
2. **`src/notebook_runner.py` — `run_unattended(config)`**:
   - Builds the grid (cartesian over the config axes), **skips cells whose `results/<case>/cell_*.json` already exists** (resume).
   - Runs each cell via `protocol.run_cell`, writing per-cell JSON immediately; on a per-cell exception, **log it and continue** (never abort the whole run for one bad cell) and record the failure in a `failures.jsonl`.
   - Prints a one-line heartbeat per cell (`[k/total] case … ok|FAIL`), periodically flushes a combined `results.csv` + the `report.py` README so partial results are visible if checked mid-run.
   - At the end writes a **summary** (cells done/failed, wall-clock, where results live) and, if a git token is configured, optionally `git add results/<case>/ && commit` so landed results survive the VM.
3. **Determinism + safety**: fixed seeds from config; no `Date.now`-style nondeterminism in cell identity; a hard per-cell timeout so one hung cell cannot stall the night.

## Acceptance
- [ ] Template notebook: Setup → single Config cell (ipywidgets + headless fallback) → Run, with **no interaction after Config**.
- [ ] `run_unattended` is resumable (skips completed cells), error-tolerant (logs + continues, `failures.jsonl`), and emits per-cell JSON + combined CSV/README + a final summary.
- [ ] A dry-run sanity (2-cell grid) demonstrates start→sleep→complete with one injected failing cell that is logged and skipped, the rest completing.
- [ ] ast.parse clean; notebook JSON valid.

## Hard boundaries
- New `notebooks/template_finetune_sweep.ipynb` + `src/notebook_runner.py`; reuse `sweep`/`protocol`/`report` unchanged where possible. Do NOT change `aggregate`/`distill`/`finetune` semantics. No `git push`/`commit`/`sbatch`/`ssh` from the agent. Mac has no torch — ast.parse + nbformat validation only.

## Report
1. The three-cell structure + how Config freezes every choice into one dict.
2. The resume + error-tolerance + heartbeat + summary mechanics.
3. The dry-run transcript showing unattended completion past an injected failure.
