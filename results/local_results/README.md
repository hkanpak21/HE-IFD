# Local probe (issue 023): how should client updates be combined?

**Status:** done (2026-05-30). Exploratory **local Mac CPU** probe — NOT a VALAR
sweep, NOT part of the headline grid. MNIST, small MLP (784→200→10), plain
supervised SGD (no distillation), K=100 steps, batch 64, seeds {42, 123}.
Everything here is self-contained and does **not** import `src/`.

## The question

The HE-IFD server aggregation is θ⋆ = θ₀ + Σᵢ wᵢ·Δᵢ with Δᵢ = θᵢ⁽ᴷ⁾ − θ₀
(`src/aggregate.py:48`). Since Σᵢ wᵢ = 1 this **telescopes to a sample-weighted
average of the clients' FINAL models**, Σᵢ wᵢ·θᵢ⁽ᴷ⁾ — it never visits a joint
trajectory. We compare it against a **synchronized trajectory** that mimics one
SGD run over pooled client mini-batches (combine per-step client updates at the
shared running point — this does NOT telescope), to learn whether a real
trajectory beats weight-averaging, by how much, at which α, and whether the
shared basin (probe) matters differently for each. Distillation is deliberately
removed so we isolate the *aggregation* question; distillation is a separate
axis and is not tested here.

## The schemes (all from a shared θ₀)

| | scheme | what it does | rounds |
|---|---|---|---|
| **A** | `weight_avg` | each client runs K local SGD steps → θᵢ⁽ᴷ⁾; θ⋆ = θ₀ + Σᵢ wᵢ(θᵢ⁽ᴷ⁾−θ₀). **This is the current HE-IFD aggregation.** | **one-shot** |
| **B** | `stepsum` | telescoping control: θ⋆ = θ₀ + Σ_k Σᵢ wᵢ·dᵢ⁽ᵏ⁾ (own-trajectory step deltas). Must equal A. | one-shot |
| **C** | `sync_sgd` | for k=1..K every client computes ONE minibatch gradient **at the shared point θ⁽ᵏ⁻¹⁾**, sample-weighted-average them, take one step. | **K rounds** |
| **D** | `fedavg_Estep` | E=5 local steps per round, then sample-weighted model average; R=20 rounds (R·E=K). Bridges A↔C. | 20 rounds |
| **E** | `centralized` | plain SGD on the pooled data from θ₀ (oracle upper bound). | — |

`weight_avg` trajectory in the figure = test acc of the *partial* telescoped
aggregate θ₀ + Σᵢ wᵢ(θᵢ⁽ᵏ⁾−θ₀) at each step k (what the server would decrypt if
all clients stopped at k), so A and C share one step axis. The k=K point is the
true one-shot deliverable. `basin`: **probe** = θ₀ warmed on ≈100 shared
class-balanced labelled samples; **no-probe** = a single shared random θ₀.

## Headline numbers (final test acc %, mean over seeds 42 & 123)

**N = 10**

| basin | α | A weight_avg | C sync_sgd | E centralized | D fedavg E5 | θ₀ | **C − A** |
|---|---|---|---|---|---|---|---|
| probe | 0.05 | 76.4 | **89.3** | 87.5 | 86.7 | 78.1 | **+12.9** |
| probe | 0.1 | 75.2 | **89.3** | 88.1 | 86.8 | 78.1 | **+14.2** |
| probe | 0.5 | 86.5 | 89.0 | 87.3 | 88.9 | 78.1 | +2.5 |
| probe | 1.0 | 87.9 | 89.3 | 86.5 | 88.8 | 78.1 | +1.4 |
| no-probe | 0.05 | 58.6 | **88.7** | 86.6 | 85.5 | 11.0 | **+30.1** |
| no-probe | 0.1 | 60.6 | **88.8** | 87.6 | 85.8 | 11.0 | **+28.2** |
| no-probe | 0.5 | 83.1 | 88.5 | 85.5 | 88.7 | 11.0 | +5.4 |
| no-probe | 1.0 | 86.7 | 88.5 | 85.5 | 88.4 | 11.0 | +1.8 |

