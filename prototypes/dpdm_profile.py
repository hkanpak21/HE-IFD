#!/usr/bin/env python3
"""
HE-IFD A5 profiling micro-task: single-client DP-DDPM training.

Goal: measure h = wall-clock hours to FID-plateau when training one DP-DDPM
(Dockhorn et al. TMLR 2022, eps=10) on a single client's MNIST partition on
one T4 GPU. The measured value of h gates the gamma-variant scope decision
per PRD section 8 item 10 and action plan A5 lines 333-339:

    h <= 3 h     -> full-grid path (gamma is 4th column in A4 headline grid)
    3 h < h <= 8 h -> subset path (gamma as separate table, 1 alpha/dataset)
    h > 8 h      -> CIFAR-100/SVHN exclusion (gamma on MNIST/FMNIST/CIFAR-10)

This wrapper imports the upstream DPDM trainer
(comparators/dpdm_upstream/runners/train_dpdm_base.py) and monkey-patches:

  * torchvision.datasets.MNIST so __getitem__ is restricted to client-0
    indices drawn from a Dirichlet(alpha=0.3) partition (N_clients=10, seed=42).
  * The trainer's compute_fid call site through a logging handler that
    detects FID-plateau (no improvement > FID_IMPROVE_TOL over the last
    PLATEAU_WINDOW evaluations) and raises a sentinel to stop training.

GOLDEN RULE: do not invoke this on the login node. Run via:
    sbatch jobs/dpdm_profile.sh

The configuration here is hard-coded per A5 spec. Override is intentionally
absent -- the profiling number must be reproducible.
"""
from __future__ import annotations

import json
import logging
import os
import re
import signal
import sys
import time
from pathlib import Path
from typing import List

# ---------------------------------------------------------------------------
# Profiling configuration (hard-coded per A5 spec; do not parameterise).
# ---------------------------------------------------------------------------
REPO_ROOT = Path("/scratch/hkanpak21/HE_IFD")
UPSTREAM_DIR = REPO_ROOT / "comparators" / "dpdm_upstream"
RESULTS_DIR = REPO_ROOT / "results"

PROFILE = {
    "dataset": "mnist_28",
    "n_clients": 10,
    "dirichlet_alpha": 0.3,
    "partition_seed": 42,
    "client_idx": 0,            # we profile client 0 of N=10.
    "epsilon": 10.0,            # Dockhorn et al. headline budget.
    "delta": 1e-5,
    "n_gpus_per_node": 1,       # single T4.
    "batch_size": 2048,         # reduced from upstream 4096 (T4 16GB vs A100 80GB).
    "max_physical_batch_size": 256,  # T4 memory bound for 28x28 grayscale.
    "n_splits": 8,              # increased from upstream 4 to fit T4 memory.
    "n_epochs": 300,            # upstream default; plateau detector exits earlier.
    "lr": 3e-4,
    "optimizer": "Adam",
    "fid_freq": 2000,           # eval every K=2000 iters (upstream uses 10000).
    "fid_samples": 5000,
    "wall_clock_cap_hours": 12.0,
}

# FID plateau heuristic. We declare plateau if the best FID in the trailing
# window has not improved by more than FID_IMPROVE_TOL relative to the best
# before that window. K = fid_freq = 2000 iters, N = PLATEAU_WINDOW = 4 evals
# -> at least 8000 iters of unimproved FID before exit. Roughly matches the
# DPDM paper's eyeballed convergence schedule and fits well inside the 12 h
# wall-clock cap even at worst-case T4 throughput.
PLATEAU_WINDOW = 4
FID_IMPROVE_TOL = 1.0

# Patterns for parsing the upstream logger; the trainer logs
#   "FID %d at iteration %d: %.6f"   (see runners/train_dpdm_base.py:177)
FID_LOG_RE = re.compile(r"FID\s+\d+\s+at iteration\s+(\d+):\s+([\d\.]+)")


# ---------------------------------------------------------------------------
# Dirichlet partition over MNIST labels.
# ---------------------------------------------------------------------------
def dirichlet_client_indices(
    labels, n_clients: int, alpha: float, seed: int, client_idx: int
) -> List[int]:
    """Return sample indices assigned to ``client_idx`` under a
    label-Dirichlet partition with parameter ``alpha``. Standard
    HE-IFD / FL non-IID convention (matches Hsu et al. 2019)."""
    import numpy as np

    rng = np.random.default_rng(seed)
    labels = np.asarray(labels)
    n_classes = int(labels.max() + 1)
    client_indices: List[List[int]] = [[] for _ in range(n_clients)]
    for cls in range(n_classes):
        cls_idx = np.where(labels == cls)[0]
        rng.shuffle(cls_idx)
        proportions = rng.dirichlet(alpha=[alpha] * n_clients)
        splits = (np.cumsum(proportions) * len(cls_idx)).astype(int)[:-1]
        for k, chunk in enumerate(np.split(cls_idx, splits)):
            client_indices[k].extend(chunk.tolist())
    return sorted(client_indices[client_idx])


