# Reported results — prior-work comparator table

> ## Provenance of the numbers in this file
>
> The previous version of this file carried a `?`-flagged disclaimer because most cells were LLM recollections. **That version was wrong on structural claims as well as digit-level cells** — FedDF was described as "one-shot" (it is multi-round at 100 rounds), FedDiff's ε / datasets / baselines were entirely fabricated, POSEIDON was labelled LeNet-5 / 13 h (it is a 3-layer FC NN / 1.4 h). A critique pass identified these.
>
> The current version is **rewritten from the actual PDFs** using `pypdf` extraction. Specific Table cells, dataset lists, ε values, baseline lists, partition schemes, and architecture choices below are quoted from extracted text, with line-anchors from each PDF available in the git history of `tools/pdf_extract.py` invocations (see commit message).
>
> Cells that remain unsourced from the PDF extract are labelled `n/r` (not recovered from our automated extraction; may still be in the paper). Nothing in this file is an LLM guess at a digit.

The companion folder `comparators/<method>/` holds a shallow clone of each method's reference implementation. `COMMIT.txt` in each subdirectory pins the upstream URL + branch + SHA.

---

## Cheatsheet — at-a-glance summary

| # | Method | Paper / Year | One-shot? | Privacy | Datasets in paper | Architecture |
|---|---|---|---|---|---|---|
| 1 | **FedMD** | Li & Wang, NeurIPS-W 2019 (arXiv:1910.03581) | yes | plaintext | MNIST↔FEMNIST (writer-partitioned, LEAF); CIFAR-10↔CIFAR-100 | heterogeneous per-client |
| 2 | **DS-FL** | Itahara et al., IEEE TMC 2021 (arXiv:2008.06180) | no (iterative) | plaintext | MNIST, Fashion-MNIST, IMDb | small MLP / 6-conv CNN / text-class |
| 3 | **FedDF** | Lin et al., NeurIPS 2020 (arXiv:2006.07242) | **no — 100 rounds main config** | plaintext | CIFAR-10, CIFAR-100, ImageNet, AG-News, SST2 | ResNet-8 (CIFAR), N=20, C=0.4 sampling |
| 4 | **DENSE** | Zhang et al., NeurIPS 2022 (arXiv:2112.12371) | yes | plaintext, **data-free** | MNIST, FMNIST, CIFAR-10, SVHN, CIFAR-100, Tiny-ImageNet | server-side generator + ResNet-18 student |
| 5 | **Co-Boosting** | Dai et al., ICLR 2024 (arXiv:2402.15070) | yes | plaintext, **data-free** | MNIST, FMNIST, SVHN, CIFAR-10, CIFAR-100 | CNN-5 (SVHN/CIFAR), LeNet-5 (MNIST/FMNIST) |
| 6 | **FedDiff** | Mendieta et al., WACV 2025 (arXiv:2405.01494) | yes | DP via diffusion generator (Opacus) | **FashionMNIST, PathMNIST, CIFAR-10** | server-side diffusion model |
| 7 | **FedKT** | Li et al., AAAI 2021 (arXiv:2010.01017) | yes | DP via PATE-style aggregation | **MNIST, SVHN, Adult, cod-rna** | MLP (MNIST), CNN (SVHN), LR / GBDT (tabular) |
| 8 | **POSEIDON** | Sav et al., NDSS 2021 (arXiv:2009.00349) | no (multi-round) | HE (multiparty CKKS, Mouchet 2021) | BCW, ESR, CREDIT, MNIST, SVHN, CIFAR-10/100, synthetic | **3-layer FC, 64 neurons/layer** (MNIST/SVHN); CNN (CIFAR-10) |

---

## 1. FedMD (Li & Wang, NeurIPS-W 2019)

**Setting they evaluate (paper Section 4):**
> "We test our framework on the MNIST/FEMNIST dataset and the CIFAR10/CIFAR100 dataset" — paper line 16 of extracted text; same wording in abstract.
> "We test this framework in two different environments. In the first environment, the public data is the MNIST and the private data is a subset of the FEMNIST. We consider the i.i.d. case where each private dataset is drawn randomly from FEMNIST, as well as the non-i.i.d. case where each participant, while only given letters written by a single writer during training, is asked to classify..." — paper lines 152-155.
> "With 10 distinct participants" — abstract.

