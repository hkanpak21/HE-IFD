#!/usr/bin/env python
"""Extended MIA surfaces (paper flow-pass items B.8 + B.9).

Two additions to the released-model MIA of ``jobs/mia_freeze_a.py``:

  B.8  VISION released-model MIA — the exact same attack (external + fellow,
       threshold + LiRA) against the freeze-A ViT-B/16 model on CIFAR-100, so
       the MIA table is no longer text-only. A prior probe saw LiRA AUC ~0.85
       on ViT/CIFAR-100 in the deprecated (both-A-B, distillation) era; this
       re-measures it on the SUBMITTED method.

  B.9  TRAINING-TIME vs INFERENCE-TIME surface — the paper's central storyline
       is that the encrypted contribution (the per-client displacement) is the
       surface worth protecting, while the released model is not. We measure
       both directly on ONE pipeline: for each target we attack (a) the
       released aggregate theta*, the clear inference-time object, and (b) a
       single client's post-fine-tuning model theta0+Delta_j, the object that
       WOULD be exposed in a plaintext protocol and that HE-OFT keeps encrypted.
       The gap between the two AUCs is the quantitative statement of what the
       encryption buys.

Both reuse the shadow/LiRA machinery in ``mia/`` and the federated cores in
``jobs/finetune_improve.py`` (text) and ``jobs/vision_matched.py`` (vision).
Per-model npz checkpoints make every cell resumable at the 3h wall.

CSV (extends the canonical schema with the surface column already present):
  backbone,N,alpha,method,seed,surface,attack,tpr_at_0.1pct,tpr_at_1pct,auc
where surface in {released, update} x {external, fellow}.
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

import finetune_improve as FI       # noqa: E402  text federated core
from mia import attacks as A        # noqa: E402
from mia import surfaces as S       # noqa: E402

CASE = "heifd_mia_surfaces"
OUTDIR = REPO / "results" / CASE
OUTDIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# per-example statistics
# ---------------------------------------------------------------------------
def _phi_from_conf(conf):
    p = np.clip(conf, 1e-12, 1 - 1e-12)
    return np.log(p) - np.log(1.0 - p)


@torch.no_grad()
def text_stats(model, ids, mask, y, bs=256):
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
    return loss, _phi_from_conf(conf)


# ---------------------------------------------------------------------------
# one federated run -> BOTH the released theta* and one client's theta0+Delta_j
# ---------------------------------------------------------------------------
def text_run_two_surfaces(task, backbone, in_idx, y_pool, ids_pool, mask_pool,
                          N, alpha, seed, model_seed, K, lr, bs, r, C):
    """Return (released_model, update_model): the aggregate, and the largest
    client's own fine-tuned model (theta0+Delta_j) — the plaintext-protocol
    leak the encryption removes."""
    FI.set_seed(seed)
    model = FI.TextLoRA(backbone, C, r=r, freeze_a=True).to(FI.DEVICE)
    theta0 = FI.trainable_state(model)
    y_in = y_pool[in_idx]
    parts_local = FI.dirichlet_partition(y_in, N, alpha, C, model_seed)
    parts = [in_idx[p] if len(p) else p for p in parts_local]
    deltas, sizes, counts = [], [], []
    biggest_state = None
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
    # released aggregate (count_head — the modal client-vote winner)
    tot = max(sum(sizes), 1); w = [s / tot for s in sizes]
    st_star = FI.agg_count_head(theta0, deltas, w, counts)
    # the largest client's own model (worst-case single-client exposure)
    j = int(np.argmax(sizes))
    st_update = {k: theta0[k] + deltas[j][k] for k in theta0}

    released = FI.TextLoRA(backbone, C, r=r, freeze_a=True).to(FI.DEVICE)
    FI.load_trainable(released, st_star)
    update = FI.TextLoRA(backbone, C, r=r, freeze_a=True).to(FI.DEVICE)
    FI.load_trainable(update, st_update)
    return released, update, j


def score_pair(sdir, n_models, y_p, C, key):
    """Score one surface's checkpoints (target = model 0). ``key`` in
    {'star','update'} selects which phi/loss arrays to read."""
    d0 = np.load(sdir / "model_0000.npz")
    labels = d0["in_mask"].astype(np.int64)
    sp = np.stack([np.load(sdir / f"model_{m:04d}.npz")[f"phi_{key}"]
                   for m in range(1, n_models)])
    sl = np.stack([np.load(sdir / f"model_{m:04d}.npz")[f"loss_{key}"]
                   for m in range(1, n_models)])
    si = np.stack([np.load(sdir / f"model_{m:04d}.npz")["in_mask"]
                   for m in range(1, n_models)])
    external = {
        "threshold": A.threshold_attack(d0[f"loss_{key}"], labels),
        "lira": A.lira_attack(d0[f"phi_{key}"], sp, si, labels),
    }
    fellow = S.score_fellow(d0[f"loss_{key}"], d0[f"phi_{key}"], sp, si,
                            labels, y_p, C, shadow_loss=sl)
    return external, fellow


def run_text_cell(task, seed, backbone="roberta_base", N=10, alpha=0.1, K=200,
                  lr=5e-4, bs=32, r=8, n_shadows=16, pool_size=6000):
    method = f"freeze_a_lora_r{r}_twosurface"
    cell = OUTDIR / f"cell_{task}_{backbone}_N{N}_a{alpha}_{method}_s{seed}.json"
    if cell.exists():
        print(f"skip (done): {cell.name}", flush=True)
        return json.loads(cell.read_text())

    ids_tr, mask_tr, ytr, ids_te, mask_te, yte, C = FI._data(task, backbone, seed)
    P = min(pool_size, len(ytr))
    ids_p, mask_p, y_p = ids_tr[:P], mask_tr[:P], ytr[:P]
    sdir = OUTDIR / "shadows" / f"{task}_{method}_s{seed}"
    sdir.mkdir(parents=True, exist_ok=True)

    n_models = n_shadows + 1
    for m in range(n_models):
        ck = sdir / f"model_{m:04d}.npz"
        if ck.exists():
            continue
        t = time.time()
        rng = np.random.default_rng(seed * 10007 + m)
        in_mask = rng.random(P) < 0.5
        in_idx = np.arange(P)[in_mask]
        released, update, j = text_run_two_surfaces(
            task, backbone, in_idx, y_p, ids_p, mask_p, N, alpha, seed,
            model_seed=seed * 10007 + m, K=K, lr=lr, bs=bs, r=r, C=C)
        loss_star, phi_star = text_stats(released, ids_p, mask_p, y_p)
        loss_upd, phi_upd = text_stats(update, ids_p, mask_p, y_p)
        acc = FI.evaluate(released, ids_te, mask_te, yte)
        np.savez_compressed(ck, in_mask=in_mask, loss_star=loss_star,
                            phi_star=phi_star, loss_update=loss_upd,
                            phi_update=phi_upd, test_acc=acc, attacker=j)
        del released, update
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print(f"  model {m}/{n_models-1} acc={acc:.3f} ({time.time()-t:.0f}s)",
              flush=True)

    ext_s, fel_s = score_pair(sdir, n_models, y_p, C, "star")
    ext_u, fel_u = score_pair(sdir, n_models, y_p, C, "update")
    row = _row(task, backbone, N, alpha, method, seed, n_shadows, P,
               released={"external": ext_s, "fellow": fel_s},
               update={"external": ext_u, "fellow": fel_u})
    cell.write_text(json.dumps(row))
    print(f"ok {task} s{seed} | released LiRA={ext_s['lira']['auc']:.3f} "
          f"update LiRA={ext_u['lira']['auc']:.3f}", flush=True)
    return row


# ---------------------------------------------------------------------------
# vision (B.8 + B.9 on ViT/CIFAR-100)
# ---------------------------------------------------------------------------
def run_vision_cell(seed, N=10, alpha=0.1, K=200, lr=5e-4, bs=32, r=8,
                    n_shadows=16, pool_size=5000, dataset="cifar100"):
    import vision_matched as VM       # noqa: E402  vision federated core
    method = f"freeze_a_vit_r{r}_twosurface"
    cell = OUTDIR / f"cell_{dataset}_vit_b16_N{N}_a{alpha}_{method}_s{seed}.json"
    if cell.exists():
        print(f"skip (done): {cell.name}", flush=True)
        return json.loads(cell.read_text())

    Xtr, ytr, Xte, yte, C = VM.load_vision(dataset, max_train=pool_size,
                                           max_test=2000, seed=seed)
    P = len(ytr)
    y_p = ytr
    sdir = OUTDIR / "shadows" / f"{dataset}_{method}_s{seed}"
    sdir.mkdir(parents=True, exist_ok=True)

    @torch.no_grad()
    def vstats(model):
        model.eval()
        losses, confs = [], []
        yt = torch.as_tensor(y_p)
        for s in range(0, P, 128):
            lo = model(VM.prep(Xtr[s:s + 128])).cpu()
            yb = yt[s:s + 128]
            losses.append(F.cross_entropy(lo, yb, reduction="none"))
            p = F.softmax(lo, dim=1)
            confs.append(p[torch.arange(len(yb)), yb])
        loss = torch.cat(losses).numpy().astype(np.float64)
        conf = torch.cat(confs).numpy().astype(np.float64)
        return loss, _phi_from_conf(conf)

    n_models = n_shadows + 1
    for m in range(n_models):
        ck = sdir / f"model_{m:04d}.npz"
        if ck.exists():
            continue
        t = time.time()
        rng = np.random.default_rng(seed * 10007 + m)
        in_mask = rng.random(P) < 0.5
        in_idx = np.arange(P)[in_mask]
        FI.set_seed(seed)
        model = VM.ViTLoRA(C, r=r, freeze_a=True).to(FI.DEVICE)
        theta0 = FI.trainable_state(model)
        y_in = y_p[in_idx]
        parts_local = FI.dirichlet_partition(y_in, N, alpha, C, seed * 10007 + m)
        parts = [in_idx[p] if len(p) else p for p in parts_local]
        deltas, sizes, counts = [], [], []
        for ci in parts:
            if len(ci) == 0:
                deltas.append({k: torch.zeros_like(v) for k, v in theta0.items()})
                counts.append(np.zeros(C)); sizes.append(0); continue
            FI.load_trainable(model, theta0)
            VM.v_train(model, Xtr[ci], y_p[ci], K, lr, bs)
            st = FI.trainable_state(model)
            deltas.append({k: st[k] - theta0[k] for k in theta0})
            counts.append(np.bincount(y_p[ci], minlength=C).astype(np.float64))
            sizes.append(int(len(ci)))
        tot = max(sum(sizes), 1); w = [s / tot for s in sizes]
        st_star = FI.agg_count_head(theta0, deltas, w, counts)
        j = int(np.argmax(sizes))
        st_upd = {k: theta0[k] + deltas[j][k] for k in theta0}

        FI.load_trainable(model, st_star)
        loss_star, phi_star = vstats(model)
        acc = VM.v_eval(model, Xte, yte)
        FI.load_trainable(model, st_upd)
        loss_upd, phi_upd = vstats(model)
        np.savez_compressed(ck, in_mask=in_mask, loss_star=loss_star,
                            phi_star=phi_star, loss_update=loss_upd,
                            phi_update=phi_upd, test_acc=acc, attacker=j)
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print(f"  vmodel {m}/{n_models-1} acc={acc:.3f} ({time.time()-t:.0f}s)",
              flush=True)

    ext_s, fel_s = score_pair(sdir, n_models, y_p, C, "star")
    ext_u, fel_u = score_pair(sdir, n_models, y_p, C, "update")
    row = _row(dataset, "vit_b16", N, alpha, method, seed, n_shadows, P,
               released={"external": ext_s, "fellow": fel_s},
               update={"external": ext_u, "fellow": fel_u})
    cell.write_text(json.dumps(row))
    print(f"ok {dataset} s{seed} | released LiRA={ext_s['lira']['auc']:.3f} "
          f"update LiRA={ext_u['lira']['auc']:.3f}", flush=True)
    return row


def _slim(res):
    return {k: v for k, v in res.items() if not k.startswith("roc_")}


def _row(task, backbone, N, alpha, method, seed, n_shadows, P, released, update):
    def pack(d):
        return {surf: {att: _slim(r) for att, r in atts.items()}
                for surf, atts in d.items()}
    return dict(task=task, backbone=backbone, N=N, alpha=alpha, method=method,
                seed=seed, n_shadows=n_shadows, pool_size=P,
                released=pack(released), update=pack(update))


CSV_HEADER = "backbone,N,alpha,method,seed,surface,attack,tpr_at_0.1pct,tpr_at_1pct,auc"


def csv_rows(row):
    out = []
    for obj, adv in (("released", "external"), ("released", "fellow"),
                     ("update", "external"), ("update", "fellow")):
        for att, res in row[obj][adv].items():
            out.append(",".join(str(x) for x in (
                row["backbone"], row["N"], row["alpha"], row["method"],
                row["seed"], f"{obj}_{adv}", att,
                round(res.get("tpr_at_fpr_0.001", float("nan")), 4),
                round(res.get("tpr_at_fpr_0.01", float("nan")), 4),
                round(res["auc"], 4))))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modality", required=True, choices=["text", "vision"])
    ap.add_argument("--cell-index", type=int, default=None)
    ap.add_argument("--n-shadows", type=int, default=16)
    args = ap.parse_args()

    rows = []
    if args.modality == "text":
        # ag_news x 3 seeds is enough for the released-vs-update contrast (B.9);
        # the 4-task RELEASED-model numbers already live in heifd_mia_freeze_a.
        cells = [(t, s) for t in ["ag_news"] for s in [42, 43, 44]]
        if args.cell_index is not None:
            cells = [cells[args.cell_index]]
        for task, seed in cells:
            try:
                rows.append(run_text_cell(task, seed, n_shadows=args.n_shadows))
            except Exception as e:  # noqa: BLE001
                import traceback
                (OUTDIR / f"FAIL_{task}_s{seed}.txt").write_text(traceback.format_exc())
                print(f"FAIL {task} s{seed}: {e}", flush=True)
    else:
        seeds = [42, 43, 44]
        if args.cell_index is not None:
            seeds = [seeds[args.cell_index]]
        for seed in seeds:
            try:
                rows.append(run_vision_cell(seed, n_shadows=args.n_shadows))
            except Exception as e:  # noqa: BLE001
                import traceback
                (OUTDIR / f"FAIL_cifar100_s{seed}.txt").write_text(traceback.format_exc())
                print(f"FAIL cifar100 s{seed}: {e}", flush=True)

    print("\n===== BEGIN results.csv =====", flush=True)
    print(CSV_HEADER)
    for r in rows:
        for line in csv_rows(r):
            print(line)
    print("===== END results.csv =====\n", flush=True)


if __name__ == "__main__":
    main()
