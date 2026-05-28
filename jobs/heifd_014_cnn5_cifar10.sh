#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --job-name=heifd_014_cnn5
#SBATCH --array=0-7
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_cnn5_cifar10_headline/runs/cnn5_%A_%a.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_cnn5_cifar10_headline/runs/cnn5_%A_%a.err
#
# Issue 014 Sub-task C — CNN-5 / CIFAR-10 full from-scratch headline grid.
#
# **BLOCKED: do NOT sbatch this until the Round-2.5 CNN-5 verify clears BOTH
# gates** (IID raw_union α=1.0 ≥ 0.60 AND m4_ood α=0.05 ≥ 0.40). See
# results/heifd_fromscratch_verify/README.md for status — Round-1 reverify
# failed at 0.5159, Round-2.5 cosine-LR + 60ep teacher tuner is the current
# attempt and its result determines whether this wrapper ever runs. The
# orchestrator submits this conditionally.
#
# Backbone hparams are committed to master in src/protocol.py::BACKBONES
# ("cnn5_cifar10" spec): teacher_epochs=60, teacher_lr=0.01,
# teacher_lr_schedule="cosine", oracle_epochs=100, warmup_epochs=10. From-scratch
# regime keeps the legacy K=300 default (the pretrained K=100 from issue 010
# does not transfer to full conv-net end-to-end training; different dynamics).
#
# Grid: cnn5_cifar10 × N{1,5,10,20,50} × α{0.01,0.05,0.1,0.3,1.0}
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
# Wall-clock budget: cnn5_cifar10 cells under the Round-2.5 hparams (60ep
# teacher + 100ep oracle + 10ep warmup) are heavier than lenet_fmnist; the
# 3h VALAR hard cap is the constraint. Round-robin chunking keeps the
# slowest cells from concentrating. If a chunk exceeds 3h, resume by
# re-submitting — already-finished cells are cached.
#
# CIFAR-10 is pre-cached under data/cifar-10-batches-py/ (download=False); no
# pretrained weights needed. No login-node prefetch required.

set -euo pipefail
REPO=/scratch/hkanpak21/HE_IFD
CASE=heifd_cnn5_cifar10_headline
mkdir -p "${REPO}/results/${CASE}/runs"
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
cd "${REPO}"
echo "[014 cnn5] job ${SLURM_ARRAY_JOB_ID:-?} task ${SLURM_ARRAY_TASK_ID:-0}/${SLURM_ARRAY_TASK_COUNT:-1} on $(hostname)"

exec srun python -u -m src.sweep \
    --backbones cnn5_cifar10 \
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
