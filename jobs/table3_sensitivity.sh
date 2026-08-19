#!/bin/bash
#SBATCH --partition=ai
#SBATCH --account=ai
#SBATCH --qos=ai
#SBATCH --gres=gpu:ampere_a40:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=10:00:00
#SBATCH --job-name=tab3
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/personal_adapter/runs/tab3_%x_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/personal_adapter/runs/tab3_%x_%j.err

# Table III of the paper prints five numbers that trace to no record.
# The skew row at alpha 0.05, 0.30 and 1.00, and the local-steps row at K=100
# and K=400. The audit of 2026-08-20 found them. This job produces the record.
#
# One config per submission. PA_ALPHA, PA_K and the seed list come from the
# caller, so the five cells run as five jobs at once, which the ai partition
# allows. The artifact filenames already carry N, alpha, K and seed, and the
# summary JSON now does too, so nothing collides.
#
# The authoritative output is the CSV block printed at the end of the log.
#
# Usage:
#   PA_ALPHA=0.05 sbatch --job-name=a005 jobs/table3_sensitivity.sh dbpedia_14 42 43 44
#   PA_K=100      sbatch --job-name=k100 jobs/table3_sensitivity.sh dbpedia_14 42
set -euo pipefail
cd /scratch/hkanpak21/HE_IFD
mkdir -p results/personal_adapter/runs
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
export HF_HUB_OFFLINE=1

echo "[tab3] PA_N=${PA_N:-10} PA_ALPHA=${PA_ALPHA:-0.1} PA_K=${PA_K:-200} args=$*"
nvidia-smi --query-gpu=name --format=csv,noheader
exec srun python -u jobs/personal_adapter_test.py "$@"
