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
