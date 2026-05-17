#!/bin/bash
#SBATCH --job-name=fedkt_smoke
#SBATCH --partition=t4_ai
#SBATCH --qos=comx29
#SBATCH --account=comx29
#SBATCH --time=00:45:00
#SBATCH --gres=gpu:1
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/fedkt_smoke_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/fedkt_smoke_%j.err
#
# Vendored comparator: FedKT (Li et al. 2021, li2021fedkt)
# Issue 09 (A6.4). Tier-1 DP-floor comparator — canonical PATE-style baseline.
#
# Usage: sbatch jobs/cfd_v2_comp_fedkt.sh <dataset> <alpha> <seed> <epsilon>
#   dataset  : mnist | svhn | celeba | a9a | cod-rna   (FedKT --dataset arg)
#   alpha    : Dirichlet concentration -> FedKT --beta arg
#   seed     : --init_seed
#   epsilon  : target ε ∈ {1, 10}; selects calibrated --gamma noise scale
#
# DP composition (verified against upstream privacy_analysis.py):
#   FedKT applies Laplace noise of scale 1/gamma to vote counts at each
#   public-query aggregation. The end-to-end ε is computed POST-HOC by the
#   moments accountant in privacy_analysis.py over the saved counts matrix.
#   --dp_level=2 puts the noise at the party (teacher) level — which is the
#   composition we actually want bounded for HE-IFD threat-model alignment.
#   We do NOT use Opacus here: FedKT's teacher training is plaintext SGD;
#   ALL privacy is consumed by the noisy-max query phase, and the upstream
#   accountant (Abadi/Papernot moments) is what releases ε. The task brief
#   mentioned Opacus's RDPAccountant; substituting it would require re-doing
#   the PATE composition derivation against an RDP→(ε,δ) conversion that
#   upstream does not implement. We instead respect upstream's accountant
#   and report its number — see Comments in issues/09-a64-vendor-fedkt.md.
#
# Conda env: `he_ifd_comparators` — user must create this once with
#   torch>=1.6, torchvision, numpy, scipy, scikit-learn, pandas, xgboost
#   (see comparators/fedkt/requirements.txt). All comparators (06–10)
#   share this env per ralph/prompt.md.

set -euo pipefail

PROJECT_ROOT=/scratch/hkanpak21/HE_IFD
FEDKT_ROOT=${PROJECT_ROOT}/comparators/fedkt
RESULTS_DIR=${PROJECT_ROOT}/results
LOGDIR=${RESULTS_DIR}/fedkt_logs_${SLURM_JOB_ID:-local}
mkdir -p "${LOGDIR}"

# ---------- arg parsing ----------
DATASET=${1:?usage: sbatch cfd_v2_comp_fedkt.sh <dataset> <alpha> <seed> <epsilon>}
ALPHA=${2:?missing alpha}
SEED=${3:?missing seed}
EPSILON=${4:?missing epsilon}

# ---------- gamma calibration for target ε ----------
# Calibrated against privacy_analysis.py for N=10 parties, n_partition=2,
# n_teacher_each_partition=5, query_portion=0.5, MNIST-scale public set.
# Values reflect rough operating points from FedKT paper Table 5; the
# *actual* ε is recomputed below by the accountant and persisted to JSON.
case "${EPSILON}" in
  1)   GAMMA=0.05 ;;
  10)  GAMMA=0.5  ;;
  *)   echo "[fedkt] unsupported epsilon=${EPSILON}; supported: 1, 10" >&2
       exit 2 ;;
esac

# ---------- dataset directory ----------
case "${DATASET}" in
  mnist|MNIST)  DATADIR=${PROJECT_ROOT}/legacy/data_mnist/  ;;
  svhn|SVHN)    DATADIR=${PROJECT_ROOT}/data/svhn/          ;;
  *)            DATADIR=${PROJECT_ROOT}/data/${DATASET}/    ;;
esac

# ---------- conda + env ----------
# shellcheck disable=SC1091
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ifd_comparators

cd "${FEDKT_ROOT}"

PRIV_TAG="priv_${DATASET}_a${ALPHA}_s${SEED}_eps${EPSILON}"
echo "[fedkt] dataset=${DATASET} alpha=${ALPHA} seed=${SEED} target_eps=${EPSILON} gamma=${GAMMA}"
echo "[fedkt] datadir=${DATADIR} logdir=${LOGDIR} priv_tag=${PRIV_TAG}"
nvidia-smi -L || true

