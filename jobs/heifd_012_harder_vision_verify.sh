#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --job-name=heifd_012v
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_012_harder_vision_verify/runs/verify_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_012_harder_vision_verify/runs/verify_%j.err
#
# Issue 012 — Harder vision dataset (CIFAR-100, Tiny-ImageNet) verify run.
# CIFAR-10 on ViT-B/32 is saturated at 0.97 IID (issue 008, see STATUS); this
# verify exercises the new BACKBONES entries (resnet18_cifar100,
# vit_b32_cifar100, plus the Tiny-ImageNet pair) on the minimal 4-cell grid
# that establishes whether distillation now adds value over θ₀:
#
#   backbones: vit_b32_cifar100 + resnet18_cifar100
#              (+ optional vit_b32_tiny_imagenet + resnet18_tiny_imagenet if
#               --include-tiny-imagenet was passed to prefetch_login.py and
#               HEIFD_012_INCLUDE_TINY=1 is set in the submit env)
#   methods:   no_phase0, raw_union_K20
#   N=16, α=0.05, seed=42 (matches the issue 011 verify regime)
#   KD hparams: K=100, τ=1, lr=0.001  (the issue 010 best defaults for the
#               pretrained-head regime — issue 011 confirmed head_only is
#               sufficient, so 012 stays head_only by default and tests the
#               harder-dataset axis in isolation)
#
# Success signature (what the orchestrator checks before submitting the
# full-grid wrapper):
#   * ViT/CIFAR-100 IID linear-probe (θ₀ or oracle, whichever applies) >= 0.60
#     (gate from issue 012; ceiling expected 0.75-0.80).
#   * ViT/CIFAR-100 raw_union_K20 > θ₀ at α=0.05 (distillation adds value —
#     the headline question issue 012 was created to answer).
#   * ResNet/CIFAR-100 raw_union_K20 in 0.50-0.65 region; θ₀ comparable.
#   * If Tiny-ImageNet included: ViT IID 0.55-0.65, ResNet IID 0.45-0.55.
#
# Resumable / chunkable via sweep.py's per-cell JSON skip-on-success. Memory
# bumped to 32G (CIFAR-100 features at ViT-B/32 dimension 768 are ~3× larger
# in cache footprint than CIFAR-10; Tiny-ImageNet adds a ~100k-image train
# tensor at 64×64 raw, which the extractor reads into GPU 128 at a time).
#
# Datasets:
#   * CIFAR-100 pre-fetched by `python jobs/prefetch_login.py --include-cifar100`
#     on the VALAR login node before this job (populates data/cifar-100-python/).
#   * Tiny-ImageNet pre-fetched by `--include-tiny-imagenet` on the login
#     node (populates data/tiny-imagenet-200/; download is ~250MB so it is
#     deliberately opt-in).
#
# Submit:
#   sbatch jobs/heifd_012_harder_vision_verify.sh                         # CIFAR-100 only
#   sbatch --export=ALL,HEIFD_012_INCLUDE_TINY=1 jobs/heifd_012_harder_vision_verify.sh

set -euo pipefail
REPO=/scratch/hkanpak21/HE_IFD
CASE=heifd_012_harder_vision_verify
mkdir -p "${REPO}/results/${CASE}/runs"
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
cd "${REPO}"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1   # weights pre-fetched on login node
echo "[012-verify] job ${SLURM_JOB_ID:-?} on $(hostname)"

# CIFAR-100 is always included; Tiny-ImageNet opt-in via env var so the
# default verify run lands on the higher-value cell first.
BACKBONES_LIST="vit_b32_cifar100,resnet18_cifar100"
if [[ "${HEIFD_012_INCLUDE_TINY:-0}" == "1" ]]; then
    BACKBONES_LIST="${BACKBONES_LIST},vit_b32_tiny_imagenet,resnet18_tiny_imagenet"
    echo "[012-verify] Tiny-ImageNet included (HEIFD_012_INCLUDE_TINY=1)"
fi

exec srun python -u -m src.sweep \
    --backbones "${BACKBONES_LIST}" \
    --Ns 16 \
    --alphas 0.05 \
    --methods no_phase0,raw_union_K20 \
    --seeds 42 \
    --K 100 \
    --tau 1 \
    --student-lr 0.001 \
    --case "${CASE}" \
    --results-root "${REPO}/results" \
    --data-root "${REPO}/data" \
    --cache-root "${REPO}/cache"
