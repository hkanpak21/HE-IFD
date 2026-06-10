#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --job-name=ftinc_e3
#SBATCH --array=0-3
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/finetune_increment_e3/runs/e3_%A_%a.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/finetune_increment_e3/runs/e3_%A_%a.err

set -euo pipefail
cd /scratch/hkanpak21/HE_IFD
mkdir -p results/finetune_increment_e3/runs
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl

# roberta-base + dbpedia_14 are pre-cached on VALAR -> run fully offline.
export HF_HUB_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false

# Job-array index -> number of clients N. One N (x3 seeds) per array task, each
# well under the wall-clock; per-(N,seed) cell JSONs make a resumed task skip
# finished work.
NS=(10 20 50 100)
N=${NS[$SLURM_ARRAY_TASK_ID]}

exec srun python -u jobs/finetune_increment_e3.py --N "$N"
