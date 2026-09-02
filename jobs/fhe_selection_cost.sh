#!/bin/bash
#SBATCH --partition=ai
#SBATCH --account=ai
#SBATCH --qos=ai
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --job-name=fhe_selection
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/fhe_serve/runs/selection_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/fhe_serve/runs/selection_%j.err

# The cost of the selection step: every client scores both arrangements on its
# held-out data under encryption, the server combines the encrypted per-class
# counts into one score per arrangement, and one value is decrypted. The paper
# asserts "at most 2NC encrypted comparisons, once" and gives no measurement.
# N in {5,10,20}, C in {4,14,77,100}, ring degree 2^15. CPU-only: no --gres.
set -euo pipefail
cd /scratch/hkanpak21/HE_IFD/fhe
mkdir -p /scratch/hkanpak21/HE_IFD/results/fhe_serve/runs
source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/lmod/lmod/init/bash 2>/dev/null || true
module load go/1.24.4
export GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off GOFLAGS=-mod=mod
go build -o /scratch/hkanpak21/HE_IFD/fhe/fhe-selection .
exec srun /scratch/hkanpak21/HE_IFD/fhe/fhe-selection \
  -selection-cost -json /scratch/hkanpak21/HE_IFD/results/fhe_serve/selection_cost.json
