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
# Historical defaults (frozen): the values used by every cell written before the
# tau/LR sweep extension landed. Including tau/LR in the descriptor ONLY when
# they differ from these legacy defaults preserves backwards-compatibility with
# existing cell_*.json filenames (so existing case dirs still resume correctly).
_LEGACY_TAU = 4.0
_LEGACY_STUDENT_LR = 0.01
# Trainable-scope (issue 011) — ``head_only`` is the pre-issue-011 default for
# every backbone, so omitting it from the descriptor keeps existing per-cell
# JSON hashes/filenames identical (resumable across the issue 011 extension).
_LEGACY_TRAINABLE_SCOPE = "head_only"
# Server-combine selector (issue 025) — ``weight_avg`` is the pre-025 linear
# aggregate, so omitting it from the descriptor keeps existing per-cell JSON
# hashes/filenames identical (resumable across the issue 025 non-linear axis).
_LEGACY_AGG_METHOD = "weight_avg"
# Client-side optimizer (TIER-1 aggregation study, Axis A) — ``sgd`` is the
# pre-axis trajectory optimizer, so omitting it from the descriptor keeps every
# existing per-cell JSON hash/filename identical (resumable across this axis).
_LEGACY_OPTIMIZER = "sgd"
# Local-step axis (issue ft01) — the pre-ft01 local step was teacher→student
# distillation, so the LEGACY value is ``distill``; omitting it from the
# descriptor when it equals ``distill`` keeps every existing per-cell JSON
# hash/filename identical (resumable across the ft01 fine-tuning pivot). The
# new headline ``finetune`` flows into the descriptor and gets a distinct stem.
_LEGACY_LOCAL_STEP = "distill"
# Trainable-unit axis (issue ft01) — the pre-ft01 trainable unit was the linear
# ``head`` (== the issue-011 ``head_only`` scope), so the LEGACY value is
# ``head``; omitting it when it equals ``head`` keeps existing per-cell JSON
# hashes/filenames identical (resumable across the ft01 trainable-unit axis).
_LEGACY_TRAINABLE_UNIT = "head"


def cell_descriptor(backbone: str, N: int, alpha: float, method: str,
                    seed: int, K: int,
                    tau: float = _LEGACY_TAU,
                    student_lr: float = _LEGACY_STUDENT_LR,
                    trainable_scope: str = _LEGACY_TRAINABLE_SCOPE,
                    agg_method: str = _LEGACY_AGG_METHOD,
                    optimizer: str = _LEGACY_OPTIMIZER,
                    local_step: str = _LEGACY_LOCAL_STEP,
                    trainable_unit: str = _LEGACY_TRAINABLE_UNIT) -> Dict:
    """Deterministic cell descriptor. ``tau`` / ``student_lr`` /
    ``trainable_scope`` / ``agg_method`` / ``optimizer`` / ``local_step`` /
    ``trainable_unit`` are appended ONLY when they differ from the historical
    defaults so existing per-cell filenames (which hashed only over
    {backbone,N,alpha,method,seed,K}) keep their hashes and remain resumable
    across the issue 010 (tau/LR), issue 011 (scope), issue 025 (agg_method),
    TIER-1 Axis-A (optimizer), and issue ft01 (local_step + trainable_unit)
    extensions. ft01's legacy values are ``distill`` + ``head`` (the pre-pivot
    behaviour), so pre-ft01 cells keep their stems/hashes."""
    desc: Dict = {"backbone": backbone, "N": N, "alpha": alpha,
                  "method": method, "seed": seed, "K": K}
    if tau != _LEGACY_TAU:
        desc["tau"] = tau
    if student_lr != _LEGACY_STUDENT_LR:
        desc["student_lr"] = student_lr
    if trainable_scope != _LEGACY_TRAINABLE_SCOPE:
        desc["trainable_scope"] = trainable_scope
    if agg_method != _LEGACY_AGG_METHOD:
        desc["agg_method"] = agg_method
    if optimizer != _LEGACY_OPTIMIZER:
        desc["optimizer"] = optimizer
    if local_step != _LEGACY_LOCAL_STEP:
        desc["local_step"] = local_step
    if trainable_unit != _LEGACY_TRAINABLE_UNIT:
        desc["trainable_unit"] = trainable_unit
    return desc


