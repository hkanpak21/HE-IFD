#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --job-name=heifd_021_mnist
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_021_mia/runs/mnist_%A_%a.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_021_mia/runs/mnist_%A_%a.err
#
# Issue 021 — MIA suite, mnist_mlp cell. N=10, α∈{0.05,1.0}, ~64 shadow models.
# Three attacks (Yeom threshold, LiRA, GLiRA) × three surfaces (external,
# fellow, prototype). Reuses src/ to build every target + shadow model.
#
# CHUNKING (the 3h cap): the chunk unit is the MODEL (target = model 0, then 64
# shadows = 65 models per (α, seed)). Shadow training dominates wall-clock and is
# embarrassingly parallel, so a SLURM job-array splits the 65 models across tasks
# via NUM_CHUNKS / CHUNK_INDEX (the runner reads these from env, exactly like
# src.sweep). Each task trains only its slice and checkpoints each model to
# results/heifd_021_mia/shadows/<cell>/model_XXXX.npz — a job that dies resumes
# by skipping models whose checkpoint exists. Scoring runs whenever ALL 65
# checkpoints for a cell are present (any task that finds them complete writes
# the per-cell JSON), and a final --score-only pass guarantees the report.
#
# The from-scratch MLP is cheap (each global model ≈ seconds on a T4), so MNIST
# fits in ONE non-array job. The job-array form is provided for parity / safety:
#
#   single job (recommended for MNIST):
#     sbatch jobs/heifd_021_mia_mnist.sh
#
#   chunked (if a node is slow): 5-way model split
#     sbatch --array=0-4 --export=ALL,NUM_CHUNKS=5 jobs/heifd_021_mia_mnist.sh
#     # then, once all chunks land, write the report:
#     sbatch --export=ALL,SCORE_ONLY=1 jobs/heifd_021_mia_mnist.sh
#
# MNIST is pre-cached under data/ (download=False); no login-node prefetch needed.

set -euo pipefail
REPO=/scratch/hkanpak21/HE_IFD
CASE=heifd_021_mia
mkdir -p "${REPO}/results/${CASE}/runs"
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
cd "${REPO}"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1

# Job-array → per-task model chunk; non-array → single chunk.
export NUM_CHUNKS="${NUM_CHUNKS:-${SLURM_ARRAY_TASK_COUNT:-1}}"
export CHUNK_INDEX="${CHUNK_INDEX:-${SLURM_ARRAY_TASK_ID:-0}}"
echo "[021-mnist] job ${SLURM_JOB_ID:-?} chunk=${CHUNK_INDEX}/${NUM_CHUNKS} on $(hostname)"

EXTRA=""
if [[ "${SCORE_ONLY:-0}" == "1" ]]; then EXTRA="--score-only"; fi

exec srun python -u -m mia.run \
    --backbones mlp_mnist \
    --Ns 10 \
    --alphas 0.05,1.0 \
    --methods "${HEIFD_METHOD:-raw_union_K20}" \
    --seeds "${HEIFD_SEEDS:-42}" \
    --n-shadows "${HEIFD_NSHADOWS:-64}" \
    --attack-pool-size "${HEIFD_POOL:-5000}" \
    --prototype-K-per-class 20 \
    --num-chunks "${NUM_CHUNKS}" \
    --chunk-index "${CHUNK_INDEX}" \
    ${EXTRA} \
    --case "${CASE}" \
    --results-root "${REPO}/results" \
    --data-root "${REPO}/data" \
    --cache-root "${REPO}/cache"
