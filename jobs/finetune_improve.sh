#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --job-name=ftimprove
#SBATCH --array=0-5
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/finetune_improve/runs/imp_%A_%a.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/finetune_improve/runs/imp_%A_%a.err

set -euo pipefail
cd /scratch/hkanpak21/HE_IFD
mkdir -p results/finetune_improve/runs
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl

export HF_HUB_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false

# Array index -> stage. s1 freeze-A vs both-A-B, s2 semantic head init,
# s3 client-side flags (CONDITIONAL — submit only if s1 leaves instability),
# s4 K x lr mini-grid, s5 rank compensation (banking77), s7 LOO robustness
# (issue fa04). One stage per array task; QOS serializes them onto one GPU.
# Per-cell JSONs make every stage resumable at the 3h wall-clock — resubmit.
# Core submission (skips conditional s3):  sbatch --array=0,1,3,4,5 jobs/finetune_improve.sh
# Prefetch first on the login node: roberta-base + the four HF datasets
# (ag_news, dbpedia_14, trec, banking77) must be in ~/.cache/huggingface.
STAGES=(s1 s2 s3 s4 s5 s7)
STAGE=${STAGES[$SLURM_ARRAY_TASK_ID]}

exec srun python -u jobs/finetune_improve.py --stage "$STAGE"
