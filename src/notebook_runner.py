"""Start-once, run-to-completion unattended sweep driver (issue ft03).

The operational backbone of the fine-tuning pivot. A researcher fills in ONE
configuration cell in ``notebooks/template_finetune_sweep.ipynb``, presses
"Confirm config" (which freezes every choice into a plain ``dict``), then calls
``run_unattended(config)`` and walks away. From that point there is **zero
interaction**: the function builds the full Cartesian cell grid, runs each cell,
and returns a summary when the whole grid is done.

It deliberately reuses the existing, unchanged building blocks:

* ``protocol.run_cell``     — runs ONE (backbone, N, α, method, seed, K, …) cell;
                              already catches its own internal exceptions and
                              returns a ``CellResult`` with ``status="FAIL"``.
* ``sweep.cell_descriptor`` / ``sweep.cell_filename`` / ``sweep.write_cell_json``
  / ``sweep.load_cells``    — the SAME deterministic descriptor → filename map the
                              sbatch sweep uses, so a run started here is
                              resume-compatible with one started by ``sweep.py``
                              and vice-versa (identical ``cell_*.json`` names).
* ``report.write_report``   — the SAME ``results/<case>/`` README + results.csv +
                              partition jsonl writer.

The four unattended-survival properties (all required by ft03):

1. **Resume.** Before running a cell, if its ``cell_*.json`` already exists AND
   records ``status == "success"``, the cell is skipped. A VM restart mid-grid
   therefore continues instead of recomputing — identical to ``sweep.py``'s rule.
2. **Error tolerance.** ``run_cell`` already returns a FAIL result for an internal
   error, but we ALSO wrap every call in try/except so that an exception which
   escapes ``run_cell`` entirely (OOM teardown, a per-cell *timeout*, or an
   intentionally-injected failing cell) is caught, logged to ``failures.jsonl``,
   and the loop **continues to the next cell** — one bad cell never aborts the
   night.
3. **Heartbeat.** Exactly one line is printed per cell — ``[k/total] <case> … ok``
   / ``FAIL`` / ``skip`` — so a researcher checking in sees forward progress.
4. **Periodic flush + final summary.** Every ``flush_every`` cells (and once at
   the end) the combined ``results.csv`` + README are rebuilt from ALL per-cell
   JSONs, so partial results are visible mid-run; a final summary dict (cells
   done / failed / skipped, wall-clock, output dir) is printed and returned.

Determinism: cell identity is a pure function of the descriptor (no wall-clock /
``Date.now`` in the key), seeds come from the config, and a hard per-cell timeout
keeps a single hung cell from stalling the whole run.

Nothing in ``aggregate`` / ``distill`` / ``finetune`` semantics is touched — this
module only orchestrates ``protocol.run_cell`` and the existing reporters.
"""
from __future__ import annotations

import json
import os
import time
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


