#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --job-name=heifd_016_amp_cnn5
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_016_signal_amp_cnn5/runs/amp_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_016_signal_amp_cnn5/runs/amp_%j.err
#
# Issue 016+ — signal-amplification diagnostic on CNN-5 / CIFAR-10.
#
# Context: results/heifd_fromscratch_verify/README.md shows the protocol fails
# BOTH participation-incentive gates on this regime —
#   IID raw_union α=1.0  = 0.5071  (gate 0.60)
#   m4_ood   α=0.05      = 0.1702  (gate 0.40)
# Six of sixteen teachers at α=0.05 sit at random (acc = 0.10), the warmed θ₀
# alone hits 0.2374 at α=0.05/raw_union_K20, and bounded-K distillation
# DEGRADES the aligned init back to 0.2058. Phase 0 is contributing the only
# useful signal — but raw_union_K20 mean-feature prototypes carry no
# inter-class structure. This case tests whether richer Phase-0 payloads lift
# θ₀ (and m4_ood) substantially.
#
# Four arms (Phase-0 lever amplification, distillation hparams held constant):
#   raw_union_K20         — baseline (the current failing config)
#   raw_union_K100        — "more of the same" — 5× the byte budget per class
#                           per client, same mechanism (no inter-class signal).
#   synthetic_K100        — same byte budget as raw_union_K100, but per-
#                           (client, class) Gaussian-around-mean samples
#                           (captures the client's view of class VARIANCE
#                           rather than transmitting raw records).
#   synthetic_logit_K100  — NOVEL — synthetic payload composed with per-class
#                           teacher-logit prototypes; warmup uses KL against
#                           the soft-label prototypes rather than CE against
#                           one-hot labels. Signal modality orthogonal to
#                           feature-space prototypes (carries inter-class
#                           confusion structure from teacher consensus).
#
# Grid: cnn5_cifar10 × N{16} × α{0.05, 1.0} × methods{4 above} × seeds{42}
#       × K_distill{300} × τ{4.0} × student_lr{0.01}  =  8 cells, 1 seed.
#
# CNN-5 backbone hparams (committed in src/protocol.py::BACKBONES["cnn5_cifar10"])
# stay unchanged: teacher_epochs=60, teacher_lr=0.01, cosine schedule,
# oracle_epochs=100, warmup_epochs=10. Teacher cache from the
# heifd_fromscratch_verify run on seed 42 is hot — only the Phase-0 builder
# + warmup paths differ across arms, so reuse is automatic. K_distill=300 is
# the legacy from-scratch default (the issue-010 K=100 pretrained finding
# does not transfer to full conv-net end-to-end training; different dynamics).
#
# Wall-clock: CNN-5 per cell ≈ 4-6 min on T4; 8 cells in one task ≈ 30-50 min;
# well inside the VALAR 3h cap with margin. No array needed.
#
# CIFAR-10 is pre-cached under data/cifar-10-batches-py/ (download=False); no
# pretrained weights needed, no login-node prefetch required.

set -euo pipefail
REPO=/scratch/hkanpak21/HE_IFD
CASE=heifd_016_signal_amp_cnn5
mkdir -p "${REPO}/results/${CASE}/runs"
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
cd "${REPO}"
echo "[016 amp] job ${SLURM_JOB_ID:-?} on $(hostname)"

exec srun python -u -m src.sweep \
    --backbones cnn5_cifar10 \
    --Ns 16 \
    --alphas 0.05,1.0 \
    --methods raw_union_K20,raw_union_K100,synthetic_K100,synthetic_logit_K100 \
    --seeds 42 \
    --K 300 \
    --tau 4.0 \
    --student-lr 0.01 \
    --case "${CASE}" \
    --results-root "${REPO}/results" \
    --data-root "${REPO}/data" \
    --cache-root "${REPO}/cache"
