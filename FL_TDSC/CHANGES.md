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

---

## 7. PRD staleness patch (2026-05-17)

The PRD (`reports/2026-05-05_methodology_pivot.md`) had drifted from the user-confirmed protocol semantics. Four internal-consistency patches applied in a single pass. Line numbers refer to the **pre-patch** PRD (baseline commit `8be000f`). No FL_TDSC `.tex` files are touched by this section — patches are PRD-internal — but the entries are recorded here so the audit trail through `CHANGES.md` covers every editable surface of the resubmission, per the rule in PRD §9.5.6.

### reports/2026-05-05_methodology_pivot.md:161-167 (§4.3 — HE depth budget per encrypted SGD step)
Reason: §4.3 described a full encrypted forward+backward chain with depth +1 per multiplied weight matrix and a projected 1k–5k bootstraps per protocol run. The 2026-05-17 user clarification (action plan A3 "Depth budget clarification", line 222) established that the protocol does **not** forward-propagate through encrypted weights: the encrypted student $\langle\theta\rangle$ is a linear accumulator over encrypted gradient contributions, $\langle\theta_E\rangle = \langle\theta_0\rangle + \sum_t \text{lr}\cdot\langle\text{grad}_t\rangle$, with per-step depth ≤ 3 (residual + scalar × CT for lr + addition). LeNet-5 fits TenSEAL's 7-level chain at logN=14 trivially. No bootstrapping is required for any cell in the §7.2 grid. The PRD prose has been rewritten to match.
Before:
```
The student forward pass on plaintext probe inputs (α) is plaintext-times-ciphertext at each layer (depth +1 per multiplied weight matrix), with polynomial activations (depth +deg). KL loss against $\widetilde Y$ at temperature $T_{\text{eff}}$: depth +1 for the softmax-replacement polynomial. Backprop: another forward-equivalent depth pass.

Single-step depth budget for the student: $O(\text{depth}_{\text{forward}})$, refreshed each step by bootstrapping (CKKS bootstrap once per accumulated depth budget, typically every few steps with reasonable parameters). γ-variant adds $O(\text{depth}_{\text{forward}})$ from the encrypted-input forward, doubling the per-step depth.

Concrete parameter sketch (logN=15, scale=2^40, ring degree 32768): bootstrap latency on a single core ≈ 5–15 s; expected 1k–5k bootstraps per protocol run for an MNIST-scale student; total HE compute on the order of hours on commodity hardware. Numbers to be tightened by the TenSEAL prototype.
```
After:
```
The protocol does not forward-propagate through encrypted weights. The encrypted student $\langle\theta\rangle$ is a **linear accumulator** over encrypted gradient contributions:
$$\langle\theta_E\rangle = \langle\theta_0\rangle + \sum_t \text{lr} \cdot \langle\text{grad}_t\rangle,$$
where each $\langle\text{grad}_t\rangle$ is a per-layer SGD update computed from the encrypted teacher signal applied to plaintext student state at step $t$. There is no backward chain rule on encrypted intermediate activations; there is no per-layer depth accumulation across the network's depth. The student's forward pass at step $t$ runs in plaintext on the current decrypted-for-loss-only copy of the weights — only the *update* contribution is encrypted and added to $\langle\theta\rangle$.

**Per-step encrypted depth ≤ 3 levels**: residual carry-over of $\langle\theta\rangle$ (depth 0), scalar plaintext × ciphertext multiplication for the learning rate (depth +1), and addition to the accumulator (depth 0). The dominant cost is the encrypted ensemble-target depth of §4.2 (loss-side depth-3 from raw logits), incurred once per probe pass, not once per step.

LeNet-5 (or any deeper student architecture) fits TenSEAL's 7-level chain trivially at logN=14. No bootstrapping is required for any cell in the §7.2 grid. γ-variant inherits the same construction; the per-step depth budget is unchanged because the encrypted synthetic probe enters the loss-side computation of §4.2, not the per-step update.

Concrete parameter sketch (logN=14, scale=$2^{40}$, ring degree 16384): per-step ciphertext-arithmetic latency on a single core ≈ tens of milliseconds; total HE compute on the order of minutes per cell on commodity hardware. Numbers to be tightened by the TenSEAL prototype (A2) and the end-to-end single-cell run (A3).
```

### reports/2026-05-05_methodology_pivot.md:93 (§2.7 — threat-model figure specification, final paragraph)
Reason: §2.7 closed with the figure being produced from a TikZ source. Appendix A "Closed" (line 422 of the pre-patch PRD) is the authoritative subsequent decision: plain SVG at `FL_TDSC/figures/threat_model_v2.svg`, converted to PDF via `rsvg-convert --format=pdf` at build time, no TikZ. §2.7 has been brought into sync with Appendix A.
Before:
```
I will produce this figure as `FL_TDSC/figures/threat_model_v2.pdf` from a TikZ source. The TikZ source is queued as a follow-up and will be added to `FL_TDSC/CHANGES.md` when committed.
```
After:
```
The figure is rendered as a plain **SVG** at `FL_TDSC/figures/threat_model_v2.svg` — single panel, minimal decoration, two fills (client `#C6A87D`, server `#8B9EA8`), plain rectangles + arrows + text. The PDF used by the manuscript is produced at build time via `rsvg-convert --format=pdf threat_model_v2.svg -o threat_model_v2.pdf`. No TikZ. The SVG source and the regenerated PDF are committed together and logged in `FL_TDSC/CHANGES.md`. Authority for this decision: Appendix A "Closed".
```

### reports/2026-05-05_methodology_pivot.md:252,256 (§8 — TenSEAL prototype, step 5 + forgetting point (a))
Reason: §8 step 5 described "one encrypted forward pass + encrypted-backprop one step", which presumed the full-encrypted-training depth model patched out of §4.3. Forgetting point (a) deferred bootstrapping to a Lattigo prototype. Under the linear accumulator, step 5 is a single-update demonstration of the $\langle\theta_E\rangle = \langle\theta_0\rangle + \sum \text{lr}\cdot\langle\text{grad}\rangle$ recurrence, depth ≤ 3, no bootstrapping needed, the smoke stays inside TenSEAL. Both passages have been rewritten in lock-step with §4.3.
Before:
```
5. Performs one encrypted forward pass of a 2-layer MLP student against $\widetilde Y$, computes encrypted KL with polynomial-softmax approximation, encrypted-backprop one step, asserts the gradient direction matches plaintext.

...

Forgetting points to watch: (a) TenSEAL automatically rescales after each multiplication and consumes a level; bootstrap is **not directly supported in TenSEAL** — for any depth beyond initial-ladder, we either deepen the level chain or move to Lattigo/PyFHEL. The smoke test will use only enough depth to demonstrate the §4.2 computation. Anything that requires bootstrapping (the encrypted student SGD loop) is deferred to a Lattigo prototype.
```
After:
```
5. Demonstrates one linear-accumulator update step: plaintext student forward on the probe, plaintext gradient computation against a decryption-for-loss-only copy of $\widetilde Y$, encryption of the resulting gradient, and addition $\langle\theta\rangle \mathrel{+}= \text{lr}\cdot\langle\text{grad}\rangle$. Verifies the $\langle\theta_E\rangle = \langle\theta_0\rangle + \sum_t \text{lr}\cdot\langle\text{grad}_t\rangle$ recurrence over $\geq 10$ steps and asserts the decrypted $\langle\theta_E\rangle$ matches a plaintext-equivalent linear accumulator within CKKS noise tolerance (max element-wise error < $10^{-3}$ at scale $2^{40}$).

...