**N = 5** (C−A): probe {0.05:+14.6, 0.1:+13.0, 0.5:+2.3, 1.0:+1.4};
no-probe {0.05:**+42.1**, 0.1:+29.2, 0.5:+5.5, 1.0:+3.4}.
**N = 1** (no heterogeneity): all schemes ≈ 86–88%, C−A ≈ +0.8 (sanity: with one
client there is nothing to aggregate, so the schemes coincide).

**Telescoping (A ≈ B):** confirmed exactly. `weight_avg` vs `stepsum` final-acc
difference = **0.00e+00** across all 36 cells; max per-parameter difference of
the two aggregates = **3.7e-07** (float32 round-off only). A and B are the same
operation, as the math says.

## Verdict

**Yes — a synchronized trajectory clearly beats one-shot weight-averaging, and
the advantage is exactly the heterogeneity regime the method cares about.**
`sync_sgd` (C) reaches ≈ 88–89% essentially independent of α, N, or basin, while
`weight_avg` (A, the current HE-IFD aggregation) degrades sharply as label skew
rises: at the headline N=10, the gap is only +1.4 pt at α=1.0 (IID) but +12.9
pt at α=0.05 (probe) and +30 pt at α=0.05 (no-probe); at N=5 no-probe it blows
out to **+42 pt**. The probe basin helps the two schemes **very differently**:
it is nearly load-bearing for `weight_avg` (no-probe α=0.05 collapses to ~46–59%,
the probe recovers ~17–28 pt of that) but almost irrelevant for `sync_sgd`
(≤1 pt either way) — because a synchronized trajectory re-centres on the shared
model every step and never lets the clients drift into incompatible basins, so
it doesn't *need* a warm θ₀ to stay coherent. `fedavg_Estep` (D, E=5) sits
between A and C as expected, tracking C at high α but sagging toward A at the
most skewed cells. And the telescoping control B reproduces A to the bit
(diff = 0.0), empirically confirming that θ₀ + Σ wᵢΔᵢ *is* a weighted average of
the clients' finals. **Caveat for HE-IFD:** `sync_sgd` and `fedavg` are
**multi-round** (K and 20 server interactions respectively), each round a fresh
encrypted aggregation + broadcast — they are fundamentally incompatible with the
one-shot / single-encrypted-aggregation / depth-≈1 CKKS constraint that is the
paper's whole selling point. So this probe is a **diagnosis, not a drop-in fix**:
it shows that the residual gap to centralized under heterogeneity is an
*aggregation-geometry* limit of one-shot weight-averaging, not a data limit, and
that HE-IFD's defences against it must come from keeping clients in one basin
*within* the one-shot budget — i.e. exactly what the shared aligned θ₀ (Phase-0)
and bounded K-step trajectory are for. The probe's outsized effect on
`weight_avg` here is direct, quantified evidence that θ₀/basin-coherence is
doing real work in the one-shot setting (and that distillation, the separate
axis removed here, is the other lever for closing the residual α-gap without
adding server rounds).

## Files

- `run_probe.py` — the self-contained grid (CPU). Run: `python run_probe.py --seeds 42 123` (full), or `--smoke` (tiny). Writes the cell JSONs + `results.csv`.
- `make_figure.py` — builds `trajectories.png` from the seed-42 cell JSONs.
- `results.csv` — long-form: scheme, basin, N, α, seed, θ₀ acc, final acc, telescope diff.
- `cell_<basin>_N<>_a<>_s<>.json` — per cell, includes full per-step/round test-acc trajectory arrays for every scheme.
- `trajectories.png` — test-acc-vs-step per scheme, faceted by α (N=10), probe (top) / no-probe (bottom). The A-vs-C gap and its growth with skew are the headline visual.

## Design choices / notes