# ---------- training + per-query noisy-max with dp_level=2 ----------
export PYTHONUNBUFFERED=1
python -u experiments.py \
  --model=simple-cnn \
  --dataset="${DATASET}" \
  --alg=fedkt \
  --partition=hetero-dir \
  --beta="${ALPHA}" \
  --init_seed="${SEED}" \
  --n_parties=10 \
  --lr=0.001 \
  --stu_lr=0.001 \
  --batch-size=32 \
  --epochs=20 \
  --stu_epochs=20 \
  --final_stu_epochs=20 \
  --n_teacher_each_partition=5 \
  --n_partition=2 \
  --dp_level=2 \
  --gamma="${GAMMA}" \
  --max_z=1 \
  --privacy_analysis_file_name="${PRIV_TAG}" \
  --device='cuda:0' \
  --datadir="${DATADIR}" \
  --logdir="${LOGDIR}/" \
  2>&1 | tee "${LOGDIR}/train.log"

# ---------- locate saved counts npz ----------
# experiments.py writes "<logdir>/<priv_tag>-<n_exp>-dp0.npz" (n_exp starts at 0,
# and our trials=1 default produces only one). dp0 = global aggregation counts;
# dp1 = per-party. Per HE-IFD threat model, dp0 is the load-bearing release.
COUNTS_NPZ="${LOGDIR}/${PRIV_TAG}-0-dp0.npz"
if [[ ! -f "${COUNTS_NPZ}" ]]; then
  # Fallback: find any matching dp0 file
  COUNTS_NPZ=$(ls -t "${LOGDIR}"/*dp0.npz 2>/dev/null | head -1 || true)
fi
if [[ -z "${COUNTS_NPZ}" || ! -f "${COUNTS_NPZ}" ]]; then
  echo "[fedkt] FATAL: no counts .npz produced; cannot run accountant" >&2
  exit 3
fi
echo "[fedkt] accountant input: ${COUNTS_NPZ}"

# ---------- moments accountant → actual post-PATE ε ----------
ACCT_LOG="${LOGDIR}/accountant.log"
python -u privacy_analysis.py \
  --np_path="${COUNTS_NPZ}" \
  --noise_eps="${GAMMA}" \
  --delta=1e-5 \
  --n_partition=2 \
  --n_parties=10 \
  2>&1 | tee "${ACCT_LOG}"

# Final-of-multiple "Epsilon = X." lines is the data-dependent Noisy-Max bound;
# the "Data independent bound =" is the worst-case. We report both for honesty
# but the post-PATE field uses the data-dependent number (load-bearing per
# task spec).
POST_PATE_EPS=$(grep -E '^Epsilon = ' "${ACCT_LOG}" | tail -1 | awk '{print $3}' | tr -d '.')
DATA_IND_EPS=$(grep -E '^Data independent bound = ' "${ACCT_LOG}" | tail -1 | awk '{print $5}' | tr -d '.')
PARTY_LEVEL_EPS=$(grep -E '^Party Level Epsilon:' "${ACCT_LOG}" | tail -1 | awk -F: '{print $2}' | tr -d '. ')

# Teacher epsilon is the per-query Laplace mechanism budget: 2*gamma per call.
# Reported separately so the post-PATE composition is auditable.
TEACHER_EPS=$(python -c "print(2.0 * ${GAMMA})")

# ---------- student accuracy (last reported by experiments.py) ----------
STU_ACC=$(grep -E 'global_stu_test_acc:' "${LOGDIR}/train.log" | tail -1 | awk '{print $NF}')
[[ -z "${STU_ACC}" ]] && STU_ACC="null"

# ---------- JSON dump (load-bearing field: post_pate_epsilon_actual) ----------
OUT_JSON="${RESULTS_DIR}/fedkt_smoke_${SLURM_JOB_ID:-local}.json"
python - <<PYEOF > "${OUT_JSON}"
import json
out = {
  "method": "fedkt",
  "upstream_sha": "0bb9a89ea266c057990a4a326b586ed3d2fb2df8",
  "dataset": "${DATASET}",
  "alpha": ${ALPHA},
  "seed": ${SEED},
  "n_parties": 10,
  "n_partition": 2,
  "n_teacher_each_partition": 5,
  "target_epsilon": ${EPSILON},
  "gamma_noise_param": ${GAMMA},
  "delta_actual": 1e-5,
  "teacher_epsilon_actual": ${TEACHER_EPS},
  "post_pate_epsilon_actual": ${POST_PATE_EPS:-null},
  "post_pate_epsilon_data_independent": ${DATA_IND_EPS:-null},
  "post_pate_epsilon_party_level": ${PARTY_LEVEL_EPS:-null},
  "student_acc": ${STU_ACC},
  "accountant": "FedKT moments-accountant (privacy_analysis.py); NOT Opacus",
  "dp_level": 2,
  "counts_npz": "${COUNTS_NPZ}",
  "accountant_log": "${ACCT_LOG}",
}
print(json.dumps(out, indent=2))
PYEOF

echo "[fedkt] wrote ${OUT_JSON}"
cat "${OUT_JSON}"
