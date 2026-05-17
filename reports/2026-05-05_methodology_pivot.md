# Methodology pivot: HE-IFD becomes encrypted public-probe CFD
## PRD — design decisions of the 2026-05-05 grilling session

**Date:** 2026-05-05
**Author:** H.İ. Kanpak (with assistance, design notes only — no experimental runs in this document)
**Status of this document:** This is the **authoritative design reference** for the rewrite. It supersedes the existing `FL_TDSC/methodology.tex` content where they conflict.

> **Deprecation note for downstream builder LLMs.** The current `FL_TDSC/methodology.tex` describes the **block-wise HE-IFD** protocol (per-block intermediate-feature ciphertexts, magnitude regularisation, sequential block training with bridges). That content is **deprecated** as of 2026-05-05. The new methodology is the encrypted CFD protocol described in §4 of this PRD. When the existing `methodology.tex` and this PRD disagree, **the PRD wins**. Do not propagate any block-wise terminology, the per-block ciphertext upload, the bridge construction, or the magnitude-regularisation loss into the rewritten paper — these structures do not exist in the new protocol.

**Scope:** Captures the design decisions reached for the HE-IFD paper rewrite, the new threat model, the public/synthetic probe variants, and the experimental plan that follows. The paper title and acronym (HE-IFD) are retained; the underlying protocol changes from block-wise intermediate-feature distillation to encrypted central federated distillation (CFD) on a public or synthetic probe set.

This document is a working specification, not the paper. Edits to `FL_TDSC/*.tex` driven by these decisions are logged separately in `FL_TDSC/CHANGES.md`.

---

## 1. Why the pivot

The block-wise HE-IFD protocol currently in `FL_TDSC/methodology.tex` carries three structural costs that the alternative protocol described in the May-5 results report avoids:

1. Polynomial deep-network composition forces magnitude regularisation, bridges, and sequential block refinement; the depth-doubly-exponential growth bound is intrinsic to the function class.
2. Per-block feature ciphertexts at every block boundary multiply the upload payload by the number of blocks $K{+}1$; a single-probe-logit upload is $1/(K{+}1)$ the volume.
3. Threshold-decrypting an encrypted student that has been trained against per-block feature pairs has the same release-cone leakage as any other final-student release, but the *intermediate-feature uploads themselves* are an additional plaintext-metadata channel for inversion attacks even under IND-CPA, because per-channel normalisation statistics must be released in the clear.

The May-5 report shows that an encrypted CFD protocol on a public probe of 5k samples (a single upload of teacher logits per client) achieves utility within 0.8 pp of the strongest unencrypted one-shot baseline at MNIST $\alpha{=}0.3$, with a markedly simpler HE depth profile and a cleaner threat surface. The pivot keeps the privacy story (cryptographic, IND-CPA, threshold-decrypted final student only) and replaces the depth-heavy block-wise compute with a single-channel encrypted aggregation followed by depth-bounded encrypted student SGD on the probe.

---

## 2. Threat model

This section is the contract that downstream sections must respect.

### 2.1 Parties and trust assumptions

- $N$ clients, each holding a private dataset $\mathcal{D}_i$. One central server. Cross-silo setting.
- All parties are **honest-but-curious (semi-honest)**: they execute the protocol faithfully but pool every observation to attempt to recover what the protocol intends to hide.
- The adversary is allowed to corrupt **the server plus up to $N{-}1$ clients** simultaneously and merge their views.
- Verifying that a semi-honest server has actually performed the homomorphic operations it claims is currently outside the scope of this paper. Verifiable HE (Viand–Knabenhans–Hithnawi 2023 SoK; Rinocchio-style verifiers; recent vCKKS lines) is the natural extension and is named explicitly in §research-directions, with no claim to having implemented it.

### 2.2 Cryptographic primitive

Multiparty CKKS in the threshold variant of Mouchet et al., as instantiated in Lattigo. Distributed key generation produces a single collective public key $\mathsf{pk}$ and per-client secret-key shares $\mathsf{sk}_i$ such that **all $N$ shares are required to decrypt** ($t{=}N$). Privacy of any client's input is preserved as long as at least one client is honest.

The choice of $t{=}N$ over $t < N$ is deliberate: any $t < N$ admits a coalition of $t{-}1$ semi-honest clients who can decrypt every aggregate the protocol exposes, including per-row teacher logits, which under our threat model directly enables subtraction attacks against the remaining honest client. $t{=}N$ creates a denial-of-service surface (any one client can refuse to participate in decryption); we accept this since DoS is a liveness concern, not a privacy concern, and is a standard cost in the multiparty-FHE literature.

### 2.3 Binding invariant on threshold decryption

**The only ciphertext ever subjected to threshold decryption (or collective key-switch to a per-client target) is the final trained student's parameter vector $\theta_E$. No per-client logit ciphertext, no aggregated ensemble target, no auxiliary encrypted scalar is ever decrypted at any stage of the protocol.**

This invariant is part of the threat model, not the protocol. Without it, a coalition of $N{-}1$ clients who know their own contributions and observe a decrypted aggregate can subtract their inputs from the aggregate and recover the honest client's contribution exactly. With it, the only adversary-visible plaintext is $\theta_E$, which is a non-linear function of all clients' private inputs through the distillation training and so does not admit a closed-form subtraction attack on any single client.

Consequence: the May-5 client-update Δθ aggregation protocol violates this invariant whenever the aggregated weights are themselves decrypted (because they linearly compose per-client deltas). It is therefore demoted to a diagnostic, not a primary variant.

### 2.4 Adversary's view (what is computationally hidden, what is plaintext, what is released)

Under (B) + the binding invariant + IND-CPA security of CKKS, the adversary's view consists of three disjoint subsets:

