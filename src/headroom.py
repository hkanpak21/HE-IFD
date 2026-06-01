"""Linear-probe headroom check (issue ft02) — the dataset SELECTION CRITERION.

A task earns a place in the fine-tuning experiments only if a frozen-backbone
**linear probe cannot already solve it**. CIFAR-10 on ViT-B/32 fails this test
(linear-probe ≈ 0.97 ⇒ no headroom ⇒ the fine-tuning lift is invisible, which is
the whole problem the pivot fixes). This module measures, per ``(backbone,
dataset)``:

  * ``train_acc`` / ``test_acc`` of a LINEAR PROBE (a single ``nn.Linear`` head)
    fit on the FROZEN features the protocol would use — i.e. exactly the cached
    ``_load_features`` tensors, same z-score standardization, same in_dim. The
    probe is trained with the repo's own SGD trainer (``teacher.train_supervised_model``)
    so the number is apples-to-apples with the protocol's ``theta0`` / oracle head.
  * a ``HEADROOM`` verdict: ``test_acc < ceiling`` (default 0.90) ⇒ the task is
    NOT linear-probe-solved ⇒ KEEP it; ``test_acc ≥ ceiling`` ⇒ DROP it (too easy,
    like ViT/CIFAR-10). The gap ``1 − test_acc`` is the headroom the fine-tuning
    trajectory has to work with.

It reuses ``protocol._load_features`` so EVERY registered backbone (vision or
text, old or new) is checkable through one path, and the frozen features are
computed-once / cached-offline exactly as the sweep consumes them. It also emits
a ``partition_diagnostic.jsonl`` (the issue's acceptance item) by running the
existing seed-keyed Dirichlet partition on each dataset, proving the new loaders
flow through the unchanged partition machinery.

GOLDEN RULE: this loads torch + the frozen extractors, so it runs ONLY on a
compute node (``sbatch jobs/ft02_headroom.sh``), never on the login node. The
login node's job is the one-time dataset/weight prefetch.

CLI (compute node)::

    python -m src.headroom \
        --backbones vit_b32_cub200,vit_b32_fgvc_aircraft,roberta_base_banking77 \
        --case ft02_headroom --probe-epochs 50 --ceiling 0.90

Each (backbone) prints ONE Colab-paste-ready CSV row:

    backbone,dataset,num_classes,n_train,n_test,train_acc,test_acc,headroom,verdict
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

# ``_load_features`` already applies the backbone's z-score standardization
# inside the ``text:`` branch, so the probe sees exactly the protocol's features.
from .protocol import BACKBONES, _load_features


# CSV header for the headroom table (Colab-paste-clean: one header, comma rows).
HEADROOM_CSV_FIELDS = [
    "backbone", "dataset", "num_classes", "n_train", "n_test",
    "train_acc", "test_acc", "headroom", "verdict",
]


def linear_probe_headroom(
    backbone: str,
    *,
    probe_epochs: int = 50,
    probe_lr: float = 0.01,
    bs: int = 256,
    seed: int = 42,
    ceiling: float = 0.90,
    data_root: str = "data",
    cache_root: str = "cache",
) -> Dict:
    """Fit a linear probe on a backbone's FROZEN features; return a headroom row.

    The probe is the legacy single-Linear head (``trainable_scope='head_only'``)
    on the SAME cached features ``_load_features`` hands the protocol — including
    the backbone's z-score standardization — so ``test_acc`` is directly the
    protocol's standalone linear-probe ceiling. Trains the probe on ALL train
    features (no probe/pool reservation: this is a ceiling measurement, not a
    federated cell) with the repo's SGD trainer.

    Returns a dict with the ``HEADROOM_CSV_FIELDS`` keys plus ``status``/``error``.
    ``verdict`` is ``"KEEP"`` when ``test_acc < ceiling`` (headroom exists), else
    ``"DROP"`` (linear-probe-solved — too easy, like ViT/CIFAR-10).
    """
    import torch

    from .evaluate import accuracy_on
    from .teacher import train_supervised_model

    spec = BACKBONES[backbone]
    row: Dict = {
        "backbone": backbone, "dataset": None, "num_classes": spec.num_classes,
        "n_train": None, "n_test": None, "train_acc": None, "test_acc": None,
        "headroom": None, "verdict": None, "status": "success", "error": None,
    }
    try:
        # head_only ⇒ the legacy linear head: this measures the LINEAR-PROBE
        # ceiling specifically (NOT LoRA / MLP capacity), the selection criterion.
        Xtr, ytr, Xte, yte, in_dim, head_factory = _load_features(
            spec, data_root, cache_root, trainable_scope="head_only")
        row["n_train"] = int(Xtr.shape[0])
        row["n_test"] = int(Xte.shape[0])

        device = "cuda" if torch.cuda.is_available() else "cpu"
        Xte_dev, yte_dev = Xte.to(device), yte.to(device)

        def make_model_fn():
            return head_factory(in_dim, spec.num_classes)

        probe = train_supervised_model(
            make_model_fn, Xtr, ytr,
            epochs=probe_epochs, lr=probe_lr, momentum=0.9, bs=bs,
            seed=seed, lr_schedule=spec.teacher_lr_schedule,
        )
        train_acc = accuracy_on(probe, Xtr.to(device), ytr.to(device))
        test_acc = accuracy_on(probe, Xte_dev, yte_dev)
        row["train_acc"] = round(float(train_acc), 4)
        row["test_acc"] = round(float(test_acc), 4)
        row["headroom"] = round(1.0 - float(test_acc), 4)
        row["verdict"] = "KEEP" if test_acc < ceiling else "DROP"
    except Exception as e:  # noqa: BLE001 — report, never crash the whole sweep
        row["status"] = "fail"
        row["error"] = f"{type(e).__name__}: {e}"
    return row


def emit_partition_diagnostic(
    backbone: str,
    out_path: Path,
    *,
    Ns: List[int],
    alphas: List[float],
    seed: int = 42,
    data_root: str = "data",
    cache_root: str = "cache",
) -> int:
    """Append per-(N, α) Dirichlet partition diagnostics for one backbone.

    Proves the new datasets flow through the UNCHANGED seed-keyed partition
    machinery (``data.partition_pool`` / ``per_client_per_class_counts``). One
    JSONL line per (N, α): the per-client total + per-client per-class counts,
    same schema as ``report.write_partition_jsonl``. Returns the line count
    written (0 on a load failure, which is logged but not raised).
    """
    from .data import (
        partition_pool,
        per_client_per_class_counts,
        reserve_probe_and_pool,
    )

    spec = BACKBONES[backbone]
    try:
        Xtr, ytr, _Xte, _yte, _in_dim, _hf = _load_features(
            spec, data_root, cache_root, trainable_scope="head_only")
    except Exception as e:  # noqa: BLE001
        print(f"[headroom] partition-diag SKIP {backbone}: {type(e).__name__}: {e}",
              flush=True)
        return 0

    nc = spec.num_classes
    probe_size = spec.labelled_probe_default
    n_written = 0
    with open(out_path, "a") as f:
        for N in Ns:
            for alpha in alphas:
                _pX, _py, pool_X, pool_y = reserve_probe_and_pool(
                    Xtr, ytr, probe_size, seed)
                client_X_list, client_y_list, sample_sizes = partition_pool(
                    pool_X, pool_y, N, alpha, seed, nc)
                per_client_per_class = per_client_per_class_counts(client_y_list, nc)
                totals = [int(s) for s in sample_sizes]
                denom = sum(totals) or 1
                weights = [t / denom for t in totals]
                f.write(json.dumps({
                    "backbone": backbone, "dataset": spec.label,
                    "N": N, "alpha": alpha, "seed": seed,
                    "num_classes": nc,
                    "per_client_total": totals,
                    "per_client_per_class": per_client_per_class,
                    "sample_weights": weights,
                }) + "\n")
                n_written += 1
    return n_written


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Linear-probe headroom check (ft02 dataset selection criterion).")
    p.add_argument("--backbones", type=str,
                   default="vit_b32_cub200,vit_b32_stanford_cars,"
                           "vit_b32_fgvc_aircraft,roberta_base_banking77,"
                           "mpnet_st_banking77,roberta_base_20news,"
                           "roberta_base_trec",
                   help=f"Comma list from {sorted(BACKBONES)}.")
    p.add_argument("--case", type=str, default="ft02_headroom",
                   help="Case slug -> results/<case>/.")
    p.add_argument("--results-root", type=str, default="results")
    p.add_argument("--data-root", type=str, default="data")
    p.add_argument("--cache-root", type=str, default="cache")
    p.add_argument("--probe-epochs", type=int, default=50)
    p.add_argument("--probe-lr", type=float, default=0.01)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--ceiling", type=float, default=0.90,
                   help="test_acc >= ceiling ⇒ DROP (linear-probe-solved, too "
                        "easy like ViT/CIFAR-10); < ceiling ⇒ KEEP (headroom).")
    p.add_argument("--partition-Ns", type=str, default="10,20",
                   help="Client counts for the partition_diagnostic.jsonl emit.")
    p.add_argument("--partition-alphas", type=str, default="0.05,0.1,1.0",
                   help="Dirichlet alphas for the partition_diagnostic.jsonl emit.")
    return p.parse_args()


def _csv_row(row: Dict) -> str:
    return ",".join(str(row.get(k, "")) for k in HEADROOM_CSV_FIELDS)


def main() -> None:
    args = parse_args()
    results_dir = Path(args.results_root) / args.case
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "runs").mkdir(exist_ok=True)

    backbones = [b.strip() for b in args.backbones.split(",") if b.strip()]
    Ns = [int(x) for x in args.partition_Ns.split(",") if x.strip()]
    alphas = [float(x) for x in args.partition_alphas.split(",") if x.strip()]

    # Fresh partition diagnostic for this run (append-mode within, truncate first).
    part_path = results_dir / "partition_diagnostic.jsonl"
    if part_path.exists():
        part_path.unlink()

    rows: List[Dict] = []
    print("[headroom] " + ",".join(HEADROOM_CSV_FIELDS), flush=True)
    for backbone in backbones:
        row = linear_probe_headroom(
            backbone, probe_epochs=args.probe_epochs, probe_lr=args.probe_lr,
            seed=args.seed, ceiling=args.ceiling,
            data_root=args.data_root, cache_root=args.cache_root,
        )
        # The dataset label comes from the registry (BackboneSpec.label segment).
        row["dataset"] = BACKBONES[backbone].label
        rows.append(row)
        print(_csv_row(row), flush=True)
        emit_partition_diagnostic(
            backbone, part_path, Ns=Ns, alphas=alphas, seed=args.seed,
            data_root=args.data_root, cache_root=args.cache_root,
        )

    # Persist: the paste-ready CSV (header + rows) and the raw JSON rows.
    csv_path = results_dir / "headroom.csv"
    with open(csv_path, "w") as f:
        f.write(",".join(HEADROOM_CSV_FIELDS) + "\n")
        for r in rows:
            f.write(_csv_row(r) + "\n")
    (results_dir / "headroom.json").write_text(json.dumps(rows, indent=2))

    kept = [r["backbone"] for r in rows if r.get("verdict") == "KEEP"]
    dropped = [r["backbone"] for r in rows if r.get("verdict") == "DROP"]
    failed = [r["backbone"] for r in rows if r.get("status") != "success"]
    print(f"[headroom] done. KEEP={kept} DROP={dropped} FAILED={failed}. "
          f"csv at {csv_path}, partition at {part_path}", flush=True)


if __name__ == "__main__":
    main()
