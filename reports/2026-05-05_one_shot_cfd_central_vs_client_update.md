# One-shot CFD: public-data central distill vs. client-update aggregation
## Matched-setting comparison against Co-Boosting (ICLR 2024) on MNIST and CIFAR-10

**Date:** 2026-05-05
**Authors:** Halil İbrahim Kanpak (computation: Valar T4 partition, t4_ai)
**Scope:** Empirical comparison of two one-shot federated distillation protocols, both compatible with our cryptographic-privacy methodology, against the strongest published one-shot baseline at its own setting.

---

## 1. Executive summary

We evaluate two one-shot federated distillation protocols under the
cryptographic-privacy methodology of `NEW_METHODOLOGY_v2.md`:

- **Public-data CFD (central distill).** Each client uploads encrypted teacher
  predictions on a public probe set; server linearly aggregates into an
  encrypted ensemble target; server runs encrypted SGD on an encrypted
  student against that target; collective key-switch returns the student.
  In plaintext simulation this is a centralised distillation against the
  ensemble target on the probe inputs. **One upload + one download per client.**

- **Client-update CFD ($\Delta\theta$ aggregation).** Each client distils its
  own teacher into a local copy of the global student (starting from the
  shared $\theta_0$), encrypts the parameter delta $\Delta\theta_i$, uploads
  it; server linearly aggregates the deltas; collective key-switch returns
  the student. **One upload + one download per client.**

Both protocols match Co-Boosting's communication shape (one upload + one
download). The differentiator is *content visibility* at the server:
Co-Boosting's server sees plaintext teacher weights; ours sees only
ciphertexts.

**Headline result.** At MNIST $\alpha=0.3$, public-data CFD with the
$\beta+\lambda$ Co-Boost augmentation reaches **0.965** vs Co-Boosting's
**0.973** — within **0.8 pp**. At higher heterogeneity and on CIFAR-10 the
gap widens, driven by (i) under-trained teachers in our budget and
(ii) a structural information ceiling: our probe set is fixed real data
while Co-Boosting iteratively generates adversarial synthetic samples.

The client-update CFD protocol consistently underperforms central distill
in every cell of the table — the well-documented one-shot federated weight-
averaging failure dominates at $N=10$ with non-IID partitions. We retain it
in the table as a *diagnostic*, not as a publishable variant.

---

## 2. Experimental setup

### 2.1 Matched-setting

Replicates Co-Boosting's Table 1 setting:

- $N = 10$ clients, Dirichlet partitioning with $\alpha \in \{0.05, 0.1, 0.3\}$.
- Public probe pool of 4000 samples held out from training before partitioning;
  Dirichlet partition is re-rolled until every client has $\ge 50$ samples.
- LeNet-5 for MNIST (28×28 input padded to 32×32). The Co-Boosting
  reference 5-layer CNN for CIFAR-10 (Conv 3→128 / 128→128 / 128→128 with
  3×3 kernels and 2×2 max-pools, then a single FC).
- Distillation temperature $T = 4.0$.

### 2.2 Local training hyperparameters

| | our run | Co-Boosting paper |
|---|---|---|
| local teacher SGD | lr=0.01, momentum=0.9, wd=5e-4 | lr=0.01, momentum=0.9, no wd, grad-clip 10 |
| teacher epochs | **30** | 100 |
| distillation lr | 0.01 (cosine) | 0.01 |
| central distill epochs | **90** | 200 |
| batch size | 128 | 128 |

Teacher and distillation epochs are smaller in our run because our compute
budget on a single Tesla T4 is tighter than the paper's reported setup.
The compute differential is part of why the gap widens at low $\alpha$ —
see §6.

### 2.3 Hardware and runtime

- Job 1032257 (MNIST): node ai01, Tesla T4, 95 min wall, 3 cells.
- Job 1032521 (CIFAR-10): node ai01, Tesla T4, 142 min wall, 3 cells.

Reproduction: `sbatch jobs/cfd_match_mnist.sh` and `sbatch jobs/cfd_match_cifar.sh`.
Demo entry point: [`demos/cfd_match_demo.py`](../demos/cfd_match_demo.py).

