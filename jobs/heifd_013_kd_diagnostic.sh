#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --job-name=heifd_013_diag
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_013_kd_diagnostic/runs/diag_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_013_kd_diagnostic/runs/diag_%j.err
#
# Issue 013 — KD-dynamics diagnostic. Runs the TWO diagnostic cells that
# empirically anchor the basin-cancellation hypothesis raised by issue 008's
# θ₀ > final phenomenon at low α on resnet18/CIFAR-10:
#
#   Cell A (degrading): resnet18_cifar10 / N=10 / α=0.05 / raw_union_K20 /
#                       seed 42 / K=20  (with diagnose=True)
#   Cell B (working):   mlp_mnist        / N=10 / α=0.05 / raw_union_K20 /
#                       seed 42 / K=20  (with diagnose=True)
#
# Both cells take the issue-013 ``diagnose=True`` path through run_cell, which
# emits a CellResult.diagnostics field carrying teacher entropy, per-step Δ
# norms, pairwise-cosine matrix and per-class θ₀-vs-final accuracy. Per-cell
# JSONs land under results/heifd_013_kd_diagnostic/ (sweep-compatible filename).
#
# Requires login-node prefetch (jobs/prefetch_login.py) for the resnet18
# CIFAR-10 features (cifar10:resnet18 path); MNIST is already under data/.
# Compute nodes load offline.

set -euo pipefail
REPO=/scratch/hkanpak21/HE_IFD
CASE=heifd_013_kd_diagnostic
mkdir -p "${REPO}/results/${CASE}/runs"
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
cd "${REPO}"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
echo "[013] job ${SLURM_JOB_ID:-?} on $(hostname)"

exec srun python -u -m src.diagnose_cells \
    --case "${CASE}" \
    --results-root "${REPO}/results" \
    --data-root "${REPO}/data" \
    --cache-root "${REPO}/cache"
