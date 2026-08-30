#!/bin/bash
#SBATCH --partition=ai
#SBATCH --account=ai
#SBATCH --qos=ai
#SBATCH --gres=gpu:ampere_a40:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=6:00:00
#SBATCH --job-name=row_leak
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/row_leakage/runs/row_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/row_leakage/runs/row_%j.err

set -euo pipefail
cd /scratch/hkanpak21/HE_IFD
mkdir -p results/row_leakage/runs
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
export HF_HUB_OFFLINE=1
exec srun python -u jobs/row_leakage.py "$@"