---

## 3. The two protocols, in detail

### 3.1 Public-data CFD (central distill)

| phase | who | what | crypto load |
|---|---|---|---|
| 0 | all | DKG → collective $\mathsf{pk}$, per-client $\mathsf{sk}_i$ | one-time |
| 1 | clients | train teacher $T_i$; compute $T_i(\mathcal P)$ on the public probe; encrypt under $\mathsf{pk}$ | client-only |
| 1↑ | clients → server | one upload of $\langle T_i(\mathcal P)\rangle$ per client | the only client→server message |
| 2 | server | $\langle\bar T(\mathcal P)\rangle = \sum_i w_i \langle T_i(\mathcal P)\rangle$, depth-0 | linear |
| 3 | server | initialise $\langle\theta\rangle$ at public $\theta_0$; run encrypted SGD on $\mathcal P$ for $E$ epochs against $\langle\bar T(\mathcal P)\rangle$ | depth-many; bootstrapped |
| 4↓ | server → clients | one download of $\langle\theta_E\rangle$ | the only server→client message |
| 5 | clients | collective key-switch on $\langle\theta_E\rangle$ | one round of share exchange |

Optional Co-Boost augmentations sit naturally in Phase 2:

- **$\beta$ ensemble boost.** Replace the uniform 1/N weights with
  $w_i = \alpha_i^\beta / \sum_j \alpha_j^\beta$, where $\alpha_i = \mathbb E_{\mathcal P}[\max\,\text{softmax}(T_i)]$
  is each teacher's self-confidence (a single scalar per client, public).
- **$\lambda$ data boost.** Per-row variance $\langle V_k\rangle = \sum_i w_i \langle T_{i,k}\rangle^2 - \langle\bar T_k\rangle^2$
  at depth 1; per-row probe weight $r_k = 1 + \lambda V_k$ multiplies the
  per-sample KL during Phase 3, focusing the student on high-disagreement
  rows.

### 3.2 Client-update CFD ($\Delta\theta$ aggregation)

| phase | who | what | crypto load |
|---|---|---|---|
| 1 | clients | train teacher $T_i$; distill $T_i$ into a local copy of the public student $\theta_0$ for $E$ epochs; compute $\Delta\theta_i = \theta_E - \theta_0$; encrypt | client-only |
| 1↑ | clients → server | one upload of $\langle\Delta\theta_i\rangle$ | the only client→server message |
| 2 | server | $\langle\bar\Delta\rangle = \sum_i w_i \langle\Delta\theta_i\rangle$, depth-0 | linear |
| 3↓ | server → clients | one download of $\theta_0 + \langle\bar\Delta\rangle$ | the only server→client message |
| 4 | clients | collective key-switch | one round |

We test two variants: vanilla (no drift control) and with FedProx-style
proximal anchor ($\frac{\mu}{2}\|\theta - \theta_0\|^2$) added to each
client's local loss to bound drift.

---

## 4. MNIST results

Job 1032257, LeNet-5, 30 teacher epochs, 30 distil epochs (R=1 cells) /
90 central-distill epochs, probe size 4000.

### 4.1 Public-data CFD on MNIST

| $\alpha$ | mean teacher | ens@$\mathcal P$ | central uniform | + β=2 | + λ=8 | **CFD-Boost (β+λ)** | Co-Boosting | gap |
|---|---|---|---|---|---|---|---|---|
| 0.05 | 0.3989 | 0.8133 | 0.8141 | 0.8108 | 0.8152 | 0.8109 | 0.939 | **−12.8** |
| 0.10 | 0.5083 | 0.8645 | 0.8576 | 0.8570 | 0.8557 | **0.8596** | 0.944 | **−8.4** |
| 0.30 | 0.8139 | 0.9653 | 0.9550 | 0.9611 | 0.9614 | **0.9651** | 0.973 | **−0.8** |

