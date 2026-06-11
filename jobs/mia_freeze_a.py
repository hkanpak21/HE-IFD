#!/usr/bin/env python
"""fa02 — full MIA suite against the freeze-A released model (issue fa02).

Backs the response-to-reviewers promise (R1-W4/R2-Q5): membership inference is
measured on THE method being submitted, not on the superseded distillation-era
model. Target and every shadow are trained through the REAL federated pipeline
(freeze-A LoRA + head, Dirichlet partition, bounded K-step trajectories,
depth-1 plain aggregate) so the shadow distribution matches the release.

Per cell (= task x seed):
  1. Fix an attack pool of P train examples (seed-keyed).
  2. Train 1 target + n_shadows shadow models; model m trains on a random half
     of the pool (IN set), federated across N clients.  Each model checkpoints
     its tiny per-example statistics (in-mask, loss, conf, phi) to an .npz the
     moment it finishes — a killed job resumes at the next model.
  3. Score: external adversary (Yeom threshold + LiRA) and the fellow-client
     adversary (class-conditional calibrated threshold + LiRA — the adversary
     our threat model actually permits, so it is the headline attack).

CSV (canonical MIA schema):
  backbone,N,alpha,method,seed,surface,attack,tpr_at_0.1pct,tpr_at_1pct,auc

Run from the repo root (sbatch jobs/mia_freeze_a.sh): imports the federated
core from jobs/finetune_improve.py and the attack machinery from mia/.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "jobs"))

import finetune_improve as FI  # noqa: E402  — the federated core (freeze-A era)
from mia import attacks as A   # noqa: E402
from mia import surfaces as S  # noqa: E402

CASE = "heifd_mia_freeze_a"
OUTDIR = REPO / "results" / CASE
OUTDIR.mkdir(parents=True, exist_ok=True)

TASKS = ["ag_news", "trec", "dbpedia_14", "banking77"]
SEEDS = [42, 43, 44]


# ---------------------------------------------------------------------------
# Per-model statistics on the attack pool
# ---------------------------------------------------------------------------
@torch.no_grad()
def pool_stats(model, ids, mask, y, bs=256):
    """Per-example (loss, true-class conf, LiRA phi) of one released model."""
    model.eval()
    yt = torch.as_tensor(y)
    losses, confs = [], []
    for s in range(0, len(y), bs):
        lo = model(ids[s:s + bs].to(FI.DEVICE), mask[s:s + bs].to(FI.DEVICE)).cpu()
        yb = yt[s:s + bs]
        losses.append(F.cross_entropy(lo, yb, reduction="none"))
        p = F.softmax(lo, dim=1)
        confs.append(p[torch.arange(len(yb)), yb])
    loss = torch.cat(losses).numpy().astype(np.float64)
    conf = torch.cat(confs).numpy().astype(np.float64)
    p = np.clip(conf, 1e-12, 1 - 1e-12)
    phi = np.log(p) - np.log(1.0 - p)          # LiRA logit-scaled confidence
    return loss, conf, phi


def train_released_model(task, backbone, in_idx, y_pool, ids_pool, mask_pool,
                         N, alpha, seed, model_seed, K, lr, bs, r, freeze_a,
                         sem_init, C, agg="count_head"):
    """One federated run on the IN half of the pool -> the released theta*.

    ``agg`` selects the released aggregate. Default ``count_head`` — the modal
    client-vote winner across the fa01 program — so the attacked artifact is
    the one the protocol actually releases; ``plain`` is the λ=1 average."""
    head_init = None
    if sem_init:
        hk = (task, backbone)
        if hk not in FI._SEMHEAD:
            FI._SEMHEAD[hk] = FI.semantic_head_init(backbone, task)
        head_init = FI._SEMHEAD[hk]
    FI.set_seed(seed)                  # theta0 (LoRA A, head) is the PUBLIC init
    model = FI.TextLoRA(backbone, C, r=r, freeze_a=freeze_a,
                        head_init=head_init).to(FI.DEVICE)
    theta0 = FI.trainable_state(model)

    y_in = y_pool[in_idx]
    parts_local = FI.dirichlet_partition(y_in, N, alpha, C, model_seed)
    parts = [in_idx[p] if len(p) else p for p in parts_local]
    deltas, sizes, counts = [], [], []
    for ci in parts:
        if len(ci) == 0:
            deltas.append({k: torch.zeros_like(v) for k, v in theta0.items()})
            counts.append(np.zeros(C)); sizes.append(0); continue
        FI.load_trainable(model, theta0)
        FI.train_steps(model, ids_pool[ci], mask_pool[ci], y_pool[ci],
                       steps=K, lr=lr, bs=bs)
        st = FI.trainable_state(model)
        deltas.append({k: st[k] - theta0[k] for k in theta0})
        counts.append(np.bincount(y_pool[ci], minlength=C).astype(np.float64))
        sizes.append(int(len(ci)))
    tot = max(sum(sizes), 1)
    w = [s / tot for s in sizes]
    if agg == "count_head":
        st = FI.agg_count_head(theta0, deltas, w, counts)
    else:
        st = FI.agg_plain(theta0, deltas, w, lam=1.0)
    FI.load_trainable(model, st)
    return model


def run_cell(task, seed, backbone="roberta_base", N=10, alpha=0.1, K=200,
             lr=5e-4, bs=32, r=8, freeze_a=True, sem_init=False,
             n_shadows=16, pool_size=6000, agg="count_head"):
    method = f"freeze_a_lora_r{r}_{agg}" + ("_sem" if sem_init else "")
    cell = OUTDIR / f"cell_{task}_{backbone}_N{N}_a{alpha}_{method}_s{seed}.json"
    if cell.exists():
        row = json.loads(cell.read_text())
        print(f"skip (done): {cell.name}", flush=True)
        return row

    ids_tr, mask_tr, ytr, ids_te, mask_te, yte, C = FI._data(task, backbone, seed)
    P = min(pool_size, len(ytr))
    pool = np.arange(P)                # load_text already seed-shuffles the sample
    ids_p, mask_p, y_p = ids_tr[:P], mask_tr[:P], ytr[:P]

    sdir = OUTDIR / "shadows" / f"{task}_{method}_s{seed}"
    sdir.mkdir(parents=True, exist_ok=True)

    n_models = n_shadows + 1           # model 0 = the target
    for m in range(n_models):
        ck = sdir / f"model_{m:04d}.npz"
        if ck.exists():
            continue
        t = time.time()
        rng = np.random.default_rng(seed * 10007 + m)
        in_mask = rng.random(P) < 0.5
        in_idx = pool[in_mask]
        model = train_released_model(
            task, backbone, in_idx, y_p, ids_p, mask_p, N, alpha, seed,
            model_seed=seed * 10007 + m, K=K, lr=lr, bs=bs, r=r,
            freeze_a=freeze_a, sem_init=sem_init, C=C, agg=agg)
        loss, conf, phi = pool_stats(model, ids_p, mask_p, y_p)
        acc = FI.evaluate(model, ids_te, mask_te, yte)
        np.savez_compressed(ck, in_mask=in_mask, loss=loss, conf=conf,
                            phi=phi, test_acc=acc)
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print(f"  model {m}/{n_models - 1} ({'target' if m == 0 else 'shadow'}) "
              f"acc={acc:.3f} ({time.time() - t:.0f}s)", flush=True)

    # ---- scoring (cheap; reads the checkpoints) ----
    d0 = np.load(sdir / "model_0000.npz")
    labels = d0["in_mask"].astype(np.int64)
    shadow_phi = np.stack([np.load(sdir / f"model_{m:04d}.npz")["phi"]
                           for m in range(1, n_models)])
    shadow_in = np.stack([np.load(sdir / f"model_{m:04d}.npz")["in_mask"]
                          for m in range(1, n_models)])

    external = {
        "threshold": A.threshold_attack(d0["loss"], labels),
        "lira": A.lira_attack(d0["phi"], shadow_phi, shadow_in, labels),
    }
    fellow = S.score_fellow(d0["loss"], d0["phi"], shadow_phi, shadow_in,
                            labels, y_p, C)

    def slim(res):                     # drop ROC arrays from the headline dict
        return {k: v for k, v in res.items() if not k.startswith("roc_")}

    row = dict(task=task, backbone=backbone, N=N, alpha=alpha, method=method,
               seed=seed, n_shadows=n_shadows, pool_size=P,
               target_test_acc=float(d0["test_acc"]),
               external={k: slim(v) for k, v in external.items()},
               fellow={k: slim(v) for k, v in fellow.items()},
               roc={f"external_{k}": {kk: v[kk] for kk in ("roc_fpr", "roc_tpr")}
                    for k, v in external.items()})
    cell.write_text(json.dumps(row))
    print(f"ok {task} s{seed} | ext: thr.auc={external['threshold']['auc']:.3f} "
          f"lira.auc={external['lira']['auc']:.3f} | fellow: "
          f"lira.auc={fellow['lira']['auc']:.3f}", flush=True)
    return row


CSV_HEADER = "backbone,N,alpha,method,seed,surface,attack,tpr_at_0.1pct,tpr_at_1pct,auc"


def csv_rows(row):
    out = []
    for surface, attset in (("external", row["external"]), ("fellow", row["fellow"])):
        for att, res in attset.items():
            out.append(",".join(str(x) for x in (
                row["backbone"], row["N"], row["alpha"], row["method"],
                row["seed"], surface, att,
                round(res.get("tpr_at_fpr_0.001", float("nan")), 4),
                round(res.get("tpr_at_fpr_0.01", float("nan")), 4),
                round(res["auc"], 4))))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cell-index", type=int, default=None,
                    help="index into TASKS x SEEDS (one cell per <=3h job); "
                         "omit to run all cells serially")
    ap.add_argument("--n-shadows", type=int, default=16)
    ap.add_argument("--pool-size", type=int, default=6000)
    ap.add_argument("--sem-init", action="store_true")
    ap.add_argument("--r", type=int, default=8)
    ap.add_argument("--agg", default="count_head", choices=["count_head", "plain"])
    args = ap.parse_args()

    cells = [(t, s) for t in TASKS for s in SEEDS]
    if args.cell_index is not None:
        cells = [cells[args.cell_index]]
    print(f"[mia_freeze_a] device={FI.DEVICE} cells={len(cells)}", flush=True)

    rows = []
    for task, seed in cells:
        try:
            rows.append(run_cell(task, seed, r=args.r, sem_init=args.sem_init,
                                 agg=args.agg,
                                 n_shadows=args.n_shadows,
                                 pool_size=args.pool_size))
        except Exception as e:  # noqa: BLE001
            import traceback
            (OUTDIR / f"FAIL_{task}_s{seed}.txt").write_text(traceback.format_exc())
            print(f"FAIL {task} s{seed}: {e}", flush=True)

    print("\n===== BEGIN results.csv =====", flush=True)
    print(CSV_HEADER)
    for r in rows:
        for line in csv_rows(r):
            print(line)
    print("===== END results.csv =====\n", flush=True)


if __name__ == "__main__":
    main()
