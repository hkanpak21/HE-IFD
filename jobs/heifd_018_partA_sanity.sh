#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --job-name=heifd_018A
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_018_partA_sanity/runs/partA_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_018_partA_sanity/runs/partA_%j.err
#
# Issue 018 — PART A: standalone centralised linear-probe sanity-check on the
# big pretrained backbones, BEFORE running the protocol on them. Part B (the
# protocol + LoRA on big backbones) is HITL-gated: the orchestrator routes
# these Part-A numbers to the user and does NOT submit Part B until the user
# authorises it. This wrapper builds ONLY Part A.
#
# What "standalone linear-probe baseline" maps to in this codebase:
#   ``protocol.run_cell`` already trains a centralised supervised head on the
#   FULL training pool (``oracle_m``) and evaluates it on the held-out test set,
#   reporting it as ``res.oracle``. With N=1, α=1.0 the pool IS the whole
#   training set minus the small labelled probe, so ``res.oracle`` is exactly
#   the centralised linear-probe / supervised-head baseline this sanity-check
#   wants. We therefore run ONE cheap cell per backbone (method=no_phase0 so no
#   Phase-0 probe is built; K=1 so the irrelevant distillation step is near-free
#   — the GATE reads ``oracle``, not ``acc``) and read ``oracle`` from the JSON.
#
# Per-backbone gates (oracle = IID centralised linear-probe acc):
#   vit_l_cifar100      IID >= 0.78   (BLOCKING: fail => STOP, report)
#   bert_large_agnews   IID >= 0.92   (BLOCKING: fail => STOP, report)
#   gpt2_medium_agnews  IID >= 0.50   (INFORMATIONAL ONLY: failure is NOT a block)
#
# One backbone per job (set HEIFD_018_BACKBONE) — ViT-L/16 and BERT-large
# feature extraction (304M / 335M param models over the full CIFAR-100 /
# AG-News train+test sets at batch 128 on a single T4) is the heavy part and is
# the reason memory is 64G and each backbone is isolated to its own ≤3h job.
# The first cell per backbone extracts + caches features; a resubmit hits the
# hot cache (sweep.py skips the already-successful cell JSON).
#
# Submit (one per backbone):
#   sbatch --export=ALL,HEIFD_018_BACKBONE=vit_l_cifar100     jobs/heifd_018_partA_sanity.sh
#   sbatch --export=ALL,HEIFD_018_BACKBONE=bert_large_agnews  jobs/heifd_018_partA_sanity.sh
#   sbatch --export=ALL,HEIFD_018_BACKBONE=gpt2_medium_agnews jobs/heifd_018_partA_sanity.sh
#
# Prefetch prerequisite (login node, has internet; compute node does not):
#   python jobs/prefetch_login.py --include-cifar100 --include-big-backbones
# (CIFAR-100 dataset for ViT-L; the three big backbone weights for all three.)

set -euo pipefail
REPO=/scratch/hkanpak21/HE_IFD
BB="${HEIFD_018_BACKBONE:?set HEIFD_018_BACKBONE=<vit_l_cifar100|bert_large_agnews|gpt2_medium_agnews>}"
CASE=heifd_018_partA_sanity
mkdir -p "${REPO}/results/${CASE}/runs"
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
cd "${REPO}"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1   # weights pre-fetched on login node
echo "[018-partA] job ${SLURM_JOB_ID:-?} backbone=${BB} on $(hostname)"

# Single centralised-baseline cell. N=1, α=1.0 => pool = full train set; the
# ``oracle`` field is the standalone linear-probe acc the gate checks. K=1,
# no_phase0 keep everything else near-free.
exec srun python -u -m src.sweep \
    --backbones "${BB}" \
    --Ns 1 \
    --alphas 1.0 \
    --methods no_phase0 \
    --seeds 42 \
    --K 1 \
    --tau 1 \
    --student-lr 0.001 \
    --case "${CASE}" \
    --results-root "${REPO}/results" \
    --data-root "${REPO}/data" \
    --cache-root "${REPO}/cache"
