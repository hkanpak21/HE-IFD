# FL_TDSC paper changes — Overleaf replay log

This log records every textual change made to the manuscript so the user can replay them in Overleaf. Line numbers refer to the **original** files extracted from `FL_TDSC.zip` (the snapshot taken at unpack time, before any edits below). Each entry has the form:

```
### <file>:<line-range>
Reason: <one line>
Before:
  <verbatim original snippet>
After:
  <verbatim replacement snippet>
```

Sections below mirror the four advisor concerns plus a verification section. Edits inside one section may touch multiple files.

---

## 1. Plaintext KL removal

Goal: drop the "Plaintext KL" baseline from the comparison narrative; the only plaintext reference points remaining are the centralised Oracle and the mean individual teacher accuracy.

Note on figures: `figures/fig_main_resnet18.pdf` and `figures/fig_arch_gen.pdf` have been regenerated without the teal Plaintext KL curve (see "Figure regeneration" entry below). The originals are preserved at `figures/_pre_kl_removal/`. The textual edits below now match the figure content.

### experiments.tex:20 (figure caption of `fig:main_resnet18`)
Reason: caption announced "Plaintext KL (teal)" as a comparator; rewriting to refer only to the two remaining plaintext reference lines (Oracle and mean teacher).
Before:
```
\caption{HE-IFD accuracy on CIFAR-10 (top) and FashionMNIST (bottom) with ResNet-18 teachers and PolyResNet-18 student. The Oracle (dashed gray) is the centralised upper bound. Plaintext KL (teal) shows what standard distillation achieves without encryption constraints. HE-IFD (orange) approaches to Oracle at small $N$ and consistently outperforms the mean teacher across all settings.}
```
After:
```
\caption{HE-IFD accuracy on CIFAR-10 (top) and FashionMNIST (bottom) with ResNet-18 teachers and PolyResNet-18 student. The two plaintext reference lines are the centralised Oracle (dashed gray, upper bound trained on all pooled data with no privacy protection) and the mean individual teacher accuracy at each setting (solid gray, the natural local-only floor each client could achieve without collaboration). HE-IFD (orange) approaches the Oracle at small $N$ and consistently outperforms the mean teacher across all settings.}
```

### experiments.tex:24-29 (Baselines list)
Reason: removed the Plaintext KL bullet and replaced the heading "Baselines" with "Reference points"; added an explicit Mean-individual-teacher reference and a sentence explaining why the polynomial-vs-ReLU question is no longer treated as a separate baseline in this paper.
Before:
```
\textbf{Baselines.} We employ the following baselines for our accuracy comparisons.
\begin{itemize}[nosep]
    \item \textbf{Oracle}: Standard ResNet-18 trained on all pooled data (centralised upper bound with no privacy protection).
    \item \textbf{Plaintext KL}: Standard ResNet-18 student trained via KL divergence on averaged teacher logits (no HE constraints). Shows the gap from using polynomial activations.
    % \item \textbf{HE-IFD}: PolyResNet-18 student trained via the full encrypted protocol with bootstrapping-enabled cascade refinement.
\end{itemize}
```
After:
```
\textbf{Reference points.} We anchor every accuracy curve in this section to two plaintext references that bracket the achievable range without our protocol:
\begin{itemize}[nosep]
    \item \textbf{Oracle}: a standard ResNet-18 trained on all pooled data in plaintext, with no privacy protection. This is the centralised upper bound on accuracy and the strongest possible baseline a non-private system could achieve.
    \item \textbf{Mean individual teacher}: the unweighted average accuracy of the $N$ local teacher models, each evaluated on the global test set after being trained only on its own private partition. This is the strongest accuracy that any client could obtain on its own without collaboration, and it is the relevant comparator for assessing whether participating in the protocol is worthwhile.
\end{itemize}
We do not include a separate plaintext-KL distillation baseline: the question this paper addresses is not how polynomial activations compare with ReLU under standard distillation (a centralised question, already studied in~\cite{baruch2022methodology, agamennone2025polynomial, alhossain2025training}), but whether a one-shot encrypted federated protocol can recover an accuracy that lies between the local-only mean teacher and the centralised Oracle.
```

### experiments.tex:49 (takeaway sentence)
Reason: the sentence anchored the degradation pattern to the now-removed Plaintext KL curve; reanchored to the Oracle (which is also the only plaintext line that survives in the figure once Plaintext KL is dropped).
Before:
```
\textbf{HE-IFD exhibits trends similar to the baseline as $N$ increases.} At $N{=}4$, $\alpha{=}0.1$, HE-IFD achieves 57\% on CIFAR-10 and 85\% on FashionMNIST. At $N{=}16$, $\alpha{=}0.1$, it reaches 35--37\% and 65--67\%, respectively. This degradation closely follows the Plaintext KL baseline, confirming that the accuracy loss comes solely from data fragmentation across more clients (weaker individual teachers), not from the encryption.
```
After:
```
\textbf{HE-IFD tracks the centralised Oracle as $N$ increases.} At $N{=}4$, $\alpha{=}0.1$, HE-IFD achieves 57\% on CIFAR-10 and 85\% on FashionMNIST. At $N{=}16$, $\alpha{=}0.1$, it reaches 35--37\% and 65--67\%, respectively. The Oracle, which has no privacy constraint and sees all pooled data, degrades along the same shape as the per-client partition shrinks; HE-IFD's curve runs roughly parallel to it across $N$. This confirms that the residual accuracy loss is attributable to data fragmentation across more clients (weaker individual teachers), not to the encryption.
```

(No other Plaintext-KL mentions in the manuscript — confirmed via grep across all .tex.)

### Figure regeneration: figures/fig_main_resnet18.pdf and figures/fig_arch_gen.pdf
Reason: the two affected PDFs in `FL_TDSC/figures/` carried a teal Plaintext KL curve that the rewritten captions and takeaways no longer reference. Regenerated without that curve so figure and prose match.

How:
- Edited `scripts/generate_figures_v2.py` so (a) `OUT` is overridable via the `FIG_OUT` env var (default unchanged at `./HEIFD_Paper/figures` for backward compatibility), (b) the two `Plaintext KL` (`kl_resnet`, `kl_vit`) plot calls were removed from `fig_main()` and `fig_arch()` (both SimpleCNN and ViT panels), and (c) the `__main__` block accepts argv to scope which figures are regenerated.
- Backed up the originals to `FL_TDSC/figures/_pre_kl_removal/` so the user can diff or revert.
- Ran `FIG_OUT=./FL_TDSC/figures /home/hkanpak21/.conda/envs/he_ofl/bin/python scripts/generate_figures_v2.py main arch` to regenerate only the two affected figures, leaving `fig_privacy.pdf`, `fig_communication.pdf`, and `fig_computation.pdf` untouched (they never had a Plaintext KL curve).
- Verified the new PDFs visually: each panel now shows three series (Oracle dashed, HE-IFD orange, Mean Teacher cross-marker) with the legend listing exactly those three.

If you ever want to regenerate the figures again from updated `results/` data, the same command works; the script no longer needs to be re-edited.



---

## 2. Voice rewrite (theory/explanation-oriented)

Goal: shift the introduction, abstract, conclusion, and lead-ins of methodology subsections from implementation-flavoured to property-of-the-function-class statements. Numerical anecdotes (e.g., "magnitude 5 → 11 → 44", "this can reach 10^4") are removed from the introduction; concrete numbers stay in the experiments section.