- Plain SGD, lr=0.1, **no momentum** (clean per-step trajectory semantics; momentum would couple steps and muddy the A-vs-C comparison).
- Trajectory eval on a 4000-image test subset every 5 steps for speed; final-acc reported on the same subset (full-10k θ₀ acc also recorded per cell). Numbers are MNIST-MLP-light, not tuned for SOTA — only the *relative* scheme ordering is the deliverable.
- Sample-weighted everything (wᵢ = nᵢ/Σnⱼ) to match `src/aggregate.py`. N=1 runs only at α=1.0 (α is meaningless with one client). Empty clients under extreme skew contribute a zero update that step.
- Total runtime ≈ 23 s for the full 36-cell × 2-seed grid on this Mac CPU.

---

# Local probe (issue 024): can a NON-LINEAR ONE-SHOT server combine beat flat averaging?

**Status:** done (2026-05-30). Extends 023 on the **same** local Mac CPU setup
(MNIST, 784→200→10 MLP, plain SGD, K=100, N∈{1,5,10}, α∈{0.05,0.1,0.5,1.0},
basin∈{probe,no-probe}, seeds {42,123}; self-contained, does **not** import
`src/`). All plaintext (to test the *idea*); HE-depth is **annotated, not
implemented**.

## The question

023 showed the linear combine θ₀+Σwᵢ·Δᵢ **telescopes to a weighted average** of
the clients' finals and leaves a large heterogeneity gap (the multi-round
`sync_sgd` fix is out of the one-shot budget). 024 stays **strictly one-shot** —
each client computes its K-step trajectory from the shared basin θ₀ and uploads
**once** (cumulative Δᵢ; Phase-0 is free, **no second client↔server round**) — and
asks: given the *same* one-shot uploads {Δᵢ}, **does any NON-LINEAR server combine
of them beat the flat average θ₀+Σwᵢ·Δᵢ under heterogeneity, and is any winner
low-depth enough for CKKS?**

## The combines (all operate on the same one-shot {Δᵢ}; m=Σwᵢ·Δᵢ, s²=Σwᵢ·Δᵢ²)

| combine | what it does | **HE depth** |
|---|---|---|
| `weight_avg` | θ₀ + m. The current HE-IFD aggregation. | **depth-1** [baseline] |
| `mag_weighted` | reweight by public scalar ‖Δᵢ‖: θ₀ + Σ(wᵢ‖Δᵢ‖/Σⱼwⱼ‖Δⱼ‖)Δᵢ. Still **linear** (reweighted average). | **depth-1** [HE-cheap] |
| `poly_gate_d2_a` | division-free gate θ₀ + m − c·(ŝ²⊙m), ŝ²=s²/s² (public-scalar rescale). One ct·ct multiply. | **depth-2** [HE-cheap] |
| `poly_gate_d2_b` | cancellation-aware gate θ₀ + m − c·m⊙v̂, v̂=(s²−m²)/s² (weighted coord variance). One ct·ct multiply. | **depth-2** [HE-cheap] |
| `sign_majority` | θ₀ + scale·sign(Σwᵢ·sign(Δᵢⱼ))·mean\|Δⱼ\| (signSGD-style). | deep [sign/compare] |
| `norm_normalized` | θ₀ + (mean‖Δ‖)·Σwᵢ(Δᵢ/‖Δᵢ‖) (unit-vector average). | deep [per-vector division] |
| `agreement_gated` | θ₀ + g⊙m, gⱼ=mⱼ²/(ε+s²ⱼ)∈[0,1] (bounded ratio; downweights cancellation). | deep [ratio] |
| `second_moment` | θ₀ + scale·m/√(ε+s²) (RMSProp-style per-coord precond). | deep [sqrt/division] |
| `coord_trimmed_mean` | per-coordinate trimmed mean across clients (drop top-1/bottom-1). | deep [sort/compare] |
| `consensus_proj` | project each Δᵢ on the mean direction u, average the projections + a residual of m. | deep [dot/division] |
| `sync_sgd` | 023 ceiling — synchronized K-round trajectory. **Out of one-shot budget.** | deep (multi-round) |
| `centralized` | 023 ceiling — SGD on pooled data. | n/a (pooled) |

