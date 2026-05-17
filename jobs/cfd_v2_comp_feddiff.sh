#!/usr/bin/env bash
#SBATCH --job-name=feddiff_smoke
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --time=01:00:00
#SBATCH --gres=gpu:1
#SBATCH --mem=24G
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/feddiff_smoke_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/feddiff_smoke_%j.err
#
# HE-IFD comparator wrapper: FedDiff (Mendieta, Sun, Chen — WACV 2025,
#   "Navigating Heterogeneity and Privacy in One-Shot Federated Learning with
#   Diffusion Models" — bibkey feddiff2024).
#
# Usage: sbatch jobs/cfd_v2_comp_feddiff.sh <DATASET> <ALPHA> <SEED> <EPSILON>
# Example: sbatch jobs/cfd_v2_comp_feddiff.sh MNIST 0.3 42 10
#
# Role in HE-IFD:
#   Primary gamma-variant headline comparator. Same problem space as our HE-IFD
#   gamma cell (DP-protected synthetic-data distillation); differs only in
#   whether the distillation channel is plaintext (FedDiff) or CKKS-encrypted
#   (ours). The (FedDiff, HE-IFD-gamma) pair is the headline privacy-utility
#   trade-off row in the resubmission's A4.1 table.
#
# DP accounting:
#   Upstream FedDiff uses Opacus (per the WACV 2025 paper: "employs the Opacus
#   library in PyTorch to track privacy budgets ... Poisson batch sampling").
#   This wrapper propagates EPSILON via --epsilon. Until upstream code lands
#   and the exact argparse flag name is confirmed (could be --epsilon,
#   --target_epsilon, or --eps), the EPS_FLAG variable below is the single
#   source of truth — adjust if the upstream argparser uses a different name.
#
# Upstream-not-yet-published caveat (issue 08, 2026-05-17):
#   The mmendiet/FedDiff repo currently ships only LICENSE + README. This
#   wrapper assumes the eventual entry-point will be main.py (the conventional
#   choice for the author's prior FL code). On launch, the wrapper hard-fails
#   with a clear message if the entry-point is missing — preferable to a
#   silent no-op smoke. When upstream populates, update ENTRY + EPS_FLAG and
#   re-run.
#
# Conda env "he_ifd_comparators" assumed; create it if missing before running.
#
# Acceptance: final student accuracy within +/- 5pp of FedDiff's published
# MNIST result at the equivalent (alpha=0.3, eps=10) setting.

set -euo pipefail

DATASET="${1:-MNIST}"
ALPHA="${2:-0.3}"
SEED="${3:-42}"
EPSILON="${4:-10}"

# Sanity-check EPSILON is in the supported set {1, 10} (A4.1 DP-floor column).
case "${EPSILON}" in
  1|1.0|10|10.0) : ;;
  *)
    echo "[feddiff] WARNING: epsilon=${EPSILON} is outside the A4.1 DP-floor set {1, 10}." >&2
    ;;
esac

REPO_ROOT="/scratch/hkanpak21/HE_IFD"
FEDDIFF_DIR="${REPO_ROOT}/comparators/feddiff"
RESULTS_DIR="${REPO_ROOT}/results"
mkdir -p "${RESULTS_DIR}"

# Conventional upstream entry-point. Update when upstream publishes.
ENTRY="main.py"
ENTRY_PATH="${FEDDIFF_DIR}/${ENTRY}"

# Upstream argparse flag for the DP epsilon. Confirm against the upstream
# argparser once code lands (Opacus convention is usually `--epsilon` or
# `--target_epsilon`). All other privacy-related flags are passed through
# in EXTRA_ARGS below.
EPS_FLAG="--epsilon"
DELTA_FLAG="--delta"
DELTA_VAL="1e-5"

# Map our (DATASET, ALPHA, SEED) onto the upstream CLI surface.
# Names mirror the most common one-shot-FL conventions used in mmendiet's
# prior repos; reconcile against upstream argparser when populated.
DATASET_FLAG="--dataset"
ALPHA_FLAG="--alpha"        # Dirichlet alpha for client partition
SEED_FLAG="--seed"
N_PARTIES_FLAG="--n_parties"
N_PARTIES=10

# Conda activation.
CONDA_BASE="/opt/ohpc/pub/compiler/conda3/latest"
# shellcheck disable=SC1091
source "${CONDA_BASE}/etc/profile.d/conda.sh"
conda activate he_ifd_comparators

OUT_JSON="${RESULTS_DIR}/feddiff_smoke_${SLURM_JOB_ID:-local}.json"
RUN_LOG="${RESULTS_DIR}/feddiff_smoke_${SLURM_JOB_ID:-local}.runlog"

