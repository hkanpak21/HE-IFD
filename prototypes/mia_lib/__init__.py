"""HE-IFD A7 post-release MIA library.

This package provides the building blocks for the issue 21 attack-suite on
decrypted student checkpoints produced by issue 14's HE-IFD pipeline:

- ``shadow_models``: shadow-model training infrastructure for LiRA.
- ``lira``: LiRA score computation (offline variant, per Carlini et al. 2022).
- ``loss_threshold``: Yeom et al. 2018 cross-entropy loss-threshold baseline.

The MIAResult dataclass lives here (not in prototypes/cell_schema.py, which
is issue 14's territory) and is what prototypes/mia_lira.py persists as JSON.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional


@dataclass
class MIAResult:
    """Per-cell post-release MIA result for one decrypted student.

    The (method, dataset, alpha, seed, variant) tuple identifies the source
    student cell (i.e. the issue 14 / issue 18 grid cell that produced the
    checkpoint at ``student_ckpt_path``). The two AUC fields are the
    membership-inference attack AUCs against that student:

    - ``lira_auc``: LiRA (Carlini et al. 2022) offline variant.
    - ``loss_threshold_auc``: Yeom et al. 2018 cross-entropy loss-threshold.

    ``status`` is ``"ok"`` on success and ``"error"`` if the attack aborted.
    On error, ``error`` carries the exception summary and the AUC fields are
    NaN-equivalent (-1.0 sentinel) so consumers can filter them out.
    """

    method: str               # e.g. "heifd_warmstart"
    dataset: str              # e.g. "MNIST"
    alpha: float              # Dirichlet non-IID parameter
    seed: int                 # cell seed
    variant: Optional[str]    # e.g. "warmstart", or None
    n_shadows: int            # number of shadow models trained / cached
    lira_auc: float
    loss_threshold_auc: float
    student_ckpt_path: str
    wall_clock_sec: float
    status: str               # "ok" | "error"
    error: Optional[str] = None
    # Optional diagnostics for downstream debugging; not load-bearing.
    n_target_points: int = 0
    n_members: int = 0
    n_nonmembers: int = 0
    shadow_cache_hit: bool = False
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


__all__ = ["MIAResult"]
