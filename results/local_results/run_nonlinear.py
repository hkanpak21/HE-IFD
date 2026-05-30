#!/usr/bin/env python3
"""Local CPU probe (issue 024): can a NON-LINEAR one-shot server combine beat
the flat weighted average under heterogeneity, and is any winner CKKS-cheap?

Research question
-----------------
Within strict ONE-SHOT HE-IFD: each client computes its K-step trajectory from
the shared aligned basin theta0 and uploads ONCE -- cumulative
    Delta_i = theta_i^(K) - theta0      (and the per-step deltas d_i^(k))
-- with NO second client<->server communication (Phase-0 alignment is free and
does NOT count as a round). The current server combine is the flat weighted
average
    theta* = theta0 + sum_i w_i * Delta_i      (depth-1 linear; telescopes).
Issue 023 showed this leaves a large heterogeneity gap to centralized at
alpha=0.05 (the synchronized-trajectory fix is multi-round, so OUT of budget).

This probe asks the strictly-one-shot question: given the SAME one-shot uploads
{Delta_i} (no extra rounds), does any NON-LINEAR function of them, computed
server-side, beat the flat average -- and is any winner low enough depth for
CKKS (depth-1 / depth-2 division-free; deep = sign/sqrt/division/sort)?

It is a SELF-CONTAINED probe reusing the 023 setup VERBATIM (MNIST, 784->200->10
MLP, plain SGD, K=100, N in {1,5,10}, alpha in {0.05,0.1,0.5,1.0}, basin in
{probe,no-probe}, seeds {42,123}). It does NOT import src/. Distillation is
deliberately removed (separate axis) so we isolate the *combine* question.

Per cell: run each client's local SGD trajectory ONCE from theta0 -> {Delta_i};
then apply every server combine below to the SAME {Delta_i} and report final
test acc. sync_sgd (multi-round) and centralized are the ceilings (out of the
one-shot budget; shown only as references, identical numbers to 023).

Server combines (all operate on the one-shot {Delta_i}; HE-depth annotated)
---------------------------------------------------------------------------
  weight_avg          theta0 + sum_i w_i Delta_i.                  depth-1 [baseline]
  mag_weighted        public-scalar reweight by ||Delta_i||:       depth-1 [HE-cheap]
                      theta0 + sum_i (w_i||Delta_i|| / sum_j w_j||Delta_j||) Delta_i.
                      (||Delta_i|| is a PUBLIC scalar a client may send -> the
                       server op stays a plaintext-scalar*ciphertext linear combo.
                       Still linear -> a reweighted average; here to show a
                       depth-1 reweight does NOT escape the average.)
  sign_majority       theta0 + lr_eff * sign(sum_i w_i sign(Delta_ij)) * mean_i|Delta_ij|.   deep [sign/compare]
  norm_normalized     theta0 + (mean_i||Delta_i||) * sum_i w_i (Delta_i/||Delta_i||).         deep [per-vector div]
  agreement_gated     theta0 + g (.) m,  m=sum_i w_i Delta_i,
                      g_j = m_j^2 / (eps + sum_i w_i Delta_ij^2) in [0,1].                     deep [ratio]
  second_moment       theta0 + m / sqrt(eps + sum_i w_i Delta_ij^2)  (RMSProp-style).          deep [sqrt/div]
  coord_trimmed_mean  per-coordinate trimmed mean across clients (drop extremes), scaled.      deep [sort/compare]
  consensus_proj      project each Delta_i onto the mean direction u; average the scalar
                      projections + a residual fraction of the mean.                           deep [dot/div]
  poly_gate_d2_a      DIVISION-FREE depth-2 gate: theta0 + m - c*(s2_hat (.) m),
                      s2 = sum_i w_i Delta_i^2 (disagreement energy), m=sum_i w_i Delta_i.
                      Pure polynomial (one extra ct*ct multiply). depth-2 [HE-cheap]
  poly_gate_d2_b      DIVISION-FREE depth-2 gate, cancellation-aware:
                      theta0 + m (.) (1 - c*var_hat),  var = s2 - m.^2 >= 0 (weighted coord
                      variance) = theta0 + m - c*m(.)var_hat. Shrinks m where clients
                      disagree, keeps it where they agree, NO denominator. depth-2 [HE-cheap]

  sync_sgd / centralized  ceilings from 023 (multi-round / pooled) -- OUT of the
                      one-shot budget, reference only.                                          deep / n/a

Outputs (all under results/local_results/)
  nl_cell_<basin>_N<>_a<>_s<>.json   per-cell, every combine's final acc + meta
  nonlinear_results.csv              long-form: combine, basin, N, alpha, seed,
                                     he_depth, theta0_acc, final_acc, vs_weight_avg,
                                     vs_centralized
  nonlinear_combines.png             final-acc vs combine, faceted by alpha at
                                     N=10 (probe top, no-probe bottom)
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

# ----------------------------------------------------------------------------- config (023 verbatim)
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = "/tmp/probe023_data"

K = 100
BATCH = 64
LR = 0.1
HIDDEN = 200
N_CLASSES = 10
IN_DIM = 784
PROBE_SIZE = 100
PROBE_EPOCHS = 30
N_TEST_EVAL = 4000
DEVICE = torch.device("cpu")

EPS = 1e-12

# HE-depth annotation per combine (depth-1 / depth-2 / deep). depth-1 & depth-2
# are CKKS-feasible (depth-2 = one extra ct*ct multiply, division-free);
# "deep" needs sign/compare/sqrt/division/sort -> not low-depth CKKS.
HE_DEPTH = {
    "weight_avg":          "depth-1",
    "mag_weighted":        "depth-1",
    "poly_gate_d2_a":      "depth-2",
    "poly_gate_d2_b":      "depth-2",
    "sign_majority":       "deep",
    "norm_normalized":     "deep",
    "agreement_gated":     "deep",
    "second_moment":       "deep",
    "coord_trimmed_mean":  "deep",
    "consensus_proj":      "deep",
    "sync_sgd":            "deep(multi-round)",
    "centralized":         "n/a(pooled)",
}

# combines applied to the one-shot {Delta_i} (excludes the two ceilings)
ONESHOT_COMBINES = [
    "weight_avg", "mag_weighted",
    "sign_majority", "norm_normalized", "agreement_gated", "second_moment",
    "coord_trimmed_mean", "consensus_proj",
    "poly_gate_d2_a", "poly_gate_d2_b",
]

# poly-gate strength. Coordinates are normalized by a single PUBLIC scalar
# (the global RMS displacement) so one c works across cells (see _poly_scale).
# NOTE: a c-sweep (see README) shows the division-free polynomial gate is
# UNBOUNDED -- s2_hat/var_hat are heavy-tailed (max ~500x the mean), so any
# c large enough to gate meaningfully detonates a few coordinates and collapses
# accuracy (min Δ vs weight_avg = -22..-86 pt at c>=0.01). The only safe value
# is c~=0.005-0.01, where the gate ~= weight_avg (mean Δ ~ +1 pt, but min < 0).
# We record c=0.01 as the realistic near-neutral best of a division-free gate;
# this is the headline finding (a polynomial gate cannot emulate the BOUNDED
# [0,1] ratio gate without a clamp, which costs depth). Reproduce the sweep with
#   python -c "import run_nonlinear" + the README c-sweep snippet.
POLY_C = 0.01


# ----------------------------------------------------------------------------- model (023 verbatim)
class MLP(nn.Module):
    def __init__(self, in_dim=IN_DIM, hidden=HIDDEN, n_classes=N_CLASSES):
        super().__init__()
        self.fc1 = nn.Linear(in_dim, hidden)
        self.fc2 = nn.Linear(hidden, n_classes)

    def forward(self, x):
        x = x.view(x.size(0), -1)
        return self.fc2(F.relu(self.fc1(x)))


def new_model(seed: int) -> MLP:
    g = torch.Generator().manual_seed(seed)
    m = MLP()
    with torch.no_grad():
        for p in m.parameters():
            if p.dim() >= 2:
                bound = 1.0 / (p.shape[1] ** 0.5)
                p.copy_(torch.empty_like(p).uniform_(-bound, bound, generator=g))
            else:
                p.zero_()
    return m


def get_state(m: nn.Module) -> Dict[str, torch.Tensor]:
    return {k: v.detach().clone() for k, v in m.state_dict().items()}


def set_state(m: nn.Module, state: Dict[str, torch.Tensor]):
    m.load_state_dict({k: v.clone() for k, v in state.items()})


def state_sub(a: Dict[str, torch.Tensor], b: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
    return {k: a[k] - b[k] for k in a}


# ---- flat-vector helpers (combines are easiest expressed on the flat param vector)
def state_keys(theta0: Dict[str, torch.Tensor]) -> List[str]:
    return list(theta0.keys())


def flatten(state: Dict[str, torch.Tensor], keys: List[str]) -> torch.Tensor:
    return torch.cat([state[k].reshape(-1) for k in keys])


def unflatten(vec: torch.Tensor, theta0: Dict[str, torch.Tensor], keys: List[str]) -> Dict[str, torch.Tensor]:
    out, off = {}, 0
    for k in keys:
        n = theta0[k].numel()
        out[k] = vec[off:off + n].reshape(theta0[k].shape).clone()
        off += n
    return out


# ----------------------------------------------------------------------------- data (023 verbatim)
def load_mnist() -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
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


# ----------------------------------------------------------------------------- eval (023 verbatim)
@torch.no_grad()
def test_acc_state(state: Dict[str, torch.Tensor], Xte, yte, m, n_eval=N_TEST_EVAL) -> float:
    set_state(m, state)
    m.eval()
    logits = m(Xte[:n_eval])
    return (logits.argmax(1) == yte[:n_eval]).float().mean().item()


@torch.no_grad()
def test_acc_vec(vec: torch.Tensor, theta0, keys, Xte, yte, m, n_eval=N_TEST_EVAL) -> float:
    return test_acc_state(unflatten(vec, theta0, keys), Xte, yte, m, n_eval)


# ----------------------------------------------------------------------------- sampler (023 verbatim)
class ClientSampler:
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
            return self.idx
        if self.pos + self.batch > len(self.idx):
            self._reshuffle()
        b = self.idx[self.pos:self.pos + self.batch]
        self.pos += self.batch
        return b


# ----------------------------------------------------------------------------- theta0 + trajectory (023 verbatim)
def build_theta0(basin: str, seed: int, Xtr, ytr) -> Dict[str, torch.Tensor]:
    m = new_model(seed)
    theta0 = get_state(m)
    if basin == "no-probe":
        return theta0
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
        F.cross_entropy(m(Xp), yp).backward()
        opt.step()
    return get_state(m)


def local_final(theta0, idx, Xtr, ytr, m, seed) -> Dict[str, torch.Tensor]:
    """Run K local SGD steps from theta0 on a client's data; return theta_i^(K).
    The per-step deltas d_i^(k) telescope to Delta_i = theta_i^(K)-theta0, which
    is the only thing every one-shot combine here needs; 023 already verified the
    telescoping bit-exactly, so we keep just the cumulative upload."""
    set_state(m, theta0)
    m.train()
    opt = torch.optim.SGD(m.parameters(), lr=LR)
    sampler = ClientSampler(idx, seed)
    for _ in range(K):
        b = sampler.next()
        opt.zero_grad()
        if len(b) > 0:
            F.cross_entropy(m(Xtr[b]), ytr[b]).backward()
            opt.step()
    return get_state(m)


# ----------------------------------------------------------------------------- ceilings (023 verbatim)
def run_sync_sgd(theta0, client_idx, weights, Xtr, ytr, m, Xte, yte, seed) -> float:
    set_state(m, theta0)
    m.train()
    samplers = [ClientSampler(client_idx[i], seed + 2000 + i) for i in range(len(client_idx))]
    for _ in range(1, K + 1):
        agg_grad = {n: torch.zeros_like(p) for n, p in m.named_parameters()}
        for i, w in enumerate(weights):
            b = samplers[i].next()
            if len(b) == 0:
                continue
            m.zero_grad()
            F.cross_entropy(m(Xtr[b]), ytr[b]).backward()
            for n, p in m.named_parameters():
                if p.grad is not None:
                    agg_grad[n] += w * p.grad.detach()
        with torch.no_grad():
            for n, p in m.named_parameters():
                p -= LR * agg_grad[n]
    return test_acc_state(get_state(m), Xte, yte, m)


def run_centralized(theta0, all_idx, Xtr, ytr, m, Xte, yte, seed) -> float:
    set_state(m, theta0)
    m.train()
    opt = torch.optim.SGD(m.parameters(), lr=LR)
    sampler = ClientSampler(all_idx, seed + 4000)
    for _ in range(K):
        b = sampler.next()
        opt.zero_grad()
        F.cross_entropy(m(Xtr[b]), ytr[b]).backward()
        opt.step()
    return test_acc_state(get_state(m), Xte, yte, m)


# ----------------------------------------------------------------------------- the server combines
# Each takes the stacked client displacements D (n_clients x P, flat), sample
# weights w (n_clients,), and theta0 vector t0 (P,); returns the combined theta
# vector (P,). All operate on the SAME one-shot {Delta_i}.

def combine_weight_avg(D, w, t0):
    m = (w[:, None] * D).sum(0)                  # sum_i w_i Delta_i
    return t0 + m


def combine_mag_weighted(D, w, t0):
    norms = D.norm(dim=1)                         # ||Delta_i|| (public scalar)
    coef = w * norms
    coef = coef / (coef.sum() + EPS)              # renormalized public scalars
    m = (coef[:, None] * D).sum(0)
    return t0 + m


def combine_sign_majority(D, w, t0):
    vote = (w[:, None] * torch.sign(D)).sum(0)    # weighted sign vote per coord
    direction = torch.sign(vote)
    mag = D.abs().mean(0)                          # mean magnitude per coord
    # effective scale so its global L1 matches weight_avg's |m| (fair compare)
    m = (w[:, None] * D).sum(0)
    scale = m.abs().sum() / (direction.abs() * mag).sum().clamp_min(EPS)
    return t0 + scale * direction * mag


def combine_norm_normalized(D, w, t0):
    norms = D.norm(dim=1, keepdim=True).clamp_min(EPS)
    units = D / norms                             # per-vector division
    mean_norm = D.norm(dim=1).mean()
    m = (w[:, None] * units).sum(0)
    return t0 + mean_norm * m


def combine_agreement_gated(D, w, t0, eps_rel=1e-3):
    m = (w[:, None] * D).sum(0)                   # sum_i w_i Delta_i
    s2 = (w[:, None] * D.pow(2)).sum(0)           # sum_i w_i Delta_i^2
    eps = eps_rel * s2.mean()
    g = m.pow(2) / (eps + s2)                      # in [0,1], downweights cancellation
    return t0 + g * m


def combine_second_moment(D, w, t0, eps_rel=1e-3):
    m = (w[:, None] * D).sum(0)
    s2 = (w[:, None] * D.pow(2)).sum(0)
    eps = eps_rel * s2.mean()
    pre = m / torch.sqrt(eps + s2)                # RMSProp-style per-coord precond
    # rescale to weight_avg's global magnitude so the compare is about *shape*
    scale = m.abs().sum() / pre.abs().sum().clamp_min(EPS)
    return t0 + scale * pre


def combine_coord_trimmed_mean(D, w, t0):
    n = D.shape[0]
    if n <= 2:
        return combine_weight_avg(D, w, t0)       # nothing to trim
    k = 1                                          # drop top-1 and bottom-1 per coord
    sorted_D, _ = torch.sort(D, dim=0)            # sort across clients per coord
    trimmed = sorted_D[k:n - k]                    # (n-2k) x P
    m = trimmed.mean(0)
    return t0 + m


def combine_consensus_proj(D, w, t0, residual=0.3):
    m = (w[:, None] * D).sum(0)                   # consensus direction (mean)
    u = m / m.norm().clamp_min(EPS)
    proj = (D * u[None, :]).sum(1)                # scalar projection of each Delta_i on u
    coh = (w * proj).sum()                         # weighted mean projection length
    # consensus component along u, plus a residual fraction of the raw mean
    return t0 + coh * u + residual * (m - coh * u)


# --- division-free depth-2 poly gates. Coordinates are scaled by a single PUBLIC
# scalar s = sqrt(mean_j s2_j) (the global RMS displacement, a public summary) so
# one constant c works across cells; this scaling is a public-scalar multiply and
# does NOT add ciphertext depth. m and s2=sum_i w_i Delta_i^2 are each one linear
# pass; the gate is ONE extra elementwise ct*ct multiply (depth-2 total), with NO
# denominator on a ciphertext.
def _poly_scale(D, w):
    s2 = (w[:, None] * D.pow(2)).sum(0)
    s = torch.sqrt(s2.mean() + EPS)               # public global RMS scalar
    return s2, s


def combine_poly_gate_d2_a(D, w, t0, c=POLY_C):
    """theta0 + m - c * (s2_hat (.) m), s2_hat = s2 / s^2 (public-scalar rescale).
    Subtracts disagreement-energy-weighted mean -> shrinks high-second-moment
    coords, keeps low-energy ones. One ct*ct multiply, no ciphertext division."""
    m = (w[:, None] * D).sum(0)
    s2, s = _poly_scale(D, w)
    s2_hat = s2 / (s * s)                          # public-scalar division only
    return t0 + m - c * (s2_hat * m)


def combine_poly_gate_d2_b(D, w, t0, c=POLY_C):
    """Cancellation-aware: theta0 + m - c * m (.) var_hat,
    var = s2 - m^2 (weighted per-coord variance, >=0), var_hat = var / s^2.
    Where clients agree var~0 -> keep m; where they cancel var large -> shrink m.
    Still one ct*ct multiply (m .* var), division-free (public-scalar s^2)."""
    m = (w[:, None] * D).sum(0)
    s2, s = _poly_scale(D, w)
    var = (s2 - m.pow(2)).clamp_min(0.0)
    var_hat = var / (s * s)                        # public-scalar division only
    return t0 + m - c * (m * var_hat)


COMBINE_FN = {
    "weight_avg":         combine_weight_avg,
    "mag_weighted":       combine_mag_weighted,
    "sign_majority":      combine_sign_majority,
    "norm_normalized":    combine_norm_normalized,
    "agreement_gated":    combine_agreement_gated,
    "second_moment":      combine_second_moment,
    "coord_trimmed_mean": combine_coord_trimmed_mean,
    "consensus_proj":     combine_consensus_proj,
    "poly_gate_d2_a":     combine_poly_gate_d2_a,
    "poly_gate_d2_b":     combine_poly_gate_d2_b,
}


# ----------------------------------------------------------------------------- driver
def run_cell(N, alpha, basin, seed, Xtr, ytr, Xte, yte):
    m = MLP().to(DEVICE)
    theta0 = build_theta0(basin, seed, Xtr, ytr)
    theta0_acc = test_acc_state(theta0, Xte, yte, m, n_eval=10000)
    keys = state_keys(theta0)
    t0 = flatten(theta0, keys)

    client_idx = dirichlet_partition(ytr, N, alpha, seed)
    sample_sizes = [len(ix) for ix in client_idx]
    total = sum(sample_sizes)
    weights = [s / total for s in sample_sizes] if total > 0 else [1.0 / N] * N
    all_idx = (np.concatenate([ix for ix in client_idx if len(ix) > 0])
               if total > 0 else np.array([], dtype=np.int64))

    # one-shot uploads: each client's trajectory ONCE -> Delta_i = theta_i^(K)-theta0
    finals = [local_final(theta0, client_idx[i], Xtr, ytr, m, seed + 1000 + i)
              for i in range(N)]
    D = torch.stack([flatten(state_sub(finals[i], theta0), keys) for i in range(N)])  # N x P
    w = torch.tensor(weights, dtype=D.dtype)

    combines = {}
    for name in ONESHOT_COMBINES:
        vec = COMBINE_FN[name](D, w, t0)
        combines[name] = test_acc_vec(vec, theta0, keys, Xte, yte, m)

    # ceilings (out of one-shot budget; reference only -- match 023)
    sync = run_sync_sgd(theta0, client_idx, weights, Xtr, ytr, m, Xte, yte, seed)
    cent = run_centralized(theta0, all_idx, Xtr, ytr, m, Xte, yte, seed)

    wa = combines["weight_avg"]
    return {
        "N": N, "alpha": alpha, "basin": basin, "seed": seed,
        "theta0_acc": theta0_acc,
        "sample_sizes": sample_sizes,
        "weights": weights,
        "combines": combines,
        "sync_sgd": sync,
        "centralized": cent,
        "delta_norms": D.norm(dim=1).tolist(),
        "best_oneshot": max(combines, key=combines.get),
        "best_oneshot_acc": max(combines.values()),
        "best_lowdepth": max(
            (k for k in combines if HE_DEPTH[k] in ("depth-1", "depth-2")),
            key=lambda k: combines[k]),
        "config": {"K": K, "BATCH": BATCH, "LR": LR, "HIDDEN": HIDDEN,
                   "PROBE_SIZE": PROBE_SIZE, "PROBE_EPOCHS": PROBE_EPOCHS,
                   "POLY_C": POLY_C},
        "_wa": wa, "_cent": cent, "_sync": sync,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 123])
    ap.add_argument("--figure", action="store_true", help="(re)build the png from existing cells")
    args = ap.parse_args()

    if not args.figure:
        Xtr, ytr, Xte, yte = load_mnist()
        if args.smoke:
            Ns, alphas, basins, seeds = [10], [0.05, 1.0], ["probe", "no-probe"], [42]
        else:
            Ns, alphas, basins, seeds = [1, 5, 10], [0.05, 0.1, 0.5, 1.0], ["probe", "no-probe"], args.seeds

        t_start = time.time()
        rows = []
        for basin in basins:
            for N in Ns:
                for alpha in alphas:
                    for seed in seeds:
                        if N == 1 and alpha != alphas[-1]:
                            continue
                        t0 = time.time()
                        res = run_cell(N, alpha, basin, seed, Xtr, ytr, Xte, yte)
                        fname = f"nl_cell_{basin}_N{N}_a{alpha}_s{seed}.json"
                        with open(os.path.join(OUT_DIR, fname), "w") as f:
                            json.dump(res, f, indent=2)
                        wa, cent = res["_wa"], res["_cent"]
                        for name, acc in res["combines"].items():
                            rows.append({
                                "combine": name, "basin": basin, "N": N,
                                "alpha": alpha, "seed": seed,
                                "he_depth": HE_DEPTH[name],
                                "theta0_acc": round(res["theta0_acc"], 4),
                                "final_acc": round(acc, 4),
                                "vs_weight_avg": round(acc - wa, 4),
                                "vs_centralized": round(acc - cent, 4),
                            })
                        for name, acc in (("sync_sgd", res["_sync"]), ("centralized", res["_cent"])):
                            rows.append({
                                "combine": name, "basin": basin, "N": N,
                                "alpha": alpha, "seed": seed,
                                "he_depth": HE_DEPTH[name],
                                "theta0_acc": round(res["theta0_acc"], 4),
                                "final_acc": round(acc, 4),
                                "vs_weight_avg": round(acc - wa, 4),
                                "vs_centralized": round(acc - cent, 4),
                            })
                        bo = res["best_oneshot"]
                        bld = res["best_lowdepth"]
                        print(f"[ok] {basin} N={N} a={alpha} s={seed} "
                              f"th0={res['theta0_acc']:.3f} WA={wa:.3f} "
                              f"best={bo}:{res['combines'][bo]:.3f} "
                              f"bestLD={bld}:{res['combines'][bld]:.3f} "
                              f"SYNC={res['_sync']:.3f} CENT={cent:.3f} "
                              f"({time.time()-t0:.1f}s)", flush=True)

        csv_path = os.path.join(OUT_DIR, "nonlinear_results.csv")
        with open(csv_path, "w", newline="") as f:
            wtr = csv.DictWriter(f, fieldnames=["combine", "basin", "N", "alpha", "seed",
                                                "he_depth", "theta0_acc", "final_acc",
                                                "vs_weight_avg", "vs_centralized"])
            wtr.writeheader()
            wtr.writerows(rows)
        print(f"[done] wrote {len(rows)} rows to {csv_path} in {time.time()-t_start:.1f}s", flush=True)

    make_figure()


# ----------------------------------------------------------------------------- figure
def make_figure():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    N, ALPHAS, BASINS = 10, [0.05, 0.1, 0.5, 1.0], ["probe", "no-probe"]
    SEEDS = [42, 123]
    bars = ONESHOT_COMBINES
    depth_color = {"depth-1": "#1f77b4", "depth-2": "#2ca02c", "deep": "#d62728"}

    def load_avg(basin, alpha):
        accs = {}
        for s in SEEDS:
            p = os.path.join(OUT_DIR, f"nl_cell_{basin}_N{N}_a{alpha}_s{s}.json")
            if not os.path.exists(p):
                continue
            with open(p) as f:
                c = json.load(f)
            for k, v in c["combines"].items():
                accs.setdefault(k, []).append(v)
            accs.setdefault("sync_sgd", []).append(c["sync_sgd"])
            accs.setdefault("centralized", []).append(c["centralized"])
            accs.setdefault("_theta0", []).append(c["theta0_acc"])
        return {k: float(np.mean(v)) for k, v in accs.items()}

    fig, axes = plt.subplots(len(BASINS), len(ALPHAS), figsize=(18, 8.5), sharey=True)
    for r, basin in enumerate(BASINS):
        for cc, alpha in enumerate(ALPHAS):
            ax = axes[r][cc]
            a = load_avg(basin, alpha)
            xs = np.arange(len(bars))
            ys = [100.0 * a.get(b, float("nan")) for b in bars]
            cols = [depth_color[HE_DEPTH[b]] for b in bars]
            ax.bar(xs, ys, color=cols, edgecolor="black", linewidth=0.4)
            wa = 100.0 * a.get("weight_avg", float("nan"))
            ax.axhline(wa, color="#d62728", linestyle="--", linewidth=1.2, alpha=0.8)
            ax.axhline(100.0 * a.get("centralized", float("nan")), color="#7f7f7f",
                       linestyle=":", linewidth=1.3)
            ax.axhline(100.0 * a.get("sync_sgd", float("nan")), color="#1f77b4",
                       linestyle="-.", linewidth=1.0, alpha=0.7)
            ax.axhline(100.0 * a.get("_theta0", float("nan")), color="black",
                       linestyle=(0, (1, 3)), linewidth=0.8, alpha=0.5)
            ax.set_title(f"{basin}  |  alpha={alpha}", fontsize=10)
            ax.set_xticks(xs)
            ax.set_xticklabels(bars, rotation=55, ha="right", fontsize=7)
            if cc == 0:
                ax.set_ylabel("final test accuracy (%)")
            ax.grid(True, axis="y", alpha=0.25)
            ax.set_ylim(0, 100)
            best_ld = max((b for b in bars if HE_DEPTH[b] in ("depth-1", "depth-2")),
                          key=lambda b: a.get(b, -1))
            ax.text(0.97, 0.04,
                    f"bestLD {best_ld}\n= {100*a.get(best_ld,0):.1f}  (WA {wa:.1f})",
                    transform=ax.transAxes, ha="right", va="bottom", fontsize=7.5,
                    bbox=dict(boxstyle="round,pad=0.25", fc="#fff7e6", ec="#d0a040", alpha=0.9))

    from matplotlib.patches import Patch
    legend = [
        Patch(facecolor=depth_color["depth-1"], edgecolor="black", label="depth-1 (HE-cheap)"),
        Patch(facecolor=depth_color["depth-2"], edgecolor="black", label="depth-2 (HE-cheap)"),
        Patch(facecolor=depth_color["deep"], edgecolor="black", label="deep (not low-depth CKKS)"),
        plt.Line2D([0], [0], color="#d62728", linestyle="--", label="weight_avg (baseline)"),
        plt.Line2D([0], [0], color="#1f77b4", linestyle="-.", label="sync_sgd (multi-round ref)"),
        plt.Line2D([0], [0], color="#7f7f7f", linestyle=":", label="centralized (oracle)"),
        plt.Line2D([0], [0], color="black", linestyle=(0, (1, 3)), label="theta0 (basin start)"),
    ]
    fig.legend(handles=legend, loc="upper center", ncol=7, fontsize=8.5,
               bbox_to_anchor=(0.5, 1.0), frameon=False)
    fig.suptitle("Non-linear ONE-SHOT server combines on MNIST MLP — final test acc by combine "
                 "(N=10, mean over seeds 42 & 123)\nbar color = HE depth; "
                 "all operate on the same one-shot {Delta_i}; sync_sgd/centralized are out-of-budget ceilings",
                 y=1.07, fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out = os.path.join(OUT_DIR, "nonlinear_combines.png")
    fig.savefig(out, dpi=130, bbox_inches="tight")
    print(f"wrote {out}", flush=True)


if __name__ == "__main__":
    main()
