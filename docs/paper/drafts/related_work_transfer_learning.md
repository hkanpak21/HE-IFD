# Draft — related-work additions: private transfer learning (for HITL review)

From the PI comment (similarity to few-shot / transfer learning; add encrypted + DP works;
find comparators). Two proposed paragraphs + bib entries + comparator plan + a differentiator
table. NOT yet in .tex.

NOTE on a correction: the search agent carried some stale framing from the *old* distillation
method ("Phase-0 P2P alignment", "shared aligned init"). The CURRENT method has **no alignment
phase** — the frozen backbone supplies the shared frame. The drafts below use the correct
current framing.

---

## Paragraph A — Encrypted transfer learning (insert in related.tex, near the HE-aggregation para)

Transfer learning under encryption has been studied, but in settings structurally different
from ours. The closest is encrypted training of a small classifier on frozen public features:
HETAL trains a softmax head on a frozen backbone entirely under CKKS, and is, by its own
description, a practical scheme for \emph{encrypted training}~\cite{lee2023hetal}; a longer line
trains linear or logistic models under homomorphic encryption by iterative encrypted gradient
descent~\cite{kim2018securelr,kim2018logistic,blatt2020semiparallel}, recently extended to small
networks and transformer layers~\cite{chiang2025cnn,frery2024encryptedft}. All of these run an
\emph{optimizer on ciphertexts}: the multiplicative depth grows with the number of steps, the
nonlinearities (softmax, sigmoid) must be polynomial-approximated, and bootstrapping is often
required. They are also single-party --- one data owner outsourcing computation to a server ---
rather than a collaboration among mutually distrustful parties. A federated variant, Priv-FedTL,
encrypts only the fine-tuned last layer of a frozen backbone across clients, but aggregates it
over \emph{many} rounds of federated training~\cite{privfedtl2026}; a concurrent scheme
homomorphically averages encrypted feature tokens for encrypted inference under a single
decryption key~\cite{alamin2025vit}. Our setting differs from every one of these on the axis that
matters for cost: we perform \emph{no} encrypted training. Each client fine-tunes in plaintext on
its own data, and the server's only homomorphic operation is a single depth-one weighted sum of
the encrypted displacements, decrypted by a threshold of clients --- no encrypted optimizer, no
polynomial nonlinearity, no bootstrapping, and no single party trusted to train or to decrypt.
The same property that separates us from encrypted \emph{training} of a full model
(\cref{sec:related-he}) separates us from encrypted training of a small head: we move the
learning out of the ciphertext domain entirely and leave the server a linear merge.

## Paragraph B — Differentially private transfer learning (insert near the DP one-shot para)

The privacy-utility trade-off our cryptographic design avoids is most sharply visible in
differentially private transfer learning, which is the natural lossy counterpart to our setting.
A well-established line shows that DP works best precisely on \emph{frozen} public features:
linear or parameter-efficient models trained with DP-SGD on a pretrained backbone reach strong
accuracy at moderate privacy budgets~\cite{tramer2021features,mehta2022dpfeatures,yu2022dpft,li2022dplearners},
and this extends to federated low-rank adaptation under
DP~\cite{liu2023dplora,xu2024dpdylora}. These methods share our backbone-plus-small-unit
structure but pay a budget-dependent accuracy tax --- the noise enters the released model --- and
they are either centralized or run over many federated rounds. Our protocol occupies the same
structural niche without the tax: the contributions are protected cryptographically rather than
by perturbation, so the released model carries no privacy-induced noise, and the entire exchange
is one round. To our knowledge no prior method is simultaneously one-shot, federated, and
private (whether by HE or DP) in this transfer-learning setting.

---

## Bib entries (append to refs.bib)

@inproceedings{lee2023hetal,
  title={{HETAL}: Efficient Privacy-preserving Transfer Learning with Homomorphic Encryption},
  author={Lee, Seewoo and Lee, Garam and Kim, Jung Woo and Shin, Junbum and Lee, Mun-Kyu},
  booktitle={International Conference on Machine Learning (ICML)}, year={2023}, note={arXiv:2403.14111}}

@article{privfedtl2026,
  title={Privacy-preserving federated transfer learning for resource-constrained devices},
  author={(authors per ScienceDirect S1389128626004615)},
  journal={Computer Networks}, year={2026}}

@article{alamin2025vit,
  title={Privacy-Preserving Federated Vision Transformer Learning with Lightweight Homomorphic Encryption in Medical AI},
  author={Al Amin, and Hasan, and Hong, and Ullah,}, journal={arXiv:2511.20983}, year={2025}}

@article{kim2018securelr,
  title={Secure Logistic Regression Based on Homomorphic Encryption: Design and Evaluation},
  author={Kim, Miran and Song, Yongsoo and Wang, Shuang and Xia, Yuhou and Jiang, Xiaoqian},
  journal={JMIR Medical Informatics}, year={2018}}

