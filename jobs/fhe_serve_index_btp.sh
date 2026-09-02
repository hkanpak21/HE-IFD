#!/bin/bash
#SBATCH --partition=ai
#SBATCH --account=ai
#SBATCH --qos=ai
#SBATCH --cpus-per-task=16
#SBATCH --mem=200G
#SBATCH --time=72:00:00
#SBATCH --job-name=fhe_index_btp
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/fhe_serve/runs/serve_index_btp_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/fhe_serve/runs/serve_index_btp_%j.err

# The encrypted argmax INDEX with level restoration done by the serving party
# alone, under collectively generated bootstrapping keys. argmax_index.csv measured
# the index under a collective refresh, which is not the mechanism the paper
# describes; this measures it under the one that is. The bootstrapping ring is 2^16,
# so the key material and the working set are large. CPU-only: no --gres, so it
# schedules beside GPU work.
set -euo pipefail
cd /scratch/hkanpak21/HE_IFD/fhe
mkdir -p /scratch/hkanpak21/HE_IFD/results/fhe_serve/runs
source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/lmod/lmod/init/bash 2>/dev/null || true
module load go/1.24.4
export GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off GOFLAGS=-mod=mod
go build -o /scratch/hkanpak21/HE_IFD/fhe/fhe-serve-index-btp .
exec srun /scratch/hkanpak21/HE_IFD/fhe/fhe-serve-index-btp \
  -serve-index-btp -json /scratch/hkanpak21/HE_IFD/results/fhe_serve/argmax_index_btp.json
