# Reported results — prior-work comparator table

> ## ⚠ DO NOT QUOTE THE `?` CELLS WITHOUT VERIFYING THEM ⚠
>
> Every cell in this document that carries a `?` is a **best-effort recollection by the LLM that drafted this file (Claude Opus 4.7), not a paper-extracted number**. LLM memory of specific table cells is unreliable. The order of magnitude is usually right; the exact percentage point is often wrong; the column-to-column ranking is often wrong; the (N, α, ε) cell I cite may not exist in the paper at all.
>
> Treat the structure of this document (which methods, which datasets, which settings) as a useful scaffold, and treat the **numbers** in `?`-marked cells as placeholders. Before any of them appears in a manuscript, slide deck, cover letter, or comparison plot, open the paper's published PDF (or the most recent arXiv version), find the relevant table, and **replace the value verbatim**. The checklist at the bottom of this file (`## Verification list`) tracks which papers still need that pass.
>
> Cells without `?` are values I have independent confidence in (either reproduced elsewhere or known with high certainty). Cells marked `n/r` are settings the paper does not report at all in any close row. Cells marked `n/a` are settings where the comparison is not meaningful.

Numbers in this document come from the **published papers** of each method (and where ambiguous, from the corresponding arXiv version). Nothing here is a rerun on our side; this is a literature table to anchor what each prior work claims at the settings they evaluated — once the `?` cells are verified against the papers.

When their setting differs from ours (different `N`, different `α`, different model, different dataset), we record what they actually used. We **do not** extrapolate.

The companion folder `comparators/<method>/` holds a shallow clone of each method's reference implementation. `COMMIT.txt` in each subdirectory pins the upstream URL + branch + SHA.

---

## Cheatsheet — at-a-glance summary

| # | Method | Paper / Year | Crypto | Probe / data assumption | Datasets in paper | Notes |
|---|---|---|---|---|---|---|
| 1 | **FedMD** | Li & Wang, NeurIPS-W 2019 (arXiv:1910.03581) | plaintext | Public probe (shared dataset, often a different label space from the private one) | MNIST (public) ↔ EMNIST-letters (private); CIFAR-10 (public) ↔ CIFAR-100 subset (private) | Defined the public-probe one-shot KD pattern; heterogeneous client architectures |
| 2 | **DS-FL** | Itahara et al., IEEE TMC 2021 (arXiv:2008.06180) | plaintext | Public probe (same domain as private) | FashionMNIST, CIFAR-10 | Same-domain probe variant of FedMD; entropy-reduced soft labels |
| 3 | **FedDF** | Lin et al., NeurIPS 2020 (arXiv:2006.07242) | plaintext | Unlabeled "auxiliary" dataset on server | CIFAR-10, CIFAR-100, AG-News | One-round ensemble distillation; tolerates model heterogeneity |
| 4 | **DENSE** | Zhang et al., NeurIPS 2022 (arXiv:2112.12371) | plaintext, **data-free** | None — generator-only | FashionMNIST, CIFAR-10, CIFAR-100, Tiny-ImageNet | Server trains a generator on plaintext client weights; no probe |
| 5 | **Co-Boosting** | Dai et al., ICLR 2024 (arXiv:2402.15070) | plaintext, **data-free** | None — adversarial generator | CIFAR-10, CIFAR-100, Tiny-ImageNet | Current SOTA for plaintext data-free one-shot FL |
| 6 | **FedDiff** | Mendieta et al., WACV 2025 (arXiv:2405.01494) | DP via diffusion generator (server-side) | DP-synthetic samples from a server-side diffusion model | CIFAR-10, CIFAR-100, Tiny-ImageNet | Primary γ-variant comparator — same problem space, plaintext channel |
| 7 | **FedKT** | Li et al., AAAI 2021 (arXiv:2010.01017) | DP via PATE | Public unlabeled set | MNIST, FashionMNIST, SVHN, CIFAR-10 + tabular | Canonical PATE-style DP one-shot FL |
| 8 | **POSEIDON** | Sav et al., NDSS 2021 (arXiv:2009.00349) | HE (multiparty CKKS) | None — full encrypted training | MNIST, CIFAR-10/100, breast-cancer, ESR (medical) | Multi-round HE-FL (not one-shot); same crypto primitives as ours |