@article{kim2018logistic,
  title={Logistic regression model training based on the approximate homomorphic encryption},
  author={Kim, Andrey and Song, Yongsoo and Kim, Miran and Lee, Keewoo and Cheon, Jung Hee},
  journal={BMC Medical Genomics}, year={2018}}

@article{blatt2020semiparallel,
  title={Secure large-scale genome-wide association studies using homomorphic encryption},
  author={Blatt, Marcelo and Gusev, Alexander and Polyakov, Yuriy and Goldwasser, Shafi},
  journal={PNAS / Proc. (semi-parallel logistic regression with FHE)}, year={2020}}

@article{chiang2025cnn,
  title={Privacy-Preserving CNN Training with Transfer Learning: Two Hidden Layers},
  author={Chiang, John}, journal={arXiv:2504.12623}, year={2025}}

@inproceedings{frery2024encryptedft,
  title={On Encrypted Fine-tuning of Transformers using Fully Homomorphic Encryption},
  author={(PPAI@AAAI authors)}, booktitle={PPAI@AAAI}, year={2024}, note={arXiv:2402.09059}}

@inproceedings{tramer2021features,
  title={Differentially Private Learning Needs Better Features (or Much More Data)},
  author={Tram{\`e}r, Florian and Boneh, Dan},
  booktitle={International Conference on Learning Representations (ICLR)}, year={2021}, note={arXiv:2011.11660}}

@article{mehta2022dpfeatures,
  title={Differentially Private Image Classification from Features},
  author={Mehta, Harsh and Krichene, Walid and Thakurta, Abhradeep and Kurakin, Alexey and Cutkosky, Ashok},
  journal={Transactions on Machine Learning Research (TMLR)}, year={2023}, note={arXiv:2211.13403}}

@inproceedings{yu2022dpft,
  title={Differentially Private Fine-tuning of Language Models},
  author={Yu, Da and Naik, Saurabh and Backurs, Arturs and Gopi, Sivakanth and Inan, Huseyin A. and others},
  booktitle={International Conference on Learning Representations (ICLR)}, year={2022}, note={arXiv:2110.06500}}

@inproceedings{li2022dplearners,
  title={Large Language Models Can Be Strong Differentially Private Learners},
  author={Li, Xuechen and Tram{\`e}r, Florian and Liang, Percy and Hashimoto, Tatsunori},
  booktitle={International Conference on Learning Representations (ICLR)}, year={2022}, note={arXiv:2110.05679}}

@article{liu2023dplora,
  title={{DP-LoRA}: Differentially Private Low-Rank Adaptation of Large Language Models Using Federated Learning},
  author={Liu, Xiao-Yang and others}, journal={ACM TMIS}, year={2024}, note={arXiv:2312.17493}}

@article{xu2024dpdylora,
  title={{DP-DyLoRA}: Fine-Tuning Transformer-Based Models On-Device under Differentially Private Federated Learning using Dynamic Low-Rank Adaptation},
  author={(authors)}, journal={arXiv:2405.06368}, year={2024}}

---

## Comparator plan (PI asked "is there anyone to compare against")

1. **Priv-FedTL (Computer Networks 2026) — the natural head-to-head.** Same federated + frozen
   backbone + encrypt-only-the-small-part, on MedMNIST (Pneumonia/Breast). Match their setup; put
   our one-shot accuracy + comm next to their multi-round numbers. CAVEAT: 3 weeks old, paywalled
   (ScienceDirect 403) — need the PDF for exact numbers; verify single-key vs threshold CKKS.
2. **HETAL — the crypto-COST baseline, not an accuracy rival.** Different problem (single-party
   outsourced training). Use it for a "what the server computes under HE" comparison:
   multiplicative depth, encrypted ops, nonlinearity. See the differentiator table below.
3. **DP-DyLoRA (ε=2) / DP-LoRA — DP federated-LoRA comparators.** Match ε at our datasets/N; show
   our HE point recovers non-private accuracy that no DP-ε point reaches.
4. **Cheapest, most reproducible: a DP-SGD logistic head on the SAME frozen features our clients
   use** (numbers exist: CIFAR-10 67.8%@ε=1, CIFAR-100 73.8%@ε=2 — arXiv:2307.11106). Plot our
   zero-cost crypto point above the whole DP privacy-utility curve. Low effort, strong rhetoric.

## Differentiator table (proposed new table — the strongest quantitative point)

"What the server must compute under HE":

| Method | encrypted object | server HE op | mult. depth | nonlinearity under HE | rounds | parties |
|---|---|---|---|---|---|---|
| HETAL | features | iterative encrypted SGD | grows with steps | softmax approx | many steps | single (outsourced) |
| encrypted-LR (Kim'18 …) | data | iterative encrypted SGD | grows with steps | sigmoid approx | many steps | single |
| Priv-FedTL | last-layer params | FedAvg-style sum | per round | none | many | federated |
| **HE-IFD (ours)** | **adapter+head displacement** | **one weighted sum** | **1** | **none** | **1** | **multiparty/threshold** |