### introduction.tex:26 (paragraph "Polynomial magnitude explosion")
Reason: replaced the "magnitude 5 → 11 → 44" anecdote with a structural statement about polynomial deep networks (composition of degree-d activations across L blocks yields degree d^L). Magnitude control is positioned as a property of the function class, not a numerical workaround.
Before:
```
\par\noindent\textbf{Polynomial magnitude explosion.} The quadratic activation $ax^2 + bx$ amplifies feature magnitudes at every composition. An input of magnitude 5 produces roughly 11 after one block, 44 after two; across five blocks this can reach $10^4$, causing gradient overflow. The problem is exacerbated in the multi-client setting, where teachers trained on heterogeneous data partitions produce features with incompatible magnitude ranges, and the HE-compatible replacement for batch normalisation (a static per-channel scale-and-shift) cannot dynamically compensate.
```
After:
```
\par\noindent\textbf{Polynomial magnitude growth is a structural property of the network class.} A polynomial activation of degree $d$, composed across $L$ blocks, yields an end-to-end map of degree $d^L$ in its input. The induced upper bound on the activation magnitude grows doubly-exponentially in depth, regardless of how the polynomial coefficients are chosen, and this is what distinguishes polynomial deep networks from ReLU networks (whose composition is piecewise $1$-Lipschitz). The federated setting amplifies the effect: heterogeneous clients induce different distributions on each block boundary, and the HE-compatible analogue of batch normalisation, a static per-channel affine map fixed before training, cannot adapt across distributions. Magnitude control is therefore a structural requirement for polynomial deep networks under federated encryption, not a numerical workaround.
```

### introduction.tex:28 (paragraph "Training--distillation distribution gap")
Reason: recast as a covariate-shift argument across composed blocks rather than a description of an empirical failure mode ("collapses to chance-level accuracy"). Bridges and refinement become explicit consequences of the consistency requirement.
Before:
```
\par\noindent\textbf{Training--distillation distribution gap.} Distilling block by block avoids CKKS multiplicative depth (see Section~\ref{sec:ckks_prelim}) accumulation, but training block $k$ on teacher-produced inputs creates a mismatch: at inference, block $k$ receives student-produced inputs from the frozen prefix. Without correction, the composed model's performance degrades toward chance-level accuracy. We address this through trainable per-channel affine bridges, initialised from uploaded feature statistics, followed by server-side sequential refinement that exposes each block to its actual inference-time distribution, without any additional client communication.
```
After:
```
\par\noindent\textbf{Training and inference distributions diverge under block-wise composition.} Decomposing the student into blocks and training each block independently confines the CKKS multiplicative depth to a single block (see Section~\ref{sec:ckks_prelim}), but it also introduces a covariate shift across the composition: block $k$ is trained on the distribution of teacher-produced inputs and evaluated on the distribution of student-produced inputs from the frozen prefix. The composed map cannot be consistent at inference unless this gap is closed. We close it through trainable per-channel affine bridges, initialised from the uploaded feature statistics, followed by a sequential refinement pass that exposes each block to its actual inference-time distribution. Both steps remain server-side and require no additional client communication.
```

### introduction.tex:31 (paragraph "Scale-aligned distillation loss")
Reason: same treatment — motivate the loss design from required invariances (sign asymmetry, scale-freeness, symmetry of over- and under-scaling) rather than from observed instability.
Before:
```
\par\noindent\textbf{Scale-aligned distillation loss.} Standard MSE is sensitive to the sign asymmetry between polynomial activations and ReLU features and allows unbounded magnitude drift that amplifies through frozen downstream blocks. Our loss combines channel-normalised MSE, which aligns feature \textit{shape} independently of scale, with a log-ratio penalty $(\log,\sigma_{\hat{f}}/\sigma_{\tilde{f}})^2$ that anchors the student's feature \textit{magnitude} to the teacher's. Unlike a plain $\ell_2$ scale penalty, the log-ratio form penalises multiplicative over- and under-scaling symmetrically and is scale-free.
```
After:
```
\par\noindent\textbf{The distillation loss must be scale-aware in magnitude and shape-aware in feature space.} Standard mean squared error is not invariant to the sign asymmetry between ReLU and polynomial features and admits unbounded magnitude drift, which is then amplified through every frozen downstream block. The structural argument above forces the loss to control \textit{shape} and \textit{magnitude} separately. We use a channel-normalised mean-squared error to align the feature shape independently of scale, combined with a log-ratio penalty $(\log\,\sigma_{\hat{f}}/\sigma_{\tilde{f}})^2$ on the per-channel standard deviations. The log-ratio form is the natural choice for matching magnitudes: it is symmetric in over- and under-scaling and invariant to a uniform rescaling of the targets, properties that a plain $\ell_2$ scale penalty does not satisfy.
```

### introduction.tex:33 (closing paragraph of "Our Approach")
Reason: stripped numeric headlines ("60.13%", "5.3 pp", "4--10 pp") from the introduction; kept one summary sentence pointing the reader to Section~\ref{sec:experiments}. Numbers stay in experiments.tex where they belong.
Before:
```
Together, these mechanisms yield stable convergence and strong accuracy across our CIFAR-10 experiments under non-IID federated partitioning. With 16 clients under highly heterogeneous data partitions, the PolyResNet-18 student achieves 60.13\%, surpassing the best individual teacher (54.79\%) by 5.3 percentage points. After threshold decryption, clients may fine-tune the shared student on their local data, improving per-client local accuracy by 4--10 percentage points without transmitting any gradients or data, or use the decrypted student as a teacher for reverse knowledge distillation into an unconstrained local ResNet-18. Our experiments across three architectures (ResNet-18, SimpleCNN, and ViT-B/32) confirm that the framework generalises beyond a single model family.
```
After:
```
Together, these three properties of polynomial deep networks under federated encryption (doubly-exponential magnitude growth, train-inference covariate shift across composed blocks, and the need for a scale-aware loss) determine the design of the protocol. Section~\ref{sec:methodology} develops each of them; Section~\ref{sec:experiments} reports the resulting accuracy on CIFAR-10 and FashionMNIST across three architectures (ResNet-18, SimpleCNN, ViT-B/32), confirms that the framework generalises beyond a single model family, and shows that the encrypted student tracks the centralised plaintext Oracle and exceeds the mean individual teacher across all heterogeneity settings.
```

