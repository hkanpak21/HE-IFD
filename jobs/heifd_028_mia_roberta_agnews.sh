#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --job-name=heifd_028_roberta
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_021_mia/runs/roberta_agnews_%A_%a.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_021_mia/runs/roberta_agnews_%A_%a.err
#
# Issue 028 — MIA suite, roberta_base_agnews cell. The LANGUAGE-modality
# pretrained backbone that pairs with the ViT/CIFAR-100 vision cell (021), so
# the §VI residual-leakage evidence covers a pretrained backbone in BOTH
# modalities. N=10, α∈{0.05,1.0}, ~64 shadows. Three attacks (Yeom threshold,
# LiRA, GLiRA) × three surfaces (external, fellow, prototype).
#
# Head-on-cached-features: the FROZEN roberta-base extracts AG-News sentence
# embeddings ONCE (masked mean-pool over real tokens, right-pad — the
# bidirectional-encoder path, NOT GPT-2's causal last-token), cached under
# cache/features/ag_news_roberta_base.pt by the protocol's own
# extract_text_features. Every target/shadow model is then a cheap linear-head
# train + K-step distillation on those cached 768-d features. Reuses src/ and
# mia/ UNCHANGED — roberta_base_agnews is already a registered backbone in
# src.protocol.BACKBONES (kind="head", num_classes=4, feature_loader
# "text:roberta_base", normalize_features="zscore"); `mia.run --backbones
# roberta_base_agnews` works without touching src/ or mia/.
#
# Shares CASE heifd_021_mia with the ViT wrapper so BOTH pretrained backbones
# land in ONE case dir / README table (auto-written by mia.report.write_report).
#
# CHUNKING (the 3h cap): chunk unit = MODEL (target = 0, then 64 shadows = 65
# models per (α, seed)). A SLURM job-array splits the 65 models across tasks via
# NUM_CHUNKS / CHUNK_INDEX; each task trains only its slice and checkpoints each
# model's attack vectors (IN-mask, φ, loss, surrogate-φ over the pool) to
# results/heifd_021_mia/shadows/<cell>/model_XXXX.npz. A preempted task resumes
# by skipping existing checkpoints; scoring fires once all 65 are present. The
# first task that extracts roberta-base features warms the shared feature cache
# for the rest — to avoid a concurrent-extraction race on a cold cache, warm it
# ONCE first (a tiny single-model run), then launch the array. 64 shadows on a
# transformer is heavy, so chunk generously (8 chunks ⇒ ~8 models/task/(α,seed),
# each task lands well under 3h even with the one-time RoBERTa extraction on the
# first task) and rely on the shadows/<cell>/ checkpoints to resume.
#
# RECOMMENDED two-step launch (cold cache → warm → array → score):
#   # 0. PREFETCH on the LOGIN NODE first (compute nodes have no internet — this
#   #    pulls roberta-base weights + the AG-News HF dataset into the caches):
#   python jobs/prefetch_login.py --include-text019   # roberta-base + ag_news
#   # 1. warm the RoBERTa/AG-News feature cache + train a few models (single task):
#   sbatch --export=ALL,NUM_CHUNKS=8,CHUNK_INDEX=0 jobs/heifd_028_mia_roberta_agnews.sh
#   # 2. once the cache exists, fan out the remaining model chunks:
#   sbatch --array=1-7 --export=ALL,NUM_CHUNKS=8   jobs/heifd_028_mia_roberta_agnews.sh
#   # 3. final report pass (scores any complete cell, rewrites README/summary):
#   sbatch --export=ALL,SCORE_ONLY=1               jobs/heifd_028_mia_roberta_agnews.sh
#
# CELLS: roberta_base_agnews, N=10, α∈{0.05,1.0}, 3 attacks × 3 surfaces,
# ~64 shadows per target. (--include-text019 also pulls all-mpnet + DBpedia-14;
# only roberta-base + ag_news are needed here, the extra pulls are harmless.)

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
echo "[028-roberta] job ${SLURM_JOB_ID:-?} chunk=${CHUNK_INDEX}/${NUM_CHUNKS} on $(hostname)"

EXTRA=""
if [[ "${SCORE_ONLY:-0}" == "1" ]]; then EXTRA="--score-only"; fi

exec srun python -u -m mia.run \
    --backbones roberta_base_agnews \
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
