#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --job-name=mia_ext_vis
#SBATCH --array=0-2
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_mia_surfaces/runs/vis_%A_%a.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_mia_surfaces/runs/vis_%A_%a.err

# B.8 + B.9 vision: released-vs-update MIA on ViT-B/16 / CIFAR-100, seeds
# {42,43,44} (array index = seed). Backs the vision row of the MIA table and
# the training-vs-inference contrast on vision. 17 ViT models/cell; per-model
# .npz resumable — resubmit the index if a cell hits the 3h wall.
# Prefetch google/vit-base-patch16-224-in21k + CIFAR-100 on the login node.
set -euo pipefail
cd /scratch/hkanpak21/HE_IFD
mkdir -p results/heifd_mia_surfaces/runs
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false

exec srun python -u jobs/mia_surfaces_ext.py --modality vision --cell-index "$SLURM_ARRAY_TASK_ID" "$@"