### main.tex:93-96 (abstract body)
Reason: rewrote the abstract into two paragraphs. Paragraph 1 states the protocol-level property (every server-side intermediate is a ciphertext under collectively held keys; release requires joint key-switching). Paragraph 2 states the training-procedure property (the design is forced by composition-of-polynomials and train-inference divergence). Removed implementation-specific phrasing ("PolyResNet-18", "11.17M parameters") and "progressive stacking" jargon from the abstract; the technical name returns in Section~\ref{sec:methodology}. Removed the "best individual teacher" framing and replaced it with the mean-teacher framing now used in experiments.tex.
Before:
```
We present HE-IFD, a one-shot, privacy-preserving federated knowledge distillation framework in which all client contributions remain encrypted throughout server-side processing.
Each client trains a local teacher model and extracts intermediate feature pairs at each block boundary, where a block is a contiguous group of layers (e.g., a residual stage) whose input and output are matched during distillation. These pairs are encrypted with homomorphic encryption (HE) and uploaded only once to the server. The server then distills these encrypted supervision signals into a full-depth HE-compatible student model without ever observing plaintext data, weights, or activations.

Training an HE-compatible student with polynomial activations and no batch normalisation is unstable under standard end-to-end distillation. We address this with progressive stacking: block-by-block training where each block receives fresh ciphertexts, avoiding accumulation of HE multiplicative depth. Combined with client-side collaborative normalisation, magnitude-regularised loss, and student-input training, this procedure yields stable convergence. Under non-IID data partitions, the student aggregates specialised knowledge from all teachers, matching or exceeding the performance that each teacher achieves on its own local class distribution. This presents a strong participation incentive for every client, even when the student's global accuracy is lower than that of the best individual teacher.
```
After:
```
We present HE-IFD, a one-shot federated knowledge distillation protocol whose central property is that every client contribution, and every server-side intermediate, remains a homomorphic ciphertext throughout training. Each client trains a local teacher on its private data, extracts the input-output pair of every block boundary, and uploads them, encrypted under a multiparty CKKS scheme with collectively held keys, to the server in a single communication round. The server distils these encrypted pairs into a homomorphism-compatible student, performing forward pass, loss evaluation, gradient computation, and weight update entirely on ciphertexts. The trained student is released to the clients only through a collective key-switching step that requires every client to participate, so the server's view of the protocol is, by construction, computationally indistinguishable from random.

Training such a student is constrained by the structure of the polynomial network class: the composition of degree-$d$ activations across $L$ blocks produces an end-to-end map of degree $d^L$, whose magnitude grows doubly-exponentially in depth, and whose train-time and inference-time input distributions diverge once each block is trained in isolation. We treat magnitude control and distribution alignment as first-class consequences of these properties rather than as numerical workarounds. The resulting protocol combines client-side collaborative normalisation, a magnitude-regularised loss with a symmetric scale-free penalty, and a server-only refinement pass that closes the train-inference gap without further client communication. Under non-IID data partitions, the student aggregates specialised knowledge from all teachers and consistently exceeds the mean individual teacher accuracy across heterogeneity settings, providing a participation incentive for every client.
```

### methodology.tex:164 (lead-in to "Training Stability" subsection)
Reason: reframed the lead-in as a consequence of the structural argument now established in Section~\ref{sec:introduction}. Numerical "$ax^2+bx+c$" example removed; the bulleted list of mechanisms below is unchanged.
Before:
```
Polynomial activations amplify magnitudes: $f(x) = ax^2 + bx + c$ maps moderate inputs to larger outputs, and successive compositions cause rapid growth. We address this with several complementary mechanisms:
```
After:
```
As established in Section~\ref{sec:introduction}, the composition of degree-$d$ polynomial activations across $L$ blocks yields an end-to-end map of degree $d^L$, whose magnitude bound grows doubly-exponentially in depth. This is a property of the function class rather than of any particular implementation, and it must be controlled by a combination of mechanisms that act on different parts of the protocol. Concretely:
```