| Subset | Content | Status |
|---|---|---|
| Encrypted | per-client teacher logit ciphertexts $\langle T_i(\mathcal P)\rangle$; any encrypted scalars $\langle\alpha_i\rangle$; the encrypted ensemble target $\widetilde Y$; encrypted student weights at every SGD iteration | computationally indistinguishable from random ring elements |
| Plaintext metadata | the public probe $\mathcal P$ itself (in the α-variant); ciphertext sizes and counts; protocol timing; per-client public data sizes if disclosed | reveals only protocol structure, not data |
| Released | the final student $\theta_E$ after threshold decryption | bounded above by the SQ-floor on $\theta_E$ |

The released-student leakage is exactly what the user described as the "lower-bound leakage": any collaborative-training output is observable to its recipients via white-box / SQ access, and this floor is unavoidable for any protocol that releases a usable model. The contribution of HE is to keep the adversary's view at *exactly* this floor, with nothing above it.

### 2.5 Privacy extension: defending the all-zeros input-coercion attack

Under (B) the all-zeros attack does not directly violate the invariant: it does not allow decryption of any aggregate. It survives in a derived form, **utility-coercion-into-privacy-amplification**: if $N{-}1$ colluding clients upload all-zero logit ciphertexts, the encrypted ensemble target collapses to a multiple of the honest client's logits, the released student becomes a single-teacher distillation of that one honest teacher, and the SQ-floor on the released student rises silently. The attack inflates the unavoidable lower-bound leakage instead of breaching the invariant.

The proposed defence is differential privacy on the upload, structured as two independent knobs:

- **(P1) DP-SGD-trained teachers, primary knob.** Each client trains $T_i$ on $\mathcal{D}_i$ with DP-SGD at per-client budget $(\varepsilon_T, \delta_T)$. By the post-processing theorem, $T_i(\mathcal P)$ inherits this budget, and so does the released student. The all-zeros amplification cannot reduce this floor: the privacy of $T_h$ is already client-local and survives any server-side computation.
- **(P2) Optional per-row Gaussian noise on logits before encryption.** Each client adds $\eta_i \sim \mathcal N(0, \sigma_P^2 I)$ to its per-row logit vector before encryption. In the honest case the noise averages as $\sigma_P/\sqrt N$ at the ensemble target so utility loss is mild; under the all-zeros amplification it shows up at full magnitude and contributes an additional $(\varepsilon_P, \delta_P)$ layer that takes effect only in the worst case.

The composition of (P1) and (P2) is the standard Gaussian-DP RDP composition. The exact $\varepsilon_T, \varepsilon_P$ values are deferred to a later working session; the methodology paper's claim is structural — that the protocol admits both knobs — not numerical.

### 2.6 Out-of-scope adversaries

- **Malicious server** (deviates from prescribed homomorphic computation): out of scope; future work via verifiable HE.
- **Malicious clients** that craft arbitrary upload payloads to corrupt utility: out of scope; this is a model-poisoning concern that does not breach privacy under the invariant. Mentioned in §discussion only.
- **Network-level adversaries** (DoS, traffic analysis, side-channels of the HE library, timing leaks beyond ciphertext sizes): out of scope.

### 2.7 Threat-model figure (specification)

A single figure shows:
- $N$ client boxes, each containing $\mathcal{D}_i, T_i, \mathsf{sk}_i$ (the per-client secret key share). Up to $N{-}1$ of these are highlighted as "may collude with server." One client is shaded as "honest" with the note "as long as one such client exists, privacy holds."
- A central server box, shaded as "may collude," holding the collective public key $\mathsf{pk}$, the public probe $\mathcal P$, and the encrypted student $\langle\theta\rangle$ during training.
- A single arrow per client from client to server labelled "$\langle T_i(\mathcal P)\rangle$ (encrypted)."
- A single arrow per client from server to client labelled "$\langle\theta_E\rangle$ (encrypted, then collectively key-switched)."
- A dashed boundary around the server's compute denoting "everything inside is ciphertext under $\mathsf{pk}$, IND-CPA-hidden."
- A small inset showing the threshold-decryption gate: $N$ key-share inputs, one plaintext output ($\theta_E$ only).
- A side panel listing exactly what the adversary sees in plaintext (Subset 2 of §2.4).

The figure is rendered as a plain **SVG** at `FL_TDSC/figures/threat_model_v2.svg` — single panel, minimal decoration, two fills (client `#C6A87D`, server `#8B9EA8`), plain rectangles + arrows + text. The PDF used by the manuscript is produced at build time via `rsvg-convert --format=pdf threat_model_v2.svg -o threat_model_v2.pdf`. No TikZ. The SVG source and the regenerated PDF are committed together and logged in `FL_TDSC/CHANGES.md`. Authority for this decision: Appendix A "Closed".

---

## 3. The probe set: variants, trust, and Co-Boosting comparison

### 3.1 Variant α — public probe (the headline)

A held-out subset of the same domain (e.g., MNIST or CIFAR-10 training set, taken aside before the Dirichlet partition is applied to clients), of size $|\mathcal P| = 5000$ following FedMD's convention. The probe is plaintext, known to the server and all clients, and labelled (the labels enable the plaintext warm-start of §6).

The probe is "public" in the sense that no party loses anything by revealing it: it was held out *before* any private partitioning, it is statistically independent of any client's private data, and any party already holds it as a known reference. Its presence is part of the protocol assumption, not part of the privacy budget.

This variant matches the FedMD / DS-FL / FedDF lineage and gives us a direct comparator against unencrypted public-probe distillation methods.

### 3.2 Variant γ — encrypted client-side diffusion-generated probe (the no-public-data extension)

Each client trains a **pixel-space DP-DDPM** on $\mathcal{D}_i$ locally with DP-SGD (Dockhorn et al., *Differentially Private Diffusion Models*, TMLR 2022, arXiv:2210.09929), at per-client budget $(\varepsilon_G, \delta_G) = (10, 10^{-5})$, sampling $|\mathcal P|/N = 500$ synthetic inputs locally (for $N{=}10$), encrypting them under $\mathsf{pk}$, and uploading. The server pools the encrypted synthetic inputs to form an encrypted probe $\langle\mathcal P_{\text{syn}}\rangle$ of total size $|\mathcal P| = 5000$ — matching the α-variant exactly so the α-vs-γ comparison isolates the public-vs-synthetic axis.

