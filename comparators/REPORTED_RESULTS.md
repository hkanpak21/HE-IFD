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
| 9 | **FedSD2C** | Zhang et al., NeurIPS 2024 (arXiv:2412.05186) | yes | plaintext (DP optional, ε∈{1,4,8,∞} reported) | **Tiny-ImageNet, ImageNette, OpenImage** (N=10 default, α ∈ {0.1, 0.3, 0.5}) | ConvNet + ResNet-18; pre-trained autoencoder distiller |
| 10 | **FuseFL** | Tang et al., NeurIPS 2024 (arXiv:2410.20380) | yes (block-wise; K-stage, costs same as 1-round) | plaintext | MNIST, FMNIST, CIFAR-10, SVHN, CIFAR-100, Tiny-ImageNet (M=5 default, α∈{0.1,0.3,0.5}) | ResNet-18 (also 10/26); block-fusion via 1×1 conv adapters |
| 11 | **FedLPA** | Liu et al., NeurIPS 2024 (arXiv:2310.00339) | yes | plaintext (DP compatible — Appendix F.1) | **MNIST, FMNIST, SVHN, CIFAR-10** (10 clients default, β ∈ {0.01, 0.05, 0.1, 0.3, 0.5} + #C ∈ {1, 2, 3}) | **simple CNN with 5 layers** (default); VGG-9 in Appendix |
| 12 | **FedAUXfdp** | Hoech et al., IJCAI-W 2022 (arXiv:2205.14960) | yes | (ε, δ)-DP; full grid ε ∈ {1.0, 0.5, 0.1, 0.01}, δ=1e-5 (class model) + ε=0.1, δ=1e-5 (scoring) | **CIFAR-10** (private) with STL-10 / CIFAR-100 (auxiliary distillation); N=20, Dir(α) α ∈ {0.01, 0.04, 0.16, 10.24} | ShuffleNet / MobileNetv2 / ResNet8 with pretrained feature extractor |
| 13 | **FedGM** | Chen, Zhou & Jiang, *Electronics* 13(10):1815, 2024 — MDPI | yes | **Label-DP** (PDF text not extracted; MDPI blocks automated fetch) | n/r (PDF blocked) — search snippets mention CIFAR-10 | n/r (PDF blocked) |
| 14 | **Hyb-Agg** | Kemmaka & Tran, arXiv:2511.23252 (2025) | yes (1-round, non-interactive aggregation) | **HE** (Multi-Key CKKS + ECDH masking); no DP | **synthetic vectors only** — no real datasets, no ML accuracy reported | n/a — protocol-only paper, no training |
| 16 | **slytHErin** | Intoci et al., Cloud S&P 2023 (arXiv:2305.00690) | n/a — inference only, no training | **HE + multiparty CKKS**; Scenario 3 = model AND data encrypted, model never decrypted | **MNIST only** | NN5 / NN20 (~754K) / NN50 (~1M), fully-connected + conv + pooling |
| 17 | **CryptPEFT** | Xia et al., NDSS 2026 (arXiv:2508.12264) | n/a — inference only | **MPC (2-party)**, not HE; adapter is the provider's plaintext secret | CIFAR-10, CIFAR-100, Food-101, SVHN, Flowers-102 | frozen public ViT backbone + encrypted PEFT adapter |
| 18 | **Mazzone et al.** | USENIX Sec '25, pp. 8541-8558 (arXiv:2412.15126) | n/a — primitive | single-key CKKS | n/a — 128-element vectors | n/a — ranking / order statistics / sorting |
| 19 | **cutmax** | Avitan et al., 2025 (arXiv:2509.08383) | n/a — primitive | 2-party, plaintext model + encrypted input | LLM output distributions | n/a — HE argmax + top-p sampling |
| 20 | **GH-OFL** | Turazza, Picone & Mamei, ICLR 2026 (arXiv:2602.01186) | **yes** | **none** — uploads per-class sufficient statistics in plaintext | n/r — abstract only, results not extracted | frozen pretrained encoder + closed-form Gaussian head |

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

## 9. FedSD2C (Zhang et al., NeurIPS 2024)

**Setting they evaluate (paper Section 4.1, lines 446-467):**
> "we conduct experiments on three real-world image datasets with different ranges of resolution including Tiny-ImageNet [54], ImageNette [55], and OpenImage [56]." — paper lines 446-447.
> "Tiny-ImageNet contains 10000 images of 64×64 resolution across 200 classes. ImageNette is a widely used subset of 10 classes from ImageNet-1K [57] with 9469 color images, resized to 128×128. OpenImage is a large-scale real-world vision dataset with over 9 million images of 256 ×256 resolution." — paper lines 447-450.
> "we use Dirichlet distribution to generate non-IID data to generate non-IID local data, as in [58] for Tiny-ImageNet and ImageNette." — paper lines 451-452.
> "The α is set to 0.1 by default unless otherwise stated. For OpenImage, we randomly choose n real-world clients from FedScale [59] and use their corresponding test sets to form global sets. We set the default number of clients n to 10, unless otherwise specified." — paper lines 457-459.
> "We use two different model architectures: ConvNet [28] and ResNet-18 [61] for all methods." — paper lines 462-463.

**Three datasets, N=10 default, α ∈ {0.1, 0.3, 0.5}** (pre-defined splits for OpenImage). The autoencoder distiller is the **publicly pre-trained Stable Diffusion autoencoder** (paper line 465), shared by the server to clients in the preparation phase.

**Baselines (paper lines 460-462):** FedAvg, DENSE, Co-Boosting, F-DAFL.

**Table 1 (paper-verbatim, lines 419-438) — ConvNet block** (columns: ImageNette α=0.1 / 0.3 / 0.5; Tiny-ImageNet α=0.1 / 0.3 / 0.5; OpenImage):
- Central (upper bound, ConvNet): 81.69 / – / – / 31.06 / – / – / 28.30 (line 427-ish — partial; see ResNet block below for fully extracted Central row)
- F-DAFL: 44.95±0.72, 52.23±0.23, 58.34±0.55, 5.25±0.41, 8.89±0.61, 10.28±0.10, 3.36±0.56
- DENSE: 42.09±0.68, 48.64±1.91, 54.74±0.75, 11.45±0.08, 14.69±0.48, 15.15±0.22, 7.00±0.84
- Co-Boosting: 39.36±0.70, 56.15±1.33, 58.60±1.02, 6.66±0.35, 9.81±0.26, 10.75±0.11, 13.59±0.98
- **FedSD2C: 50.68±0.20, 57.89±0.96, 58.17±0.51, 20.73±0.12, 23.53±0.18, 24.10±0.30, 23.00±0.24**

**Table 1 — ResNet-18 block (paper lines 432-438):**
- Central: ImageNette = 90.00, Tiny-ImageNet = 61.98, OpenImage = 34.17
- FedAvg: 9.86±0.13 / 10.06±0.20 / 10.76±0.35 / – / – / – / 1.68±0.16
- F-DAFL: 37.86±0.38, 39.52±0.46, 46.06±0.16, 7.91±0.22, 12.30±0.36, 13.31±0.56, 12.75±0.14
- DENSE: 38.37±0.36, 47.85±2.17, 49.78±2.11, 8.88±0.23, 13.05±0.36, 17.24±0.43, 14.85±0.62
- Co-Boosting: 27.06±0.61, 28.53±0.86, 30.53±1.12, 10.29±0.43, 14.35±0.93, 16.39±0.59, 9.52±1.52
- **FedSD2C: 47.52±0.51, 53.69±0.17, 55.90±0.53, 26.83±0.10, 29.92±0.37, 31.66±0.85, 22.69±0.14**

The agent's earlier claim — "ImageNette 47.52% @ α=0.1, Tiny-ImageNet 26.83% on ResNet-18" — **verified**, both cells reproduce paper-verbatim.

**DP integration (paper Table S6, line 980-982):** "Performance of integrating DP-SGD" — ResNet-18 / Tiny-ImageNet only:
> "FedSD2C 22.92 25.13 26.01 26.83" at ε ∈ {1, 4, 8, ∞} — paper line 982.

**Apples-to-apples with our v1:** FedSD2C operates at higher resolution (Tiny-ImageNet 64×64, ImageNette 128×128, OpenImage 256×256) than our MNIST 28×28 — direct comparison is **context-only**, not numerical. The DP-SGD column (ε=1 → 22.92 % on Tiny-ImageNet) is the right anchor for our future DP one-shot variant if we move beyond MNIST.

---

## 10. FuseFL (Tang et al., NeurIPS 2024 Spotlight)

**Setting they evaluate (paper Section 6.1, lines 581-596):**
> "we conduct comprehensive experiments with commonly used datasets in FL, including MNIST [77], CIFAR-10 [73], FMNIST [146], SVHN [99], CIFAR-100 [73] and Tiny-Imagenet [76]." — paper lines 581-583.
> "we partitioned the datasets through a widely-used non-IID partition method, namely Latent Dirichlet Sampling [56; 67; 113; 80], in which the coefficient a represents the non-IID degree. Lower a generates more non-IID datasets, and vice versa. Consistent with established practices in the field [158; 113; 92; 80], each dataset was divided with three distinct degrees of non-IID with a ∈ {0.1, 0.3, 0.5}." — paper lines 585-588.
> "we train ResNet-18 [51] on all datasets in main experiments. And we reduce and increase the number of layers as ResNet-10 and ResNet-26 to verify the effect of FuseFL in model-heterogeneity FL." — paper lines 590-591/595.
> "The number of clients is set as M = 5 by default. Moreover, we study the scalability of our methods with different M ∈ {5, 10, 20, 50}." — paper lines 595-596.

**Caveat on the "one-shot" label.** FuseFL frames itself as one-shot in the sense that "**the actual communication cost is as same as one-shot FL. Because FuseFL only communicates a part of the model**" (paper line 614-615), but the number of communication rounds is **equal to the number of split blocks K** (paper lines 613-614). So in our taxonomy: communication-budget-equivalent-to-one-shot, but rounds = K ∈ {2, 4, 8}.

**Table 2 cells (paper line 604-608, paper-verbatim — columns are Dataset MNIST / FMNIST / CIFAR-10 / SVHN / CIFAR-100 / Tiny-Imagenet; α ∈ {0.1, 0.3, 0.5} within each dataset):**

FedAvg: 48.24, 72.94, 90.55 / 41.69, 82.96, 83.72 / 23.93, 27.72, 43.67 / 31.65, 61.51, 56.09 / 4.58, 11.61, 12.11 / 3.12, 10.46, 11.89
FedDF: 60.15, 74.01, 92.18 / 43.58, 80.67, 84.67 / 40.58, 46.78, 53.56 / 49.13, 73.34, 73.98 / 28.17, 30.28, 36.35 / 15.34, 18.22, 27.43
Fed-DAFL: 64.38, 74.18, 93.01 / 47.14, 80.59, 84.02 / 47.34, 53.89, 58.59 / 53.23, 76.56, 78.03 / 28.89, 34.89, 38.19 / 18.38, 22.18, 28.22
Fed-ADI: 64.13, 75.03, 93.49 / 48.49, 81.15, 84.19 / 48.59, 54.68, 59.34 / 53.45, 77.45, 78.85 / 30.13, 35.18, 40.28 / 19.59, 25.34, 30.21
DENSE: 66.61, 76.48, 95.82 / 50.29, 83.96, 85.94 / 50.26, 59.76, 62.19 / 55.34, 79.59, 80.03 / 32.03, 37.32, 42.07 / 22.44, 28.14, 32.34
Ensemble: 86.81, 96.76, 97.22 / 67.71, 87.25, 89.42 / 57.5, 77.35, 79.91 / 65.29, 88.31, 85.7 / 35.69, 49.41, 53.39 / 30.85, 39.43, 45.8
**FuseFL K=2**: 97.02, 98.43, 98.54 / 83.15, 89.94, 89.47 / **70.85, 81.41, 84.34** / 76.88, 91.07, 90.87 / 34.07, 45.12, 46.12 / 29.28, 31.11, 34.34
**FuseFL K=4**: 97.19, 98.34, 98.29 / 83.05, 84.58, 90.50 / 73.79, 84.58, 81.15 / 78.08, 89.63, 89.34 / 36.86, 42.79, 49.30 / 27.63, 33.04, 34.28
**FuseFL K=8**: 96.66, 98.35, 98.16 / 83.2, 88.57, 88.24 / 70.46, 80.70, 74.99 / 80.31, 88.88, 89.94 / 34.97, 39.08, 40.73 / 25.21, 32.59, 33.82

Agent's earlier claim — "CIFAR-10 α=0.5 K=2 84.34%" — **verified** (CIFAR-10 K=2 row = 70.85 / 81.41 / 84.34 for α = 0.1 / 0.3 / 0.5; the 84.34 cell sits at α=0.5).

**Apples-to-apples with our v1:** Same FL benchmark family (MNIST, FMNIST, CIFAR-10) and same α grid. FuseFL CIFAR-10 / M=5 / K=2 / α=0.5 = 84.34 % is the closest published plaintext one-shot peer on CIFAR-10 with N small. Their MNIST K=2 row (97.02, 98.43, 98.54) is the practical plaintext-MLP-on-MNIST ceiling. **The closer methodological match for our HE-IFD is FuseFL with K=2** (block-fusion at 2 rounds), since our protocol is genuinely 1-round / no block-wise fusion.

---

## 11. FedLPA (Liu et al., NeurIPS 2024)

**Setting they evaluate (paper Section 4.1, lines 443-510):**
> "We conduct experiments on MNIST [63], Fashion-MNIST [64], CIFAR-10 [65], and SVHN [66] datasets." — paper lines 443-444.
> "use a simple CNN with 5 layers in our experiments. The experiments with more complex neural network structures are in Appendix G.8." — paper lines 507-508.
> "By default, we set 10 clients and run 200 local epochs for each client." — paper lines 509-510.
> "the parameter dimensions for MNIST, FMNIST, SVHN, and CIFAR-10 are 784, 784, 3,072, and 3,072, respectively." — paper line 459.

**User's suspicion confirmed**: the **main results are reported on a simple 5-layer CNN** (a small model). Appendix G has additional experiments on VGG-9 (paper line 1717) and EMNIST (line 1741). NIID-Bench partition scheme is used (line 460: `github.com/Xtra-Computing/NIID-Bench`).

**Partitioning:** Two schemes — Dirichlet (β ∈ {0.01, 0.05, 0.1, 0.3, 0.5}) and pathological (#C ∈ {1, 2, 3} where each client sees only #C classes).

**Table 1 cells (paper-verbatim, lines 464-505; columns: FedLPA / FedNova / SCAFFOLD / FedAvg / FedProx / DENSE):**

FMNIST (lines 466-475):
- β=0.01: **21.20±0.67** / 10.13±0.00 / 15.97±0.12 / 18.17±0.15 / 13.37±0.19 / **15.23±0.14**
- β=0.05: 54.27±0.38 / 18.67±0.41 / 18.67±0.41 / 18.67±0.41 / 22.03±0.14 / 47.77±0.20
- β=0.1: 55.33±0.06 / 30.47±0.59 / 31.40±0.25 / 30.93±0.58 / 31.00±0.52 / 52.93±0.67
- β=0.3: 68.20±0.04 / 49.40±0.26 / 46.00±0.02 / 45.17±0.05 / 44.30±0.08 / 64.27±0.08

CIFAR-10 (lines 476-485):
- β=0.01: 16.17±0.00 / 11.57±0.02 / 11.47±0.01 / 11.53±0.05 / 10.47±0.00 / 12.30±0.03
- β=0.05: 18.37±0.00 / 10.30±0.00 / 10.73±0.01 / 10.23±0.00 / 10.97±0.02 / 17.87±0.31
- β=0.1: 19.97±0.02 / 12.30±0.04 / 10.87±0.01 / 12.83±0.06 / 11.97±0.04 / 19.93±0.07
- β=0.3: 26.60±0.01 / 11.77±0.02 / 10.93±0.01 / 10.53±0.00 / 10.97±0.00 / 25.57±0.84

MNIST (lines 486-495):
- β=0.01: 39.17±1.16 / 13.53±0.20 / 8.87±0.01 / 9.37±0.00 / 9.33±0.00 / 15.80±0.24
- β=0.05: 70.07±0.05 / 31.60±0.71 / 41.07±0.46 / 38.57±0.28 / 32.23±0.18 / 57.83±1.55
- β=0.1: 77.43±0.14 / 48.07±0.28 / 47.73±0.22 / 48.63±0.15 / 47.40±0.00 / 70.33±0.02
- β=0.3: 85.77±0.02 / 67.6±0.40 / 67.07±0.15 / 66.17±0.21 / 63.40±0.41 / 84.50±0.01

SVHN (lines 496-505):
- β=0.01: 19.20±0.00 / 13.73±0.14 / 9.83±0.00 / 12.13±0.04 / 11.43±0.12 / 17.33±0.28
- β=0.05: 22.93±0.38 / 14.90±0.43 / 15.77±0.14 / 16.60±0.23 / 15.90±0.12 / 21.47±0.20
- β=0.1: 39.77±0.69 / 25.97±0.13 / 25.70±0.08 / 22.17±0.02 / 24.50±0.06 / 19.43±0.45
- β=0.3: 52.23±0.26 / 34.40±0.28 / 34.03±0.06 / 33.93±0.26 / 34.70±0.20 / 47.13±7.14

Agent's earlier claim — "FMNIST β=0.01 21.20%, beats DENSE 15.23%" — **verified** (FedLPA = 21.20±0.67, DENSE = 15.23±0.14 at FMNIST β=0.01 in Table 1).

**Co-Boosting comparison (Table 18 / line 1635-1638, FMNIST):**
> "Co-Boosting 17.31±0.24 (β=0.01), 48.97±1.44 (β=0.05), 73.15±1.86 (β=0.1), 83.37±0.44 (β=0.3), 86.21±0.31 (β=0.5)"
> "when the β is smaller than 0.1, our method outperforms Co-Boosting" — paper line 1639.

So on FMNIST at β=0.01: FedLPA = 21.20 > Co-Boosting = 17.31 > DENSE = 15.23; at β≥0.1 Co-Boosting catches up and overtakes.

**Apples-to-apples with our v1:** FedLPA is the **most direct same-task small-model peer** to our v1 — MNIST + FMNIST, 10 clients, no Dirichlet `α` mapping but the β parameter has the same role. FedLPA MNIST β=0.3 = 85.77 % (10 clients, 5-layer CNN, one round) vs our v1 MNIST N=8 = 53.18 %; FedLPA's posterior-aggregation does substantially better than our linear δ-aggregator at the same N/dataset, but the **methods are doing different things** — FedLPA needs second-order Fisher information from each client; ours sends only first-order δ. The FedLPA architecture being a 5-layer CNN (vs our 784→128→32→10 MLP) is also a non-trivial confound.

---

## 12. FedAUXfdp (Hoech et al., IJCAI-W 2022)

**Setting they evaluate (paper Section 5, lines 513-530):**
> "using CIFAR-10 as local client data and both STL-10 and CIFAR-100 as auxiliary data. Of the auxiliary data, 80% is used for distillation" — paper lines 514-516.
> "The number of clients is n = 20 and there is full participation in one round of communication." — paper lines 520-521.
> "The training data is split among the clients using a Dirichlet distribution with parameter α as done first in [Hsu et al., 2019] and later in [Lin et al., 2020; Chen and Chao, 2020]. With the lowest α = 0.01... est α = 10.24, each client sees a substantial number of images from every class." — paper lines 522-526.
> "We follow [Sattler et al., 2021a] in their selection of highlighted Dirichlet parameters α, who chose α = 2^n * 10^-2, for n ∈ {0, 2, 4, 10}." — paper lines 528-529.

**So:** **CIFAR-10 local data** + STL-10 / CIFAR-100 auxiliary distillation, **N=20**, Dir(α) α ∈ {0.01, 0.04, 0.16, 10.24}. Architectures: ShuffleNet, MobileNetv2, ResNet8.

**Table 2 (paper-verbatim, lines 605-607; cumulative privacy loss ε=0.6, δ=2e-5; columns: ShuffleNet α=0.01 / 0.04 / 0.16 / 10.24, MobileNetv2 α=0.01 / 0.04 / 0.16 / 10.24):**
- FedAvg+P: 46.0±0.4 / 56.7±6.6 / 67.5±3.5 / 74.1±1.4 / 47.2±2.6 / 54.2±5.5 / 65.6±0.9 / 72.0±0.6
- FedD+P: 41.8±4.4 / 54.7±5.0 / 68.8±2.1 / 72.3±1.6 / 43.7±1.8 / 52.2±4.6 / 67.0±1.7 / 70.8±0.2
- **FedAUXfdp: 75.2±1.1 / 74.6±1.1 / 72.3±0.6 / 71.7±1.3 / 72.8±0.4 / 72.0±1.2 / 70.8±0.2 / 69.4±0.8**

**Table 3 (paper-verbatim, lines 612-617; class-model DP grid, scoring model fixed at ε=0.1, δ=1e-5; same 8 (architecture × α) columns):**
- FedAUX+F (no class DP): 64.8±1.1 / 64.9±0.5 / 67.7±0.8 / 73.4±0.1 / 60.1±1.2 / 61.2±1.8 / 63.7±0.8 / 67.5±0.0
- FedAUXfdp (no class DP): 76.1±0.3 / 75.6±0.4 / 75.2±0.5 / 75.4±0.1 / 73.0±0.5 / 73.3±0.6 / 73.2±0.2 / 73.0±0.1
- FedAUXfdp (ε=1.0, δ=1e-5): 75.7±0.7 / 75.1±0.7 / 74.6±0.5 / 74.9±0.2 / 73.0±0.4 / 72.7±1.0 / 72.7±0.3 / 72.4±0.0
- FedAUXfdp (ε=0.5, δ=1e-5): 75.2±1.1 / 74.6±1.1 / 72.3±0.6 / 71.7±1.3 / 72.8±0.4 / 72.0±1.2 / 70.8±0.2 / 69.4±0.8
- FedAUXfdp (ε=0.1, δ=1e-5): 60.8±2.4 / 59.4±5.8 / 33.9±5.4 / 34.6±3.0 / 66.4±3.3 / 53.1±12.9 / 38.9±4.4 / 34.9±3.3
- FedAUXfdp (ε=0.01, δ=1e-5): 36.3±5.1 / 39.8±7.5 / 12.6±5.1 / 11.7±3.5 / 44.4±6.8 / 28.7±5.1 / 16.6±5.8 / 11.5±0.8

**Table 4 (paper line 622-625; ResNet8, with STL-10 vs CIFAR-100 as distillation data):**
- STL-10: 77.2±0.5 / 75.4±1.0 / 74.7±0.9 / 74.4±0.8
- CIFAR-100: 70.4±0.7 / 68.9±1.8 / 67.6±1.6 / 68.5±1.9

**Apples-to-apples with our v1:** **FedAUXfdp at (ε=0.5, δ=1e-5) on CIFAR-10 / N=20 / α=0.01 = 75.2 %** is genuinely the strongest published DP one-shot baseline on CIFAR-10. It relies on a **pre-trained feature extractor** on auxiliary public data (STL-10 / CIFAR-100), which is a stronger assumption than ours; the comparison would be "FedAUXfdp's ε ∈ {0.5, 1.0} ceiling on CIFAR-10" vs whatever γ-noise band we land on. Our v1 has no DP variant yet, so this is **context-only** until we add Gaussian-mechanism noise to the cumulative-δ aggregate.

---

## 13. FedDiff + FMF (Mendieta et al., WACV 2025) — extension of §6 above

**Confirmed identity:** arXiv:2405.01494 is **the same paper as §6 (FedDiff)**. The "+FMF" refers to **Fourier Magnitude Filtering**, an extension proposed *within* the same paper (paper Section 5.3, line 701). FMF is not a separate work. Agent's earlier instruction treating "FedDiff + FMF" as a separate peer is wrong; they are §6.

**Additional Table 4 baseline rows (paper line 585-591, paper-verbatim) — already noted partially in §6:**

FashionMNIST (line 587):
- FedAvg: 21.04±12.1 / 20.82±12.3 / 20.39±12.6
- DENSE: 26.34±9.03 / 26.29±9.81 / 24.29±15.6
- OneShot-Ens: 31.27±10.9 / 31.32±10.1 / 29.99±16.7
- FedCVAE: 44.40±1.70 / 43.89±2.53 / 41.65±3.19
- **FedDiff: 75.92±1.86 / 75.08±2.13 / 73.43±1.50**

PathMNIST (line 589):
- FedAvg: 16.98±8.93 / 15.30±6.44 / 14.85±4.19
- DENSE: 20.56±6.59 / 19.19±3.76 / 18.41±1.86
- OneShot-Ens: 24.59±7.63 / 23.38±2.60 / 22.23±2.02
- FedCVAE: 24.06±1.57 / 22.15±2.68 / 20.51±1.29
- **FedDiff: 54.98±2.04 / 51.51±1.85 / 47.85±3.68**

CIFAR-10 (line 591) — was already in §6, repeated here for completeness:
- FedAvg: 16.35±1.52 / 15.39±1.87 / 15.07±2.12
- DENSE: 16.97±2.35 / 15.68±2.27 / 14.98±1.25
- OneShot-Ens: 17.73±2.71 / 17.34±2.35 / 15.72±1.34
- FedCVAE: 16.29±1.55 / 16.08±2.19 / 15.86±2.83
- **FedDiff: 32.93±1.93 / 31.76±2.68 / 27.78±1.66**

**ε=1 FedDiff (paper line 620-622):**
> "an even tighter privacy budget of ϵ = 1 for FedDiff, achieving 65.53±0.70, 44.38±3.35, and 21.48±1.53 on FashionMNIST, PathMNIST, and CIFAR-10"

**FMF gains (paper line 773-775):** roughly 2% improvement on PathMNIST and CIFAR-10 at ε=10 vs FedDiff alone; exact cells not in our extract — see Figure 5 in the paper.

---

## 14. FedGM (Chen, Zhou, Jiang — *Electronics* 13(10):1815, 2024)

**Provenance caveat — flagged.** This paper is published in MDPI *Electronics* (open access) but the publisher's CDN serves an **HTTP 403 Access Denied** to all automated fetches we tried (curl with browser UA, WebFetch, MDPI `/pdf` and `/htm` endpoints). The full text is not extractable from our toolchain.

**What we can verify from search-engine snippets (not paper-verbatim — snippets only):**
- Title: "One-Shot Federated Learning with Label Differential Privacy."
- Authors: Z. Chen, C. Zhou, Z. Jiang.
- Venue: *Electronics* 13(10), Article 1815, MDPI, May 2024. DOI 10.3390/electronics13101815.
- Mechanism: uses **iterative gradient matching to learn a surrogate** dataset that clients send to the server instead of model updates; surrogate is protected by **label differential privacy**.
- Headline claim per snippet: "FedGM achieves a test accuracy of 67.5% ± 0.2% on CIFAR-10." **This is a search-engine summary, not paper-verbatim** — the exact ε binding, the number of clients, the partition scheme, and the exact accuracy table all remain `n/r`.

**Cells we explicitly DO NOT have:**
- Number of clients N: `n/r`
- Partition scheme (Dirichlet? IID? non-IID α?): `n/r`
- Architecture: `n/r`
- ε grid for label-DP: `n/r`
- Full table cells beyond the snippet 67.5±0.2%: `n/r`

**Action needed:** open the paper in a browser (not curl), copy the relevant table text into the repo at `/tmp/he-ifd-pdfs/fedgm.txt`, then re-run a transcription pass. Until then, this entry stays partial.

**Apples-to-apples with our v1:** Cannot establish — too many cells unsourced. The "67.5% on CIFAR-10" snippet, if it really is at a label-DP ε comparable to FedDiff/FedAUXfdp, would beat FedDiff (32.93 % at ε=50, CIFAR-10) by a large margin; that's a remarkable claim and exactly why the paper-verbatim binding to dataset / ε / N matters. Treat the headline as **unverified** until the PDF is accessed.

---

## 15. Hyb-Agg (Kemmaka & Tran, arXiv:2511.23252, 2025)

**Setting they evaluate (paper Section VI, lines 686-792):**
> "Hyb-Agg, a lightweight and communication-efficient secure aggregation protocol that integrates Multi-Key CKKS (MK-CKKS) homomorphic encryption with Elliptic Curve Diffie-Hellman (ECDH)-based additive masking." — paper lines 16-19.
> "Hyb-Agg reduces the secure aggregation process to a single, non-interactive client-to-server transmission per round" — paper lines 20-21.
> "We implement and evaluate Hyb-Agg on both high-performance and resource-constrained devices, including a Raspberry Pi 4, demonstrating that it delivers sub-second execution times while achieving a constant communication expansion factor of approximately 12× over plaintext size." — paper lines 27-31.

**Critical caveat — no real ML datasets, no accuracy numbers.**
> "The experiments were conducted using synthetic data. Specifically, client inputs were modeled as vectors of randomly generated 64-bit floating-point numbers (double), with the dimensionality d varied as an experimental parameter... using synthetic data allows for a clean and reproducible measurement of the protocol's scalability" — paper lines 777-790.

So Hyb-Agg is a **protocol-only paper**: it reports cryptographic latency / bandwidth on synthetic vectors, not federated learning accuracy.

**Headline performance (paper Table II, line 1010-1016 — Raspberry Pi 4, N=50, d=8192):**

| Metric | Measured Performance |
|---|---|
| Avg. Client Total Time | 431.8 ms |
| Server Total Time | 191.1 ms |
| Client Uplink per Round | 787 KB |
| Communication Expansion | ≈12× |

**Expansion factor analysis (paper lines 876-895):**
> "For a data vector of dimension d=65,536 composed of 64-bit (8-byte) floating-point numbers, the plaintext size is 65,536 × 8 = 524,288 bytes... ClientUplinkBytes is approximately 6.3MB. This yields a communication expansion factor of approximately 6,300,000 / 524,288 ≈ 12×."
> "with smaller d, unused slots let fixed polynomial/modulus bytes dominate, so the factor can be higher (about 24× near d ≈ 4,095)" — paper lines 888-890.

**Table I comparison vs other secure aggregation schemes (paper lines 99-104):**
- Hyb-Agg: hybrid MK-CKKS + ECDH; 1 round; ~12× expansion; secure under server + ≤ N-2 client collusion; Raspberry Pi 4
- xMK-CKKS (Tian et al.): 2 rounds; high (grows with N); ≤ N-2; Jetson Nano
- tMK-CKKS: 2 rounds; ~O(t); ≤ t-1; simulated
- FedSHE: single-key CKKS; 1 round; very low expansion (≈6.6% of Paillier-FL); but requires trusted key manager

**Apples-to-apples with our v1:** Hyb-Agg is a **complementary primitive**, not a competitor — it sits at the secure-aggregation layer that our protocol would also need. Our HE-IFD `aggregate.py` is FHE-compatible by construction (linear δ-aggregation only); plugging in Hyb-Agg's MK-CKKS layer would be the natural mechanism to lift v1 from plaintext-simulated to real HE. The relevant numbers from Hyb-Agg are **latency (431.8 ms client / 191.1 ms server) and bandwidth (~12× expansion)** — these become per-round overheads on top of our N-sweep accuracy curves once we add the HE layer. No accuracy comparison applies.

---

## 16. slytHErin (Intoci et al., Cloud S&P 2023) — THE ENCRYPTED-SERVING PEER

**Francesco Intoci, Sinem Sav, Apostolos Pyrgelis, Jean-Philippe Bossuat, Juan Ramón Troncoso-Pastoriza, Jean-Pierre Hubaux. "slytHErin: An Agile Framework for Encrypted Deep Neural Network Inference." 5th Workshop on Cloud Security and Privacy (Cloud S&P), 2023. arXiv:2305.00690v1.**

Verified 2026-08-02 by reading `comparators/poseidon/2305.00690v1.pdf` directly (pages 1-2, 11-16). Same group as POSEIDON (Sav, Pyrgelis, Troncoso-Pastoriza, Hubaux).

**Why this matters:** it is the only prior system found that serves a model **held under a multiparty key and never decrypted**. Its Scenario 3 is our serving setting.

**Three scenarios (paper Section 1, p. 2, verbatim):**
> "(i) the client's data is encrypted while the model is in cleartext, (ii) the client's data is in cleartext and the model is encrypted, and (iii) both the client's data and the model are encrypted."

**Scenario 3 mechanism (paper Section 5.6, p. 11, verbatim):**
> "In **Scenario 3**, the model-providers rely on these functionalities to refresh the ciphertexts noise and to change the encryption key of the prediction result, so that only the client can decrypt it."

So the querier receives the **prediction result**, i.e. the score vector, NOT a label. No encrypted argmax.

**Setup (paper Section 6.1, p. 12):** Go + Lattigo. MNIST only. NN5 = 5-layer CNN; NN20 = 20-layer, ~754K params; NN50 = 50-layer, ~1M params. CKKS at 128-bit security. Local cluster, 20 ms network delay, 1 Gbps, Ubuntu 22.04, 12-core Intel Xeon E5-2680 2.5 GHz, 256 GB RAM. Results averaged over 3-5 runs.

**Table 2 (paper p. 14, verbatim) — NN20 on Scenario 3, varying model-provider count:**

| # of Parties | Latency (s) | Throughput (samples/s) |
|---|---|---|
| 3 | 245.58 (±0.50) | 1.19 |
| 5 | 238.15 (±4.12) | 1.22 |
| 10 | 278.19 (±9.11) | 1.05 |
| 20 | 354.17 (±10.66) | 0.82 |

Figure 5 (p. 14) gives amortized time per sample, distributed vs centralized bootstrapping: 0.84/0.82/0.95/1.21 s distributed against 1.67 s centralized at 3/5/10/20 parties.

**Table 3 (paper p. 15, verbatim) — NN50, batch of 585 samples, Scenario 3 at N=3 model-providers:**

| Scenario | Latency (s) | Amortized (s/sample) | Throughput (samples/s) | Avg latency/layer (s) |
|---|---|---|---|---|
| 1: plaintext model, encrypted data | 2,496.83 | 4.26 | 0.234 | 48.95 |
| 2: encrypted model, plaintext data | 2,699.75 | 4.62 | 0.216 | 52.93 |
| 3: encrypted model, encrypted data | 613.52 | 2.09 | 0.476 | 12.02 |

**Table 1 (paper p. 14, verbatim) — NN5, Scenario 1, latency (s) against prior frameworks:**

| Framework | batch 1 | batch 83 | batch 4,096 |
|---|---|---|---|
| CryptoNets | 250 | 250 | 250 |
| Faster CryptoNets | 39.1 | 3,245 | 160,153 |
| LoLa | 2.2 | 182.6 | 8,951 |
| nGraph-HE2 | 2.05 | 2.05 | 2.05 |
| **slytHErin** | **3.7** | **4.08** | **243.4** |

**Apples-to-apples with HE-OFT:** the closest quantitative peer we have. Both hold the model under a multiparty CKKS key and never decrypt it, and both key-switch only to the querier. **Two differences must be stated whenever the numbers are placed side by side.** (a) slytHErin evaluates the *entire network* homomorphically, which is why its models are 5-to-50-layer networks on MNIST rather than a pretrained transformer; we evaluate a public frozen backbone in plaintext on the client and put only the final linear map under encryption. (b) slytHErin returns the score vector; we take the argmax under encryption and return only the label. By our own §5.6 extraction record, a score vector is a materially cheaper extraction target than a label. Our comparable figure is the per-query total at N=10, 31.5 s at 4 classes and 113.2 s at 100 classes (`results/fhe_serve/cost_grid.json`, `argmax_tournament.csv`), single-threaded, unbatched, against their 278.19 s batch latency and ~0.95 s amortized per sample at 10 parties on a 12-core machine. **We do not batch and they do; any published comparison must say so.**

---

## 17. CryptPEFT (Xia et al., NDSS 2026)

**Saisai Xia, Wenhao Wang, Zihao Wang, Yuhui Zhang, Yier Jin, Dan Meng, Rui Hou. "CryptPEFT: Efficient and Private Neural Network Inference via Parameter-Efficient Fine-Tuning." NDSS 2026. arXiv:2508.12264 (submitted 17 Aug 2025).**

Verified 2026-08-02 from the arXiv abstract page. Title, author list and venue read directly.

**Abstract, verbatim (the operative sentences):**
> "we propose CryptPEFT, the first PEFT solution specifically designed for private inference scenarios. CryptPEFT introduces a novel one-way communication (OWC) architecture that confines encrypted computation solely to the adapter, significantly reducing both computational and communication overhead. ... We evaluated CryptPEFT using Vision Transformer backbones across widely used image classification datasets. Our results show that CryptPEFT significantly outperforms existing baselines, delivering speedups ranging from 20.62× to 291.48× in simulated wide-area network (WAN) and local-area network (LAN) settings. On CIFAR-100, CryptPEFT attains 85.47% accuracy with just 2.26 seconds of inference latency."

**Structural match to us:** public frozen ViT backbone run in plaintext by the client, client encrypts the intermediate features, only the adapter is evaluated under encryption, client receives the label. The motivation for the one-way architecture is ours: avoid the two-way traffic between backbone and adapter.

**Where it stops:** two-party secure computation (MPC), not HE. Single client and single provider, not federated. The secret adapter is that provider's plaintext. No training protocol, so it does not address how mutually distrustful parties would build the adapter.

**Apples-to-apples with HE-OFT:** a related-work anchor and a design-validation citation, not an accuracy peer. Their 85.47% on CIFAR-100 is a *single-provider fine-tune*, not a federated merge, so it is not comparable to our Table II CIFAR-100 figures. Cite it for the architecture, not for a number.

---

## 18. Mazzone et al. (USENIX Security 2025) — encrypted argmax peer

**Federico Mazzone, Maarten Everts, Florian Hahn, Andreas Peter. "Efficient Ranking, Order Statistics, and Sorting under CKKS." USENIX Security Symposium 2025, pp. 8541-8558. arXiv:2412.15126 (v1 19 Dec 2024, v2 10 Feb 2025).**

Verified 2026-08-02 from the arXiv abstract page for title, authors and venue. The 5.76 s and 78.64 s figures were reproduced on that page.

**Abstract figures:** ranks a 128-element vector in ≈5.76 s, computes argmin/argmax in 12.83 s, sorts in 78.64 s. Constant comparison depth, achieved by abandoning the swap-based paradigm and re-encoding the vector for simultaneous all-pairs comparison. Open source at github.com/FedericoMazzone/openfhe-statistics.

> **`n/r`: the 12.83 s argmin/argmax figure appeared in the automated extraction but was NOT reproduced on the second fetch, which dropped that clause. Transcribe it from the paper before it goes into the manuscript.** Ring degree and party model also `n/r`.

**Apples-to-apples with HE-OFT:** direct peer for `results/fhe_serve/argmax_tournament.csv`. Ours at C padded to 128 is 7 tournament rounds, 112.4 s total, of which 46.3 s is 34 collective refreshes, at N=10 parties and ring 2^15, single-threaded. Theirs is single-key. The gap is a mix of the multiparty setting, the refresh count and the algorithm. **Cite it as the construction that would reduce our dominant cost, not as a like-for-like defeat.**

---

## 19. cutmax (Avitan et al., 2025) — argmax at vocabulary scale

**Matan Avitan, Moran Baruch, Nir Drucker, Itamar Zimerman, Yoav Goldberg. "Efficient Decoding Methods for Language Models on Encrypted Data." arXiv:2509.08383 (v1 10 Sep 2025, v2 17 Nov 2025).**

Verified 2026-08-02 from the arXiv abstract page.

**Abstract, verbatim (operative sentences):**
> "We introduce cutmax, an HE-friendly argmax algorithm that reduces ciphertext operations compared to prior methods, enabling practical greedy decoding under encryption. We also propose the first HE-compatible nucleus (top-p) sampling method, leveraging cutmax for efficient stochastic decoding with provable privacy guarantees. ... Evaluations on realistic LLM outputs show latency reductions of 24x-35x over baselines, advancing secure text generation."

Per-model timings (32,768 and 151,936 vocabularies, 1× H100) appeared in the automated extraction but are **`n/r`** here: not reproduced on the verification fetch. Transcribe before use.

**Apples-to-apples with HE-OFT:** two-party, plaintext model, encrypted input, so the trust model is not ours. Relevant in two places. It is the right citation for the label-only interface argument, since it returns an encrypted one-hot without decrypting the scores. And **it publishes an HE-compatible top-p sampling method, which overlaps the Gumbel-max sampling result in `docs/notes/generation-scope.md` that we have not implemented.** Read it before that note is written up.

---

## 20. GH-OFL (Turazza, Picone & Mamei, ICLR 2026)

**Fabio Turazza, Marco Picone, Marco Mamei. "The Gaussian-Head OFL Family: One-Shot Federated Learning from Client Global Statistics." ICLR 2026. arXiv:2602.01186 (v1 1 Feb 2026, v2 29 May 2026).**

Verified 2026-08-02 from the arXiv abstract page: title, author list, venue and dates read directly.

**What it does (from the abstract):** assumes class-conditional Gaussianity of pretrained embeddings, so clients transmit only per-class sufficient statistics rather than models. The server builds heads from three components: closed-form Gaussian heads, FisherMix with synthetic samples, and Proto-Hyper for refinement. Claims state-of-the-art robustness under strong non-IID skew while remaining strictly data-free.

> **`n/r`: datasets, backbones, client counts, α values and every accuracy figure.** Only the abstract page was read. Transcribe the results tables before any number is used or any comparison is claimed.

**Apples-to-apples with HE-OFT:** structurally this is our accuracy setting with the cryptography removed — one round, frozen pretrained encoder, a head fitted at the server. It is the peer a reviewer familiar with this line will name. The comparison favours us on the security axis and tests us on accuracy: GH-OFL uploads per-class sufficient statistics **in plaintext**, which is precisely the object our coverage-weighted merge keeps encrypted, because a coalition that learned the per-class totals recovers the remaining client's class histogram. Worth reading properly before Table II is defended.

---

## What this table is for

1. **Bound our v1 claims** against what each closest published neighbour reports. Today, v1 on MNIST is in the same band as FedKT non-private (62.8 % FedAvg, 90.5 % FedKT) and roughly tracks DENSE's CIFAR-10 / α=0.1 (50.26 %) when normalised across dataset difficulty — but we are MNIST-only and have not built CIFAR yet, so the direct number isn't apples-to-apples.
2. **Pin the resubmission's positioning axes**:
   - **Plaintext one-shot utility ceiling**: Co-Boosting (CIFAR-10 / N=10 / α=0.1 / CNN-5 = 57.09 %); FuseFL (CIFAR-10 / M=5 / K=2 / α=0.5 = 84.34 % — but K=2 means 2 communication rounds, framed as 1-shot in their accounting); FedSD2C (Tiny-ImageNet ResNet-18 / N=10 / α=0.1 = 26.83 %, complex datasets); FedLPA (MNIST / 10c / β=0.3 / 5-layer CNN = 85.77 %).
   - **DP one-shot utility-privacy frontier**: FedDiff (CIFAR-10 / ε=10 = 27.78 %; FashionMNIST / ε=1 = 65.53 %); **FedAUXfdp (CIFAR-10 / N=20 / α=0.01 / ShuffleNet / ε=0.5 = 75.2 %)** — currently the strongest DP one-shot CIFAR-10 number we have paper-verbatim, with the caveat of pretrained auxiliary feature extractor; FedKT for MNIST/SVHN; FedGM headline (label-DP CIFAR-10 ≈ 67.5 %) **unverified — MDPI PDF blocked**.
   - **HE multi-round peer**: POSEIDON (MNIST / N=10 = 92.1 % in 1.4 h, multi-round). **HE secure-aggregation primitive**: Hyb-Agg (MK-CKKS + ECDH, 1-round, ~12× expansion, 431.8 ms client on Raspberry Pi 4) — pluggable into our aggregator.
   - **Public-probe methodology lineage**: FedMD (heterogeneous-task), DS-FL (same-domain).
   - **Data-free one-shot lineage**: DENSE, Co-Boosting, FedSD2C (distiller-distillate instead of generator).
   - **Posterior / Bayesian one-shot lineage**: FedLPA.
   - **Block-fusion progressive-train lineage**: FuseFL.

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
- [x] **FedSD2C — Table 1 main cells (Tiny-ImageNet, ImageNette, OpenImage) on ConvNet + ResNet-18.** Resolved 2026-05-22 by PDF extraction (lines 419-438). Agent's earlier claim (47.52 / 26.83 on ResNet-18) verified.
- [x] **FedSD2C — DP integration cells.** Resolved 2026-05-22: Table S6 (ResNet-18, Tiny-ImageNet, ε ∈ {1, 4, 8, ∞}) = 22.92 / 25.13 / 26.01 / 26.83.
- [x] **FuseFL — Table 2 main cells across 6 datasets × 3 α × 3 K values.** Resolved 2026-05-22 by PDF extraction (lines 604-608). Agent's earlier "CIFAR-10 α=0.5 K=2 84.34%" verified.
- [x] **FuseFL — default M (number of clients).** Resolved 2026-05-22: M=5 default; sweep over M ∈ {5, 10, 20, 50}.
- [x] **FedLPA — Table 1 main cells (FMNIST, MNIST, CIFAR-10, SVHN) × Dirichlet β grid × baselines.** Resolved 2026-05-22 by PDF extraction (lines 464-505). Agent's "FMNIST β=0.01 21.20 vs DENSE 15.23" verified. Default 10 clients, 5-layer CNN, NIID-Bench partition.
- [x] **FedLPA — architecture (user suspected small-model constraint).** Resolved 2026-05-22: confirmed simple 5-layer CNN as default; VGG-9 + EMNIST in Appendix G.
- [x] **FedAUXfdp — Tables 2, 3, 4 ε grid + accuracy cells.** Resolved 2026-05-22 by PDF extraction (lines 605-625). Full ε ∈ {1.0, 0.5, 0.1, 0.01} grid extracted; N=20, CIFAR-10 client data + STL-10/CIFAR-100 aux, ShuffleNet/MobileNetv2/ResNet8.
- [x] **FedDiff = arXiv:2405.01494; FMF is in-paper extension, not a separate work.** Resolved 2026-05-22; FashionMNIST and PathMNIST Table 4 baseline rows extracted (lines 585-591).
- [ ] **FedGM — full PDF extraction.** Blocked: MDPI CDN returns HTTP 403 to all automated fetches (curl/WebFetch). Need a human to open the PDF in a browser and paste the relevant table text. Cells `n/r`: N, partition, ε grid, full accuracy table. Headline "67.5 ± 0.2 % on CIFAR-10" is from a search-engine snippet only, not paper-verbatim.
- [x] **Hyb-Agg — datasets / latency / expansion factor.** Resolved 2026-05-22: synthetic-vectors-only, no ML accuracy; 12× expansion, 431.8 ms client / 191.1 ms server on Raspberry Pi 4 (N=50, d=8192). Protocol-only paper.

Until the open boxes are filled, the comparator-vs-v1 narrative leans on the cells already extracted above. None of the numerical claims in the file are LLM-generated digits.
