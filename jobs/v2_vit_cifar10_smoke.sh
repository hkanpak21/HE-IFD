#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --job-name=v2_vit_smoke
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/v2_he-ifd_vit_cifar10/runs/smoke_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/v2_he-ifd_vit_cifar10/runs/smoke_%j.err
#
# v2 ViT-B/16 + CIFAR-10 SMOKE TEST
#   default mode: FULL FINE-TUNE (no LoRA) -- faithful v1-method on ViT
#   Set V2_USE_LORA=1 to use LoRA mode instead.
#   N=4, seed=42, methods=M0,M1, alpha=0.1, teacher_epochs=3, K=3.

set -euo pipefail

REPO_ROOT="/scratch/hkanpak21/HE_IFD"
RESULTS_DIR="${REPO_ROOT}/results/v2_he-ifd_vit_cifar10"
mkdir -p "${RESULTS_DIR}/runs"

source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl

cd "${REPO_ROOT}"

echo "[v2 smoke] job ${SLURM_JOB_ID} on $(hostname)"
echo "[v2 smoke] python: $(which python)"
nvidia-smi -L || true

USE_LORA_FLAG=""
if [[ "${V2_USE_LORA:-0}" == "1" ]]; then
    USE_LORA_FLAG="--use-lora"
fi
PYTHONPATH="${REPO_ROOT}" exec srun python -u -m src.v2.sweep \
    --methods "${V2_METHODS:-M0,M1}" \
    --dataset "${V2_DATASET:-cifar10}" \
    --Ns "${V2_NS:-4}" \
    --seeds "${V2_SEEDS:-42}" \
    --alpha "${V2_ALPHA:-0.1}" \
    --K "${V2_K:-3}" \
    --tau "${V2_TAU:-4.0}" \
    ${USE_LORA_FLAG} \
    --rank "${V2_RANK:-8}" \
    --lora-alpha "${V2_LORA_ALPHA:-16}" \
    --weight-mode "${V2_WEIGHT_MODE:-samples}" \
    --teacher-epochs "${V2_TEACHER_EPOCHS:-3}" \
    --teacher-lr "${V2_TEACHER_LR:-5e-4}" \
    --teacher-batch-size "${V2_TEACHER_BS:-128}" \
    --distill-lr "${V2_DISTILL_LR:-5e-4}" \
    --distill-batch-size "${V2_DISTILL_BS:-128}" \
    --results-dir "${RESULTS_DIR}" \
    --cache-root "${REPO_ROOT}/cache/v2"
