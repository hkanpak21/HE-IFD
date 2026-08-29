#!/bin/bash
#SBATCH --partition=ai
#SBATCH --account=ai
#SBATCH --qos=ai
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --job-name=fhe_serve_index
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/fhe_serve/runs/serve_index_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/fhe_serve/runs/serve_index_%j.err

# The encrypted argmax INDEX (Algorithm 2), measured against the value-only
# tournament as its control. CPU-only: no --gres, so it schedules beside GPU work.
set -euo pipefail
cd /scratch/hkanpak21/HE_IFD/fhe
module load go/1.24.4
go build -o /scratch/hkanpak21/HE_IFD/fhe/fhe-serve-index .
exec srun /scratch/hkanpak21/HE_IFD/fhe/fhe-serve-index \
  -serve-index -json /scratch/hkanpak21/HE_IFD/results/fhe_serve/argmax_index.json