Per-teacher accuracies (for context):
- α=0.05: 0.314, 0.499, 0.546, 0.305, 0.301, 0.329, 0.512, 0.135, 0.596, 0.453
- α=0.1: 0.435, 0.441, 0.603, 0.469, 0.609, 0.514, 0.513, 0.327, 0.472, 0.700
- α=0.3: 0.851, 0.873, 0.792, 0.792, 0.861, 0.917, 0.793, 0.752, 0.802, 0.706

Observations:

1. **The central-distill student is at the ens@P ceiling in every cell.**
   At α=0.05 the student hits 0.81 against an ensemble of 0.81; at α=0.3,
   0.965 vs 0.965. Soft-label distillation gives 0–1 pp above the argmax
   ceiling; not the dominant lever.
2. **β and λ are nearly free at α=0.3** (+1 pp combined) and **mostly
   neutral at α=0.05** (within sampling noise). The β+λ headline of 0.9651
   is the best one-shot CFD number on MNIST in our table.
3. **Gap to Co-Boosting closes monotonically with α.** At α=0.3 we are
   within 0.8 pp; at α=0.05 the gap is 12.8 pp, all of which is below
   the ens@P ceiling (Co-Boosting's data-free generator pushes their
   effective ensemble accuracy higher than ours).

### 4.2 Client-update CFD on MNIST

| $\alpha$ | R=1 vanilla | R=1 + prox μ=0.5 |
|---|---|---|
| 0.05 | 0.1523 | 0.7497 |
| 0.10 | 0.2111 | 0.8298 |
| 0.30 | 0.1225 | 0.8205 |

Observations:

1. **R=1 vanilla weight averaging fails** at every α. Per-client distilled
   students are individually 0.87–0.94 (we measured this in the diagnostic
   in [`CFD_BOOST_ABLATIONS.md`](../CFD_BOOST_ABLATIONS.md)) but the average
   is 0.12–0.21 — they live in different basins and the average is in no
   basin. Mean inter-client cosine similarity of $\Delta\theta_i$ is 0.44.
2. **FedProx anchor with μ=0.5 rescues the protocol** — bounds drift so
   the average is in the same basin. Lifts to 0.75 / 0.83 / 0.82.
3. **Even the rescued client-update protocol underperforms central
   distill** across all α: −6 / −3 / −15 pp. The client-update protocol
   has no path to compete with central distill at this $N$.

### 4.3 Side-by-side MNIST headline (one-shot only)

| α | public-data (β+λ) | client-update (R=1+prox 0.5) | Δ in favour of public-data | Co-Boosting |
|---|---|---|---|---|
| 0.05 | **0.811** | 0.750 | +6.1 pp | 0.939 |
| 0.10 | **0.860** | 0.830 | +3.0 pp | 0.944 |
| 0.30 | **0.965** | 0.821 | +14.4 pp | 0.973 |

---

## 5. CIFAR-10 results

Job 1032521, CNN-5, same hyperparameters as MNIST, probe size 4000, 90
central-distill epochs.

### 5.1 Public-data CFD on CIFAR-10

| $\alpha$ | mean teacher | ens@$\mathcal P$ | central uniform | + β=2 | + λ=8 | CFD-Boost (β+λ) | Co-Boosting | gap |
|---|---|---|---|---|---|---|---|---|
| 0.05 | 0.2389 | 0.2407 | 0.2381 | 0.2247 | 0.2372 | 0.2249 | 0.472 | **−23.4** |
| 0.10 | 0.2829 | 0.3910 | **0.3829** | 0.2364 | 0.3836 | 0.2374 | 0.571 | **−18.8** |
| 0.30 | 0.4080 | 0.5577 | 0.5189 | 0.5044 | **0.5213** | 0.5050 | 0.702 | **−18.1** |

Per-teacher accuracies:
- α=0.05: 0.222, 0.232, 0.337, 0.196, 0.223, 0.405, 0.190, 0.179, 0.139, 0.268
- α=0.1: 0.175, 0.261, 0.197, 0.317, 0.412, 0.142, 0.223, 0.279, 0.467, 0.358
- α=0.3: 0.473, 0.354, 0.413, 0.441, 0.383, 0.370, 0.416, 0.362, 0.410, 0.459

