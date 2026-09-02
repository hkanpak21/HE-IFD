#!/bin/bash
#SBATCH --partition=ai
#SBATCH --account=ai
#SBATCH --qos=ai
#SBATCH --gres=gpu:ampere_a40:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=02:00:00
#SBATCH --job-name=fhe_export_head
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/fhe_serve/runs/export_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/fhe_serve/runs/export_%j.err

set -euo pipefail
cd /scratch/hkanpak21/HE_IFD
mkdir -p results/fhe_serve/runs results/fhe_serve/real_query
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
export HF_HUB_OFFLINE=1
exec srun python -u jobs/fhe_export_head.py "$@"
