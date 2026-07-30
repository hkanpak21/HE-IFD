#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --job-name=ext_defence
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/extraction_defence/runs/def_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/extraction_defence/runs/def_%j.err
set -euo pipefail
cd /scratch/hkanpak21/HE_IFD
mkdir -p results/extraction_defence/runs
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
exec srun python -u jobs/extraction_defence.py "$@"