# ---------------------------------------------------------------------------
# Monkey-patch torchvision.datasets.MNIST to return only client-0 samples.
# ---------------------------------------------------------------------------
def install_mnist_partition_patch() -> int:
    """Wrap MNIST.__init__ so the constructed dataset holds only the
    Dirichlet client-0 subset. Returns the number of samples kept."""
    import torchvision

    orig_init = torchvision.datasets.MNIST.__init__
    n_kept_ref = {"n": 0}

    def patched_init(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        # MNIST stores tensors on self.data / self.targets after init.
        labels = self.targets.numpy() if hasattr(self.targets, "numpy") else list(self.targets)
        keep = dirichlet_client_indices(
            labels=labels,
            n_clients=PROFILE["n_clients"],
            alpha=PROFILE["dirichlet_alpha"],
            seed=PROFILE["partition_seed"],
            client_idx=PROFILE["client_idx"],
        )
        import torch
        idx = torch.tensor(keep, dtype=torch.long)
        self.data = self.data[idx]
        self.targets = self.targets[idx]
        n_kept_ref["n"] = len(keep)
        logging.getLogger(__name__).info(
            "[dpdm_profile] client-%d MNIST partition: %d / %d samples kept "
            "(alpha=%.2f, N=%d, seed=%d)",
            PROFILE["client_idx"], len(keep), len(idx),
            PROFILE["dirichlet_alpha"], PROFILE["n_clients"],
            PROFILE["partition_seed"],
        )

    torchvision.datasets.MNIST.__init__ = patched_init
    return n_kept_ref["n"]


# ---------------------------------------------------------------------------
# Plateau detector implemented as a logging.Handler on the root logger.
# When triggered, raises PlateauReached, which we catch in main().
# ---------------------------------------------------------------------------
class PlateauReached(Exception):
    pass


class PlateauWatcher(logging.Handler):
    def __init__(self, window: int, tol: float):
        super().__init__(level=logging.INFO)
        self.window = window
        self.tol = tol
        self.history: List[tuple] = []   # (iter, fid)
        self.best_so_far = float("inf")
        self.last_fid = None
        self.last_iter = None

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = record.getMessage()
        except Exception:
            return
        m = FID_LOG_RE.search(msg)
        if not m:
            return
        it = int(m.group(1))
        fid = float(m.group(2))
        self.history.append((it, fid))
        self.last_iter = it
        self.last_fid = fid
        if len(self.history) <= self.window:
            self.best_so_far = min(self.best_so_far, fid)
            return
        # Best FID before the trailing window.
        pre_window = self.history[: -self.window]
        pre_best = min(f for _, f in pre_window)
        window_best = min(f for _, f in self.history[-self.window:])
        if pre_best - window_best <= self.tol:
            logging.getLogger(__name__).info(
                "[dpdm_profile] FID plateau: pre_best=%.4f window_best=%.4f "
                "(delta %.4f <= tol %.4f over last %d evals).",
                pre_best, window_best, pre_best - window_best,
                self.tol, self.window,
            )
            raise PlateauReached()


# ---------------------------------------------------------------------------
# Build the OmegaConf config object the upstream trainer expects, starting
# from configs/mnist_28/train_eps_10.0.yaml and overriding for single-T4.
# ---------------------------------------------------------------------------
def build_config():
    from omegaconf import OmegaConf

    cfg_path = UPSTREAM_DIR / "configs" / "mnist_28" / "train_eps_10.0.yaml"
    cfg = OmegaConf.load(str(cfg_path))

    # Setup overrides for single-T4 (upstream defaults assume 8x A100).
    cfg.setup.n_gpus_per_node = PROFILE["n_gpus_per_node"]
    cfg.setup.n_nodes = 1
    cfg.setup.node_rank = 0
    cfg.setup.local_rank = 0
    cfg.setup.global_rank = 0
    cfg.setup.global_size = 1
    cfg.setup.runner = "train_dpdm_base"
    cfg.setup.mode = "train"
    cfg.setup.root_folder = str(REPO_ROOT)
    cfg.setup.workdir = "results/dpdm_profile_workdir_%s" % os.environ.get(
        "SLURM_JOB_ID", "local"
    )
    cfg.setup.device = "cuda:0"

    # Train / DP / sampler overrides for T4 memory + plateau detection.
    cfg.train.batch_size = PROFILE["batch_size"]
    cfg.train.n_epochs = PROFILE["n_epochs"]
    cfg.train.fid_freq = PROFILE["fid_freq"]
    cfg.train.fid_samples = PROFILE["fid_samples"]
    cfg.train.fid_threshold = 1  # eval from iter 1 onward; plateau watcher waits for window.
    cfg.dp.epsilon = PROFILE["epsilon"]
    cfg.dp.delta = PROFILE["delta"]
    cfg.dp.max_physical_batch_size = PROFILE["max_physical_batch_size"]
    cfg.dp.n_splits = PROFILE["n_splits"]

    # FID statistics: precompute_data_mnist_fid_statistics.py writes
    # assets/stats/mnist_train.npz relative to upstream root.
    cfg.data.fid_stats = [
        str(UPSTREAM_DIR / "assets" / "stats" / "mnist_train.npz")
    ]
    return cfg


# ---------------------------------------------------------------------------
# Distributed bootstrap: even for n_gpus=1 the upstream uses torch.distributed
# with backend=nccl. We initialise a single-rank world here so the trainer's
# dist.barrier() and DPDDP wrapper still function.
# ---------------------------------------------------------------------------
def init_singleton_distributed() -> None:
    import torch
    import torch.distributed as dist

    if dist.is_available() and not dist.is_initialized():
        os.environ.setdefault("MASTER_ADDR", "127.0.0.1")
        os.environ.setdefault("MASTER_PORT", "6020")
        os.environ.setdefault("RANK", "0")
        os.environ.setdefault("WORLD_SIZE", "1")
        os.environ.setdefault("LOCAL_RANK", "0")
        dist.init_process_group(
            backend="nccl",
            init_method="env://",
            rank=0,
            world_size=1,
        )
    if torch.cuda.is_available():
        torch.cuda.set_device(0)


# ---------------------------------------------------------------------------
# Wall-clock cap watchdog using SIGALRM (UNIX-only; OK for Linux/Valar).
# ---------------------------------------------------------------------------
class WallClockCap(Exception):
    pass


def install_wallclock_cap(hours: float) -> None:
    def _handler(signum, frame):
        raise WallClockCap()
    signal.signal(signal.SIGALRM, _handler)
    signal.alarm(int(hours * 3600))


# ---------------------------------------------------------------------------
# Main entry point.
# ---------------------------------------------------------------------------
def main() -> int:
    job_id = os.environ.get("SLURM_JOB_ID", "local")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_json = RESULTS_DIR / f"dpdm_profile_{job_id}.json"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )
    log = logging.getLogger("dpdm_profile")

    # Make the upstream importable.
    sys.path.insert(0, str(UPSTREAM_DIR))

    log.info("[dpdm_profile] profiling config: %s", json.dumps(PROFILE, indent=2))
    log.info("[dpdm_profile] upstream dir: %s", UPSTREAM_DIR)
    log.info("[dpdm_profile] writing summary to: %s", out_json)

    n_samples = install_mnist_partition_patch()
    watcher = PlateauWatcher(window=PLATEAU_WINDOW, tol=FID_IMPROVE_TOL)
    logging.getLogger().addHandler(watcher)

    install_wallclock_cap(PROFILE["wall_clock_cap_hours"])

    summary = {
        "job_id": job_id,
        "profile_config": PROFILE,
        "plateau": {
            "window": PLATEAU_WINDOW,
            "fid_improve_tol": FID_IMPROVE_TOL,
        },
        "client_partition_size": None,
        "wall_clock_hours": None,
        "peak_gpu_memory_mb": None,
        "samples_per_sec": None,
        "final_fid": None,
        "termination_reason": None,
        "fid_history": [],
    }

    try:
        init_singleton_distributed()
        import torch
        torch.cuda.reset_peak_memory_stats()

        cfg = build_config()
        summary["client_partition_size"] = n_samples or len(
            __import__("torchvision").datasets.MNIST(
                root=str(UPSTREAM_DIR / "toy_data"), train=True, download=True
            )
        )

        # Lazy import so torch is initialised first.
        os.chdir(UPSTREAM_DIR)  # upstream uses relative paths (toy_data/, assets/).
        from runners import train_dpdm_base

        start = time.perf_counter()
        try:
            train_dpdm_base.training(cfg, cfg.setup.workdir, "train")
            summary["termination_reason"] = "training_completed_all_epochs"
        except PlateauReached:
            summary["termination_reason"] = "fid_plateau"
        except WallClockCap:
            summary["termination_reason"] = "wall_clock_cap_hit"
        elapsed = time.perf_counter() - start

        summary["wall_clock_hours"] = elapsed / 3600.0
        if torch.cuda.is_available():
            summary["peak_gpu_memory_mb"] = (
                torch.cuda.max_memory_allocated() / (1024 * 1024)
            )
        # samples/sec = (n_kept_samples * epochs_run) / elapsed_seconds.
        # We approximate epochs_run from the last FID iteration recorded.
        if watcher.history:
            last_iter = watcher.history[-1][0]
            iters_per_epoch = max(
                1, summary["client_partition_size"] // PROFILE["batch_size"]
            )
            approx_epochs = max(1, last_iter / iters_per_epoch)
            samples_processed = summary["client_partition_size"] * approx_epochs
            summary["samples_per_sec"] = samples_processed / max(elapsed, 1e-6)
            summary["final_fid"] = watcher.last_fid
        summary["fid_history"] = watcher.history
    except Exception as exc:  # noqa: BLE001
        summary["termination_reason"] = f"exception: {type(exc).__name__}: {exc}"
        log.exception("[dpdm_profile] training aborted")
    finally:
        with open(out_json, "w") as f:
            json.dump(summary, f, indent=2, default=str)
        log.info("[dpdm_profile] wrote %s", out_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