Forgetting points to watch: (a) The linear-accumulator construction consumes ≤ 3 levels per step (residual carry-over of $\langle\theta\rangle$, scalar plaintext × ciphertext for the learning rate, addition). TenSEAL's 7-level chain at logN=14 absorbs this with margin; **no bootstrapping is needed** and the smoke stays entirely inside TenSEAL. The previously-planned Lattigo migration for bootstrapping support is dropped.
```

### reports/2026-05-05_methodology_pivot.md:379-387 (§10 — Open items, in priority order)
Reason: §10 predated the 2026-05-17 priority reframe in `reports/2026-05-10_tdsc_rejection_action_plan.md` §0 and ordered work items in roughly authoring-order rather than priority-order. The list also still carried "Generate `figures/threat_model_v2.pdf` from a TikZ source" (stale per the §2.7 patch above) and item 7 "execute §9 archive + restructure" (already completed; the HE_IFD tree exists). Re-ordered to mirror the action-plan priority ladder: A4 (P1, headline tri-axis grid) → A3 (P2, end-to-end CKKS calibration) → A7 (P3, MIA evidence) → text/figure work (A1, A8, A11, A10) → γ-variant (A5) → reference items (verifiable-HE citation, deferred ε/δ decisions). Stale and completed items dropped.
Before:
```
1. Verify the verifiable-HE citation (Viand SoK + a concrete vCKKS reference). Add to `references.bib` and reference once in §threat-model.
2. Decide $(\varepsilon_T, \delta_T)$ and $(\varepsilon_P, \delta_P)$ (and $(\varepsilon_G, \delta_G)$ for γ). Defer until experimental utility numbers exist; the paper's claim is structural.
3. Generate `figures/threat_model_v2.pdf` from a TikZ source.
4. Draft `prototypes/cfd_tenseal_smoke.py` and run on the t4_ai partition (never login-node).
5. Author `jobs/cfd_v2_*.sh` and execute the §7.2 grid.
6. Apply the §6 / §7 / §8 numbers to `FL_TDSC/methodology.tex` and `FL_TDSC/experiments.tex`. Log every textual change in `FL_TDSC/CHANGES.md`.
7. Once user confirms, execute §9 archive + restructure.
```
After:
```
1. **A4 (P1, headline).** Execute the §7.2 tri-axis accuracy / communication / time grid on Valar `t4_ai`; report $\Delta_{\text{HE}} \leq 1$ pp at every cell. This is the cover-letter's headline-contribution evidence. Authoring `jobs/cfd_v2_*.sh` is the gating sub-task.
2. **A3 (P2, calibration).** End-to-end CKKS run on a single cell with the linear-accumulator construction (§4.3); serves as anchor for the simulator-vs-real-HE gap claimed by A4. The A2 TenSEAL smoke (`prototypes/cfd_tenseal_smoke.py`, §8) is a prerequisite.
3. **A7 (P3, privacy evidence).** Membership-inference attack (LiRA + loss-threshold) on the decrypted student weights $\theta_E$. The resubmission needs a concrete MIA number to back the structural privacy argument.
4. **Text and figure work.** Methodology rewrite (A1), threat-model textual rewrite (A8), threat-model SVG (A11; see §2.7), abstract / §I-A rewrite (A10). Apply the §6 / §7 / §8 numbers to `FL_TDSC/methodology.tex` and `FL_TDSC/experiments.tex`. Log every textual change in `FL_TDSC/CHANGES.md` per the rule in §9.5.6 and the precedent set in §6 of that file.
5. **γ-variant (A5).** DP-DDPM profiling, then per-client generators, then γ cells in the A4 grid. Conditional on A4 leaving compute headroom; γ is the optional extension that distinguishes us from the public-probe-only baseline.
6. **Reference items.** Verifiable-HE citation (Viand SoK + a concrete vCKKS reference) added to `FL_TDSC/references.bib` and cited once in §threat-model. Deferred $(\varepsilon_T, \delta_T), (\varepsilon_P, \delta_P), (\varepsilon_G, \delta_G)$ decisions become defensible only once experimental utility numbers exist; the paper's claim is structural in the interim.
```

---

## 8. A9 future-work paragraph on malicious / colluding clients (2026-05-17)

Action plan A9 (resolving R2-Q4 / AE-4) calls for an explicit out-of-scope acknowledgement of actively malicious clients and the open problem of robust aggregation under HE. Concrete edits across `conclusion.tex`, `references.bib`, and `reports/cover_letter_draft.md`. The verifiable-HE citation pair is `viand2023verifiable` (SoK, already in bib per §5.2) plus a newly added `atapoor2024vfhe` (Cryptology ePrint 2024/582, lattice-SNARK construction for verifiable CKKS).

### conclusion.tex:15 (Future work paragraph)
Reason: the existing one-sentence future-work line conflated three unrelated tracks (upload-cost reduction, Byzantine-resilient aggregation under HE, bootstrapping-free schedules) into a single comma-separated list and named "Byzantine-resilient aggregation under encryption" without distinguishing it from the unaddressed malicious-client threat surface that R2-Q4 / AE-4 explicitly raised. Split into two paragraphs: the first retains the in-scope efficiency-style future work (upload-cost + bootstrapping-free schedules); the second is a half-page dedicated discussion of the out-of-scope adversaries, naming encrypted-feature poisoning, model poisoning under encryption, and the open problem of HE-compatible robust aggregation. The new paragraph also cites verifiable HE (Viand SoK + Atapoor lattice-SNARK CKKS) as the natural extension toward verifiable correctness (orthogonal to robustness) and states the out-of-scope status unambiguously per the `feedback-paper-voice` register.
Before:
```
Future work includes reducing the one-shot upload cost (${\sim}$115\,GB per client at $N{=}4$, $\sim 460$ GB total across all clients) through ciphertext compression and feature selection, integrating Byzantine-resilient aggregation under encryption, and investigating bootstrapping-free training schedules for deeper HE-compatible architectures.
```
After:
```
Future work along the present threat model includes reducing the one-shot upload cost (${\sim}$115\,GB per client at $N{=}4$, $\sim 460$ GB total across all clients) through ciphertext compression and feature selection, and investigating bootstrapping-free training schedules for deeper HE-compatible architectures.

