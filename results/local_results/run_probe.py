#!/usr/bin/env python3
"""Local CPU probe (issue 023): how should client updates be combined?

Research question
-----------------
The HE-IFD server aggregation is theta* = theta0 + sum_i w_i * Delta_i with
Delta_i = theta_i^(K) - theta0. Because sum_i w_i = 1 this *telescopes* to a
sample-weighted average of the clients' FINAL models, sum_i w_i * theta_i^(K).
It never visits a joint trajectory. We ask: does a SYNCHRONIZED trajectory --
combining per-step client updates at the shared running point, the way one SGD
run over pooled mini-batches would -- beat that weight-averaging under label
heterogeneity, and does the shared basin (probe warm-start) matter differently
for each scheme?

This is a SELF-CONTAINED probe. It does NOT import src/. Plain supervised local
SGD (no distillation) is used throughout to isolate the *aggregation* question;
distillation is a separate axis (see README).

Schemes
-------
A. weight_avg   one-shot: each client runs K local SGD steps from theta0 ->
                theta_i^(K); theta* = theta0 + sum_i w_i (theta_i^(K) - theta0).
B. stepsum      telescoping control: theta* = theta0 + sum_k sum_i w_i d_i^(k)
                with d_i^(k) the client's own step-k delta. Must == A.
C. sync_sgd     synchronized trajectory: for k=1..K every client computes ONE
                minibatch gradient AT the shared running point theta^(k-1),
                sample-weighted-average them, apply one optimizer step. Multi-
                round; does NOT telescope.
D. fedavg_Estep E=5 local steps per round before averaging models, R rounds
                (R*E ~ K). Bridges A <-> C.
E. centralized  SGD on the pooled data from theta0 (oracle upper bound).

Outputs (all under results/local_results/)
  cell_<scheme>_<basin>_N<>_a<>_s<>.json   per-cell incl. acc trajectory array
  results.csv                              long-form summary
  trajectories.png                         test-acc vs step, faceted by alpha
                                           (N=10, probe + no-probe)
  README.md                                question + verdict (written separately)
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import time
from typing import Dict, List, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision

# ----------------------------------------------------------------------------- config
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = "/tmp/probe023_data"

K = 100               # local/sync steps per client (and centralized steps)
BATCH = 64
LR = 0.1              # plain SGD lr (no momentum -> clean trajectory semantics)
HIDDEN = 200
N_CLASSES = 10
IN_DIM = 784
PROBE_SIZE = 100      # shared labelled samples used to warm theta0 (probe basin)
PROBE_EPOCHS = 30     # passes over the 100-sample probe set to form theta0
EVAL_EVERY = 5        # record test acc every this many steps (and at step 0/K)
N_TEST_EVAL = 4000    # test subset for fast-but-stable accuracy during trajectory
DEVICE = torch.device("cpu")


# ----------------------------------------------------------------------------- model
class MLP(nn.Module):
    def __init__(self, in_dim=IN_DIM, hidden=HIDDEN, n_classes=N_CLASSES):
        super().__init__()
        self.fc1 = nn.Linear(in_dim, hidden)
        self.fc2 = nn.Linear(hidden, n_classes)

    def forward(self, x):
        x = x.view(x.size(0), -1)
        return self.fc2(F.relu(self.fc1(x)))


def new_model(seed: int) -> MLP:
    """A model with deterministic init for the given seed (shared random theta0)."""
    g = torch.Generator().manual_seed(seed)
    m = MLP()
    with torch.no_grad():
        for p in m.parameters():
            if p.dim() >= 2:
                # kaiming-ish uniform but generator-seeded for reproducibility
                bound = 1.0 / (p.shape[1] ** 0.5)
                p.copy_(torch.empty_like(p).uniform_(-bound, bound, generator=g))
            else:
                p.zero_()
    return m


def get_state(m: nn.Module) -> Dict[str, torch.Tensor]:
    return {k: v.detach().clone() for k, v in m.state_dict().items()}


def set_state(m: nn.Module, state: Dict[str, torch.Tensor]):
    m.load_state_dict({k: v.clone() for k, v in state.items()})


def state_axpy(dst: Dict[str, torch.Tensor], a: float, x: Dict[str, torch.Tensor]):
    """dst += a * x, in place, per key."""
    for k in dst:
        dst[k] = dst[k] + a * x[k]
    return dst


def state_sub(a: Dict[str, torch.Tensor], b: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
    return {k: a[k] - b[k] for k in a}


# ----------------------------------------------------------------------------- data
def load_mnist() -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """Returns flattened, normalized train/test tensors entirely in memory."""
    tr = torchvision.datasets.MNIST(DATA_ROOT, train=True, download=False)
    te = torchvision.datasets.MNIST(DATA_ROOT, train=False, download=False)
    mean, std = 0.1307, 0.3081
    Xtr = (tr.data.float() / 255.0 - mean) / std
    Xte = (te.data.float() / 255.0 - mean) / std
    Xtr = Xtr.view(Xtr.size(0), -1)
    Xte = Xte.view(Xte.size(0), -1)
    return Xtr, tr.targets.long(), Xte, te.targets.long()


def dirichlet_partition(labels: torch.Tensor, n_clients: int, alpha: float,
                        seed: int) -> List[np.ndarray]:
    """Label-Dirichlet partition: per class, split its indices across clients by
    a Dir(alpha) draw. Lower alpha = more skew. Returns list of index arrays."""
    rng = np.random.default_rng(seed)
    labels_np = labels.numpy()
    n = len(labels_np)
    if n_clients == 1:
        return [np.arange(n)]
    client_idx = [[] for _ in range(n_clients)]
    for c in range(N_CLASSES):
        idx_c = np.where(labels_np == c)[0]
        rng.shuffle(idx_c)
        props = rng.dirichlet([alpha] * n_clients)
        cuts = (np.cumsum(props) * len(idx_c)).astype(int)[:-1]
        for ci, chunk in enumerate(np.split(idx_c, cuts)):
            client_idx[ci].extend(chunk.tolist())
    out = []
    for ci in range(n_clients):
        arr = np.array(client_idx[ci], dtype=np.int64)
        rng.shuffle(arr)
        out.append(arr)
    return out


# ----------------------------------------------------------------------------- eval
@torch.no_grad()
def test_acc(state: Dict[str, torch.Tensor], Xte: torch.Tensor, yte: torch.Tensor,
             m: MLP, n_eval: int = N_TEST_EVAL) -> float:
    set_state(m, state)
    m.eval()
    X = Xte[:n_eval]
    y = yte[:n_eval]
    logits = m(X)
    pred = logits.argmax(1)
    return (pred == y).float().mean().item()


# ----------------------------------------------------------------------------- minibatch sampler
class ClientSampler:
    """Cycles deterministically through a client's local indices, yielding
    minibatches of size BATCH."""
    def __init__(self, idx: np.ndarray, seed: int, batch: int = BATCH):
        self.idx = idx.copy()
        self.batch = batch
        self.rng = np.random.default_rng(seed)
        self.pos = 0
        self._reshuffle()

    def _reshuffle(self):
        self.rng.shuffle(self.idx)
        self.pos = 0

    def next(self) -> np.ndarray:
        if len(self.idx) == 0:
            return self.idx  # empty client -> empty batch (zero gradient)
        if self.pos + self.batch > len(self.idx):
            self._reshuffle()
        b = self.idx[self.pos:self.pos + self.batch]
        self.pos += self.batch
        return b


# ----------------------------------------------------------------------------- theta0 builders
def build_theta0(basin: str, seed: int, Xtr: torch.Tensor, ytr: torch.Tensor) -> Dict[str, torch.Tensor]:
    """no-probe: a single shared random init (same for all clients).
    probe: that init warmed on ~PROBE_SIZE shared, class-balanced labelled
    samples (a public seed set), forming a shared aligned basin."""
    m = new_model(seed)
    theta0 = get_state(m)
    if basin == "no-probe":
        return theta0
    # probe: class-balanced ~PROBE_SIZE shared samples
    rng = np.random.default_rng(seed + 777)
    per_class = max(1, PROBE_SIZE // N_CLASSES)
    probe_idx = []
    labels_np = ytr.numpy()
    for c in range(N_CLASSES):
        idx_c = np.where(labels_np == c)[0]
        probe_idx.extend(rng.choice(idx_c, size=per_class, replace=False).tolist())
    probe_idx = np.array(probe_idx)
    Xp, yp = Xtr[probe_idx], ytr[probe_idx]
    set_state(m, theta0)
    m.train()
    opt = torch.optim.SGD(m.parameters(), lr=LR)
    for _ in range(PROBE_EPOCHS):
        opt.zero_grad()
        loss = F.cross_entropy(m(Xp), yp)
        loss.backward()
        opt.step()
    return get_state(m)


# ----------------------------------------------------------------------------- training primitives
def local_trajectory(theta0: Dict[str, torch.Tensor], idx: np.ndarray,
                     Xtr: torch.Tensor, ytr: torch.Tensor, m: MLP,
                     seed: int) -> List[Dict[str, torch.Tensor]]:
    """Run K local SGD steps from theta0 on a client's data. Returns the list of
    K post-step states [theta^(1), ..., theta^(K)] (theta^(0)=theta0 implicit)."""
    set_state(m, theta0)
    m.train()
    opt = torch.optim.SGD(m.parameters(), lr=LR)
    sampler = ClientSampler(idx, seed)
    states = []
    for _ in range(K):
        b = sampler.next()
        opt.zero_grad()
        if len(b) > 0:
            loss = F.cross_entropy(m(Xtr[b]), ytr[b])
            loss.backward()
            opt.step()
        # else: empty client, no update this step (keeps state)
        states.append(get_state(m))
    return states


# ----------------------------------------------------------------------------- schemes
def run_weight_avg_and_stepsum(theta0, client_idx, weights, Xtr, ytr, Xte, yte,
                               m, seed):
    """Schemes A (weight_avg) and B (stepsum), computed together so we can prove
    A==B numerically and share the per-client trajectories.

    Trajectory semantics for the one-shot schemes: at step k we report the test
    accuracy of the PARTIAL telescoped aggregate
        theta0 + sum_i w_i (theta_i^(k) - theta0)
    i.e. what the server *would* decrypt if every client had stopped at step k.
    This puts A on the same step axis as the synchronized scheme C so the gap is
    visible. The final point (k=K) is the actual one-shot deliverable."""
    n_clients = len(client_idx)
    # per-client trajectories of post-step states
    traj = [local_trajectory(theta0, client_idx[i], Xtr, ytr, m, seed + 1000 + i)
            for i in range(n_clients)]

    eval_steps = sorted(set(list(range(0, K + 1, EVAL_EVERY)) + [K]))
    acc_traj = []
    for k in eval_steps:
        if k == 0:
            agg = {kk: vv.clone() for kk, vv in theta0.items()}
        else:
            agg = {kk: vv.clone() for kk, vv in theta0.items()}
            for i, w in enumerate(weights):
                delta = state_sub(traj[i][k - 1], theta0)  # theta_i^(k) - theta0
                state_axpy(agg, w, delta)
        acc_traj.append(test_acc(agg, Xte, yte, m))
    final_A = acc_traj[-1]

    # Scheme B (stepsum): theta0 + sum_k sum_i w_i d_i^(k), d_i^(k)=theta_i^(k)-theta_i^(k-1)
    aggB = {kk: vv.clone() for kk, vv in theta0.items()}
    for i, w in enumerate(weights):
        prev = theta0
        for k in range(K):
            d = state_sub(traj[i][k], prev)
            state_axpy(aggB, w, d)
            prev = traj[i][k]
    final_B = test_acc(aggB, Xte, yte, m)

    # numerical telescoping check: max param diff between A-final-agg and B
    aggA = {kk: vv.clone() for kk, vv in theta0.items()}
    for i, w in enumerate(weights):
        state_axpy(aggA, w, state_sub(traj[i][K - 1], theta0))
    max_diff = max((aggA[k] - aggB[k]).abs().max().item() for k in aggA)

    return {
        "weight_avg": {"final_acc": final_A, "acc_traj": acc_traj, "eval_steps": eval_steps},
        "stepsum": {"final_acc": final_B, "acc_traj": acc_traj, "eval_steps": eval_steps},
        "telescope_max_param_diff": max_diff,
    }


def run_sync_sgd(theta0, client_idx, weights, Xtr, ytr, m, Xte, yte, seed):
    """Scheme C: synchronized trajectory. One shared model. Each step, every
    client computes a minibatch gradient at the shared running point, take the
    sample-weighted average, apply one SGD step."""
    set_state(m, theta0)
    m.train()
    samplers = [ClientSampler(client_idx[i], seed + 2000 + i) for i in range(len(client_idx))]
    eval_steps = sorted(set(list(range(0, K + 1, EVAL_EVERY)) + [K]))
    acc_traj = [test_acc(get_state(m), Xte, yte, m)]  # step 0
    for k in range(1, K + 1):
        # accumulate sample-weighted-average gradient at the shared point
        agg_grad = {n: torch.zeros_like(p) for n, p in m.named_parameters()}
        for i, w in enumerate(weights):
            b = samplers[i].next()
            if len(b) == 0:
                continue
            m.zero_grad()
            loss = F.cross_entropy(m(Xtr[b]), ytr[b])
            loss.backward()
            for n, p in m.named_parameters():
                if p.grad is not None:
                    agg_grad[n] += w * p.grad.detach()
        with torch.no_grad():
            for n, p in m.named_parameters():
                p -= LR * agg_grad[n]
        if k in eval_steps:
            acc_traj.append(test_acc(get_state(m), Xte, yte, m))
    return {"final_acc": acc_traj[-1], "acc_traj": acc_traj, "eval_steps": eval_steps}


def run_fedavg_estep(theta0, client_idx, weights, Xtr, ytr, m, Xte, yte, seed, E=5):
    """Scheme D: R rounds of E local steps then sample-weighted model average.
    R*E ~ K. Trajectory recorded per round (mapped onto the step axis)."""
    R = max(1, K // E)
    global_state = {k: v.clone() for k, v in theta0.items()}
    eval_steps = [0] + [r * E for r in range(1, R + 1)]
    acc_traj = [test_acc(global_state, Xte, yte, m)]
    samplers = [ClientSampler(client_idx[i], seed + 3000 + i) for i in range(len(client_idx))]
    for r in range(R):
        new_states = []
        for i in range(len(client_idx)):
            set_state(m, global_state)
            m.train()
            opt = torch.optim.SGD(m.parameters(), lr=LR)
            for _ in range(E):
                b = samplers[i].next()
                opt.zero_grad()
                if len(b) > 0:
                    loss = F.cross_entropy(m(Xtr[b]), ytr[b])
                    loss.backward()
                    opt.step()
            new_states.append(get_state(m))
        # sample-weighted average of local models
        agg = {k: torch.zeros_like(v) for k, v in global_state.items()}
        for i, w in enumerate(weights):
            for k in agg:
                agg[k] += w * new_states[i][k]
        global_state = agg
        acc_traj.append(test_acc(global_state, Xte, yte, m))
    return {"final_acc": acc_traj[-1], "acc_traj": acc_traj, "eval_steps": eval_steps, "E": E, "R": R}


def run_centralized(theta0, all_idx, Xtr, ytr, m, Xte, yte, seed):
    """Scheme E: plain SGD on the pooled data from theta0 (oracle upper bound)."""
    set_state(m, theta0)
    m.train()
    opt = torch.optim.SGD(m.parameters(), lr=LR)
    sampler = ClientSampler(all_idx, seed + 4000)
    eval_steps = sorted(set(list(range(0, K + 1, EVAL_EVERY)) + [K]))
    acc_traj = [test_acc(get_state(m), Xte, yte, m)]
    for k in range(1, K + 1):
        b = sampler.next()
        opt.zero_grad()
        loss = F.cross_entropy(m(Xtr[b]), ytr[b])
        loss.backward()
        opt.step()
        if k in eval_steps:
            acc_traj.append(test_acc(get_state(m), Xte, yte, m))
    return {"final_acc": acc_traj[-1], "acc_traj": acc_traj, "eval_steps": eval_steps}


# ----------------------------------------------------------------------------- driver
def run_cell(N, alpha, basin, seed, Xtr, ytr, Xte, yte):
    m = MLP().to(DEVICE)
    theta0 = build_theta0(basin, seed, Xtr, ytr)
    theta0_acc = test_acc(theta0, Xte, yte, m, n_eval=10000)

    client_idx = dirichlet_partition(ytr, N, alpha, seed)
    sample_sizes = [len(ix) for ix in client_idx]
    total = sum(sample_sizes)
    weights = [s / total for s in sample_sizes] if total > 0 else [1.0 / N] * N
    all_idx = np.concatenate([ix for ix in client_idx if len(ix) > 0]) if total > 0 else np.array([], dtype=np.int64)

    cells = {}

    ab = run_weight_avg_and_stepsum(theta0, client_idx, weights, Xtr, ytr, Xte, yte, m, seed)
    cells["weight_avg"] = ab["weight_avg"]
    cells["stepsum"] = ab["stepsum"]
    telescope_diff = ab["telescope_max_param_diff"]

    cells["sync_sgd"] = run_sync_sgd(theta0, client_idx, weights, Xtr, ytr, m, Xte, yte, seed)
    cells["fedavg_Estep"] = run_fedavg_estep(theta0, client_idx, weights, Xtr, ytr, m, Xte, yte, seed)
    cells["centralized"] = run_centralized(theta0, all_idx, Xtr, ytr, m, Xte, yte, seed)

    return {
        "N": N, "alpha": alpha, "basin": basin, "seed": seed,
        "theta0_acc": theta0_acc,
        "sample_sizes": sample_sizes,
        "weights": weights,
        "telescope_max_param_diff": telescope_diff,
        "schemes": cells,
        "config": {"K": K, "BATCH": BATCH, "LR": LR, "HIDDEN": HIDDEN,
                   "PROBE_SIZE": PROBE_SIZE, "PROBE_EPOCHS": PROBE_EPOCHS,
                   "EVAL_EVERY": EVAL_EVERY},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="tiny grid for a quick sanity check")
    ap.add_argument("--seeds", type=int, nargs="+", default=[42])
    args = ap.parse_args()

    Xtr, ytr, Xte, yte = load_mnist()

    if args.smoke:
        Ns = [10]
        alphas = [0.05, 1.0]
        basins = ["probe", "no-probe"]
        seeds = [42]
    else:
        Ns = [1, 5, 10]
        alphas = [0.05, 0.1, 0.5, 1.0]
        basins = ["probe", "no-probe"]
        seeds = args.seeds

    t_start = time.time()
    rows = []
    for basin in basins:
        for N in Ns:
            for alpha in alphas:
                for seed in seeds:
                    # N=1 has no heterogeneity; alpha is irrelevant -> only run alpha=1.0
                    if N == 1 and alpha != alphas[-1]:
                        continue
                    t0 = time.time()
                    res = run_cell(N, alpha, basin, seed, Xtr, ytr, Xte, yte)
                    fname = f"cell_{basin}_N{N}_a{alpha}_s{seed}.json"
                    with open(os.path.join(OUT_DIR, fname), "w") as f:
                        json.dump(res, f, indent=2)
                    dt = time.time() - t0
                    for scheme, sc in res["schemes"].items():
                        rows.append({
                            "scheme": scheme, "basin": basin, "N": N,
                            "alpha": alpha, "seed": seed,
                            "theta0_acc": round(res["theta0_acc"], 4),
                            "final_acc": round(sc["final_acc"], 4),
                            "telescope_max_param_diff": res["telescope_max_param_diff"],
                        })
                    wa = res["schemes"]["weight_avg"]["final_acc"]
                    ss = res["schemes"]["sync_sgd"]["final_acc"]
                    ce = res["schemes"]["centralized"]["final_acc"]
                    print(f"[ok] basin={basin} N={N} a={alpha} s={seed} "
                          f"th0={res['theta0_acc']:.3f} WA={wa:.3f} SYNC={ss:.3f} "
                          f"CENT={ce:.3f} tele_diff={res['telescope_max_param_diff']:.2e} "
                          f"({dt:.1f}s)", flush=True)

    # write results.csv
    csv_path = os.path.join(OUT_DIR, "results.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["scheme", "basin", "N", "alpha", "seed",
                                          "theta0_acc", "final_acc",
                                          "telescope_max_param_diff"])
        w.writeheader()
        w.writerows(rows)
    print(f"[done] wrote {len(rows)} rows to {csv_path} in {time.time()-t_start:.1f}s", flush=True)


if __name__ == "__main__":
    main()
