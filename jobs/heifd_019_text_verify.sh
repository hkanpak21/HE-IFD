#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --job-name=heifd_019v
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_019_text_verify/runs/verify_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_019_text_verify/runs/verify_%j.err
#
# Issue 019 — Stronger frozen TEXT backbones verify run. The text deployment
# story is the weak link (DistilBERT collapses at α=0.05: acc 0.437, m4 0.363,
# oracle 0.904; GPT-2 is a poor frozen extractor). This verify exercises the new
# strong frozen text backbones on the minimal grid that establishes whether they
# substantially beat DistilBERT at α=0.05:
#
#   backbones: roberta_base_agnews + mpnet_st_agnews
#              (both bidirectional → masked mean-pool, frozen; only the linear
#               head displacement enters the aggregate)
#              (+ optional roberta_base_dbpedia + mpnet_st_dbpedia if Part-2
#               DBpedia-14 was prefetched and HEIFD_019_INCLUDE_DBPEDIA=1 set)
#   methods:   no_phase0, raw_union_K20
#   N=10, α∈{0.05, 1.0}, seed=42
#   KD hparams: K=100, τ=1, lr=0.001  (issue 010 best pretrained-head defaults;
#               head_only scope per issue 011)
#
# The bar to beat (current DistilBERT, AG-News, α=0.05):
#   acc 0.437 | θ₀ 0.410 | mean_teacher 0.293 | oracle 0.904 | m4_ood 0.363
# Acceptance target (issue 019): α=0.05 raw_union acc ≥ 0.6, m4 ≥ 0.5,
#   oracle ≥ 0.93 — toward the ViT/CIFAR-100 level.
#
# Resumable / chunkable via sweep.py's per-cell JSON skip-on-success. Memory
# 32G (RoBERTa/MPNet 768-d feature caches on AG-News are modest; DBpedia-14 at
# 560k train is the larger footprint, extracted 32 texts at a time on GPU).
#
# Weights/datasets MUST be pre-fetched on the VALAR login node first:
#   python jobs/prefetch_login.py --include-text019
# (pulls roberta-base + all-mpnet-base-v2 via plain HF AutoModel — NO
#  sentence-transformers package needed — plus the DBpedia-14 HF dataset).
# Compute nodes then load offline (HF_HUB_OFFLINE=1 / TRANSFORMERS_OFFLINE=1).
#
# Submit:
#   sbatch jobs/heifd_019_text_verify.sh                                   # AG-News only
#   sbatch --export=ALL,HEIFD_019_INCLUDE_DBPEDIA=1 jobs/heifd_019_text_verify.sh

set -euo pipefail
REPO=/scratch/hkanpak21/HE_IFD
CASE=heifd_019_text_verify
mkdir -p "${REPO}/results/${CASE}/runs"
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
cd "${REPO}"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1   # weights pre-fetched on login node
export HF_DATASETS_OFFLINE=1                      # dataset pre-fetched on login node
echo "[019-verify] job ${SLURM_JOB_ID:-?} on $(hostname)"

# AG-News strong backbones always included; DBpedia-14 opt-in (Part 2) so the
# default verify lands on the headline AG-News comparison-to-DistilBERT first.
BACKBONES_LIST="roberta_base_agnews,mpnet_st_agnews"
if [[ "${HEIFD_019_INCLUDE_DBPEDIA:-0}" == "1" ]]; then
    BACKBONES_LIST="${BACKBONES_LIST},roberta_base_dbpedia,mpnet_st_dbpedia"
    echo "[019-verify] DBpedia-14 included (HEIFD_019_INCLUDE_DBPEDIA=1)"
fi

exec srun python -u -m src.sweep \
    --backbones "${BACKBONES_LIST}" \
    --Ns 10 \
    --alphas 0.05,1.0 \
    --methods no_phase0,raw_union_K20 \
    --seeds 42 \
    --K 100 \
    --tau 1 \
    --student-lr 0.001 \
    --case "${CASE}" \
    --results-root "${REPO}/results" \
    --data-root "${REPO}/data" \
    --cache-root "${REPO}/cache"
