#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=04:00:00       # 64 shadow models per dataset; shadows dominate wall-clock
#SBATCH --job-name=mia_lira
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/mia/lira_%j.log
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/mia/lira_%j.err

# HE-IFD A7 post-release MIA (issue 21).
#
# Usage:
#   sbatch jobs/mia_lira.sh <student_ckpt_path> <dataset> <alpha> <seed> <variant>
#
# The first MIA job per (dataset, seed) pays the full 64-shadow training
# cost (~3-4 h on a T4 for LeNet-5 MNIST/FMNIST, slightly more for
# ResNet-8 CIFAR-10). Subsequent jobs reuse the cache at
# results/shadows/<dataset>_<seed>/ and run in minutes (scoring only).

set -euo pipefail

mkdir -p /scratch/hkanpak21/HE_IFD/results/mia

cd /scratch/hkanpak21/HE_IFD
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl

exec srun python -u prototypes/mia_lira.py \
    --student-ckpt "$1" --dataset "$2" --alpha "$3" --seed "$4" --variant "$5" \
    --n-shadows 64 --shadow-cache results/shadows
