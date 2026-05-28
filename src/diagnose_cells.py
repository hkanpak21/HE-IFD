"""Issue-013 entrypoint — runs the two KD-dynamics diagnostic cells.

This module is the *only* place we ever call ``run_cell(..., diagnose=True)``
in normal operation. Everything else (sweeps, ablations, headline grids) uses
the byte-identical ``diagnose=False`` path. Keeping the diagnostic invocation
in its own entrypoint guarantees no accidental cross-contamination of sweep
behaviour.

The two cells (issue 013):

* **Cell A — degrading case:** ``resnet18_cifar10`` / α=0.05 / N=10 /
  ``raw_union_K20`` / K=20 / seed 42 → diagnostics + IID acc reproduce the
  θ₀ > final phenomenon observed in 008 and let issue 013 attribute it.
* **Cell B — working case:** ``mlp_mnist`` / α=0.05 / N=10 /
  ``raw_union_K20`` / K=20 / seed 42 → diagnostics on a cell where distillation
  *helps* — control row for the comparison.

K=20 is intentional: it matches the ``raw_union_K20`` method label (warmup
K_per_class=20), and a 20-step trajectory makes the per-step Δ-norm profile
small enough to be JSON-friendly while still spanning the bounded regime the
protocol uses.

Cell JSONs are written under ``results/heifd_013_kd_diagnostic/`` using the
same ``cell_<stem>_<hash>.json`` convention as ``src.sweep`` (the same
descriptor->filename function is imported). The orchestrator can then point
the existing ``src.report`` writer at that directory if desired; an analysis
write-up against the live data is post-run.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List

from .protocol import run_cell
from .sweep import cell_descriptor, cell_filename


# The two diagnostic cells, declared as plain dicts so they are JSON-loggable.
# Per the issue brief: identical (α, N, method, seed, K), differ only in the
# (backbone, dataset) — one degrading (resnet18), one working (mlp).
DEFAULT_CELLS: List[Dict] = [
    {
        "backbone": "resnet18_cifar10",
        "N": 10, "alpha": 0.05, "method": "raw_union_K20",
        "seed": 42, "K": 20,
    },
    {
        "backbone": "mlp_mnist",
        "N": 10, "alpha": 0.05, "method": "raw_union_K20",
        "seed": 42, "K": 20,
    },
]


def write_cell_json(results_dir: Path, res_dict: Dict, desc: Dict) -> Path:
    """Write a per-cell JSON under the same filename convention as src.sweep.

    ``res_dict`` is the ``CellResult.to_dict()`` payload (asdict-ed); ``desc``
    is the descriptor used by ``cell_filename`` for a deterministic hash.
    """
    path = results_dir / cell_filename(desc)
    payload = dict(res_dict)
    payload["_descriptor"] = desc
    path.write_text(json.dumps(payload, indent=2))
    return path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Issue-013 KD-dynamics diagnostic — runs two cells with "
                    "diagnose=True and writes per-cell JSONs.")
    p.add_argument("--case", type=str, default="heifd_013_kd_diagnostic",
                   help="Results case slug -> results/<case>/.")
    p.add_argument("--results-root", type=str, default="results")
    p.add_argument("--data-root", type=str, default="data")
    p.add_argument("--cache-root", type=str, default="cache")
    p.add_argument("--tau", type=float, default=4.0)
    p.add_argument("--student-lr", type=float, default=0.01)
    p.add_argument("--force", action="store_true",
                   help="Recompute even if a cell JSON already exists.")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    job_id = os.environ.get("SLURM_JOB_ID")
    node = os.environ.get("SLURMD_NODENAME") or os.environ.get("HOSTNAME")

    results_dir = Path(args.results_root) / args.case
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "runs").mkdir(exist_ok=True)

    print(f"[013] running {len(DEFAULT_CELLS)} diagnostic cells -> {results_dir}", flush=True)
    for cell in DEFAULT_CELLS:
        desc = cell_descriptor(
            cell["backbone"], cell["N"], cell["alpha"],
            cell["method"], cell["seed"], cell["K"],
        )
        out_path = results_dir / cell_filename(desc)
        if out_path.exists() and not args.force:
            prior_ok = False
            try:
                prior_ok = json.loads(out_path.read_text()).get("status") == "success"
            except (json.JSONDecodeError, OSError):
                prior_ok = False
            if prior_ok:
                print(f"[013] skip  {out_path.name} (success exists)", flush=True)
                continue
            print(f"[013] retry {out_path.name} (prior status != success)", flush=True)
        print(f"[013] start {cell['backbone']} N={cell['N']} a={cell['alpha']} "
              f"{cell['method']} s={cell['seed']} K={cell['K']} diagnose=True",
              flush=True)
        res = run_cell(
            backbone=cell["backbone"], N=cell["N"], alpha=cell["alpha"],
            seed=cell["seed"], method=cell["method"], K=cell["K"],
            tau=args.tau, student_lr=args.student_lr,
            data_root=args.data_root, cache_root=args.cache_root,
            job_id=job_id, node=node,
            diagnose=True,
        )
        write_cell_json(results_dir, res.to_dict(), desc)
        tag = "ok" if res.status == "success" else "FAIL"
        acc = f"{res.acc:.4f}" if res.acc is not None else "n/a"
        t0 = f"{res.theta0_acc:.4f}" if res.theta0_acc is not None else "n/a"
        print(f"[013] {tag}   acc={acc} theta0_acc={t0} "
              f"wall={res.wall_clock_sec:.1f}s err={res.error}", flush=True)
    print("[013] done.", flush=True)


if __name__ == "__main__":
    main()
