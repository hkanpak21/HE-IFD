#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --job-name=extract_budget
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/extraction_budget/runs/ext_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/extraction_budget/runs/ext_%j.err
set -euo pipefail
cd /scratch/hkanpak21/HE_IFD
mkdir -p results/extraction_budget/runs
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
exec srun python -u jobs/extraction_budget.py "$@"
