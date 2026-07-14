#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=02:00:00
#SBATCH --job-name=fhe_argmax
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/fhe_serve/runs/argmax_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/fhe_serve/runs/argmax_%j.err

# Serve-mode encrypted ARGMAX cost (Job 2): the full argmax over C classes with
# its bootstraps wired to collective refreshes — the per-query "price of Serve".
# CPU-only (no GPU used); Lattigo/Go; builds offline from the pre-reconciled cache.
set -uo pipefail
cd /scratch/hkanpak21/HE_IFD/fhe
mkdir -p /scratch/hkanpak21/HE_IFD/results/fhe_serve/runs

source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/lmod/lmod/init/bash 2>/dev/null || true
module load go/1.24.4
export GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off GOFLAGS=-mod=mod

echo "[fhe_argmax] go: $(go version)"
echo "[fhe_argmax] building..."
go build -o fhe-serve . || { echo "[fhe_argmax] BUILD FAILED"; exit 1; }
echo "[fhe_argmax] running encrypted-argmax benchmark..."
srun ./fhe-serve -serve-argmax -json /scratch/hkanpak21/HE_IFD/results/fhe_serve/argmax_cost.json
echo "[fhe_argmax] done."