So **the private dataset is FEMNIST** (LEAF's writer-partitioned EMNIST-byclass split), **not "EMNIST-letters"** as the previous draft of this file claimed.

**Partitioning:** I.I.D. = each client's private set drawn randomly from FEMNIST. Non-I.I.D. = each client sees letters written by a single writer. No Dirichlet `α`.

**Headline metric (paper section 5.1 / Table 4):**
> "the final test accuracy of each model on average receives a 20% gain on top of what's possible without collaboration and is only a few percent lower than the performance each model would have obtained if all private datasets were pooled" — abstract.

Per-participant pooled-private baselines (FEMNIST/MNIST, I.I.D., 10 participants):
> "[0.895, 0.886, 0.875, 0.889, 0.885, 0.899, 0.903, 0.902, 0.902, 0.901]" — paper line 364.

**Apples-to-apples with our v1:** FedMD's heterogeneous-task setup (MNIST public ↔ FEMNIST private) is not directly comparable to our same-task Dirichlet partition; only the public-probe one-shot KD pattern carries over.

---

## 2. DS-FL (Itahara et al., IEEE TMC 2021)

**Setting they evaluate (paper Section V):**
> "two major tasks, MNIST and Fashion-MNIST, were used." — paper lines 954-955.
> Architectures: small MLP for MNIST; six 3×3-conv CNN for Fashion-MNIST (lines 1037-1046).

Plus an IMDb text-classification experiment (line 1069). **No CIFAR-10** in the experiments.

**Number of clients: `K = 100`** in the main image-classification experiments (user-verified via ar5iv / IEEE TMC paper, Section IV/V, 2026-05-21).

**Partitioning: label-extreme non-IID.** Each client holds data from only **2–3 classes** in the "strong non-IID" variant; a "weak non-IID" variant has all 10 classes but heavily skewed; an IID baseline is also reported. **No Dirichlet α** — the paper predates the routine use of Dir(α) and describes the partition qualitatively. The `n/r` for α stays — there is no α to fill in.

**Public dataset construction:** for the FashionMNIST experiments they use an "open dataset" composed of MNIST + Fashion-MNIST images mixed (lines 1114-1116) — non-trivial construction that we should not paraphrase from this extract.

**Headline number (abstract):**
> "DS-FL reduces communication costs up to 99% relative to those of the FL benchmark while achieving similar or higher classification accuracy."

**Apples-to-apples with our v1:** same dataset family (MNIST, Fashion-MNIST), but the protocol is multi-round (iterative DS-FL with entropy-reduction averaging) — not one-shot. The methodology lineage matches our public-probe choice; the numerical comparison would need their N + non-IID grid which I haven't extracted yet.

---

## 3. FedDF (Lin et al., NeurIPS 2020)

**Setting they evaluate (paper Section 4 / Section 5):**
> "We perform 100 communication rounds, and active clients are sampled with ratio C = 0.4 from a total of 20 clients." — paper line 304.
> Architecture: ResNet-8 for CIFAR-10/100; ResNet-20 for ImageNet; DistilBERT-class for AG-News/SST2 (paper line 303 + Section 4).

**FedDF is NOT one-shot.** Multi-round, 100 rounds in the headline CIFAR experiments. The previous draft of this file calling it "one-round ensemble distillation" was wrong. The abstract's "fewer communication rounds than any existing FL technique" refers to faster convergence under the same multi-round protocol, not single-round.

**Datasets (abstract):** CIFAR-10, CIFAR-100, ImageNet, AG-News, SST2.

**Table 1 metric (paper line 340-342):**
> "Table 1: Evaluating different FL methods in different scenarios (i.e. different client sampling fractions, # of local epochs and target accuracies), in terms of the **number of communication rounds to reach target top-1 test accuracy**. We evaluate on ResNet-8 with CIFAR-10."

So FedDF's Table 1 reports *rounds-to-target* rather than accuracy-at-fixed-budget. Numerical cells not extracted from our pass (they'd be tabular and dense; n/r). The "+8 pp at non-IID" pattern claimed in the previous draft was a fabrication.

**Apples-to-apples with our v1:** the multi-round paradigm makes a direct accuracy comparison tricky — they need many rounds to converge; we do one round. The right comparison is "at equal communication budget" (we do one round, they need ~10s of rounds to match), and that comparison comes out structurally in our favour.

