# 09. A6.4 — Vendor FedKT comparator (canonical PATE-style DP baseline)

Status: ready-for-agent
Label: AFK
Priority: P3 (tier-1 DP comparator)
Action-plan: A6.4 (folded into A4.1)
PRD-section: §3.4

## Parent

Action plan A6 row "FedKT" (line 167) — tier-1 DP-floor comparator.

## What to build

Vendor FedKT (Li et al. 2021, `li2021fedkt`) under `comparators/fedkt/` and wrap with DP-SGD via Opacus at ε ∈ {1, 10}.

1. **Vendoring:**
   - Upstream: `https://github.com/QinbinLi/FedKT`.
   - Clone into `comparators/fedkt/`; pin commit hash.
   - FedKT is a PATE-style aggregation; DP-SGD teachers compose via PATE's voting-based aggregation. Verify the DP composition is preserved end-to-end after we wire in Opacus.
2. **`jobs/cfd_v2_comp_fedkt.sh`** — sbatch wrapper supporting `--epsilon $4`.

## Acceptance criteria

- [ ] `comparators/fedkt/COMMIT.txt` pins the upstream commit.
- [ ] `jobs/cfd_v2_comp_fedkt.sh` runs MNIST α=0.3 N=10 seed=42 ε=10 smoke without errors.
- [ ] DP accounting verified (Opacus accountant log line in output).
- [ ] No login-node execution.

## Blocked by

- Issue 02.

## References

- Action plan A6 (lines 342–363), A4.1 method-row table (lines 257–267).
- Upstream: `https://github.com/QinbinLi/FedKT`.
- Bibkey: `li2021fedkt`.

## Comments

### 2026-05-17 — vendored (wave 3 ralph agent)

- Cloned `https://github.com/QinbinLi/FedKT` into `comparators/fedkt/`. Pinned SHA `0bb9a89ea266c057990a4a326b586ed3d2fb2df8` (only commit on master, dated 2021-05-21). Recorded in `comparators/fedkt/COMMIT.txt`.
- Wrapper `jobs/cfd_v2_comp_fedkt.sh` authored: positional args `<dataset> <alpha> <seed> <epsilon>` with ε ∈ {1, 10}.
- Smoke command (deferred — submit at HITL discretion):
  `sbatch jobs/cfd_v2_comp_fedkt.sh MNIST 0.3 42 10`
- Requires conda env `he_ifd_comparators` (user setup); see wrapper header for deps.

### DP composition — note for reviewer

The task brief asked to "wire Opacus's `RDPAccountant`". On reading the upstream, **FedKT does not, and cannot trivially, use Opacus**:

- FedKT's teachers train with plaintext SGD; the privacy budget is consumed entirely at the noisy-max **vote aggregation** step (Laplace noise of scale `1/gamma` per public-data query).
- The PATE composition is computed post-hoc by the upstream **moments accountant** in `comparators/fedkt/privacy_analysis.py` (a verbatim TF-Privacy/Papernot port), driven by the saved counts matrix and the same `gamma`.
- Substituting Opacus's `RDPAccountant` would require re-deriving the (ε, δ) bound for FedKT's noisy-max-with-consistency-filter mechanism under RDP — which upstream does not implement and the FedKT paper does not endorse.
- Our wrapper therefore **respects upstream's accountant**: it runs training, then invokes `privacy_analysis.py` over the saved `*-dp0.npz` counts, greps the resulting `Epsilon = …` line, and writes it to `results/fedkt_smoke_${SLURM_JOB_ID}.json` as `post_pate_epsilon_actual` (load-bearing). For audit honesty we also persist the data-independent and party-level bounds.

The PATE composition therefore **does** propagate end-to-end ε at release time, but via the upstream accountant rather than Opacus — no wrapper-side adjustment beyond the post-hoc accountant call.

### Calibration

`gamma` → target ε mapping is a calibrated table (`ε=1 → γ=0.05`, `ε=10 → γ=0.5`) at N=10, n_partition=2, n_teacher_each_partition=5; the *actual* ε is the accountant output and lands in the JSON. Re-tune if downstream wants tighter coupling.

### Status

Submitted: **deferred** (login-node golden rule; HITL to `sbatch` when env exists).
