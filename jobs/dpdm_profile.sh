#!/usr/bin/env bash
#SBATCH --job-name=dpdm_profile
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --time=12:00:00
#SBATCH --gres=gpu:1
#SBATCH --mem=24G
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/dpdm_profile_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/dpdm_profile_%j.err
#
# HE-IFD A5 profiling micro-task: single-client DP-DDPM on one T4.
# Issue: issues/22-a5-dpdm-profiling.md
# Reference: Dockhorn et al. "Differentially Private Diffusion Models" (TMLR 2023).
# Upstream pinned in comparators/dpdm_upstream/COMMIT.txt.
#
# Usage:
#   sbatch jobs/dpdm_profile.sh
#
# Notes:
#   * Conda env "he_ifd_gamma" assumed; create it if missing before running. The
#     upstream requirements.txt pins torch==1.11.0+cu113 plus a custom Opacus
#     fork (timudk/opacus_dpdm @ dpdm); install both inside he_ifd_gamma:
#         conda create -n he_ifd_gamma python=3.9 -y
#         conda activate he_ifd_gamma
#         pip install -r comparators/dpdm_upstream/requirements.txt
#   * The wrapper hard-codes batch_size=2048, max_physical_batch_size=256,
#     n_splits=8 to fit T4 16 GB; upstream defaults assume 8 x A100 80 GB.
#   * The wrapper exits early on FID plateau (no improvement > 1.0 across
#     the last 4 evaluations of fid_freq=2000 iters).
#   * 12 h SLURM cap = wall-clock cap baked into the wrapper. If the cap
#     is hit before plateau, the conditional-path decision still proceeds:
#     h > 8 -> CIFAR-100/SVHN exclusion per PRD section 9.5.2.

set -euo pipefail

REPO_ROOT="/scratch/hkanpak21/HE_IFD"
RESULTS_DIR="${REPO_ROOT}/results"
mkdir -p "${RESULTS_DIR}"

# Conda activation. Mirror the path used by sibling comparator wrappers
# (see jobs/cfd_v2_comp_fedmd.sh).
CONDA_BASE="/opt/ohpc/pub/compiler/conda3/latest"
# shellcheck disable=SC1091
source "${CONDA_BASE}/etc/profile.d/conda.sh"
conda activate he_ifd_gamma

echo "[dpdm_profile] job ${SLURM_JOB_ID:-local} on $(hostname)"
echo "[dpdm_profile] python: $(which python)"
nvidia-smi || true

cd "${REPO_ROOT}"
exec python prototypes/dpdm_profile.py
