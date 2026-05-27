# HE-IFD: One-Shot Federated Distillation under Multiparty Homomorphic Encryption — Methodology

## 1. Setting and threat model

We consider $N$ clients holding private labelled datasets $\mathcal{D}_1, \dots, \mathcal{D}_N$ over a common label space $\mathcal{Y} = \{1, \dots, C\}$. Local label distributions are non-IID and severely heterogeneous: in our experiments, partitions are sampled from a Dirichlet prior $\mathrm{Dir}(\alpha)$ with $\alpha \in \{0.05, 0.1, 0.3, 1.0\}$, so at $\alpha = 0.05$ each client typically sees only one or two classes. A semi-honest central server orchestrates the protocol and learns nothing about the clients' data beyond what is leaked by the final decrypted student model. All cryptographic operations use the multiparty CKKS scheme: a distributed key-generation (DKG) protocol produces a public encryption key whose corresponding decryption key is threshold-shared among the clients, so no individual party (server included) can decrypt ciphertexts. Decryption requires the collaboration of a threshold of honest clients.

In addition to cryptographic privacy, we optionally provide an information-theoretic privacy guarantee: client contributions to the public alignment step (Phase 0) can be released under Gaussian differential privacy with parameters $(\varepsilon, \delta)$. This protects against an adversary who eventually obtains the decrypted student, since the only client-specific signals that influence the released model under encryption are aggregated, and the only client-specific signals that are released in the clear (Phase 0 prototypes) can carry a calibrated DP guarantee.

The deployment we target is one-shot: each client performs all of its local computation in a single block, uploads a single encrypted message, and the server returns a single decrypted aggregate. Multi-round federated optimisation is explicitly out of scope.

## 2. Why this is HE-friendly

A naïve approach to encrypted federated distillation runs the student's forward pass under HE, which forces polynomial activations, restricts depth via the modulus budget, and ties the architecture to whatever the CKKS multiplicative depth allows. We deliberately avoid this. In our protocol the encrypted unit is the *parameters* of the student model, not its forward pass. The server's only cryptographic operation is a sample-weighted linear combination of client weight tensors — plaintext scalars multiplied by ciphertext tensors plus ciphertext-ciphertext additions — which consumes essentially no multiplicative budget and imposes no constraint whatsoever on the student's architecture. Consequently the student can be a standard MLP, CNN, ResNet, or transformer head with ReLU, GELU, softmax, and any other non-polynomial activations.

The trade-off is that *distillation itself runs in plaintext, locally on each client*, using each client's own teacher and the public probe. We argue, and our experiments confirm, that this is the right place to spend plaintext compute: it is the step that requires the most non-linear operations per parameter, and it is the step that benefits most from architecture freedom.

## 3. End-to-end pipeline

The protocol has three stages, executed in order:

**Stage 1 — Local teacher training (plaintext, client-side).** Each client $i$ trains a local teacher $T_i$ on $\mathcal{D}_i$ by standard supervised SGD. The teacher's architecture is chosen by the deployment: for pretrained-backbone experiments we use a frozen backbone (ResNet-18, ViT-B/32, DistilBERT, GPT-2-small) with a trainable linear head; for from-scratch experiments we use a small MLP. Hyperparameters: learning rate $0.05$, 5 warmup epochs, batch size 128.

**Stage 2 — Phase 0 alignment (plaintext, client-to-client).** Each client computes per-class feature prototypes from its teacher and exchanges them with the other clients, optionally under DP. This is the only step that leaks any client-specific signal in the clear; everything afterwards is either local or encrypted.

**Stage 3 — Local distillation (plaintext, client-side) and encrypted aggregation (server-side).** Using its local teacher, the (possibly DP-noised) prototypes received from other clients, and a small public labelled probe $P$, each client distills a student $S_i$ by $K = 300$ steps of SGD on an augmented probe constructed from real probe samples and synthetic prototype samples. Each client then encrypts its final student weights $W_i^S$ under the joint CKKS public key and uploads $\mathrm{CT}(W_i^S)$. The server computes the sample-weighted aggregate $\mathrm{CT}\!\left(\sum_i \frac{n_i}{\sum_j n_j} W_i^S\right)$ using only plaintext-times-ciphertext multiplications and ciphertext additions, then the clients jointly run threshold decryption on the result to recover the final student $W^S$.

The student trained in Stage 3 is, by construction, the same architecture across clients (only the parameter values differ), which is what makes Stage 3 aggregation linear and HE-friendly.

## 4. Phase 0 alignment in detail

