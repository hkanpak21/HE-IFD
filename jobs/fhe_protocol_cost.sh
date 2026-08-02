#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=01:00:00
#SBATCH --job-name=fhe_proto
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/fhe_serve/runs/protocol_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/fhe_serve/runs/protocol_%j.err

# Per-operation cost of the encrypted-serving protocol: ciphertext-by-ciphertext
# head application under a private query, encrypted reciprocal for the head merge,
# key switch to the querier's key, and selection scoring. These are the operations
# Release-mode aggregation never paid for.
# CPU-only (no GPU used); Lattigo/Go; builds offline from the pre-reconciled cache.
set -uo pipefail
cd /scratch/hkanpak21/HE_IFD/fhe
mkdir -p /scratch/hkanpak21/HE_IFD/results/fhe_serve/runs

source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/lmod/lmod/init/bash 2>/dev/null || true
module load go/1.24.4
export GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off GOFLAGS=-mod=mod

echo "[fhe_proto] go: $(go version)"
echo "[fhe_proto] building..."
go build -o fhe-serve . || { echo "[fhe_proto] BUILD FAILED"; exit 1; }
echo "[fhe_proto] running protocol-cost benchmark..."
srun ./fhe-serve -protocol-cost -json /scratch/hkanpak21/HE_IFD/results/fhe_serve/protocol_cost.json
echo "[fhe_proto] done."
