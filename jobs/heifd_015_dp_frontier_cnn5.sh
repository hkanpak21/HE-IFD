#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --job-name=heifd_015_cnn5
#SBATCH --array=0-8
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_015_dp_frontier_cnn5/runs/cnn5_%A_%a.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_015_dp_frontier_cnn5/runs/cnn5_%A_%a.err
#
# Issue 015 — DP-ε frontier sweep on from-scratch CNN-5 / CIFAR-10.
#
# BLOCKED-BUT-PREPARED: the orchestrator submits this only AFTER 014's dp_avg
# LeNet re-run + CNN-5 land. Same averaging-variant DP-frontier question as the
# MLP/LeNet wrappers, on the CNN-5/CIFAR-10 backbone: does the frontier flatten
# from ε ≈ 2 onward? ε panel {0.5, 2, 8, 32, ∞} @ Kpc=20 + Kpc panel {1, 5, 20}
# @ ε ∈ {2, 8}. epsinf -> σ=0 (raw_union-equivalent sanity reference).
#
# parse_method already handles every token below (verified by tracing each
# token through _extract_eps / _extract_int_after). No src/ change was needed.
#
# Grid: cnn5_cifar10 × N{10} × α{0.05,0.3,1.0}
#       × methods{ dp_avg_eps0.5_K20, dp_avg_eps2_K20, dp_avg_eps8_K20,
#                  dp_avg_eps32_K20, dp_avg_epsinf_K20,        (ε sweep @ Kpc=20)
#                  dp_avg_eps2_K1, dp_avg_eps2_K5,             (Kpc sweep @ ε=2)
#                  dp_avg_eps8_K1, dp_avg_eps8_K5 }            (Kpc sweep @ ε=8)
#       × seeds{42,43,44}  = 9 × 1 × 3 × 3 = 81 cells.
#
# Chunking: SLURM job array (--array=0-8 → 9 chunks, ~9 cells each) via
# sweep.py's --num-chunks / --chunk-index round-robin striping. CNN-5/CIFAR-10
# is the heaviest from-scratch backbone (teacher_epochs=60, oracle_epochs=100,
# cosine LR); 9 chunks keeps each well under the 3h wall. Resumable — re-
# submitting skips status=success cells.
#
# NOTE: the phase0 flatten-bridge fix (explicit flat_dim in _flatten_clients)
# lets dp_avg run on the conv backbone without the empty-tensor crash at extreme
# heterogeneity; the α grid here is mild (0.05/0.3/1.0 at N=10), but the fix is
# in place regardless.
#
# CIFAR-10 is pre-cached under data/cifar-10-batches-py/ (download=False); the
# CNN-5 trains on RAW pixels, no pretrained weights, no login-node prefetch.

set -euo pipefail
REPO=/scratch/hkanpak21/HE_IFD
CASE=heifd_015_dp_frontier_cnn5
mkdir -p "${REPO}/results/${CASE}/runs"
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
cd "${REPO}"
echo "[015 cnn5] job ${SLURM_ARRAY_JOB_ID:-?} task ${SLURM_ARRAY_TASK_ID:-0}/${SLURM_ARRAY_TASK_COUNT:-1} on $(hostname)"

exec srun python -u -m src.sweep \
    --backbones cnn5_cifar10 \
    --Ns 10 \
    --alphas 0.05,0.3,1.0 \
    --methods dp_avg_eps0.5_K20,dp_avg_eps2_K20,dp_avg_eps8_K20,dp_avg_eps32_K20,dp_avg_epsinf_K20,dp_avg_eps2_K1,dp_avg_eps2_K5,dp_avg_eps8_K1,dp_avg_eps8_K5 \
    --seeds 42,43,44 \
    --K "${HEIFD_K:-300}" \
    --case "${CASE}" \
    --results-root "${REPO}/results" \
    --data-root "${REPO}/data" \
    --cache-root "${REPO}/cache" \
    --num-chunks "${SLURM_ARRAY_TASK_COUNT:-9}" \
    --chunk-index "${SLURM_ARRAY_TASK_ID:-0}"
