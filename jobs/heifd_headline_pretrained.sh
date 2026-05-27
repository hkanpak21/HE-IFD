#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --job-name=heifd_pt
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_pretrained_headline/runs/pt_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_pretrained_headline/runs/pt_%j.err
#
# Pretrained-backbone headline grid (issue 008). ONE backbone per job (set via
# HEIFD_BACKBONE) so its features extract+cache exactly once at the first cell —
# no cross-chunk extraction race. Each backbone's 360-cell grid (N{5,10,20,50} x
# alpha{0.01..1.0} x 6 methods x 3 seeds) runs in one resumable <=3h job; head
# cells are cheap (linear head on cached features) so it fits. Resubmit to resume.
#
#   sbatch --export=ALL,HEIFD_BACKBONE=resnet18_cifar10 jobs/heifd_headline_pretrained.sh
#   sbatch --export=ALL,HEIFD_BACKBONE=vit_b32_cifar10  jobs/heifd_headline_pretrained.sh
#   sbatch --export=ALL,HEIFD_BACKBONE=distilbert_agnews jobs/heifd_headline_pretrained.sh
#   sbatch --export=ALL,HEIFD_BACKBONE=gpt2_agnews       jobs/heifd_headline_pretrained.sh
#
# Requires login-node prefetch (jobs/prefetch_login.py) to have populated the
# HF/torch caches first; compute nodes load offline.

set -euo pipefail
REPO=/scratch/hkanpak21/HE_IFD
BB="${HEIFD_BACKBONE:?set HEIFD_BACKBONE=<resnet18_cifar10|vit_b32_cifar10|distilbert_agnews|gpt2_agnews>}"
CASE=heifd_pretrained_headline
mkdir -p "${REPO}/results/${CASE}/runs"
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
cd "${REPO}"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1   # weights pre-fetched on login node
echo "[pt] job ${SLURM_JOB_ID:-?} backbone=${BB} on $(hostname)"

exec srun python -u -m src.sweep \
    --backbones "${BB}" \
    --Ns 5,10,20,50 \
    --alphas 0.01,0.05,0.1,0.3,1.0 \
    --methods no_phase0,warmup_only_labelled,labelled_probe_warmup,raw_union_K20,dp_avg_eps2_K20,dp_avg_eps8_K20 \
    --seeds 42,43,44 \
    --K "${HEIFD_K:-300}" \
    --case "${CASE}" \
    --results-root "${REPO}/results" \
    --data-root "${REPO}/data" \
    --cache-root "${REPO}/cache"
