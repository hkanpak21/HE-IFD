# 06. A6.1 — Vendor Co-Boosting comparator

Status: ready-for-agent
Label: AFK
Priority: P3 (tier-1 no-DP comparator; reusable from May-5)
Action-plan: A6.1 (folded into A4.1)
PRD-section: §3.4 (Co-Boosting as privacy-unaware ceiling)

## Parent

Action plan A6 row "Co-Boosting" (line 165) + PRD §3.4 (lines 124–127).

## What to build

Wrap Co-Boosting (Dai et al. ICLR 2024, `dai2024coboosting`) into our jobs harness. The May-5 implementation at `experiments/coboost_baseline.py` (referenced in action plan line 165 — likely in the legacy archive at `legacy/`) is the reuse base. Two artefacts:

1. **`comparators/coboosting/`** — vendored or pinned implementation. Approach:
   - If May-5's `experiments/coboost_baseline.py` is reusable as-is, copy to `comparators/coboosting/coboost_baseline.py` with no modifications and record provenance in `comparators/coboosting/COMMIT.txt`.
   - Else port from upstream `https://github.com/yuanyuanyuan/Co-Boosting` (or whichever commit the May-5 code was based on); pin commit hash in `COMMIT.txt`.
2. **`jobs/cfd_v2_comp_coboost.sh`** — sbatch wrapper that runs Co-Boosting on our (dataset, α, N=10, seed) grid cell. Arguments: `--dataset $1 --alpha $2 --seed $3`.

Co-Boosting is plaintext; no CKKS involvement. Privacy framing per PRD §3.4: "the privacy-unaware ceiling: the strongest unencrypted one-shot baseline."

## Acceptance criteria

- [ ] `comparators/coboosting/` exists with the implementation and `COMMIT.txt`.
- [ ] `jobs/cfd_v2_comp_coboost.sh` runs end-to-end on MNIST α=0.3 N=10 seed=42 as a smoke check.
- [ ] Smoke output (final student accuracy) written to `results/coboost_smoke_<job_id>.json`.
- [ ] No login-node execution.

## Blocked by

- Issue 02 (Ralph scaffold; jobs harness conventions need to be set).

## References

- Action plan A6 (lines 342–363), A4.1 (lines 244–316).
- PRD §3.4 (lines 124–127).
- Upstream: `https://github.com/yuanyuanyuan/Co-Boosting` (Co-Boosting ICLR 2024).
- Bibkey: `dai2024coboosting`.

## Comments

### 2026-05-17 — wave-3 agent: vendor + wrapper landed; smoke deferred

- **Upstream clone**
  - URL: `https://github.com/rong-dai/Co-Boosting` (the prompt's `yuanyuanyuan/Co-Boosting` 404s; canonical repo is `rong-dai/Co-Boosting`, verified via GitHub search API on 2026-05-17).
  - Clone date: 2026-05-17.
  - Pinned SHA: `b95d715ebf04307192094160e49334d3ab7519f0` (only commit on the upstream's `main` — author published as a single squashed upload 2024-02-22).
  - Tree was cloned untouched into `comparators/coboosting/`; pin recorded at `comparators/coboosting/COMMIT.txt`.
- **Entry point wrapped**
  - Co-Boosting is a two-stage pipeline. Stage 1: `fl_pretrain.py` trains `--num_users=10` client teachers under `partition=dirichlet beta=<alpha>`. Stage 2: `datafree_kd.py --method co_boosting` runs generator + ensemble distillation, reading the stage-1 pickle via `--fl_model <identity>`. Both stages run in the same SLURM job inside `jobs/cfd_v2_comp_coboost.sh`.
- **Path-patching note (decided unilaterally)**
  - Upstream hard-codes IO under `/gdata/dairong/{Co_boosting,Co_Boosting,fedsam}` in 10+ places. The wrapper preserves the vendored tree as-is and, at job time, copies it into per-job scratch and runs `sed -i 's|/gdata/dairong|<JOB_SCRATCH>/gdata/dairong|g'` on the work-copy `.py` files. This keeps `comparators/coboosting/` pristine for provenance while letting the smoke run on Valar without `/gdata` write access.
- **Conda env expected**
  - `he_ifd_comparators` (proposed-new; does NOT yet exist on Valar — `conda env list` confirms). User should create it before first submission, e.g. `conda create -n he_ifd_comparators --clone he_ofl && conda activate he_ifd_comparators && pip install --no-deps tqdm`. Upstream needs only stock pytorch + tqdm; `he_ofl` (torch 2.3.0+cu121) is a suitable base per memory `valar`.
- **Smoke command (deferred, not submitted)**
  - `sbatch jobs/cfd_v2_comp_coboost.sh MNIST 0.3 42`
  - Final-accuracy + DP-accountant (null for plaintext) JSON lands at `results/coboost_smoke_${SLURM_JOB_ID}.json`.
  - Sanity expectation: `final_student_acc ≥ 0.9` on MNIST per issue's AC framing of "smoke check".
- **Smoke status: DEFERRED**
  - Reason 1 (golden rule): cannot run Python on login node.
  - Reason 2 (issue 03): QoS=`comx29` escalation is HITL; cannot self-confirm submission access from this agent.
  - Reason 3 (env): `he_ifd_comparators` does not exist yet; first submission needs human-created env.
- **Acceptance check (per prompt)**
  - [x] `comparators/coboosting/COMMIT.txt` exists with the SHA + URL + clone date.
  - [x] `jobs/cfd_v2_comp_coboost.sh` exists, executable, has all required `#SBATCH` headers (partition, qos, account, gres=gpu:1, time=00:30:00, mem=16G, output, error), references absolute paths.
  - [x] `bash -n jobs/cfd_v2_comp_coboost.sh` returns 0.
  - [ ] Smoke acc ≥ 0.9 — cannot satisfy from login node; carried to HITL once issue 03 unblocks.
- **Status decision**
  - Issue stays in `issues/` (NOT moved to `issues/done/`) because the runtime AC is unmet pending HITL submission.

