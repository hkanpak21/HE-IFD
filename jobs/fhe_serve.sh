#!/bin/bash
#SBATCH --partition=ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --job-name=fhe_serve
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/fhe_serve/runs/serve_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/fhe_serve/runs/serve_%j.err

# Serve-mode (encrypted-inference) cost benchmark: the collective refresh
# (multiparty bootstrap) unit + threshold decrypt — the per-query atoms Release
# mode does not pay. CPU-only (no GPU); Lattigo/Go. The module cache + go.sum are
# pre-reconciled on the LOGIN node (go mod tidy) so this builds fully offline.
set -uo pipefail
cd /scratch/hkanpak21/HE_IFD/fhe
mkdir -p /scratch/hkanpak21/HE_IFD/results/fhe_serve/runs

source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/lmod/lmod/init/bash 2>/dev/null || true
module load go/1.24.4
export GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off GOFLAGS=-mod=mod

echo "[fhe_serve] go: $(go version)"
echo "[fhe_serve] building..."
go build -o fhe-serve . || { echo "[fhe_serve] BUILD FAILED"; exit 1; }
echo "[fhe_serve] running serve-mode benchmark..."
srun ./fhe-serve -serve -json /scratch/hkanpak21/HE_IFD/results/fhe_serve/serve_primitives.json
echo "[fhe_serve] done."