def descriptor_hash(desc: Dict) -> str:
    canon = json.dumps(desc, sort_keys=True, default=str)
    return hashlib.sha256(canon.encode()).hexdigest()[:12]


def cell_filename(desc: Dict) -> str:
    # Filename stem reflects only the dimensions the descriptor records, so
    # legacy (tau=4.0, lr=0.01, scope=head_only) cells keep their original
    # stems and the new non-default tau/LR/scope cells get distinct,
    # self-describing stems.
    stem = (f"cell_{desc['backbone']}_N{desc['N']}_a{desc['alpha']}"
            f"_{desc['method']}_s{desc['seed']}_K{desc['K']}")
    if "tau" in desc:
        stem += f"_t{desc['tau']}"
    if "student_lr" in desc:
        stem += f"_lr{desc['student_lr']}"
    if "trainable_scope" in desc:
        stem += f"_sc{desc['trainable_scope']}"
    if "agg_method" in desc:
        stem += f"_agg{desc['agg_method']}"
    if "optimizer" in desc:
        stem += f"_opt{desc['optimizer']}"
    if "local_step" in desc:
        stem += f"_ls{desc['local_step']}"
    if "trainable_unit" in desc:
        stem += f"_tu{desc['trainable_unit']}"
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
                   help="Bounded distillation trajectory length (single value).")
    p.add_argument("--Ks", type=str, default=None,
                   help="Optional comma list of K values to sweep, e.g. 30,100,300,1000. "
                        "When set, overrides --K and adds K as a grid axis.")
    p.add_argument("--tau", type=float, default=4.0,
                   help="KD softmax temperature (single value).")
    p.add_argument("--taus", type=str, default=None,
                   help="Optional comma list of τ values to sweep, e.g. 1,4. When set, "
                        "overrides --tau and adds τ as a grid axis.")
    p.add_argument("--student-lr", type=float, default=0.01,
                   help="Student SGD learning rate (single value).")
    p.add_argument("--student-lrs", type=str, default=None,
                   help="Optional comma list of student LRs to sweep, e.g. 0.001,0.01. "
                        "When set, overrides --student-lr and adds LR as a grid axis.")
    p.add_argument("--scope", type=str, default="head_only",
                   help="Trainable-layer scope (single value) per issue 011: "
                        "'head_only' (default; legacy linear head), 'lora_<rank>' "
                        "(rank-r LoRA on the head, e.g. lora_8), 'last_block' / "
                        "'last_n_blocks_<n>' (MLP-on-cached-features). Only the "
                        "'head' backbones (resnet18 / vit_b32 / distilbert / "
                        "gpt2) accept non-default scopes; from-scratch backbones "
                        "raise NotImplementedError for non-'head_only'.")
    p.add_argument("--scopes", type=str, default=None,
                   help="Optional comma list of scope tokens to sweep, e.g. "
                        "head_only,lora_8,last_block. When set, overrides "
                        "--scope and adds scope as a grid axis (the issue 011 "
                        "focused comparison).")
    p.add_argument("--agg-methods", type=str, default="weight_avg",
                   help="Server-combine selector axis (issue 025). Comma list "
                        "from weight_avg (default; the linear production "
                        "aggregate), mag_weighted, sign_majority, "
                        "agreement_gated, norm_normalized, second_moment, "
                        "coord_median, coord_trimmed_mean, consensus_proj, "
                        "poly_gate_d2_a, poly_gate_d2_b (see "
                        "aggregate.NONLINEAR_DEPTH). Each value is an extra grid "
                        "axis; weight_avg keeps the byte-identical linear path "
                        "and its cells reuse the legacy filename/hash.")
    p.add_argument("--optimizer", type=str, default="sgd",
                   help="Client-side distillation optimizer (single value; "
                        "TIER-1 Axis A). One of sgd (default; the legacy SGD "
                        "trajectory), sgd_momentum, nesterov, adam, adamw, "
                        "rmsprop, adagrad, lamb. 'sgd' keeps the byte-identical "
                        "trajectory and its cells reuse the legacy "
                        "filename/hash.")
    p.add_argument("--optimizers", type=str, default=None,
                   help="Optional comma list of client optimizers to sweep, e.g. "
                        "sgd,adam,lamb. When set, overrides --optimizer and adds "
                        "the optimizer as a grid axis (TIER-1 Axis A).")
    p.add_argument("--local-step", type=str, default="distill",
                   help="Client-side local step (single value; issue ft01). "
                        "'distill' (default; the legacy teacher→student KL "
                        "trajectory — byte-identical, reuses the legacy "
                        "filename/hash) or 'finetune' (the headline: DIRECT "
                        "supervised fine-tuning, cross-entropy on local hard "
                        "labels). NOTE: defaults to 'distill' here so existing "
                        "sweeps reproduce byte-for-byte; the run_cell default is "
                        "'finetune' (the new headline for notebooks).")
    p.add_argument("--local-steps", type=str, default=None,
                   help="Optional comma list of local steps to sweep, e.g. "
                        "finetune,distill. When set, overrides --local-step and "
                        "adds the local step as a grid axis (issue ft01).")
    p.add_argument("--trainable-unit", type=str, default="head",
                   help="Trainable unit (single value; issue ft01). 'head' "
                        "(default; linear probe == legacy head_only — "
                        "byte-identical, reuses the legacy filename/hash), 'lora' "
                        "(LoRA adapter + head — the headline; 'lora_<rank>' for "
                        "an explicit rank), or 'last_n' / 'last_n_<n>' (last-N "
                        "blocks as an MLP-on-cached-features head). Resolves to "
                        "an issue-011 trainable_scope so the displacement flows "
                        "through the UNCHANGED depth-1 aggregate.")
    p.add_argument("--trainable-units", type=str, default=None,
                   help="Optional comma list of trainable units to sweep, e.g. "
                        "head,lora,last_n (the ft07 trainable-unit comparison). "
                        "When set, overrides --trainable-unit and adds the unit "
                        "as a grid axis (issue ft01).")
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
    """Deterministically-ordered list of cell descriptors (the sweep order).

    The default sweep is the historical 6-axis grid (backbone × N × α × method ×
    seed × K with a single K). When ``--Ks`` / ``--taus`` / ``--student-lrs`` /
    ``--scopes`` / ``--agg-methods`` / ``--optimizers`` / ``--local-steps`` /
    ``--trainable-units`` are provided, those become additional grid axes
    (single-value flags ``--K`` / ``--tau`` / ``--student-lr`` / ``--scope`` /
    ``--optimizer`` / ``--local-step`` / ``--trainable-unit`` are ignored for
    that axis). Non-default (tau, student_lr, trainable_scope, agg_method,
    optimizer, local_step, trainable_unit) values flow into the descriptor so
    cell filenames stay distinct — see ``cell_descriptor`` for the
    backwards-compat rule (``agg_method`` defaults to ``weight_avg``, ``optimizer``
    to ``sgd``, ``local_step`` to ``distill``, ``trainable_unit`` to ``head``, and
    each is omitted from the descriptor at its legacy value so those legacy cells
    keep their filename/hash and resume).
    """
    Ks = parse_int_list(args.Ks) if args.Ks else [args.K]
    taus = parse_float_list(args.taus) if args.taus else [args.tau]
    lrs = parse_float_list(args.student_lrs) if args.student_lrs else [args.student_lr]
    scopes = parse_str_list(args.scopes) if args.scopes else [args.scope]
    agg_methods = parse_str_list(args.agg_methods) if args.agg_methods else [_LEGACY_AGG_METHOD]
    optimizers = parse_str_list(args.optimizers) if args.optimizers else [args.optimizer]
    local_steps = parse_str_list(args.local_steps) if args.local_steps else [args.local_step]
    trainable_units = (
        parse_str_list(args.trainable_units) if args.trainable_units
        else [args.trainable_unit])
    grid: List[Dict] = []
    for backbone in parse_str_list(args.backbones):
        for N in parse_int_list(args.Ns):
            for alpha in parse_float_list(args.alphas):
                for method in parse_str_list(args.methods):
                    for seed in parse_int_list(args.seeds):
                        for K in Ks:
                            for tau in taus:
                                for student_lr in lrs:
                                    for scope in scopes:
                                        for agg_method in agg_methods:
                                            for optimizer in optimizers:
                                                for local_step in local_steps:
                                                    for trainable_unit in trainable_units:
                                                        grid.append(cell_descriptor(
                                                            backbone, N, alpha, method, seed, K,
                                                            tau=tau, student_lr=student_lr,
                                                            trainable_scope=scope,
                                                            agg_method=agg_method,
                                                            optimizer=optimizer,
                                                            local_step=local_step,
                                                            trainable_unit=trainable_unit))
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
        # Per-cell tau/LR/scope come from the descriptor when the multi-flag
        # sweep is in use; otherwise fall back to the single-value CLI flags
        # (the legacy contract — every cell shares one tau / LR / scope).
        cell_tau = desc.get("tau", args.tau)
        cell_lr = desc.get("student_lr", args.student_lr)
        cell_scope = desc.get("trainable_scope", args.scope)
        cell_agg = desc.get("agg_method", _LEGACY_AGG_METHOD)
        cell_optimizer = desc.get("optimizer", args.optimizer)
        cell_local_step = desc.get("local_step", _LEGACY_LOCAL_STEP)
        cell_trainable_unit = desc.get("trainable_unit", _LEGACY_TRAINABLE_UNIT)
        print(f"[sweep] start {desc['backbone']} N={desc['N']} a={desc['alpha']} "
              f"{desc['method']} s={desc['seed']} K={desc['K']} "
              f"tau={cell_tau} lr={cell_lr} scope={cell_scope} agg={cell_agg} "
              f"opt={cell_optimizer} ls={cell_local_step} tu={cell_trainable_unit}",
              flush=True)
        res = run_cell(
            backbone=desc["backbone"], N=desc["N"], alpha=desc["alpha"],
            seed=desc["seed"], method=desc["method"], K=desc["K"], tau=cell_tau,
            student_lr=cell_lr, probe_size=args.probe_size,
            data_root=args.data_root, cache_root=args.cache_root,
            job_id=job_id, node=node,
            trainable_scope=cell_scope,
            agg_method=cell_agg,
            optimizer=cell_optimizer,
            local_step=cell_local_step,
            trainable_unit=cell_trainable_unit,
        )
        write_cell_json(results_dir, res, desc)
        tag = "ok" if res.status == "success" else "FAIL"
        if res.status != "success":
            n_fail += 1
        else:
            n_run += 1
        acc = f"{res.acc:.4f}" if res.acc is not None else "n/a"
        mt = f"{res.mean_teacher:.4f}" if res.mean_teacher is not None else "n/a"
        print(f"[sweep] {tag}   {desc['method']} agg={res.agg_method}"
              f"({res.agg_depth}) opt={res.optimizer} acc={acc} mean_teacher={mt} "
              f"wall={res.wall_clock_sec:.1f}s err={res.error}", flush=True)

    # Rebuild the case report from ALL per-cell JSONs in the dir (resumable-friendly).
    all_cells = load_cells(results_dir)
    write_report(results_dir=str(results_dir), cells=all_cells, args=vars(args))
    print(f"[sweep] done. ran={n_run} skipped={n_skip} failed={n_fail}. "
          f"report at {results_dir / 'README.md'}", flush=True)


if __name__ == "__main__":
    main()
