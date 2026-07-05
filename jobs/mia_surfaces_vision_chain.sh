#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --job-name=mia_vis_chain
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_mia_surfaces/runs/vischain_%j.out

# B.8 + B.9 vision, self-chaining (like s9): the 17 ViT models per cell exceed
# one 3h slot under GPU contention, and Slurm array tasks do NOT resume, so we
# run all 3 CIFAR-100 cells SERIALLY with per-model .npz + per-cell-JSON resume,
# cap compute below the wall, and resubmit until all 3 cell JSONs exist.
# PRIORITY over text: it backs the missing MIA table row.
set -uo pipefail
cd /scratch/hkanpak21/HE_IFD
mkdir -p results/heifd_mia_surfaces/runs
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false

timeout 9600 srun python -u jobs/mia_surfaces_ext.py --modality vision || true

DONE=$(ls results/heifd_mia_surfaces/cell_cifar100_*twosurface_s*.json 2>/dev/null | wc -l)
echo "[chain] vision MIA cells done: ${DONE}/3"
if [ "${DONE}" -lt 3 ]; then
  echo "[chain] resubmitting vision successor"
  sbatch jobs/mia_surfaces_vision_chain.sh
else
  echo "[chain] vision MIA complete; kicking off text chain"
  sbatch jobs/mia_surfaces_text_chain.sh
fi
