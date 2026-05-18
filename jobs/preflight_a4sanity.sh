#!/usr/bin/env bash
# HE-IFD A4-sanity preflight gate launcher (issue 15 / PRD section 9.5.4).
#
# Usage:
#   bash jobs/preflight_a4sanity.sh \
#       --dataset MNIST --alpha 0.3 --seed 42 \
#       [--comparator coboost|fedmd] [--threshold-pp 2.0] [--timeout-sec 7200]
#
# This wrapper is intentionally a plain `bash` script, NOT an sbatch job:
# the preflight does no training itself -- it submits two sbatch jobs
# (one HE-IFD warmstart cell + one plaintext comparator cell), polls
# sacct, and computes the accuracy gap. That orchestration is allowed
# on the login node by the golden rule (no heavy torch / tenseal work
# is done in this process).
#
# Because the two spawned jobs may take hours to complete, the right
# invocation pattern for unattended runs is nohup + & + a log file, e.g.:
#
#   nohup bash jobs/preflight_a4sanity.sh \
#       --dataset MNIST --alpha 0.3 --seed 42 \
#       > results/preflight_a4sanity.nohup.log 2>&1 &
#   disown
#
# Exit codes (propagated from prototypes/preflight_a4sanity.py):
#   0  PASS  -- HE-IFD beats comparator by >= threshold (default 2 pp).
#   2  FAIL  -- gap < threshold; HALT AND ESCALATE per PRD 9.5.4.
#   3  INCONCLUSIVE -- a cell failed/timed out/OOM'd; no verdict made.
#   1  orchestration error (sbatch missing, args bad, etc.).
#
# A JSON record of the run is always written to
# results/preflight_a4sanity_<UTC-timestamp>.json (see python script).

set -euo pipefail

REPO_ROOT="/scratch/hkanpak21/HE_IFD"
PRELIGHT_PY="${REPO_ROOT}/prototypes/preflight_a4sanity.py"

if [ ! -f "${PRELIGHT_PY}" ]; then
    echo "[preflight] missing ${PRELIGHT_PY}" >&2
    exit 1
fi

# Activate the canonical env. The preflight script itself only needs the
# stdlib (subprocess, json, time), but importing prototypes.cell_schema
# may pull in heavier deps once issue 14 lands, so we activate he_ofl up
# front for safety.
CONDA_BASE="/opt/ohpc/pub/compiler/conda3/latest"
if [ -f "${CONDA_BASE}/etc/profile.d/conda.sh" ]; then
    # shellcheck disable=SC1091
    source "${CONDA_BASE}/etc/profile.d/conda.sh"
    conda activate he_ofl 2>/dev/null || true
fi

exec python -u "${PRELIGHT_PY}" "$@"
