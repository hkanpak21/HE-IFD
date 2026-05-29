"""Resumable, chunkable MIA runner — the only entrypoint sbatch runs.

Pipeline per cell (one backbone × N × α × method × seed):

  1. Load features once (``mia.target.load_features`` → ``src.protocol``).
  2. Fix the LiRA attack pool (``make_attack_pool``).
  3. Train the TARGET global model + ``n_shadows`` shadow models, each on a
     random half of the pool (``train_global_model``, reusing ``src/``).
  4. Once all shadows exist, run the three surfaces (``mia.surfaces``) and write
     the per-cell JSON (``mia.report``).

Resumability + 3h cap (the heavy cost is shadow-model training):

* **Per-model checkpoint.** Each shadow model's contribution to the attack is
  its IN/OUT mask over the pool + its φ/loss/conf vectors AND its surrogate φ.
  These are tiny (a few floats per pool example), so we checkpoint each model to
  ``shadows/<cell>/model_<idx>.npz`` immediately after training. A job that dies
  mid-sweep resumes by skipping models whose checkpoint already exists.
* **Model-level chunking.** ``--num-chunks`` / ``--chunk-index`` (or env
  NUM_CHUNKS / CHUNK_INDEX) split the (target + shadows) model list ACROSS jobs:
  each job trains only its slice of models and writes their checkpoints. The
  FINAL job (or a cheap scoring-only pass, ``--score-only``) reads all
  checkpoints and runs the attacks. So a cell needing 64 shadows × a few-minute
  train fits in many ≤3h jobs; no single job exceeds the cap.
* **Cell-level chunking.** Multiple cells can also be split with the same flags
  when each cell is itself cheap.

The chunking unit is therefore the MODEL (target counts as model index 0). This
is the right granularity because shadow training dominates wall-clock and is
embarrassingly parallel across models.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from . import report as R
from . import surfaces as S
from .target import (
    Features, GlobalModel, TargetConfig, in_out_mask, load_features,
    make_attack_pool, model_confidences, train_global_model,
)


# ---------------------------------------------------------------------------
# Per-model checkpoint I/O (the resume unit)
# ---------------------------------------------------------------------------
def _shadow_dir(results_dir: Path, slug: str, seed: int) -> Path:
    d = results_dir / "shadows" / f"{slug}_s{seed}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _ckpt_path(sdir: Path, model_idx: int) -> Path:
    # model_idx 0 == the target; >=1 == shadow models.
    return sdir / f"model_{model_idx:04d}.npz"


def _train_and_checkpoint_model(
    model_idx: int,
    feats: Features,
    cfg: TargetConfig,
    pool_X,
    pool_y,
    cell_seed: int,
    sdir: Path,
    glira_steps: int,
    glira_lr: float,
    glira_tau: float,
    glira_query_size: int,
    force: bool = False,
) -> bool:
    """Train one model (target if idx 0) and checkpoint its attack contributions.

    Returns True if it (re)trained, False if a checkpoint was reused. The
    checkpoint stores: the IN mask over the pool, the model's φ/loss/conf on the
    pool, and its GLiRA surrogate φ on the pool. That is everything the attacks
    need — we never reload model weights for scoring, only these vectors.
    """
    cpath = _ckpt_path(sdir, model_idx)
    if cpath.exists() and not force:
        try:
            np.load(cpath)  # integrity check
            return False
        except (OSError, ValueError):
            pass  # corrupt → retrain

    pool_size = int(pool_X.shape[0])
    # Target uses the cell seed; shadows use distinct per-model seeds so their
    # IN/OUT halves differ. Determinism makes the split resume-stable.
    model_seed = cell_seed if model_idx == 0 else (cell_seed * 100003 + model_idx)
    in_mask = in_out_mask(pool_size, model_seed)
    gm = train_global_model(feats, cfg, pool_X, pool_y, in_mask, model_seed)

    conf = model_confidences(gm.params, feats.make_model_fn, pool_X, pool_y)
    # GLiRA surrogate φ (distil from this model's query outputs).
    query_X = feats.Xte[:glira_query_size]
    surr = S.distill_surrogate(
        gm.params, feats, cfg, query_X, seed=model_idx + 1,
        steps=glira_steps, lr=glira_lr, tau=glira_tau)
    surr_conf = model_confidences(surr, feats.make_model_fn, pool_X, pool_y)

    np.savez_compressed(
        cpath,
        in_mask=in_mask,
        phi=conf["logit_scaled"].astype(np.float32),
        loss=conf["loss"].astype(np.float32),
        conf=conf["conf"].astype(np.float32),
        surrogate_phi=surr_conf["logit_scaled"].astype(np.float32),
        model_idx=np.int64(model_idx),
    )
    return True


def _load_ckpt(sdir: Path, model_idx: int) -> Optional[Dict]:
    cpath = _ckpt_path(sdir, model_idx)
    if not cpath.exists():
        return None
    try:
        d = np.load(cpath)
        return {k: d[k] for k in d.files}
    except (OSError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Scoring from checkpoints (no model retraining)
# ---------------------------------------------------------------------------
def _score_cell_from_ckpts(
    feats: Features, cfg: TargetConfig, pool_X, pool_y, cell_seed: int,
    sdir: Path, prototype_K_per_class: int,
) -> Optional[Dict]:
    """Run the three surfaces from per-model checkpoints. None if incomplete."""
    n_total = cfg.n_shadows + 1  # +1 target
    ckpts = [_load_ckpt(sdir, i) for i in range(n_total)]
    if any(c is None for c in ckpts):
        missing = [i for i, c in enumerate(ckpts) if c is None]
        print(f"[mia] scoring deferred: {len(missing)} model checkpoints "
              f"missing (e.g. {missing[:5]}).", flush=True)
        return None

    pool_size = int(pool_X.shape[0])
    target_ck = ckpts[0]
    shadow_cks = ckpts[1:]

    labels = np.zeros(pool_size, dtype=np.int64)
    labels[target_ck["in_mask"]] = 1

    shadow_phi = np.stack([c["phi"] for c in shadow_cks]).astype(np.float64)
    shadow_surr_phi = np.stack([c["surrogate_phi"] for c in shadow_cks]).astype(np.float64)
    shadow_in = np.stack([c["in_mask"] for c in shadow_cks]).astype(bool)

    t_loss = target_ck["loss"].astype(np.float64)
    t_phi = target_ck["phi"].astype(np.float64)
    t_surr_phi = target_ck["surrogate_phi"].astype(np.float64)
    pool_y_np = pool_y.cpu().numpy() if hasattr(pool_y, "cpu") else np.asarray(pool_y)

    surfaces: Dict = {}
    # External: threshold + LiRA (θ⋆ own φ) + GLiRA (surrogate φ).
    surfaces["external"] = S.score_external(
        t_loss, t_phi, t_surr_phi, shadow_phi, shadow_surr_phi, shadow_in, labels)
    # Fellow: class-conditional calibration on the shadow OUT population.
    surfaces["fellow"] = S.score_fellow(
        t_loss, t_phi, shadow_phi, shadow_in, labels, pool_y_np, feats.num_classes)

    # Prototype channel: reconstruct the release from the TARGET's members.
    target_gm = GlobalModel(
        params={}, theta0={}, prototypes=None,
        in_idx=np.where(target_ck["in_mask"])[0], sample_sizes=[])
    surfaces["prototype"] = S.run_prototype_surface(
        target_gm, feats, cfg, pool_X, pool_y,
        K_per_class=prototype_K_per_class, seed=cell_seed)

    return surfaces


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_list(s: str, typ=str):
    out = []
    for x in s.split(","):
        x = x.strip()
        if not x:
            continue
        out.append(float("inf") if (typ is float and x in ("inf", "Inf")) else typ(x))
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Resumable, chunkable HE-IFD MIA suite.")
    p.add_argument("--backbones", default="mlp_mnist",
                   help="Comma list: mlp_mnist, vit_b32_cifar100.")
    p.add_argument("--Ns", default="10")
    p.add_argument("--alphas", default="0.05,1.0")
    p.add_argument("--methods", default="raw_union_K20",
                   help="Phase-0 method under attack (the released-model config).")
    p.add_argument("--seeds", default="42")
    p.add_argument("--n-shadows", type=int, default=64)
    p.add_argument("--attack-pool-size", type=int, default=5000)
    p.add_argument("--K", type=int, default=None, help="Override distill K.")
    p.add_argument("--tau", type=float, default=None)
    p.add_argument("--student-lr", type=float, default=None)
    p.add_argument("--probe-size", type=int, default=None)
    p.add_argument("--prototype-K-per-class", type=int, default=20)
    # GLiRA surrogate distillation knobs.
    p.add_argument("--glira-steps", type=int, default=200)
    p.add_argument("--glira-lr", type=float, default=0.01)
    p.add_argument("--glira-tau", type=float, default=1.0)
    p.add_argument("--glira-query-size", type=int, default=2000)
    # I/O
    p.add_argument("--case", default="heifd_021_mia")
    p.add_argument("--results-root", default="results")
    p.add_argument("--data-root", default="data")
    p.add_argument("--cache-root", default="cache")
    # chunking (over MODELS within a cell)
    p.add_argument("--num-chunks", type=int,
                   default=int(os.environ.get("NUM_CHUNKS", "1")))
    p.add_argument("--chunk-index", type=int,
                   default=int(os.environ.get("CHUNK_INDEX", "0")))
    p.add_argument("--score-only", action="store_true",
                   help="Skip training; only score cells whose checkpoints are "
                        "all present, and (re)write the report.")
    p.add_argument("--force", action="store_true",
                   help="Retrain models even if a checkpoint exists.")
    return p.parse_args()


def build_cells(args) -> List[TargetConfig]:
    cells: List[TargetConfig] = []
    for bb in parse_list(args.backbones, str):
        for N in parse_list(args.Ns, int):
            for a in parse_list(args.alphas, float):
                for meth in parse_list(args.methods, str):
                    cfg = TargetConfig.with_kd_defaults(
                        bb, N=N, alpha=a, method=meth,
                        K=args.K, tau=args.tau, student_lr=args.student_lr,
                        probe_size=args.probe_size,
                        attack_pool_size=args.attack_pool_size,
                        n_shadows=args.n_shadows)
                    cells.append(cfg)
    return cells


def select_model_chunk(n_models: int, num_chunks: int, chunk_index: int) -> List[int]:
    """Round-robin slice of model indices [0, n_models) for this job."""
    if num_chunks <= 1:
        return list(range(n_models))
    return [i for i in range(n_models) if i % num_chunks == chunk_index]


def main() -> None:
    args = parse_args()
    job_id = os.environ.get("SLURM_JOB_ID")
    results_dir = Path(args.results_root) / args.case
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "runs").mkdir(exist_ok=True)

    cells = build_cells(args)
    seeds = parse_list(args.seeds, int)
    print(f"[mia] {len(cells)} cell-configs × {len(seeds)} seeds; "
          f"n_shadows={args.n_shadows}; chunk {args.chunk_index}/{args.num_chunks}; "
          f"job={job_id}", flush=True)

    for cfg in cells:
        for seed in seeds:
            slug = R.cell_slug(cfg.backbone, cfg.N, cfg.alpha, cfg.method)
            print(f"[mia] cell {slug} seed={seed}", flush=True)
            feats = load_features(cfg)
            pool_X, pool_y, _pool_idx = make_attack_pool(feats, cfg, seed=seed)
            sdir = _shadow_dir(results_dir, slug, seed)

            n_total = cfg.n_shadows + 1
            if not args.score_only:
                my_models = select_model_chunk(
                    n_total, args.num_chunks, args.chunk_index)
                n_trained = n_reused = 0
                for midx in my_models:
                    retrained = _train_and_checkpoint_model(
                        midx, feats, cfg, pool_X, pool_y, seed, sdir,
                        args.glira_steps, args.glira_lr, args.glira_tau,
                        args.glira_query_size, force=args.force)
                    if retrained:
                        n_trained += 1
                        print(f"[mia] ok    model {midx}/{n_total-1} trained "
                              f"({slug} s{seed})", flush=True)
                    else:
                        n_reused += 1
                print(f"[mia] cell {slug} s{seed}: trained={n_trained} "
                      f"reused={n_reused} (chunk {args.chunk_index})", flush=True)

            # Score only when every model checkpoint is present (resume-safe).
            surfaces = _score_cell_from_ckpts(
                feats, cfg, pool_X, pool_y, seed, sdir,
                args.prototype_K_per_class)
            if surfaces is not None:
                payload = {
                    "backbone": cfg.backbone, "N": cfg.N, "alpha": cfg.alpha,
                    "method": cfg.method, "seed": seed, "K": cfg.K,
                    "tau": cfg.tau, "student_lr": cfg.student_lr,
                    "n_shadows": cfg.n_shadows,
                    "attack_pool_size": cfg.attack_pool_size,
                    "glira": {"steps": args.glira_steps, "lr": args.glira_lr,
                              "tau": args.glira_tau,
                              "query_size": args.glira_query_size},
                    "job_id": job_id,
                    "surfaces": surfaces,
                }
                R.write_cell(results_dir, slug, seed, payload)
                print(f"[mia] scored cell {slug} s{seed} -> "
                      f"{R.cell_json_path(results_dir, slug, seed).name}",
                      flush=True)

    R.write_report(str(results_dir))
    print(f"[mia] done. report at {results_dir / 'README.md'}", flush=True)


if __name__ == "__main__":
    main()
