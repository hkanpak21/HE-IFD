#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --job-name=linearize
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/linearize_test/runs/lin_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/linearize_test/runs/lin_%j.err

set -euo pipefail
cd /scratch/hkanpak21/HE_IFD
mkdir -p results/linearize_test/runs
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
export HF_HUB_OFFLINE=1
exec srun python -u jobs/linearize_test.py "$@"
