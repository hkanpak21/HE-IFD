#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --job-name=fhe_grid
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/fhe_serve/runs/cost_grid_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/fhe_serve/runs/cost_grid_%j.err

# Per-operation cost over the cross product of ring degree and federation size:
# logN in {14,15,16} against N in {5,10,20}. One figure replaces two tables.
# CPU-only. No --gres, so this runs beside a GPU job rather than queueing behind it.
set -uo pipefail
cd /scratch/hkanpak21/HE_IFD/fhe
mkdir -p /scratch/hkanpak21/HE_IFD/results/fhe_serve/runs

source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/lmod/lmod/init/bash 2>/dev/null || true
module load go/1.24.4
export GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off GOFLAGS=-mod=mod

echo "[fhe_grid] go: $(go version)"
go build -o fhe-serve . || { echo "[fhe_grid] BUILD FAILED"; exit 1; }
echo "[fhe_grid] running the cost grid..."
srun ./fhe-serve -cost-grid -json /scratch/hkanpak21/HE_IFD/results/fhe_serve/cost_grid.json
echo "[fhe_grid] done."