---

## 1. FedMD (Li & Wang, NeurIPS-W 2019)

**Setting they evaluate.** Public dataset = MNIST or CIFAR-10. Private (per-client) dataset = EMNIST-letters or CIFAR-100 subset, partitioned so each of `N=10` clients holds a different subset of classes. Each client uses its own architecture (2-layer MLPs through ResNets). Evaluation is on the private-task test set.

**Published numbers (paraphrased from their Table 1 / Table 2 — verify on paper before quoting):**

| Setting | N | Public | Private (eval) | Mean teacher | FedMD student | Gap (student − mean teacher) |
|---|---|---|---|---|---|---|
| FEMNIST_Balanced | 10 | MNIST | EMNIST-letters (balanced) | ≈ 70.1 % `?` | ≈ 76.5 % `?` | ≈ +6.4 pp `?` |
| FEMNIST_Imbalanced | 10 | MNIST | EMNIST-letters (skewed) | ≈ 51 % `?` | ≈ 70 % `?` | ≈ +19 pp `?` |
| CIFAR_Balanced | 10 | CIFAR-10 | CIFAR-100 (subset of 20 classes) | ≈ 33 % `?` | ≈ 56 % `?` | ≈ +23 pp `?` |

All values marked `?` need direct paper-table verification — they're my best recollection of the order-of-magnitude.

**Apples-to-apples with our v1:** **not directly**. FedMD uses heterogeneous-task partitioning (different label spaces), not Dirichlet-on-the-same-task. The methodology comparison is structural ("public-probe KD"), not numerical.

---

## 2. DS-FL (Itahara et al., IEEE TMC 2021)

**Setting they evaluate.** Same-domain public probe (~5–10 % of training data carved off as the shared probe). Dirichlet partitioning of the rest. Evaluated at `N=10` and `N=100`.

**Published numbers (their Tables 2 and 3 — verify):**

| Dataset | N | α | DS-FL student | FedAvg baseline | Notes |
|---|---|---|---|---|---|
| FashionMNIST | 10 | IID | ≈ 87 % `?` | ≈ 89 % `?` | FedAvg slightly ahead at IID |
| FashionMNIST | 10 | non-IID (α=0.1?) | ≈ 80 % `?` | ≈ 70 % `?` | DS-FL pulls ahead at non-IID |
| CIFAR-10 | 10 | IID | ≈ 72 % `?` | ≈ 75 % `?` | |
| CIFAR-10 | 10 | non-IID | ≈ 60 % `?` | ≈ 45 % `?` | |

All `?` values need paper verification.

**Apples-to-apples with our v1:** closest fit so far — same dataset family (FashionMNIST / CIFAR-10), Dirichlet partition, public probe of ~5 % size. We don't have DS-FL's exact α/N grid; will need to do paper inspection.

---

## 3. FedDF (Lin et al., NeurIPS 2020)

**Setting they evaluate.** Each of `N=20` clients trains a local model (ResNet-8 / ResNet-20 etc.). Server holds an unlabeled "auxiliary" dataset. After one round of local training, server distils the ensemble of client models into a student via prediction-matching on the auxiliary dataset.

**Published numbers (their Table 1, paraphrased — verify):**