The two `poly_gate_d2` variants are the **only** candidates that are both
non-linear **and** CKKS-cheap (division-free degree-2 polynomials: m and s² are
each one linear pass, the gate is one extra elementwise ciphertext·ciphertext
multiply, the s² normaliser is a *public* scalar). They are the agent-designed
attempt to mimic `agreement_gated`'s [0,1] gate **without** a denominator.

## Headline (N=10, α=0.05, final test acc %, mean over seeds 42 & 123)

| basin | `weight_avg` | best NON-LINEAR one-shot | Δ vs WA | best LOW-DEPTH one-shot | Δ vs WA | `sync_sgd` (ref) | `centralized` (ref) |
|---|---|---|---|---|---|---|---|
| **probe** | **76.4** | `poly_gate_d2_a` 78.2 (depth-2) | **+1.8** | `poly_gate_d2_a` 78.2 (depth-2) | **+1.8** | 89.3 | 87.5 |
| **no-probe** | **58.6** | `consensus_proj` 58.6 (deep) | **+0.0** | `mag_weighted` 60.6 (depth-1, *linear*) | +2.0 | 88.7 | 86.6 |

Full N=10 means and per-α Δ-vs-WA tables are in `nonlinear_results.csv`; the
faceted bar chart is `nonlinear_combines.png`.

**The "+1.8 / +2.0" wins are within seed noise**, not real. Per-seed at the
probe α=0.05 cell, `poly_gate_d2_a` is **+4.0 pt (seed 42) but −0.4 pt (seed
123)**; at no-probe it is **+2.9 (s42) but −8.4 (s123)** — the seed-to-seed swing
(≈ 4–12 pt) dwarfs the ≈ 2 pt mean margin. Across all 8 N=10 cells, no one-shot
combine beats `weight_avg` by more than +2.0 pt on average, and every one of them
*loses* in at least one cell (win audit in `nonlinear_results.csv`-derived stats:
best is `poly_gate_d2_b`, 3/8 cells > +0.5 pt, max +8.2 pt at one cell, but −1.3
to −85 pt elsewhere depending on c).

## Why the depth-2 poly gate can't win reliably (the real finding)

The division-free polynomial gate is **unbounded**, unlike the [0,1] ratio gate
it imitates. The per-coordinate disagreement ŝ²/v̂ is **heavy-tailed** (median
≈ 0.2 but max ≈ 500× the mean), so the degree-2 term c·ŝ²⊙m **detonates a handful
of coordinates** once c is large enough to gate meaningfully. A c-sweep over the 8
N=10 cells (seed 42):

| c | `poly_gate_d2_a` mean Δ / min Δ vs WA | `poly_gate_d2_b` mean Δ / min Δ |
|---|---|---|
| 0.005 | +1.5 / −1.0 | +0.8 / −0.5 |
| 0.01 (used) | −5.9 / −22.5 | +1.0 / −1.1 |
| 0.02 | −23.1 / −66.0 | −2.4 / −12.3 |
| 0.05 | −40.6 / −86.5 | −16.9 / −54.5 |

The only **safe** operating point is c ≈ 0.005–0.01, where the gate is
**indistinguishable from `weight_avg`** (mean Δ ≈ +1 pt, but min Δ < 0). To make
a polynomial gate both strong and safe you would need to *clamp* the tails — a
min/compare op, which is exactly the **depth-adding** non-polynomial primitive
the depth-2 form was built to avoid. The deep schemes that *do* bound their gate
(`agreement_gated`'s ratio ∈ [0,1], `norm_normalized`'s per-vector division) also
fail to beat `weight_avg` at α=0.05 — and several deep schemes **collapse** under
skew (`sign_majority` −19.5 pt, `second_moment` −10.7 pt, `coord_trimmed_mean`
−11.2 pt at no-probe α=0.05) because with extreme label skew the per-coordinate
sign/trim/precondition statistics are dominated by the heterogeneity, not signal.

## Verdict

**No — within the strict one-shot budget, no non-linear server combine of the
one-shot uploads reliably beats the flat weighted average under heterogeneity,
and the one combine that is low-depth enough for CKKS (the division-free depth-2
poly gate) is the clearest non-winner.** At the headline α=0.05, N=10:

