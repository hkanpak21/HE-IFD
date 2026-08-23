#!/bin/bash
#SBATCH --partition=ai
#SBATCH --account=ai
#SBATCH --qos=ai
#SBATCH --gres=gpu:ampere_a40:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --job-name=cifarft
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/personal_adapter_vision/runs/fulltest_%x_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/personal_adapter_vision/runs/fulltest_%x_%j.err

# Table IV of the paper argues from margins of a few thousandths, and the
# largest of them, the cell where the selected arrangement beats the disclosed
# model by 0.005, is ten test images out of two thousand. vm.load_vision
# defaults to max_test=2000 against CIFAR-10's full 10000. This job reruns the
# four matched cells on the whole test set, which needs no retraining and
# multiplies the resolving power by five.
#
# One (N, alpha) per submission, three seeds each, so the four cells run at
# once. The summary JSON now carries N, alpha, K and the test size, so nothing
# collides. The authoritative output is still the CSV block in the .out log.
#
# Usage:
#   PA_N=20 PA_ALPHA=0.04 PA_MAXTEST=10000 sbatch --job-name=n20a004 jobs/cifar_fulltest.sh cifar10 42 43 44
set -euo pipefail
cd /scratch/hkanpak21/HE_IFD
mkdir -p results/personal_adapter_vision/runs
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
export HF_HUB_OFFLINE=1

echo "[cifarft] PA_N=${PA_N:-10} PA_ALPHA=${PA_ALPHA:-0.1} PA_K=${PA_K:-200} PA_MAXTEST=${PA_MAXTEST:-2000} args=$*"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
exec srun python -u jobs/personal_adapter_vision.py "$@"