Architecture choice. Pixel-space DP-DDPM (rather than latent-space DP-LDM, Lyu et al. arXiv:2305.15759) because no shared latent autoencoder exists across federated clients without itself being a leakage channel. Generator architecture: a small U-Net (~2–3M params) per Dockhorn et al.'s reference implementation at github.com/nv-tlabs/DPDM. Per-client training cost on T4: ≈ 6–12 h per client per dataset; for $N{=}10$ × 3 datasets this is the dominant compute item in γ-variant experiments and the reason γ is run on a subset of the headline grid only.

Privacy budget. Headline at $(\varepsilon_G, \delta_G) = (10, 10^{-5})$ — Dockhorn et al.'s primary evaluation point and the standard DP-image-synthesis anchor. A tighter $(\varepsilon_G, \delta_G) = (1, 10^{-5})$ point reported as an ablation in §discussion. These two pairs are exactly the values at which DPDM has published downstream classifier numbers (98.1% MNIST at $\varepsilon{=}10$; 83.2% MNIST at $\varepsilon{=}1$); we can compare directly.

Probe size. $|\mathcal P_{\text{syn}}| = 5000$. No prior-work convention exists for "encrypted synthetic probe size in federated distillation" because no prior work runs encrypted distillation on a synthetic probe; FedDM (Xiong et al. CVPR 2023, arXiv:2207.09653) uses 10–50 images-per-class per client for a different purpose (data condensation), and FedGM (Liu et al., MDPI Electronics 2024) uses gradient-matched synthesis with only label-DP, which is a structurally different privacy story. Anchoring to α's 5000 is the only defensible choice that lets the α-vs-γ comparison be apples-to-apples.

Critical design point: in γ, **the synthetic probe is never decrypted at any point**. It stays encrypted through the entire student-training loop. The student's forward pass on encrypted inputs requires depth-many ciphertext-ciphertext multiplications, so γ is HE-cost-heavier than α. By the post-processing theorem, the released student's leakage on $\mathcal{D}_i$ is bounded by $(\varepsilon_G + \varepsilon_P, \delta_G + \delta_P)$ via composition (no $\varepsilon_T$ since teachers are non-DP per the headline decision).

The privacy advantage over Co-Boosting (Dai et al. ICLR 2024, arXiv:2402.15070) is structural and stated explicitly in the manuscript: Co-Boosting trains a server-side adversarial generator on plaintext client weights and produces synthetic samples adversarially in plaintext; the server has full knowledge of every synthetic sample plus full knowledge of every teacher. Co-Boosting carries no DP guarantee on the synthetic distribution and structurally cannot acquire one without abandoning the adversarial-generator construction at the server. Our γ-variant trains the generator at the client under DP-SGD; the server sees only encrypted synthetic and encrypted teacher logits; the synthetic distribution carries a formal $(\varepsilon_G, \delta_G)$ that Co-Boosting cannot match at any utility cost. The γ-variant therefore positions itself not as a utility-improvement on Co-Boosting but as the only one-shot federated distillation protocol with a formal DP-on-synthetic guarantee.

### 3.3 Variant ε — no probe, client-update Δθ aggregation (legacy diagnostic)

Each client distils its own teacher into a local copy of the global student starting from a shared random init $\theta_0$, encrypts the parameter delta, uploads. Server linearly aggregates and threshold-decrypts. **This violates the binding invariant of §2.3 and is retained only as a diagnostic** — it is the protocol the May-5 report identified as failing under $N{-}1$ collusion (per-client deltas are linearly subtractable from the decrypted aggregate). Not a publishable variant.

### 3.4 What we say about Co-Boosting

Co-Boosting is reframed in the related-work section as "the privacy-unaware ceiling": the strongest unencrypted one-shot baseline, which we approach in α and surpass in privacy guarantee in both α and γ. The privacy comparison is not numerical (Co-Boosting has no privacy budget) but structural — they leak plaintext teacher weights and plaintext synthetic to the server; we leak neither to the server beyond ciphertexts.

---

## 4. Encrypted CFD protocol (replaces current §methodology of paper)

### 4.1 Phases

| Phase | Who | What | HE cost |
|---|---|---|---|
| 0 | all | DKG → collective $\mathsf{pk}$, per-client $\mathsf{sk}_i$ | one-time |
| 1 | clients | local teacher SGD on $\mathcal{D}_i$ (DP-SGD if (P1) is on); compute $T_i(\mathcal P)$; optional per-row Gaussian noise (P2); encrypt under $\mathsf{pk}$ | client-only |
| 1↑ | clients → server | upload $\langle T_i(\mathcal P)\rangle$ — one ciphertext bundle per client | the only client→server message |
| 2a | server | warm-start: plaintext SGD on $(\mathcal P, y_{\mathcal P})$ for $E_1$ epochs to get $\theta_0^*$. (α only; γ uses shared random $\theta_0$.) | plaintext |
| 2b | server | encrypt $\theta_0^*$ as $\langle\theta\rangle$; compute encrypted ensemble target $\widetilde Y = \sum_i \langle\alpha_i^\beta\rangle \cdot \langle T_i(\mathcal P)\rangle$; depth $\leq 2$. | encrypted, depth-2 |
| 2c | server | encrypted SGD on $\langle\theta\rangle$ against $\widetilde Y$ on probe inputs $\mathcal P$ (plaintext in α; encrypted in γ) for $E_2$ epochs. | encrypted, bootstrapped |
| 3↓ | server → clients | one download of $\langle\theta_E\rangle$ | the only server→client message |
| 4 | clients | collective key-switch on $\langle\theta_E\rangle$; receive plaintext $\theta_E$ | one round of share exchange |
| 5 | clients | (optional) cheap local fine-tuning of $\theta_E$ on $\mathcal{D}_i$ for personalised $\theta_{E,i}$ | client-only |

