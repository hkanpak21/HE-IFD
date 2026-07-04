#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --job-name=ftimp_s9
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/finetune_improve/runs/s9_%j.out

# Self-chaining s9: trainable-unit axis (head-only r=0, r=4, r=16 on DBpedia)
# + N=100 (client-level checkpoints in cache/finetune_improve/ let the >3h
# cell finish across slots). Backs tab:setup's promised axes. Runs one ~2h40m
# slot, then resubmits itself until all 12 cells exist.
set -uo pipefail
cd /scratch/hkanpak21/HE_IFD
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false

# Cap compute below the 3h Slurm wall so the chain logic always runs.
timeout 9600 srun python -u jobs/finetune_improve.py --stage s9 || true

DONE=$(ls results/finetune_improve/cell_dbpedia_14*_r0_fa1* \
          results/finetune_improve/cell_dbpedia_14*_r4_fa1* \
          results/finetune_improve/cell_dbpedia_14*_r16_fa1_si0* \
          results/finetune_improve/cell_dbpedia_14*N100*_r8_fa1* 2>/dev/null | wc -l)
echo "[chain] s9 cells done: ${DONE}/12"
if [ "${DONE}" -lt 12 ]; then
  echo "[chain] resubmitting successor"
  sbatch jobs/finetune_improve_s9_chain.sh
else
  echo "[chain] s9 complete, stopping"
fi
