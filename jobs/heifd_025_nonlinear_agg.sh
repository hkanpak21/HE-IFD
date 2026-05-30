#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --job-name=heifd_025_nonlinear_agg
#SBATCH --array=0-15
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_025_nonlinear_agg/runs/nonlinear_agg_%A_%a.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_025_nonlinear_agg/runs/nonlinear_agg_%A_%a.err
#
# Issue 025 — non-linear ONE-SHOT server-combine investigation, in the real src/
# pipeline (the issue-024 local MNIST-MLP probe, now on the headline backbones).
#
# THE QUESTION. The HE-IFD server aggregate is the linear, sample-weighted
# θ⋆ = θ₀ + Σᵢ wᵢ·Δᵢ (multiplicative depth ≈ 1, the paper's whole selling point).
# It telescopes to a weighted average of the clients' FINAL models and leaves a
# heterogeneity gap to centralized at small α (issue 023/024). Issue 025 stays
# STRICTLY ONE-SHOT — the SAME one-shot uploads {Δᵢ} from the bounded K-step
# trajectory, no extra client↔server rounds — and asks: does ANY non-linear
# server function of {Δᵢ} beat the flat weighted average under heterogeneity, and
# is any winner CKKS-cheap (depth-1 / division-free depth-2)? The 024 probe said
# NO on MNIST-MLP; this sweep tests the same combines on the headline backbones.
#
# WHAT VARIES. The server combine (--agg-methods) is the headline axis. Every
# combine is applied to the SAME {Δᵢ}; distillation is identical across them, so
# each (backbone, α, method, seed) protocol cell is run once per combine over its
# shared uploads. weight_avg is the linear baseline (byte-identical to the
# production aggregate, depth-1) every other combine is measured against:
#
#   depth-1 [CKKS-cheap]:  weight_avg (baseline), mag_weighted
#   depth-2 [CKKS-cheap]:  poly_gate_d2_a, poly_gate_d2_b   (division-free, BOUNDED
#                          [0,1] gate — the issue-025 safe fix for the 024 detonation)
#   deep    [not low-depth CKKS, plaintext study of the idea]:
#                          sign_majority, agreement_gated, norm_normalized,
#                          second_moment, coord_median, consensus_proj
#
# WHAT THE TWO PROTOCOL METHODS PROBE.
#   raw_union_K20  — clients distil from a SHARED aligned θ₀ (basin coherence ON);
#                    the regime where the flat average already works well.
#   no_phase0      — NO basin: each client distils from a fresh random θ₀, so the
#                    {Δᵢ} are maximally incoherent — the hardest case for ANY fixed
#                    one-shot combine, and where a non-linear combine has the most
#                    theoretical room to help (the 024 probe found it still doesn't).
#
# Grid: backbones{mlp_mnist, lenet_fmnist, vit_b32_cifar100, roberta_base_agnews} (4)
#       × α{0.05, 0.1, 0.3, 1.0}                                                  (4)
#       × methods{raw_union_K20, no_phase0}                                       (2)
#       × --agg-methods{weight_avg, mag_weighted, sign_majority, agreement_gated,
#                       norm_normalized, second_moment, coord_median,
#                       consensus_proj, poly_gate_d2_a, poly_gate_d2_b}          (10)
#       × N{10}                                                                   (1)
#       × seeds{42,43,44}                                                         (3)
#       = 4 × 4 × 2 × 10 × 1 × 3 = 960 cells.
#
# K=20 (the basin-coherence K from the 024/023 probes — short bounded trajectory)
# is fixed via HEIFD_K; the distillation is light, so the per-cell cost is
# dominated by the (cached) teachers/oracle, NOT the combine. The 10 combines on
# one protocol cell share its uploads, so they are cheap relative to the run.
#
# Chunking: SLURM job array (--array=0-15 → 16 chunks) with round-robin striping
# via sweep.py --num-chunks / --chunk-index (~60 cells/chunk). The
# vit_b32_cifar100 cells (100 classes) are the heaviest; round-robin spreads them
# across all 16 chunks so no chunk approaches the 3h VALAR cap. Resumable:
# re-submitting skips any cell whose JSON already records status=success
# (src/sweep.py). weight_avg cells reuse the legacy filename/hash (cell_descriptor
# omits the default agg_method), so they coincide with — and resume from — any
# already-computed raw_union_K20 / no_phase0 weight_avg cell.
#
# PREFETCH (login node, internet — compute nodes are offline):
#   * ViT-B/32 weights + CIFAR-100 in the HF/torch cache (vit_b32_cifar100; reuse
#     the issue-012 caches if already populated).
#   * RoBERTa-base weights + AG-News in the HF cache (roberta_base_agnews; reuse
#     the issue-019 caches). roberta_base_agnews z-scores its features at load.
#   * MNIST / FashionMNIST are pre-cached under data/ (download=False).
# Run a small smoke first (e.g. one chunk, seeds 42 only) and confirm
# status=success before launching the full array.

set -euo pipefail
REPO=/scratch/hkanpak21/HE_IFD
CASE=heifd_025_nonlinear_agg
mkdir -p "${REPO}/results/${CASE}/runs"
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
export HF_HUB_OFFLINE=1           # ViT-B/32 + RoBERTa weights + CIFAR-100/AG-News pre-fetched on the login node
cd "${REPO}"
echo "[025 nonlinear_agg] job ${SLURM_ARRAY_JOB_ID:-?} task ${SLURM_ARRAY_TASK_ID:-0}/${SLURM_ARRAY_TASK_COUNT:-1} on $(hostname)"

exec srun python -u -m src.sweep \
    --backbones mlp_mnist,lenet_fmnist,vit_b32_cifar100,roberta_base_agnews \
    --Ns 10 \
    --alphas 0.05,0.1,0.3,1.0 \
    --methods raw_union_K20,no_phase0 \
    --agg-methods weight_avg,mag_weighted,sign_majority,agreement_gated,norm_normalized,second_moment,coord_median,consensus_proj,poly_gate_d2_a,poly_gate_d2_b \
    --seeds 42,43,44 \
    --K "${HEIFD_K:-20}" \
    --case "${CASE}" \
    --results-root "${REPO}/results" \
    --data-root "${REPO}/data" \
    --cache-root "${REPO}/cache" \
    --num-chunks "${SLURM_ARRAY_TASK_COUNT:-16}" \
    --chunk-index "${SLURM_ARRAY_TASK_ID:-0}"
