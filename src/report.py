"""Auto-write the experimental case report: README + results.csv + partition jsonl.

Follows the ``results/<case>/`` convention (CLAUDE.md / the user's
results_formatting spec, also used by the archived ``src/v1`` reporter):

    results/<case>/
        README.md                    3-sentence description + auto-populated table
        results.csv                  one long-form row per cell
        partition_diagnostic.jsonl   per-client per-class counts, one line per cell
        cell_*.json                  per-cell results (written by sweep)
        runs/                        Slurm stdout/stderr

Pure-stdlib (csv/json) so it imports cleanly on the login node. The README table
leads with IID test accuracy (the headline metric) alongside the mean/best/oracle
teacher references and the realised σ for DP cells.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List

from .protocol import CellResult


CASE_BLURB = (
    "HE-IFD plaintext simulation of the one-shot federated distillation protocol: "
    "each client distils its own teacher into a student over a bounded K-step "
    "trajectory from a shared, Phase-0-aligned init θ₀, then uploads the cumulative "
    "trainable-parameter displacement Δ_i = θ_i^(K) − θ₀; the server's only operation "
    "is the sample-weighted linear combine θ₀ + Σ_i w_i·Δ_i (w_i = n_i/Σ_j n_j), which "
    "uses plaintext-scalar × ciphertext and ciphertext + ciphertext only and is thus "
    "FHE-compatible by construction (multiplicative depth ≈ 1). "
    "This case sweeps the grid below; IID test accuracy is the lead metric, with "
    "mean/best teacher and a centralised oracle as references."
)

CSV_FIELDS = [
    "backbone", "dataset", "N", "alpha", "seed", "K", "tau",
    "method", "phase0_kind", "probe_size_actual", "sigma",
    "acc", "mean_teacher", "best_teacher", "oracle",
    "wall_clock_sec", "phase_teacher_sec", "phase_phase0_sec",
    "phase_distill_sec", "phase_aggregate_sec", "phase_eval_sec",
    "job_id", "node", "status", "error",
]


def write_csv(path: Path, cells: List[CellResult]) -> None:
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        for c in cells:
            w.writerow({k: getattr(c, k, None) for k in CSV_FIELDS})


def write_partition_jsonl(path: Path, cells: List[CellResult]) -> None:
    with open(path, "w") as f:
        for c in cells:
            f.write(json.dumps({
                "backbone": c.backbone, "N": c.N, "alpha": c.alpha, "seed": c.seed,
                "per_client_total": c.per_client_total,
                "per_client_per_class": c.per_client_per_class,
                "sample_weights": c.sample_weights,
            }) + "\n")


def _fmt(x, nd: int = 4) -> str:
    return f"{x:.{nd}f}" if isinstance(x, (int, float)) and x is not None else "n/a"


def render_table(cells: List[CellResult]) -> str:
    rows = [
        (c.backbone, c.N, c.alpha, c.method, c.seed, c.acc,
         c.mean_teacher, c.best_teacher, c.oracle, c.sigma, c.status)
        for c in cells
    ]
    rows.sort(key=lambda r: (str(r[0]), r[1], r[2], str(r[3]), r[4]))
    head = ("| backbone | N | α | method | seed | acc | mean_teacher | best_teacher | oracle | σ | status |\n"
            "|---|---|---|--------|------|-----|--------------|--------------|--------|---|--------|")
    body = []
    for bb, N, a, m, s, acc, mt, bt, orc, sig, st in rows:
        body.append(
            f"| {bb} | {N} | {a} | {m} | {s} | {_fmt(acc)} | {_fmt(mt)} | "
            f"{_fmt(bt)} | {_fmt(orc)} | {_fmt(sig)} | {st} |")
    return head + "\n" + ("\n".join(body) if body else "| _(no cells yet)_ |")


def write_report(results_dir: str, cells: List[CellResult], args: Dict) -> None:
    root = Path(results_dir)
    root.mkdir(parents=True, exist_ok=True)
    (root / "runs").mkdir(exist_ok=True)

    write_csv(root / "results.csv", cells)
    write_partition_jsonl(root / "partition_diagnostic.jsonl", cells)

    config_block = (
        "## Sweep configuration\n\n"
        f"- Backbones: `{args.get('backbones')}`\n"
        f"- N values: `{args.get('Ns')}`\n"
        f"- Dirichlet α: `{args.get('alphas')}`\n"
        f"- Methods: `{args.get('methods')}`\n"
        f"- Seeds: `{args.get('seeds')}`\n"
        f"- K (bounded trajectory length): `{args.get('K')}`\n"
        f"- τ (distill temperature): `{args.get('tau')}`\n"
        f"- Student LR: `{args.get('student_lr')}`\n"
        f"- Labelled-probe size P: `{args.get('probe_size')}` "
        f"(None = backbone default)\n"
    )

    case = root.name
    (root / "README.md").write_text(
        f"# {case}\n\n"
        f"{CASE_BLURB}\n\n"
        f"{config_block}\n"
        f"## Results\n\n"
        f"{render_table(cells)}\n\n"
        f"Raw per-cell JSONs live here as `cell_<backbone>_N<n>_a<α>_<method>_s<seed>_K<k>_<hash>.json`.\n"
        f"Per-client per-class counts at `partition_diagnostic.jsonl`. "
        f"Slurm stdout/stderr at `runs/`. Long-form rows at `results.csv`.\n"
    )
