#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --qos=comx29
#SBATCH --account=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=00:30:00
#SBATCH --job-name=smoke_tenseal
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/smoke_tenseal_%j.log
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/smoke_tenseal_%j.err
#
# HE-IFD A2 TenSEAL smoke prototype: validates the linear-accumulator
# depth-<=-3 claim from PRD section 4.3.
#
# Issue: issues/04-a2-tenseal-smoke.md
# Anchor: reports/2026-05-05_methodology_pivot.md sections 4.2 + 4.3 + 8
#         reports/2026-05-10_tdsc_rejection_action_plan.md A2 (lines 201-208)
#
# Usage:
#   sbatch jobs/smoke_tenseal.sh
#
# Notes:
#   * Conda env "he_ifd_smoke" is the canonical target name; create with the
#     minimal install:
#         conda create -n he_ifd_smoke python=3.9 -y
#         conda activate he_ifd_smoke
#         pip install tenseal numpy torch
#     If he_ifd_smoke is absent the wrapper falls back to "he_ofl" which
#     already has tenseal==0.3.16, numpy, and torch==2.3.0+cu121 installed.
#   * The smoke is CPU-bound (TenSEAL has no GPU path); the T4 GRES request
#     is for partition gating only -- nvidia-smi is logged for the record.
#   * Wall-clock budget: <30 min on a single T4 node per PRD section 8
#     ("smoke run completes in < 30 min wall-clock on a single T4").
#   * GOLDEN RULE: never run prototypes/cfd_tenseal_smoke.py on the login
#     node. Always via this sbatch wrapper.

set -euo pipefail

REPO_ROOT="/scratch/hkanpak21/HE_IFD"
RESULTS_DIR="${REPO_ROOT}/results"
mkdir -p "${RESULTS_DIR}"

CONDA_BASE="/opt/ohpc/pub/compiler/conda3/latest"
# shellcheck disable=SC1091
source "${CONDA_BASE}/etc/profile.d/conda.sh"

# Prefer the dedicated smoke env per issue spec; fall back to he_ofl which
# already vendors tenseal==0.3.16 + numpy + torch.
if conda env list | grep -qE "^he_ifd_smoke[[:space:]]"; then
    conda activate he_ifd_smoke
else
    echo "[smoke_tenseal] he_ifd_smoke not found, falling back to he_ofl"
    conda activate he_ofl
fi

echo "[smoke_tenseal] job ${SLURM_JOB_ID:-local} on $(hostname)"
echo "[smoke_tenseal] python: $(which python)"
echo "[smoke_tenseal] tenseal: $(python -c 'import tenseal; print(tenseal.__version__)')"
nvidia-smi -L || true

cd "${REPO_ROOT}"
exec srun python -u prototypes/cfd_tenseal_smoke.py \
    --logn 14 --scale 40 --N 10 --probe 5000 --C 10
