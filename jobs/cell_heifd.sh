#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=03:00:00
#SBATCH --job-name=heifd_cell
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/cells/heifd_%j.log
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/cells/heifd_%j.err
#
# HE-IFD A3 single-cell wrapper.
# Issue: issues/14-a3-end-to-end-ckks-single-cell.md
#
# Args:
#   $1 dataset    (MNIST | FashionMNIST | CIFAR-10 | SVHN | CIFAR-100)
#   $2 alpha      (Dirichlet, e.g. 0.3)
#   $3 seed       (e.g. 42)
#   $4 variant    (warmstart | randominit | warmstart-no-ensemble | epsilon | gamma)
#
# Example:
#   sbatch jobs/cell_heifd.sh MNIST 0.3 42 warmstart
#
# Wall-clock: smoke (MNIST/LeNet-5, |P|=5000, E1=30, E2=200) ~30-45 min on T4.
# CIFAR-10/ResNet-8 cells run up to ~90 min.
# GOLDEN RULE: never run prototypes/heifd_train.py from the login node.

set -euo pipefail

REPO_ROOT="/scratch/hkanpak21/HE_IFD"
RESULTS_DIR="${REPO_ROOT}/results/cells"
mkdir -p "${RESULTS_DIR}"

CONDA_BASE="/opt/ohpc/pub/compiler/conda3/latest"
# shellcheck disable=SC1091
source "${CONDA_BASE}/etc/profile.d/conda.sh"
conda activate he_ofl

DATASET="${1:?dataset arg required}"
ALPHA="${2:?alpha arg required}"
SEED="${3:?seed arg required}"
VARIANT="${4:?variant arg required}"

echo "[cell_heifd] job ${SLURM_JOB_ID:-local} on $(hostname)"
echo "[cell_heifd] python: $(which python)"
echo "[cell_heifd] tenseal: $(python -c 'import tenseal; print(tenseal.__version__)')"
echo "[cell_heifd] args: dataset=${DATASET} alpha=${ALPHA} seed=${SEED} variant=${VARIANT}"
nvidia-smi -L || true

cd "${REPO_ROOT}"
exec srun python -u prototypes/heifd_train.py \
    --dataset "${DATASET}" \
    --alpha "${ALPHA}" \
    --seed "${SEED}" \
    --variant "${VARIANT}" \
    --N 10 \
    --probe 1000
