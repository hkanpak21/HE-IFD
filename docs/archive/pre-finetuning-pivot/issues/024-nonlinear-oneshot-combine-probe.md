# 024 — Local probe: can a non-linear ONE-SHOT server combine beat flat averaging?  [AFK, LOCAL CPU]

> **STATUS: ✅ DONE** (2026-05-30) — non-linear combine probe landed. Paired (within-partition) result: `second_moment`/RMSProp and the deep / depth-2 combines all **lose** to `weight_avg` (mean ≈ −8pp, range +8 to −23pp; negative in ~28/36 cells). The earlier "+22 RMSProp win" was a **non-reproducible single-run artifact** — the seed/partition lottery alone moves accuracy up to ~15pp. Feeds 025 + 026.

**The question.** Within strict one-shot (clients compute their K-step trajectory from the shared basin θ₀, upload **once** — cumulative Δᵢ *and* per-step deltas; Phase-0 alignment is free and does NOT count as a round; **no second client↔server communication**), the linear server combine θ₀+Σwᵢ·Δᵢ telescopes to a weighted average and leaves a large heterogeneity gap (probe 023: −11 to −28 pt vs centralized at α=0.05). **Does any NON-LINEAR server combine of the same one-shot uploads beat the flat average?** And is any winner low-depth enough for CKKS?

## What to build + run (extend `results/local_results/`)

Reuse the 023 setup verbatim (MNIST, 784→200→10 MLP, CPU, K=100, N∈{1,5,10}, α∈{0.05,0.1,0.5,1.0}, basin∈{probe,no-probe}, seeds {42,123}). For each cell, run each client's local trajectory ONCE from θ₀ to get {Δᵢ} and {dᵢ⁽ᵏ⁾}, then apply each of these **one-shot server combines** and report final test acc. All in plaintext.

**Schemes (be exhaustive; annotate HE-depth for each):**
1. `weight_avg` — θ₀+Σwᵢ·Δᵢ (baseline, depth-1 linear). [reference]
2. `mag_weighted` — public-scalar reweight: θ₀+Σ (wᵢ‖Δᵢ‖ / Σⱼwⱼ‖Δⱼ‖)·Δᵢ. **Depth-1 / HE-feasible** (‖Δᵢ‖ sent as a public scalar). Still linear → telescopes; include to show a depth-1 reweight doesn't escape.
3. `sign_majority` — coordinate-wise: θ₀ + lr·sign(Σwᵢ·sign(Δᵢⱼ))·mean|Δⱼ| (signSGD-style). [deep: sign/compare]
4. `norm_normalized` — average of unit-normalized displacements: θ₀ + (mean‖Δ‖)·Σwᵢ·(Δᵢ/‖Δᵢ‖). [deep: per-vector division]
5. `agreement_gated` — θ₀ + g⊙(Σwᵢ·Δᵢ), gⱼ=(Σwᵢ·Δᵢⱼ)²/(ε+Σwᵢ·Δᵢⱼ²) ∈[0,1] (downweights canceling coords). [deep: ratio]
6. `second_moment` — RMSProp-style per-coord precond: θ₀ + (Σwᵢ·Δᵢ)/√(ε+Σwᵢ·Δᵢⱼ²). [deep: sqrt/division]
7. `coord_trimmed_mean` — per-coordinate trimmed mean across clients (drop top/bottom). [deep: sort/compare]
8. `consensus_proj` — project each Δᵢ onto the mean direction, average the projections + a residual fraction. [deep: dot/division]
9. **(genuinely-low-depth candidates)** `poly_gate_d2` — a DIVISION-FREE depth-2 gate: θ₀ + (Σwᵢ·Δᵢ) − c·(Σwᵢ·Δᵢ)⊙(meansqⱼ) or similar pure-polynomial form the agent designs to mimic agreement-gating WITHOUT a denominator. Try 1–2 such depth-2 polynomial variants — these are the only ones that could be both non-linear AND CKKS-cheap.

For reference also run `sync_sgd` (multi-round) and `centralized` as the ceilings (already in 023).

## Acceptance
- [ ] `results/local_results/run_nonlinear.py` runs locally on CPU, reusing the 023 client-training, applying all combines; writes `nonlinear_results.csv` + a `nonlinear_combines.png` (final-acc vs scheme, faceted by α at N=10, probe+no-probe).
- [ ] A table: for each scheme × α (N=10), final acc vs `weight_avg` and vs `centralized`, with a **HE-depth column** (depth-1 / depth-2 / deep) per scheme.
- [ ] `results/local_results/README.md` updated with the verdict: does ANY non-linear one-shot combine beat `weight_avg` under heterogeneity? If yes, which, by how much, and is it low-depth (the `poly_gate_d2` / `mag_weighted` rows are the only HE-cheap ones)? If only deep ones win, say so plainly.

## Hard boundaries
- Write only under `results/local_results/`. May reuse the local venv from 023 (`/tmp/probe023`) or recreate. Run locally (Mac CPU — allowed). Do NOT modify src/, mia/, fhe/, paper, other results. No git push/commit/sbatch/ssh.

## Report
1. The combines implemented + the depth annotation per scheme.
2. Headline: best non-linear combine vs weight_avg vs centralized at α=0.05 (N=10), probe + no-probe.
3. Verdict: is there a low-depth non-linear one-shot combine that beats averaging? Implication for the method.
