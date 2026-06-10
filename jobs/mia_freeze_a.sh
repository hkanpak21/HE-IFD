#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --job-name=mia_fa
#SBATCH --array=0-11
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_mia_freeze_a/runs/mia_%A_%a.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_mia_freeze_a/runs/mia_%A_%a.err

set -euo pipefail
cd /scratch/hkanpak21/HE_IFD
mkdir -p results/heifd_mia_freeze_a/runs
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl

export HF_HUB_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false

# Array index = cell index into TASKS x SEEDS (4 tasks x 3 seeds = 12 cells).
# 17 federated models per cell (1 target + 16 shadows); per-model .npz
# checkpoints make a wall-clock kill resumable — just resubmit the index.
# Submit AFTER fa01-s1/s2 verdicts; pass --sem-init if S2 promotes it.
exec srun python -u jobs/mia_freeze_a.py --cell-index "$SLURM_ARRAY_TASK_ID" "$@"
