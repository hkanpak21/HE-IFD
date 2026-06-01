#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --job-name=ft02_hr
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/ft02_headroom/runs/headroom_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/ft02_headroom/runs/headroom_%j.err
#
# Issue ft02 — Linear-probe HEADROOM CHECK (the dataset selection criterion).
#
# For each (backbone, dataset) it fits a single nn.Linear probe on the FROZEN
# features the protocol would use (cached once, offline) and reports train/test
# accuracy + a KEEP/DROP verdict: test_acc < ceiling (0.90) ⇒ KEEP (the task is
# NOT linear-probe-solved, fine-tuning has headroom); >= ceiling ⇒ DROP (too
# easy, like ViT/CIFAR-10 at 0.97 — the saturation the pivot fixes).
#
# It ALSO emits results/ft02_headroom/partition_diagnostic.jsonl by running the
# unchanged seed-keyed Dirichlet partition on each new dataset (acceptance item).
#
# PREREQ (login node, once — see jobs/prefetch_login.py docstrings for the
# per-dataset fetch + license; CUB-200 and Stanford Cars are MANUAL placements):
#   python jobs/prefetch_login.py --include-text019 --include-ft02-text --include-ft02-fgvc
#   # then manually place CUB_200_2011/ and stanford_cars/ under data/ if used.
#
# Resumable note: the EXPENSIVE step (frozen-feature extraction) is cached per
# (backbone, dataset) under cache/features/, so a re-submission re-uses features
# and only re-fits the cheap linear probe. Select a subset with --backbones.
#
# Submit (CUB needs manual data; default list below is the auto-fetchable subset
# plus CUB/Cars which will FAIL-gracefully-and-report if their data is absent):
#   sbatch jobs/ft02_headroom.sh
#   sbatch --export=ALL,FT02_BACKBONES=vit_b32_fgvc_aircraft,roberta_base_banking77 jobs/ft02_headroom.sh

set -euo pipefail
REPO=/scratch/hkanpak21/HE_IFD
CASE=ft02_headroom
mkdir -p "${REPO}/results/${CASE}/runs"
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
cd "${REPO}"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1   # weights/datasets pre-fetched on login node
echo "[ft02-headroom] job ${SLURM_JOB_ID:-?} on $(hostname)"

# Default backbone set spans both modalities + all three text tasks + the three
# fine-grained vision tasks. Override with FT02_BACKBONES to run a subset.
BACKBONES_LIST="${FT02_BACKBONES:-vit_b32_cub200,vit_b32_stanford_cars,vit_b32_fgvc_aircraft,roberta_base_banking77,mpnet_st_banking77,roberta_base_20news,mpnet_st_20news,roberta_base_trec,mpnet_st_trec}"

exec srun python -u -m src.headroom \
    --backbones "${BACKBONES_LIST}" \
    --case "${CASE}" \
    --results-root "${REPO}/results" \
    --data-root "${REPO}/data" \
    --cache-root "${REPO}/cache" \
    --probe-epochs 50 \
    --ceiling 0.90
