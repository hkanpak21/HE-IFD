#!/usr/bin/env python3
"""HE-IFD A7 post-release MIA driver (issue 21).

End-to-end orchestrator that runs LiRA (offline, Carlini et al. 2022) and a
loss-threshold baseline (Yeom et al. 2018) against one decrypted student
checkpoint produced by issue 14's HE-IFD pipeline, and writes a
:class:`prototypes.mia_lib.MIAResult` JSON to disk.

The student checkpoint, the (dataset, alpha, seed, variant) tuple, and the
list of members vs. non-members come from issue 14's
``prototypes.cell_schema.CellResult``. We import that lazily so that a
syntax-check on this file does not require issue 14 to have landed yet.

GOLDEN RULE: only invoke via sbatch (see ``jobs/mia_lira.sh``). The shadow
training path enforces a CUDA-availability check by default.

CLI
---
::

    python prototypes/mia_lira.py \
        --student-ckpt PATH \
        --dataset MNIST --alpha 0.3 --seed 42 --variant warmstart \
        --n-shadows 64 \
        --shadow-cache results/shadows

"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
import traceback
from dataclasses import asdict
from pathlib import Path
from typing import Optional, Tuple

import numpy as np


REPO_ROOT = Path("/scratch/hkanpak21/HE_IFD")
# Make ``prototypes`` importable when run as ``python prototypes/mia_lira.py``.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


LOG = logging.getLogger("mia_lira")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="A7 post-release MIA (LiRA + loss-threshold) against a "
                    "decrypted HE-IFD student checkpoint."
    )
    p.add_argument(
        "--student-ckpt",
        required=True,
        type=Path,
        help="Path to the decrypted student checkpoint (issue 14 output).",
    )
    p.add_argument(
        "--cell-result",
        type=Path,
        default=None,
        help="Optional path to the CellResult JSON for this student. If "
             "omitted we infer (dataset, alpha, seed, variant) from the "
             "CLI flags and assume members = first half of the training "
             "split (a sentinel partition; used only for syntax / dry-run).",
    )
    p.add_argument("--dataset", required=True, choices=["MNIST", "FashionMNIST", "CIFAR10"])
    p.add_argument("--alpha", required=True, type=float)
    p.add_argument("--seed", required=True, type=int)
    p.add_argument("--variant", default=None, type=str)
    p.add_argument("--method", default="heifd_warmstart", type=str,
                   help="Tag identifying the upstream training method.")
    p.add_argument("--n-shadows", default=64, type=int)
    p.add_argument(
        "--shadow-cache",
        default=Path("results/shadows"),
        type=Path,
        help="Root dir for the shadow-model cache; per-(dataset, seed) "
             "subdirs are created underneath.",
    )
    p.add_argument(
        "--data-root",
        default=Path("data"),
        type=Path,
        help="Torchvision data dir.",
    )
    p.add_argument(
        "--results-dir",
        default=Path("results/mia"),
        type=Path,
    )
    p.add_argument(
        "--shadow-epochs",
        default=20,
        type=int,
        help="Epochs per shadow model (per-shadow cost dominates total budget).",
    )
    p.add_argument(
        "--shadow-batch-size",
        default=128,
        type=int,
    )
    p.add_argument(
        "--n-candidates",
        default=4000,
        type=int,
        help="Total number of candidate points (members + non-members) to "
             "score. Larger => more stable AUC, more wall-clock.",
    )
    p.add_argument(
        "--no-cuda-required",
        action="store_true",
        help="Allow shadow training without CUDA (testing only).",
    )
    return p.parse_args(argv)


# ---------------------------------------------------------------------------
# Cell result loader (loose coupling with issue 14).
# ---------------------------------------------------------------------------
def _load_cell_result(path: Optional[Path]):
    """Return (member_indices, nonmember_indices) into the shadow training pool.

    If ``path`` is provided, we expect the CellResult JSON to expose at
    least these fields (issue 14 owns the canonical schema):

    - ``member_indices``: list[int] -- training-pool indices of points the
      student was distilled / fine-tuned against.
    - ``nonmember_indices``: list[int] -- held-out indices (typically the
      cell's eval / heldout split).

    If ``path`` is None, we return ``(None, None)`` and the driver falls
    back to a sentinel split (first half of the train pool = members).
    This sentinel is only for syntax/dry-run; live MIA runs MUST pass a
    real CellResult.
    """
    if path is None:
        return None, None
    if not path.exists():
        raise FileNotFoundError(f"--cell-result {path} not found")
    with open(path) as f:
        blob = json.load(f)
    mem = blob.get("member_indices")
    non = blob.get("nonmember_indices")
    if mem is None or non is None:
        raise KeyError(
            "CellResult JSON missing member_indices / nonmember_indices; "
            "issue 14 owns this schema."
        )
    return list(mem), list(non)


def _sentinel_split(n_pool: int) -> Tuple[list, list]:
    half = n_pool // 2
    return list(range(half)), list(range(half, n_pool))


def _sample_candidates(
    member_idx, nonmember_idx, n_candidates: int, rng: np.random.Generator
):
    """Sample ~half members and ~half non-members from the available pools."""
    n_half = n_candidates // 2
    m = np.asarray(member_idx, dtype=int)
    nm = np.asarray(nonmember_idx, dtype=int)
    if len(m) > n_half:
        m = rng.choice(m, size=n_half, replace=False)
    if len(nm) > n_half:
        nm = rng.choice(nm, size=n_half, replace=False)
    return m.astype(int), nm.astype(int)


# ---------------------------------------------------------------------------
# Target student loader
# ---------------------------------------------------------------------------
def _load_target_student(dataset: str, ckpt_path: Path):
    """Load the decrypted student. We assume the student architecture
    matches the shadow architecture for the dataset (LeNet-5 / ResNet-8),
    consistent with the issue 14 / issue 18 grid spec. The checkpoint is
    expected to be a torch ``state_dict``.
    """
    import torch

    from prototypes.mia_lib.shadow_models import instantiate_arch

    if not ckpt_path.exists():
        raise FileNotFoundError(f"--student-ckpt {ckpt_path} not found")
    model = instantiate_arch(dataset)
    sd = torch.load(str(ckpt_path), map_location="cpu")
    # Accept both raw state_dicts and {"model": state_dict, ...} wrappers.
    if isinstance(sd, dict) and "state_dict" in sd:
        sd = sd["state_dict"]
    elif isinstance(sd, dict) and "model" in sd and isinstance(sd["model"], dict):
        sd = sd["model"]
    model.load_state_dict(sd, strict=False)
    model.eval()
    return model


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(argv=None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )

    job_id = os.environ.get("SLURM_JOB_ID", "local")
    args.results_dir.mkdir(parents=True, exist_ok=True)

    variant_tag = args.variant if args.variant else "none"
    out_path = (
        args.results_dir
        / f"lira_{args.dataset}_a{args.alpha}_s{args.seed}_{variant_tag}_{job_id}.json"
    )

    # Pre-populate result with error sentinel; we overwrite on success.
    from prototypes.mia_lib import MIAResult

    result = MIAResult(
        method=args.method,
        dataset=args.dataset,
        alpha=float(args.alpha),
        seed=int(args.seed),
        variant=args.variant,
        n_shadows=int(args.n_shadows),
        lira_auc=-1.0,
        loss_threshold_auc=-1.0,
        student_ckpt_path=str(args.student_ckpt),
        wall_clock_sec=0.0,
        status="error",
        error=None,
    )

    t_start = time.perf_counter()
    try:
        import torch  # noqa: F401  (defer import; report nice error if missing)

        # 1. Shadow population.
        from prototypes.mia_lib.shadow_models import (
            train_shadow_models,
            load_full_dataset,
        )

        bundle = train_shadow_models(
            args.dataset,
            n_shadows=args.n_shadows,
            seed=args.seed,
            shadow_cache_root=args.shadow_cache,
            data_root=args.data_root,
            epochs=args.shadow_epochs,
            batch_size=args.shadow_batch_size,
            require_cuda=not args.no_cuda_required,
        )
        result.shadow_cache_hit = bool(bundle.cache_hit)
        LOG.info(
            "[mia_lira] shadow bundle: n=%d, victim_size=%d, pool=%d, cache_hit=%s",
            bundle.n_shadows, bundle.victim_size, bundle.n_train_pool,
            bundle.cache_hit,
        )

        # 2. Resolve the candidate split.
        tr_x, tr_y, _, _ = load_full_dataset(args.dataset, args.data_root)
        mem_idx, nonmem_idx = _load_cell_result(args.cell_result)
        if mem_idx is None:
            LOG.warning(
                "[mia_lira] --cell-result not provided; using sentinel "
                "first-half/second-half split. Live runs must pass the "
                "CellResult JSON."
            )
            mem_idx, nonmem_idx = _sentinel_split(int(tr_x.shape[0]))

        rng = np.random.default_rng(args.seed)
        m_sel, nm_sel = _sample_candidates(
            mem_idx, nonmem_idx, args.n_candidates, rng
        )
        cand_idx = np.concatenate([m_sel, nm_sel])
        cand_x = tr_x[cand_idx]
        cand_y = tr_y[cand_idx]
        is_member = np.concatenate(
            [np.ones(len(m_sel), dtype=bool), np.zeros(len(nm_sel), dtype=bool)]
        )
        result.n_target_points = int(len(cand_idx))
        result.n_members = int(is_member.sum())
        result.n_nonmembers = int((~is_member).sum())

        # 3. Target student.
        target_model = _load_target_student(args.dataset, args.student_ckpt)
        device = "cuda" if torch.cuda.is_available() else "cpu"

        # 4. LiRA attack.
        from prototypes.mia_lib.lira import lira_attack

        lira_auc, _ = lira_attack(
            bundle=bundle,
            target_model=target_model,
            candidate_xs=cand_x,
            candidate_ys=cand_y,
            is_member=is_member,
            candidate_pool_indices=cand_idx,
            device=device,
        )
        result.lira_auc = float(lira_auc)
        LOG.info("[mia_lira] LiRA AUC = %.4f", lira_auc)

        # 5. Loss-threshold attack.
        from prototypes.mia_lib.loss_threshold import loss_threshold_attack

        lt_auc, _ = loss_threshold_attack(
            target_model=target_model,
            candidate_xs=cand_x,
            candidate_ys=cand_y,
            is_member=is_member,
            device=device,
        )
        result.loss_threshold_auc = float(lt_auc)
        LOG.info("[mia_lira] loss-threshold AUC = %.4f", lt_auc)

        result.status = "ok"
    except Exception as exc:  # noqa: BLE001
        result.status = "error"
        result.error = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
        LOG.exception("[mia_lira] attack failed")
    finally:
        result.wall_clock_sec = float(time.perf_counter() - t_start)
        with open(out_path, "w") as f:
            json.dump(result.to_dict(), f, indent=2, default=str)
        LOG.info("[mia_lira] wrote %s", out_path)
    return 0 if result.status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
