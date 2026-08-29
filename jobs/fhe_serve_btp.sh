#!/bin/bash
#SBATCH --partition=ai
#SBATCH --account=ai
#SBATCH --qos=ai
#SBATCH --cpus-per-task=16
#SBATCH --mem=200G
#SBATCH --time=48:00:00
#SBATCH --job-name=fhe_serve_btp
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/fhe_serve/runs/serve_btp_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/fhe_serve/runs/serve_btp_%j.err

# The tournament argmax with level restoration done by the serving party alone,
# under collectively generated bootstrapping keys. The bootstrapping ring is 2^16,
# so the key material and the working set are large. CPU-only: no --gres.
set -euo pipefail
cd /scratch/hkanpak21/HE_IFD/fhe
module load go/1.24.4
go build -o /scratch/hkanpak21/HE_IFD/fhe/fhe-serve-btp .
exec srun /scratch/hkanpak21/HE_IFD/fhe/fhe-serve-btp \
  -serve-btp -json /scratch/hkanpak21/HE_IFD/results/fhe_serve/argmax_tournament_btp.json