| Dataset | N | α (Dirichlet) | Local model | Student (FedDF) | FedAvg | Notes |
|---|---|---|---|---|---|---|
| CIFAR-10 | 20 | 0.1 | ResNet-8 | ≈ 78 % `?` | ≈ 70 % `?` | FedDF gains +8 pp at non-IID |
| CIFAR-10 | 20 | 1.0 | ResNet-8 | ≈ 83 % `?` | ≈ 81 % `?` | Closer at near-IID |
| CIFAR-100 | 20 | 0.1 | ResNet-8 | ≈ 35 % `?` | ≈ 28 % `?` | |
| CIFAR-100 | 20 | 1.0 | ResNet-8 | ≈ 47 % `?` | ≈ 45 % `?` | |
| AG-News | 20 | non-IID | DistilBERT | ≈ 87 % `?` | ≈ 83 % `?` | |

**Apples-to-apples with our v1:** closer than FedMD; same Dirichlet partitioning, similar α range (0.1, 1.0). But N=20 vs our `{1..32}` sweep, ResNet-8 vs our MLP, server-side ensemble distillation step vs our client-side. The "ensemble distillation gives biggest gain at non-IID" finding mirrors what we observed at N=32 / α=0.1.

---

## 4. DENSE (Zhang et al., NeurIPS 2022)

**Setting they evaluate.** Data-free: server trains a generator on the plaintext concatenation of client models (no probe, no client-side data). Evaluated `N=10`, Dirichlet α ∈ {0.05, 0.1, 0.3, 0.5}.

**Published numbers (their Table 1, paraphrased — verify):**

| Dataset | N | α | DENSE student | FedAvg | FedDF | Notes |
|---|---|---|---|---|---|---|
| FashionMNIST | 10 | 0.05 | ≈ 71 % `?` | ≈ 35 % `?` | ≈ 67 % `?` | |
| FashionMNIST | 10 | 0.1 | ≈ 75 % `?` | ≈ 52 % `?` | ≈ 71 % `?` | |
| CIFAR-10 | 10 | 0.05 | ≈ 41 % `?` | ≈ 21 % `?` | ≈ 33 % `?` | |
| CIFAR-10 | 10 | 0.1 | ≈ 51 % `?` | ≈ 28 % `?` | ≈ 47 % `?` | |
| CIFAR-100 | 10 | 0.05 | ≈ 22 % `?` | ≈ 8 % `?` | ≈ 18 % `?` | |
| Tiny-ImageNet | 10 | 0.05 | ≈ 14 % `?` | ≈ 4 % `?` | ≈ 9 % `?` | |

**Apples-to-apples with our v1:** closest in N (=10) and α range (0.1 is the same as ours). DENSE has no probe, ours has one, so the comparison is across two different problem variants. Their FashionMNIST α=0.1 number (~75 %) is in the same ballpark as our N=2 student on MNIST (67 %); CIFAR-10 α=0.1 (~51 %) is in the same ballpark as our N=8 (53 %).

---

## 5. Co-Boosting (Dai et al., ICLR 2024)

**Setting they evaluate.** Data-free one-shot FL. Server holds a generator co-trained with the ensemble of client models. Adversarial objective: generator finds inputs that maximise teacher disagreement; student distils from teacher predictions on these synthetic inputs. Evaluated `N ∈ {5, 10}`, Dirichlet `α ∈ {0.1, 1.0}`, ResNet-18 backbone.

**Published numbers (their Table 1 / 2, paraphrased — verify):**

| Dataset | N | α | Co-Boosting student | DENSE | FedDF | Best individual teacher |
|---|---|---|---|---|---|---|
| CIFAR-10 | 5 | 0.1 | ≈ 63 % `?` | ≈ 57 % `?` | ≈ 41 % `?` | ≈ 35 % `?` |
| CIFAR-10 | 5 | 1.0 | ≈ 80 % `?` | ≈ 79 % `?` | ≈ 70 % `?` | ≈ 78 % `?` |
| CIFAR-10 | 10 | 0.1 | ≈ 62 % `?` | ≈ 55 % `?` | ≈ 39 % `?` | ≈ 26 % `?` |
| CIFAR-100 | 5 | 0.1 | ≈ 39 % `?` | ≈ 32 % `?` | ≈ 21 % `?` | ≈ 16 % `?` |
| Tiny-ImageNet | 5 | 0.1 | ≈ 16 % `?` | ≈ 11 % `?` | ≈ 7 % `?` | ≈ 6 % `?` |

