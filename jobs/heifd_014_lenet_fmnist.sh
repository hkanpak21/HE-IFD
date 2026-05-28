#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --job-name=heifd_014_lenet
#SBATCH --array=0-7
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_lenet_fmnist_headline/runs/lenet_%A_%a.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_lenet_fmnist_headline/runs/lenet_%A_%a.err
#
# Issue 014 Sub-task A — LeNet-5 / FashionMNIST full from-scratch headline grid.
#
# Mirrors heifd_headline_fromscratch.sh's structure but on the LeNet/FMNIST
# backbone (BackboneSpec.lenet_fmnist; from-scratch conv net on raw 1x28x28
# images). The from-scratch regime keeps the legacy K=300 default (NOT the
# pretrained K=100 from issue 010 — different dynamics: linear head on cached
# pretrained features vs full conv net training end-to-end). LeNet/FMNIST
# already cleared the issue-007 sanity gate at N=16/α∈{0.05,1.0} (raw_union
# 0.67/0.05, 0.81/IID vs oracle 0.89 — see results/heifd_fromscratch_verify/);
# this full grid validates that pattern across the Phase-II N grid + α grid.
#
# Grid: lenet_fmnist × N{1,5,10,20,50} × α{0.01,0.05,0.1,0.3,1.0}
#       × methods{no_phase0, warmup_only_labelled, labelled_probe_warmup,
#                 raw_union_K20, dp_avg_eps2_K20, dp_avg_eps8_K20}
#       × seeds{42,43,44}  = 5 × 5 × 6 × 3 = 450 cells.
#
# Chunking: SLURM job array (--array=0-7 → 8 chunks) with round-robin striping
# via sweep.py's --num-chunks / --chunk-index. Each chunk runs ~57 cells; the
# heavier N=50 cells are spread across all 8 chunks (round-robin) rather than
# concentrated in one. Sweep is resumable — re-submitting skips cells whose
# JSON already records status=success (see src/sweep.py).
#
# FashionMNIST is pre-cached under data/FashionMNIST/ (download=False); no
# pretrained weights needed. No login-node prefetch required.

set -euo pipefail
REPO=/scratch/hkanpak21/HE_IFD
CASE=heifd_lenet_fmnist_headline
mkdir -p "${REPO}/results/${CASE}/runs"
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
cd "${REPO}"
echo "[014 lenet] job ${SLURM_ARRAY_JOB_ID:-?} task ${SLURM_ARRAY_TASK_ID:-0}/${SLURM_ARRAY_TASK_COUNT:-1} on $(hostname)"

exec srun python -u -m src.sweep \
    --backbones lenet_fmnist \
    --Ns 1,5,10,20,50 \
    --alphas 0.01,0.05,0.1,0.3,1.0 \
    --methods no_phase0,warmup_only_labelled,labelled_probe_warmup,raw_union_K20,dp_avg_eps2_K20,dp_avg_eps8_K20 \
    --seeds 42,43,44 \
    --K "${HEIFD_K:-300}" \
    --case "${CASE}" \
    --results-root "${REPO}/results" \
    --data-root "${REPO}/data" \
    --cache-root "${REPO}/cache" \
    --num-chunks "${SLURM_ARRAY_TASK_COUNT:-8}" \
    --chunk-index "${SLURM_ARRAY_TASK_ID:-0}"
