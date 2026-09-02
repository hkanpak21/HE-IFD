#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --job-name=heifd_021_vit
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_021_mia/runs/vit_cifar100_%A_%a.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_021_mia/runs/vit_cifar100_%A_%a.err
#
# Issue 021 — MIA suite, vit_b32_cifar100 cell. N=10, α∈{0.05,1.0}, ~64 shadows.
# Three attacks (Yeom threshold, LiRA, GLiRA) × three surfaces (external, fellow,
# prototype). Head-on-cached-features: the frozen ViT-B/32 extracts CIFAR-100
# features ONCE (cached under cache/features/cifar100_vit_b32.pt by the protocol's
# own extractor); every target/shadow model is then a cheap linear-head train +
# K=100 distillation. Reuses src/ — the protocol is not reimplemented.
#
# CHUNKING (the 3h cap): chunk unit = MODEL (target = 0, then 64 shadows = 65
# models per (α, seed)). A SLURM job-array splits the 65 models across tasks via
# NUM_CHUNKS / CHUNK_INDEX; each task trains only its slice and checkpoints each
# model's attack vectors (IN-mask, φ, loss, surrogate-φ over the pool) to
# results/heifd_021_mia/shadows/<cell>/model_XXXX.npz. A preempted task resumes
# by skipping existing checkpoints; scoring fires once all 65 are present. The
# first task that extracts ViT features warms the shared feature cache for the
# rest — to avoid a concurrent-extraction race on a cold cache, warm it ONCE
# first (a tiny single-model run), then launch the array.
#
# RECOMMENDED two-step launch (cold cache → warm → array → score):
#   # 1. warm the ViT/CIFAR-100 feature cache + train a few models (single task):
#   sbatch --export=ALL,NUM_CHUNKS=8,CHUNK_INDEX=0 jobs/heifd_021_mia_vit_cifar100.sh
#   # 2. once the cache exists, fan out the remaining model chunks:
#   sbatch --array=1-7 --export=ALL,NUM_CHUNKS=8 jobs/heifd_021_mia_vit_cifar100.sh
#   # 3. final report pass (scores any complete cell, rewrites README/summary):
#   sbatch --export=ALL,SCORE_ONLY=1 jobs/heifd_021_mia_vit_cifar100.sh
#
# With 8 model chunks × 65 models / 8 ≈ 8 models per task per (α,seed) — each task
# lands well under 3h even with the one-time ViT extraction on the first task.
#
# REQUIRES the login-node prefetch to have populated the ViT-B/32 weights + the
# CIFAR-100 dataset root first:
#   python jobs/prefetch_login.py --include-cifar100   # on the login node

set -euo pipefail
REPO=/scratch/hkanpak21/HE_IFD
CASE=heifd_021_mia
mkdir -p "${REPO}/results/${CASE}/runs"
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
cd "${REPO}"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1

export NUM_CHUNKS="${NUM_CHUNKS:-${SLURM_ARRAY_TASK_COUNT:-1}}"
export CHUNK_INDEX="${CHUNK_INDEX:-${SLURM_ARRAY_TASK_ID:-0}}"
echo "[021-vit] job ${SLURM_JOB_ID:-?} chunk=${CHUNK_INDEX}/${NUM_CHUNKS} on $(hostname)"

EXTRA=""
if [[ "${SCORE_ONLY:-0}" == "1" ]]; then EXTRA="--score-only"; fi

exec srun python -u -m mia.run \
    --backbones vit_b32_cifar100 \
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
