#!/bin/bash
#SBATCH --partition=ai
#SBATCH --account=ai
#SBATCH --qos=ai
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --job-name=fhe_serve_real
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/fhe_serve/runs/serve_real_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/fhe_serve/runs/serve_real_%j.err

# One real query, end to end: a real trained head, real query features, the
# encrypted serving path, and the label the querier alone decrypts. Needs the
# export jobs/fhe_export_head.sh writes first. CPU-only: no --gres, so it
# schedules beside GPU work.
set -euo pipefail
EXPORT="${1:-/scratch/hkanpak21/HE_IFD/results/fhe_serve/real_query/ag_news_s42_A.json}"
TAG="$(basename "${EXPORT%.json}")"
cd /scratch/hkanpak21/HE_IFD/fhe
module load go/1.24.4
go build -o /scratch/hkanpak21/HE_IFD/fhe/fhe-serve-real .
exec srun /scratch/hkanpak21/HE_IFD/fhe/fhe-serve-real \
  -serve-real "$EXPORT" -logn 15 -real-parties 10 \
  -json "/scratch/hkanpak21/HE_IFD/results/fhe_serve/real_query/${TAG}_answers.json"