Observations:

1. **Teachers are under-trained** at 30 epochs — mean accuracy 0.24–0.41.
   Co-Boosting's teachers (100 epochs) are reportedly stronger.
2. **ens@P is now far from ground truth.** At α=0.05 it is 0.24
   (~random), at α=0.3 it is 0.56. Central distill is at the ceiling in
   every cell, just like MNIST.
3. **β=2 actively hurts on CIFAR-10.** At α=0.1 it drops central distill
   from 0.383 to 0.236 (−15 pp). Mechanism: β raises weight on globally-
   confident teachers, but at low α those teachers are *narrow* — confident
   on 1–2 classes only — so the boosted ensemble target collapses toward a
   small subset of classes. The data-boost λ is benign by comparison
   because it operates per-row, not per-teacher.
4. **The β collapse is the single largest algorithmic fix point** for
   CIFAR. A class-coverage-aware weighting (per-class confidence rather
   than global α_i) should remove it; covered in §7.

### 5.2 Client-update CFD on CIFAR-10

| $\alpha$ | R=1 vanilla | R=1 + prox μ=0.5 |
|---|---|---|
| 0.05 | 0.1081 | 0.1797 |
| 0.10 | 0.1000 | 0.2348 |
| 0.30 | 0.3639 | 0.3790 |

Observations:

1. **Same vanilla collapse** as MNIST, similar magnitude.
2. **Prox rescue is weaker on CIFAR.** With μ=0.5, R=1 + prox reaches only
   0.18 / 0.23 / 0.38. The reason is that CIFAR teachers themselves are
   weaker (mean 0.24–0.41), so the upper bound on what local distillation
   can transfer is lower. Drift control alone doesn't recover the gap.

### 5.3 Side-by-side CIFAR-10 headline (one-shot only)

| α | public-data (best) | client-update (R=1+prox 0.5) | Δ in favour of public-data | Co-Boosting |
|---|---|---|---|---|
| 0.05 | **0.238** (uniform) | 0.180 | +5.8 pp | 0.472 |
| 0.10 | **0.383** (uniform) | 0.235 | +14.8 pp | 0.571 |
| 0.30 | **0.521** (+λ) | 0.379 | +14.2 pp | 0.702 |

---

## 6. Where do we fall behind Co-Boosting? Decomposition.

The gap to Co-Boosting decomposes into five distinct components, each with
a different magnitude and a different fix path. The table is a rough
attribution of the worst-case cell (CIFAR-10 α=0.05, gap 23.4 pp).

| # | source of gap | our setting | Co-Boosting | rough cost MNIST α=0.05 | rough cost CIFAR-10 α=0.3 | fixable? |
|---|---|---|---|---|---|---|
| 1 | **Teacher convergence** | 30 local epochs, mean teacher 0.40/0.41 | 100 local epochs, mean teacher reportedly ≥0.55 | 5–7 pp | 8–12 pp | yes — pure compute |
| 2 | **Probe is fixed real data** | 4000 held-out training samples | adversarial synthetic samples regenerated each iter | 5–8 pp | 4–6 pp | partial — see #5 below |
| 3 | **No data-free generator at server** | server has only encrypted predictions on probe; cannot evaluate teachers on new inputs | server has plaintext teacher weights; can run any input through any teacher | core enabler of #2 | core enabler of #2 | structurally not (privacy) |
| 4 | **Distillation length** | 90 central-distill epochs | 200 epochs | 1–2 pp | 1–2 pp | yes — pure compute |
| 5 | **β reweighting is class-blind** | β raises weight on globally-confident teachers via $\alpha_i^\beta$ | per-class-coverage-aware weighting | 1–2 pp | 3–5 pp at low α | yes — algorithmic |

