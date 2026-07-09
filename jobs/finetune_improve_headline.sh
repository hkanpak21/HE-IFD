#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --job-name=ftimp_hl
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/finetune_improve/runs/headline_%j.out

# Self-chaining headline backfill: re-run the tab:headline configs (4 text tasks,
# N=10, alpha=0.1, K=200, r=8, freeze-A, 3 seeds) with --force to add
# best_local/mean_local (per-client standalone accuracy on the global test set,
# for the "stronger than any single client trains alone" claim). The local phase
# is deterministic, so every existing number reproduces exactly; --force is
# idempotent (a cell already carrying best_local is skipped), so the chain
# converges when all 12 cells have the field.
set -uo pipefail
cd /scratch/hkanpak21/HE_IFD
mkdir -p results/finetune_improve/runs
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false

# Cap compute below the 3h Slurm wall so the chain logic always runs.
timeout 9600 srun python -u jobs/finetune_improve.py --stage headline --force || true

DONE=$(grep -l '"best_local"' \
        results/finetune_improve/cell_ag_news_roberta_base_N10_a0.1_s*_K200_r8_fa1_si0_*lr0.0005.json \
        results/finetune_improve/cell_trec_roberta_base_N10_a0.1_s*_K200_r8_fa1_si0_*lr0.0005.json \
        results/finetune_improve/cell_dbpedia_14_roberta_base_N10_a0.1_s*_K200_r8_fa1_si0_*lr0.0005.json \
        results/finetune_improve/cell_banking77_roberta_base_N10_a0.1_s*_K200_r8_fa1_si0_*lr0.0005.json \
        2>/dev/null | wc -l)
echo "[chain] headline cells with best_local: ${DONE}/12"
if [ "${DONE}" -lt 12 ]; then
  echo "[chain] resubmitting successor"
  sbatch jobs/finetune_improve_headline.sh
else
  echo "[chain] headline backfill complete, stopping"
fi
