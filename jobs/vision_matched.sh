#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --job-name=vis_match
#SBATCH --array=0-3
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/vision_matched/runs/vm_%A_%a.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/vision_matched/runs/vm_%A_%a.err

set -euo pipefail
cd /scratch/hkanpak21/HE_IFD
mkdir -p results/vision_matched/runs
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl

export HF_HUB_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false

# Array index -> stage: 0 s6 (CIFAR-100 vision arm), 1 dense (CIFAR-10 N=5),
# 2 fedaux (CIFAR-10 N=20), 3 fedsd2c (Tiny-ImageNet N=10). Per-cell JSON
# resumable — resubmit an index after a TIMEOUT to finish its remainder.
# Prefetch on login node first: google/vit-base-patch16-224-in21k +
# uoft-cs/cifar10 + uoft-cs/cifar100 + zh-plus/tiny-imagenet.
exec srun python -u jobs/vision_matched.py --stage "$SLURM_ARRAY_TASK_ID"