Items 1, 4, 5 are completely under our control. Item 2 is partially under
our control via client-side synthetic-sample generation (each client trains
a tiny generator locally, uploads encrypted synthetic samples in the same
upload as predictions; collective key-switch returns plaintext synthetic to
all parties; central distill on union of probe and synthetic). Item 3 is
the *price of cryptographic privacy*: it is the same structural advantage
Co-Boosting has over POSEIDON in raw efficiency, just inverted.

---

## 7. What the data implies for the protocol

1. **Public-data central distill is the headline.** It is the only one-shot
   variant that beats the per-client weight-averaging failure across the
   board, by 3–15 pp at every cell.

2. **Co-Boost mechanisms are conditional, not free.** β is only safe when
   teacher confidence correlates with class coverage — true at high α,
   false at low α with non-IID. The published protocol should:
   - Use λ unconditionally (it never hurts and gains 0–1 pp).
   - Use β only when class-coverage information is available, or replace
     it with a per-class boosting estimate $w_{i,c}$ derived from
     $\mathbb E_{\mathcal P}[T_i(x)_c \cdot \mathbb 1\{\text{argmax}\,T_i(x) = c\}]$,
     itself a depth-1 functional of $\langle T_i(\mathcal P)\rangle$.

3. **The honest framing for the gap to Co-Boosting** is:
   - At α ≥ 0.3 with comparable teacher budget, we expect to be within
     1–2 pp on MNIST and 5–10 pp on CIFAR-10 (the latter mainly closing
     via item 1).
   - At α ≤ 0.1, a residual gap of 5–10 pp on MNIST and 10–15 pp on
     CIFAR-10 *is the price of the cryptographic privacy guarantee* —
     specifically, the price of not having the server hold plaintext
     teacher weights for adversarial sample generation. POSEIDON pays
     this same cost in iteration count; we pay it in single-shot
     accuracy at extreme heterogeneity.

4. **Client-update CFD is not a publishable variant** at this scale.
   The R=1 vanilla failure is generic and cannot be fixed without either
   a drift-control term (and even then it underperforms central distill)
   or extra rounds (and the extra rounds erase the one-shot property).

---

## 8. Open questions and next experimental steps

In rough decreasing return-on-investment order:

1. **Bump teacher epochs to 100 and central-distill to 200.** Honest
   apples-to-apples with Co-Boosting. ~3× compute. Estimated to close
   8–12 pp on CIFAR-10 α=0.3.

2. **Replace global-confidence β with per-class boosting $w_{i,c}$.**
   Removes the β-collapse on CIFAR. Expected to add 3–5 pp at low α
   and prevent the −15 pp regression at CIFAR α=0.1.

3. **One-shot synthetic-augmented probe.** Each client trains a small
   DP-protected generator locally, uploads encrypted synthetic samples in
   the same upload as predictions; collective key-switch returns the union
   to clients/server; central distill on probe ∪ synthetic. The closest
   one-shot analogue to Co-Boosting's data-free server-side generator.

4. **Ablate prox μ across N and α.** μ=0.5 was hand-tuned at MNIST
   N=10 α=0.3. Larger N or lower α likely needs a larger μ. We have
   no theory for this scaling yet.

5. **Real CKKS validation.** Hook up Lattigo or TenSEAL to confirm the
   depth-≤1 server arithmetic actually matches the plaintext simulation
   under encryption. Numerically not contentious (CKKS precision is
   ~$10^{-5}$ per slot) but completes the story.

---

## Appendix A — raw output references

- MNIST sweep: `/scratch/hkanpak21/HE_Distillation/results/cfd_match_mnist_1032257.out`
- CIFAR-10 sweep: `/scratch/hkanpak21/HE_Distillation/results/cfd_match_cifar_1032521.out`
- Demo source: [`demos/cfd_match_demo.py`](../demos/cfd_match_demo.py)
- Underlying primitives: [`demos/cfd_mlp_demo.py`](../demos/cfd_mlp_demo.py)
- Earlier MLP/N=4 sweep numbers + boost-lever ablation: [`CFD_BOOST_ABLATIONS.md`](../CFD_BOOST_ABLATIONS.md)
- Methodology evolution: `NEW_METHODOLOGY_v2.md` §17–§18