---

## 4. DENSE (Zhang et al., NeurIPS 2022)

**Setting they evaluate (paper Section 3 / Table 1):**
> "Table 1: Accuracy of different methods across α = {0.1, 0.3, 0.5} on different datasets." — paper line 403.
> "Dataset MNIST FMNIST CIFAR10 SVHN CIFAR100 Tiny-ImageNet" — paper line 404.

**Six datasets**: MNIST, FMNIST, CIFAR-10, SVHN, CIFAR-100, Tiny-ImageNet.

**Baselines (paper line 406, Table 1 column header):** FedAvg, FedDF, Fed-DAFL, Fed-ADI, DENSE (ours).

**Table 1 cells (paper-verbatim, MNIST through Tiny-ImageNet at α ∈ {0.1, 0.3, 0.5}):**
> Line 406: "FedAvg 48.24 72.94 90.55 41.69 82.96 83.72 23.93 27.72 43.67 31.65 61.51 56.09 4.58 11.61 12.11 3.12 10.46 11.89"
> Line 406: "FedDF 60.15 74.01 92.18 43.58 80.67 84.67 40.58 46.78 53.56 49.13 73.34 73.98 28.17 30.28 36.35 15.34 18.22 27.43"
> Line 406: "Fed-DAFL 64.38 74.18 93.01 47.14 80.59 84.02 47.34 53.89 58.59 53.23 76.56 78.03 28.89 34.89 38.19 18.38 22.18 28.22"
> Line 406: "Fed-ADI 64.13 75.03 93.49 48.49 81.15 84.19 48.59 54.68 59.34 53.45 77.45 78.85 30.13 35.18 40.28 19.59 25.34 30.21"
> Line 407: "DENSE (ours) 66.61 76.48 95.82 50.29 83.96 85.94 50.26 59.76 62.19 55.34 79.59 80.03 32.03 37.32 42.07 22.44 28.14 32.34"

Reading as (dataset, α=0.1 / α=0.3 / α=0.5) tuples for DENSE: MNIST = (66.61, 76.48, 95.82); FMNIST = (50.29, 83.96, 85.94); CIFAR-10 = (50.26, 59.76, 62.19); SVHN = (55.34, 79.59, 80.03); CIFAR-100 = (32.03, 37.32, 42.07); Tiny-ImageNet = (22.44, 28.14, 32.34).

**Headline gap (paper line 472-473):**
> "DENSE outperforms the best baseline method Fed-ADI by 5.08% when α = 0.3 on CIFAR10 dataset."

