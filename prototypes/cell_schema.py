"""
Shared per-cell result schema for the HE-IFD experimental grid.

This file is the source-of-truth contract between:
  * issue 14 (this owner) -- writes CellResult instances from heifd_train.py
  * issue 15 (preflight)  -- reads/validates JSON blobs against this schema
  * issue 18 (fanout)     -- emits one CellResult per grid cell
  * issue 21 (MIA)        -- decorates CellResult with the MIA fields

Keep this file dependency-free (stdlib only) and stable: any breaking change
forces a coordinated update across the four converging issues.
"""
from __future__ import annotations

import json
import os
import socket
import time
from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class CellResult:
    method: str                # "heifd" | "coboost" | "fedmd" | "feddiff" | "fedkt" | ...
    dataset: str               # "MNIST" | "FashionMNIST" | "CIFAR-10" | "SVHN" | "CIFAR-100"
    alpha: float               # Dirichlet alpha
    seed: int
    N: int                     # number of clients
    variant: Optional[str]     # "warmstart" | "randominit" | "warmstart-no-ensemble" | "gamma" | "epsilon" -- None for non-heifd methods
    job_id: str                # SLURM_JOB_ID env var, "local" if missing
    node: str                  # socket.gethostname()
    wall_clock_sec: float
    status: str                # "success" | "failed" | "timeout"
    error: Optional[str]       # exception type + message if status != "success"
    student_acc: Optional[float]
    mean_teacher_acc: Optional[float]
    oracle_acc: Optional[float]
    epsilon_actual: Optional[float]   # DP methods only
    delta_actual: Optional[float]     # DP methods only
    notes: Optional[str]              # free-form (e.g. depth-budget audit log line)

    def dump(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def make(cls, method, dataset, alpha, seed, N, variant=None) -> "CellResult":
        return cls(
            method=method, dataset=dataset, alpha=alpha, seed=seed, N=N,
            variant=variant,
            job_id=os.environ.get("SLURM_JOB_ID", "local"),
            node=socket.gethostname(),
            wall_clock_sec=0.0, status="failed", error=None,
            student_acc=None, mean_teacher_acc=None, oracle_acc=None,
            epsilon_actual=None, delta_actual=None, notes=None,
        )

    def default_path(self, root: str = "results/cells") -> str:
        v = f"_{self.variant}" if self.variant else ""
        return f"{root}/{self.method}_{self.dataset}_a{self.alpha}_s{self.seed}{v}_{self.job_id}.json"

    @classmethod
    def load(cls, path: str) -> "CellResult":
        """Inverse of dump(): read a JSON blob into a CellResult."""
        with open(path) as f:
            payload = json.load(f)
        return cls(**payload)


# Sentinel used by the fanout (issue 18) when timing out / killing a cell that
# never produced a JSON. Keeping this here avoids string-literal drift.
TIMEOUT_STATUS = "timeout"
FAILED_STATUS = "failed"
SUCCESS_STATUS = "success"


def now_seconds() -> float:
    """Single-source-of-truth for wall-clock timestamps so all writers agree."""
    return time.time()
