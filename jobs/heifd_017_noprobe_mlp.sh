#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --job-name=heifd_017_noprobe
#SBATCH --array=0-7
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_017_noprobe_mlp/runs/noprobe_%A_%a.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_017_noprobe_mlp/runs/noprobe_%A_%a.err
#
# Issue 017 — no-probe DP-common-basin FULL headline grid on MNIST/MLP.
#
# CENTRAL Phase-II experiment (elevated by the user): the weak-alignment /
# low-leak regime. The labelled public probe is REMOVED entirely; θ₀ is warmed
# only on the (DP-noisy or raw-union) per-(client, class) prototypes — a WEAK
# θ₀. The thesis to demonstrate: the HE-secure K-step distillation lifts the
# global model well above this weak θ₀ (large acc − θ₀) and above the average
# client teacher (acc ≥ mean_teacher), with m4_ood > 0 — i.e. distillation
# carries the learning while alignment leaks minimally.
#
# The with-probe baselines (dp_avg_eps2_K20, raw_union_K20) are run in the SAME
# grid so the COST OF REMOVING THE PROBE is a direct per-(α, ε) Δacc between the
# with-probe row and its no-probe twin.
#
# Grid: mlp_mnist × N{1,5,10,20,50} × α{0.01,0.05,0.1,0.3,1.0}
#       × methods{noprobe_dp_avg_eps2_K20, noprobe_dp_avg_eps8_K20,
#                 noprobe_raw_union_K20,                        (the 3 no-probe)
#                 dp_avg_eps2_K20, raw_union_K20}              (the 2 with-probe)
#       × seeds{42,43,44}  = 5 × 5 × 5 × 3 = 375 cells.
#
# Chunking: SLURM job array (--array=0-7 → 8 chunks) with round-robin striping
# via sweep.py's --num-chunks / --chunk-index. ~47 cells/chunk; the heavier
# N=50 cells are spread across all 8 chunks (round-robin) rather than
# concentrated. mlp_mnist cells are light (from-scratch MLP on 784-d MNIST), so
# a chunk stays well under the 3h VALAR cap. Sweep is resumable — re-submitting
# skips cells whose JSON already records status=success (see src/sweep.py).
#
# N=1 is the degenerate single-client sanity floor (no-probe θ₀ ≈ that one
# client's prototype warmup). MNIST is pre-cached under data/MNIST/
# (download=False); no pretrained weights, no login-node prefetch required.
#
# Run heifd_017_noprobe_verify.sh FIRST (10-cell smoke) and confirm
# status=success before launching this grid.

set -euo pipefail
REPO=/scratch/hkanpak21/HE_IFD
CASE=heifd_017_noprobe_mlp
mkdir -p "${REPO}/results/${CASE}/runs"
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
cd "${REPO}"
echo "[017 noprobe] job ${SLURM_ARRAY_JOB_ID:-?} task ${SLURM_ARRAY_TASK_ID:-0}/${SLURM_ARRAY_TASK_COUNT:-1} on $(hostname)"

exec srun python -u -m src.sweep \
    --backbones mlp_mnist \
    --Ns 1,5,10,20,50 \
    --alphas 0.01,0.05,0.1,0.3,1.0 \
    --methods noprobe_dp_avg_eps2_K20,noprobe_dp_avg_eps8_K20,noprobe_raw_union_K20,dp_avg_eps2_K20,raw_union_K20 \
    --seeds 42,43,44 \
    --K "${HEIFD_K:-300}" \
    --case "${CASE}" \
    --results-root "${REPO}/results" \
    --data-root "${REPO}/data" \
    --cache-root "${REPO}/cache" \
    --num-chunks "${SLURM_ARRAY_TASK_COUNT:-8}" \
    --chunk-index "${SLURM_ARRAY_TASK_ID:-0}"
