#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --job-name=heifd_012h
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_012_harder_vision_headline/runs/headline_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_012_harder_vision_headline/runs/headline_%j.err
#
# Issue 012 — Harder-vision-dataset full grid (CIFAR-100, optionally Tiny-ImageNet).
# Mirrors `heifd_headline_pretrained.sh` but on the harder-dataset axis. The
# orchestrator only submits this AFTER `heifd_012_harder_vision_verify.sh`
# produces sensible numbers (ViT/CIFAR-100 IID ≥ 0.60 + raw_union > θ₀ at α=0.05).
#
# ONE backbone per job (set via HEIFD_BACKBONE) so its features extract+cache
# exactly once at the first cell — no cross-chunk extraction race (the
# CIFAR-100 / Tiny-ImageNet feature caches are larger than CIFAR-10; concurrent
# extraction would also push memory). Each backbone's full grid runs in one
# resumable ≤3h job; head cells are cheap (linear head on cached features) so
# the per-cell wall-clock is dominated by warmup + K=100 distillation. Resubmit
# to resume any cell that didn't get a `status=success` JSON.
#
# Grid (per backbone): N × α × methods × seeds × K
#   N    : {1, 5, 10, 20, 50}     (Phase II N-grid per docs/prd; 5 values)
#   α    : {0.01, 0.05, 0.1, 0.3, 1.0}   (5 values)
#   meth : {no_phase0, warmup_only_labelled, labelled_probe_warmup,
#           raw_union_K20, dp_avg_eps2_K20, dp_avg_eps8_K20}        (6 values)
#   seed : {42, 43, 44}           (3 seeds — the standard headline replication)
#   K    : 100 (issue 010 best for pretrained head); τ=1, lr=0.001
#   scope: head_only              (issue 011 confirmed head_only suffices)
# Total per backbone: 5 × 5 × 6 × 3 = 450 cells.
#
# If only ViT/CIFAR-100 is needed (the highest-value cell per issue 012):
#   sbatch --export=ALL,HEIFD_BACKBONE=vit_b32_cifar100 \
#          jobs/heifd_012_harder_vision_headline.sh
#
# Other backbones (set HEIFD_BACKBONE accordingly):
#   sbatch --export=ALL,HEIFD_BACKBONE=resnet18_cifar100 \
#          jobs/heifd_012_harder_vision_headline.sh
#   sbatch --export=ALL,HEIFD_BACKBONE=vit_b32_tiny_imagenet \
#          jobs/heifd_012_harder_vision_headline.sh
#   sbatch --export=ALL,HEIFD_BACKBONE=resnet18_tiny_imagenet \
#          jobs/heifd_012_harder_vision_headline.sh
#
# Chunking (450 cells is too large for a single 3h job — chunk via SLURM
# job-array; the sweep CLI consumes NUM_CHUNKS/CHUNK_INDEX from env per
# CLAUDE.md):
#   sbatch --array=0-7 --export=ALL,HEIFD_BACKBONE=vit_b32_cifar100,NUM_CHUNKS=8 \
#          jobs/heifd_012_harder_vision_headline.sh
# With 8 chunks × 450/8 ≈ 56 cells, each chunk lands well under the 3h cap
# even for ViT-B/32 (the heaviest extractor per chunk because the feature
# cache is built lazily on first access; subsequent chunks hit a hot cache).
#
# Requires the login-node prefetch (jobs/prefetch_login.py --include-cifar100
# [--include-tiny-imagenet]) to have populated the dataset roots first.

set -euo pipefail
REPO=/scratch/hkanpak21/HE_IFD
BB="${HEIFD_BACKBONE:?set HEIFD_BACKBONE=<vit_b32_cifar100|resnet18_cifar100|vit_b32_tiny_imagenet|resnet18_tiny_imagenet>}"
CASE=heifd_012_harder_vision_headline
mkdir -p "${REPO}/results/${CASE}/runs"
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
cd "${REPO}"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1   # weights pre-fetched on login node

# SLURM job-array support: each task picks its own chunk via SLURM_ARRAY_TASK_ID.
# Non-array submissions default to single-chunk (NUM_CHUNKS=1, CHUNK_INDEX=0).
export NUM_CHUNKS="${NUM_CHUNKS:-${SLURM_ARRAY_TASK_COUNT:-1}}"
export CHUNK_INDEX="${CHUNK_INDEX:-${SLURM_ARRAY_TASK_ID:-0}}"
echo "[012-headline] job ${SLURM_JOB_ID:-?} backbone=${BB} chunk=${CHUNK_INDEX}/${NUM_CHUNKS} on $(hostname)"

exec srun python -u -m src.sweep \
    --backbones "${BB}" \
    --Ns 1,5,10,20,50 \
    --alphas 0.01,0.05,0.1,0.3,1.0 \
    --methods no_phase0,warmup_only_labelled,labelled_probe_warmup,raw_union_K20,dp_avg_eps2_K20,dp_avg_eps8_K20 \
    --seeds 42,43,44 \
    --K "${HEIFD_K:-100}" \
    --tau "${HEIFD_TAU:-1}" \
    --student-lr "${HEIFD_LR:-0.001}" \
    --num-chunks "${NUM_CHUNKS}" \
    --chunk-index "${CHUNK_INDEX}" \
    --case "${CASE}" \
    --results-root "${REPO}/results" \
    --data-root "${REPO}/data" \
    --cache-root "${REPO}/cache"
