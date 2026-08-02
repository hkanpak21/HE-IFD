#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=01:00:00
#SBATCH --job-name=fhe_tourn
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/fhe_serve/runs/tournament_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/fhe_serve/runs/tournament_%j.err

# Serve-mode encrypted argmax via a LOG-DEPTH SIMD tournament (QuickMax): the
# optimized alternative to the naive C-1 fold, ceil(log2 C) rounds. Measures the
# real multiparty-CKKS latency + refresh count to confirm the ~C/log2(C) estimate.
# CPU-only (no GPU used); Lattigo/Go; builds offline from the pre-reconciled cache.
set -uo pipefail
cd /scratch/hkanpak21/HE_IFD/fhe
mkdir -p /scratch/hkanpak21/HE_IFD/results/fhe_serve/runs

source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/lmod/lmod/init/bash 2>/dev/null || true
module load go/1.24.4
export GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off GOFLAGS=-mod=mod

echo "[fhe_tourn] go: $(go version)"
echo "[fhe_tourn] building..."
go build -o fhe-serve . || { echo "[fhe_tourn] BUILD FAILED"; exit 1; }
echo "[fhe_tourn] running tournament argmax benchmark..."
srun ./fhe-serve -serve-tournament -json /scratch/hkanpak21/HE_IFD/results/fhe_serve/argmax_tournament.json
echo "[fhe_tourn] done."
