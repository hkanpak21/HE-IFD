#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --job-name=ftinc_sw
#SBATCH --array=0-3
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/finetune_increment_sweep/runs/sw_%A_%a.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/finetune_increment_sweep/runs/sw_%A_%a.err

set -euo pipefail
cd /scratch/hkanpak21/HE_IFD
mkdir -p results/finetune_increment_sweep/runs
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl

export HF_HUB_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false

# Array index -> stage. e2 heterogeneity (+E6 lambda), e4 K-sweep, e5 public-base
# ablation, e1b MPNet. One stage per array task; QOS serializes them to one GPU.
STAGES=(e2 e4 e5 e1b)
STAGE=${STAGES[$SLURM_ARRAY_TASK_ID]}

exec srun python -u jobs/finetune_increment_sweep.py --stage "$STAGE"
