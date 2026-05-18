#!/usr/bin/env python3
"""Aggregate per-cell A4.1 grid results into a long-form CSV.

Globs `results/cells/*.json`, parses each via the shared schema in
`prototypes/cell_schema.py:CellResult` (written by issue 14), and writes a
long-form CSV row per cell. If a manifest is supplied (the file emitted by
`jobs/generate_grid.py`), submitted cells without a matching JSON are
recorded with status="missing" — i.e. the sbatch was submitted but no
output JSON is present (either still running, crashed before writing, or
the cell was a `known_blocked` placeholder).

INDEPENDENCE GUARANTEE (user directive 2026-05-17):
    JSON parse errors on a single file do NOT crash the aggregator — that
    file is recorded with status="failed", error_class="json_parse_error",
    and the run continues. Per-method success rates are reported so the
    operator can see which sub-grid (e.g. FedDiff = upstream placeholder)
    is degraded without the rest of the grid being lost.

Usage:
    python jobs/collect_grid.py [--out results/grid_<UTC-timestamp>.csv]
                                [--manifest results/grid_manifest_*.json]
                                [--cells-dir results/cells]
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import glob
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
CELLS_DIR_DEFAULT = REPO_ROOT / "results" / "cells"
RESULTS_DIR = REPO_ROOT / "results"

# Long-form CSV columns. Mirrors the per-cell schema from
# prototypes/cell_schema.py:CellResult (issue 14). Kept stable so downstream
# pandas / R scripts can rely on column order.
CSV_COLUMNS = [
    "method",
    "dataset",
    "alpha",
    "seed",
    "N",
    "variant",
    "status",
    "student_acc",
    "mean_teacher_acc",
    "oracle_acc",
    "epsilon_actual",
    "delta_actual",
    "wall_clock_sec",
    "job_id",
    "node",
    "error_class",
    "notes",
]


def _utc_stamp() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


# ---------------------------------------------------------------------------
# Schema import. Defensive: if issue 14 has not yet written
# prototypes/cell_schema.py we fall back to a tolerant dict-based parser so
# the aggregator scaffold still runs (returns header + zero rows on empty
# cells/, mirroring the acceptance gate).
# ---------------------------------------------------------------------------
sys.path.insert(0, str(REPO_ROOT))
try:
    from prototypes.cell_schema import CellResult  # type: ignore
    _HAS_SCHEMA = True
except Exception:  # pragma: no cover - fallback path
    CellResult = None  # type: ignore
    _HAS_SCHEMA = False


def _row_from_cellresult(cr: Any) -> dict[str, Any]:
    """Best-effort projection of a CellResult instance into the CSV row dict.

    The shared schema (prototypes/cell_schema.py) names the failure-info
    field `error` (string). The CSV column is `error_class` because the
    aggregator also synthesises its own classes (`json_parse_error`,
    `schema_validation_error`, `no_output_json`) for files the cell never
    wrote. We project the schema's `error` value into `error_class` so the
    final CSV has one consistent error column for downstream consumers.
    """
    def _get(name: str, default: Any = None) -> Any:
        if hasattr(cr, name):
            return getattr(cr, name)
        if isinstance(cr, dict):
            return cr.get(name, default)
        return default

    row = {col: _get(col) for col in CSV_COLUMNS}
    # Schema-native field is `error`; CSV column is `error_class`.
    if row.get("error_class") is None:
        row["error_class"] = _get("error")
    if row.get("status") is None:
        row["status"] = "success"
    return row


def _row_from_raw_dict(d: dict) -> dict[str, Any]:
    """Fallback parser used when prototypes/cell_schema.py is absent."""
    row = {col: d.get(col) for col in CSV_COLUMNS}
    if row.get("error_class") is None:
        row["error_class"] = d.get("error")
    if row.get("status") is None:
        row["status"] = "success"
    return row


def _load_cell_json(path: Path) -> dict[str, Any]:
    """Parse one results/cells/*.json into a CSV row dict.

    Lenient: any exception → status='failed', error_class='json_parse_error'.
    """
    try:
        raw = json.loads(path.read_text())
    except Exception as exc:
        return {
            **{c: None for c in CSV_COLUMNS},
            "status": "failed",
            "error_class": "json_parse_error",
            "notes": f"{type(exc).__name__}: {exc}".replace("\n", " ")[:240],
        }

    if _HAS_SCHEMA:
        try:
            # Prefer a constructor that takes the parsed dict; tolerate either
            # CellResult(**raw) or CellResult.from_dict(raw).
            if hasattr(CellResult, "from_dict"):
                cr = CellResult.from_dict(raw)  # type: ignore[union-attr]
            else:
                cr = CellResult(**raw)  # type: ignore[misc]
            return _row_from_cellresult(cr)
        except Exception as exc:
            return {
                **_row_from_raw_dict(raw),
                "status": "failed",
                "error_class": "schema_validation_error",
                "notes": f"{type(exc).__name__}: {exc}".replace("\n", " ")[:240],
            }

    return _row_from_raw_dict(raw)


def _cell_key(d: dict) -> tuple[str, str, float, int]:
    return (
        str(d.get("method")),
        str(d.get("dataset")),
        float(d.get("alpha")) if d.get("alpha") is not None else float("nan"),
        int(d.get("seed")) if d.get("seed") is not None else -1,
    )


def _load_manifest(path: Path) -> list[dict]:
    try:
        m = json.loads(path.read_text())
    except Exception as exc:
        sys.stderr.write(f"[collect_grid] manifest unreadable: {exc}\n")
        return []
    cells = m.get("cells") or []
    return cells


def _resolve_manifest_path(arg: str | None) -> Path | None:
    """Allow --manifest to be either an exact path or a glob; pick newest match."""
    if arg is None:
        return None
    matches = sorted(glob.glob(arg))
    if not matches:
        sys.stderr.write(f"[collect_grid] no manifest matched glob: {arg}\n")
        return None
    return Path(matches[-1])


def _summarise(rows: list[dict]) -> None:
    per_method_total: dict[str, int] = defaultdict(int)
    per_method_success: dict[str, int] = defaultdict(int)
    per_method_wallclock: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        m = r.get("method") or "<unknown>"
        per_method_total[m] += 1
        if r.get("status") == "success":
            per_method_success[m] += 1
            wc = r.get("wall_clock_sec")
            if isinstance(wc, (int, float)):
                per_method_wallclock[m].append(float(wc))

    width = max((len(k) for k in per_method_total), default=10)
    print("")
    print("=== per-method aggregate ===")
    hdr = f"{'method'.ljust(width)}  success  total  rate    mean_wc_sec"
    print(hdr)
    for m in sorted(per_method_total):
        succ = per_method_success[m]
        tot = per_method_total[m]
        rate = succ / tot if tot else 0.0
        wcs = per_method_wallclock[m]
        mean_wc = sum(wcs) / len(wcs) if wcs else float("nan")
        print(
            f"{m.ljust(width)}  {succ:>7}  {tot:>5}  {rate:>5.2f}  "
            f"{mean_wc:>11.1f}"
        )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=None, help="output CSV path")
    ap.add_argument(
        "--manifest",
        default=None,
        help="grid manifest JSON path or glob (e.g. results/grid_manifest_*.json)",
    )
    ap.add_argument(
        "--cells-dir",
        default=str(CELLS_DIR_DEFAULT),
        help=f"per-cell result dir (default: {CELLS_DIR_DEFAULT})",
    )
    args = ap.parse_args()

    cells_dir = Path(args.cells_dir)
    cells_dir.mkdir(parents=True, exist_ok=True)

    # 1. Parse every JSON file present.
    json_paths = sorted(cells_dir.glob("*.json"))
    rows: list[dict] = []
    found_keys: set[tuple[str, str, float, int]] = set()
    for p in json_paths:
        row = _load_cell_json(p)
        rows.append(row)
        try:
            found_keys.add(_cell_key(row))
        except Exception:
            pass  # row identity missing; keep the row but skip the join key

    # 2. Manifest join: any submitted cell without a JSON → status='missing'.
    manifest_path = _resolve_manifest_path(args.manifest)
    if manifest_path is not None:
        for mcell in _load_manifest(manifest_path):
            key = _cell_key(mcell)
            if key in found_keys:
                continue
            jobid = mcell.get("job_id")
            extras = mcell.get("extra_args") or []
            variant = extras[0] if extras else None
            missing_row = {col: None for col in CSV_COLUMNS}
            missing_row.update(
                {
                    "method": mcell.get("method"),
                    "dataset": mcell.get("dataset"),
                    "alpha": mcell.get("alpha"),
                    "seed": mcell.get("seed"),
                    "variant": variant,
                    "status": "missing",
                    "job_id": jobid,
                    "error_class": "no_output_json",
                    "notes": (
                        "submitted per manifest but no per-cell JSON present "
                        "(still running, crashed before write, or "
                        "known_blocked)"
                    ),
                }
            )
            rows.append(missing_row)

    # 3. Write CSV (header always; zero data rows is fine).
    out_path = (
        Path(args.out)
        if args.out
        else RESULTS_DIR / f"grid_{_utc_stamp()}.csv"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    sys.stderr.write(f"[collect_grid] wrote {len(rows)} rows -> {out_path}\n")

    # 4. Stdout summary.
    _summarise(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