This is one encrypted upload + one encrypted download + one threshold-decrypt round, end-to-end.

### 4.2 β / λ secure handling

**β-boost without division.** Each client computes $\alpha_i = \mathbb{E}_{\mathcal P}[\max\sigma(T_i)]$ in plaintext (a single scalar), encrypts, uploads. Server raises to power $\beta$ via $\log_2 \beta$ ctxt-ctxt mults (depth $\log_2 \beta$, $=1$ for $\beta{=}2$). Ensemble target uses **un-normalised weights** $\langle\alpha_i^\beta\rangle$:
$$\widetilde Y = \sum_i \langle\alpha_i^\beta\rangle \cdot \langle T_i(\mathcal P)\rangle.$$
At distillation temperature $T'$ the KL identity $\text{KL}(\sigma(c\,Y/T) \| \sigma(S/T)) = \text{KL}(\sigma(Y/(T/c)) \| \sigma(S/T))$ shows that the omitted normalisation constant $c = \sum_j \alpha_j^\beta$ is absorbed into an effective temperature $T_{\text{eff}} = T'/c$. Convergent student is identical to the explicitly-normalised variant. **No division under HE; nothing decrypted; per-client confidence never appears in plaintext server-side.**

**λ-boost via uniform-weight per-row variance.** Per-row variance is computed with uniform weights:
$$V_k = \tfrac{1}{N}\sum_i \langle T_{i,k}\rangle^2 - \big(\tfrac{1}{N}\sum_i \langle T_{i,k}\rangle\big)^2,$$
one ctxt-ctxt square (depth +1), one ctxt-ctxt square of the mean (depth +1), subtraction (depth-0). $r_k = 1 + \lambda V_k$ then multiplies the per-row KL contribution; depth +1. Total loss-side depth-3 from raw logits. The plain $1/N$ scalar is trivially absorbed by ciphertext-plaintext multiplication (depth-0). No division required.

This decouples β and λ — λ's variance estimator no longer depends on the β-weights — at a small loss of theoretical optimality. The May-5 result that λ is "never hurts and gains 0–1 pp" suggests the simpler λ form is adequate.

### 4.3 HE depth budget per encrypted SGD step

The protocol does not forward-propagate through encrypted weights. The encrypted student $\langle\theta\rangle$ is a **linear accumulator** over encrypted gradient contributions:
$$\langle\theta_E\rangle = \langle\theta_0\rangle + \sum_t \text{lr} \cdot \langle\text{grad}_t\rangle,$$
where each $\langle\text{grad}_t\rangle$ is a per-layer SGD update computed from the encrypted teacher signal applied to plaintext student state at step $t$. There is no backward chain rule on encrypted intermediate activations; there is no per-layer depth accumulation across the network's depth. The student's forward pass at step $t$ runs in plaintext on the current decrypted-for-loss-only copy of the weights — only the *update* contribution is encrypted and added to $\langle\theta\rangle$.

**Per-step encrypted depth ≤ 3 levels**: residual carry-over of $\langle\theta\rangle$ (depth 0), scalar plaintext × ciphertext multiplication for the learning rate (depth +1), and addition to the accumulator (depth 0). The dominant cost is the encrypted ensemble-target depth of §4.2 (loss-side depth-3 from raw logits), incurred once per probe pass, not once per step.

LeNet-5 (or any deeper student architecture) fits TenSEAL's 7-level chain trivially at logN=14. No bootstrapping is required for any cell in the §7.2 grid. γ-variant inherits the same construction; the per-step depth budget is unchanged because the encrypted synthetic probe enters the loss-side computation of §4.2, not the per-step update.

Concrete parameter sketch (logN=14, scale=$2^{40}$, ring degree 16384): per-step ciphertext-arithmetic latency on a single core ≈ tens of milliseconds; total HE compute on the order of minutes per cell on commodity hardware. Numbers to be tightened by the TenSEAL prototype (A2) and the end-to-end single-cell run (A3).

---

## 5. Communication complexity

Per-protocol-run, in ciphertext units (one ciphertext = one CKKS vector, $N_{\text{slots}} = 16384$ at logN=15).

| message | direction | volume |
|---|---|---|
| client logit upload | client→server | $\lceil |\mathcal P| \cdot C / N_{\text{slots}}\rceil$ ctxts per client (C = num classes) |
| client confidence upload | client→server | 1 ctxt per client (single scalar in slot 0) |
| client synthetic upload (γ only) | client→server | $\lceil |\mathcal P_{\text{syn}}|/N \cdot d_{\text{input}} / N_{\text{slots}}\rceil$ ctxts per client |
| student download | server→client | $\lceil |\theta_E| / N_{\text{slots}}\rceil$ ctxts per client |
| key-switch shares | client↔client | one share per client, single round |

Concrete for MNIST/CIFAR-10 with $|\mathcal P| = 5000, C = 10, N = 10$ clients, LeNet-5 student (~60k params): each client upload is $\lceil 50000/16384\rceil = 4$ ctxts; download is $\lceil 60000/16384\rceil = 4$ ctxts; **total per-client traffic ≈ 8 ctxts ≈ 8 MB at ~1 MB/ctxt**, in a single round. This is in the same order of magnitude as the May-5 plaintext logit upload (50000 × 4 bytes × 32× CKKS expansion ≈ 6.4 MB) and comparable to one round of FedAvg on a small model.

Co-Boosting reports per-client traffic in the same band but unencrypted; HE-IFD pays a ~30× constant-factor expansion for ciphertext encoding, which is acceptable for a one-shot protocol.

---

## 6. Two-stage initialisation (variant α only)

### 6.1 Protocol

- **Stage 1 (plaintext, server-side).** Server trains the student on $(\mathcal P, y_{\mathcal P})$ with cross-entropy for $E_1 = 30$ epochs. Output: $\theta_0^*$, a "public-probe-only" student that knows the probe distribution but has zero client knowledge.
- **Stage 2 (encrypted, server-side).** Encrypted SGD on the probe with encrypted ensemble target $\widetilde Y$ (KL distillation), starting from encrypted $\langle\theta_0^*\rangle$, for $E_2$ epochs.

