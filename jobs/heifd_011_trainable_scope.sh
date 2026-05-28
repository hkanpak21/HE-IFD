#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --job-name=heifd_011
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_011_scope_resnet18/runs/scope_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_011_scope_resnet18/runs/scope_%j.err
#
# Issue 011 — Trainable-layer-scope focused comparison on the regime
# issues 008/010/013 jointly localised:
#   resnet18 / CIFAR-10 / α=0.05 / N=10 / raw_union_K20 + no_phase0.
# Issue 010 already lifted the broken (K=300, τ=4, lr=0.01) default to
# (K=100, τ=1, lr=0.001) → mean acc 0.7617 (partial: closes the 26pp gap,
# leaves ~2pp residual vs θ₀≈0.74). Issue 011 tests whether adding
# trainable capacity beyond the linear head closes that residual.
#
# Grid (2 methods × 3 seeds × 3 scopes = 18 cells):
#   backbone resnet18_cifar10 · N=10 · α=0.05
#   methods  no_phase0 + raw_union_K20  (the two methods 010 used)
#   scopes   head_only      (sanity reference; should reproduce 010's 0.7617)
#            lora_8         (rank-8 LoRA adapter on the head; +4176 params)
#            last_block     (MLP head: in_dim->128->10; +66.5k params, ~14× head_only)
#   K=100, τ=1, lr=0.001    — the issue-010 Round-1 best defaults
#                             (isolates scope/capacity from KD hparams; if we
#                              kept the old K=300/τ=4/lr=0.01 default the
#                              head_only baseline would reproduce the broken
#                              0.48 and the scope comparison would be meaningless)
#   seeds {42, 43, 44}
#
# Sweep CLI: scope flows through --scopes (added with issue 011). Cell
# descriptors include trainable_scope only when non-default, so lora_8 /
# last_block cells get distinct, self-describing filenames while any
# pre-issue-011 head_only cell (none in this case dir yet) would keep its
# legacy hash. See src/sweep.py::cell_descriptor for the backwards-compat rule.
#
# Wall-clock estimate: issue 010's K=100/τ=1/lr=0.001 cell ran ~20-30s. With
# 18 cells and a single task, the job is ~6-10 min — comfortably inside the
# 3h VALAR hard cap. (If lora_8 / last_block prove slower, the existing
# --num-chunks / --chunk-index plumbing can split via SLURM job-array; the
# 18-cell grid does not need it.)
#
# Memory bump: 24G -> 32G. last_block adds ~66k params per state_dict, and
# distill.py's return_steps path can spike if any future diagnostic cell
# lands here — 32G gives headroom without competing with the t4_ai pool.
#
# Dataset (CIFAR-10) is pre-cached under data/; resnet18 pretrained weights
# are pre-fetched on the login node (HF_HUB_OFFLINE=1 / TRANSFORMERS_OFFLINE=1
# in the env block). No login-node prefetch needed beyond what issue 008
# already populated (resnet18 feature cache from heifd_pretrained_headline).
#
# Acceptance gate (orchestrator will append to results/<case>/README.md
# post-run): the headline is mean_acc per scope across 3 seeds, compared to
# the issue-010 Round-1 head_only baseline 0.7617 and the warmed θ₀≈0.74.
# Methodology-impact framing decision routes to the user per issue 011's
# HITL touchpoint.

set -euo pipefail
REPO=/scratch/hkanpak21/HE_IFD
CASE=heifd_011_scope_resnet18
mkdir -p "${REPO}/results/${CASE}/runs"
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
cd "${REPO}"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
echo "[011] job ${SLURM_JOB_ID:-?} on $(hostname)"

exec srun python -u -m src.sweep \
    --backbones resnet18_cifar10 \
    --Ns 10 \
    --alphas 0.05 \
    --methods no_phase0,raw_union_K20 \
    --seeds 42,43,44 \
    --K 100 \
    --tau 1 \
    --student-lr 0.001 \
    --scopes head_only,lora_8,last_block \
    --case "${CASE}" \
    --results-root "${REPO}/results" \
    --data-root "${REPO}/data" \
    --cache-root "${REPO}/cache"