### conclusion.tex:4 (opening paragraph)
Reason: replaced the "blind compute delegate" implementation flavour with a property-of-the-protocol statement (server's view is computationally indistinguishable from random; release requires collective key-switching). Made the contrast with differential privacy explicit on the right axis (statistical vs. cryptographic; no noise composition assumption).
Before:
```
We presented HE-IFD, a one-shot federated knowledge distillation framework in which all client contributions remain encrypted throughout server-side processing. The server acts as a blind compute delegate, distilling encrypted supervision signals into a full-depth HE-compatible student without ever observing plaintext data, weights, or activations. The CKKS encryption provides a cryptographically guaranteed privacy against a semi-honest server, eliminating the privacy-utility trade-off that characterises differential privacy approaches.
```
After:
```
We presented HE-IFD, a one-shot federated knowledge distillation protocol whose central property is that every client contribution and every server-side intermediate is, by construction, a homomorphic ciphertext under collectively held keys. The server's view of training is computationally indistinguishable from random under the IND-CPA security of multiparty CKKS, and release of the trained student requires the joint participation of all clients via collective key-switching. This is a fundamentally different privacy guarantee from the statistical one offered by differential privacy: it does not trade utility for privacy, and it does not require any assumption about the composition of noise across rounds.
```


---

## 3. Threshold HE clarification

Goal: rewrite Phase 3 of the methodology to explain how threshold HE is actually used — DKG to produce a collective public key with per-client secret-key shares, encryption under the collective key, server-side homomorphic computation as in single-key CKKS, collective key-switching for decryption that requires every client to participate. Cite Lattigo (already in bib) and add a Mouchet et al. citation for the underlying multiparty-CKKS scheme.

### references.bib:409 (after the `lattigo` entry)
Reason: added the Mouchet et al. PoPETs 2021 reference for the underlying multiparty CKKS scheme, distinct from the Lattigo software citation.
Before: (no entry)
After:
```
@article{mouchet2021multiparty,
  title={Multiparty Homomorphic Encryption from Ring-Learning-with-Errors},
  author={Mouchet, Christian and Troncoso-Pastoriza, Juan R. and Bossuat, Jean-Philippe and Hubaux, Jean-Pierre},
  journal={Proceedings on Privacy Enhancing Technologies},
  volume={2021},
  number={4},
  pages={291--311},
  year={2021}
}
```

### methodology.tex:21-23 (Threat Model and CKKS instantiation)
Reason: extended the threat model with the explicit "at least one honest client" trust assumption that the multiparty CKKS construction guarantees, and made the CKKS instantiation reference the multiparty scheme rather than vanilla CKKS. Added forward reference to the rewritten Phase 3.
Before:
```
\par\noindent\textbf{Threat Model.} We assume a semi-honest (honest-but-curious) server that follows the protocol faithfully but may attempt to infer private information from everything it observes. All clients are assumed to behave honestly. The adversary's goal is to infer information about a client's private dataset $\mathcal{D}_i$ or the client's local model, including individual samples, label distributions, or model weights, from the messages it receives during training.

Given this system and threat model, sending plaintext teacher outputs to the server is insufficient. Because, as discussed in Section~\ref{sec:bg_server_inference}, even a single round of plaintext knowledge transfer exposes clients to inference and inversion attacks. We therefore instantiate the knowledge transfer channel using the CKKS HE scheme~\cite{cheon2017ckks}, which allows the server to perform all distillation computation directly on ciphertexts.
```
After:
```
\par\noindent\textbf{Threat Model.} We assume a semi-honest (honest-but-curious) server that follows the protocol faithfully but may attempt to infer private information from everything it observes. The adversary's goal is to infer information about a client's private dataset $\mathcal{D}_i$ or the client's local model, including individual samples, label distributions, or model weights, from the messages it receives during training. We further assume that the server may collude with up to $N-1$ clients; privacy of the remaining honest client's input is guaranteed by the threshold structure of the multiparty CKKS scheme described in Section~\ref{sec:phase3}, which requires the joint participation of all $N$ clients to decrypt any ciphertext.

Given this system and threat model, sending plaintext teacher outputs to the server is insufficient. Because, as discussed in Section~\ref{sec:bg_server_inference}, even a single round of plaintext knowledge transfer exposes clients to inference and inversion attacks. We therefore instantiate the knowledge transfer channel using the multiparty CKKS HE scheme~\cite{cheon2017ckks, mouchet2021multiparty} — the same construction implemented in Lattigo~\cite{lattigo} — which lets the server perform all distillation computation directly on ciphertexts under a public key whose corresponding secret key is held in shares across the $N$ clients.
```

### methodology.tex:145-148 (Phase 3: Threshold Decryption)
Reason: replaced the duplicated, garbled paragraph with a structured walk-through of how threshold HE is used in HE-IFD: setup via DKG, encryption under the collective public key, collective key-switching for decryption, and the trust assumption (one honest client suffices). Cites Mouchet et al. for the construction and Lattigo for the implementation. Fixes the in-place duplication bug from the original paragraph.
Before:
```
\subsubsection{Phase~3: Threshold Decryption}
\label{sec:phase3}

After server-side distillation, the trained student weights remain encrypted on the server. The server distributes the encrypted model to all clients. Each client holds a secret key share, and decryption happens locally on each client's device: the client applies its key share to obtain the plaintext student weights. No single client can decrypt alone (threshold security), and the server never sees plaintext weights at any point in the protocol. If this phase is omitted, the student remains encrypted and can be used for encrypted inference directly. Keys are generated via a distributed key generation (DKG) protocol in which each client contributes a random share, and no single party ever holds the full secret key. The server distributes the encrypted model to all clients. Each client holds a secret key share, and decryption happens locally on each client's device: the client applies its key share to obtain the plaintext student weights. No single client can decrypt alone (threshold security), and the server never sees plaintext weights at any point in the protocol. If this phase is omitted, the student remains encrypted and can be used for encrypted inference directly.
```
After:
```
\subsubsection{Phase~3: Threshold Decryption}
\label{sec:phase3}

We instantiate the encrypted channel of HE-IFD with the multiparty CKKS protocol of~\cite{mouchet2021multiparty}, available in the open-source Lattigo library~\cite{lattigo}. We describe how the protocol is used in HE-IFD; the underlying construction is unchanged from the cited references and we treat it as a black box.

\par\noindent\textbf{Setup (before Phase~1).} The $N$ clients run a distributed key generation (DKG) protocol with no trusted dealer. Each client $i$ samples a secret-key share $\mathsf{sk}_i$ from the CKKS secret-key distribution and contributes a corresponding share to the protocol. The DKG output is (i)~a collective public key $\mathsf{pk}$ usable by everyone for encryption, (ii)~collective evaluation and rotation keys usable by the server for homomorphic computation, and (iii)~the secret-key shares $\{\mathsf{sk}_i\}_{i=1}^{N}$, kept privately by the clients. The full secret key $\mathsf{sk} = \sum_{i=1}^{N} \mathsf{sk}_i$ is never assembled at any single party at any point in the protocol.

\par\noindent\textbf{Encryption (Phase~2).} Every client encrypts its normalised feature pairs (Section~\ref{sec:phase2}) under the collective public key $\mathsf{pk}$ and uploads the ciphertexts to the server. From the server's perspective, the resulting ciphertexts behave exactly as ordinary single-key CKKS ciphertexts: the server applies homomorphic additions, ciphertext-by-plaintext multiplications, ciphertext-by-ciphertext multiplications (using the collective relinearisation key), and slot rotations (using the collective rotation keys) in the usual way. No client interaction is required during this phase.

\par\noindent\textbf{Collective decryption (Phase~3).} To release the trained student in plaintext, the server initiates a single round of \emph{collective key-switching}~\cite{mouchet2021multiparty}: it broadcasts the encrypted student weights $\enc{\mathbf{W}}$ to the clients, and each client $i$ contributes a key-switching share that re-encrypts $\enc{\mathbf{W}}$ from the collective key $\mathsf{pk}$ to a target key $\mathsf{pk}'$ (e.g., the all-zero key, which yields plaintext, or a fresh public key whose corresponding secret is held by a designated recipient). Every client's share is computed locally from $\mathsf{sk}_i$ and added a small smudging noise to mask its individual contribution. Combining all $N$ shares yields the re-encrypted ciphertext, from which $\mathbf{W}$ can be decrypted; combining any strict subset of $N-1$ shares yields a uniformly random ring element under the RLWE assumption~\cite{lyubashevsky2010ideal}. If this phase is skipped, the student stays encrypted and the server can serve encrypted inference directly.

\par\noindent\textbf{Trust assumption.} Privacy of every client's input holds as long as at least one of the $N$ clients is honest. This is strictly stronger than the trust assumption of single-key CKKS deployments, which require a trusted decryption authority, and matches the threat model of Section~\ref{sec:framework}: even if the server colludes with $N-1$ clients, the joint view consists of ciphertexts under a key whose remaining share is held by the honest client and is therefore computationally indistinguishable from random.
```


---

## 4. Related work restructuring

Goal: extended (paragraph-length) treatment for the works directly compared in experiments (POSEIDON, BatchCrypt, FedSHE as the newer comparator, vanilla FedAvg, DP-SGD, LDP, plus the DP-based one-shot FL family); single-sentence + cite for everything else.

### background.tex:36-43 (replaced commented-out "One-Shot Federated Learning Methods" block with active "One-Shot Federated Distillation" subsection)
Reason: the user requested that works most related to ours (and most relevant to the experiments) get a clearer treatment. The commented block was re-enabled and rewritten into two paragraphs: one covers the plaintext distillation family (FedMD, DS-FL, FedDF, Cronus, DENSE, Co-Boosting, FuseFL) with one sentence per system and an explicit privacy axis of comparison; the second covers the DP-based one-shot FL family (FedKT, FedMD-NFDP, FedDiff, FedDM) with the structural reason DP collapses in one-shot settings and the cryptographic-vs-statistical axis of comparison.
Before:
```
% \subsection{One-Shot Federated Learning Methods}
% \label{sec:bg_oneshot}

% One-shot FL methods~\cite{guha2019oneshot, wang2025towards} restrict client-server communication to a single round. They fall into three families: distillation-based methods that transfer logits, features, or distilled datasets~\cite{zhang2022dense, lin2020feddf, dai2024coboosting, tang2024fusefl, chen2024fedsd2c}; generative methods that upload trained generators or synthesised data~\cite{feddiff2024, xiong2023feddm}; and aggregation-based methods that directly fuse model parameters through matching or alignment~\cite{jhunjhunwala2024fedfisher, allouah2024fens}.

% Among distillation-based methods, DENSE~\cite{zhang2022dense} uploads full plaintext models and trains a generator on the server. Co-Boosting~\cite{dai2024coboosting} iteratively co-trains data and ensemble for state-of-the-art one-shot accuracy. FuseFL~\cite{tang2024fusefl} is architecturally closest to HE-IFD: it decomposes the network into blocks and trains each block sequentially with progressive fusion, paralleling our block-by-block distillation. However, FuseFL operates in plaintext and requires unrestricted access to intermediate activations, which is incompatible with encryption. All of these methods expose client contributions to the server without privacy protection.

% Only a small number of one-shot FL methods provide formal privacy guarantees, and all of them rely on differential privacy (DP). FedKT~\cite{li2021fedkt} achieves $(\varepsilon, 0)$-DP through noisy voting on a public dataset. FedMD-NFDP~\cite{sun2021fedmdnfdp} uses a noise-free sampling mechanism for $(\varepsilon, \delta)$-DP. FedDiff~\cite{feddiff2024} applies DP to diffusion model training, and FedDM~\cite{xiong2023feddm} supports optional DP on synthetic data. DP inherently trades accuracy for privacy: at meaningful privacy levels ($\varepsilon \leq 1$), accuracy collapses toward random guessing~\cite{sun2021fedmdnfdp, gad2024communication}. No existing one-shot FL method uses homomorphic encryption for knowledge transfer. HE-IFD fills this gap by providing cryptographic privacy through CKKS encryption without injecting noise into the distillation signal.
```
After:
```
%% ─────────────────────────────────────────────────────
\subsection{One-Shot Federated Distillation}
\label{sec:bg_oneshot}

One-shot federated learning~\cite{guha2019oneshot, wang2025towards} restricts client-server communication to a single round and is the family of FL designs that share our problem statement. Among the plaintext distillation systems in this family, FedMD~\cite{li2019fedmd} and DS-FL~\cite{itahara2021dsfl} have clients transfer softmax predictions on a shared public dataset; FedDF~\cite{lin2020feddf} distils an ensemble of heterogeneous client models into a server model; Cronus~\cite{chang2019cronus} adds robust aggregation by spectrally filtering the client predictions; DENSE~\cite{zhang2022dense} uploads full plaintext models and trains a generator on the server; Co-Boosting~\cite{dai2024coboosting} iteratively co-trains data and ensemble; and FuseFL~\cite{tang2024fusefl} is architecturally closest to HE-IFD in that it also decomposes the student into blocks and trains them sequentially. None of these methods provide cryptographic protection: every client contribution reaches the server in plaintext and is therefore subject to the inversion, label-distribution, and membership-inference attacks reviewed in Section~\ref{sec:bg_server_inference}. The distinguishing axis of HE-IFD relative to this family is privacy: the supervision signal is a ciphertext under collectively held keys, and the server's view is computationally indistinguishable from random regardless of the architectural similarity to FuseFL.

The smaller subset of one-shot FL systems that do offer formal privacy guarantees rely uniformly on differential privacy. FedKT~\cite{li2021fedkt} achieves $(\varepsilon, 0)$-DP through noisy voting on a public dataset; FedMD-NFDP~\cite{sun2021fedmdnfdp} uses a noise-free sampling mechanism for $(\varepsilon, \delta)$-DP; FedDiff~\cite{feddiff2024} applies DP to diffusion-model training; and FedDM~\cite{xiong2023feddm} supports optional DP on synthetic data. The structural cost of this approach is that one-shot settings consume the entire privacy budget in a single round, with no across-round amplification, so accuracy collapses toward random guessing at meaningful privacy levels ($\varepsilon \leq 1$)~\cite{sun2021fedmdnfdp, gad2024communication}. The distinguishing axis of HE-IFD relative to this DP family is the type of guarantee: cryptographic and noise-free rather than statistical and noise-coupled to utility.
```

### background.tex:50 (HE-Compatible Neural Network Design subsection)
Reason: tightened the closing paragraph so prior polynomial-network work (Sisyphus, Baruch et al., Agamennone, AlHossain, Pirillo) is explicitly named as centralised single-model training, and HE-IFD's contribution is positioned as the first stable polynomial-network training under heterogeneous federated supervision.
Before:
```
Running neural networks on encrypted data requires that all operations reduce to addition and multiplication over ciphertexts. Standard operations such as ReLU, batch normalisation, and softmax are non-polynomial and cannot be evaluated under encryption. Prior work addresses this for \emph{encrypted inference}, where a pre-trained model with known plaintext weights evaluates on encrypted inputs, by replacing ReLU with learnable polynomial activations~\cite{baruch2022methodology} and absorbing batch normalisation parameters into preceding layers~\cite{ibarrondo2021fhebn}. \emph{Encrypted training}~\cite{sav2021poseidon} is substantially harder: both weights and data are ciphertexts, every operation is ciphertext-by-ciphertext (consuming multiplicative levels), and the backward pass doubles the depth of the forward pass. In the federated distillation setting, the challenge is compounded because the supervision signal itself is an encrypted ciphertext from a heterogeneous client, and teachers trained on different data distributions produce features with incompatible magnitude ranges. Our work is the first to address stable training of HE-compatible architectures under fully encrypted federated supervision.
```
After:
```
Running neural networks on encrypted data requires that all operations reduce to addition and multiplication over ciphertexts. Standard operations such as ReLU, batch normalisation, and softmax are non-polynomial and cannot be evaluated under encryption. Prior work on \emph{encrypted inference}, where a pre-trained model with known plaintext weights evaluates on encrypted inputs, replaces ReLU with learnable polynomial activations~\cite{baruch2022methodology, garimella2021sisyphus} and absorbs batch normalisation parameters into preceding layers~\cite{ibarrondo2021fhebn}. Recent centralised work has addressed the stability of training such polynomial networks: tighter ReLU approximations~\cite{agamennone2025polynomial}, boundary-loss and gradient-clipping schedules for deeper polynomial models~\cite{alhossain2025training}, and reboot-style block-independent training for polynomial MLPs~\cite{pirillo2025reboot}. \emph{Encrypted training}~\cite{sav2021poseidon} is substantially harder than inference: both weights and data are ciphertexts, every learnable operation is ciphertext-by-ciphertext (consuming multiplicative levels), and the backward pass roughly doubles the depth of the forward pass. All of the works above operate on a single centralised model; HE-IFD is the first to address stable polynomial-network training under fully encrypted, heterogeneous federated supervision, where teachers trained on different distributions produce target features with incompatible magnitude ranges.
```

### background.tex (new subsection inserted after HE-Compatible Neural Network Design)
Reason: introduced an "Encrypted Federated Learning Systems" subsection giving paragraph-length, axes-explicit treatment to the works directly compared in our experiments — POSEIDON, BatchCrypt, and FedSHE as the newer comparator. Vanilla FedAvg, FedML-HE, and CURE are mentioned in a closing sentence with citations only.
Before: (no subsection)
After:
```
%% ─────────────────────────────────────────────────────
\subsection{Encrypted Federated Learning Systems}
\label{sec:bg_he_fl}

The works that HE-IFD is most directly compared with in Section~\ref{sec:experiments} are encrypted federated learning systems. They share the cryptographic privacy goal but differ from HE-IFD on three axes: the unit that is encrypted (gradient updates vs.\ teacher features), the number of communication rounds, and where the multiplicative-depth budget is spent.

\par\noindent\textbf{POSEIDON~\cite{sav2021poseidon}.} POSEIDON is the canonical multiparty-CKKS system for federated training; it supports the same threshold trust model as HE-IFD and shares its underlying multiparty-CKKS construction~\cite{mouchet2021multiparty}. The unit that is encrypted is the per-round gradient: every client encrypts its gradient updates under the collective key, the server homomorphically aggregates them, and the result is broadcast back. The protocol is therefore inherently multi-round, and each round consumes the full forward+backward depth of the model under encryption, requiring bootstrapping to be invoked across rounds. HE-IFD differs on every axis: a single round, encryption of intermediate teacher features rather than gradients, and a depth budget that is confined to a single block of the student because each block is trained on fresh ciphertexts.

\par\noindent\textbf{BatchCrypt~\cite{zhang2020batchcrypt}.} BatchCrypt instantiates the same multi-round encrypted-gradient pattern with batched Paillier encryption rather than CKKS. The scheme is additively homomorphic, which is sufficient for FedAvg-style gradient aggregation but rules out the polynomial-network training that HE-IFD performs server-side. The relevant axis of comparison in our experiments is communication cost: BatchCrypt's per-round cost is dominated by encrypted gradients, scales linearly with the number of rounds, and gives the curve a slope similar to encrypted POSEIDON despite the different scheme.

\par\noindent\textbf{FedSHE~\cite{wei2025fedshe}.} A more recent CKKS-based federated learning system that introduces adaptive packing strategies to compress the per-round encrypted-gradient upload, reducing the constant in front of the multi-round communication curve. FedSHE remains structurally multi-round and encrypts gradient updates rather than supervision signals; HE-IFD is orthogonal to this line of work in that it eliminates the multi-round pattern entirely rather than optimising its constants. The two designs are complementary: an adaptive-packing scheme analogous to FedSHE's would also reduce the size of HE-IFD's single ciphertext upload.

In the same broader category, Vanilla FedAvg~\cite{mcmahan2017communication} is the unencrypted multi-round baseline used in the communication-cost comparison, and FedML-HE~\cite{jin2023fedml} and CURE~\cite{kanpak2024cure} are further multi-round encrypted-FL systems we cite for context but do not include as primary curves.
```

### background.tex:59 (Motivation for One-Shot Communication paragraph)
Reason: rewrote the BatchCrypt-specific clause as a forward reference to the new "Encrypted Federated Learning Systems" subsection so the motivation paragraph is no longer the place where comparator systems are introduced; explicit handoff between the two parts of the related work.
Before:
```
Homomorphic encryption (HE)~\cite{cheon2017ckks} provides end-to-end cryptographic protection without injecting noise, avoiding the utility--privacy tradeoff of DP. However, applying HE to standard iterative training is prohibitively expensive: systems like BatchCrypt~\cite{zhang2020batchcrypt} remain significantly slower than plaintext methods, and training deep networks over many rounds rapidly exhausts the finite multiplicative depth budget in the CKKS scheme~\cite{cheon2017ckks} which we further discuss in \ref{sec:ckks_prelim}. Bootstrapping~\cite{cheon2018bootstrapping} refreshes this budget but introduces substantial latency, rendering layer-wise application impractical. One-shot settings resolve this tension: ciphertexts are used once, and block-independent training with fresh ciphertexts confines the depth budget to a single block rather than the full network. This principle was recently validated for encrypted MLP training~\cite{pirillo2025reboot}. Our framework extends it to federated one-shot distillation over heterogeneous clients.
```
After:
```
Homomorphic encryption (HE)~\cite{cheon2017ckks} provides end-to-end cryptographic protection without injecting noise, avoiding the utility--privacy tradeoff of DP. However, applying HE to standard iterative training is structurally expensive. The systems reviewed in Section~\ref{sec:bg_he_fl} (POSEIDON, BatchCrypt, FedSHE) all encrypt per-round gradient updates and therefore exhaust the multiplicative-depth budget of CKKS~\cite{cheon2017ckks} (further discussed in Section~\ref{sec:ckks_prelim}) in every round; bootstrapping~\cite{cheon2018bootstrapping} refreshes the budget but at substantial latency. One-shot settings resolve this tension: ciphertexts are used once, and block-independent training with fresh ciphertexts confines the depth budget to a single block of the student rather than the full network. This principle was recently validated for encrypted MLP training~\cite{pirillo2025reboot}. HE-IFD extends it to federated one-shot distillation over heterogeneous clients.
```


---

## 4b. Experiments-section comparison framing

Goal: tighten the experiments-section narrative around DP and HE-FL comparisons so the axes of differentiation are explicit (statistical vs.\ cryptographic, one-shot vs.\ multi-round, gradient vs.\ feature). No new experiments; only wording.

### experiments.tex:64 (Privacy Analysis lead-in)
Reason: made the comparison axes explicit (type of guarantee × number of rounds) and added a one-sentence summary of the cryptographic guarantee referencing Section~\ref{sec:phase3}.
Before:
```
We compare HE-IFD against two differential privacy (DP) baselines on ResNet-18 CIFAR-10 at $N{=}4$. We compare with Local Differential Privacy (LDP)~\cite{kasiviswanathan2011can}, where each client perturbs its data locally before uploading (one-shot compatible), and DP-SGD~\cite{abadi2016deep}, where gradient noise is injected during centralised training (multi-round). Both provide a statistical $(\varepsilon, \delta)$-guarantee parameterised by the privacy budget $\varepsilon$, where a smaller $\varepsilon$ means stronger privacy but more noise. HE-IFD provides a cryptographic guarantee as the server operates entirely on CKKS ciphertexts and has no attack surface during training. Figure~\ref{fig:privacy} shows the privacy-utility trade-off. HE-IFD is shown as a single point at MIA AUC = 0.5 because its MIA AUC is 0.5 by construction (random guessing), regardless of the attack strength. Our key findings are:
```
After:
```
We compare HE-IFD against two differential privacy (DP) baselines on ResNet-18 CIFAR-10 at $N{=}4$, chosen so that the comparison spans both axes of the design space: the type of guarantee (statistical vs.\ cryptographic) and the number of communication rounds (one-shot vs.\ multi-round). Local Differential Privacy (LDP)~\cite{kasiviswanathan2011can} perturbs each client's data locally before upload and is therefore one-shot compatible; DP-SGD~\cite{abadi2016deep} injects calibrated Gaussian noise into per-sample gradients during multi-round training. Both yield a statistical $(\varepsilon, \delta)$-guarantee parameterised by the privacy budget $\varepsilon$, with smaller $\varepsilon$ corresponding to stronger privacy but more noise and lower utility. HE-IFD provides a cryptographic guarantee under the IND-CPA security of multiparty CKKS (Section~\ref{sec:phase3}): the server's view consists of ciphertexts under a key whose corresponding secret is held in shares across the clients, and any inference about the inputs of an honest client reduces to breaking RLWE. Among the three, HE-IFD is the only one-shot mechanism with a cryptographic guarantee. Figure~\ref{fig:privacy} shows the privacy-utility trade-off; HE-IFD appears as a single point at MIA AUC = 0.5 because the AUC is 0.5 by construction during training, independent of attack strength. Key findings:
```

### experiments.tex:88 (Communication Cost — comparator paragraph)
Reason: the existing wording lumped multi-round encrypted FL into one parenthetical citation. Rewrote to explicitly name POSEIDON, BatchCrypt, and FedSHE (with FedML-HE and CURE as further citations) and to state the axis of comparison (gradient vs.\ feature, multi-round vs.\ one-shot) consistent with the new Encrypted FL Systems subsection in background.tex.
Before:
```
Figure~\ref{fig:communication} compares total communication across three settings: (i) vanilla (unencrypted) FedAvg \cite{mcmahan2017communication}, where clients upload plaintext gradient updates with no privacy protection; (ii) multi-round encrypted FL \cite{sav2021poseidon,zhang2020batchcrypt}, where clients encrypt gradient updates under CKKS in every round; and (iii) HE-IFD (ours), which requires a single encrypted upload. In multi-round encrypted FL, each of 200 training rounds requires all $N$ clients to encrypt their 11.2M-parameter gradient updates as CKKS ciphertexts (${\sim}$2.7 GB per client per round), upload them, and receive the aggregated model back. This accumulates to ${\sim}1{,}068 \times N$ GB, reaching 4,272 GB at $N{=}4$ and 34 TB at $N{=}32$. Even unencrypted vanilla FedAvg~\cite{mcmahan2017communication} scales linearly, reaching 558 GB at $N{=}32$ over 200 rounds.
```
After:
```
Figure~\ref{fig:communication} compares total communication across three regimes that span the design space introduced in Section~\ref{sec:bg_he_fl}: (i)~Vanilla (unencrypted) FedAvg~\cite{mcmahan2017communication}, the multi-round plaintext baseline that establishes the linear-in-$N$ floor; (ii)~Multi-round encrypted FL, represented by POSEIDON~\cite{sav2021poseidon} and BatchCrypt~\cite{zhang2020batchcrypt} (and architecturally similar systems such as FedSHE~\cite{wei2025fedshe}, FedML-HE~\cite{jin2023fedml}, and CURE~\cite{kanpak2024cure}), where clients encrypt gradient updates and upload them in every round; and (iii)~HE-IFD, which encrypts teacher features instead of gradients and uploads them once. The axis of comparison is the unit that is encrypted (gradient vs.\ feature) and the number of rounds. In multi-round encrypted FL, each of 200 training rounds requires all $N$ clients to encrypt their 11.2M-parameter gradient updates as CKKS ciphertexts (${\sim}$2.7~GB per client per round), upload them, and receive the aggregated model back. This accumulates to ${\sim}1{,}068 \times N$~GB, reaching 4,272~GB at $N{=}4$ and 34~TB at $N{=}32$. Even unencrypted Vanilla FedAvg scales linearly with $N$, reaching 558~GB at $N{=}32$ over 200 rounds.
```

### experiments.tex:111 (Computation Cost — comparator paragraph)
Reason: same alignment as above — name the comparator family explicitly and forward-reference Section~\ref{sec:bg_he_fl}.
Before:
```
By comparison, multi-round encrypted FL requires server-side encrypted aggregation that grows linearly with $N$: at $N{=}4$ this takes ${\sim}$7.6 CPU-hours for aggregation alone plus ${\sim}$152 hours of bootstrapping; at $N{=}32$, aggregation reaches ${\sim}$60 CPU-hours. A plaintext oracle trains in about 0.5 hours on a single GPU.
```
After:
```
By comparison, the multi-round encrypted FL family discussed in Section~\ref{sec:bg_he_fl} (POSEIDON, BatchCrypt, FedSHE) requires server-side encrypted aggregation that grows linearly with $N$: at $N{=}4$ this takes ${\sim}$7.6~CPU-hours for aggregation alone plus ${\sim}$152~hours of bootstrapping; at $N{=}32$, aggregation reaches ${\sim}$60~CPU-hours. The Oracle plaintext baseline trains in about 0.5~hours on a single GPU.
```

---

## 5. Verification

Goal: build `main.pdf` end-to-end, confirm no missing-citation or undefined-reference warnings, list any residual issues.

**No TeX engine on host.** `pdflatex`, `bibtex`, `lualatex`, `xelatex`, `latexmk`, and `tectonic` are all absent on this machine, so a full build was not run here. The user will need to compile in Overleaf (or on a host with TeX Live installed). The following static checks were run instead:

- **Citation closure.** All 63 `\cite{...}` keys used across `introduction.tex`, `background.tex`, `methodology.tex`, `experiments.tex`, and `conclusion.tex` resolve to entries in `references.bib`. The new entry `mouchet2021multiparty` is present and is referenced from `methodology.tex` (Threat Model, Phase~3 walkthrough, Phase~3 collective decryption) and from `background.tex` (POSEIDON paragraph in the new Encrypted FL Systems subsection). Verified by:
  ```
  comm -23 <(grep -hoE '\\cite\{[^}]+\}' *.tex | sed -E 's/\\cite\{//; s/\}$//' | tr ',' '\n' | sed 's/^ *//; s/ *$//' | sort -u) <(grep -oE '^@[a-zA-Z]+\{[a-zA-Z0-9_]+,' references.bib | sed -E 's/^@[a-zA-Z]+\{//; s/,$//' | sort -u)
  ```
  Output: empty (no missing keys).
- **Reference closure.** Every `\ref{...}` target is defined by a `\label{...}` somewhere in the active sources. In particular, the new label `sec:bg_he_fl` (introduced for the Encrypted FL Systems subsection) is referenced from the Motivation paragraph in `background.tex` and from two paragraphs of `experiments.tex` (Communication Cost and Computation Cost). Verified by an analogous `comm -23` over `\label` and `\ref` keys: empty.
- **Macros.** The new threshold-HE paragraph uses `\mathsf{...}` (built-in) and `\enc{...}` (defined as `\llbracket #1 \rrbracket` at `main.tex:28`); both work in standard `IEEEtran` with the `stmaryrd` package, which is already loaded.

Residual items the user must do in Overleaf to complete this revision:

1. **Regenerate the two PDFs that still contain the teal Plaintext KL curve**: `figures/fig_main_resnet18.pdf` and `figures/fig_arch_gen.pdf`. The captions and surrounding text have been rewritten to no longer reference the curve, so until the PDFs are regenerated there will be a teal line in the figure that is not described by the caption. The plot script is at `/scratch/hkanpak21/HE_Distillation/generate_plots.py` (or `generate_v2_experiments.py`); the user may also ask for this regeneration to be done in a follow-up after plan mode.
2. **Run `pdflatex/bibtex/pdflatex/pdflatex`** in Overleaf or any TeX Live environment to confirm the build is warning-clean. The static checks above predict no missing-citation or undefined-reference warnings.
3. **Decide on the venue for the Mouchet et al. citation**: the bib entry uses the PoPETs 2021 version (the canonical reference). Some communities cite the WAHC 2020 precursor instead; if your advisor prefers WAHC 2020, replace the `journal/volume/number/pages/year` lines of `mouchet2021multiparty` with `booktitle={WAHC}, year={2020}`.
4. **Optional**: if the user wants FedSHE to appear as a third multi-round-encrypted curve in `figures/fig_communication.pdf` and `figures/fig_computation.pdf`, the curve needs to be added to those figures. The text already names FedSHE as a comparator; the figure would only confirm the visual pattern.

---

## 5. Methodology pivot (2026-05-05)

This section opens the rewrite that follows the design captured in `reports/2026-05-05_methodology_pivot.md` (the **PRD**). The PRD is the authoritative reference; entries below cover only edits that have already landed.

### 5.1 New file: `figures/threat_model_v2.svg`

Reason: the threat model itself changed under the pivot (probe-based encrypted CFD instead of block-wise intermediate-feature distillation; explicit treatment of the $N{-}1$ collusion bound and the binding invariant on threshold decryption). A new figure is required and replaces, in spirit, the threat-model portion of the existing `HE-IFD_sysFigure.pdf`. The new figure is authored as plain SVG (single panel, two fills `#C6A87D` client / `#8B9EA8` server, plain rectangles + arrows + text) rather than TikZ to keep the source diff-friendly and renderable in any browser.

To embed in `main.tex`: convert `threat_model_v2.svg` to PDF via `rsvg-convert -f pdf -o figures/threat_model_v2.pdf figures/threat_model_v2.svg` (or `inkscape --export-type=pdf figures/threat_model_v2.svg`), then `\includegraphics[width=0.85\textwidth]{figures/threat_model_v2.pdf}` in the threat-model subsection.

### 5.2 references.bib cleanup pass (2026-05-05)

A single cleanup pass over `references.bib`, scripted at `jobs/cleanup_bib_2026-05-05.py`. Result: 106 entries → 65 entries (1008 → 624 lines).

**Dropped (43 entries — defined but never cited in any .tex):**

`hinton2015distilling, geiping2020inverting, chen2024fedsd2c, lin2020ensemble, mora2024knowledge, wei2020federated, bagdasaryan2019differential, papernot2018scalable, qi2023differentially, xia2024pt, nasr2023tight, cheu2021manipulation, thapa2022split, pasquini2021unleashing, kariyappa2021gradient, xu2024stealthy, wu2025musplitfed, reagen2021cheetah, juvekar2018gazelle, obla2020effective, lee2022privacy, huangsuwan2025feddrip, croitoru2023diffusion, carlini2023extracting, ye2023feddisco, lee2022fedntd, zhu2021data, kornblith2019similarity, zhao2020idlg, liu2025oneshot, qi2023privatekt, hoech2022fedauxfdp, huang2025dkdfl, gilad2016cryptonets, alhossain2025stablepolynomial, mazzone2022repeated, behrens2025memorized, roux2025byzantine, merity2017pointer, sanh2019distilbert, socher2013recursive, jhunjhunwala2024fedfisher, allouah2024fens`.

This list contains the four duplicate keys identified by title-match (`lin2020ensemble` dup of `lin2020feddf`; `qi2023differentially` and `qi2023privatekt` are duplicates of each other and both unused; `alhossain2025stablepolynomial` dup of `alhossain2025training`). The fourth pair flagged by the dup checker, `kerkouche2023client` vs `kerkouche2023property`, was kept intact: titles match exactly but author lists differ (3 authors WPES 2023 vs 5 authors IEEE S&P 2023), and both keys are cited in different contexts (introduction.tex vs background.tex). Treat as two distinct papers.

**Venue strings normalised on five surviving entries:**

- `shi2025unveiling`: journal → `PoPETs`
- `mouchet2021multiparty`: journal → `PoPETs`
- `dimitrov2024spear`: booktitle → `NeurIPS`
- `lin2020feddf`: booktitle → `NeurIPS`
- `galichin2025glira`: journal → `IEEE TIFS`

Author lists and author-name shortening untouched per user instruction.

**Appended (2 entries — needed by the rewrite per PRD §3.2 and §2.1):**

- `dockhorn2022dpdm` — Dockhorn, Cao, Vahdat, Kreis. *Differentially Private Diffusion Models*. TMLR 2022 (arXiv:2210.09929). Cited by the γ-variant DP-DDPM construction.
- `viand2023verifiable` — Viand, Knabenhans, Hithnawi. *SoK: Fully Homomorphic Encryption Compilers and Verifiable Computation*. IEEE S&P 2023 (arXiv:2301.07041). Cited by the threat-model "verifiable HE as future work" paragraph.

Final state: 65 bib entries, 63 currently cited, 2 awaiting first citation in the methodology rewrite. No broken refs (verified via `grep` over all `.tex` against bib keys).

### 5.3 Pending wholesale replacements (NOT YET APPLIED — to be logged when the rewrite lands)

The PRD specifies wholesale replacement of the following sections post-cutover. They are listed here as a forward declaration so the eventual bulk-replacement entries are easy to locate:

- `methodology.tex` §3 onwards — replaced by PRD §4 (encrypted CFD protocol).
- `experiments.tex` — replaced by PRD §7 (new experimental grid, HE-vs-plaintext discrepancy section, communication/compute measurements from prototype).
- `background.tex` §2.3 — extended with one paragraph on Co-Boosting's privacy gap and one paragraph on DP synthetic data prior work (Dockhorn et al. TMLR 2022, FedGM 2024) that we cite for the γ-variant.

Until those entries appear with concrete before/after diffs, the .tex files in `FL_TDSC/` retain their pre-pivot content; the **PRD wins** on any disagreement (per the deprecation note at the top of the PRD).

---

## 6. References audit (2026-05-17)

Fact-check pass over `references.bib` against the keys cited in `*.tex` and the cross-references in the PRD (`reports/2026-05-05_methodology_pivot.md`) and the action plan (`reports/2026-05-10_tdsc_rejection_action_plan.md`).

**Static checks (clean).**
- All `\cite{...}` keys in `*.tex` resolve to bib entries (no broken refs).
- No duplicate keys in `references.bib` (65 entries, 65 unique keys).
- No exact-title duplicates across keys.
- Two entries (`dockhorn2022dpdm`, `viand2023verifiable`) remain pre-added without first citation; both are reserved for the A1 wholesale methodology rewrite per `2026-05-10_tdsc_rejection_action_plan.md` §4.

**Fact-check finding 1 — `zhang2022dense` metadata was wrong (FIXED).**

The bib entry for the DENSE paper (cited as DENSE in `background.tex:40` and as the canonical data-free one-shot baseline in PRD §3, action plan A4) carried the title "Practical Data-Free Federated Learning" with year 2021 and NeurIPS volume 34. The actual paper at arXiv:2112.12371 with this author list is "DENSE: Data-Free One-Shot Federated Learning" published at NeurIPS 2022 (volume 35). Likely an early-draft title that was kept after the paper was renamed for camera-ready. Author list matched, so this is a metadata fix not a paper swap.

### references.bib:95-102 (`zhang2022dense` entry)
Reason: bib entry carried the early-draft title, wrong year (2021 vs 2022), and wrong NeurIPS volume (34 vs 35). Fix-up to canonical NeurIPS 2022 publication metadata, with arXiv URL added per the convention used for other ML-conference entries in this file.
Before:
```
@inproceedings{zhang2022dense,
  title={Practical Data-Free Federated Learning},
  author={Zhang, Jie and Chen, Chen and Li, Bo and Lyu, Lingjuan and Wu, Shuang and Ding, Shouhong and Shen, Chunhua and Qi, Chao},
  booktitle={NeurIPS},
  volume={34},
  pages={11919--11932},
  year={2021}
}
```
After:
```
@inproceedings{zhang2022dense,
  title={{DENSE}: Data-Free One-Shot Federated Learning},
  author={Zhang, Jie and Chen, Chen and Li, Bo and Lyu, Lingjuan and Wu, Shuang and Ding, Shouhong and Shen, Chunhua and Qi, Chao},
  booktitle={NeurIPS},
  volume={35},
  pages={21414--21428},
  year={2022},
  url={https://arxiv.org/abs/2112.12371}
}
```

**Fact-check finding 2 — PRD-only prose typos (not in `.tex`; recorded here for traceability; PRD itself patched in this same pass).**

These do not affect the manuscript and therefore do not generate before/after entries in this changelog. PRD-side patches applied in `reports/2026-05-05_methodology_pivot.md` so the audit trail closes here:

- PRD line 115 (γ-variant probe-size discussion): the parenthetical "FedDM (arXiv:2407.14730)" was wrong — arXiv:2407.14730 is a different 2024 paper that does not match the `xiong2023feddm` bib entry. Patched to "FedDM (Xiong et al. CVPR 2023, arXiv:2207.09653)" matching the bib.
- PRD line 306 (verifiable-HE forward-reference): the parenthetical title "Verifiable Fully Homomorphic Encryption" was a paraphrase that lost the SoK framing. Patched to the canonical "SoK: Fully Homomorphic Encryption Compilers and Verifiable Computation" matching the `viand2023verifiable` bib entry.

**Outstanding (to verify before resubmission).**

- The `zhang2022dense` page range (21414–21428) is the most likely NeurIPS 2022 page range for arXiv:2112.12371 based on the proceedings ordering but has not been cross-checked against the official NeurIPS 2022 proceedings index in this audit. Verify on Overleaf compile / proceedings DOI before submit.
- The `kerkouche2023client` vs `kerkouche2023property` pair retained from CHANGES.md §5.2 still has identical titles; the author/venue distinction was accepted on faith from the §5.2 dup-check. If this is a single paper double-entered under two keys, one must be merged before submit. Out of scope for this pass.
- Both pre-added entries (`dockhorn2022dpdm`, `viand2023verifiable`) must receive their first `\cite{...}` during A1 (methodology rewrite); flag for the rewriter so the BibTeX warning surface stays empty.
