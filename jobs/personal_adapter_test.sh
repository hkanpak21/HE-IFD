#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --job-name=persadapt
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/personal_adapter/runs/pa_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/personal_adapter/runs/pa_%j.err

set -euo pipefail
cd /scratch/hkanpak21/HE_IFD
mkdir -p results/personal_adapter/runs
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
export HF_HUB_OFFLINE=1
exec srun python -u jobs/personal_adapter_test.py "$@"