The motivation is structural. At $\alpha = 0.05$ each client sees one or two classes, so its local teacher is competent on those classes but produces meaningless logits on the rest. Distilling such a teacher into a global student on a small public probe collapses the student onto whichever classes happen to dominate the probe, regardless of the client's own data. The probe alone is not enough: the student needs *some* signal about classes the local teacher cannot reach. Phase 0 supplies that signal in a controlled form.

For client $i$ with teacher $T_i$, the prototypes are computed as follows. Let $\phi_i(\cdot)$ denote $T_i$'s penultimate feature map (for pretrained backbones this is the frozen-backbone embedding; for the from-scratch MLP it is the pre-softmax representation). For each class $c$ that client $i$ has at least $K_{\text{pc}}$ examples of (we set $K_{\text{pc}} = 20$), the client computes the mean
$$
\mu_{i,c} = \frac{1}{K_{\text{pc}}} \sum_{k=1}^{K_{\text{pc}}} \phi_i(x_{i,c,k}),
$$
where $\{x_{i,c,k}\}$ is a random subset of $\mathcal{D}_i$ restricted to class $c$. Clients without enough class-$c$ examples produce no class-$c$ prototype. The set $\{\mu_{i,c}\}_{i,c}$ is exchanged among clients.

Each receiving client $j$ then constructs an *augmented probe* by treating each received $\mu_{i,c}$ as a synthetic feature-space example with label $c$. During local distillation, $j$'s student is trained jointly on real probe examples (feature-mapped through $\phi_j$ for consistency) and the synthetic prototypes, with the distillation loss treating both uniformly. The student therefore sees per-class anchors from every region of feature space that some client has covered, not just the regions $j$ itself covers.

We refer to two specific variants of Phase 0 in the experiments: `raw_union_K20`, in which prototypes are exchanged without noise; and `dp_avg_eps2_K20`, `dp_avg_eps8_K20`, in which prototypes are released under Gaussian DP as described in §6. The qualifier *avg* refers to the averaging-variant accounting (as opposed to a per-example union bound) and is the design choice that makes DP at strict $\varepsilon$ usable.

## 5. Local distillation

Each client distills its student $S_i$ on the augmented probe. The student initialisation is identical across clients (deterministic from a seed), which is important because aggregation is linear and assumes a shared parameter coordinate frame. For the pretrained-backbone setups we train only the linear classification head ($K_{\text{tail}} = 1$), which has $\sim$5–8K parameters depending on the backbone — small enough to fit in a single CKKS ciphertext at standard parameters. For the from-scratch MLP we train the full network (still small, $\sim$60K parameters).

The local distillation loss for a probe example $(x, y)$ is the standard Hinton form:
$$
\mathcal{L}_i(x, y) = (1 - \lambda)\,\mathrm{CE}\!\left(S_i(x), y\right) + \lambda\,\tau^2\,\mathrm{KL}\!\left(\sigma(T_i(x)/\tau)\,\Big\|\,\sigma(S_i(x)/\tau)\right),
$$
with $\tau = 4.0$ and $\lambda$ scheduled from 0 (pure CE during warmup) to 1.0 (pure KD) over 5 epochs. The student learning rate is $0.01$ with cosine decay over $K = 300$ steps. Synthetic prototype examples are treated identically to real probe examples in the loss; the only difference is that for synthetic examples $x$ is already in feature space, so the forward pass skips the embedding step.

The "warmup-only" baseline in our experiments corresponds to running this same procedure with $\lambda$ held at $0$ for all steps and the probe restricted to the public labelled probe (no prototypes). This isolates the protocol's contribution: any improvement over warmup-only is attributable specifically to (a) Phase 0 prototype injection and (b) distillation from a heterogeneous mixture of teachers.

## 6. Encrypted aggregation

After Stage 3, each client holds a plaintext student $W_i^S \in \mathbb{R}^d$ (where $d$ is the number of trainable parameters, $\sim$5K–60K in our experiments). The client packs $W_i^S$ into a single CKKS ciphertext under the joint public key and uploads $\mathrm{CT}(W_i^S)$.

The server's aggregation step is purely linear:
$$
\mathrm{CT}(W^S_{\text{agg}}) = \sum_{i=1}^{N} \omega_i \cdot \mathrm{CT}(W_i^S), \qquad \omega_i = \frac{n_i}{\sum_j n_j},
$$
where each $\omega_i$ is a plaintext scalar (the server knows dataset cardinalities, which we treat as public metadata; if cardinalities must also be hidden, they can be encrypted at negligible cost). This computation uses only plaintext-ciphertext multiplications and ciphertext-ciphertext additions, both of which are cheap and consume one level of multiplicative budget total. We use CKKS parameters $(N_{\text{ring}} = 2^{14}, \log Q \approx 218)$ throughout, which give comfortable headroom for the linear combination plus any future post-processing.

