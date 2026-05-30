"""Issue 026 — task-arithmetic λ-scaling cheap verify (EVAL-ONLY, no retraining).

Our server op θ⋆ = θ₀ + Σ_j w_j·Δ_j IS task arithmetic (Ilharco et al. 2023) with
the scaling coefficient pinned to λ=1. The one optimization lever that fits
{one-shot, HE depth-1} and that we have never tested is λ in

    θ⋆(λ) = θ₀ + λ·Σ_j w_j·Δ_j = (1−λ)·θ₀ + λ·θ⋆(1).

So sweeping λ slides along the line between the basin θ₀ (λ=0) and the current
aggregate θ⋆(1) (λ=1). Because it is a pure interpolation over the SAME one-shot
{Δ_j}, the whole curve is EVAL-ONLY: one bounded distillation trajectory per cell,
then one cheap ``aggregate`` reweight (a public-scalar multiply — still depth-1
under CKKS) + one test eval per λ. No per-λ retraining.

This harness REUSES ``protocol.run_cell`` (it does NOT duplicate the pipeline
setup): it calls ``run_cell(..., lambda_scales=<list>)``, which fills the new
opt-in ``CellResult.lambda_curve`` field with the acc-vs-λ curve, writes a per-cell
JSON next to it (sweep filename/hash conventions, so cells are resumable and
distinct), and refreshes a focused case README summarising per cell:
the acc-vs-λ curve, the argmax λ⋆, acc(λ⋆) − acc(λ=1), and standalone θ₀ acc
(= the λ=0 point).

Like the rest of ``src``, all torch / pipeline imports are LAZY (inside
``run_cell``); this module is import-safe under ``ast.parse`` on the login node.

Usage (the issue-026 verify cells):
    python -m src.lambda_verify \
        --backbones mlp_mnist,vit_b32_cifar100 \
        --Ns 10 --alphas 0.05,1.0 --methods raw_union_K20 --seeds 42 --K 300 \
        --lambda-scales 0,0.25,0.5,0.75,1.0,1.25,1.5,1.75,2.0 \
        --case heifd_026_lambda_verify
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from .protocol import BACKBONES, CellResult, run_cell
from .sweep import (
    cell_descriptor,
    cell_filename,
    parse_float_list,
    parse_int_list,
    parse_str_list,
    write_cell_json,
)


# Default λ grid for the cheap verify (issue 026): 0 (standalone θ₀) … 2.0,
# straddling λ=1 so a peak at λ<1 (basin deserves more trust) or λ>1 (push harder
# along the trajectory) is both reachable.
_DEFAULT_LAMBDAS = "0,0.25,0.5,0.75,1.0,1.25,1.5,1.75,2.0"


# ---------------------------------------------------------------------------
# λ-curve descriptor / filename: the SAME deterministic stem+hash as a normal
# sweep cell (so the {backbone,N,α,method,seed,K,tau,lr,scope} dims resume the
# same way), with the λ grid folded into the descriptor so a λ-verify cell never
# collides with a plain sweep cell of the same protocol point.
# ---------------------------------------------------------------------------
def lambda_cell_descriptor(backbone: str, N: int, alpha: float, method: str,
                           seed: int, K: int, lambdas: List[float]) -> Dict:
    desc = cell_descriptor(backbone, N, alpha, method, seed, K)
    desc["lambda_scales"] = [float(x) for x in lambdas]
    return desc


def _summarise_curve(curve: Optional[List[Dict]]) -> Dict:
    """argmax λ⋆, acc(λ⋆), acc(λ=1), lift = acc(λ⋆)−acc(λ=1), and θ₀ acc (λ=0)."""
    if not curve:
        return {"lambda_star": None, "acc_star": None, "acc_lam1": None,
                "lift_over_lam1": None, "theta0_acc_lam0": None}
    best = max(curve, key=lambda p: (p["acc"] if p["acc"] is not None else -1.0))
    acc_lam1 = next((p["acc"] for p in curve if abs(p["lambda"] - 1.0) < 1e-12), None)
    acc_lam0 = next((p["acc"] for p in curve if abs(p["lambda"] - 0.0) < 1e-12), None)
    lift = (best["acc"] - acc_lam1) if (best["acc"] is not None
                                        and acc_lam1 is not None) else None
    return {"lambda_star": best["lambda"], "acc_star": best["acc"],
            "acc_lam1": acc_lam1, "lift_over_lam1": lift,
            "theta0_acc_lam0": acc_lam0}


def _fmt(x, nd: int = 4) -> str:
    return f"{x:.{nd}f}" if isinstance(x, (int, float)) else "n/a"


def write_lambda_report(results_dir: Path, cells: List[CellResult],
                        lambdas: List[float], args: Dict) -> None:
    """Focused README: per-cell acc-vs-λ curve + λ⋆ + lift over λ=1 + θ₀ (λ=0)."""
    case = results_dir.name
    lam_header = " | ".join(f"λ={lam:g}" for lam in lambdas)
    lam_sep = "|".join(["---"] * len(lambdas))
    head = (f"| backbone | N | α | method | seed | {lam_header} | "
            f"λ⋆ | acc(λ⋆) | acc(λ=1) | lift(λ⋆−1) | θ₀(λ=0) | status |\n"
            f"|---|---|---|--------|------|{lam_sep}|---|--------|---------|"
            f"-----------|---------|--------|")
    rows: List[str] = []
    for c in sorted(cells, key=lambda c: (str(c.backbone), c.N, c.alpha,
                                          str(c.method), c.seed)):
        s = _summarise_curve(c.lambda_curve)
        # Map λ -> acc for the per-λ columns (in the requested λ order).
        lam2acc = {round(p["lambda"], 6): p["acc"]
                   for p in (c.lambda_curve or [])}
        cells_acc = " | ".join(_fmt(lam2acc.get(round(lam, 6))) for lam in lambdas)
        lam_star = f"{s['lambda_star']:g}" if s["lambda_star"] is not None else "n/a"
        rows.append(
            f"| {c.backbone} | {c.N} | {c.alpha} | {c.method} | {c.seed} | "
            f"{cells_acc} | {lam_star} | {_fmt(s['acc_star'])} | "
            f"{_fmt(s['acc_lam1'])} | {_fmt(s['lift_over_lam1'])} | "
            f"{_fmt(s['theta0_acc_lam0'])} | {c.status} |")
    table = head + "\n" + ("\n".join(rows) if rows else "| _(no cells yet)_ |")

    blurb = (
        "Issue 026 — task-arithmetic scaling coefficient λ, cheap EVAL-ONLY verify.\n\n"
        "Our server op θ⋆ = θ₀ + Σ_j w_j·Δ_j **is task arithmetic** (Ilharco et al. "
        "2023) with the scaling coefficient pinned to λ=1. This case sweeps λ in\n\n"
        "> θ⋆(λ) = θ₀ + λ·Σ_j w_j·Δ_j = (1−λ)·θ₀ + λ·θ⋆(1),\n\n"
        "which is a pure **interpolation** between the basin θ₀ (λ=0) and the current "
        "aggregate θ⋆(1) (λ=1). Sliding λ is therefore **eval-only** — one bounded "
        "distillation trajectory per cell, then one ``aggregate`` reweight (a public-"
        "scalar multiply → still depth-1 under CKKS) + one test eval per λ; **no "
        "per-λ retraining**. The question: does λ≠1 help in the shared-basin regime? "
        "A peak at **λ<1** ⇒ the basin deserves more trust (down-weight the "
        "displacement); **λ>1** ⇒ push harder along the trajectory; λ⋆≈1 with no lift "
        "⇒ λ=1 holds and no λ grid is warranted. The λ=0 column reproduces the "
        "standalone θ₀ accuracy; the λ=1 column reproduces the headline aggregate acc."
    )
    config_block = (
        "## Sweep configuration\n\n"
        f"- Backbones: `{args.get('backbones')}`\n"
        f"- N values: `{args.get('Ns')}`\n"
        f"- Dirichlet α: `{args.get('alphas')}`\n"
        f"- Methods (basin source): `{args.get('methods')}`\n"
        f"- Seeds: `{args.get('seeds')}`\n"
        f"- K (bounded trajectory length): `{args.get('K')}`\n"
        f"- λ grid (--lambda-scales): `{args.get('lambda_scales')}`\n"
    )
    (results_dir / "README.md").write_text(
        f"# {case}\n\n{blurb}\n\n{config_block}\n## Results\n\n{table}\n\n"
        f"Per-cell JSONs (with the full `lambda_curve`) live here as "
        f"`cell_*.json`. Slurm stdout/stderr at `runs/`.\n"
    )


def load_lambda_cells(results_dir: Path) -> List[CellResult]:
    """Reload every per-cell JSON into CellResult objects (for the report).

    Only fields the current CellResult schema defines are passed through, so a
    JSON carrying extra keys (e.g. ``_descriptor``) reloads cleanly and the new
    ``lambda_curve`` field is restored when present.
    """
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
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Issue 026 — task-arithmetic λ-scaling cheap verify "
                    "(eval-only interpolation θ⋆(λ)=(1−λ)θ₀+λθ⋆(1); no retraining).")
    p.add_argument("--backbones", type=str, default="mlp_mnist,vit_b32_cifar100",
                   help=f"Comma list from {sorted(BACKBONES)}.")
    p.add_argument("--Ns", type=str, default="10", help="Client counts, e.g. 10.")
    p.add_argument("--alphas", type=str, default="0.05,1.0",
                   help="Dirichlet alphas, e.g. 0.05,1.0.")
    p.add_argument("--methods", type=str, default="raw_union_K20",
                   help="Basin source method(s), e.g. raw_union_K20.")
    p.add_argument("--seeds", type=str, default="42", help="Seeds, e.g. 42.")
    p.add_argument("--K", type=int, default=300,
                   help="Bounded distillation trajectory length.")
    p.add_argument("--lambda-scales", type=str, default=_DEFAULT_LAMBDAS,
                   help="Comma list of λ values to evaluate (eval-only), e.g. "
                        f"'{_DEFAULT_LAMBDAS}'. λ=0 is standalone θ₀; λ=1 is the "
                        "current aggregate; the curve interpolates between them.")
    p.add_argument("--probe-size", type=int, default=None,
                   help="Labelled-probe size P (default: backbone-specific).")
    p.add_argument("--case", type=str, default="heifd_026_lambda_verify",
                   help="Case slug -> results/<case>/.")
    p.add_argument("--results-root", type=str, default="results")
    p.add_argument("--data-root", type=str, default="data")
    p.add_argument("--cache-root", type=str, default="cache")
    p.add_argument("--force", action="store_true",
                   help="Recompute even if a cell JSON already exists.")
    return p.parse_args()


def build_grid(args, lambdas: List[float]) -> List[Dict]:
    """Deterministically-ordered λ-verify cell descriptors (backbone × N × α ×
    method × seed; single K; the λ grid is a per-cell list folded into each
    descriptor, NOT a grid axis — every cell evaluates the whole λ curve)."""
    grid: List[Dict] = []
    for backbone in parse_str_list(args.backbones):
        for N in parse_int_list(args.Ns):
            for alpha in parse_float_list(args.alphas):
                for method in parse_str_list(args.methods):
                    for seed in parse_int_list(args.seeds):
                        grid.append(lambda_cell_descriptor(
                            backbone, N, alpha, method, seed, args.K, lambdas))
    return grid


def main() -> None:
    args = parse_args()
    job_id = os.environ.get("SLURM_JOB_ID")
    node = os.environ.get("SLURMD_NODENAME") or os.environ.get("HOSTNAME")

    lambdas = parse_float_list(args.lambda_scales)
    results_dir = Path(args.results_root) / args.case
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "runs").mkdir(exist_ok=True)

    grid = build_grid(args, lambdas)
    print(f"[lambda_verify] {len(grid)} cells; λ grid={lambdas}; case={args.case}",
          flush=True)

    n_run = n_skip = n_fail = 0
    for desc in grid:
        out_path = results_dir / cell_filename(desc)
        if out_path.exists() and not args.force:
            prior_ok = False
            try:
                prior_ok = json.loads(out_path.read_text()).get("status") == "success"
            except (json.JSONDecodeError, OSError):
                prior_ok = False
            if prior_ok:
                n_skip += 1
                print(f"[lambda_verify] skip  {out_path.name} (success exists)",
                      flush=True)
                continue
            print(f"[lambda_verify] retry {out_path.name} (prior status != success)",
                  flush=True)
        print(f"[lambda_verify] start {desc['backbone']} N={desc['N']} "
              f"a={desc['alpha']} {desc['method']} s={desc['seed']} K={desc['K']}",
              flush=True)
        res = run_cell(
            backbone=desc["backbone"], N=desc["N"], alpha=desc["alpha"],
            seed=desc["seed"], method=desc["method"], K=desc["K"],
            probe_size=args.probe_size, data_root=args.data_root,
            cache_root=args.cache_root, job_id=job_id, node=node,
            lambda_scales=lambdas,
        )
        write_cell_json(results_dir, res, desc)
        tag = "ok" if res.status == "success" else "FAIL"
        if res.status != "success":
            n_fail += 1
        else:
            n_run += 1
        s = _summarise_curve(res.lambda_curve)
        lam_star = f"{s['lambda_star']:g}" if s["lambda_star"] is not None else "n/a"
        print(f"[lambda_verify] {tag}   {desc['method']} acc(λ=1)={_fmt(s['acc_lam1'])}"
              f" λ⋆={lam_star} acc(λ⋆)={_fmt(s['acc_star'])} "
              f"lift={_fmt(s['lift_over_lam1'])} θ₀(λ=0)={_fmt(s['theta0_acc_lam0'])} "
              f"wall={res.wall_clock_sec:.1f}s err={res.error}", flush=True)

    all_cells = load_lambda_cells(results_dir)
    write_lambda_report(results_dir, all_cells, lambdas, vars(args))
    print(f"[lambda_verify] done. ran={n_run} skipped={n_skip} failed={n_fail}. "
          f"report at {results_dir / 'README.md'}", flush=True)


if __name__ == "__main__":
    main()