# ---------------------------------------------------------------------------
# Config schema + defaults
# ---------------------------------------------------------------------------
# Every key the Config cell freezes. ``run_unattended`` reads ONLY this dict, so
# the notebook's single interactive cell fully determines the run. Each axis is a
# LIST (the Cartesian product is the grid); scalar knobs are scalars. Defaults
# here are also the headless ``input()``-fallback defaults in the template, so the
# two config paths agree.
DEFAULT_CONFIG: Dict[str, Any] = {
    # --- grid axes (lists → Cartesian product) ---
    "backbones": ["vit_b32_cifar100"],
    "Ns": [10],
    "alphas": [0.1],
    # Local-step + alignment are folded into the protocol ``method`` token (see
    # protocol.parse_method): direct fine-tuning / distillation is selected by the
    # trainable scope + method; e.g. raw_union_K300 (raw alignment), no_phase0,
    # labelled_probe_warmup, dp_avg_eps8_K300, …
    "methods": ["raw_union_K300"],
    "seeds": [42, 43, 44],
    # Bounded-trajectory length(s) K. A list ⇒ K becomes a grid axis.
    "Ks": [300],
    # Trainable unit(s): head_only | lora_<rank> | last_block | last_n_blocks_<n>.
    # A list ⇒ trainable-unit comparison axis.
    "scopes": ["head_only"],
    # --- scalar knobs (passed straight to run_cell) ---
    "tau": 4.0,
    "student_lr": 0.01,
    "agg_method": "weight_avg",     # depth-1 linear combine (the production aggregate)
    "optimizer": "sgd",
    "probe_size": None,             # None ⇒ backbone default
    # Optional eval-only λ-scaling curve along θ₀ + λ·Σ wᵢΔᵢ (issue 026). A list
    # of floats turns it on (only meaningful for the linear weight_avg aggregate);
    # None / [] leaves run_cell byte-identical to the no-λ path.
    "lambda_scales": None,
    # --- I/O ---
    "case": "ft_unattended_demo",
    "results_root": "results",
    "data_root": "data",
    "cache_root": "cache",
    # --- unattended-run controls ---
    "resume": True,                 # skip cells whose success JSON already exists
    "per_cell_timeout_sec": 1800,   # hard cap so one hung cell can't stall the night
    "flush_every": 1,               # rebuild CSV/README every N completed cells
    # Best-effort ``git add results/<case> && commit`` after the run IF a token is
    # configured on the runtime. Default OFF; never run by the offline agent.
    "git_commit": False,
}


