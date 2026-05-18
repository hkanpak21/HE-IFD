#!/usr/bin/env python3
"""Generate per-cell sbatch submissions for the A4.1 headline accuracy grid.

Reads `jobs/grid_spec.yaml`, expands the Cartesian product of
(method × dataset × alpha × seed) under the chosen tier filter, and emits
one independent `sbatch <wrapper> <dataset> <alpha> <seed> <extra_args...>`
invocation per cell.

INDEPENDENCE GUARANTEE (user directive 2026-05-17):
    No --dependency=afterok edges. Each cell stands alone. The aggregator
    (jobs/collect_grid.py) reports per-cell status from whatever JSON files
    are present at run time; missing/failed cells do not block siblings.

Usage:
    python jobs/generate_grid.py --tier {A,B,C} [--method M] [--dry-run] [--limit N]

Outputs:
    - Submitted sbatch jobs (or printed commands under --dry-run).
    - A manifest at results/grid_manifest_<UTC-timestamp>.json mapping each
      submitted cell to its sbatch job id (under --dry-run the manifest job
      ids are recorded as "DRYRUN").

Cell identity is stamped on every sbatch via `--comment "method=... dataset=...
alpha=... seed=..."` so `sacct -o JobID,Comment` can later resolve the mapping
even if the manifest is lost.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import itertools
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - env hint
    sys.stderr.write(
        "[generate_grid] PyYAML missing. Run from conda env `he_ofl` or\n"
        "               `pip install pyyaml`.\n"
    )
    raise

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = REPO_ROOT / "jobs" / "grid_spec.yaml"
RESULTS_DIR = REPO_ROOT / "results"


def _utc_stamp() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _load_spec(path: Path) -> dict:
    with path.open("r") as fh:
        return yaml.safe_load(fh)


def _resolve_tier(spec: dict, tier: str) -> tuple[list[str], list[float], list[int]]:
    grid = spec["grid"]
    tiers = spec["tiers"]
    if tier not in tiers:
        raise SystemExit(
            f"[generate_grid] unknown tier '{tier}'. choices: {sorted(tiers)}"
        )
    t = tiers[tier]
    datasets = t.get("datasets_filter") or grid["datasets"]
    alphas = t.get("alphas_filter") or grid["alphas"]
    seeds = t.get("seeds_filter") or grid["seeds"]
    # normalise scalar types
    alphas = [float(a) for a in alphas]
    seeds = [int(s) for s in seeds]
    return list(datasets), list(alphas), list(seeds)


def _skip_set(spec: dict) -> set[tuple[str, str, float, int]]:
    skip = spec.get("skip") or []
    out: set[tuple[str, str, float, int]] = set()
    for row in skip:
        out.add(
            (
                str(row["method"]),
                str(row["dataset"]),
                float(row["alpha"]),
                int(row["seed"]),
            )
        )
    return out


def _expand_cells(spec: dict, tier: str, method_filter: str | None) -> list[dict]:
    datasets, alphas, seeds = _resolve_tier(spec, tier)
    methods = spec["methods"]
    if method_filter is not None:
        if method_filter not in methods:
            raise SystemExit(
                f"[generate_grid] unknown method '{method_filter}'. "
                f"choices: {sorted(methods)}"
            )
        method_keys = [method_filter]
    else:
        method_keys = list(methods.keys())

    skip = _skip_set(spec)
    cells: list[dict] = []
    for method, dataset, alpha, seed in itertools.product(
        method_keys, datasets, alphas, seeds
    ):
        if (method, dataset, alpha, seed) in skip:
            continue
        meta = methods[method]
        cells.append(
            {
                "method": method,
                "dataset": dataset,
                "alpha": float(alpha),
                "seed": int(seed),
                "wrapper": meta["wrapper"],
                "extra_args": [str(a) for a in (meta.get("extra_args") or [])],
                "known_blocked": meta.get("known_blocked"),
            }
        )
    return cells


def _cell_comment(cell: dict) -> str:
    return (
        f"method={cell['method']} dataset={cell['dataset']} "
        f"alpha={cell['alpha']} seed={cell['seed']}"
    )


def _sbatch_argv(cell: dict) -> list[str]:
    wrapper = str(REPO_ROOT / cell["wrapper"])
    argv = [
        "sbatch",
        "--comment",
        _cell_comment(cell),
        wrapper,
        str(cell["dataset"]),
        str(cell["alpha"]),
        str(cell["seed"]),
    ]
    argv.extend(cell["extra_args"])
    return argv


_JOBID_RE = re.compile(r"Submitted batch job (\d+)")


def _submit(argv: list[str]) -> str:
    """Submit one sbatch invocation; return the job id or 'SUBMIT_FAILED:<reason>'."""
    try:
        res = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            check=False,
            cwd=str(REPO_ROOT),
        )
    except FileNotFoundError as exc:
        return f"SUBMIT_FAILED:sbatch_not_found:{exc}"
    if res.returncode != 0:
        first_line = (res.stderr or res.stdout or "").splitlines()[:1]
        msg = first_line[0] if first_line else f"rc={res.returncode}"
        return f"SUBMIT_FAILED:{msg}"
    m = _JOBID_RE.search(res.stdout or "")
    if not m:
        return f"SUBMIT_FAILED:no_jobid_in_stdout:{(res.stdout or '').strip()[:120]}"
    return m.group(1)


def _print_summary(cells: list[dict], manifest_rows: list[dict]) -> None:
    per_method: dict[str, int] = {}
    for c in cells:
        per_method[c["method"]] = per_method.get(c["method"], 0) + 1
    blocked: list[str] = sorted(
        {c["method"] for c in cells if c.get("known_blocked")}
    )
    width = max((len(k) for k in per_method), default=8)
    print("")
    print("=== submission summary ===")
    print(f"{'method'.ljust(width)}  count")
    for m in sorted(per_method):
        flag = "  [known_blocked]" if m in blocked else ""
        print(f"{m.ljust(width)}  {per_method[m]:>5}{flag}")
    print(f"{'TOTAL'.ljust(width)}  {sum(per_method.values()):>5}")
    if blocked:
        print("")
        print("note: methods flagged known_blocked are still submitted so the")
        print("      aggregator records their absence honestly; do not chain")
        print("      --dependency=afterok on them.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tier", required=True, choices=["A", "B", "C"])
    ap.add_argument("--method", default=None, help="restrict to one method key")
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="print sbatch commands instead of submitting",
    )
    ap.add_argument(
        "--limit",
        type=int,
        default=None,
        help="submit at most N cells (after tier+method filtering)",
    )
    ap.add_argument(
        "--spec",
        default=str(SPEC_PATH),
        help=f"path to grid spec yaml (default: {SPEC_PATH})",
    )
    args = ap.parse_args()

    spec = _load_spec(Path(args.spec))
    cells = _expand_cells(spec, args.tier, args.method)
    if args.limit is not None:
        cells = cells[: args.limit]

    if not cells:
        print("[generate_grid] no cells to submit after filters.", file=sys.stderr)
        return 1

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    manifest_rows: list[dict] = []

    for cell in cells:
        argv = _sbatch_argv(cell)
        if args.dry_run:
            # Quote argv so the printed line is copy-paste safe.
            printable = " ".join(_shquote(a) for a in argv)
            print(printable)
            jobid = "DRYRUN"
        else:
            jobid = _submit(argv)
            print(f"[{cell['method']}] {cell['dataset']} α={cell['alpha']} "
                  f"seed={cell['seed']} -> {jobid}")
        manifest_rows.append(
            {
                "method": cell["method"],
                "dataset": cell["dataset"],
                "alpha": cell["alpha"],
                "seed": cell["seed"],
                "wrapper": cell["wrapper"],
                "extra_args": cell["extra_args"],
                "known_blocked": cell.get("known_blocked"),
                "sbatch_argv": argv,
                "job_id": jobid,
            }
        )

    stamp = _utc_stamp()
    manifest_path = RESULTS_DIR / f"grid_manifest_{stamp}.json"
    manifest = {
        "generated_at_utc": stamp,
        "tier": args.tier,
        "method_filter": args.method,
        "dry_run": bool(args.dry_run),
        "spec_path": str(args.spec),
        "cell_count": len(manifest_rows),
        "cells": manifest_rows,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    print(f"[generate_grid] manifest -> {manifest_path}")

    _print_summary(cells, manifest_rows)
    return 0


def _shquote(s: str) -> str:
    """Minimal shell-quote: wrap in single quotes if it contains anything funky."""
    if s and all(c.isalnum() or c in "-_./=" for c in s):
        return s
    return "'" + s.replace("'", "'\\''") + "'"


if __name__ == "__main__":
    raise SystemExit(main())
