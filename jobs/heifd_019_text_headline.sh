#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --job-name=heifd_019h
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_019_text_headline/runs/headline_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_019_text_headline/runs/headline_%j.err
#
# Issue 019 — Stronger frozen TEXT backbones FULL headline grid. Mirrors the
# pretrained headline wrapper (jobs/heifd_headline_pretrained.sh): ONE backbone
# per job (set via HEIFD_BACKBONE) so its 768-d features extract+cache exactly
# once at the first cell — no cross-chunk extraction race. The full grid per
# backbone is N{5,10,20,50} × α{0.01,0.05,0.1,0.3,1.0} × 6 methods × 3 seeds.
#
# NOT auto-submitted by the implementing agent — the orchestrator submits this
# only AFTER jobs/heifd_019_text_verify.sh confirms the new backbones beat
# DistilBERT at α=0.05 (acc ≥ 0.6, m4 ≥ 0.5, oracle ≥ 0.93).
#
#   sbatch --export=ALL,HEIFD_BACKBONE=roberta_base_agnews   jobs/heifd_019_text_headline.sh
#   sbatch --export=ALL,HEIFD_BACKBONE=mpnet_st_agnews       jobs/heifd_019_text_headline.sh
#   # Part-2 DBpedia-14 (richer OOD/m4 story; needs --include-text019 prefetch):
#   sbatch --export=ALL,HEIFD_BACKBONE=roberta_base_dbpedia  jobs/heifd_019_text_headline.sh
#   sbatch --export=ALL,HEIFD_BACKBONE=mpnet_st_dbpedia      jobs/heifd_019_text_headline.sh
#
# Head cells are cheap (linear head on cached features), so a 360-cell grid
# fits the 3h cap once features are cached; if a single backbone's grid would
# exceed 3h (DBpedia-14's 560k-sample feature extraction is the long pole on
# the FIRST cell only — it caches thereafter), resubmit to resume (sweep.py
# skips already-completed cells), or split via SLURM array using the chunk
# flags below (HEIFD_NUM_CHUNKS / SLURM_ARRAY_TASK_ID).
#
# Requires login-node prefetch first:
#   python jobs/prefetch_login.py --include-text019
# Compute nodes load offline.

set -euo pipefail
REPO=/scratch/hkanpak21/HE_IFD
BB="${HEIFD_BACKBONE:?set HEIFD_BACKBONE=<roberta_base_agnews|mpnet_st_agnews|roberta_base_dbpedia|mpnet_st_dbpedia>}"
CASE=heifd_019_text_headline
mkdir -p "${REPO}/results/${CASE}/runs"
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
cd "${REPO}"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1
echo "[019-headline] job ${SLURM_JOB_ID:-?} backbone=${BB} on $(hostname)"

# Optional SLURM-array chunking (only used if launched with --array). When not
# an array job these resolve to the single-chunk (whole grid) path.
CHUNK_ARGS=()
if [[ -n "${HEIFD_NUM_CHUNKS:-}" && -n "${SLURM_ARRAY_TASK_ID:-}" ]]; then
    CHUNK_ARGS=(--num-chunks "${HEIFD_NUM_CHUNKS}" --chunk-index "${SLURM_ARRAY_TASK_ID}")
    echo "[019-headline] chunk ${SLURM_ARRAY_TASK_ID}/${HEIFD_NUM_CHUNKS}"
fi

exec srun python -u -m src.sweep \
    --backbones "${BB}" \
    --Ns 5,10,20,50 \
    --alphas 0.01,0.05,0.1,0.3,1.0 \
    --methods no_phase0,warmup_only_labelled,labelled_probe_warmup,raw_union_K20,dp_avg_eps2_K20,dp_avg_eps8_K20 \
    --seeds 42,43,44 \
    --K "${HEIFD_K:-100}" \
    --tau "${HEIFD_TAU:-1}" \
    --student-lr "${HEIFD_LR:-0.001}" \
    --case "${CASE}" \
    --results-root "${REPO}/results" \
    --data-root "${REPO}/data" \
    --cache-root "${REPO}/cache" \
    "${CHUNK_ARGS[@]}"
