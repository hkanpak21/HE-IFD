#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --job-name=heifd_fs
#SBATCH --array=0-7
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_mlp_mnist_headline/runs/fs_%A_%a.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_mlp_mnist_headline/runs/fs_%A_%a.err
#
# From-scratch headline grid (issue 007), MNIST/MLP — the one from-scratch
# backbone that exists today. FMNIST/CIFAR-10 from-scratch (LeNet-5/CNN-5) need
# new backbones (separate issue) before they can be added here.
#
# Grid: mlp_mnist × N{5,10,20,50} × α{0.01,0.05,0.1,0.3,1.0}
#       × methods{no_phase0, warmup_only_labelled, labelled_probe_warmup,
#                 raw_union_K20, dp_avg_eps2_K20, dp_avg_eps8_K20}
#       × seeds{42,43,44}  = 360 cells, split into 8 resumable chunks (≤3h each).
# Reports IID acc + M3 + M4 + θ₀ + no-align baseline inline (issue 005).
#
# Issue 014 Sub-task B (extension in-place): the N grid is overridable via the
# HEIFD_NS env var, e.g. `HEIFD_NS=1 sbatch jobs/heifd_headline_fromscratch.sh`
# extends the existing 5/10/20/50 matrix with the Phase-II N=1 degenerate-baseline
# cells (90 new cells: 5α × 6methods × 3seeds). Because sweep.py is resumable,
# the original 360 cells stay cached (their JSONs already exist with
# status=success) and only the new N=1 cells run. Same case slug
# `heifd_mlp_mnist_headline` — extends in place. K is similarly overridable via
# HEIFD_K (legacy from-scratch default 300).

set -euo pipefail
REPO=/scratch/hkanpak21/HE_IFD
CASE=heifd_mlp_mnist_headline
mkdir -p "${REPO}/results/${CASE}/runs"
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
cd "${REPO}"
echo "[fs] job ${SLURM_ARRAY_JOB_ID:-?} task ${SLURM_ARRAY_TASK_ID:-0}/${SLURM_ARRAY_TASK_COUNT:-1} on $(hostname)"

exec srun python -u -m src.sweep \
    --backbones mlp_mnist \
    --Ns "${HEIFD_NS:-5,10,20,50}" \
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