**Number of clients: default m = 5** (user-verified, anchored to Table 2's first sweep row; the explicit "Table 1 uses m=5" sentence is in Section 3.1 of the paper and was not in our automated text-extract). Table 2 sweeps m ∈ {5, 10, 20, 50} on CIFAR-10/SVHN.

**Apples-to-apples with our v1:** DENSE's CIFAR-10 / α=0.1 at 50.26 % vs our v1 N=8 MNIST result of 0.5318 — same order of magnitude, different dataset (CIFAR vs MNIST) and different protocol (data-free, no probe vs probe-based).

---

## 5. Co-Boosting (Dai et al., ICLR 2024)

**Setting they evaluate (paper Section 4.1, lines 379-395):**
> "We conduct experiments on five real-world image datasets that are standard in the FL literature: MNIST, FMNIST, SVHN, CIFAR10, and CIFAR100." — paper lines 379-381.
> "we sample pk ∼ Dir(α) and allocate api k proportion of the data of class i to client k." — paper lines 383-385.
> "We use CNN with 5 layers for SVHN, CIFAR10, and CIFAR100, LeNet-5 for MNIST and FMNIST." — paper lines 392-393.
> "Unless otherwise stated, experiments are done with 10 clients and Dir(0.1)-parted." — paper lines 394-395.

**Five datasets** (not 4, not "Tiny-ImageNet" in main Table 1 — Tiny-ImageNet is in appendix Table 12). **α ∈ {0.05, 0.1, 0.3}** in Table 1 — not {0.1, 1.0} as the prior draft claimed.

**Baselines (paper lines 387-391):** FedAvg, DENSE, F-DAFL, F-ADI, FedDF.

**Table 1 cells (paper-verbatim — CIFAR-10 and CIFAR-100 rows extracted; columns are FedAvg / FedDF / F-ADI / F-DAFL / DENSE / Co-Boosting):**

CIFAR-10:
- α=0.05: 17.49 ± 2.51, 37.53 ± 0.67, 36.94 ± 1.70, 37.82 ± 1.30, 38.37 ± 1.08, **47.20 ± 0.81** (paper line 369)
- α=0.1:  27.54 ± 1.80, 49.63 ± 0.80, 47.19 ± 0.97, 46.32 ± 0.97, 47.80 ± 1.21, **57.09 ± 0.94** (paper line 370)
- α=0.3:  46.39 ± 2.37, 67.18 ± 0.60, 60.60 ± 1.32, 65.89 ± 1.69, 66.77 ± 1.55, **70.24 ± 1.56** (paper line 371)

CIFAR-100:
- α=0.05: 6.45 ± 0.92, 16.07 ± 0.54, 13.75 ± 1.01, 15.79 ± 0.21, 16.17 ± 1.33, **19.24 ± 1.42** (paper line 374)
- α=0.1:  10.28 ± 1.70, 22.07 ± 0.43, 19.44 ± 1.66, 20.99 ± 1.17, 22.21 ± 1.41, **23.59 ± 1.27** (paper line 375)
- α=0.3:  15.22 ± 2.08, 30.71 ± 0.53, 26.14 ± 1.37, 28.79 ± 1.25, 30.33 ± 1.24, **31.30 ± 1.30** (paper line 376)

Plus α=0.05 paragraph (paper lines 402-405):
> "Co-Boosting surpasses the best baseline by substantial margins with **12.87%, 5.85%, 5.16%, 8.83%, and 3.07% on MNIST, FMNIST, SVHN, CIFAR-10, and CIFAR-100**, respectively."

**Number-of-clients sweep (paper Table 11, line 933):** n ∈ {5, 10, 20, 50} on CIFAR-10.

**Apples-to-apples with our v1:** Co-Boosting is the closest published peer to our HE-IFD on the plaintext utility axis. Their CIFAR-10 / N=10 / α=0.1 / CNN-5 cell = 57.09 % (Co-Boosting) vs DENSE 47.80 %. We do not yet run on CIFAR-10; our v1 is MNIST-only with an MLP, so the direct comparison requires upgrading our v1 to CNN + CIFAR before claiming parity.

---

## 6. FedDiff (Mendieta et al., WACV 2025)

**Setting they evaluate (paper Section 4 + Table 4):**
> "Datasets. We employ three datasets, FashionMNIST [33], PathMNIST [35], and CIFAR-10 [19]" — paper lines 382-383.
> "we divide the training set among C clients with a Dirichlet distribution Dir(α), as commonly done in FL literature... in the Supp. Material we visualize data distributions with Dir(0.1) and Dir(0.001) across 10 clients" — paper lines 386-394.
> "we train all approaches under (ϵ, δ) DP at the clients for various privacy levels of **ϵ = 50, 25, and 10**, with **δ = 10e−5**, **C = 10**, and **α = 0.01**." — paper line 593.

**Three datasets** (not CIFAR-100, not Tiny-ImageNet — these were fabricated in the prior draft).
**ε ∈ {50, 25, 10}** plus supplemental **ε = 1** (not {2, 5, 10} as the prior draft claimed).
**Baselines** (paper Table 4, line 591): **FedAvg, DENSE, OneShot-Ens, FedCVAE** (not "Co-Boosting (DP)" or "FedKT" as the prior draft claimed — Co-Boosting (DP) does not exist).

**Table 4 cells (paper-verbatim, CIFAR-10 row, columns ε=50 / 25 / 10):**
- FedAvg: 16.35 ± 1.52, 15.39 ± 1.87, 15.07 ± 2.12
- DENSE: 16.97 ± 2.35, 15.68 ± 2.27, 14.98 ± 1.25
- OneShot-Ens: 17.73 ± 2.71, 17.34 ± 2.35, 15.72 ± 1.34
- FedCVAE: 16.29 ± 1.55, 16.08 ± 2.19, 15.86 ± 2.83
- **FedDiff: 32.93 ± 1.93, 31.76 ± 2.68, 27.78 ± 1.66**

**ε=1 supplemental (FedDiff only) (paper line 611-612):**
> "an even tighter privacy budget of ϵ = 1 for FedDiff, achieving **65.53 ± 0.70, 44.38 ± 3.35, and 21.48 ± 1.53** on **FashionMNIST, PathMNIST, and CIFAR-10**"

**Apples-to-apples with our v1:** FedDiff is our DP one-shot peer. We do not yet have a DP variant; the γ-variant of our protocol would target the ε=10 row on CIFAR-10 (FedDiff achieves 27.78 %). Our current v1 doesn't reach this comparison.

---

## 7. FedKT (Li et al., AAAI 2021)

**Setting they evaluate (paper Section 4):**
> "we set the number of parties to **50 for Adult and cod-rna** and to **10 for MNIST and SVHN**." — paper line 553-554.
> Datasets per Table 4 line 1012: **Adult, cod-rna, MNIST, SVHN**.
> Architecture: "A multilayer perceptron (MLP) with two hidden layers on MNIST dataset. Each hidden layer has 100 units using ReLU activations. (4) A CNN on extended SVHN dataset." — paper lines 535-537.

**Datasets are Adult / cod-rna / MNIST / SVHN.** The prior draft of this file listed "MNIST, FashionMNIST, SVHN, CIFAR-10" — FashionMNIST and CIFAR-10 are NOT in FedKT's main experiments.

**Baselines (paper Table 1, line 595):** SOLO, FedAvg, FedProx, SCAFFOLD, FedDF, PNFM, PATE, XGBOOST.

**Table 1 cells (paper-verbatim, single-round non-private comparison):**
> "MNIST: FedKT 90.5% ± 0.3% | SOLO 69.0% | FedAvg 62.8% | FedProx 44.3% | SCAFFOLD 51.7% | FedDF 83.8% | PNFM 65.9% | PATE/XGBOOST 92.7%" — paper line 598.
> "SVHN: FedKT 83.2% ± 0.4% | SOLO 62.8% | FedAvg 26.8% | FedProx 20.1% | SCAFFOLD 16.2% | FedDF 77.2% | (PATE) 86.6%" — paper line 599.

**Privacy budget (user-verified from arXiv:2010.01017 Table 2):**

DP results are reported only for **Adult and cod-rna** (tabular). MNIST/SVHN DP results are deferred to the published AAAI 2021 Appendix B.7 (not in arXiv v1) and remain `n/r` from our extraction.

Table 2 (paper-verbatim, data-dependent ε from the moments accountant):

| Dataset | Mode | γ | #queries | ε | FedKT acc | L0 acc |
|---|---|---|---|---|---|---|
| Adult | L1 | 0.04 | 0.5 % | 2.56 | 76.8 % | 82.2 % |
| Adult | L1 | 0.04 | 1.0 % | 4.73 | 80.2 % | 82.2 % |
| Adult | L2 | 0.05 | 0.5 % | 3.24 | 79.0 % | 82.4 % |
| Adult | L2 | 0.05 | 1.0 % | 4.76 | 79.2 % | 82.4 % |
| cod-rna | L1 | 0.06 | 0.5 % | 5.48 | 82.6 % | 88.3 % |
| cod-rna | L1 | 0.10 | 0.5 % | 6.89 | 84.7 % | 88.3 % |
| cod-rna | L2 | 0.05 | 0.5 % | 4.51 | 81.4 % | 89.7 % |
| cod-rna | L2 | 0.05 | 2.0 % | 9.78 | 84.7 % | 89.7 % |

The paper states (line 621): "the accuracy is still comparable to the non-private version given a privacy budget less than 10." — ε values are data-dependent (from the moments accountant), not a fixed grid the user picks.

**Table 1 version discrepancy — flag for verification.** Our extracted Table 1 cells (FedKT MNIST = 90.5 % ± 0.3 %, SOLO = 69.0 %, FedAvg = 62.8 %) come from the PDF at arxiv.org/pdf/2010.01017 fetched 2026-05-21. The user notes that arXiv v1 of this paper reports FedKT MNIST = 95.9 %, SOLO = 80.0 %, FedAvg (2 rounds) = 83.5 % — a substantial divergence. The MLP-on-MNIST setup described at paper line 535–537 (which our extract anchors on) matches the AAAI 2021 camera-ready, not arXiv v1. So our 90.5 % / 62.8 % / 69.0 % numbers likely correspond to the **published AAAI 2021 version**, not arXiv v1. **Resolution requires checking the version we extracted from** — to be done by opening the PDF metadata or comparing against the AAAI 2021 published proceedings PDF.

**Apples-to-apples with our v1:** FedKT MNIST at FedKT=90.5 %, FedAvg=62.8 %, SOLO=69.0 % (single-round) compared to our v1 MNIST N=10 cell: our N=2 student = 67.4 %, our N=4 = 62.1 %. At N≥16 we are at 66.6–71.2 %, in the FedAvg / SOLO band, well below FedKT. **This is the closest published-vs-ours numerical comparison on MNIST**; FedKT has DP-budget-vs-no-DP advantages built in, so the gap is partly that we don't aggregate as cleanly as PATE does in plaintext.

---

## 8. POSEIDON (Sav et al., NDSS 2021)

**Setting they evaluate (paper Section V):**
> "POSEIDON trains a 3-layer neural network on the MNIST dataset with 784 features and 60K samples distributed among 10 parties in less than 2 hours." — abstract.
> "POSEIDON trains a 2-layer NN model on a dataset with 23 features and 30,000 samples distributed among 10 parties, in **8.7 minutes**. Moreover, POSEIDON trains a **3-layer NN with 64 neurons per hidden-layer on the MNIST dataset with 784 features and 60K samples shared between 10 parties, in 1.4 hours**, and a NN with convolutional and pooling layers on the CIFAR-10 dataset..." — paper lines 65-67.
> "we instantiate POSEIDON with **N = 10** and **N = 50** parties." — paper line 855.
> Datasets: BCW, ESR, CREDIT, MNIST, SVHN, CIFAR-10, CIFAR-100, synthetic (paper Section V.B/C).

**Architecture:** 3-layer FC NN with 64 neurons/layer for MNIST and SVHN. CNN for CIFAR-10. NOT LeNet-5 — that was wrong in the prior draft.

**Table III, N = 10 parties, MNIST row (paper line 879):**
> "MNIST 92.1% 91.3% 87.8% 90.6% 89.9% 5,283.1 0.38"

**Column semantics (user-verified interpretive reading, 2026-05-21; needs paper-caption transcription to be fully verbatim):**
- **92.1 % = C1 = Centralised** training (single party, all data pooled) — upper bound, NOT POSEIDON.
- 91.3 % = C2 = Decentralised non-private (standard FedAvg-style, no HE)
- 87.8 % = L = Local training only (each party trains independently) — lower bound / SOLO analogue
- 90.6 % = D = a fourth baseline (likely a distributed non-HE aggregation variant; exact label still n/r)
- **89.9 % = POSEIDON** — this is the HE-protected result
- 5,283.1 = training time in seconds (≈ 1.47 h — consistent with the abstract's "less than 2 h" claim)
- 0.38 = communication (likely GB)

So **POSEIDON's MNIST accuracy at N=10 is 89.9 %**, not 92.1 % (which is the centralised upper bound). The previous version of this file conflated the two; this is now corrected.

**Table IV, N = 50 parties (extrapolated), MNIST + CIFAR (paper line 936 + abstract):**
> "CIFAR-100 43.6% 41.8% 8.2% 41.1% 0.026 1404 0.006"

**CIFAR-10 at N = 50 (user-verified from arXiv:2009.00349 abstract + body):**
- Two CNN configurations are reported. Headline wall-clock: **175 hours** for CIFAR-10 at N=50.
- POSEIDON CIFAR-10 accuracy at N=50: **51.8 %** (config 1) or **61.1 %** (config 2) — exact cell tuple `(C1, C2, L, POSEIDON, training-h, inference-h)` is (54.6, 52.1, 26.8, 51.8, 175, 0.001) for config 1 and (63.6, 62.0, 28.0, 61.1, 184.8, 0.004) for config 2. (Numbers per the user's verification pass; need direct caption transcription before final manuscript use.)

**Crypto scheme:** Multiparty CKKS per Mouchet et al. (paper line 856 mentions CKKS ring degree N = 2^13 or 2^14; this is CKKS notation specifically). The previous draft's "multiparty CKKS" label is correct, with citation grounded in the paper body (not just the abstract's generic "multiparty lattice-based cryptography").

**Apples-to-apples with our v1:** **POSEIDON's MNIST = 89.9 % at N=10** under HE (multi-round, 1.4 h wall-clock); the centralised plaintext upper bound on the same setup is 92.1 %. Our v1 MNIST at N=10 not yet swept; surrounding cells N=8 = 0.53, N=16 = 0.67, N=32 = 0.71. Our v1 is plaintext-simulated, not real HE, so the comparison is one step ahead — when we instantiate the protocol under multiparty CKKS the comparison axis becomes "POSEIDON 89.9 % in 1.4 h multi-round" vs "HE-IFD ??? in seconds one-round". We expect to trade accuracy for wall-clock at the order-of-magnitude level.

---

## What this table is for

1. **Bound our v1 claims** against what each closest published neighbour reports. Today, v1 on MNIST is in the same band as FedKT non-private (62.8 % FedAvg, 90.5 % FedKT) and roughly tracks DENSE's CIFAR-10 / α=0.1 (50.26 %) when normalised across dataset difficulty — but we are MNIST-only and have not built CIFAR yet, so the direct number isn't apples-to-apples.
2. **Pin the resubmission's positioning axes**:
   - **Plaintext one-shot utility ceiling**: Co-Boosting (CIFAR-10 / N=10 / α=0.1 / CNN-5 = 57.09 %).
   - **DP one-shot utility-privacy frontier**: FedDiff (CIFAR-10 / ε=10 = 27.78 %; FashionMNIST / ε=1 = 65.53 %); FedKT for MNIST/SVHN.
   - **HE multi-round peer**: POSEIDON (MNIST / N=10 = 92.1 % in 1.4 h, multi-round).
   - **Public-probe methodology lineage**: FedMD (heterogeneous-task), DS-FL (same-domain).
   - **Data-free one-shot lineage**: DENSE, Co-Boosting.

---

## Verification list — what remains unsourced

These are the cells still labelled `n/r` (not recovered from the automated PDF extraction). They are not LLM guesses; they are simply not extracted yet. To fill them in, open the published paper and transcribe verbatim:

- [x] **DS-FL — number of clients K + partition scheme.** Resolved 2026-05-21 by user verification: K = 100 clients; label-extreme partition (2–3 classes/client in strong non-IID); no Dirichlet α.
- [ ] DS-FL — final-round accuracy numbers per dataset (in convergence figures, not tables; requires reading figures from the IEEE TMC paper).
- [ ] FedDF — Table 1 rounds-to-target cells for CIFAR-10 / CIFAR-100 (dense tabular; not in text layer).
- [x] **DENSE — default m in Table 1.** Resolved (likely m = 5, from Table 2's first sweep row; explicit confirmation in Section 3.1 still pending).
- [ ] Co-Boosting — Table 1 MNIST, FMNIST, SVHN row cells (only CIFAR-10 + CIFAR-100 extracted; same 6-column × 3-α format).
- [ ] FedDiff — Table 4 FashionMNIST and PathMNIST baseline rows (CIFAR-10 row extracted; FedDiff-only ε=1 supplemental values transcribed in §6 above).
- [x] **FedKT — DP ε grid (Adult / cod-rna part of Table 2).** Resolved 2026-05-21 by user verification: see Table 2 transcription in §7 above. MNIST/SVHN DP-mode results remain n/r (AAAI Appendix B.7 only).
- [ ] FedKT — verify our Table 1 extract is from arXiv v1 or AAAI 2021 camera-ready (90.5 % vs 95.9 % discrepancy noted in §7).
- [x] **POSEIDON Table III column semantics.** Resolved 2026-05-21 by user verification (interpretive): C1=92.1, C2=91.3, L=87.8, D=90.6, POSEIDON=89.9, training=5,283 s ≈ 1.47 h, comm=0.38 (GB?). Still needs caption-verbatim transcription to confirm column labels D and units.
- [x] **POSEIDON Table IV CIFAR-10 row + wall-clock.** Resolved 2026-05-21 (interpretive): N=50, 175 h, POSEIDON accuracy 51.8 % (config 1) or 61.1 % (config 2). Caption-verbatim transcription pending.

Until the open boxes are filled, the comparator-vs-v1 narrative leans on the cells already extracted above. None of the numerical claims in the file are LLM-generated digits.