- **probe:** the best one-shot of *any* depth is `poly_gate_d2_a` at +1.8 pt —
  but that margin is **inside the seed noise** (+4.0 / −0.4 across two seeds) and
  leaves a ≈ 9 pt gap to `centralized` (87.5) and ≈ 11 pt to `sync_sgd` (89.3).
- **no-probe:** the best *non-linear* combine is flat (`consensus_proj` +0.0);
  the only thing that nudges up is `mag_weighted` (+2.0 pt) — and **that is a
  depth-1 *linear* reweight, not a non-linear combine**, so it still telescopes
  to a (re-)weighted average and is again noise-level off a much lower base.
- Every deep, theoretically-richer scheme (sign vote, RMSProp precond, trimmed
  mean, agreement ratio, norm-normalisation, consensus projection) is **≤ WA** at
  α=0.05, and several **hurt** it badly under skew.

**Implication for HE-IFD.** This closes the door the 023 probe pointed at: the
residual heterogeneity gap is **not** recoverable by a cleverer *server-side
function of the one-shot uploads*. The information lost by collapsing K
independent local trajectories into a single weighted average at the end is gone
by upload time — no fixed non-linear post-hoc combine puts it back, and the only
combines that could ever be CKKS-cheap (depth-1 linear reweights; division-free
depth-2 polynomials) are precisely the ones with no headroom. So HE-IFD should
**not** add a non-linear server aggregator: the depth-1 `weight_avg` it already
uses is, empirically, on the Pareto front of {one-shot, CKKS-cheap} combines. The
levers that *do* move the heterogeneity number must act **before/within** the
one-shot budget — the shared aligned θ₀ (Phase-0), the bounded K-step trajectory
that keeps clients in one basin, and distillation (the separate axis removed here)
— **not** a fancier encrypted combine. This is a clean, reviewer-facing
justification for keeping the server op at multiplicative depth ≈ 1.

## Files (024)

- `run_nonlinear.py` — self-contained grid (CPU). Run: `python run_nonlinear.py --seeds 42 123` (full ≈ 12 s), `--smoke` (tiny), or `--figure` (rebuild the png from existing cells). Writes the `nl_cell_*.json` + `nonlinear_results.csv` + `nonlinear_combines.png`. Reuses the 023 venv at `/tmp/probe023` and data at `/tmp/probe023_data`.
- `nonlinear_results.csv` — long-form: combine, basin, N, α, seed, **he_depth**, θ₀ acc, final acc, **vs_weight_avg**, **vs_centralized** (per row).
- `nl_cell_<basin>_N<>_a<>_s<>.json` — per cell: every combine's final acc, the two ceilings, the per-client ‖Δᵢ‖, best one-shot / best low-depth picks, config.
- `nonlinear_combines.png` — final-acc bar per combine, faceted by α (N=10), probe (top) / no-probe (bottom); bar **colour = HE depth** (blue depth-1, green depth-2, red deep); dashed = `weight_avg`, dotted = `centralized`, dash-dot = `sync_sgd`, fine-dotted = θ₀.

## Design choices / notes (024)

- `poly_gate_d2` strength fixed at **c = 0.01** in the recorded grid — the most generous value that is still mostly-non-destructive for the better-behaved variant; the README c-sweep above is the evidence that **no** single c both gates meaningfully and stays safe (so this is a property of the division-free form, not a tuning miss).
- Several deep schemes are globally rescaled to `weight_avg`'s L1 magnitude (`sign_majority`, `second_moment`) so the comparison is about update *shape/direction*, not an accidental step-size change. `agreement_gated` (∈[0,1]) and `norm_normalized` set their own scale by construction.
- Ceilings `sync_sgd` / `centralized` are recomputed identically to 023 and reproduce its numbers (sanity that the shared setup is intact). They are **out of the one-shot budget** and shown only as references.
- Same plaintext-only caveat as 023: MNIST-MLP-light numbers, only the *relative* ordering of combines is the deliverable. HE depth is annotated from the operation each combine needs (linear / one ct·ct multiply / sign·sqrt·div·sort), **not** measured on a real CKKS backend.
