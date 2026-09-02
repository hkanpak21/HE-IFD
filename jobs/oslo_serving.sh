#!/bin/bash
#SBATCH --partition=ai
#SBATCH --account=ai
#SBATCH --qos=ai
#SBATCH --gres=gpu:ampere_a40:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=8:00:00
#SBATCH --job-name=oslo
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/oslo_serving/runs/oslo_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/oslo_serving/runs/oslo_%j.err

set -euo pipefail
cd /scratch/hkanpak21/HE_IFD
mkdir -p results/oslo_serving/runs
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
export HF_HUB_OFFLINE=1
exec srun python -u jobs/oslo_serving.py "$@"
