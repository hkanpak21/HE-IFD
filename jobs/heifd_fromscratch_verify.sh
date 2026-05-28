#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --job-name=heifd_fsverify
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_fromscratch_verify/runs/verify_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_fromscratch_verify/runs/verify_%j.err
#
# Verify the NEW from-scratch backbones (issue 007 extension): LeNet-5/FMNIST and
# CNN-5/CIFAR-10. 4 cells, no_phase0 + raw_union at alpha {0.05, 1.0}, N=16, seed
# 42. Must pass the sanity gate BEFORE scaling to the full FMNIST/CIFAR-10 grid
# (a local conv-net port has runtime/shape bugs ast.parse can't catch).
#   alpha=0.05: raw_union > no_phase0  |  alpha=1.0: acc near a sane ceiling.

set -euo pipefail
REPO=/scratch/hkanpak21/HE_IFD
mkdir -p "${REPO}/results/heifd_fromscratch_verify/runs"
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
cd "${REPO}"
echo "[fsverify] job ${SLURM_JOB_ID:-?} on $(hostname)"
exec srun python -u -m src.sweep \
    --backbones lenet_fmnist,cnn5_cifar10 \
    --Ns 16 \
    --alphas 0.05,1.0 \
    --methods no_phase0,raw_union_K20 \
    --seeds 42 \
    --K 300 \
    --case heifd_fromscratch_verify \
    --results-root "${REPO}/results" \
    --data-root "${REPO}/data" \
    --cache-root "${REPO}/cache"
