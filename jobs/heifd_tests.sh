#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --job-name=heifd_tests
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_tests/runs/tests_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_tests/runs/tests_%j.err
#
# Run the unit suite (issues 002/003) on a compute node. aggregate/phase0/data
# tests are pure-tensor; the GPT-2 regression (test_backbones.py) needs the
# pre-fetched weights + AG News, so run this AFTER jobs/prefetch_login.py.

set -euo pipefail
REPO=/scratch/hkanpak21/HE_IFD
mkdir -p "${REPO}/results/heifd_tests/runs"
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
cd "${REPO}"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONPATH="${REPO}"
echo "[tests] job ${SLURM_JOB_ID:-?} on $(hostname)"
exec srun python -m pytest tests/ -v --tb=short
