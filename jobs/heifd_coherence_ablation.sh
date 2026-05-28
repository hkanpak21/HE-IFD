#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --job-name=heifd_cohabl
#SBATCH --array=0-5
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_coherence_ablation/runs/cohabl_%A_%a.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_coherence_ablation/runs/cohabl_%A_%a.err
#
# Aggregation-coherence ablation (issue 006 / PRD user story 17): the empirical
# "why the design works" evidence. On each shared cell the partition, per-client
# teachers, and raw_union Phase-0-aligned θ₀ are held FIXED; only how each client's
# student travelled from θ₀ varies across four regimes:
#   heifd                    -> bounded K-step distillation from shared θ₀ (ours)
#   converged_shared_init    -> supervised-to-convergence from shared θ₀, averaged
#   converged_diff_init      -> supervised-to-convergence from DIFFERENT inits, averaged
#   unbounded_distill_shared -> UNBOUNDED (long-K) distillation from shared θ₀, averaged
# Every regime's server op is the SAME linear θ_ref+Σ w_i·Δ_i (PT×CT+CT+CT).
#
# Grid: {mlp_mnist, cnn5_cifar10} × α{0.05, 0.3} × N=10 × seeds{42,43,44} = 12
#       cells, split across a 6-task array (round-robin → 2 cells/task) so each
#       task stays well under the VALAR 3h hard cap. Resumable: a re-submit skips
#       cells whose JSON already records status=success (see src/ablation.py).
# Datasets (MNIST, CIFAR-10) are pre-cached under data/ with download=False — no
# pretrained backbones, so no login-node HF pre-fetch is required for this job.

set -euo pipefail
REPO=/scratch/hkanpak21/HE_IFD
CASE=heifd_coherence_ablation
mkdir -p "${REPO}/results/${CASE}/runs"
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
cd "${REPO}"
echo "[cohabl] job ${SLURM_ARRAY_JOB_ID:-?} task ${SLURM_ARRAY_TASK_ID:-0}/${SLURM_ARRAY_TASK_COUNT:-1} on $(hostname)"

exec srun python -u -m src.ablation \
    --backbones mlp_mnist,cnn5_cifar10 \
    --Ns 10 \
    --alphas 0.05,0.3 \
    --seeds 42,43,44 \
    --K "${HEIFD_K:-300}" \
    --unbounded-K "${HEIFD_UNBOUNDED_K:-3000}" \
    --converge-epochs "${HEIFD_CONVERGE_EPOCHS:-40}" \
    --K-per-class 20 \
    --case "${CASE}" \
    --results-root "${REPO}/results" \
    --data-root "${REPO}/data" \
    --cache-root "${REPO}/cache" \
    --num-chunks "${SLURM_ARRAY_TASK_COUNT:-6}" \
    --chunk-index "${SLURM_ARRAY_TASK_ID:-0}"
