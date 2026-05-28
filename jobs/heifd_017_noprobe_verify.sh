#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --job-name=heifd_017_verify
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_017_noprobe_verify/runs/verify_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_017_noprobe_verify/runs/verify_%j.err
#
# Issue 017 — no-probe DP-common-basin VERIFY run. Confirms the no-probe path
# (no labelled public probe; the (raw-union or DP-noisy) per-(client, class)
# prototypes themselves warm θ₀) runs end-to-end on MNIST/MLP BEFORE the full
# grid is launched. A local-only ast.parse cannot catch the runtime
# flatten/reshape bridge or the prototype-set warmup; this small grid does.
#
# Grid: mlp_mnist × N{10} × α{0.05, 1.0}
#       × methods{noprobe_dp_avg_eps2_K20, noprobe_dp_avg_eps8_K20,
#                 noprobe_raw_union_K20,                       (the 3 no-probe)
#                 dp_avg_eps2_K20, raw_union_K20}             (the 2 with-probe)
#       × seeds{42}  = 1 × 2 × 5 × 1 = 10 cells.
#
# Pass condition: all 10 cells status=success; the no-probe θ₀ is weak (low
# theta0_acc) yet acc (post-distillation) lifts above it — confirming the
# distillation carries the learning in the low-leak regime. The orchestrator
# runs THIS first, then submits heifd_017_noprobe_mlp.sh on success.
#
# MNIST is pre-cached under data/MNIST/ (download=False); no prefetch needed.

set -euo pipefail
REPO=/scratch/hkanpak21/HE_IFD
CASE=heifd_017_noprobe_verify
mkdir -p "${REPO}/results/${CASE}/runs"
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
cd "${REPO}"
echo "[017 verify] job ${SLURM_JOB_ID:-?} on $(hostname)"

exec srun python -u -m src.sweep \
    --backbones mlp_mnist \
    --Ns 10 \
    --alphas 0.05,1.0 \
    --methods noprobe_dp_avg_eps2_K20,noprobe_dp_avg_eps8_K20,noprobe_raw_union_K20,dp_avg_eps2_K20,raw_union_K20 \
    --seeds 42 \
    --K "${HEIFD_K:-300}" \
    --case "${CASE}" \
    --results-root "${REPO}/results" \
    --data-root "${REPO}/data" \
    --cache-root "${REPO}/cache"
