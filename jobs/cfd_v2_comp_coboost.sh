#!/bin/bash
# Co-Boosting (Dai et al., ICLR 2024) comparator wrapper for HE-IFD smoke cell.
#
# Usage:  sbatch jobs/cfd_v2_comp_coboost.sh <dataset> <alpha> <seed>
# Example: sbatch jobs/cfd_v2_comp_coboost.sh MNIST 0.3 42
#
# The upstream code at /scratch/hkanpak21/HE_IFD/comparators/coboosting/ is
# left UNMODIFIED (vendor-as-is policy from issues/06). Upstream hard-codes
# every IO path under /gdata/dairong/... so we transparently redirect that
# tree to a per-job scratch dir via a symlink hack before invocation.
#
# Co-Boosting is a two-stage pipeline:
#   1. fl_pretrain.py  — train N=10 client teachers on Dirichlet(beta=alpha)
#                        partition; saves <identity>.pkl checkpoint.
#   2. datafree_kd.py  — generator + KD distillation from the ensembled
#                        teachers into a single student.
# Both stages must run in the same SLURM job (the second reads the first's
# checkpoint). Smoke target: MNIST, alpha=0.3, seed=42, N=10, cnn backbone.
#
# Output: results/coboost_smoke_${SLURM_JOB_ID}.json with the final student
# accuracy (extracted from upstream's "Best: %.4f" log line). DP accountant:
# none — Co-Boosting is plaintext (the PRD §3.4 privacy-unaware ceiling).
#
#SBATCH --partition=t4_ai
#SBATCH --qos=comx29
#SBATCH --account=comx29
#SBATCH --gres=gpu:1
#SBATCH --time=00:30:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --output=results/coboost_smoke_%j.out
#SBATCH --error=results/coboost_smoke_%j.err

set -euo pipefail

# ---- arg parsing ----------------------------------------------------------
DATASET_RAW="${1:-MNIST}"
ALPHA="${2:-0.3}"
SEED="${3:-42}"

# Upstream uses lower-case dataset keys; normalise.
DATASET="$(printf '%s' "$DATASET_RAW" | tr '[:upper:]' '[:lower:]')"
case "$DATASET" in
  mnist|fmnist|cifar10|cifar100) ;;
  *) echo "[coboost] ERROR: unsupported dataset '$DATASET_RAW' (expect MNIST/FMNIST/CIFAR10/CIFAR100)" >&2; exit 2 ;;
esac

# ---- env setup ------------------------------------------------------------
# NOTE: conda env `he_ifd_comparators` is expected to be pre-created with
# torch>=2.0, torchvision, numpy, scipy. If absent on first submission, the
# user (or a one-off setup job) should run e.g.:
#     conda create -n he_ifd_comparators --clone he_ofl && \
#       conda activate he_ifd_comparators && \
#       pip install --no-deps tqdm
# (the upstream needs nothing beyond stock pytorch + tqdm).
# shellcheck source=/dev/null
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ifd_comparators

# ---- path plumbing --------------------------------------------------------
REPO_ROOT="/scratch/hkanpak21/HE_IFD"
UPSTREAM_DIR="${REPO_ROOT}/comparators/coboosting"
RESULTS_DIR="${REPO_ROOT}/results"
mkdir -p "$RESULTS_DIR"

# Per-job scratch where the upstream's /gdata/dairong/... tree is rehomed.
JOB_SCRATCH="/scratch/hkanpak21/HE_IFD/results/coboost_scratch_${SLURM_JOB_ID:-local}"
mkdir -p "$JOB_SCRATCH"

# Surrogate the upstream's hard-coded prefix. The upstream writes to
# /gdata/dairong/{Co_boosting,Co_Boosting,fedsam}; we can't symlink /gdata
# (no root), so instead we copy the upstream tree into JOB_SCRATCH and run
# from there with a sed-patch trick. Simpler approach: build a private
# overlay via fakeroot-style symlink under $HOME and pre-substitute. Since
# we can't truly redirect absolute paths without modifying the upstream,
# fall back to creating /gdata/dairong/... only if /gdata is writable.
if [ -d /gdata ] && [ -w /gdata ]; then
  REAL_PREFIX="/gdata/dairong"
  mkdir -p "${REAL_PREFIX}/Co_boosting/checkpoints/FL_pretrain"
  mkdir -p "${REAL_PREFIX}/Co_boosting/LOG/FL_pretrain"
  mkdir -p "${REAL_PREFIX}/Co_Boosting/LOG"
  mkdir -p "${REAL_PREFIX}/Co_Boosting/checkpoints"
  mkdir -p "${REAL_PREFIX}/fedsam/Data/Raw"
  DATA_ROOT="${REAL_PREFIX}/fedsam/Data/Raw"
