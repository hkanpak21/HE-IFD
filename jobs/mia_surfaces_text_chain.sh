#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --job-name=mia_txt_chain
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_mia_surfaces/runs/txtchain_%j.out

# B.9 text (released-vs-update contrast), self-chaining. ag_news x 3 seeds,
# serial with per-model .npz + per-cell-JSON resume. Reuses the checkpoints
# already on disk (s42: 12 models, s43: 7 models). Resubmits until 3 JSONs.
set -uo pipefail
cd /scratch/hkanpak21/HE_IFD
mkdir -p results/heifd_mia_surfaces/runs
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false

timeout 9600 srun python -u jobs/mia_surfaces_ext.py --modality text || true

DONE=$(ls results/heifd_mia_surfaces/cell_ag_news_*twosurface_s*.json 2>/dev/null | wc -l)
echo "[chain] text MIA cells done: ${DONE}/3"
if [ "${DONE}" -lt 3 ]; then
  echo "[chain] resubmitting text successor"
  sbatch jobs/mia_surfaces_text_chain.sh
else
  echo "[chain] text MIA complete, stopping"
fi