echo "[feddiff] dataset=${DATASET} alpha=${ALPHA} seed=${SEED} epsilon=${EPSILON}"
echo "[feddiff] entry=${ENTRY_PATH}"
echo "[feddiff] eps_flag=${EPS_FLAG} delta_flag=${DELTA_FLAG} delta_val=${DELTA_VAL}"
echo "[feddiff] writing summary to ${OUT_JSON}"

# Fail loudly if upstream is not yet populated. This is preferable to a
# silent no-op smoke that would falsely satisfy the sbatch exit-code gate.
if [ ! -f "${ENTRY_PATH}" ]; then
  echo "[feddiff] FATAL: upstream entry-point ${ENTRY_PATH} not found." >&2
  echo "[feddiff] mmendiet/FedDiff has not yet published its training code." >&2
  echo "[feddiff] See comparators/feddiff/COMMIT.txt for the action list." >&2
  python - "${OUT_JSON}" "${DATASET}" "${ALPHA}" "${SEED}" "${EPSILON}" <<'PY'
import json, sys
out, ds, alpha, seed, eps = sys.argv[1:6]
with open(out, "w") as f:
    json.dump({
        "comparator": "feddiff",
        "dataset": ds,
        "alpha": float(alpha),
        "seed": int(seed),
        "epsilon_requested": float(eps),
        "student_acc": None,
        "generator_epsilon_actual": None,
        "generator_delta_actual": None,
        "status": "upstream_not_populated",
        "note": "mmendiet/FedDiff ships only LICENSE+README as of pin in COMMIT.txt",
    }, f, indent=2)
print(f"[feddiff] wrote stub summary to {out}")
PY
  exit 3
fi

cd "${FEDDIFF_DIR}"

# Run upstream entry-point. Tee stdout so we can extract metrics post-hoc.
python "${ENTRY}" \
  "${DATASET_FLAG}" "${DATASET}" \
  "${ALPHA_FLAG}" "${ALPHA}" \
  "${SEED_FLAG}" "${SEED}" \
  "${N_PARTIES_FLAG}" "${N_PARTIES}" \
  "${EPS_FLAG}" "${EPSILON}" \
  "${DELTA_FLAG}" "${DELTA_VAL}" \
  2>&1 | tee "${RUN_LOG}"

# Extract final student accuracy. FedDiff's eval lines typically print
# "student acc: X.XX" or similar; grep the last accuracy-shaped float as a
# best-effort summary.
STUDENT_ACC="$(grep -Eo '(student[_ ]?acc|global[_ ]?acc|test[_ ]?acc)[: ]+[0-9]*\.[0-9]+' "${RUN_LOG}" | tail -n1 | grep -Eo '[0-9]*\.[0-9]+' || echo 'null')"

# Extract realised epsilon / delta from Opacus accountant. Opacus prints lines
# like "epsilon = X.XX, delta = Y.YY" via PrivacyEngine.get_epsilon(); also
# accept the json-line fallback "actual_epsilon: ...".
EPS_ACTUAL="$(grep -Eo '(epsilon|actual_epsilon)[ =:]+[0-9]*\.[0-9]+' "${RUN_LOG}" | tail -n1 | grep -Eo '[0-9]*\.[0-9]+' || echo 'null')"
DELTA_ACTUAL="$(grep -Eo '(delta|actual_delta)[ =:]+[0-9]+(\.[0-9]+)?(e-?[0-9]+)?' "${RUN_LOG}" | tail -n1 | grep -Eo '[0-9]+(\.[0-9]+)?(e-?[0-9]+)?' || echo 'null')"

python - "${OUT_JSON}" "${STUDENT_ACC}" "${EPS_ACTUAL}" "${DELTA_ACTUAL}" "${DATASET}" "${ALPHA}" "${SEED}" "${EPSILON}" <<'PY'
import json, sys
out, acc, eps_a, delta_a, ds, alpha, seed, eps_req = sys.argv[1:9]

def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None

with open(out, "w") as f:
    json.dump({
        "comparator": "feddiff",
        "dataset": ds,
        "alpha": float(alpha),
        "seed": int(seed),
        "epsilon_requested": float(eps_req),
        "student_acc": _f(acc),
        "generator_epsilon_actual": _f(eps_a),
        "generator_delta_actual": _f(delta_a),
        "status": "ok",
    }, f, indent=2)
print(f"[feddiff] wrote {out}: student_acc={_f(acc)} eps_actual={_f(eps_a)} delta_actual={_f(delta_a)}")
PY
