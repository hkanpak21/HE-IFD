#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --job-name=llm_scale
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/llm_scale/runs/llm_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/llm_scale/runs/llm_%j.err

set -euo pipefail
cd /scratch/hkanpak21/HE_IFD
mkdir -p results/llm_scale/runs
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl

export HF_HUB_OFFLINE=1
export HF_DATASETS_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false

# fa03: 4 cells ({ag_news, dbpedia_14} x seeds {42,43}), per-cell JSON
# resumable. Prefetch Qwen/Qwen2.5-0.5B on the login node first.
exec srun python -u jobs/llm_scale.py --backbone qwen25_05b
