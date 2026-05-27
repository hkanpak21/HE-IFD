#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --job-name=heifd_mnist_verify
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/v1_he-ifd_mlp_mnist_verify/runs/verify_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/v1_he-ifd_mlp_mnist_verify/runs/verify_%j.err
#
# Issue 001 verification: from-scratch MNIST/MLP cell through the consolidated
# flat src/ package. Runs no_phase0 and raw_union_K20 at alpha in {0.05, 1.0},
# N=16, seed 42, K=300. This exercises the qualitative sanity gate:
#   - alpha=0.05 : raw_union_K20 > no_phase0   (alignment beats no-alignment)
#   - alpha=1.0  : acc near mean-teacher / oracle ceiling (IID)
#
# GOLDEN RULE: this sbatch wrapper is the ONLY entrypoint that runs python.
# Never run the protocol on the login node. Datasets are pre-cached (download=False).

set -euo pipefail

REPO_ROOT="/scratch/hkanpak21/HE_IFD"
CASE="${HEIFD_CASE:-v1_he-ifd_mlp_mnist_verify}"
RESULTS_DIR="${REPO_ROOT}/results/${CASE}"
mkdir -p "${RESULTS_DIR}/runs"

source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl

cd "${REPO_ROOT}"

echo "[verify] job ${SLURM_JOB_ID:-?} on $(hostname)"
echo "[verify] python: $(which python)"
nvidia-smi -L || true

# Resumable + chunkable. To split a larger grid across multiple <=3h jobs, submit
# as an array and pass --num-chunks/--chunk-index (or env NUM_CHUNKS/CHUNK_INDEX):
#   sbatch --array=0-3 jobs/he-ifd_mlp_mnist_verify.sh   # with NUM_CHUNKS=4 etc.
PYTHONPATH="${REPO_ROOT}" exec srun python -u -m src.sweep \
    --backbones "${HEIFD_BACKBONES:-mlp_mnist}" \
    --Ns "${HEIFD_NS:-16}" \
    --alphas "${HEIFD_ALPHAS:-0.05,1.0}" \
    --methods "${HEIFD_METHODS:-no_phase0,raw_union_K20}" \
    --seeds "${HEIFD_SEEDS:-42}" \
    --K "${HEIFD_K:-300}" \
    --tau "${HEIFD_TAU:-4.0}" \
    --student-lr "${HEIFD_STUDENT_LR:-0.01}" \
    --case "${CASE}" \
    --results-root "${REPO_ROOT}/results" \
    --data-root "${REPO_ROOT}/data" \
    --cache-root "${REPO_ROOT}/cache" \
    --num-chunks "${NUM_CHUNKS:-1}" \
    --chunk-index "${CHUNK_INDEX:-0}"
