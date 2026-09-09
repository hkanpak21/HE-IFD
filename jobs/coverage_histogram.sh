#!/bin/bash
#SBATCH --partition=ai
#SBATCH --account=ai
#SBATCH --qos=ai
#SBATCH --cpus-per-task=4

#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --job-name=coverage
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/coverage/runs/cov_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/coverage/runs/cov_%j.err

set -euo pipefail
cd /scratch/hkanpak21/HE_IFD
mkdir -p results/coverage/runs
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
export HF_HUB_OFFLINE=1
exec srun python -u jobs/coverage_histogram.py "$@"