**Apples-to-apples with our v1:** the **closest non-DP comparator**. Same `N=5..10`, same `α=0.1`. Their CIFAR-10 N=10 α=0.1 ≈ 62 % is the "privacy-unaware ceiling" we aim to approach with an HE protocol. We are on a different dataset (MNIST) and different model (MLP vs ResNet-18), so direct numerical comparison requires us to add CIFAR-10 + ResNet to our pipeline before claiming parity.

---

## 6. FedDiff (Mendieta et al., WACV 2025)

**Setting they evaluate.** Server trains a DP-diffusion generator (DP-SGD with target `(ε, δ)` budget). Distils the ensemble of client teachers on plaintext synthetic samples from the diffusion model. Reported `(ε, δ)` budgets: `(2, 1e-5)`, `(5, 1e-5)`, `(10, 1e-5)`. `N=5, 10`.

**Published numbers (their Table 1, paraphrased — verify; upstream code at `mmendiet/FedDiff` is still a placeholder so we can't run the smoke):**

| Dataset | N | α | ε | FedDiff student | Co-Boosting (DP) | FedKT |
|---|---|---|---|---|---|---|
| CIFAR-10 | 5 | 0.1 | 10 | ≈ 55 % `?` | n/a | ≈ 45 % `?` |
| CIFAR-10 | 10 | 0.1 | 10 | ≈ 53 % `?` | n/a | ≈ 41 % `?` |
| CIFAR-10 | 10 | 0.1 | 1 | ≈ 35 % `?` | n/a | ≈ 22 % `?` |
| CIFAR-100 | 10 | 0.1 | 10 | ≈ 28 % `?` | n/a | ≈ 19 % `?` |

**Apples-to-apples with our v1:** the **closest DP comparator** but on different data + model. v1 carries no DP at all; the γ-variant of our protocol is what would line up against FedDiff's `ε=10` row. We don't have a γ-variant implementation yet.

**Caveat.** Upstream code is unreleased. We cannot reproduce these numbers ourselves; only paper claims.

---

## 7. FedKT (Li et al., AAAI 2021)

**Setting they evaluate.** PATE-style: client-trained teachers vote on a public unlabeled set; the aggregated noisy-max votes are used to label the public set; a server-side student trains on those labels. DP guarantee through the PATE accountant. `N ∈ {10, 30}`, `ε ∈ {2, 4, 8}`.

**Published numbers (their Table 2 / 3, paraphrased — verify):**

| Dataset | N | ε | FedKT student | DP-SGD baseline | Notes |
|---|---|---|---|---|---|
| MNIST | 10 | 2 | ≈ 96 % `?` | ≈ 90 % `?` | |
| MNIST | 10 | 8 | ≈ 98 % `?` | ≈ 94 % `?` | |
| FashionMNIST | 10 | 2 | ≈ 84 % `?` | ≈ 76 % `?` | |
| CIFAR-10 | 10 | 8 | ≈ 65 % `?` | ≈ 52 % `?` | |
| SVHN | 10 | 8 | ≈ 81 % `?` | ≈ 75 % `?` | |

**Apples-to-apples with our v1:** same datasets (MNIST present!), same N=10. But FedKT carries a DP budget that v1 does not; the comparison is "FedKT at ε=∞ (no privacy) vs v1 (no DP, encrypted channel)". FedKT does not publish an ε=∞ ablation, so we can only line up the structural argument.

---

## 8. POSEIDON (Sav et al., NDSS 2021)

**Setting they evaluate.** Multi-round federated NN training entirely under multiparty CKKS — every gradient, every aggregation, every forward pass is on ciphertexts. Reported on MNIST (LeNet-5), CIFAR-10 (CNN), breast-cancer (logistic regression). Not one-shot — typical 100+ communication rounds.

**Published numbers (their Table 4 / 5, paraphrased — verify):**

| Dataset | Model | N | Accuracy (POSEIDON / plaintext baseline) | Rounds | Wall-clock |
|---|---|---|---|---|---|
| MNIST | LeNet-5 | 10 | 95.6 % `?` / 95.8 % `?` | 100 `?` | ~ 13 h `?` |
| MNIST | LeNet-5 | 50 | 95.4 % `?` / 95.7 % `?` | 100 `?` | ~ 35 h `?` |
| CIFAR-10 | CNN | 10 | 65 % `?` / 67 % `?` | 200 `?` | ~ 39 h `?` |
| breast-cancer | logreg | 10 | 96.8 % `?` / 97.1 % `?` | — | ~ 30 min `?` |

**Apples-to-apples with our v1:** POSEIDON's **accuracy** track is essentially "FedAvg-on-ciphertexts at convergence" — they expect to match plaintext within ~0.5 pp. Their interesting axis is **wall-clock and communication**, which is orders of magnitude beyond what one-shot HE-IFD pays.

Our v1 should approach POSEIDON's accuracy ceiling (or stay below by < 5 pp) while paying a single round of encrypted aggregation, not 100+ rounds.

---

## What this table is for

1. **Sanity check our v1 numbers** against what each closest neighbour reports. (Today: our N=32 / MNIST / α=0.1 student at 71.20 % is on the same order of magnitude as DENSE / Co-Boosting at α=0.1 on small models; we are below their ResNet-18 numbers because we run an MLP.)
2. **Pin which method we line up against on each axis of the resubmission paper:**
   - Plaintext one-shot **utility ceiling**: Co-Boosting.
   - DP one-shot **utility-privacy frontier**: FedDiff (γ-variant comparator), FedKT (tabular).
   - HE **crypto-stack peer**: POSEIDON (multi-round) — we differentiate on the one-shot axis.
   - Public-probe **methodology lineage**: FedMD, DS-FL — we cite as origins.
3. **Document gaps**: every `?` is a paper-inspection task. Before any of these numbers go into the manuscript they need to come from the paper's actual table, not from my recollection.

## Verification list (TODO)

Each line below = "open the paper's published version, transcribe the cited cells verbatim, drop the `?` mark". Until the line is checked off, **every `?` row in that paper's section should be treated as LLM hallucination at the digit level** even if the structure (datasets, model, N range, α range) is right.

- [ ] FedMD Table 1 + Table 2 — MNIST↔EMNIST-letters balanced + imbalanced
- [ ] DS-FL Tables 2 and 3 — FashionMNIST / CIFAR-10 at N=10
- [ ] FedDF Table 1 — CIFAR-10 / CIFAR-100 at N=20 across α
- [ ] DENSE Table 1 — FashionMNIST / CIFAR-10 / CIFAR-100 / Tiny-ImageNet at N=10 across α
- [ ] Co-Boosting Table 1 + Table 2 — CIFAR-10 / CIFAR-100 / Tiny-ImageNet at N∈{5, 10} across α∈{0.1, 1.0}
- [ ] FedDiff Table 1 — CIFAR-10 / CIFAR-100 at N∈{5, 10} across ε∈{1, 2, 5, 10}
- [ ] FedKT Table 2 + Table 3 — MNIST / FashionMNIST / SVHN / CIFAR-10 across ε∈{2, 4, 8} at N=10
- [ ] POSEIDON Tables 4 and 5 — MNIST / CIFAR-10 / breast-cancer accuracy + wall-clock + rounds at N=10

When these are done, this file becomes a paper-citable reference table rather than a draft.
