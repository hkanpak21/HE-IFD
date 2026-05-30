#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --job-name=heifd_026_lambda_verify
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_026_lambda_verify/runs/lambda_verify_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_026_lambda_verify/runs/lambda_verify_%j.err
#
# Issue 026 — task-arithmetic scaling coefficient λ, cheap EVAL-ONLY verify.
#
# THE QUESTION. Our server op θ⋆ = θ₀ + Σ_j w_j·Δ_j IS task arithmetic (Ilharco
# et al. 2023) with the scaling coefficient pinned to λ=1. The one optimization
# lever that fits {one-shot, HE depth-1} and that we have never tested is λ in
#
#     θ⋆(λ) = θ₀ + λ·Σ_j w_j·Δ_j = (1−λ)·θ₀ + λ·θ⋆(1).
#
# This is a pure INTERPOLATION between the basin θ₀ (λ=0) and the current
# aggregate θ⋆(1) (λ=1), so the whole curve is EVAL-ONLY: one bounded distillation
# trajectory per cell, then one ``aggregate`` reweight (a public-scalar multiply →
# still depth-1 under CKKS) + one test eval per λ. NO per-λ retraining. A peak at
# λ<1 ⇒ the basin deserves more trust; λ>1 ⇒ push harder along the trajectory;
# λ⋆≈1 with no lift ⇒ λ=1 holds and a λ grid is NOT worth running. Verify cheaply
# BEFORE committing any grid.
#
# Cells (issue-026 spec):
#   backbones {mlp_mnist, vit_b32_cifar100}                                  (2)
#   × N {10}                                                                 (1)
#   × α {0.05, 1.0}                                                          (2)
#   × method {raw_union_K20} (the raw_union basin source)                    (1)
#   × seeds {42}                                                             (1)
#   = 4 cells, each evaluating the full λ grid {0,0.25,…,2.0} (9 points).
# Fast (one trajectory + 9 evals per cell), well under the 3h VALAR cap.
# Resumable: re-submitting skips any cell whose JSON already records
# status=success (src/lambda_verify.py).
#
# NOTE backbone key: the issue prose says "mnist_mlp"; the registered BackboneSpec
# key is "mlp_mnist" (see src/protocol.py BACKBONES). We use the registry key.
#
# PREFETCH (login node, internet — compute nodes are offline): the ViT/CIFAR-100
# cell needs ViT-B/32 weights + CIFAR-100 in the HF/torch cache. Run once on the
# login node before submitting:
#     python jobs/prefetch_login.py --include-cifar100
# MNIST is pre-cached under data/ (download=False). The ViT feature cache is built
# on first use, or reuse the existing vit_b32_cifar100 caches from issue 012/022.

set -euo pipefail
REPO=/scratch/hkanpak21/HE_IFD
CASE=heifd_026_lambda_verify
mkdir -p "${REPO}/results/${CASE}/runs"
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
export HF_HUB_OFFLINE=1           # ViT-B/32 weights + CIFAR-100 pre-fetched on the login node
export TRANSFORMERS_OFFLINE=1
cd "${REPO}"
echo "[026 lambda_verify] job ${SLURM_JOB_ID:-?} on $(hostname)"

exec srun python -u -m src.lambda_verify \
    --backbones mlp_mnist,vit_b32_cifar100 \
    --Ns 10 \
    --alphas 0.05,1.0 \
    --methods raw_union_K20 \
    --seeds 42 \
    --K "${HEIFD_K:-300}" \
    --lambda-scales "${HEIFD_LAMBDAS:-0,0.25,0.5,0.75,1.0,1.25,1.5,1.75,2.0}" \
    --case "${CASE}" \
    --results-root "${REPO}/results" \
    --data-root "${REPO}/data" \
    --cache-root "${REPO}/cache"
