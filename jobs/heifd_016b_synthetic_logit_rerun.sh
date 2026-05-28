#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --job-name=heifd_016b_synlogit
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_016b_synthetic_logit/runs/synlogit_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_016b_synthetic_logit/runs/synlogit_%j.err
#
# Issue 016b — synthetic_logit re-run after the conv2d shape-bug fix.
#
# THE BUG (now fixed in src/protocol.py + src/phase0.py)
# ------------------------------------------------------
# In issue 016 every synthetic_logit_K100 cell on CNN-5 FAILED with
#   RuntimeError: Expected 3D (unbatched) or 4D (batched) input to conv2d
# Root cause: the synthetic_logit Phase-0 path fed FLATTENED (n_i, 3072)
# per-client tensors to build_logit_prototypes, which runs them THROUGH the
# conv teachers (teacher(X_i)); conv2d rejects flat input. The plain
# synthetic_K100 path survived because it only generates Gaussian samples in
# flat feature space (no teacher forward pass). Fix: feed the synthetic-sample
# path the flat tensors and the logit-prototype path the NATIVE-shape tensors
# (no-op for pretrained-feature backbones, where native IS flat).
#
# THE RUN
# -------
# Two backbones, two KD configs, ONE results case:
#
#   A) cnn5_cifar10 (from-scratch conv — the case that failed):
#        K_distill=300, τ=4, lr=0.01  (legacy from-scratch defaults — match the
#        ORIGINAL failing config so we confirm the shape fix works and read the
#        synthetic_logit arm's number under the same KD knobs as issue 016).
#
#   B) resnet18_cifar10 (pretrained linear head — synthetic samples live in
#      smooth cached-feature space, NOT pixel space, so should behave far better):
#        K_distill=100, τ=1, lr=0.001  (the issue-010 resnet18 best — this
#        backbone needs τ=1).
#
# Methods (both backbones): synthetic_logit_K100 (NOVEL, the fixed arm) +
# synthetic_K100 (plain synthetic, to isolate the logit modality's effect) +
# raw_union_K20 (the minimal-leak baseline reference).
#
# Grid: 3 methods × 2 backbones × α{0.05, 1.0} × seed{42} = 12 cells.
#   cnn5 arm:     3 × 2 = 6 cells at K=300/τ=4/lr=0.01
#   resnet18 arm: 3 × 2 = 6 cells at K=100/τ=1/lr=0.001
#
# WIN / READ-OUT:
#   - Primary: confirm synthetic_logit_K100 RUNS (no conv2d crash) on cnn5.
#   - Compare synthetic_logit_K100 vs synthetic_K100 vs raw_union_K20 on
#     theta0_acc + acc + m4_ood. Does the orthogonal teacher-logit modality
#     lift the aligned init / OOD acc over plain feature prototypes?
#   - Cross-backbone: synthetic samples in resnet18 feature space should
#     behave far better than in cnn5 pixel space.
#
# Teacher caches: cnn5_cifar10/seed42/N16/α∈{0.05,1.0} is hot from
# heifd_fromscratch_verify + heifd_016_signal_amp_cnn5. resnet18_cifar10/seed42/
# N16/α∈{0.05,1.0} is hot from the headline pretrained runs / issue 010 — both
# reused automatically. CIFAR-10 pre-cached (download=False). resnet18 weights
# load offline from cache (HF_HUB_OFFLINE=1); the login node must have populated
# ~/.cache/torch already (it has, from prior resnet18 runs).
#
# Wall-clock: cnn5 cells ≈ 4-6 min (K=300), resnet18 head cells ≈ 1-2 min
# (cheap head + K=100). 12 cells ≈ 35-55 min — well inside the 3h cap.

set -euo pipefail
REPO=/scratch/hkanpak21/HE_IFD
CASE=heifd_016b_synthetic_logit
mkdir -p "${REPO}/results/${CASE}/runs"
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
export HF_HUB_OFFLINE=1
cd "${REPO}"
echo "[016b synlogit] job ${SLURM_JOB_ID:-?} on $(hostname)"

# ---- arm A: cnn5_cifar10 (from-scratch) at legacy K=300/τ=4/lr=0.01 ----
echo "[016b synlogit] arm A: cnn5_cifar10 (K=300, tau=4, lr=0.01)"
srun python -u -m src.sweep \
    --backbones cnn5_cifar10 \
    --Ns 16 \
    --alphas 0.05,1.0 \
    --methods synthetic_logit_K100,synthetic_K100,raw_union_K20 \
    --seeds 42 \
    --K 300 \
    --tau 4.0 \
    --student-lr 0.01 \
    --case "${CASE}" \
    --results-root "${REPO}/results" \
    --data-root "${REPO}/data" \
    --cache-root "${REPO}/cache"

# ---- arm B: resnet18_cifar10 (pretrained head) at issue-010 best K=100/τ=1/lr=0.001 ----
echo "[016b synlogit] arm B: resnet18_cifar10 (K=100, tau=1, lr=0.001)"
exec srun python -u -m src.sweep \
    --backbones resnet18_cifar10 \
    --Ns 16 \
    --alphas 0.05,1.0 \
    --methods synthetic_logit_K100,synthetic_K100,raw_union_K20 \
    --seeds 42 \
    --K 100 \
    --tau 1.0 \
    --student-lr 0.001 \
    --case "${CASE}" \
    --results-root "${REPO}/results" \
    --data-root "${REPO}/data" \
    --cache-root "${REPO}/cache"
