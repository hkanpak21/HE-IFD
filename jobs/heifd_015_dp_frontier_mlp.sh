#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --job-name=heifd_015_mlp
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_015_dp_frontier_mlp/runs/mlp_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_015_dp_frontier_mlp/runs/mlp_%j.err
#
# Issue 015 — DP-ε frontier sweep on from-scratch MLP / MNIST.
#
# The averaging-variant DP claim (methodology §7) lives on a frontier: we need
# the ε panel {0.5, 2, 8, 32, ∞} at fixed Kpc=20, plus a Kpc panel {1, 5, 20}
# at ε ∈ {2, 8}, to show whether the frontier flattens from ε ≈ 2 onward as
# claimed. epsinf maps to σ=0 (raw_union-equivalent with the DP machinery set
# to zero noise — the sanity reference).
#
# parse_method already handles every token in the panel below (verified by
# tracing each token through _extract_eps / _extract_int_after — eps0.5 keeps
# its decimal via [0-9.]+, epsinf -> dp_sigma σ=0). No src/ change was needed.
#
# Grid: mlp_mnist × N{10} × α{0.05,0.3,1.0}
#       × methods{ dp_avg_eps0.5_K20, dp_avg_eps2_K20, dp_avg_eps8_K20,
#                  dp_avg_eps32_K20, dp_avg_epsinf_K20,        (ε sweep @ Kpc=20)
#                  dp_avg_eps2_K1, dp_avg_eps2_K5,             (Kpc sweep @ ε=2)
#                  dp_avg_eps8_K1, dp_avg_eps8_K5 }            (Kpc sweep @ ε=8)
#       × seeds{42,43,44}  = 9 × 1 × 3 × 3 = 81 cells.
#
# mlp_mnist cells are fast (teacher_epochs=5, linear MLP on 28×28); 81 cells fit
# comfortably in one ≤3h job, so no SLURM array is used. The sweep is resumable
# — re-submitting skips cells whose JSON already records status=success
# (see src/sweep.py), so a wall-clock death resumes rather than restarts.
#
# MNIST is pre-cached under data/MNIST/ (download=False); no pretrained weights
# needed, no login-node prefetch required.

set -euo pipefail
REPO=/scratch/hkanpak21/HE_IFD
CASE=heifd_015_dp_frontier_mlp
mkdir -p "${REPO}/results/${CASE}/runs"
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
cd "${REPO}"
echo "[015 mlp] job ${SLURM_JOB_ID:-?} on $(hostname)"

exec srun python -u -m src.sweep \
    --backbones mlp_mnist \
    --Ns 10 \
    --alphas 0.05,0.3,1.0 \
    --methods dp_avg_eps0.5_K20,dp_avg_eps2_K20,dp_avg_eps8_K20,dp_avg_eps32_K20,dp_avg_epsinf_K20,dp_avg_eps2_K1,dp_avg_eps2_K5,dp_avg_eps8_K1,dp_avg_eps8_K5 \
    --seeds 42,43,44 \
    --K "${HEIFD_K:-300}" \
    --case "${CASE}" \
    --results-root "${REPO}/results" \
    --data-root "${REPO}/data" \
    --cache-root "${REPO}/cache"
