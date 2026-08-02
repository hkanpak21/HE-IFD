#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:40:00
#SBATCH --job-name=to_npz
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/personal_adapter/runs/npz_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/personal_adapter/runs/npz_%j.err

set -euo pipefail
cd /scratch/hkanpak21/HE_IFD
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
export HF_HUB_OFFLINE=1
exec srun python -u jobs/artifacts_to_npz.py \
  results/personal_adapter/artifacts results/personal_adapter_vision/artifacts
