#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --job-name=heifd_016b_distill_cnn5
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_016b_distill_debug_cnn5/runs/distill_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_016b_distill_debug_cnn5/runs/distill_%j.err
#
# Issue 016b — distillation-debugging on CNN-5 / CIFAR-10 with CORRECT KD hparams.
#
# THE QUESTION
# ------------
# Does the HE-secure bounded-K-step KL distillation ADD VALUE over θ₀ when given
# correct KD hyperparameters (τ=1), with the leak-minimised Phase-0 alignment
# held FIXED at raw_union_K20?
#
# Background. Issue 016 (results/heifd_016_signal_amp_cnn5/) found that
# "distillation degrades θ₀" on CNN-5 — but EVERY cell there distilled at
# τ=4 / K=300 / lr=0.01, the legacy from-scratch defaults. Issue 010
# (results/heifd_010_kd_hparams_resnet18/) showed that on resnet18 τ is the
# dominant KD lever: τ=4 DEGRADES (acc 0.48) while τ=1 RECOVERS (acc 0.76).
# That τ fix was applied ONLY to resnet18, never to CNN-5. So the 016
# "distillation degrades" finding is CONFOUNDED by known-bad KD hparams.
# This job de-confounds it.
#
# Alignment is deliberately held MINIMAL (raw_union_K20, the low-leak default —
# raw prototypes are released in clear, so the Phase-0 payload must stay SMALL).
# The research goal is that the DISTILLATION carries the learning, not the
# alignment. We do NOT fatten K_pc here (no K100); we vary only the distillation
# knobs.
#
# Grid: cnn5_cifar10 × N{16} × α{0.05, 1.0} × method{raw_union_K20} × seed{42}
#       × Ks{30, 100, 300} × τ{1, 4} × student_lr{0.001, 0.01}
#       = 2 × 3 × 2 × 2 = 24 cells, 1 seed (diagnostic).
#
# WIN CONDITION (per (K, τ, lr) cell): acc > theta0_acc, i.e. the distilled+
# aggregated student beats the aligned init it started from -> distillation
# adds value. Compare acc vs theta0_acc per cell in the auto-written results.
# The headline contrast is the τ=1 cells vs the τ=4 cells:
#   - if τ=1 makes distillation beat θ₀ on CNN-5  -> mechanism is sound, τ=4 was the bug;
#   - if τ=1 STILL degrades θ₀ on CNN-5           -> full-from-scratch-deep-net
#     distillation is outside the basin-coherence envelope (consistent with
#     issue 011's last_block basin-escape finding) — a clean scoping statement.
#
# CNN-5 backbone hparams (BACKBONES["cnn5_cifar10"]) stay unchanged:
# teacher_epochs=60, teacher_lr=0.01, cosine schedule, oracle_epochs=100,
# warmup_epochs=10. The teacher cache for cnn5_cifar10/seed42/N16/α∈{0.05,1.0}
# is already hot from heifd_fromscratch_verify + heifd_016_signal_amp_cnn5 —
# only the distillation knobs change, so teacher reuse is automatic and only
# the K-step trajectory is recomputed per cell.
#
# Wall-clock: CNN-5 per cell ≈ 4-6 min on T4 (teachers cached; only distill +
# eval recompute). 24 cells ≈ 1.5-2.5h — inside the VALAR 3h cap. Single task,
# no array. If a future re-run trends near the wall, split with
# NUM_CHUNKS=2 / CHUNK_INDEX={0,1} via a 2-task array (sweep.py is resumable —
# completed cell_*.json are skipped on resubmission).
#
# CIFAR-10 is pre-cached under data/cifar-10-batches-py/ (download=False); no
# pretrained weights, no login-node prefetch required.

set -euo pipefail
REPO=/scratch/hkanpak21/HE_IFD
CASE=heifd_016b_distill_debug_cnn5
mkdir -p "${REPO}/results/${CASE}/runs"
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
cd "${REPO}"
echo "[016b distill] job ${SLURM_JOB_ID:-?} on $(hostname)"

exec srun python -u -m src.sweep \
    --backbones cnn5_cifar10 \
    --Ns 16 \
    --alphas 0.05,1.0 \
    --methods raw_union_K20 \
    --seeds 42 \
    --Ks 30,100,300 \
    --taus 1,4 \
    --student-lrs 0.001,0.01 \
    --case "${CASE}" \
    --results-root "${REPO}/results" \
    --data-root "${REPO}/data" \
    --cache-root "${REPO}/cache"
