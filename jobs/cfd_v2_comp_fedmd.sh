#!/usr/bin/env bash
#SBATCH --job-name=fedmd_smoke
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --time=00:30:00
#SBATCH --gres=gpu:1
#SBATCH --mem=16G
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/fedmd_smoke_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/fedmd_smoke_%j.err
#
# HE-IFD comparator wrapper: FedMD (Li & Wang 2019, li2019fedmd).
# Usage: sbatch jobs/cfd_v2_comp_fedmd.sh <DATASET> <ALPHA> <SEED>
# Example: sbatch jobs/cfd_v2_comp_fedmd.sh MNIST 0.3 42
#
# Notes (issue 07 vendor decisions, 2026-05-17):
#   * Upstream pins N_parties=10 and N_alignment=5000 already (conf/*.json),
#     so no probe-size or party-count adapter shim is required.
#   * Upstream partition is BALANCED (N_samples_per_class), NOT Dirichlet(alpha).
#     ALPHA is currently logged + exported as FEDMD_ALPHA only; a proper Dirichlet
#     adapter in data_utils.generate_bal_private_data is a follow-up
#     (see issue 07 Comments). For the smoke, default upstream partition is used.
#   * SEED is exported as FEDMD_SEED but upstream does not surface a seed CLI;
#     deterministic reseeding likewise deferred.
#   * Conda env "he_ifd_comparators" assumed; create it if missing before running.
#
# Acceptance: final student accuracy >= 0.9 on MNIST per upstream paper
# (FedMD reports >0.99 on the FEMNIST-balanced configuration whose public probe
# is MNIST; this is the canonical "MNIST" smoke per the upstream README demo).

set -euo pipefail

DATASET="${1:-MNIST}"
ALPHA="${2:-0.3}"
SEED="${3:-42}"

export FEDMD_ALPHA="${ALPHA}"
export FEDMD_SEED="${SEED}"

REPO_ROOT="/scratch/hkanpak21/HE_IFD"
FEDMD_DIR="${REPO_ROOT}/comparators/fedmd"
RESULTS_DIR="${REPO_ROOT}/results"
mkdir -p "${RESULTS_DIR}"

# Map DATASET -> upstream entry point + conf.
case "${DATASET}" in
  MNIST|FEMNIST|EMNIST)
    ENTRY="FEMNIST_Balanced.py"
    CONF="conf/EMNIST_balance_conf.json"
    ;;
  CIFAR|CIFAR10|CIFAR100)
    ENTRY="CIFAR_Balanced.py"
    CONF="conf/CIFAR_balance_conf.json"
    ;;
  *)
    echo "[fedmd] Unsupported dataset: ${DATASET}" >&2
    exit 2
    ;;
esac

# Conda activation (env created later if missing; see header note).
CONDA_BASE="/opt/ohpc/pub/compiler/conda3/latest"
# shellcheck disable=SC1091
source "${CONDA_BASE}/etc/profile.d/conda.sh"
if conda env list | grep -qE "^he_ifd_comparators[[:space:]]"; then
    conda activate he_ifd_comparators
else
    echo "[fedmd] he_ifd_comparators not found, falling back to he_ofl"
    conda activate he_ofl
fi

OUT_JSON="${RESULTS_DIR}/fedmd_smoke_${SLURM_JOB_ID:-local}.json"

echo "[fedmd] dataset=${DATASET} alpha=${ALPHA} seed=${SEED} entry=${ENTRY} conf=${CONF}"
echo "[fedmd] writing summary to ${OUT_JSON}"

cd "${FEDMD_DIR}"

# Run upstream entry-point. Tee stdout so we can extract the final accuracy.
RUN_LOG="${RESULTS_DIR}/fedmd_smoke_${SLURM_JOB_ID:-local}.runlog"
python "${ENTRY}" -conf "${CONF}" 2>&1 | tee "${RUN_LOG}"

# Extract final student (collaboration) accuracy. FedMD prints per-round eval
# lines such as "model X: acc 0.99..." across N_rounds; grab the last
# accuracy-shaped float in the log as a best-effort summary.
STUDENT_ACC="$(grep -Eo 'acc[: ]+[0-9]*\.[0-9]+' "${RUN_LOG}" | tail -n1 | grep -Eo '[0-9]*\.[0-9]+' || echo 'null')"

python - "${OUT_JSON}" "${STUDENT_ACC}" "${DATASET}" "${ALPHA}" "${SEED}" <<'PY'
import json, sys
out, acc, ds, alpha, seed = sys.argv[1:6]
try:
    acc_val = float(acc)
except (TypeError, ValueError):
    acc_val = None
with open(out, "w") as f:
    json.dump({
        "comparator": "fedmd",
        "dataset": ds,
        "alpha": float(alpha),
        "seed": int(seed),
        "student_acc": acc_val,
    }, f, indent=2)
print(f"[fedmd] wrote {out}: student_acc={acc_val}")
PY
