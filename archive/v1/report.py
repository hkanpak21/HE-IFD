"""Auto-write the experimental case README + results CSV.

Follows results_formatting.md (archive/2026-05-18_pre_v1/results_old/results_formatting.md):
    Folder per experimental case.
    README with 3-sentence explanation + auto-populated table.
    Sibling runs/ dir for stdout/stderr.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List

from .cell import CellResult


CASE_BLURB = (
    "HE-IFD v1 simulation (plaintext): clients locally distil from their "
    "teachers into a shared random init via KL with temperature, ship per-layer "
    "cumulative deltas, the server averages them linearly (FHE-compatible). "
    "Tests whether the protocol learns and whether accuracy scales with N. "
    "Architecture MLP 784->128->32->10 on MNIST, Dirichlet alpha=0.1 partition; "
    "no real FHE in v1 -- server-side operations are restricted to linear ops "
    "(addition + plaintext-scalar multiplication) so the simulation upper-bounds "
    "what the encrypted version produces. Default distillation set is the "
    "client's local data D_i only (no public probe); see `use_probe` flag."
)


def write_csv(path: Path, cells: List[CellResult]) -> None:
    fieldnames = [
        "method", "dataset", "N", "alpha", "seed", "K", "tau",
        "probe_size", "use_probe",
        "student_acc", "mean_teacher_acc", "best_teacher_acc", "worst_teacher_acc",
        "wall_clock_sec", "phase_teacher_sec", "phase_distill_sec",
        "phase_aggregate_sec", "phase_eval_sec",
        "job_id", "node", "status", "error",
    ]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for c in cells:
            row = {k: getattr(c, k, None) for k in fieldnames}
            w.writerow(row)


def write_partition_jsonl(path: Path, cells: List[CellResult]) -> None:
    with open(path, "w") as f:
        for c in cells:
            f.write(json.dumps({
                "N": c.N, "seed": c.seed,
                "per_client_total": c.per_client_total,
                "per_client_per_class": c.per_client_per_class,
            }) + "\n")


def render_table(cells: List[CellResult]) -> str:
    rows = [(c.N, c.seed, c.student_acc, c.mean_teacher_acc,
             c.best_teacher_acc, c.worst_teacher_acc,
             c.wall_clock_sec, c.status) for c in cells]
    rows.sort(key=lambda r: (r[0], r[1]))
    head = ("| N | seed | student_acc | mean_teacher_acc | best_teacher_acc | worst_teacher_acc | wall_clock (s) | status |\n"
            "|---|------|-------------|------------------|------------------|-------------------|----------------|--------|")
    body_lines = []
    for N, seed, sa, mt, bt, wt, wc, status in rows:
        sa_s = f"{sa:.4f}" if sa is not None else "n/a"
        mt_s = f"{mt:.4f}" if mt is not None else "n/a"
        bt_s = f"{bt:.4f}" if bt is not None else "n/a"
        wt_s = f"{wt:.4f}" if wt is not None else "n/a"
        body_lines.append(f"| {N} | {seed} | {sa_s} | {mt_s} | {bt_s} | {wt_s} | {wc:.1f} | {status} |")
    return head + "\n" + "\n".join(body_lines)


def write_report(results_dir: str, cells: List[CellResult], args: Dict) -> None:
    root = Path(results_dir)
    root.mkdir(parents=True, exist_ok=True)
    (root / "runs").mkdir(exist_ok=True)
    csv_path = root / "results.csv"
    partition_path = root / "partition_diagnostic.jsonl"
    readme_path = root / "README.md"

    write_csv(csv_path, cells)
    write_partition_jsonl(partition_path, cells)

    table = render_table(cells)
    config_block = (
        "## Sweep configuration\n\n"
        f"- N values swept: `{args.get('Ns')}`\n"
        f"- Seeds: `{args.get('seeds')}`\n"
        f"- Dirichlet alpha: `{args.get('alpha')}`\n"
        f"- K (client distill epochs): `{args.get('K')}`\n"
        f"- tau (distill temperature): `{args.get('tau')}`\n"
        f"- use_probe: `{args.get('use_probe')}`\n"
        f"- Probe size (only if use_probe): `{args.get('probe_size')}`\n"
        f"- Teacher epochs: `{args.get('teacher_epochs')}`\n"
    )

    readme_path.write_text(
        f"# v1 HE-IFD N-sweep — MNIST MLP\n\n"
        f"{CASE_BLURB}\n\n"
        f"{config_block}\n"
        f"## Results\n\n"
        f"{table}\n\n"
        f"Raw per-cell JSONs live in this directory as `cell_N<n>_s<seed>_<job_id>.json`.\n"
        f"Partition diagnostic (per-client per-class sample counts) at "
        f"`partition_diagnostic.jsonl`.\n"
        f"Slurm stdout/stderr at `runs/`.\n"
    )
