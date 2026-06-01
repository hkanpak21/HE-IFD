# 007 — From-scratch headline sweep  [AFK]

> **STATUS: ⚠️ PARTIAL** (2026-05-28) — MNIST/MLP DONE; FMNIST+CIFAR-10 backbones merged but full grid not yet queued.
>
> **Part 1 — MNIST/MLP from-scratch full grid:** job array 1112402 (8 chunks). **360/360 cells, all status=success.** Headline raw_union @ α=0.05 N=50 = 0.919; near-oracle at IID. θ₀-standalone closely matches final at α=0.05 — the θ₀≥final phenomenon is pretrained-only, not from-scratch.
> **Part 2 — FMNIST + CIFAR-10 from-scratch backbones extension:** new backbones `lenet_fmnist` (LeNet-5) + `cnn5_cifar10` (CNN-5) + raw image loaders + `BACKBONES` entries + dp_avg pixel-space bridge in `protocol.py` (`7bf4407`, `915a072`). Verify job 1113571 ran:
>   - **LeNet/FMNIST sanity gate PASSES**: raw_union 0.67/α=0.05, 0.81/IID vs oracle 0.89.
>   - **CNN-5/CIFAR-10 has a 27pp IID gap to oracle** (raw_union IID 0.48 vs oracle 0.75) — under-trained at 10 teacher epochs.
> **Continuation:**
>   - LeNet/FMNIST full grid (360 cells): can queue independently *now* if desired (sbatch a wrapper analogous to `heifd_headline_fromscratch.sh` with `--backbones lenet_fmnist`).
>   - CNN-5/CIFAR-10 full grid: blocked on issue **011** (trainable layer scope) and/or **010** (KD hyperparams) settling the regime. After fix → re-verify → queue full grid.

**Milestone:** M1 · **Blocked by:** 001, 004, 005 · **Blocks:** 009

**Required reading:** [`docs/prd/...`](../prd/he-ifd-tnse-resubmission.md), [`CLAUDE.md`](../../CLAUDE.md), `comparators/REPORTED_RESULTS.md` (the DP-one-shot peers we will sit beside).

## What to build

The from-scratch headline grid — the fair, backbone-free comparison that isolates the protocol's contribution and sits in the DP-one-shot peer band:

- **Datasets / nets:** MNIST + FMNIST (LeNet-5) and CIFAR-10 (CNN-5), from scratch (no pretrained backbone).
- **Axes:** N ∈ {5, 10, 20, 50}; α ∈ {0.01, 0.05, 0.1, 0.3, 1.0}; **K-sweep** (a few values around the notebook's 300 to test saturation); alignment-strategy ablation {no-Phase0, raw-proto, DP-avg ε ∈ {0.5, 2, 8, 32}} × Kpc.
- **Metrics per cell (inline, from 005):** IID acc + M3 + M4 + standalone θ₀ acc + no-alignment baseline; 3 seeds, mean ± std.
- One `results/<case>/` per dataset, e.g. `heifd_lenet_mnist_headline`, `heifd_lenet_fmnist_headline`, `heifd_cnn5_cifar10_headline`.

## Acceptance criteria

- [ ] Full grid run for the three datasets with the axes above, 3 seeds, results under `results/<case>/`.
- [ ] Each cell reports IID + M3 + M4 + θ₀ + no-align inline (no second pass).
- [ ] Teacher cache (004) reused — no redundant teacher training across methods/K within a cell group.
- [ ] The grid is **split into ≤3-hour VALAR jobs** (cluster limit) via resumable chunked submission; a preempted/expired job resumes without recomputing finished cells.

## How to verify

Inspect `results/<case>/README.md` tables. Sanity: alignment helps most at low α; the gap shrinks toward α=1.0.

## Ops

`sbatch` only; **`--time` ≤ 03:00:00** — chunk the grid (env-var/job-array cell selection) and rely on `sweep.py` resumability. Env `he_ofl`; datasets cached (`download=False`).
