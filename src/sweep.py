"""Resumable, chunkable sweep CLI — the only entrypoint sbatch runs.

Builds the Cartesian grid over (backbone × N × α × method × seed × K), then runs
each cell via ``protocol.run_cell`` and persists a per-cell JSON. Two operational
properties required by issue 001 / CLAUDE.md:

* **Resumable.** Each cell writes ``cell_<stem>_<hash>.json``; the stem+hash are a
  deterministic function of the cell descriptor (NOT the Slurm job id), so a
  re-run skips any cell whose JSON already exists. A preempted job resumes
  instead of restarting.
* **Chunkable.** The flattened, deterministically-ordered cell list can be split
  into ``--num-chunks`` contiguous chunks; ``--chunk-index`` (or env CHUNK_INDEX)
  selects which chunk this job runs. A large grid is thus split across multiple
  ≤3-hour VALAR jobs (the cluster wall-clock limit) — e.g. a Slurm job array
  with ``--num-chunks=$SLURM_ARRAY_TASK_COUNT --chunk-index=$SLURM_ARRAY_TASK_ID``.

Usage (single verification cell):
    python -m src.sweep --backbones mlp_mnist --Ns 16 --alphas 1.0 \
        --methods raw_union_K20 --seeds 42 --K 300 \
        --case v1_he-ifd_mlp_mnist_verify

Examples of the grid axes are documented in ``--help``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from .protocol import BACKBONES, CellResult, run_cell
from .report import write_report


# ---------------------------------------------------------------------------
# Descriptor / filename helpers (deterministic -> resumable)
# ---------------------------------------------------------------------------
def cell_descriptor(backbone: str, N: int, alpha: float, method: str,
                    seed: int, K: int) -> Dict:
    return {"backbone": backbone, "N": N, "alpha": alpha,
            "method": method, "seed": seed, "K": K}


def descriptor_hash(desc: Dict) -> str:
    canon = json.dumps(desc, sort_keys=True, default=str)
    return hashlib.sha256(canon.encode()).hexdigest()[:12]


def cell_filename(desc: Dict) -> str:
    stem = (f"cell_{desc['backbone']}_N{desc['N']}_a{desc['alpha']}"
            f"_{desc['method']}_s{desc['seed']}_K{desc['K']}")
    return f"{stem}_{descriptor_hash(desc)}.json"


def write_cell_json(results_dir: Path, res: CellResult, desc: Dict) -> Path:
    path = results_dir / cell_filename(desc)
    payload = res.to_dict()
    payload["_descriptor"] = desc
    path.write_text(json.dumps(payload, indent=2))
    return path


def load_cells(results_dir: Path) -> List[CellResult]:
    """Reload every per-cell JSON in a case dir into CellResult objects (for report)."""
    cells: List[CellResult] = []
    for p in sorted(results_dir.glob("cell_*.json")):
        try:
            d = json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        d.pop("_descriptor", None)
        valid = {f: d[f] for f in CellResult.__dataclass_fields__ if f in d}
        cells.append(CellResult(**valid))
    return cells


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_float_list(s: str) -> List[float]:
    out = []
    for x in s.split(","):
        x = x.strip()
        if not x:
            continue
        out.append(float("inf") if x in ("inf", "Inf") else float(x))
    return out


def parse_int_list(s: str) -> List[int]:
    return [int(x) for x in s.split(",") if x.strip()]


def parse_str_list(s: str) -> List[str]:
    return [x.strip() for x in s.split(",") if x.strip()]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Resumable, chunkable HE-IFD protocol sweep.")
    p.add_argument("--backbones", type=str, default="mlp_mnist",
                   help=f"Comma list from {sorted(BACKBONES)}.")
    p.add_argument("--Ns", type=str, default="16",
                   help="Client counts, e.g. 5,10,20,50.")
    p.add_argument("--alphas", type=str, default="1.0",
                   help="Dirichlet alphas, e.g. 0.01,0.05,0.1,0.3,1.0.")
    p.add_argument("--methods", type=str, default="no_phase0,raw_union_K20",
                   help="Method panel, e.g. no_phase0,warmup_only_labelled,"
                        "labelled_probe_warmup,raw_union_K20,dp_avg_eps2_K20,"
                        "dp_avg_eps8_K20.")
    p.add_argument("--seeds", type=str, default="42",
                   help="Seeds, e.g. 42,43,44.")
    p.add_argument("--K", type=int, default=300,
                   help="Bounded distillation trajectory length (swept axis).")
    p.add_argument("--tau", type=float, default=4.0)
    p.add_argument("--student-lr", type=float, default=0.01)
    p.add_argument("--probe-size", type=int, default=None,
                   help="Labelled-probe size P (default: backbone-specific).")
    p.add_argument("--case", type=str, default="v1_he-ifd_mlp_mnist_verify",
                   help="Case slug -> results/<case>/.")
    p.add_argument("--results-root", type=str, default="results")
    p.add_argument("--data-root", type=str, default="data")
    p.add_argument("--cache-root", type=str, default="cache")
    # chunking
    p.add_argument("--num-chunks", type=int,
                   default=int(os.environ.get("NUM_CHUNKS", "1")),
                   help="Split the grid into this many contiguous chunks.")
    p.add_argument("--chunk-index", type=int,
                   default=int(os.environ.get("CHUNK_INDEX", "0")),
                   help="Which chunk (0-based) this job runs.")
    p.add_argument("--force", action="store_true",
                   help="Recompute even if a cell JSON already exists.")
    return p.parse_args()


def build_grid(args) -> List[Dict]:
    """Deterministically-ordered list of cell descriptors (the sweep order)."""
    grid: List[Dict] = []
    for backbone in parse_str_list(args.backbones):
        for N in parse_int_list(args.Ns):
            for alpha in parse_float_list(args.alphas):
                for method in parse_str_list(args.methods):
                    for seed in parse_int_list(args.seeds):
                        grid.append(cell_descriptor(backbone, N, alpha, method, seed, args.K))
    return grid


def select_chunk(grid: List[Dict], num_chunks: int, chunk_index: int) -> List[Dict]:
    """Return the contiguous chunk ``chunk_index`` of ``num_chunks`` (round-robin
    sizing so chunks differ by at most one cell)."""
    if num_chunks <= 1:
        return grid
    if not (0 <= chunk_index < num_chunks):
        raise ValueError(f"chunk_index {chunk_index} out of range [0,{num_chunks})")
    return [d for i, d in enumerate(grid) if i % num_chunks == chunk_index]


def main() -> None:
    args = parse_args()
    job_id = os.environ.get("SLURM_JOB_ID")
    node = os.environ.get("SLURMD_NODENAME") or os.environ.get("HOSTNAME")

    results_dir = Path(args.results_root) / args.case
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "runs").mkdir(exist_ok=True)

    grid = build_grid(args)
    my_cells = select_chunk(grid, args.num_chunks, args.chunk_index)
    print(f"[sweep] grid={len(grid)} cells; chunk {args.chunk_index}/{args.num_chunks} "
          f"-> {len(my_cells)} cells; case={args.case}", flush=True)

    n_run = n_skip = n_fail = 0
    for desc in my_cells:
        out_path = results_dir / cell_filename(desc)
        if out_path.exists() and not args.force:
            # Resume only past SUCCESSFUL cells; a prior FAIL (or corrupt JSON)
            # must be retried, not treated as done.
            prior_ok = False
            try:
                prior_ok = json.loads(out_path.read_text()).get("status") == "success"
            except (json.JSONDecodeError, OSError):
                prior_ok = False
            if prior_ok:
                n_skip += 1
                print(f"[sweep] skip  {out_path.name} (success exists)", flush=True)
                continue
            print(f"[sweep] retry {out_path.name} (prior status != success)", flush=True)
        print(f"[sweep] start {desc['backbone']} N={desc['N']} a={desc['alpha']} "
              f"{desc['method']} s={desc['seed']} K={desc['K']}", flush=True)
        res = run_cell(
            backbone=desc["backbone"], N=desc["N"], alpha=desc["alpha"],
            seed=desc["seed"], method=desc["method"], K=desc["K"], tau=args.tau,
            student_lr=args.student_lr, probe_size=args.probe_size,
            data_root=args.data_root, cache_root=args.cache_root,
            job_id=job_id, node=node,
        )
        write_cell_json(results_dir, res, desc)
        tag = "ok" if res.status == "success" else "FAIL"
        if res.status != "success":
            n_fail += 1
        else:
            n_run += 1
        acc = f"{res.acc:.4f}" if res.acc is not None else "n/a"
        mt = f"{res.mean_teacher:.4f}" if res.mean_teacher is not None else "n/a"
        print(f"[sweep] {tag}   {desc['method']} acc={acc} mean_teacher={mt} "
              f"wall={res.wall_clock_sec:.1f}s err={res.error}", flush=True)

    # Rebuild the case report from ALL per-cell JSONs in the dir (resumable-friendly).
    all_cells = load_cells(results_dir)
    write_report(results_dir=str(results_dir), cells=all_cells, args=vars(args))
    print(f"[sweep] done. ran={n_run} skipped={n_skip} failed={n_fail}. "
          f"report at {results_dir / 'README.md'}", flush=True)


if __name__ == "__main__":
    main()