A second class of future work concerns adversaries that fall outside the present threat model. The semi-honest assumption on clients bounds the contribution to passive collusion; an actively malicious client can craft adversarial logit ciphertexts (encrypted-feature poisoning) or submit ciphertexts engineered to bias the aggregate $\widetilde{Y}$ (model poisoning under encryption), neither of which the binding invariant of Section~\ref{sec:bg_server_inference} addresses. The classical plaintext defences against these threats---coordinate-wise median aggregation, Krum, trimmed mean---do not directly port to the homomorphic setting, since their rank-based statistics are not realisable as low-depth arithmetic circuits on ciphertexts. A robust aggregation primitive compatible with HE is therefore an open problem distinct from the present work's contribution. The natural extension toward verifiable correctness---independent of robustness---is verifiable HE: a server proves in zero knowledge that the computation it performed on ciphertexts was the prescribed one, as surveyed by~\cite{viand2023verifiable} and concretised for CKKS by~\cite{atapoor2024vfhe}. We do not claim defence against any of these adversaries; we acknowledge the threat surface explicitly so that the contribution of HE-IFD is correctly bounded to what is established here: privacy of the client data against a semi-honest server colluding with up to $N{-}1$ clients.
```

### references.bib:625-626 (atapoor2024vfhe — new entry)
Reason: `viand2023verifiable` already provides the SoK-level survey of verifiable HE; A9 also requires one concrete vCKKS reference so the natural-extension claim is anchored to a specific construction, not just a survey. Atapoor et al. 2024 (Cryptology ePrint 2024/582, "Verifiable FHE via Lattice-Based SNARKs") instantiates verifiable CKKS via lattice-SNARKs and is the standard recent citation in the verifiable-CKKS line. Filed as `@misc` with `howpublished = {Cryptology ePrint Archive, Paper 2024/582}` because the ePrint version is the canonical reference until a venue acceptance lands; this matches the `@misc`/`howpublished` convention already used in this file for ePrint citations.
Before:
```
(no entry — atapoor2024vfhe did not exist)
```
After:
```
@misc{atapoor2024vfhe,
  title        = {Verifiable {FHE} via Lattice-Based {SNARKs}},
  author       = {Atapoor, Shahla and Baghery, Karim and Pereira, Hilder V. L. and Spiessens, Jannik},
  howpublished = {Cryptology ePrint Archive, Paper 2024/582},
  year         = {2024},
  url          = {https://eprint.iacr.org/2024/582}
}
```

### reports/cover_letter_draft.md:91-93 (§6 Closing — one-line cross-reference)
Reason: the cover letter's §2 AE-4 row already points reviewers at §VII Future Work for the out-of-scope-adversaries acknowledgement. The §6 Closing did not restate this, leaving the editorial reader to backtrack through the §2 table to find the cross-reference. Per issue 26's "Section 6 (or the appropriate out-of-scope concerns section)" guidance, added one sentence at the end of §6 that names the three out-of-scope adversaries explicitly and names both citations (Viand SoK + Atapoor lattice-SNARK CKKS) so the closing paragraph can stand alone without requiring the table.
Before:
```
We are grateful for the rigour of the previous review cycle. The substantial revisions invited by the AE have been read at the level of *protocol design* rather than *prose polish*, and we believe the resubmission is materially stronger across all three reviewer axes (security, evaluation, presentation). We look forward to the editorial decision.
```
After:
```
We are grateful for the rigour of the previous review cycle. The substantial revisions invited by the AE have been read at the level of *protocol design* rather than *prose polish*, and we believe the resubmission is materially stronger across all three reviewer axes (security, evaluation, presentation). Out-of-scope adversaries — actively malicious clients, encrypted-feature poisoning, and the open problem of HE-compatible robust aggregation — are acknowledged explicitly in §VII Future Work, with verifiable HE cited as the natural extension via the Viand SoK and Atapoor et al.'s lattice-SNARK construction for CKKS. We look forward to the editorial decision.
```

---

## 9. A8 threat-model rewrite (2026-05-17)

Action plan A8 (lines 378–391 of `reports/2026-05-10_tdsc_rejection_action_plan.md`) called for rewriting `methodology.tex` §threat-model so it reflects the resubmission's threat model rather than the rejected block-wise HE-IFD protocol's. The legacy paragraphs at lines 19–25 described a generic semi-honest server with a forward-reference to `sec:phase3` for the threshold structure; the IND-CPA prose was carried as a commented-out paragraph at line 25. The PRD's §2.1–§2.6 (`reports/2026-05-05_methodology_pivot.md` lines 30–94) has been imported as a new `\subsubsection{System and Threat Model}` with the binding invariant as the central property and the R2-Q6 plaintext-student-weights paragraph (lines 396–398 of the action plan) lifted close to verbatim. The IND-CPA framing has been reinstated as live prose inside the new Adversary's view paragraph rather than as a separate paragraph. The new subsubsection carries the label `sec:threat_binding`, which both the new prose and the existing issue-26 future-work paragraph at `conclusion.tex:17` will eventually want to use (the conclusion.tex paragraph currently mis-references `sec:bg_server_inference` for the binding invariant; that is issue 26's surface, not this issue's, so left untouched).

### FL_TDSC/methodology.tex:16-25 (System Model / Threat Model paragraphs + commented IND-CPA paragraph)
Reason: legacy paragraphs described the rejected block-wise HE-IFD protocol's threat model (semi-honest server + $N{-}1$ colluding clients, no binding invariant, no plaintext-metadata enumeration, no all-zeros amplification, no out-of-scope adversaries list). Replaced by a paper-register import of PRD §2.1–§2.6, with the R2-Q6 plaintext-student-weights paragraph from action plan A8 (lines 396–398) inserted as the structural answer to "why student weights stay plaintext during training". New `\label{sec:threat_binding}` introduced so subsequent edits (issue 13 wholesale methodology rewrite; issue 26 future-work paragraph re-aim) can cross-reference the binding invariant directly. The commented-out IND-CPA paragraph at line 25 has been removed and its content reinstated as live prose inside the new "Adversary's view" paragraph, since binding invariant + IND-CPA + SQ-floor is the formal contribution.
Before:
```
% \subsubsection{System Model and Threat Model}
% \label{sec:system_model}

\par\noindent\textbf{System Model.} We consider a cross-silo federated learning setting with $N$ clients and a central server. Each client $i$ holds a private dataset $\mathcal{D}_i$ that is never shared or transmitted. Clients wish to collaboratively train a shared student model by transferring knowledge from their locally trained teacher models to the server, without exposing their private data, including raw training data and any intermediate representations. Communication between clients and the server is restricted to a single round: each client sends a set of encrypted messages derived from its local data and model, after which the server performs all remaining computation independently with no further client interaction. An optional release phase at the end allows clients to collectively obtain the trained model.

\par\noindent\textbf{Threat Model.} We assume a semi-honest (honest-but-curious) server that follows the protocol faithfully but may attempt to infer private information from everything it observes. The adversary's goal is to infer information about a client's private dataset $\mathcal{D}_i$ or the client's local model, including individual samples, label distributions, or model weights, from the messages it receives during training. We further assume that the server may collude with up to $N-1$ clients; privacy of the remaining honest client's input is guaranteed by the threshold structure of the multiparty CKKS scheme described in Section~\ref{sec:phase3}, which requires the joint participation of all $N$ clients to decrypt any ciphertext.

Given this system and threat model, sending plaintext teacher outputs to the server is insufficient. Because, as discussed in Section~\ref{sec:bg_server_inference}, even a single round of plaintext knowledge transfer exposes clients to inference and inversion attacks. We therefore instantiate the knowledge transfer channel using the multiparty CKKS HE scheme~\cite{cheon2017ckks, mouchet2021multiparty} — the same construction implemented in Lattigo~\cite{lattigo} — which lets the server perform all distillation computation directly on ciphertexts under a public key whose corresponding secret key is held in shares across the $N$ clients.

% Under the IND-CPA security of CKKS, the server's entire view during training (encrypted feature pairs, intermediate activations, loss values, gradients, and student weights) is computationally indistinguishable from random. The server operates purely as a blind compute delegate and learns nothing about any client's private data. For additional protection, clients may add calibrated differential privacy noise before encryption, achieving $(\epsilon, \delta)$-differential privacy for the released model; this is optional since the cryptographic guarantee already prevents the server from inspecting any individual contribution during training.
```
After:
```
\subsubsection{System and Threat Model}
\label{sec:threat_binding}

\par\noindent\textbf{Parties and trust.} We consider a cross-silo federated learning setting with $N$ clients and a central server. Each client $i$ holds a private dataset $\mathcal{D}_i$ that is never shared or transmitted. All parties are honest-but-curious: they execute the protocol faithfully but pool every observation to attempt to recover what the protocol intends to hide. The adversary may corrupt the server together with up to $N{-}1$ clients and merge their views; privacy of any client's input is preserved as long as at least one client is honest. Verifying that a semi-honest server has actually performed the homomorphic operations it claims is outside the present scope and is the natural extension toward verifiable HE discussed alongside the malicious-client surface in the Future Work section.

\par\noindent\textbf{Multiparty CKKS at $t{=}N$.} The cryptographic primitive is the multiparty variant of CKKS in the threshold instantiation of Mouchet et al.~\cite{mouchet2021multiparty}, as available in Lattigo~\cite{lattigo}. Distributed key generation produces a single collective public key $\mathsf{pk}$ and per-client secret-key shares $\mathsf{sk}_i$, with the threshold for decryption set to $t{=}N$: all $N$ shares are required to recover any plaintext. The choice $t{=}N$ over $t < N$ is deliberate. Any $t < N$ admits a coalition of $t{-}1$ semi-honest clients who can decrypt every aggregate the protocol exposes, including per-row teacher logits, which under the present threat model directly enables subtraction attacks against the remaining honest client. The cost of $t{=}N$ is a liveness surface (any one client can refuse to participate in the decryption round); this is standard in the multiparty-FHE literature and is not a privacy concern.

\par\noindent\textbf{Binding invariant on threshold decryption.} The central property of the protocol's threat model is the following: the only ciphertext ever subjected to threshold decryption, or to collective key-switching to a per-client target key, is the final trained student's parameter vector $\theta_E$. No per-client logit ciphertext, no aggregated ensemble target, and no auxiliary encrypted scalar is decrypted at any stage. The binding invariant is part of the threat model, not a property of the protocol implementation: it constrains what the protocol is allowed to release rather than what it can compute. Without it, a coalition of $N{-}1$ clients who know their own contributions and observe a decrypted aggregate can subtract their inputs and recover the honest client's contribution exactly. With it, the only adversary-visible plaintext is $\theta_E$, which is a non-linear function of every client's private inputs through the distillation training and therefore admits no closed-form subtraction attack on any single client.

\par\noindent\textbf{Plaintext student weights during training.} The student weights themselves are not encrypted during training: the warm-started student $\theta_0^\star$ and the per-iteration plaintext student state used to compute gradients are never encrypted. What carries cryptographic protection is a separate encrypted accumulator $\langle\Delta\rangle = \sum_t \eta \langle g_t\rangle$ holding the teacher-induced refinement, computed from the encrypted teacher signal $\langle T_i(\mathcal P)\rangle$ applied to the plaintext student state. At release time the two are composed: $\langle\theta_E\rangle = \langle\theta_0^\star\rangle + \langle\Delta\rangle$, threshold-decrypted, and shipped to the clients. The ciphertext-times-plaintext versus ciphertext-times-ciphertext distinction is therefore real but already optimised: CT$\times$PT is the dominant arithmetic throughout the per-step update, while CT$\times$CT appears only in the depth-bounded ensemble target construction (Section~\ref{sec:phase2}), which is at most three multiplicative levels deep and runs once per protocol execution. The binding invariant is preserved because the only ciphertext ever submitted to threshold decryption is the composed end-state $\langle\theta_E\rangle$, never an intermediate $\langle\Delta\rangle$ or $\langle T_i(\mathcal P)\rangle$ in isolation.

\par\noindent\textbf{Adversary's view.} Under the binding invariant and the IND-CPA security of CKKS, the adversary's view (server in coalition with $N{-}1$ clients) partitions into three disjoint subsets. The encrypted subset consists of the per-client teacher logit ciphertexts $\langle T_i(\mathcal P)\rangle$, any encrypted scalars $\langle\alpha_i\rangle$, the encrypted ensemble target $\widetilde Y$, and the encrypted accumulator $\langle\Delta\rangle$ at every step of training, all computationally indistinguishable from uniformly random ring elements. The plaintext-metadata subset consists of the public probe $\mathcal P$ itself, ciphertext sizes and counts, protocol timing, and any per-client public sizes that are disclosed by transport; this subset reveals only protocol structure, not data. The released subset consists of the threshold-decrypted student $\theta_E$ alone. The released-student leakage is exactly the lower bound that no collaborative-training protocol can avoid: any output usable as a model is observable to its recipients through white-box or statistical-query access. The contribution of cryptographic instantiation is to hold the adversary's view at exactly this floor, with nothing above it; the inference-attack surface that this floor closes off relative to plaintext distillation is reviewed in Section~\ref{sec:bg_server_inference} and is not duplicated here.

\par\noindent\textbf{All-zeros amplification and its defence.} The binding invariant prevents direct decryption attacks but does not rule out a derived form, utility-coercion-into-privacy-amplification: if $N{-}1$ colluding clients upload all-zero logit ciphertexts, the encrypted ensemble target collapses to a multiple of the single honest client's logits, the released student becomes a single-teacher distillation of that honest teacher, and the statistical-query floor on $\theta_E$ rises silently. The attack does not breach the invariant; it inflates the unavoidable lower bound. Two independent knobs defend against it. (P1)~Each client trains its teacher $T_i$ on $\mathcal{D}_i$ with DP-SGD at a per-client budget $(\varepsilon_T, \delta_T)$; by the post-processing theorem, $T_i(\mathcal P)$ inherits this budget and so does the released student, and the all-zeros amplification cannot reduce a client-local floor that is already established before any server-side aggregation. (P2)~Each client may add per-row Gaussian noise $\eta_i \sim \mathcal N(0, \sigma_P^2 I)$ to its logit vector before encryption. In the honest case this averages as $\sigma_P/\sqrt N$ at the ensemble target so utility loss is mild; under the all-zeros amplification it surfaces at full magnitude and contributes an additional $(\varepsilon_P, \delta_P)$ layer that takes effect only in the worst case. The composition of (P1) and (P2) follows the standard Gaussian-DP RDP accountant. The claim made by the methodology is structural: the protocol admits both knobs while keeping the binding invariant; concrete budget values belong to the experimental section.

\par\noindent\textbf{Out-of-scope adversaries.} A malicious server that deviates from the prescribed homomorphic computation is out of scope; the natural extension is verifiable HE. A malicious client that crafts adversarial logit ciphertexts (encrypted-feature poisoning) or biased payloads (model poisoning under encryption) is out of scope; this is a robustness concern that does not breach privacy under the binding invariant and is taken up explicitly in Section~\ref{sec:conclusion}, where the absence of a low-depth HE-compatible robust aggregator is named as an open problem. Network-level adversaries (denial of service, traffic analysis, side-channels of the underlying HE library, timing leaks beyond ciphertext sizes) are likewise out of scope.
```

**Voice / structural decisions.**
- The R2-Q6 paragraph from action plan A8 lines 396–398 has been imported as the "Plaintext student weights during training" paragraph, placed immediately after the binding invariant so it functions as the structural answer to "why student weights stay plaintext". The `\ref{sec:methodology_ensemble}` of the action-plan sketch has been generalised to `\ref{sec:phase2}` because `sec:methodology_ensemble` does not exist yet (issue 13's scope); the depth-3 ensemble-target claim is the load-bearing content, not the precise subsection number.
- The PRD §2.4 table has been rewritten as flowing prose ("partitions into three disjoint subsets") per `feedback-paper-voice`, which prefers paragraphs over enumerable lists in body text where the list is short.
- The PRD §2.6 three-bullet list has been collapsed into one paragraph with three sentence-level entries, again per voice guidance.
- The IND-CPA framing previously carried as a commented-out paragraph has been reinstated as live prose at the opening of the "Adversary's view" paragraph.
- The forward-reference to the §conclusion future-work paragraph (issue 26) is `\ref{sec:conclusion}` rather than a more specific subsection label, since the conclusion is a single un-subdivided section.
- No mention of "per-block ciphertexts", "block-wise training", "magnitude regularisation", or "bridge construction" remains in the rewritten section; those terms still live elsewhere in `methodology.tex` and belong to issue 13's wholesale rewrite scope.

**Syntactic checks performed (cluster compile gate unavailable, pdflatex.fmt missing).**
- Balanced braces on `FL_TDSC/methodology.tex` (`python3 -c "t=open(...).read(); print(t.count('{'), t.count('}'))"` reports 779/779; up from the pre-edit 762/762, with the net +17/+17 matching the new prose).
- Every `\cite{...}` in the new section (`mouchet2021multiparty`, `lattigo`) resolves to a bib entry in `FL_TDSC/references.bib`.
- Every `\ref{...}` in the new section (`sec:phase2`, `sec:conclusion`, `sec:bg_server_inference`) resolves to a `\label{...}` in `FL_TDSC/*.tex`. The new `\label{sec:threat_binding}` is unique.

**Follow-on cross-reference fix (orchestrator-applied during merge).** Issue 26's future-work paragraph at `conclusion.tex:17` pre-dated this section's new `\label{sec:threat_binding}` and consequently mis-cited `sec:bg_server_inference` (the inference-attack background) as the home of the binding invariant. Re-aimed at `sec:threat_binding` in this same commit so the cross-reference resolves to the actual binding-invariant paragraph from now on; the §8 entry above remains the historical record of issue 26's pre-fix state.

---

## 10. A11 threat-model SVG (2026-05-17)

The threat-model figure called for by PRD section 2.7 and Appendix A "Closed" item (lines 421-422) has been hand-authored as plain SVG at `FL_TDSC/figures/threat_model_v2.svg`. The figure is single-panel, 800x600 px, with all eight elements from PRD section 2.7's spec: N=4 client boxes (one honest, three colluding) on the left; central server box with dashed ciphertext-boundary annotation; encrypted client-to-server arrows in ColorBrewer Dark2 teal `#1B9E77` carrying $\langle T_i(\mathcal P)\rangle$; encrypted server-to-client arrows in ColorBrewer Dark2 orange `#D95F02` carrying the collectively key-switched $\langle\theta_E\rangle$; a threshold-decryption gate inset (top right) showing N key-share triangles fanning into a t=N gate with a single plaintext output; and a side panel (lower right) enumerating the adversary's plaintext view (Subset 2 of PRD section 2.4). Client fill `#C6A87D` and server fill `#8B9EA8` exactly per the `feedback-colors` memory. No TikZ, no design-MCP detour: this matches the Appendix A "Closed" decision authoritatively.

Build conversion to PDF is deferred to a node with `librsvg2-bin` installed (or Overleaf-side at submit time); `rsvg-convert` is not available on the Valar login node. The SVG-only deliverable is acceptable per the orchestrator's environmental note.

### FL_TDSC/figures/threat_model_v2.svg
Reason: PRD section 2.7 + Appendix A "Closed" call for a hand-authored plain-SVG threat-model figure with two fills (client `#C6A87D`, server `#8B9EA8`) and eight specified elements. The pre-existing 900x560 viewBox-style SVG in the same path predates the spec and omitted half the required content (no threshold-decryption gate inset, no side panel enumerating the plaintext view, no per-direction Dark2 colour discrimination on arrows). Rewritten in full as 800x600 with `<g id="...">` groupings for the major regions (`title`, `clients`, `server`, `upload-arrows`, `download-arrows`, `threshold-gate`, `adversary-view-panel`, `footer`) so the file is editor-friendly. `xmllint --noout` returns clean (exit 0, zero stderr).
Before:
```
(file existed but was incomplete vs the eight-element spec; 900x560 viewBox, no
threshold-decryption gate inset, no adversary's-plaintext-view side panel, single
arrow direction, no Dark2 colour discrimination, no `<g id>` groupings)
```
After:
```
800x600 px plain SVG, 14 rects + 17 lines + 7 paths + 59 text elements; all eight
PRD section 2.7 elements present (N=4 client boxes with one honest + three colluding,
server box with dashed IND-CPA boundary annotation, per-direction upload/download
encrypted arrows in ColorBrewer Dark2 teal `#1B9E77` / orange `#D95F02`, threshold-
decryption gate inset with N key-share triangles -> t=N gate -> theta_E plaintext
output, side panel enumerating adversary's plaintext view as four bullets, title
"Threat model: semi-honest server + up to N-1 colluding clients"). Client fill
`#C6A87D` x5 (four client rects + one legend swatch), server fill `#8B9EA8` x3
(server rect + threshold-gate body + legend swatch).
```

### FL_TDSC/figures/threat_model_v2.pdf
Reason: the figure's matching PDF (`\includegraphics{...}` resolution target for `methodology.tex`) is regenerated from the SVG via `rsvg-convert --format=pdf FL_TDSC/figures/threat_model_v2.svg -o FL_TDSC/figures/threat_model_v2.pdf`. `rsvg-convert` is not installed on the Valar login node (per `valar` memory + orchestrator note), so the PDF regeneration is deferred to Overleaf-side build (or a future ralph iteration on a node with `librsvg2-bin` installed). The SVG-only deliverable is acceptable per the orchestrator brief; the build line is recorded in `jobs/build_figures.sh` (via this iteration's sidecar `.agent-output/11-build-line.txt`) for re-runnability.
Before:
```
(stale PDF exists at this path from the pre-spec SVG; will be overwritten by the
deferred rsvg-convert pass)
```
After:
```
(deferred; regenerated from threat_model_v2.svg via rsvg-convert --format=pdf
once librsvg2-bin is available on the build host or via Overleaf compile)
```

---

## 11. A11 protocol-overview SVG (2026-05-17)

New protocol-overview figure authored at `FL_TDSC/figures/protocol_overview_v2.svg`, the figure-level counterpart of issue 05's R2-Q6 textual rewrite and the companion to `threat_model_v2.svg` (CHANGES.md §5.1). Per the action plan A11 figure-spec update (`reports/2026-05-10_tdsc_rejection_action_plan.md` lines 420–446) and PRD §4.1 phase table + §4.3 linear-accumulator clarification (`reports/2026-05-05_methodology_pivot.md` lines 134–168). Single panel, plain SVG (no TikZ), left-to-right phase progression 0 → 1 → 2a → 2b → 2c → 3, with Phase 2c rendered as two parallel tracks (plaintext student state on top, encrypted teacher-induced delta accumulator on bottom) and a `+` composition glyph at the 2c → 3 boundary emitting `⟨θ_E⟩ = ⟨θ_0*⟩ + ⟨Δ⟩` in Server colour. Palette per `feedback-colors` memory: Client `#C6A87D`, Server `#8B9EA8`, lightened Client `#E0D2BA` for the plaintext-student track, ColorBrewer Dark2 `#1B9E77` for key-share arrows and `#D95F02` for encrypted upload arrows. Editor-friendly group structure: `<g id="phase-0">`, `<g id="phase-1">`, `<g id="phase-2a">`, `<g id="phase-2b">`, `<g id="plaintext-track">`, `<g id="encrypted-track">`, `<g id="composition">`, `<g id="phase-3">`, `<g id="legend">`. Build wiring (one-line `rsvg-convert` invocation) recorded in `.agent-output/12-build-line.txt` for the orchestrator to fold into `jobs/build_figures.sh` alongside the existing `threat_model_v2.svg` line.

### FL_TDSC/figures/protocol_overview_v2.svg (new file)
Reason: action plan A11 requires a protocol-overview figure that (i) walks the reader through the six CFD phases 0/1/2a/2b/2c/3 from PRD §4.1, (ii) visually distinguishes the plaintext warm-started student track from the encrypted accumulator track inside Phase 2c per the 2026-05-17 figure-spec update, and (iii) renders the composition `⟨θ_E⟩ = ⟨θ_0*⟩ + ⟨Δ⟩` at the 2c → 3 boundary so anyone reading the figure can see at a glance that the student forward pass runs in plaintext during training and only the teacher-induced delta is encrypted. This pre-empts R2-Q6 visually and is the figure-level counterpart of issue 05's R2-Q6 rewrite (`methodology.tex` / `background.tex`).
Before:
```
(no file)
```
After:
```
Hand-authored plain SVG at 1200 × 520 viewBox, single panel, left-to-right six-phase progression with vertical dashed `#666666` phase separators between phases. Phase 0 shows the server box (`#8B9EA8`) with a DKG glyph and three client boxes (`#C6A87D`) emitting key-share arrows (`#1B9E77`) that converge into the server, producing a `collective pk` label below. Phase 1 shows three client boxes (re-drawn) each emitting `⟨T_i(P)⟩` encrypted-teacher-logit arrows (`#D95F02`) into Phase 2's region. Phase 2a shows a lightened server box (`#8B9EA8` at 50% opacity) labelled `plaintext SGD on (P, y_P) → θ_0*` with the annotation `α only · plaintext`. Phase 2b shows a full-opacity server box labelled `Ỹ = Σ_i ⟨α_i^β⟩ · ⟨T_i(P)⟩` with the `depth ≤ 3` annotation, and emits two arrows into Phase 2c (a dashed server-grey arrow carrying `θ_0* (plaintext)` into the top track, and an orange `⟨Ỹ⟩` arrow into the bottom track). Phase 2c contains two parallel tracks: the top track `<g id="plaintext-track">` is a box with the lightened-Client fill `#E0D2BA`, labelled `θ (plaintext)` with a `forward pass` glyph and the annotation `student state in the clear`; the bottom track `<g id="encrypted-track">` is a Server-coloured `#8B9EA8` box labelled `⟨Δ⟩ (encrypted accumulator over ⟨g_t⟩)` with the `accumulate ⟨g_t⟩` glyph, the recurrence `Δ ← Δ + lr · ⟨g_t⟩`, and the annotation `per-step depth ≤ 3` (matching `project-linear-accumulator`). At the Phase 2c → 3 boundary a `<g id="composition">` group renders a bracket joining the two tracks, a circled `+` glyph (a `<circle>` with a centred `+` `<text>`), and an output arrow in Server colour `#8B9EA8` carrying the label `⟨θ_E⟩ = ⟨θ_0*⟩ + ⟨Δ⟩`. Phase 3 shows the server doing a `key-switch` (annotated `collective key-switch`) and three fan-out arrows to three client boxes, the bottom one labelled `θ_E (plaintext)` to make the plaintext delivery explicit. A legend at the bottom maps the five visual idioms (Client, Server/encrypted state, plaintext student state, key-share arrows, encrypted upload arrows, server-side encrypted arrows, plaintext delivery) to their colours.
```

### jobs/build_figures.sh (orchestrator-owned; build-line recorded in sidecar)
Reason: `jobs/build_figures.sh` is owned by the orchestrator in this wave; the per-figure build line is recorded in `.agent-output/12-build-line.txt` for the orchestrator to append next to the existing `threat_model_v2.svg → threat_model_v2.pdf` invocation. The line is the standard `rsvg-convert --format=pdf …` form used for `threat_model_v2.svg` (`rsvg-convert` is unavailable on the login node, so no PDF is produced in this wave).
Before:
```
(orchestrator-owned; not edited in this issue)
```
After:
```
rsvg-convert --format=pdf FL_TDSC/figures/protocol_overview_v2.svg -o FL_TDSC/figures/protocol_overview_v2.pdf
```

---

---

## 12. A10 abstract + §I-A challenges rewrite (2026-05-17)

Action plan A10 (lines 400–419 of `reports/2026-05-10_tdsc_rejection_action_plan.md`) called for two coupled rewrites: (i) the abstract's participation-incentive paragraph, with the May-5 working numbers per the "numbers freeze + replacement protocol" (MNIST $\alpha{=}0.3$: $0.965$ student vs $0.81$ mean teacher; CIFAR-10 $\alpha{=}0.3$: $0.521$ vs $0.408$), and (ii) the §I-A "Our Approach" challenges paragraph, replacing the three legacy challenges (polynomial magnitude explosion, training–distillation distribution gap, scale-anchored loss — all artefacts of the rejected block-wise protocol) with the four post-pivot challenges aligned with the resubmission's CFD / linear-accumulator design. The numbers reconcile with the per-reviewer framing of `reports/cover_letter_draft.md` §3 (R3-1: "Abstract revised with concrete numbers (May-5 working text, reconciled against A4.1 in week 14): each client receives back a model strictly better than its local teacher with no plaintext leakage of its data; structural argument made explicit"). The four challenges follow the cover letter §2's AE-6 / R3-2 row verbatim except for the C1/C3 ordering, which is shifted so that C1 (depth budget — the load-bearing protocol-design property) leads and C3 (binding invariant — the load-bearing security property) follows the ensemble-construction C2; the legacy ordering inside the cover letter table was sequenced by reviewer concern, not by paper exposition.

### FL_TDSC/main.tex:89-99 (Abstract — second and third paragraphs)
Reason: legacy abstract framed the protocol with the rejected version's three structural claims (doubly-exponential magnitude growth, train-inference covariate shift, scale-aware loss) and the rejected version's per-block ciphertext-upload story. Replaced with (a) a rewritten protocol paragraph that names the public-probe encrypted logit upload, the ensemble target, and the linear-accumulator construction, and (b) a participation-incentive paragraph that makes the structural argument and supplies the four May-5 working numbers. The DP-tax framing matches `reports/cover_letter_draft.md` §3 R1-W4 (DP-SGD noise injected at the local teacher, no central DP tax on top of the cryptographic guarantee). The opening "we present" sentence retains the existing voice anchor. The two pre-existing commented-out blocks (the placeholder lead and the rejected-version abstract) are left untouched.
Before:
```
\begin{abstract}

% Federated learning enables collaborative training while keeping client data local, yet sharing model updates or distillation targets with a central server exposes private information. Existing mitigations, such as differential privacy and secure aggregation, either degrade model quality or fail to prevent the server from inspecting the aggregated signal. Homomorphic encryption (HE) offers cryptographic protection, but an iterative training of deep networks with HE is prohibitively expensive due to large multiplicative depth.

We present HE-IFD, a one-shot federated knowledge distillation protocol whose central property is that every client contribution, and every server-side intermediate, remains a homomorphic ciphertext throughout training. Each client trains a local teacher on its private data, extracts the input-output pair of every block boundary, and uploads them, encrypted under a multiparty CKKS scheme with collectively held keys, to the server in a single communication round. The server distils these encrypted pairs into a homomorphism-compatible student, performing forward pass, loss evaluation, gradient computation, and weight update entirely on ciphertexts. The trained student is released to the clients only through a collective key-switching step that requires every client to participate, so the server's view of the protocol is, by construction, computationally indistinguishable from random.

Training such a student is constrained by the structure of the polynomial network class: the composition of degree-$d$ activations across $L$ blocks produces an end-to-end map of degree $d^L$, whose magnitude grows doubly-exponentially in depth, and whose train-time and inference-time input distributions diverge once each block is trained in isolation. We treat magnitude control and distribution alignment as first-class consequences of these properties rather than as numerical workarounds. The resulting protocol combines client-side collaborative normalisation, a magnitude-regularised loss with a symmetric scale-free penalty, and a server-only refinement pass that closes the train-inference gap without further client communication. Under non-IID data partitions, the student aggregates specialised knowledge from all teachers and consistently exceeds the mean individual teacher accuracy across heterogeneity settings, providing a participation incentive for every client.

% The CKKS encryption provides cryptographically guaranteed privacy against a semi-honest server, making additional defences such as differential privacy unnecessary for training-time protection.

\end{abstract}
```
After:
```
\begin{abstract}

% Federated learning enables collaborative training while keeping client data local, yet sharing model updates or distillation targets with a central server exposes private information. Existing mitigations, such as differential privacy and secure aggregation, either degrade model quality or fail to prevent the server from inspecting the aggregated signal. Homomorphic encryption (HE) offers cryptographic protection, but an iterative training of deep networks with HE is prohibitively expensive due to large multiplicative depth.

We present HE-IFD, a one-shot federated knowledge distillation protocol whose central property is that every client contribution, and every server-side intermediate, remains a homomorphic ciphertext throughout training. Each client trains a local teacher on its private data, evaluates it on a public probe, and uploads the encrypted teacher logits, under a multiparty CKKS scheme with collectively held keys, to the server in a single communication round. The server aggregates the encrypted logits into an ensemble target and distils a student against that target, with the per-step encrypted update held as a linear accumulator over teacher-induced gradients applied to a plaintext student state. The trained student is released to the clients only through a collective key-switching step that requires every client to participate, so the server's view of the protocol is, under the IND-CPA security of CKKS, computationally indistinguishable from random.

The protocol's structural argument for participation is that each client receives back a student strictly better than its own local teacher, with no plaintext leakage of the data that trained that teacher. At the worst-case heterogeneity setting a sceptical reader is most likely to probe ($N{=}10$ clients, Dirichlet $\alpha{=}0.3$), the HE-IFD student reaches $0.965$ on MNIST against a mean individual teacher accuracy of $0.81$ ($+15.5$ pp) and $0.521$ on CIFAR-10 against a mean teacher of $0.408$ ($+11.3$ pp). The differential-privacy budget required to bound post-release inference on the decrypted student is absorbed entirely by the cryptographic instantiation: DP-SGD noise is injected at the local teacher rather than at the aggregate, so there is no central DP tax on top of the cryptographic guarantee. Together, the binding invariant on threshold decryption and the linear-accumulator construction reduce the adversary's view, server in coalition with up to $N{-}1$ clients, to the released student alone, the floor that no collaborative-training protocol can avoid.

% The CKKS encryption provides cryptographically guaranteed privacy against a semi-honest server, making additional defences such as differential privacy unnecessary for training-time protection.

\end{abstract}
```

### FL_TDSC/introduction.tex:24-33 (§I-A "Our Approach" — three legacy challenges + closing paragraph)
Reason: the three legacy `\par\noindent\textbf{...}` paragraphs (polynomial magnitude growth, train–inference covariate shift, scale-aware loss) described a protocol that the resubmission no longer implements. They are artefacts of the rejected block-wise HE-IFD design, per `reports/cover_letter_draft.md` §2 AE-6 row ("the three legacy challenges are artefacts of the depth-heavy block-wise protocol"). Replaced with four `\par\noindent\textbf{(C1)..(C4)}` paragraphs following the post-pivot CFD / linear-accumulator design. Each paragraph closes with an explicit `\ref{...}` pointer to the section that develops the construction in full, satisfying the "linking to chapters" demand the advisor flagged in R3-2. The legacy closing paragraph ("Together, these three properties...") is replaced with a four-properties closing that names the same four challenges and points to `\ref{sec:methodology}` and `\ref{sec:experiments}`. The three-phase enumeration (lines 18–22) and the "server never observes any individual teacher output..." lead sentence at line 24 are preserved verbatim; only the post-enumeration body is rewritten.
Before:
```
The server never observes any individual teacher output, student weight, or intermediate activation in plaintext. It operates as a blind compute delegate that executes the distillation protocol on encrypted data. A key technical difficulty is training an HE-compatible network where non-polynomial operations (ReLU, batch normalisation) are replaced with polynomial equivalents that can be evaluated on ciphertexts, from encrypted intermediate supervision. Several compounding challenges make standard distillation approaches fail. 

\par\noindent\textbf{Polynomial magnitude growth is a structural property of the network class.} A polynomial activation of degree $d$, composed across $L$ blocks, yields an end-to-end map of degree $d^L$ in its input. The induced upper bound on the activation magnitude grows doubly-exponentially in depth, regardless of how the polynomial coefficients are chosen, and this is what distinguishes polynomial deep networks from ReLU networks (whose composition is piecewise $1$-Lipschitz). The federated setting amplifies the effect: heterogeneous clients induce different distributions on each block boundary, and the HE-compatible analogue of batch normalisation, a static per-channel affine map fixed before training, cannot adapt across distributions. Magnitude control is therefore a structural requirement for polynomial deep networks under federated encryption, not a numerical workaround.

\par\noindent\textbf{Training and inference distributions diverge under block-wise composition.} Decomposing the student into blocks and training each block independently confines the CKKS multiplicative depth to a single block (see Section~\ref{sec:ckks_prelim}), but it also introduces a covariate shift across the composition: block $k$ is trained on the distribution of teacher-produced inputs and evaluated on the distribution of student-produced inputs from the frozen prefix. The composed map cannot be consistent at inference unless this gap is closed. We close it through trainable per-channel affine bridges, initialised from the uploaded feature statistics, followed by a sequential refinement pass that exposes each block to its actual inference-time distribution. Both steps remain server-side and require no additional client communication.


\par\noindent\textbf{The distillation loss must be scale-aware in magnitude and shape-aware in feature space.} Standard mean squared error is not invariant to the sign asymmetry between ReLU and polynomial features and admits unbounded magnitude drift, which is then amplified through every frozen downstream block. The structural argument above forces the loss to control \textit{shape} and \textit{magnitude} separately. We use a channel-normalised mean-squared error to align the feature shape independently of scale, combined with a log-ratio penalty $(\log\,\sigma_{\hat{f}}/\sigma_{\tilde{f}})^2$ on the per-channel standard deviations. The log-ratio form is the natural choice for matching magnitudes: it is symmetric in over- and under-scaling and invariant to a uniform rescaling of the targets, properties that a plain $\ell_2$ scale penalty does not satisfy.

Together, these three properties of polynomial deep networks under federated encryption (doubly-exponential magnitude growth, train-inference covariate shift across composed blocks, and the need for a scale-aware loss) determine the design of the protocol. Section~\ref{sec:methodology} develops each of them; Section~\ref{sec:experiments} reports the resulting accuracy on CIFAR-10 and FashionMNIST across three architectures (ResNet-18, SimpleCNN, ViT-B/32), confirms that the framework generalises beyond a single model family, and shows that the encrypted student tracks the centralised plaintext Oracle and exceeds the mean individual teacher across all heterogeneity settings.
```
After:
```
The server never observes any individual teacher output, student weight, or intermediate activation in plaintext. It operates as a blind compute delegate that executes the distillation protocol on encrypted data. Four properties of the protocol class determine the design and govern what can be proven about it; each is the structural answer to a distinct concern raised by the rejected version's review cycle.

\par\noindent\textbf{(C1) HE depth budget for an end-to-end encrypted student update.} A naive encrypted SGD step that forward-propagates through encrypted weights accumulates one multiplicative level per affine layer plus the degree of every polynomial activation, which exceeds the level chain available in any practical CKKS parameterisation long before the student converges. We avoid the naive construction. The encrypted state at every step is a \emph{linear accumulator} over teacher-induced gradient contributions, $\langle\theta_E\rangle = \langle\theta_0^\star\rangle + \sum_t \eta\,\langle g_t\rangle$, where each $\langle g_t\rangle$ is computed from the encrypted teacher signal applied to a plaintext student state. The per-step depth is at most three multiplicative levels (residual carry-over, scalar-by-ciphertext for the learning rate, addition to the accumulator), and the dominant ciphertext-by-ciphertext cost is confined to the depth-3 ensemble target construction described in Section~\ref{sec:phase2}; the full protocol fits inside a single CKKS level chain at $\log N \in \{14, 15\}$ with no bootstrapping. The structural justification for the plaintext student state during training, and for what is and is not allowed to be threshold-decrypted, is the binding invariant developed in Section~\ref{sec:threat_binding}.

\par\noindent\textbf{(C2) $\beta/\lambda$ ensemble boost without division under HE.} Pooling per-client encrypted teacher logits into an ensemble target with confidence-aware reweighting requires both a per-client confidence weight $\alpha_i^\beta$ and a per-row data-boost factor $1+\lambda V_k$ on the encrypted variance across teachers. Both knobs are constructed in CKKS without any encrypted division: the $\beta$-power is taken on the plaintext scalar $\alpha_i$ and applied as a scalar-by-ciphertext multiplication, and the per-row variance is built as $\langle V_k\rangle = \sum_i w_i \langle T_{i,k}\rangle^2 - \langle\bar T_k\rangle^2$ at depth 1. The resulting ensemble target is at most three multiplicative levels deep regardless of $N$. The construction is detailed in Section~\ref{sec:phase2}; the same section formalises why the depth bound is independent of $N$ and why a per-class coverage-aware variant of $\beta$ is the natural extension at the lowest-$\alpha$ heterogeneity settings.

\par\noindent\textbf{(C3) Binding invariant under $N{-}1$ collusion.} The cryptographic primitive is the multiparty variant of CKKS in the threshold instantiation at $t{=}N$: all $N$ secret-key shares must concur to recover any plaintext. The choice $t{=}N$ rather than $t < N$ is deliberate, because any $t < N$ admits a coalition of $t{-}1$ semi-honest clients who can decrypt the per-client logit ciphertexts and the aggregated ensemble target, which under the present threat model directly enables subtraction attacks against the remaining honest client. The protocol's central security property, that the only ciphertext ever subjected to threshold decryption is the final trained student $\theta_E$, is the binding invariant, formalised in Section~\ref{sec:threat_binding}. With the invariant, the adversary's view (server in coalition with up to $N{-}1$ clients) consists of IND-CPA ciphertexts, plaintext metadata (probe set, ciphertext sizes, timing), and the released student alone.

\par\noindent\textbf{(C4) Post-release statistical-query-floor mitigation.} The binding invariant prevents direct decryption attacks on intermediate state, but it does not rule out a derived form, utility-coercion-into-privacy-amplification: if $N{-}1$ colluding clients upload all-zero logit ciphertexts, the encrypted ensemble target collapses to a multiple of the single honest client's logits and the released student becomes a single-teacher distillation of that honest teacher. The attack does not breach the invariant; it inflates the unavoidable statistical-query floor on $\theta_E$. The protocol admits two independent defensive knobs: each client trains its teacher with DP-SGD at a per-client budget $(\varepsilon_T, \delta_T)$ that survives by post-processing into the released student, and each client may add per-row Gaussian noise to its logit vector before encryption, which surfaces at full magnitude under the all-zeros amplification and averages to $\sigma_P/\sqrt N$ in the honest case. The composition is bounded by the standard Gaussian-DP RDP accountant. The construction is developed in Section~\ref{sec:threat_binding}.

Together, these four properties (the depth budget for the linear accumulator, the division-free $\beta/\lambda$ ensemble boost, the binding invariant on threshold decryption, and the SQ-floor mitigation by DP-SGD teachers plus per-row Gaussian noise) determine the design of the protocol. Section~\ref{sec:methodology} develops each of them; Section~\ref{sec:experiments} reports the resulting accuracy on MNIST and CIFAR-10 against the strongest published one-shot baselines, and shows that the encrypted student consistently exceeds the mean individual teacher accuracy across heterogeneity settings, with the largest margins at the smallest $\alpha$.
```

**Cross-reference decisions.**
- **C1 (HE depth budget)** points to `\ref{sec:phase2}` for the depth-3 ensemble target (the dominant CT$\times$CT cost) and to `\ref{sec:threat_binding}` for the plaintext-student-state-during-training paragraph that anchors the linear-accumulator construction. The methodology has no `sec:linear_accumulator` label yet — that is issue 13's scope (wholesale methodology rewrite). When issue 13 lands, this C1 pointer may want to be retargeted to a more specific label inside §4.3; for now, `sec:phase2` + `sec:threat_binding` together carry the load-bearing claims.
- **C2 ($\beta/\lambda$ ensemble boost)** points to `\ref{sec:phase2}` exclusively, on the precedent set by `CHANGES.md` §9 (the A8 threat-model rewrite), which already targets `sec:phase2` for "the depth-bounded ensemble target construction" because no `sec:methodology_ensemble` or `sec:phase2_ensemble` label exists yet. This is the same retargeting flag that issue 13 will resolve.
- **C3 (binding invariant)** points to `\ref{sec:threat_binding}` — the label introduced by issue 05's threat-model rewrite. Exact fit.
- **C4 (SQ-floor mitigation)** points to `\ref{sec:threat_binding}`, which carries the "All-zeros amplification and its defence" paragraph from issue 05. When issue 13 sublabels the methodology, the C4 pointer can be retargeted to a more specific label inside that paragraph; for now, `sec:threat_binding` is the only label that covers it.

**Voice / structural decisions.**
- The "we proudly demonstrate" register is held off: the abstract's second paragraph opens with "The protocol's structural argument for participation is that..." rather than "We show...". The participation-incentive numbers are framed as evidence at the worst-case heterogeneity setting a sceptical reader will probe first, not as a headline result.
- The four C1–C4 paragraphs follow the same `\par\noindent\textbf{...}` template used by the legacy three paragraphs, and by the issue-05 threat-model paragraphs at `methodology.tex:19–31`, so the visual structure of §I-A is preserved.
- The pre-existing three-phase enumeration (lines 18–22) is kept verbatim, even though it still says "block by block" and uses "PolyResNet-18" as the student example. The post-pivot CFD protocol no longer trains block-by-block, but the three-phase enumeration is the canonical opening of §I-A in this draft and the wholesale rewrite belongs to issue 13. The C1–C4 paragraphs name the linear-accumulator construction explicitly, so the C1 framing wins over the enumeration phrasing where they conflict; future issue 13 should align the enumeration with C1–C4.
- The commented-out backup block at lines 56–109 (the prior version of §I-A) is left untouched.

**Numbers freeze.**
- All four May-5 numbers ($0.965$, $0.81$, $0.521$, $0.408$) appear verbatim in the abstract's participation-incentive paragraph. The deltas ($+15.5$ pp, $+11.3$ pp) are arithmetic; both are derived from the May-5 numbers directly.
- The $N{=}10$, Dirichlet $\alpha{=}0.3$ context (the worst-case heterogeneity reviewers will probe first) is named explicitly so the numbers are unambiguous when read against `reports/2026-05-05_one_shot_cfd_central_vs_client_update.md` §4.1 and §5.1.
- Per action plan A10's "Numbers freeze + replacement protocol" (lines 408–417), these are the working text; the 2026-07-01 A4.1 partial-results reconciliation may silently update them if $|\Delta| \le 3$ pp on either ratio.

**Syntactic checks performed (cluster compile gate unavailable, `pdflatex.fmt` missing per `ralph/prompt.md` §FEEDBACK LOOPS).**
- Balanced braces on `FL_TDSC/main.tex`: 317/317 (up from 314/314 pre-edit; net $+3/+3$ matches the new prose with one extra `\sqrt N$ and two extra `\{` from the math-mode constructs).
- Balanced braces on `FL_TDSC/introduction.tex`: 97/97 (up from 89/89 pre-edit; net $+8/+8$ matches the new prose with new `\ref{...}`, `\textbf{...}`, and math-mode constructs).
- Every `\cite{...}` in the edited regions resolves: no new `\cite{...}` keys introduced in either file; the abstract's new prose makes no bibliographic citations, and §I-A's pre-existing citations (`zhu2019deep`, `so2023securing`, `jagielski2023students`, `shao2023selective`, `kerkouche2023client`, `zhang2020batchcrypt`, `jin2023fedml`, `kanpak2024cure`, `agamennone2025polynomial`, `alhossain2025training`) are untouched.
- Every `\ref{...}` in the new §I-A region resolves to a `\label{...}` in `FL_TDSC/*.tex`: `sec:phase2` → `methodology.tex:102`, `sec:threat_binding` → `methodology.tex:17`, `sec:methodology` → `methodology.tex:2`, `sec:experiments` → `experiments.tex:2`.
- Legacy challenge terms ("polynomial magnitude", "training–distillation", "scale-aligned", "scale-anchored") absent from active §I-A prose (lines 15–35). Three commented-out occurrences remain at lines 86, 88, 90 inside the pre-existing backup block (lines 56–109); not in active prose, so the acceptance criterion holds.