def normalize_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Return ``DEFAULT_CONFIG`` overlaid with ``config``, coercing the axis keys
    to lists so a researcher can pass a scalar (``"Ns": 10``) and still get a
    valid one-element axis. Pure / side-effect free → safe to call repeatedly."""
    cfg = dict(DEFAULT_CONFIG)
    cfg.update(config or {})
    for axis in ("backbones", "Ns", "alphas", "methods", "seeds", "Ks", "scopes"):
        v = cfg.get(axis)
        if v is None:
            cfg[axis] = []
        elif not isinstance(v, (list, tuple)):
            cfg[axis] = [v]
        else:
            cfg[axis] = list(v)
    if isinstance(cfg.get("lambda_scales"), (int, float)):
        cfg["lambda_scales"] = [float(cfg["lambda_scales"])]
    return cfg


# ---------------------------------------------------------------------------
# Grid construction (descriptors identical to sweep.build_grid)
# ---------------------------------------------------------------------------
def build_grid(config: Dict[str, Any]) -> List[Dict]:
    """Cartesian product over the config axes → deterministically-ordered list of
    cell descriptors, each produced by the SAME ``sweep.cell_descriptor`` the
    sbatch sweep uses. Identical iteration order to ``sweep.build_grid`` (backbone
    → N → α → method → seed → K → scope), so the two entrypoints agree on cell
    identity and resume each other's partial runs.

    ``tau`` / ``student_lr`` / ``agg_method`` / ``optimizer`` ride along as the
    scalar knobs from the config; ``cell_descriptor`` omits them from the key when
    they equal the historical defaults, so legacy cells keep their filename/hash.
    """
    from .sweep import cell_descriptor

    cfg = normalize_config(config)
    grid: List[Dict] = []
    for backbone in cfg["backbones"]:
        for N in cfg["Ns"]:
            for alpha in cfg["alphas"]:
                for method in cfg["methods"]:
                    for seed in cfg["seeds"]:
                        for K in cfg["Ks"]:
                            for scope in cfg["scopes"]:
                                grid.append(cell_descriptor(
                                    backbone, int(N), float(alpha), method,
                                    int(seed), int(K),
                                    tau=float(cfg["tau"]),
                                    student_lr=float(cfg["student_lr"]),
                                    trainable_scope=scope,
                                    agg_method=cfg["agg_method"],
                                    optimizer=cfg["optimizer"],
                                ))
    return grid


# ---------------------------------------------------------------------------
# Per-cell timeout (works on the notebook main thread AND in worker threads)
# ---------------------------------------------------------------------------
class CellTimeout(Exception):
    """Raised when a single cell exceeds ``per_cell_timeout_sec``."""


def _run_with_timeout(fn: Callable[[], Any], timeout_sec: Optional[float]) -> Any:
    """Run ``fn()`` under a hard wall-clock cap. ``timeout_sec`` falsy ⇒ no cap.

    Prefers ``signal.SIGALRM`` (cheap, no extra thread) when we are on the main
    thread of the main interpreter — the Colab notebook case. Falls back to a
    daemon worker thread + ``join(timeout)`` when SIGALRM is unavailable (e.g.
    called off the main thread, or on a platform without alarm). The fallback
    cannot forcibly kill the worker thread, so on timeout it raises CellTimeout
    and leaves the orphaned thread to finish in the background — the SWEEP still
    advances, which is the property ft03 requires (a hung cell never stalls the
    loop)."""
    if not timeout_sec or timeout_sec <= 0:
        return fn()

    import signal
    import threading

    on_main = threading.current_thread() is threading.main_thread()
    has_alarm = hasattr(signal, "SIGALRM")
    if on_main and has_alarm:
        def _handler(signum, frame):  # noqa: ANN001
            raise CellTimeout(f"cell exceeded {timeout_sec:.0f}s")

        old = signal.signal(signal.SIGALRM, _handler)
        # setitimer takes a float; alarm() only whole seconds. Prefer setitimer.
        try:
            signal.setitimer(signal.ITIMER_REAL, float(timeout_sec))
            return fn()
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0.0)
            signal.signal(signal.SIGALRM, old)

    # --- thread fallback -----------------------------------------------------
    result: Dict[str, Any] = {}

    def _target():
        try:
            result["value"] = fn()
        except BaseException as exc:  # noqa: BLE001 — surface in the parent
            result["exc"] = exc

    th = threading.Thread(target=_target, daemon=True)
    th.start()
    th.join(float(timeout_sec))
    if th.is_alive():
        raise CellTimeout(f"cell exceeded {timeout_sec:.0f}s (thread fallback)")
    if "exc" in result:
        raise result["exc"]
    return result.get("value")


# ---------------------------------------------------------------------------
# Reporting helpers
# ---------------------------------------------------------------------------
def _flush_report(results_dir: Path, config: Dict[str, Any]) -> None:
    """Rebuild results.csv + partition jsonl + README from ALL cell_*.json in the
    dir (resume-friendly: includes cells from prior sessions). Best-effort — a
    transient read error here must never abort the sweep."""
    try:
        from .report import write_report
        from .sweep import load_cells

        cells = load_cells(results_dir)
        # report.write_report reads a handful of ``args.get(...)`` keys for the
        # config block; map the config axes onto the names it expects.
        report_args = {
            "backbones": ",".join(map(str, config["backbones"])),
            "Ns": ",".join(map(str, config["Ns"])),
            "alphas": ",".join(map(str, config["alphas"])),
            "methods": ",".join(map(str, config["methods"])),
            "agg_methods": config["agg_method"],
            "seeds": ",".join(map(str, config["seeds"])),
            "K": ",".join(map(str, config["Ks"])),
            "tau": config["tau"],
            "student_lr": config["student_lr"],
            "probe_size": config["probe_size"],
        }
        write_report(results_dir=str(results_dir), cells=cells, args=report_args)
    except Exception as exc:  # noqa: BLE001 — partial report is non-fatal
        print(f"[runner] WARN report flush failed: {exc!r}", flush=True)


def _append_failure(results_dir: Path, record: Dict[str, Any]) -> None:
    """Append one JSON line to ``failures.jsonl`` (audit trail of every failed /
    timed-out cell). Best-effort; never raises into the loop."""
    try:
        with open(results_dir / "failures.jsonl", "a") as f:
            f.write(json.dumps(record, default=str) + "\n")
    except OSError as exc:
        print(f"[runner] WARN could not record failure: {exc!r}", flush=True)


def _maybe_git_commit(results_dir: Path, case: str) -> Optional[str]:
    """Best-effort ``git add results/<case> && commit`` so landed numbers survive a
    Colab VM reset. Runs ONLY when explicitly enabled in config AND git auth is
    configured on the runtime (a stored credential helper or token). Returns a
    short status string. The offline agent never calls this (git_commit defaults
    to False); this is runtime behaviour on Colab, not an agent action."""
    import subprocess

    try:
        env = os.environ.copy()
        subprocess.run(["git", "add", str(results_dir)], check=True,
                       capture_output=True, env=env)
        msg = f"results: {case} unattended run (notebook_runner)"
        cp = subprocess.run(
            ["git", "commit", "-m", msg,
             "-m", "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"],
            capture_output=True, text=True, env=env)
        if cp.returncode == 0:
            return "committed"
        return f"commit skipped (rc={cp.returncode}: {cp.stdout.strip()[:80]})"
    except Exception as exc:  # noqa: BLE001
        return f"commit error: {exc!r}"


# ---------------------------------------------------------------------------
# The entrypoint: run_unattended
# ---------------------------------------------------------------------------
def run_unattended(config: Dict[str, Any]) -> Dict[str, Any]:
    """Build the grid from ``config`` and run every cell to completion, unattended.

    Contract (ft03):
      * ZERO interaction after this is called — no ``input()``, no widgets.
      * Resumable: skips cells whose ``cell_*.json`` already records success.
      * Error-tolerant: per-cell exceptions / timeouts are logged to
        ``failures.jsonl`` and the loop continues.
      * One heartbeat line per cell; periodic CSV/README flush; a final summary.

    Returns a summary dict (also printed): ``{total, done, failed, skipped,
    wall_clock_sec, results_dir, failures_log, git}``.
    """
    from .protocol import run_cell
    from .sweep import cell_filename, write_cell_json

    cfg = normalize_config(config)
    job_id = os.environ.get("SLURM_JOB_ID") or os.environ.get("COLAB_JOB_ID")
    node = os.environ.get("SLURMD_NODENAME") or os.environ.get("HOSTNAME")

    results_dir = Path(cfg["results_root"]) / cfg["case"]
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "runs").mkdir(exist_ok=True)

    grid = build_grid(cfg)
    total = len(grid)
    timeout = cfg["per_cell_timeout_sec"]
    flush_every = max(1, int(cfg["flush_every"]))
    lambda_scales = cfg["lambda_scales"] or None

    print(f"[runner] START case={cfg['case']} cells={total} "
          f"resume={cfg['resume']} timeout={timeout}s "
          f"-> {results_dir}", flush=True)

    run_start = time.time()
    n_done = n_fail = n_skip = 0

    for k, desc in enumerate(grid, start=1):
        out_path = results_dir / cell_filename(desc)
        tag_id = (f"{desc['backbone']} N={desc['N']} a={desc['alpha']} "
                  f"{desc['method']} s={desc['seed']} K={desc['K']}")

        # --- resume: skip a previously-successful cell -----------------------
        if cfg["resume"] and out_path.exists():
            prior_ok = False
            try:
                prior_ok = json.loads(out_path.read_text()).get("status") == "success"
            except (json.JSONDecodeError, OSError):
                prior_ok = False
            if prior_ok:
                n_skip += 1
                print(f"[{k}/{total}] {cfg['case']} {tag_id} skip (success exists)",
                      flush=True)
                continue

        # --- run the cell under a hard per-cell timeout, tolerating failure --
        cell_tau = desc.get("tau", cfg["tau"])
        cell_lr = desc.get("student_lr", cfg["student_lr"])
        cell_scope = desc.get("trainable_scope", "head_only")
        cell_agg = desc.get("agg_method", cfg["agg_method"])
        cell_optimizer = desc.get("optimizer", cfg["optimizer"])
        t_cell = time.time()
        try:
            res = _run_with_timeout(
                lambda d=desc, t=cell_tau, lr=cell_lr, sc=cell_scope,
                ag=cell_agg, op=cell_optimizer: run_cell(
                    backbone=d["backbone"], N=d["N"], alpha=d["alpha"],
                    seed=d["seed"], method=d["method"], K=d["K"],
                    tau=t, student_lr=lr,
                    probe_size=cfg["probe_size"],
                    data_root=cfg["data_root"], cache_root=cfg["cache_root"],
                    job_id=job_id, node=node,
                    trainable_scope=sc, agg_method=ag,
                    optimizer=op,
                    lambda_scales=lambda_scales,
                ),
                timeout,
            )
            # run_cell catches its own internal errors and returns status=FAIL;
            # persist whatever it returned and branch on that status.
            write_cell_json(results_dir, res, desc)
            if res.status == "success":
                n_done += 1
                acc = f"{res.acc:.4f}" if res.acc is not None else "n/a"
                print(f"[{k}/{total}] {cfg['case']} {tag_id} ok "
                      f"acc={acc} wall={res.wall_clock_sec:.1f}s", flush=True)
            else:
                n_fail += 1
                _append_failure(results_dir, {
                    "ts": time.time(), "cell": tag_id, "descriptor": desc,
                    "kind": "run_cell_FAIL", "error": res.error,
                    "wall_clock_sec": res.wall_clock_sec,
                })
                print(f"[{k}/{total}] {cfg['case']} {tag_id} FAIL "
                      f"err={res.error}", flush=True)

        except CellTimeout as exc:
            n_fail += 1
            _append_failure(results_dir, {
                "ts": time.time(), "cell": tag_id, "descriptor": desc,
                "kind": "timeout", "error": str(exc),
                "wall_clock_sec": time.time() - t_cell,
            })
            print(f"[{k}/{total}] {cfg['case']} {tag_id} FAIL "
                  f"err=timeout({timeout}s)", flush=True)

        except BaseException as exc:  # noqa: BLE001 — one bad cell never aborts the run
            n_fail += 1
            _append_failure(results_dir, {
                "ts": time.time(), "cell": tag_id, "descriptor": desc,
                "kind": "exception", "error": repr(exc),
                "traceback": traceback.format_exc()[-1500:],
                "wall_clock_sec": time.time() - t_cell,
            })
            print(f"[{k}/{total}] {cfg['case']} {tag_id} FAIL "
                  f"err={exc!r}", flush=True)

        # --- periodic flush so partial results are visible mid-run -----------
        if k % flush_every == 0:
            _flush_report(results_dir, cfg)

    # --- final flush + summary ----------------------------------------------
    _flush_report(results_dir, cfg)
    wall = time.time() - run_start

    git_status = "disabled"
    if cfg.get("git_commit"):
        git_status = _maybe_git_commit(results_dir, cfg["case"]) or "unknown"

    summary = {
        "case": cfg["case"],
        "total": total,
        "done": n_done,
        "failed": n_fail,
        "skipped": n_skip,
        "wall_clock_sec": round(wall, 1),
        "results_dir": str(results_dir),
        "readme": str(results_dir / "README.md"),
        "results_csv": str(results_dir / "results.csv"),
        "failures_log": str(results_dir / "failures.jsonl"),
        "git": git_status,
    }
    print("[runner] DONE " + json.dumps(summary), flush=True)
    print(f"[runner] {n_done} ok / {n_fail} failed / {n_skip} skipped "
          f"of {total} cells in {wall:.1f}s. Results: {results_dir}", flush=True)
    if n_fail:
        print(f"[runner] {n_fail} failed cell(s) logged at "
              f"{results_dir / 'failures.jsonl'} — the run completed past them.",
              flush=True)
    # Write a machine-readable summary alongside the case for provenance.
    try:
        (results_dir / "run_summary.json").write_text(json.dumps(summary, indent=2))
    except OSError:
        pass
    return summary


__all__ = [
    "DEFAULT_CONFIG",
    "normalize_config",
    "build_grid",
    "run_unattended",
    "CellTimeout",
]
