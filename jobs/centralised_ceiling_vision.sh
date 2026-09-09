#!/bin/bash
#SBATCH --partition=ai
#SBATCH --account=ai
#SBATCH --qos=ai
#SBATCH --gres=gpu:ampere_a40:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=12:00:00
#SBATCH --job-name=ceil_vis
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/centralised_ceiling/runs/ceilvis_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/centralised_ceiling/runs/ceilvis_%j.err

set -euo pipefail
cd /scratch/hkanpak21/HE_IFD
mkdir -p results/centralised_ceiling/runs
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
export HF_HUB_OFFLINE=1
exec srun python -u jobs/centralised_ceiling_vision.py "$@"
