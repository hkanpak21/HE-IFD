#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --job-name=ftimp_s8
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/finetune_improve/runs/s8_%j.out

# Self-chaining s8 sweep: runs one ~3h slot of the heterogeneity/client-count
# sweep (resumes from per-cell JSONs), then, if fewer than 18 het/N cells
# exist, submits its own successor before exiting. Runs entirely on VALAR, so
# it survives the local session ending and VPN drops — no local loop needed.
# Stops automatically once all 18 cells are present.
set -uo pipefail
cd /scratch/hkanpak21/HE_IFD
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false

# Cap the compute at 2h40m so the chain logic below ALWAYS runs before the 3h
# Slurm wall (which would otherwise kill the whole script, resubmit included).
# Per-cell JSONs make the early exit lossless: a cell interrupted mid-compute is
# simply redone next slot.
timeout 9600 srun python -u jobs/finetune_improve.py --stage s8 || true

DONE=$(ls results/finetune_improve/cell_dbpedia_14*a0.05* \
          results/finetune_improve/cell_dbpedia_14*a0.3* \
          results/finetune_improve/cell_dbpedia_14*a1.0* \
          results/finetune_improve/cell_dbpedia_14*N20* \
          results/finetune_improve/cell_dbpedia_14*N50* \
          results/finetune_improve/cell_dbpedia_14*N100* 2>/dev/null | wc -l)
echo "[chain] s8 cells done: ${DONE}/18"
if [ "${DONE}" -lt 18 ]; then
  echo "[chain] resubmitting successor"
  sbatch jobs/finetune_improve_s8_chain.sh
else
  echo "[chain] s8 complete, stopping"
fi
