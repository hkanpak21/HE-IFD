#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --job-name=heifd_022_synth_basin
#SBATCH --array=0-7
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_022_synth_basin/runs/synth_basin_%A_%a.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_022_synth_basin/runs/synth_basin_%A_%a.err
#
# Issue 022 — DP-MERF synthetic-basin study (Harder et al. 2021, harder2021dpmerf).
#
# THE CONTRAST (the paper's value proposition, made concrete). A DP synthetic-data
# generator can be used two ways; this grid measures the gap between them on the
# SAME backbones / partitions / seeds:
#
#   * Mode A — DP-synthesize EVERYTHING (the naive DP-one-shot baseline, cf.
#     FedDiff): dp_synth_all_eps{2,8}. DP-MERF is fit to ALL of a client's data;
#     the synthetic set carries the whole contribution and the student is trained
#     one-shot directly on it — NO basin, NO bounded distillation, NO HE benefit.
#     Covering every sample at meaningful ε forces large DP noise ⇒ accuracy is
#     expected to DROP, and the released model stays MIA-vulnerable.
#
#   * Mode B — DP a FEW samples for the basin, HE for the rest (OURS):
#     merf_basin_eps{2,8}_K20. DP-MERF is applied to only K_per_class=20 samples
#     per class, even at tight ε, SOLELY to build the shared basin θ₀ (which need
#     only align, not classify). The bulk of the contribution flows through the
#     bounded distillation, protected LOSSLESSLY by HE ⇒ good accuracy
#     (≈ raw_union / DP-prototype basins) + cryptographic privacy on the real
#     contribution.
#
# Reference rows in the SAME grid pin Mode B against the existing basin sources:
#   raw_union_K20            — no-DP alignment ceiling for the basin.
#   dp_avg_eps2_K20          — DP per-class mean prototype (with labelled probe).
#   noprobe_dp_avg_eps2_K20  — DP prototype, NO labelled public probe (weakest leak).
# So merf_basin_eps2_K20 ≈ {raw_union_K20, dp_avg_eps2_K20} >> dp_synth_all_eps2
# is the result the study demonstrates, and feeds the alignment-source comparison
# table + the synthetic-basin paragraph.
#
# (Hook for issue 021) Both modes produce a released student via run_cell that the
# MIA suite reconstructs and attacks: Mode A's θ⋆ is trained directly on the
# synthetic data (MIA-vulnerable); Mode B's θ⋆ is the HE aggregate whose bulk is
# HE-protected, so only the decrypted θ⋆ is attackable.
#
# Grid: backbones{mlp_mnist, vit_b32_cifar100}                                    (2)
#       × methods{dp_synth_all_eps2, dp_synth_all_eps8,                           (Mode A)
#                 merf_basin_eps2_K20, merf_basin_eps8_K20,                       (Mode B)
#                 raw_union_K20, dp_avg_eps2_K20, noprobe_dp_avg_eps2_K20}        (refs)  (7)
#       × α{0.05, 0.3, 1.0}                                                       (3)
#       × N{10}                                                                   (1)
#       × seeds{42,43,44}                                                         (3)
#       = 2 × 7 × 3 × 1 × 3 = 126 cells.
#
# NOTE backbone key: the issue prose says "mnist_mlp"; the registered BackboneSpec
# key is "mlp_mnist" (see src/protocol.py BACKBONES). We use the registry key.
#
# Chunking: SLURM job array (--array=0-7 → 8 chunks) with round-robin striping via
# sweep.py --num-chunks / --chunk-index (~16 cells/chunk). The vit_b32_cifar100
# Mode-A cells (DP-MERF over ALL local data, 100 classes) are the heaviest; round-
# robin spreads them across all 8 chunks so no chunk approaches the 3h VALAR cap.
# Resumable: re-submitting skips any cell whose JSON already records
# status=success (src/sweep.py).
#
# PREFETCH (login node, internet): ViT-B/32 weights + CIFAR-100 must be in the
# HF/torch cache before this runs (compute nodes are offline). MNIST is pre-cached
# under data/ (download=False). The ViT feature cache is built on first use; do a
# one-cell login-node-cached run or rely on the existing vit_b32_cifar100 caches
# from issue 012 if already populated.
#
# Run a small smoke first (e.g. one chunk, seeds 42 only) and confirm
# status=success before launching the full array.

set -euo pipefail
REPO=/scratch/hkanpak21/HE_IFD
CASE=heifd_022_synth_basin
mkdir -p "${REPO}/results/${CASE}/runs"
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
export HF_HUB_OFFLINE=1           # ViT-B/32 weights + CIFAR-100 are pre-fetched on the login node
cd "${REPO}"
echo "[022 synth_basin] job ${SLURM_ARRAY_JOB_ID:-?} task ${SLURM_ARRAY_TASK_ID:-0}/${SLURM_ARRAY_TASK_COUNT:-1} on $(hostname)"

exec srun python -u -m src.sweep \
    --backbones mlp_mnist,vit_b32_cifar100 \
    --Ns 10 \
    --alphas 0.05,0.3,1.0 \
    --methods dp_synth_all_eps2,dp_synth_all_eps8,merf_basin_eps2_K20,merf_basin_eps8_K20,raw_union_K20,dp_avg_eps2_K20,noprobe_dp_avg_eps2_K20 \
    --seeds 42,43,44 \
    --K "${HEIFD_K:-300}" \
    --case "${CASE}" \
    --results-root "${REPO}/results" \
    --data-root "${REPO}/data" \
    --cache-root "${REPO}/cache" \
    --num-chunks "${SLURM_ARRAY_TASK_COUNT:-8}" \
    --chunk-index "${SLURM_ARRAY_TASK_ID:-0}"
