#!/bin/bash
#SBATCH --partition=ai
#SBATCH --account=ai
#SBATCH --qos=ai
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=04:00:00
#SBATCH --job-name=fhe_comm
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/fhe_serve/runs/comm_grid_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/fhe_serve/runs/comm_grid_%j.err

# Communication over the cross product of ring degree, moduli chain and client
# count, plus the one-time bootstrapping key material.
#
# Why this job exists. runCommCost used to hardcode ring degree 2^14 and the
# eight-modulus aggregation chain, so every byte figure in the paper was taken
# at parameters the serving path does not use. runTournament serves at 2^15 on
# a fifteen-modulus chain, where a ciphertext is far larger. This job measures
# both chains at 2^14, 2^15 and 2^16 so the per-query total can be stated at the
# parameters that actually run.
#
# It also saves the bootstrapping key size and generation time to a record.
# Those two numbers are in the paper and have never had one.
#
# CPU-only. No --gres, so it runs beside a GPU job instead of taking a slot.
set -uo pipefail
cd /scratch/hkanpak21/HE_IFD/fhe
mkdir -p /scratch/hkanpak21/HE_IFD/results/fhe_serve/runs

source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/lmod/lmod/init/bash 2>/dev/null || true
module load go/1.24.4
export GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off GOFLAGS=-mod=mod

echo "[fhe_comm] go: $(go version)"
go build -o fhe-serve . || { echo "[fhe_comm] BUILD FAILED"; exit 1; }

OUT=/scratch/hkanpak21/HE_IFD/results/fhe_serve
echo "[fhe_comm] communication grid, two chains x three ring degrees x three federation sizes"
srun ./fhe-serve -comm-cost -json "$OUT/comm_grid.json" || echo "[fhe_comm] comm-cost FAILED"

echo "[fhe_comm] bootstrapping key material"
srun ./fhe-serve -btp-keys -json "$OUT/btp_keys.json" || echo "[fhe_comm] btp-keys FAILED"

echo "[fhe_comm] done."
