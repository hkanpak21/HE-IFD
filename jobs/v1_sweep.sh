#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=04:00:00
#SBATCH --job-name=v1_sweep
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/v1_he-ifd_mlp_mnist_n-sweep/runs/sweep_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/v1_he-ifd_mlp_mnist_n-sweep/runs/sweep_%j.err
#
# HE-IFD v1 N-sweep: plaintext simulation, MLP 784->128->32->10, MNIST,
# Dirichlet alpha=0.1, N in {1,2,4,8,16,32}.
#
# All Python runs under conda env he_ofl (existing; has torch + torchvision).
# GOLDEN RULE: this is the only entrypoint that runs python -- never on the login node.

set -euo pipefail

REPO_ROOT="/scratch/hkanpak21/HE_IFD"
RESULTS_DIR="${REPO_ROOT}/${V1_RESULTS_DIR:-results/v1_he-ifd_mlp_mnist_n-sweep}"
mkdir -p "${RESULTS_DIR}/runs"

source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl

cd "${REPO_ROOT}"

echo "[v1_sweep] job ${SLURM_JOB_ID} on $(hostname)"
echo "[v1_sweep] python: $(which python)"
nvidia-smi -L || true
echo "[v1_sweep] PYTHONPATH=${REPO_ROOT}"

# Default sweep:
#   Ns = 1,2,4,8,16,32
#   seeds = 42 (one seed for first run; bump to multi-seed later)
#   alpha = 0.1
#   K = 5
#   use_probe = unset (no probe) -- set V1_USE_PROBE=1 to include P in distillation
USE_PROBE_FLAG=""
if [[ "${V1_USE_PROBE:-0}" == "1" ]]; then
    USE_PROBE_FLAG="--use-probe"
fi
PYTHONPATH="${REPO_ROOT}" exec srun python -u -m src.v1.sweep \
    --Ns "${V1_NS:-1,2,4,8,16,32}" \
    --seeds "${V1_SEEDS:-42}" \
    --alpha "${V1_ALPHA:-0.1}" \
    --K "${V1_K:-5}" \
    --tau "${V1_TAU:-4.0}" \
    --probe-size "${V1_PROBE_SIZE:-5000}" \
    ${USE_PROBE_FLAG} \
    --teacher-epochs "${V1_TEACHER_EPOCHS:-30}" \
    --results-dir "${RESULTS_DIR}" \
    --cache-root "${REPO_ROOT}/cache"