The aggregated ciphertext is then jointly decrypted by a threshold of clients under the multiparty protocol, producing the plaintext final student $W^S_{\text{agg}}$. This student is what we report accuracy on.

A practical point worth noting: because the protocol is one-shot, the entire encrypted message a client sends is *one* ciphertext (the student head, $\sim$5–8K parameters for pretrained-backbone setups). At standard CKKS parameters, this is roughly 200–400 KB per client, which is negligible compared to a single round of standard federated averaging on a full model.

### Why deltas vs. final weights are interchangeable

In several of our development runs we encrypted per-step weight *deltas* and aggregated them on the server with a plaintext schedule, then applied the aggregate to a shared initialisation. This is mathematically equivalent to aggregating final weights when the schedule is linear in client contributions, which it is in our protocol. We settled on encrypting final weights because it minimises the number of ciphertexts in flight without changing the result.

## 7. Differential privacy: the averaging variant

Phase 0 is the only stage that releases client-specific information in the clear (encryption protects Stage 3). We therefore add Gaussian DP at Phase 0. The naïve approach — treating each prototype $\mu_{i,c}$ as the unit of release and clipping at the per-example feature norm — leads to a catastrophic noise level at strict $\varepsilon$, because the L2 sensitivity of releasing $K_{\text{pc}}$ feature vectors under a union bound is $K_{\text{pc}} \cdot C_{\text{clip}}$, and the noise scales linearly with sensitivity. We instead use an averaging-variant accounting that exploits the fact that the released quantity is already a *mean*, not a sum or a set.

Let $\phi(x)$ be the feature map, and assume $\|\phi(x)\|_2 \le C_{\text{clip}}$ for all $x$ (we enforce this in practice by per-example clipping at a backbone-specific quantile of the empirical feature-norm distribution: $C_{\text{clip}} \in \{32.75, 52.86, 8.56, 240.20\}$ for ResNet-18, ViT-B/32, DistilBERT, and GPT-2-small respectively, chosen at the 95th percentile of training feature norms). The released prototype is
$$
\tilde{\mu}_{i,c} = \frac{1}{K_{\text{pc}}} \sum_{k=1}^{K_{\text{pc}}} \phi(x_{i,c,k}) + \mathcal{N}\!\left(0, \sigma^2 I\right).
$$
Changing one example $x_{i,c,k}$ in the underlying dataset changes the mean by at most $\frac{2 C_{\text{clip}}}{K_{\text{pc}}}$ in L2 (the factor of 2 accounts for replacement; for add/remove the factor is 1, and we use 2 to be conservative). So the L2 sensitivity of releasing one prototype is
$$
\Delta_{\text{proto}} = \frac{2 C_{\text{clip}}}{K_{\text{pc}}}.
$$
For a Gaussian mechanism at $(\varepsilon, \delta)$ per prototype, the noise standard deviation is
$$
\sigma = \frac{\Delta_{\text{proto}} \sqrt{2 \ln(1.25/\delta)}}{\varepsilon} = \frac{2 C_{\text{clip}} \sqrt{2 \ln(1.25/\delta)}}{K_{\text{pc}}\,\varepsilon}.
$$
A client releases at most $C$ prototypes (one per class it covers), so the total privacy cost per client is bounded by the composition of $C$ Gaussian mechanisms. We use Rényi DP composition to convert this to a final $(\varepsilon, \delta)$ guarantee per client. In practice, with $\delta = 10^{-5}$ and the per-prototype $\varepsilon \in \{0.5, 2, 8, 32\}$ that we report, the composed-per-client $\varepsilon$ is within a small constant factor (the RDP tradeoff is favourable because each release has small enough sensitivity that the privacy loss random variable is concentrated).

The averaging variant is what makes DP practically usable here. Under union accounting at $K_{\text{pc}} = 20$, the sensitivity is $K_{\text{pc}}$ times larger and the noise destroys the signal at $\varepsilon \le 8$. Under averaging accounting, the same $K_{\text{pc}} = 20$ shrinks the sensitivity by a factor of $K_{\text{pc}}$ and the DP frontier becomes flat from $\varepsilon \approx 2$ onward in our experiments.

