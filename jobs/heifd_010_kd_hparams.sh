#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --job-name=heifd_010
#SBATCH --array=0-3
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_010_kd_hparams_resnet18/runs/kdhp_%A_%a.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_010_kd_hparams_resnet18/runs/kdhp_%A_%a.err
#
# Issue 010 — KD hyperparam sweep on the broken regime (resnet18 / CIFAR-10 /
# α=0.05 / N=10). Issue 008 found raw_union=0.48 vs θ₀=0.74 here, so K-step KD
# is actively DEGRADING the warmed init by 26pp. This job tests whether the gap
# closes via KD hyperparams alone (current K=300 / τ=4 / lr=0.01 may overshoot
# a tiny linear head that is already at 0.74 after probe warmup).
#
# Grid (4 × 2 × 2 × 3 seeds = 48 cells):
#   backbone resnet18_cifar10 · N=10 · α=0.05 · method raw_union_K20 (= the cell
#       008 found broken; Phase-0 Kpc=20 held fixed so only K/τ/LR vary)
#   K   ∈ {30, 100, 300, 1000}   (overshoot vs undershoot trajectory length)
#   τ   ∈ {1, 4}                  (sharp vs smoothed soft targets)
#   lr  ∈ {0.001, 0.01}           (gentle vs current SGD step size)
#   seeds {42, 43, 44}
#
# Sweep CLI: the additive --Ks / --taus / --student-lrs flags (added with this
# issue) cross all three axes inside one process. Cell descriptors carry the
# non-default (τ, lr) values so per-cell JSON filenames stay distinct, and
# legacy cells (τ=4.0, lr=0.01) keep their existing hashes — see
# src/sweep.py::cell_descriptor for the backwards-compat rule.
#
# Chunking: SLURM job array (--array=0-3 → 4 chunks) with round-robin striping
# via sweep.py's --num-chunks / --chunk-index. Each chunk runs 12 of the 48
# cells (mix of K values per chunk thanks to round-robin), so the K=1000
# slow-cell load is spread across all 4 chunks rather than concentrated in one.
# All chunks share the resnet18 feature cache (one extraction, then reuse).
# Resumable: re-submitting skips cells whose JSON already records
# status=success (see src/sweep.py).
#
# Wall-clock estimate: prior 008 pretrained job ran 360 resnet18 cells in <3h
# at K=300, so ~30 s/cell. Scaling per K (linear in distill): K=30 ≈ 10 s,
# K=100 ≈ 18 s, K=300 ≈ 30 s, K=1000 ≈ 80 s — chunk total ≈ 7 min. Comfortably
# inside the 3h VALAR hard cap with a >20× safety margin.
#
# Dataset (CIFAR-10) is pre-cached under data/; resnet18 pretrained weights are
# pre-fetched on the login node into the torch cache (compute nodes load
# offline via HF_HUB_OFFLINE=1 / TRANSFORMERS_OFFLINE=1). No login-node
# prefetch needed beyond what 008 already populated.

set -euo pipefail
REPO=/scratch/hkanpak21/HE_IFD
CASE=heifd_010_kd_hparams_resnet18
mkdir -p "${REPO}/results/${CASE}/runs"
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
cd "${REPO}"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
echo "[kdhp] job ${SLURM_ARRAY_JOB_ID:-?} task ${SLURM_ARRAY_TASK_ID:-0}/${SLURM_ARRAY_TASK_COUNT:-1} on $(hostname)"

exec srun python -u -m src.sweep \
    --backbones resnet18_cifar10 \
    --Ns 10 \
    --alphas 0.05 \
    --methods raw_union_K20 \
    --seeds 42,43,44 \
    --Ks 30,100,300,1000 \
    --taus 1,4 \
    --student-lrs 0.001,0.01 \
    --case "${CASE}" \
    --results-root "${REPO}/results" \
    --data-root "${REPO}/data" \
    --cache-root "${REPO}/cache" \
    --num-chunks "${SLURM_ARRAY_TASK_COUNT:-4}" \
    --chunk-index "${SLURM_ARRAY_TASK_ID:-0}"