else
  # /gdata is read-only on Valar t4_ai. Patch the upstream in-place inside a
  # WORK_COPY (the vendored tree at $UPSTREAM_DIR stays pristine).
  WORK_COPY="${JOB_SCRATCH}/work"
  mkdir -p "$WORK_COPY"
  cp -a "${UPSTREAM_DIR}/." "${WORK_COPY}/"
  # Substitute the hard-coded prefix to JOB_SCRATCH/gdata.
  PRIV_PREFIX="${JOB_SCRATCH}/gdata/dairong"
  mkdir -p "${PRIV_PREFIX}/Co_boosting/checkpoints/FL_pretrain"
  mkdir -p "${PRIV_PREFIX}/Co_boosting/LOG/FL_pretrain"
  mkdir -p "${PRIV_PREFIX}/Co_Boosting/LOG"
  mkdir -p "${PRIV_PREFIX}/Co_Boosting/checkpoints"
  mkdir -p "${PRIV_PREFIX}/fedsam/Data/Raw"
  find "${WORK_COPY}" -maxdepth 2 -name "*.py" -exec \
    sed -i "s|/gdata/dairong|${PRIV_PREFIX}|g" {} +
  UPSTREAM_DIR="${WORK_COPY}"
  DATA_ROOT="${PRIV_PREFIX}/fedsam/Data/Raw"
fi

# CIFAR-10 data is already on disk per memory `valar.md`. If smoke uses
# CIFAR-10 we'd prefer to reuse it; for MNIST the upstream auto-downloads.
if [ "$DATASET" = "cifar10" ] && [ -d /scratch/hkanpak21/HE_Distillation/data/cifar-10-batches-py ]; then
  ln -sfn /scratch/hkanpak21/HE_Distillation/data/cifar-10-batches-py "${DATA_ROOT}/cifar-10-batches-py"
fi

cd "$UPSTREAM_DIR"

# ---- canonical identity string (mirrors upstream convention) --------------
# The upstream constructs args.identity = "<dataset>_clients<N>_<partition><beta>_sig<sigma>_<model>_Llr<lr>_Le<epochs>_seed<seed>"
# For smoke: N=10, partition=dir, sigma=0.0, cnn, Llr=0.01, Le=100.
NUM_USERS=10
MODEL="cnn"
LOCAL_LR=0.01
LOCAL_EP=100
SIGMA=0.0
PARTITION="dir"
FL_IDENT="${DATASET}_clients${NUM_USERS}_${PARTITION}${ALPHA}_sig${SIGMA}_${MODEL}_Llr${LOCAL_LR}_Le${LOCAL_EP}_seed${SEED}"
echo "[coboost] fl identity = ${FL_IDENT}"

# ---- stage 1: FL pretrain (teachers) --------------------------------------
echo "[coboost] === stage 1: fl_pretrain ($(date -Is)) ==="
python fl_pretrain.py \
  --dataset "${DATASET}" \
  --partition "dirichlet" \
  --beta "${ALPHA}" \
  --seed "${SEED}" \
  --num_users "${NUM_USERS}" \
  --model "${MODEL}" \
  --local_lr "${LOCAL_LR}" \
  --local_ep "${LOCAL_EP}" \
  --sigma "${SIGMA}" \
  --batch_size 128

# ---- stage 2: data-free KD distillation -----------------------------------
echo "[coboost] === stage 2: datafree_kd co_boosting ($(date -Is)) ==="
KD_LOG="${JOB_SCRATCH}/datafree_kd.stdout"
python datafree_kd.py \
  --method co_boosting \
  --dataset "${DATASET}" \
  --data_root "${DATA_ROOT}" \
  --fl_model "${FL_IDENT}" \
  --batch_size 128 \
  --teacher "${MODEL}" \
  --student "${MODEL}" \
  --kd_lr 0.01 \
  --epochs 200 \
  --g_steps 30 \
  --lr_g 1e-3 \
  --seed "${SEED}" \
  --print_freq 1 2>&1 | tee "${KD_LOG}"

# ---- extract final accuracy + write results JSON --------------------------
FINAL_ACC="$(grep -oE 'Best: [0-9]+\.[0-9]+' "${KD_LOG}" | tail -1 | awk '{print $2}')"
if [ -z "${FINAL_ACC:-}" ]; then FINAL_ACC="null"; fi

OUT_JSON="${RESULTS_DIR}/coboost_smoke_${SLURM_JOB_ID:-local}.json"
cat > "${OUT_JSON}" <<EOF
{
  "comparator": "coboost",
  "upstream_commit": "$(cat "${REPO_ROOT}/comparators/coboosting/COMMIT.txt" | head -1)",
  "dataset": "${DATASET_RAW}",
  "alpha": ${ALPHA},
  "seed": ${SEED},
  "num_users": ${NUM_USERS},
  "model": "${MODEL}",
  "fl_identity": "${FL_IDENT}",
  "final_student_acc": ${FINAL_ACC},
  "dp_accountant": null,
  "dp_note": "Co-Boosting is plaintext (no DP); PRD §3.4 privacy-unaware ceiling",
  "slurm_job_id": "${SLURM_JOB_ID:-local}",
  "completed_at": "$(date -Is)"
}
EOF
echo "[coboost] wrote ${OUT_JSON}"
echo "[coboost] final_student_acc=${FINAL_ACC}"