### Server-side averaging across clients further reduces noise

A subtlety: after $N$ clients each release a noisy prototype for class $c$, the receiving client $j$ averages them, $\bar{\mu}_c = \frac{1}{N_c} \sum_{i \in S_c} \tilde{\mu}_{i,c}$, where $N_c$ is the number of clients that have class $c$. This averaging reduces the noise variance by a factor of $N_c$ in the prototype actually used for distillation, without changing the per-client DP guarantee. So the *utility* of Phase 0 under DP improves as more clients participate, which is the right scaling for a federated protocol.

## 8. One-shot suffices because the backbone is pretrained

A central design choice is to freeze a publicly available pretrained backbone and train only the classification head ($K_{\text{tail}} = 1$). This is the deployment we believe will dominate in practice: practitioners have access to strong open-weight backbones (ViT, DistilBERT, ResNet, and so on), and the federated learning problem reduces to learning a head on top of them. With a frozen backbone, the trainable parameters fit in a single ciphertext, the local distillation step is fast, and one round of communication is enough — the head is small enough that a single aggregate is the right granularity. The from-scratch MLP experiments on MNIST exist to verify that the protocol still functions when there is no pretrained representation; they are not the intended deployment.

This is also why we report Section A (MLP from scratch) and Section B/C (pretrained backbones) separately: they answer different questions. Section A asks whether the protocol contributes anything beyond a labelled probe in the worst case; Section B/C asks how much it contributes in the realistic case.

## 9. Comparison to the original TNSE design

For completeness, the original TNSE draft of this work ran encrypted *intermediate-feature* distillation in which the student's forward pass was evaluated under HE on encrypted client features. This required polynomial activation approximations, depth-budget management across the student's layers, and ciphertext-level packing tricks for hidden activations. It scaled poorly: a small student with polynomial activations gives up several accuracy points relative to ReLU, and depth was bounded by the multiplicative budget rather than by the problem.

The redesign in this paper moves all non-linear work to plaintext local distillation and reserves encryption for a single linear aggregation of student weights. This removes every constraint the original design imposed on the student architecture and gives back the accuracy lost to polynomial activations, while preserving the cryptographic privacy property that the server never sees any client's data, features, or teacher. The one-shot, pretrained-backbone deployment is what makes this redesign attractive: a single linear aggregation of small heads is enough to recover most of the centralised-training accuracy across all backbones we tested.

## 10. Hyperparameters and reproducibility

For all experiments we use $N = 16$ clients, $K = 300$ local distillation steps, $\tau = 4.0$, student LR $= 0.01$ (cosine), teacher LR $= 0.05$ (5 warmup epochs), $K_{\text{pc}} = 20$ prototypes per class, $\delta = 10^{-5}$, and clipping at the 95th-percentile feature norm of the training data for each backbone. Each cell in the experiments is replicated across 3 seeds (42, 43, 44) and we report mean ± standard deviation. The full hyperparameter table and per-run results are released alongside the paper.

---

## A. Notation summary

| Symbol | Meaning |
|---|---|
| $N$ | number of clients |
| $\alpha$ | Dirichlet concentration of label heterogeneity |
| $\mathcal{D}_i$, $n_i$ | local dataset and its size for client $i$ |
| $C$ | number of classes |
| $T_i$, $S_i$ | local teacher and student of client $i$ |
| $W_i^S$ | parameters of student $S_i$ |
| $\phi_i(\cdot)$ | penultimate feature map of teacher $T_i$ |
| $\mu_{i,c}$ | mean feature prototype of class $c$ at client $i$ |
| $K_{\text{pc}}$ | examples per class used to compute one prototype (= 20) |
| $K$ | local distillation steps (= 300) |
| $K_{\text{tail}}$ | number of trainable tail layers (= 1 for pretrained, full network for from-scratch) |
| $\tau$ | distillation temperature (= 4.0) |
| $C_{\text{clip}}$ | feature-norm clipping bound (backbone-specific, 95th percentile) |
| $\varepsilon, \delta$ | DP parameters (per-prototype $\varepsilon$ as reported, $\delta = 10^{-5}$) |
| $\sigma$ | Gaussian DP noise std, $\sigma = 2 C_{\text{clip}} \sqrt{2 \ln(1.25/\delta)} / (K_{\text{pc}} \varepsilon)$ |
| $P$ | size of the public labelled probe (∈ {25, 100, 500} in Section A) |
| CT(·) | CKKS ciphertext under the joint public key |