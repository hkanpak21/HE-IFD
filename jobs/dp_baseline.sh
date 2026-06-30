#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --job-name=dp_base
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/dp_baseline/runs/dp_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/dp_baseline/runs/dp_%j.err

set -euo pipefail
cd /scratch/hkanpak21/HE_IFD
mkdir -p results/dp_baseline/runs
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl

export HF_HUB_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false

# opacus is installed ISOLATED in a scratch target dir (NOT in he_ofl, whose
# torch must stay 2.3.0 — installing opacus into he_ofl upgrades torch to 2.8
# and breaks transformers/peft). The job picks opacus up via PYTHONPATH; all
# else (torch/transformers/peft) comes from he_ofl.
export PYTHONPATH=/scratch/hkanpak21/dp_deps:${PYTHONPATH:-}

# DP comparator: centralized DP-SGD logistic head on frozen RoBERTa features,
# eps in {1,2,4,8} + non-private, over the 4 text tasks. Per-task JSON resumable.
exec srun python -u jobs/dp_baseline.py