### 6.2 Hypothesis

Warm-starting on $\theta_0^*$ both reduces the number of encrypted SGD steps required for convergence and reduces the magnitude of the encrypted-vs-plaintext discrepancy at a fixed total training budget. The first effect lowers HE compute cost; the second tightens the gap between the published encrypted-domain accuracy and a hypothetical plaintext-domain run of the same protocol.

### 6.3 Ablations (post-baseline)

- **(A1) Random-init Stage 2.** Starts $\langle\theta\rangle$ from a fresh random init, $E_2' \geq E_2$ chosen so plaintext-equivalent training budget matches. Isolates the warm-start contribution.
- **(A2) Warm-start without ensemble target.** Stage 2 is plaintext SGD on $(\mathcal P, y_{\mathcal P})$ for additional epochs, no encrypted teacher knowledge. Isolates the encrypted-teacher-knowledge contribution. If A2 is competitive with full CFD, the headline contribution shifts to "warm-start is enough" — a paper-existential outcome we need to know about early.

### 6.4 Note on γ

In γ, no plaintext probe labels exist, so warm-start is not defined. γ runs from a shared random $\theta_0$ agreed at protocol start (deterministic seed). The γ-variant's HE-vs-plaintext gap is therefore the floor for what HE costs us, since there is no warm-start to amortise the cost.

---

## 7. Experimental grid

### 7.1 Reused artifacts

The May-5 sweep (job 1032257 MNIST, job 1032521 CIFAR-10) used 30-epoch teachers, 90-epoch central distill, $N{=}10$, Dirichlet $\alpha \in \{0.05, 0.1, 0.3\}$. Teacher checkpoints at `results/saved_teachers/` are partial: only `n4_a05_s42` and `n1_a1000_s42` are present. Re-using them would force $N{=}4$, which is a different setting from May-5. Action: **train a new round of teachers up to 100 epochs to match Co-Boosting's reported teacher budget**, save to `results/teachers_v2/`, and reuse across all subsequent experiments.

### 7.2 Grid

A single, narrow grid that exercises the dimensions that matter:

| axis | values |
|---|---|
| dataset | MNIST, CIFAR-10, FashionMNIST |
| $N$ | 10 (matches Co-Boosting and May-5) |
| Dirichlet $\alpha$ | 0.05, 0.1, 0.3, 1.0 |
| variant | α-warmstart, α-randominit (A1), α-warmstart-no-ensemble (A2), γ-encrypted-synth, ε-clientupdate (legacy) |
| seed | 3 seeds |

