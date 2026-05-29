"""Results writer for ``results/heifd_021_mia/``.

Emits, in the repo's ``results/<case>/`` convention:

  results/heifd_021_mia/
    README.md                  description + auto-populated headline table
    summary.json               machine-readable summary the paper table reads
    cell_<...>.json            per-cell results (attacks × surfaces, full ROC)
    shadows/<cell>/...         shadow-model φ checkpoints (resume across jobs)
    runs/                      Slurm stdout/stderr

Pure stdlib (json/csv) so it imports cleanly on the login node.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


CASE_BLURB = (
    "Membership-inference study (issue 021) of the HE-IFD released global model "
    "θ⋆ and the Phase-0 prototype channel. Three attacks — Yeom et al. 2018 "
    "loss/confidence threshold, Carlini et al. 2022 LiRA (likelihood-ratio "
    "shadow-model attack), and Galichin et al. 2025 GLiRA (distillation-guided "
    "black-box LiRA) — are run across three adversary surfaces: external "
    "(black-box query on θ⋆), fellow-client (a participant with its own data + "
    "the shared Phase-0 prototypes as a stronger prior), and the prototype "
    "channel (membership inference directly on the per-class prototype release, "
    "at raw and ε∈{2,8}). Scored by TPR@0.1%FPR and ROC/AUC. Reuses src/ to "
    "build every target and shadow model — the protocol is NOT reimplemented. "
    "Expected: HE-IFD released-model leakage ≤ a matched DP one-shot baseline "
    "(DP perturbs the released model; HE-IFD does not), and the prototype-"
    "channel AUC/TPR collapses toward chance as ε tightens, validating the "
    "averaging-variant DP accounting."
)


def cell_slug(backbone: str, N: int, alpha: float, method: str) -> str:
    return f"{backbone}_N{N}_a{alpha}_{method}"


def cell_json_path(results_dir: Path, slug: str, seed: int) -> Path:
    return results_dir / f"cell_{slug}_s{seed}.json"


def write_cell(results_dir: Path, slug: str, seed: int, payload: Dict) -> Path:
    results_dir.mkdir(parents=True, exist_ok=True)
    p = cell_json_path(results_dir, slug, seed)
    p.write_text(json.dumps(payload, indent=2))
    return p


def load_cells(results_dir: Path) -> List[Dict]:
    cells = []
    for p in sorted(results_dir.glob("cell_*.json")):
        try:
            cells.append(json.loads(p.read_text()))
        except (json.JSONDecodeError, OSError):
            continue
    return cells


def _fmt(x, nd: int = 4) -> str:
    return f"{x:.{nd}f}" if isinstance(x, (int, float)) else "n/a"


def _get(d: Dict, *keys, default=None):
    for k in keys:
        if not isinstance(d, dict) or k not in d:
            return default
        d = d[k]
    return d


def render_table(cells: List[Dict]) -> str:
    """Headline table: one row per (cell, surface, attack) with TPR@0.1%FPR + AUC."""
    head = ("| backbone | N | α | method | seed | surface | attack | "
            "TPR@0.1%FPR | TPR@1%FPR | AUC |\n"
            "|---|---|---|--------|------|---------|--------|-------------|"
            "-----------|-----|")
    body = []
    for c in cells:
        bb, N, a = c.get("backbone"), c.get("N"), c.get("alpha")
        meth, seed = c.get("method"), c.get("seed")
        for surface, sres in c.get("surfaces", {}).items():
            for attack, ares in sres.items():
                if not isinstance(ares, dict):
                    continue
                # prototype surface nests by eps; flatten one level
                if attack in ("raw",) or attack.startswith("eps"):
                    label = f"prototype/{attack}"
                    t01 = ares.get("tpr_at_fpr_0.001")
                    t1 = ares.get("tpr_at_fpr_0.01")
                    auc = ares.get("auc")
                    body.append(
                        f"| {bb} | {N} | {a} | {meth} | {seed} | {surface} | "
                        f"{label} | {_fmt(t01)} | {_fmt(t1)} | {_fmt(auc)} |")
                else:
                    t01 = ares.get("tpr_at_fpr_0.001")
                    t1 = ares.get("tpr_at_fpr_0.01")
                    auc = ares.get("auc")
                    body.append(
                        f"| {bb} | {N} | {a} | {meth} | {seed} | {surface} | "
                        f"{attack} | {_fmt(t01)} | {_fmt(t1)} | {_fmt(auc)} |")
    return head + "\n" + ("\n".join(body) if body else "| _(no cells yet)_ |")


def build_summary(cells: List[Dict]) -> Dict:
    """Compact, machine-readable summary the paper §VI table reads.

    Flattens to a list of records: (backbone, N, alpha, method, seed, surface,
    attack, tpr@0.1%, tpr@1%, tpr@10%, auc). The prototype surface contributes
    one record per ε. ROC arrays are NOT included here (they live in the per-cell
    JSON) so summary.json stays small.
    """
    records = []
    for c in cells:
        base = {k: c.get(k) for k in ("backbone", "N", "alpha", "method", "seed")}
        for surface, sres in c.get("surfaces", {}).items():
            for attack, ares in sres.items():
                if not isinstance(ares, dict) or "auc" not in ares:
                    continue
                records.append({
                    **base, "surface": surface, "attack": attack,
                    "tpr_at_fpr_0.001": ares.get("tpr_at_fpr_0.001"),
                    "tpr_at_fpr_0.01": ares.get("tpr_at_fpr_0.01"),
                    "tpr_at_fpr_0.1": ares.get("tpr_at_fpr_0.1"),
                    "auc": ares.get("auc"),
                    "sigma": ares.get("sigma"),
                    "n_members": ares.get("n_members"),
                })
    return {"n_cells": len(cells), "records": records}


def write_report(results_dir: str) -> None:
    root = Path(results_dir)
    root.mkdir(parents=True, exist_ok=True)
    (root / "runs").mkdir(exist_ok=True)
    cells = load_cells(root)

    summary = build_summary(cells)
    (root / "summary.json").write_text(json.dumps(summary, indent=2))

    case = root.name
    (root / "README.md").write_text(
        f"# {case}\n\n"
        f"{CASE_BLURB}\n\n"
        f"## Results (TPR at fixed FPR + AUC)\n\n"
        f"{render_table(cells)}\n\n"
        f"`summary.json` holds the same numbers as flat records for the paper "
        f"table. Full ROC arrays (`roc_fpr` / `roc_tpr`) for log-log plots live "
        f"in each `cell_*.json` under `surfaces.<surface>.<attack>`. Shadow-model "
        f"φ checkpoints (resume support) are under `shadows/<cell>/`. Slurm logs "
        f"under `runs/`.\n\n"
        f"### Reading the table\n\n"
        f"- **external / lira / glira / threshold** — leakage of θ⋆ to a "
        f"black-box adversary. GLiRA is the query-only fit; LiRA here reads θ⋆'s "
        f"own confidences (an upper reading); threshold is the Yeom floor.\n"
        f"- **fellow** — the same, for a participant with auxiliary data + "
        f"prototypes (a stronger prior; expect ≥ external).\n"
        f"- **prototype/raw vs prototype/eps8 vs prototype/eps2** — leakage of "
        f"the Phase-0 prototype channel; AUC/TPR should fall toward chance "
        f"(AUC→0.5, TPR@0.1%FPR→0.001) as ε tightens.\n"
    )
