#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --job-name=mia_ext_txt
#SBATCH --array=0-8
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_mia_surfaces/runs/txt_%A_%a.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_mia_surfaces/runs/txt_%A_%a.err

# B.9 text: released-vs-update MIA on {ag_news, dbpedia_14, banking77} x seeds
# {42,43,44}. 17 models/cell, per-model .npz resumable. Array index = cell.
set -euo pipefail
cd /scratch/hkanpak21/HE_IFD
mkdir -p results/heifd_mia_surfaces/runs
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false

exec srun python -u jobs/mia_surfaces_ext.py --modality text --cell-index "$SLURM_ARRAY_TASK_ID" "$@"