That is $3 \times 4 \times 5 \times 3 = 180$ cells, manageable on the T4 partition over a few days. We do **not** sweep $|\mathcal P|$, $\beta$, $\lambda$, or $E$ in the headline grid; those are fixed at $|\mathcal P|=5000, \beta=2, \lambda=8, E_1=30, E_2=200$ (the latter to match Co-Boosting's distillation length).

### 7.3 HE-vs-plaintext discrepancy measurement

For each cell, we measure two student accuracies:
- $\text{Acc}_{\text{plain}}$: full Stage 2 in plaintext arithmetic (no CKKS).
- $\text{Acc}_{\text{cipher}}$: full Stage 2 in CKKS-simulated arithmetic with realistic noise injection at scale $2^{-40}$.

The headline number is $\text{Acc}_{\text{cipher}}$. The discrepancy $\Delta = \text{Acc}_{\text{plain}} - \text{Acc}_{\text{cipher}}$ is the *HE tax*. We report $\Delta$ in a dedicated table to demonstrate that the encryption costs us ≤ 1 pp at every cell — the central technical claim of the paper.

### 7.4 Hardware

All runs on Valar `t4_ai` partition; never the login node. `sbatch jobs/cfd_v2_<dataset>_<variant>.sh`. Job templates live under `jobs/` (to be authored).

---

## 8. TenSEAL prototype + smoke test

A standalone Python prototype, written before any large-scale experiment, that:
1. Constructs a TenSEAL CKKS context with parameters matching the methodology (logN=14 minimum, scale=2^40, polynomial modulus ring degree configured to support depth ≥ 6 between bootstraps).
2. Encrypts mock teacher logit tensors of shape $(|\mathcal P|, C) = (5000, 10)$ with mock $\alpha_i$ scalars, $i = 1, \ldots, N$.
3. Performs the §4.2 β-aggregation (one ctxt-ctxt mult + linear sum) and recovers $\widetilde Y$ as a ciphertext.
4. Decrypts (with all simulated key shares) and compares against the plaintext-equivalent computation; asserts max element-wise error < $10^{-3}$.
5. Demonstrates one linear-accumulator update step: plaintext student forward on the probe, plaintext gradient computation against a decryption-for-loss-only copy of $\widetilde Y$, encryption of the resulting gradient, and addition $\langle\theta\rangle \mathrel{+}= \text{lr}\cdot\langle\text{grad}\rangle$. Verifies the $\langle\theta_E\rangle = \langle\theta_0\rangle + \sum_t \text{lr}\cdot\langle\text{grad}_t\rangle$ recurrence over $\geq 10$ steps and asserts the decrypted $\langle\theta_E\rangle$ matches a plaintext-equivalent linear accumulator within CKKS noise tolerance (max element-wise error < $10^{-3}$ at scale $2^{40}$).

This is a smoke test of the *primitives*, not the full protocol. It establishes that the depth budget claimed in §4.3 is real. To be implemented as `prototypes/cfd_tenseal_smoke.py` and run as `srun --partition=t4_ai --account=comx29 python prototypes/cfd_tenseal_smoke.py` (no login-node execution).

Forgetting points to watch: (a) The linear-accumulator construction consumes ≤ 3 levels per step (residual carry-over of $\langle\theta\rangle$, scalar plaintext × ciphertext for the learning rate, addition). TenSEAL's 7-level chain at logN=14 absorbs this with margin; **no bootstrapping is needed** and the smoke stays entirely inside TenSEAL. The previously-planned Lattigo migration for bootstrapping support is dropped. (b) Per-row Gaussian noise (P2) in the smoke test must be added to the *plaintext* logits before encryption, not to ciphertexts — the latter is non-trivial. (c) Precision: CKKS scale=$2^{40}$ gives ≈ 12 decimal digits, lower than f64 plaintext, so the plaintext baseline must use the same finite-precision arithmetic for a fair comparison.

---

## 9. Repository archive + new structure

**Cutover happens after grilling locks the design and this PRD is finalised, not before.** The current `HE_Distillation/` tree stays intact during the grilling so we don't lose context.

The plan:

1. **Archive.** Tar the entire current `/scratch/hkanpak21/HE_Distillation/` to `/scratch/hkanpak21/archive/HE_Distillation_2026-05-05.tar.gz` (sbatch job onto t4_ai, never login-node). Verify checksum. Do not delete the source until explicit user go-ahead.
2. **New clean tree.** `/scratch/hkanpak21/HE_IFD/`:
   ```
   FL_TDSC/                # paper text in full (no pruning at carry-over time)
   prototypes/             # TenSEAL prototype (parametric on student arch)
   reports/                # this PRD + the May-5 results report
   jobs/                   # sbatch templates
   results/                # initially empty
   legacy -> /scratch/hkanpak21/archive/HE_Distillation_2026-05-05.tar.gz   # symlink for reference
   ```
3. **Paper content at cutover.** `FL_TDSC/{main,methodology,experiments,introduction,background,conclusion,supplementary}.tex` carry over **verbatim, without pruning**. The deprecated block-wise content in `methodology.tex` is left in place at cutover; the wholesale replacement happens in the new tree as a logged CHANGES.md entry, so the diff is reproducible.
4. **Bib cleanup task (separate).** `references.bib` is cleaned up *after* cutover: remove duplicate entries, drop entries no longer cited by any `.tex`, normalise venue strings to short forms (e.g., "ACNS" instead of "Annual International Conference on Applied Cryptography and Network Security"). **Author lists and author names are kept as-is** — the existing shortening convention is fine. This is its own pass, logged in CHANGES.md, before any rewriting starts.
5. **Voice preservation.** The existing prose register in `methodology.tex:21` and `experiments.tex` is the target tone. New sections written in the same austere theoretical voice — no documentation-flavoured prose, no "we proudly demonstrate," no bullet sprawl in body text. Sceptical-professor reader assumed throughout. (Detailed in memory `feedback_paper_voice.md`.)
6. **CHANGES.md continuity.** `FL_TDSC/CHANGES.md` continues from its current state; every textual change driven by this PRD is logged with the established before/after format for Overleaf replay. The wholesale methodology-section replacement is logged as a single bulk-replacement entry that points to §4 of this PRD as the authoritative new content.

Code under `/scratch/hkanpak21/HE_Distillation/{src,demos,experiments,jobs,results,checkpoints,...}` does **not** carry over verbatim. Useful primitives (the May-5 demo entry points, multiparty CKKS bindings) are re-implemented from scratch in the new `prototypes/` tree to match the new methodology cleanly. The legacy code remains in the archive for reference.

---

## 9.5. Adaptive execution methodology (added 2026-05-17)

This PRD is the methodology, not the execution recipe. When an agent (Claude or otherwise) runs the experimental program in `reports/2026-05-10_tdsc_rejection_action_plan.md`, deviations will happen — comparator repos fail to reproduce, Valar QoS gets denied, projections undershoot, checkpoint-resume corrupts state. This section governs *how* the agent responds: which deviations are routine *tweaks* the agent applies and logs, which are *escalations* that halt execution and request user input.

The principle: **methodology has a stable core and adjustable peripherals.** Adjusting the peripherals is a tweak; touching the core is an escalation. Discuss methodology in terms of simple tweaks, not wholesale redesign.

### 9.5.1 Stable core (touch requires explicit user re-approval)

These design properties define the work; an agent that proposes to change them is no longer executing this PRD, it is proposing a new one.

- **The binding invariant** of §2.3: the only ciphertext ever subjected to threshold decryption is the final composed student. Any change that decrypts an intermediate aggregate, per-client logit ciphertext, or per-step ⟨Δ⟩ is a stable-core touch.
- **Multiparty CKKS at $t = N$.** Lowering $t$ admits the subtraction attack of §2.3; raising it is meaningless. The DKG / collective-key-switch structure of §2.2 is fixed.
- **Linear-accumulator construction** (per [[project-linear-accumulator]]): ⟨θ_E⟩ = ⟨θ_0*⟩ + Σ_t η · ⟨g_t⟩, with the student forward pass running on plaintext weights during training. Restoring a full encrypted forward+backward chain (the rejected version's protocol) is a stable-core touch.
- **α-vs-γ variant boundaries.** α keeps the probe plaintext server-side; γ keeps the probe encrypted end-to-end. Crossing these boundaries (e.g., partially decrypting γ's synthetic probe during training "for efficiency") is a stable-core touch.
- **Cryptographic regime.** CKKS at logN ∈ {14, 15}, scale ≈ 2^40, multiparty per Mouchet et al. Switching to BFV / BGV / TFHE, or to a non-multiparty single-key setup, is a stable-core touch.

### 9.5.2 Adjustable peripherals (agent may tweak with logged rationale)

These are tunable knobs whose values are arrived at through experimentation; the methodology survives wide variation across them.

| Peripheral | Default | Adjustable range |
|---|---|---|
| Probe size $\|\mathcal P\|$ | 5 000 | 2 000–10 000 if compute tight; report sensitivity at one cell |
| β | 2 | $\{1, 2, 4\}$; values requiring depth > log₂(4) = 2 mults are not tweakable |
| λ | 8 | $\{0, 4, 8, 16\}$; λ = 0 reduces to vanilla weighted-mean target |
| $E_1, E_2$ (warm-start, distill epochs) | 30, 200 | $E_1 \in [10, 50]$, $E_2 \in [100, 300]$; outside this needs justification |
| Number of seeds | 3 | 2 if compute is tight; 1 only with explicit caveat in §V |
| Dataset set | 5 (MNIST, FashionMNIST, SVHN, CIFAR-10, CIFAR-100) | Drop CIFAR-100 first under compute pressure, then SVHN; never drop MNIST or CIFAR-10 (the headline anchors) |
| α grid | $\{0.05, 0.1, 0.3\}$ | Drop α = 0.1 first; never drop α = 0.05 (the strong non-IID anchor) |
| Comparator set | 4 tier-1, 5 tier-2 | Drop tier-2 freely; one tier-1 may be dropped if upstream vendoring fails twice consecutively, replaced with the most recent untried tier-2 alternative in the same privacy regime |
| Student architecture | LeNet-5 (default), DeiT-tiny (A13 Phase B) | Add ResNet-18-poly or ViT-tiny if A13 projection supports; never run a student requiring > 50 M params under HE |
| DP-DDPM scope | per A5 conditional paths | Stay within Dockhorn-validated $(\varepsilon, \delta) \in \{(1, 10^{-5}), (10, 10^{-5})\}$ |
| N (client count) | 10 (headline); $\{5, 10, 20, 50\}$ (N-ablation) | Drop the 50-client cell first; never drop the 10-client headline |
| Library | TenSEAL (per A3 resolution) | Lattigo only if a stable-core operation needs bootstrapping; this should never happen under the linear-accumulator construction |
| sbatch chunk size | 8 h (Valar cap) | Smaller is fine; larger requires checkpoint-resume validation per A6 fold-in |

### 9.5.3 Reporting protocol — for every tweak applied

When an agent applies a peripheral tweak, it writes a one-page tweak report to `reports/2026-MM-DD_tweak_<short_slug>.md` with these fields:

- *Expected:* what the action-plan / PRD said.
- *Observed:* what actually happened (with timestamps, sbatch job IDs, stderr snippet, etc.).
- *Tweak:* the peripheral adjusted, old value → new value, with a pointer to its row in §9.5.2.
- *Justification:* why this value, why this peripheral and not another.
- *Plan impact:* which action(s) in `2026-05-10_tdsc_rejection_action_plan.md` are affected; timeline slip estimate (none / hours / days / weeks).
- *Cross-references:* link any related tweaks, escalations, or upstream issues.

A running index of all tweaks lives at `reports/decision_log.md` (append-only). This is the audit trail the cover letter cites for the "what we did during the resubmission" framing.

### 9.5.4 Escalation triggers — agent must halt and request user input

The agent does NOT proceed past any of these without explicit user confirmation:

- Any proposed change to the stable core (§9.5.1).
- Compute overrun > 50 % on a named action (e.g., A4.1 budgeted at 1 600 GPU-h actually projecting to 2 500+ GPU-h).
- Critical-path slip > 1 week.
- A4-sanity gate failure (gap < 2 pp; per §A4.4 of action plan).
- Number divergence > 3 pp from A10's working text (per A10 §replacement protocol).
- Both tier-1 DP comparators (FedDiff, FedKT) fail to reproduce — all DP-floor evidence is at risk.
- Linear-accumulator construction produces measurable divergence from plaintext student training > 5 % gradient norm at any layer (signals a bug, not a tweak).
- Any sbatch job submitted on the login node (golden rule violation; this is automatic-halt no exceptions).

### 9.5.5 Debug protocol — when an agent hits an unexpected error

Three-strike rule before escalation:

1. **Strike 1: the obvious fix.** Read the stack trace, fix the typo, re-run. Most errors die here.
2. **Strike 2: the documented fallback.** Each action in the action plan names its fallback (e.g., A3 → if TenSEAL precision drift, lower scale; A6 vendoring → if upstream commit broken, pin to last-known-working tag). Apply the fallback, re-run.
3. **Strike 3: the tweak.** If a peripheral adjustment per §9.5.2 dissolves the issue, apply it, log per §9.5.3, continue.

If three strikes fail, escalate (§9.5.4). Specific debugging conventions:

- *Numerical/training divergence:* always attempt bit-for-bit reproduction first (same seed, same env, same hardware). If that succeeds, suspect environment drift in the original run, not the methodology.
- *Checkpoint-resume failures:* trust the deterministic state-save protocol (per A6 / scripts/sbatch_resume_wrapper.sh) first; suspect random-seed drift second; suspect bug in user code third.
- *HE precision divergence:* check scale (2^40 default), check level chain (depth ≤ 3 must hold per linear-accumulator), check rotation key freshness, in that order.
- *Slurm-side failures:* TIMEOUT → checkpoint-resume issue; OUT_OF_MEMORY → reduce batch size (peripheral); REQUEUE → cluster-side preemption, not our problem, just verify checkpoint validity.

### 9.5.6 Decision log

`reports/decision_log.md` (to be created on first tweak) is an append-only ledger:

```
## 2026-MM-DD — A<n> — <short slug>

- Tweak: <peripheral> <old> → <new>
- Reason: <one sentence>
- Report: reports/2026-MM-DD_tweak_<slug>.md
- Impact: <none / hours / days / weeks>
```

The cover letter (§3 of `reports/cover_letter_draft.md`) cites this log as evidence of methodological transparency.

---

## 10. Open items, in priority order

Re-ordered 2026-05-17 to mirror the action-plan priority ladder (`reports/2026-05-10_tdsc_rejection_action_plan.md` §0).

1. **A4 (P1, headline).** Execute the §7.2 tri-axis accuracy / communication / time grid on Valar `t4_ai`; report $\Delta_{\text{HE}} \leq 1$ pp at every cell. This is the cover-letter's headline-contribution evidence. Authoring `jobs/cfd_v2_*.sh` is the gating sub-task.
2. **A3 (P2, calibration).** End-to-end CKKS run on a single cell with the linear-accumulator construction (§4.3); serves as anchor for the simulator-vs-real-HE gap claimed by A4. The A2 TenSEAL smoke (`prototypes/cfd_tenseal_smoke.py`, §8) is a prerequisite.
3. **A7 (P3, privacy evidence).** Membership-inference attack (LiRA + loss-threshold) on the decrypted student weights $\theta_E$. The resubmission needs a concrete MIA number to back the structural privacy argument.
4. **Text and figure work.** Methodology rewrite (A1), threat-model textual rewrite (A8), threat-model SVG (A11; see §2.7), abstract / §I-A rewrite (A10). Apply the §6 / §7 / §8 numbers to `FL_TDSC/methodology.tex` and `FL_TDSC/experiments.tex`. Log every textual change in `FL_TDSC/CHANGES.md` per the rule in §9.5.6 and the precedent set in §6 of that file.
5. **γ-variant (A5).** DP-DDPM profiling, then per-client generators, then γ cells in the A4 grid. Conditional on A4 leaving compute headroom; γ is the optional extension that distinguishes us from the public-probe-only baseline.
6. **Reference items.** Verifiable-HE citation (Viand SoK + a concrete vCKKS reference) added to `FL_TDSC/references.bib` and cited once in §threat-model. Deferred $(\varepsilon_T, \delta_T), (\varepsilon_P, \delta_P), (\varepsilon_G, \delta_G)$ decisions become defensible only once experimental utility numbers exist; the paper's claim is structural in the interim.

---

## Appendix A — Decisions log (this session)

### Locked
- Pivot from block-wise HE-IFD to encrypted CFD; paper acronym retained.
- Threat model (B): semi-honest server + up to $N{-}1$ semi-honest clients colluding.
- Multiparty CKKS, $t{=}N$ threshold decryption.
- Binding invariant: the only ciphertext ever threshold-decrypted is the final student.
- ε-variant (client-update Δθ aggregation) retained as legacy diagnostic only — violates the invariant under collusion.
- Co-Boosting reframed as the privacy-unaware ceiling.
- Verifiable HE: cited as future work via Viand–Knabenhans–Hithnawi 2023 (arXiv:2301.07041, "SoK: Fully Homomorphic Encryption Compilers and Verifiable Computation"). Not implemented.
- Model-poisoning attacks declared out of scope.
- Probe is public-by-construction in the headline; FedMD's 5000-sample convention is the principled basis.
- HE prototype scope: TenSEAL real-HE for short validation runs with per-step intermediate decryption; plaintext + calibrated Gaussian-noise-injection simulator for the headline grid. Simulator is calibrated against TenSEAL validation runs. No Lattigo, no end-to-end real-HE for the headline. Framing: "we proved the protocol is implementable and the noise model is calibrated to real HE; we simulate to exhaust the methodology space."
- Prototype is **parametric on student architecture**: a small model is the default for development, but the protocol code accepts any HE-compatible architecture so on-demand benchmarks are possible. Prototype reports three measurements: per-step plaintext-vs-HE divergence (correctness), wall-clock per phase (compute), and ciphertext bytes-on-wire per phase (communication). The compute and communication numbers feed §experiments directly.
- DP decision is empirical-driven (D4): headline grid runs **no-DP teachers + (P2)-toggle** so two numbers come out per cell. **DP-SGD teachers** are a separate small subset (MNIST $\alpha\in\{0.05,0.3\}$ + CIFAR-10 $\alpha=0.3$, 1 seed) to measure the actual utility tax. Final framing in the paper (headline vs. extension vs. discussion) is decided after the numbers exist. Headline is no-DP teachers per the user's call.
- γ-variant generator: **pixel-space DP-DDPM** per Dockhorn et al. TMLR 2022 (arXiv:2210.09929). $(\varepsilon_G, \delta_G)=(10, 10^{-5})$ headline, $(1, 10^{-5})$ ablation. $|\mathcal P_{\text{syn}}|=5000$, 500 synthetic samples per client at $N{=}10$. Budget composes as B1 (generator carries the DP budget; teachers non-DP). Reference impl: github.com/nv-tlabs/DPDM.

### Provisional (Claude-recommended; user has not signed off)
- Probe size fixed at $|\mathcal P| = 5000$ with no sweep.
- β handled via un-normalised aggregation + temperature absorption; λ via uniform-weight per-row variance.
- Two-stage init = plaintext supervised warm-start (Option I) for α; shared random seed for γ.
- DP defence parameters $(\varepsilon_T, \delta_T), (\varepsilon_P, \delta_P), (\varepsilon_G, \delta_G)$ deferred — paper claims structural admission only.
- Single shared $S$ released; client-side cheap fine-tuning to obtain $S_i$ documented as optional Phase 5.
- Phase 5 personalisation: **F2 — last-layer-only fine-tuning** (head only, freeze body). Recipe: 5 epochs, SGD lr=1e-3 momentum=0.9. Reported as a single ablation column at one $(N,\alpha)$ cell per dataset. $S_i$ stays on-device, never uploaded; leakage on $S_i$ reduces to leakage on $S$ by post-processing.
- Headline grid: 3 datasets × $N{=}10$ × 4 Dirichlet $\alpha$ × 5 variants × 3 seeds = 180 cells. $|\mathcal P|, \beta, \lambda, E_1, E_2$ fixed per §7.2.

### Still open — to be grilled

- Communication-complexity numbers: which CKKS parameters do we benchmark against for the per-ciphertext byte count? Defaults: $N_{\text{ring}}{=}2^{14}$, $\log_2 q \approx 438$, λ=128. Confirmed during prototype run.

### Closed
- Threat-model figure: simple plain **SVG**, single panel, minimal decoration. Two fills (client `#C6A87D`, server `#8B9EA8`), plain rectangles + arrows + text. File `FL_TDSC/figures/threat_model_v2.svg`. Convert to PDF via `rsvg-convert --format=pdf` at build time. No TikZ, no design-MCP detour.
