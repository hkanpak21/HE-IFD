# 023 — Local probe: how should client updates be combined?  [AFK, LOCAL CPU]

> **STATUS: ✅ DONE** (2026-05-30) — 408-row local probe landed (`results/local_results/`). Verdict: the user's sequential round-robin "calculate round-k updates" trajectory **== `weight_avg` exactly** (stepsum vs weight_avg diff 4e-7); the bounded-from-shared-basin combine telescopes to a weighted average of finals — i.e. **task arithmetic**. Feeds 025 + 026.

**Why.** The current server aggregation is θ⋆ = θ₀ + Σᵢ wᵢ·Δᵢ with Δᵢ=θᵢ⁽ᴷ⁾−θ₀ (see `src/aggregate.py:48`), which since Σwᵢ=1 **telescopes to a sample-weighted average of the clients' final heads** (Σᵢ wᵢ·θᵢ⁽ᴷ⁾). We suspect this weight-averaging is why distillation adds little and the method looks like "averaging with extra steps." We want to empirically compare it against a **synchronized trajectory** that mimics one SGD run over pooled client mini-batches — applying combined per-step client updates to a shared running model — which does NOT telescope to averaging. Find out whether a real trajectory beats weight-averaging, by how much, and whether the basin (probe) matters differently for each.

## What to build + run (self-contained; do NOT depend on `src/`)

A single script `results/local_results/run_probe.py` (+ its outputs) that, on MNIST with a small from-scratch MLP (e.g. 784→200→10), CPU only, runs this grid and records full trajectories.

**Env:** create a local venv and `pip install torch torchvision` (CPU build) — this Mac currently has no torch; install it. Download MNIST via torchvision (internet OK locally). Keep training light: K≈100 steps, batch≈64, a couple of teacher/probe epochs at most.

**Axes:** N ∈ {1, 5, 10} · α ∈ {0.05, 0.1, 0.5, 1.0} (Dirichlet over labels) · basin ∈ {probe, no-probe}. probe = warm a shared θ₀ on a small (≈100-sample) shared labelled set; no-probe = a single shared random θ₀ (same seed for all clients). seed=42 (a couple of seeds if cheap).

**Aggregation schemes to compare (the core of this issue):**
- **A. `weight_avg`** (current, one-shot): each client runs K local SGD steps from θ₀ on its own data → θᵢ⁽ᴷ⁾; θ⋆ = θ₀ + Σᵢ wᵢ(θᵢ⁽ᴷ⁾−θ₀). One upload.
- **B. `stepsum`** (telescoping control): θ⋆ = θ₀ + Σ_k Σᵢ wᵢ·dᵢ⁽ᵏ⁾ with dᵢ⁽ᵏ⁾ the client's own step-k delta. Should ≈ A — include it to confirm the telescoping empirically.
- **C. `sync_sgd`** (the synchronized-trajectory / SGD-batch mimic): for k=1..K, every client computes ONE minibatch gradient **at the shared running point θ⁽ᵏ⁻¹⁾**, take the sample-weighted average of those gradients, apply one step → θ⁽ᵏ⁾. Multi-round; does not telescope.
- **D. `fedavg_Estep`** (interpolator, optional): like C but each client does E∈{5} local steps per round before averaging, for R rounds (R·E≈K). Bridges A↔C.
- **E. `centralized`** (oracle upper bound): plain SGD on the pooled data from θ₀.

For every (scheme, basin, N, α): record the **final test accuracy** AND the **per-step/round test-accuracy trajectory** (so we can see whether C climbs while A stays flat). Use distillation-free local supervised SGD throughout to isolate the aggregation question (note in the README that distillation is a separate axis).

## Acceptance
- [ ] `results/local_results/run_probe.py` runs end-to-end locally on CPU and writes per-cell JSON (incl. the trajectory arrays) + a summary `results.csv` under `results/local_results/`.
- [ ] A summary figure `results/local_results/trajectories.png`: test-acc-vs-step curves per scheme, faceted by α (at N=10, probe + no-probe), so the A-vs-C gap is visible.
- [ ] `results/local_results/README.md`: the question, the schemes, and a 1-paragraph verdict — does `sync_sgd` beat `weight_avg`, by how much, at which α, and does the probe help each differently? Confirm A≈B (telescoping).

## Hard boundaries
- New files under `results/local_results/` only. Do NOT modify `src/`, `mia/`, `fhe/`, the paper, or other results. You MAY install torch/torchvision into a local venv and RUN locally (this is a Mac CPU probe, NOT subject to the VALAR no-python rule). No `git push`/`commit`/`sbatch`/`ssh`.

## Report
1. The schemes as implemented + any design choices.
2. The headline numbers: weight_avg vs sync_sgd vs centralized, with/without probe, across N and α.
3. Verdict: does a real trajectory beat weight-averaging, and what does that imply for the one-shot/HE constraint (sync_sgd is multi-round)?
