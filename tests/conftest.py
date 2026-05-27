"""Pytest scaffolding for the HE-IFD unit suite.

Makes the flat ``src`` package importable as ``src.aggregate`` etc. regardless of
the directory pytest is launched from (the repo has no ``pyproject.toml`` /
``pytest.ini`` and is run via an sbatch wrapper that ``cd``s to the repo root,
but a developer might also run ``pytest tests/`` from elsewhere). We prepend the
repo root — the parent of this ``tests/`` directory — to ``sys.path`` so the
``src`` package (which already carries an ``__init__.py``) resolves.

These tests are behaviour-level: they exercise the public functions of
``src.aggregate``, ``src.phase0`` and ``src.data`` and assert their externally
observable contracts (the FHE-linearity / telescoping identity, the DP-sigma
formula, partition reproducibility, probe/training disjointness). They never
reach into module internals.

torch/numpy are imported lazily inside the individual tests via
``pytest.importorskip`` so that a collection pass on a machine without the
scientific stack does not error — only the tests that genuinely need a tensor
backend are skipped there. On VALAR's ``he_ofl`` env both are present, so the
whole suite runs.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
