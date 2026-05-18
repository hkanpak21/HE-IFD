#!/usr/bin/env python3
"""
HE-IFD A4-sanity preflight gate (issue 15 / PRD section 9.5.4).

Runs one HE-IFD warmstart cell against one plaintext no-DP comparator cell
(Co-Boosting or FedMD) on a single (dataset, alpha, seed). If the accuracy
gap is < 2 pp, halts and escalates so the user can decide whether the
"no accuracy degradation vs prior one-shot FL" claim is still defensible
before committing the full A4.1 grid (hundreds of cells, hours of compute).

Orchestration only -- this script submits two sbatch jobs, polls sacct,
reads their CellResult JSON outputs, and prints a verdict. It performs NO
training itself, so it is safe to invoke directly on the login node (or
under nohup for the multi-hour wait).

CLI
---
    python prototypes/preflight_a4sanity.py \\
        --dataset MNIST \\
        --alpha 0.3 \\
        --seed 42 \\
        [--comparator coboost|fedmd]  # default fedmd (smaller wall-clock)
        [--threshold-pp 2.0]          # gap threshold for halt
        [--timeout-sec 7200]          # max wait for both jobs (default 2h)

Exit codes
----------
    0  PREFLIGHT PASS: heifd_acc - comparator_acc >= threshold_pp.
    2  PREFLIGHT FAIL: gap < threshold_pp -- halt and escalate per PRD 9.5.4.
    3  INCONCLUSIVE: at least one cell failed/timed out/OOM'd; no verdict.
    1  CLI / orchestration error (argparse, sbatch missing, etc.).

Outputs
-------
    Always writes results/preflight_a4sanity_<UTC>.json with both cell
    payloads + the verdict (or the diagnostic, if inconclusive) so the
    user has a record regardless of outcome.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path("/scratch/hkanpak21/HE_IFD")
RESULTS_DIR = REPO_ROOT / "results"
CELLS_DIR = RESULTS_DIR / "cells"

POLL_INTERVAL_SEC = 30
TERMINAL_STATES = {
    "COMPLETED",
    "FAILED",
    "TIMEOUT",
    "CANCELLED",
    "OUT_OF_MEMORY",
    "NODE_FAIL",
    "BOOT_FAIL",
    "PREEMPTED",
    "DEADLINE",
}
SUCCESS_STATES = {"COMPLETED"}

HEIFD_JOB_SCRIPT = REPO_ROOT / "jobs" / "cell_heifd.sh"  # owned by issue 14
COMPARATOR_SCRIPTS = {
    "coboost": REPO_ROOT / "jobs" / "cfd_v2_comp_coboost.sh",
    "fedmd": REPO_ROOT / "jobs" / "cfd_v2_comp_fedmd.sh",
}


# ---------------------------------------------------------------------------
# Deferred import of cell_schema (issue 14 owns the file).
# ---------------------------------------------------------------------------


def _load_cell_result_cls():
    """
    Import prototypes.cell_schema.CellResult on demand.

    This is deferred so the preflight script remains syntax-clean and
    importable even if issue 14 has not landed cell_schema.py yet. The
    error message points the user at the upstream owner.
    """
    try:
        sys.path.insert(0, str(REPO_ROOT))
        from prototypes.cell_schema import CellResult  # type: ignore
    except ImportError as exc:  # pragma: no cover - exercised at runtime only
        raise ImportError(
            "prototypes.cell_schema.CellResult is not available. "
            "This module is owned by issue 14 (end-to-end HE-IFD pipeline). "
            "The preflight gate cannot parse cell outputs without it. "
            "Wait for issue 14 to land before invoking the preflight."
        ) from exc
    return CellResult


# ---------------------------------------------------------------------------
# sbatch submission + sacct polling
# ---------------------------------------------------------------------------


def submit_sbatch(script: Path, args: List[str]) -> str:
    """
    Submit `script` with positional args via sbatch and return the job_id.

    Uses `sbatch --parsable` so stdout is just "<job_id>" (or
    "<job_id>;<cluster>") -- we split on ';' and take the first field.
    """
    if not script.exists():
        raise FileNotFoundError(f"sbatch script not found: {script}")
    cmd = ["sbatch", "--parsable", str(script), *args]
    print(f"[preflight] submitting: {' '.join(cmd)}", flush=True)
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            f"sbatch failed for {script.name} (rc={proc.returncode}): "
            f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
        )
    raw = proc.stdout.strip().splitlines()[-1]
    job_id = raw.split(";", 1)[0].strip()
    if not job_id:
        raise RuntimeError(f"could not parse job_id from sbatch output: {proc.stdout!r}")
    print(f"[preflight]   -> job_id={job_id}", flush=True)
    return job_id


def query_sacct_state(job_id: str) -> Optional[str]:
    """
    Return the SLURM state for `job_id` via `sacct -X -n -P -o State`.

    `-X` strips the .batch / .extern sub-steps, `-n` omits the header,
    `-P` uses `|` as a separator (no padding). Returns None if sacct
    yields no rows (job not yet enqueued in the accounting DB).
    """
    cmd = ["sacct", "-j", job_id, "-o", "State", "-X", "-n", "-P"]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        # transient sacct failure -- treat as "unknown, try again"
        return None
    lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    if not lines:
        return None
    # First line is the primary job step. Strip CANCELLED-by-uid suffixes.
    state = lines[0].split(" ")[0]
    return state


def poll_until_terminal(
    job_ids: List[str], timeout_sec: int, interval_sec: int = POLL_INTERVAL_SEC
) -> Dict[str, str]:
    """
    Block until every job_id reaches a terminal state, or `timeout_sec` elapses.

    Returns a dict {job_id: state}. Jobs that never reach a terminal state
    within the budget are reported as state "TIMEOUT_PREFLIGHT" so the
    caller can distinguish a SLURM TIMEOUT (the job itself ran past its
    --time= budget) from a preflight-watchdog timeout (we gave up waiting).
    """
    deadline = time.monotonic() + timeout_sec
    states: Dict[str, str] = {jid: "PENDING" for jid in job_ids}
    while True:
        for jid in job_ids:
            if states[jid] in TERMINAL_STATES:
                continue
            s = query_sacct_state(jid)
            if s is not None:
                states[jid] = s
        remaining = [jid for jid, st in states.items() if st not in TERMINAL_STATES]
        if not remaining:
            return states
        if time.monotonic() >= deadline:
            for jid in remaining:
                states[jid] = "TIMEOUT_PREFLIGHT"
            return states
        time.sleep(interval_sec)


# ---------------------------------------------------------------------------
# Result-file location + parsing
# ---------------------------------------------------------------------------


def find_cell_result(job_id: str) -> Optional[Path]:
    """
    Locate the per-cell JSON output for `job_id`.

    Issue 14's cell wrapper writes results/cells/*_<job_id>.json (per the
    coordination protocol). Comparators currently write to results/ with
    names like coboost_smoke_<job_id>.json or fedmd_smoke_<job_id>.json;
    accept either layout so the gate works against the comparator scripts
    as they exist today.
    """
    candidates: List[Path] = []
    if CELLS_DIR.exists():
        candidates.extend(CELLS_DIR.glob(f"*_{job_id}.json"))
    if RESULTS_DIR.exists():
        candidates.extend(RESULTS_DIR.glob(f"*_{job_id}.json"))
    # de-dupe while preserving order
    seen: set = set()
    unique = [p for p in candidates if not (p in seen or seen.add(p))]
    if not unique:
        return None
    # Prefer files under results/cells/ (issue-14 canonical layout).
    unique.sort(key=lambda p: (0 if CELLS_DIR in p.parents else 1, p.name))
    return unique[0]


def parse_cell_result(job_id: str, path: Path) -> Tuple[Dict[str, Any], Optional[float], str]:
    """
    Parse a cell-result JSON.

    Returns (payload, accuracy, status_label). Tries the CellResult schema
    first (issue 14); if the JSON has the older comparator shape
    (`final_student_acc` or `student_acc` plus no `status` field), falls
    back to a heuristic mapping.
    """
    payload = json.loads(path.read_text())

    # Preferred path: cell_schema.CellResult roundtrip.
    try:
        CellResult = _load_cell_result_cls()
        cell = CellResult.from_dict(payload) if hasattr(CellResult, "from_dict") else None
    except ImportError:
        cell = None
    except Exception:
        cell = None

    if cell is not None:
        acc = getattr(cell, "accuracy", None)
        status = getattr(cell, "status", "unknown") or "unknown"
        return payload, (float(acc) if acc is not None else None), status

    # Fallback: comparator-shaped JSON (no `status` field, accuracy under
    # one of a few well-known keys).
    for key in ("accuracy", "final_student_acc", "student_acc"):
        if key in payload and payload[key] is not None:
            try:
                return payload, float(payload[key]), "success"
            except (TypeError, ValueError):
                pass
    return payload, None, payload.get("status", "unknown") or "unknown"


# ---------------------------------------------------------------------------
# Verdict + JSON summary
# ---------------------------------------------------------------------------


def make_summary_path() -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    return RESULTS_DIR / f"preflight_a4sanity_{ts}.json"


def write_summary(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"[preflight] summary written: {path}", flush=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="preflight_a4sanity",
        description="HE-IFD A4-sanity preflight gate (issue 15 / PRD 9.5.4).",
    )
    p.add_argument("--dataset", required=True, help="dataset name (e.g. MNIST, CIFAR10)")
    p.add_argument("--alpha", required=True, type=float, help="Dirichlet alpha (e.g. 0.3)")
    p.add_argument("--seed", required=True, type=int, help="random seed (e.g. 42)")
    p.add_argument(
        "--comparator",
        choices=sorted(COMPARATOR_SCRIPTS.keys()),
        default="fedmd",
        help="plaintext no-DP comparator (default: fedmd -- smaller wall-clock)",
    )
    p.add_argument(
        "--threshold-pp",
        type=float,
        default=2.0,
        help="gap threshold in pp; halt if (heifd - comparator) < threshold (default 2.0)",
    )
    p.add_argument(
        "--timeout-sec",
        type=int,
        default=7200,
        help="max wall-clock seconds to wait for both jobs (default 7200 = 2h)",
    )
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    comparator_script = COMPARATOR_SCRIPTS[args.comparator]

    summary_path = make_summary_path()
    summary: Dict[str, Any] = {
        "issue": 15,
        "prd_section": "9.5.4",
        "invocation": {
            "dataset": args.dataset,
            "alpha": args.alpha,
            "seed": args.seed,
            "comparator": args.comparator,
            "threshold_pp": args.threshold_pp,
            "timeout_sec": args.timeout_sec,
        },
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "summary_path": str(summary_path),
    }

    # ---- submit both jobs --------------------------------------------------
    try:
        heifd_job_id = submit_sbatch(
            HEIFD_JOB_SCRIPT,
            [args.dataset, str(args.alpha), str(args.seed), "warmstart"],
        )
        comparator_job_id = submit_sbatch(
            comparator_script,
            [args.dataset, str(args.alpha), str(args.seed)],
        )
    except (FileNotFoundError, RuntimeError) as exc:
        summary["error"] = f"sbatch submission failed: {exc}"
        summary["verdict"] = "ERROR_SUBMIT"
        write_summary(summary_path, summary)
        print(f"[preflight] ERROR: {exc}", file=sys.stderr)
        return 1

    summary["job_ids"] = {"heifd": heifd_job_id, "comparator": comparator_job_id}

    # ---- poll until both terminal -----------------------------------------
    print(
        f"[preflight] polling sacct every {POLL_INTERVAL_SEC}s "
        f"(timeout={args.timeout_sec}s)",
        flush=True,
    )
    states = poll_until_terminal([heifd_job_id, comparator_job_id], args.timeout_sec)
    summary["sacct_states"] = states
    print(f"[preflight] terminal states: {states}", flush=True)

    # ---- locate + parse cell outputs --------------------------------------
    cell_payloads: Dict[str, Any] = {}
    accuracies: Dict[str, Optional[float]] = {}
    statuses: Dict[str, str] = {}
    for label, jid in (("heifd", heifd_job_id), ("comparator", comparator_job_id)):
        sacct_state = states.get(jid, "UNKNOWN")
        path = find_cell_result(jid)
        if path is None:
            cell_payloads[label] = {
                "job_id": jid,
                "sacct_state": sacct_state,
                "error": "no result JSON found",
                "search_paths": [str(CELLS_DIR), str(RESULTS_DIR)],
            }
            accuracies[label] = None
            statuses[label] = "missing_output"
            continue
        try:
            payload, acc, status = parse_cell_result(jid, path)
        except Exception as exc:  # parse errors / missing CellResult etc.
            cell_payloads[label] = {
                "job_id": jid,
                "sacct_state": sacct_state,
                "result_path": str(path),
                "error": f"parse failure: {exc}",
            }
            accuracies[label] = None
            statuses[label] = "parse_error"
            continue
        cell_payloads[label] = {
            "job_id": jid,
            "sacct_state": sacct_state,
            "result_path": str(path),
            "payload": payload,
        }
        accuracies[label] = acc
        statuses[label] = status

    summary["cells"] = cell_payloads
    summary["accuracies"] = accuracies
    summary["cell_statuses"] = statuses

    # ---- verdict -----------------------------------------------------------
    both_success = (
        states.get(heifd_job_id) in SUCCESS_STATES
        and states.get(comparator_job_id) in SUCCESS_STATES
        and statuses.get("heifd") == "success"
        and statuses.get("comparator") == "success"
        and accuracies.get("heifd") is not None
        and accuracies.get("comparator") is not None
    )

    if not both_success:
        diag = (
            "INCONCLUSIVE -- at least one cell did not produce a usable "
            "accuracy. Per-cell summary:"
        )
        for label, jid in (("heifd", heifd_job_id), ("comparator", comparator_job_id)):
            diag += (
                f"\n  - {label} (job {jid}): sacct={states.get(jid)} "
                f"status={statuses.get(label)} acc={accuracies.get(label)}"
            )
        summary["verdict"] = "INCONCLUSIVE"
        summary["diagnostic"] = diag
        summary["finished_utc"] = datetime.now(timezone.utc).isoformat()
        write_summary(summary_path, summary)
        print(diag, file=sys.stderr)
        print(
            "[preflight] escalate to user; no decision possible without "
            "two successful cells.",
            file=sys.stderr,
        )
        return 3

    heifd_acc = float(accuracies["heifd"])  # type: ignore[arg-type]
    comparator_acc = float(accuracies["comparator"])  # type: ignore[arg-type]
    gap_pp = (heifd_acc - comparator_acc) * 100.0
    summary["gap_pp"] = gap_pp
    summary["heifd_acc"] = heifd_acc
    summary["comparator_acc"] = comparator_acc

    if gap_pp >= args.threshold_pp:
        verdict = f"PREFLIGHT PASS -- gap = {gap_pp:.2f} pp"
        summary["verdict"] = "PASS"
        summary["finished_utc"] = datetime.now(timezone.utc).isoformat()
        write_summary(summary_path, summary)
        print(verdict)
        return 0

    verdict = (
        f"PREFLIGHT FAIL -- gap = {gap_pp:.2f} pp "
        f"(threshold = {args.threshold_pp} pp). "
        f"HALT AND ESCALATE per PRD section 9.5.4."
    )
    summary["verdict"] = "FAIL"
    summary["finished_utc"] = datetime.now(timezone.utc).isoformat()
    write_summary(summary_path, summary)
    print(verdict)
    return 2


if __name__ == "__main__":
    sys.exit(main())
