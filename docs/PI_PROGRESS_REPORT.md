# HE-IFD — Progress Report

*One-shot federated learning under multiparty homomorphic encryption.*
Prepared for the PIs. Status as of 2026-06-22. Numbers are from the runs in
`results/`; the membership-inference suite is in its final scoring pass and is
flagged where it appears.

---

## Part 1 — What the project is

### The setting

Several parties (hospitals, banks, phones) each hold private labelled data and
want one shared classifier without pooling the data. Standard federated
learning solves this but pays two recurring costs: it runs for tens to hundreds
of **rounds**, and every round discloses a fresh update computed on private
data, which is a documented leakage surface. **One-shot** FL removes the first
cost (a single upload and download), but not the second — a client's single
contribution still encodes its data. The field's two answers to that second
cost are unsatisfying at the extremes: send the contribution in the clear (no
privacy), or perturb it with **differential privacy** (a statistical guarantee
bought with an accuracy loss in the released model).

We take the third route — **homomorphic encryption (HE)** — but in a form that
makes it cheap. The key observation is that an HE server is *blind*: it
computes on ciphertexts, so it cannot branch on a value, cannot run
data-dependent control flow, and each multiplication spends a finite noise
budget. The only thing it can afford at scale is a **fixed, shallow, linear**
operation. So we design the protocol around exactly that.

### The method

- Every client uses the **same frozen public pretrained backbone** (e.g.
  RoBERTa, ViT) and trains only a small **low-rank adapter (LoRA) plus a
  classifier head**, starting from a shared public initialization θ₀. The
  backbone is never trained, never transmitted, never encrypted.
- Each client fine-tunes its small unit on its own data for a **bounded number
  of steps** and uploads only the encrypted **displacement** Δⱼ = θⱼ − θ₀.
- The server computes one **sample-weighted linear combination**
  θ⋆ = θ₀ + Σⱼ wⱼ·Δⱼ entirely under **multiparty CKKS** — only
  plaintext-scalar × ciphertext and ciphertext additions, **multiplicative
  depth one, no bootstrapping**. A threshold of clients then jointly decrypts
  the result. One upload, one download.

Why a linear server step is enough: a weighted average of independently trained
models is only meaningful if the models share a frame. A frozen pretrained
backbone *supplies that frame for free* — every client starts its small unit
from the same θ₀ and moves only a little, so the displacements live in one
coordinate system and add constructively instead of cancelling. This is also
why we fine-tune rather than train from scratch: from-scratch has no shared
frame and would need the multi-round or server-side computation that HE
forbids. Algebraically the aggregation is **task arithmetic** (task-vector
merging); the contribution is the one-shot encrypted protocol that makes it
work and makes it cheap.

### The privacy argument

The client contributions are protected **cryptographically, with no
perturbation and no accuracy cost** — under multiparty CKKS the server and any
sub-threshold coalition of clients see only ciphertexts (we give a standard
simulation/IND-CPA argument). Because there is **no alignment phase**, no
data-derived quantity ever leaves a client before encryption. The *one* object
revealed in the clear is the final shared model, which any protocol that hands
parties a joint model must reveal; its residual leakage we **measure** with
membership inference rather than assert.

### The experimental program

Datasets span four text classification tasks of growing label space — AG-News
(4 classes), TREC (6), DBpedia (14), Banking77 (77) — on frozen RoBERTa, plus a
vision arm (CIFAR-10/100, Tiny-ImageNet on a frozen ViT-B/16) and a
billion-parameter-class language model (Qwen2.5-0.5B). Data are split across
clients by a Dirichlet(α) label partition (smaller α = more skew). We report,
against a **centralized** ceiling (the same model fine-tuned on the pooled
data): the accuracy of the released model, its lift over a frozen-feature
linear probe, and the gap to centralized — over heterogeneity α, client count
N, and trajectory length K, at three seeds. The cryptography is **not
simulated**: the full protocol (key-gen → encrypt → aggregate → threshold
decrypt) runs end-to-end in **Lattigo** and is checked against the plaintext
result.

### Context

This is a resubmission. The previous version (rejected from IEEE TDSC) trained
the model *under* encryption with polynomial activations — the source of its
accuracy loss, ~hundreds-of-GB uploads, and instability at higher client
counts. The current method does **no training under encryption**: it moves all
learning to the clients in plaintext and leaves the server a single depth-one
linear sum. This directly answers the prior reviewers' main complaints (upload
size, accuracy cost of the crypto, NLP coverage, end-to-end CKKS measurement).

---

## Part 2 — What we achieved newly (this work period)

Everything in this part is **new since the last checkpoint**. The starting
point was a working-but-fragile pipeline whose central claim was actually
**false as stated** and whose headline numbers were unstable. We diagnosed
that, fixed it, and turned the fix into three new contributions, all validated
on the cluster.

### 2.1 We found and fixed a broken central claim (the bilinearity bug)

The paper's spine was "the encrypted aggregation is *linear* in the transmitted
quantities, i.e. exact task arithmetic." For standard LoRA where **both**
factors A and B are trained, this is **mathematically false**: averaging A's and
B's separately does not average the weight updates BᵢAᵢ (the product is
bilinear). The symptom was visible in the data as **catastrophic seed
collapses** under heterogeneity (e.g. AG-News dropping to 0.27–0.31 on one
seed), which made reported means meaningless.

**Fix:** we freeze the LoRA down-projection A at its shared public init and
train only B (+head) — *FFA-LoRA* style. Then Σⱼ wⱼ·Bⱼ·A₀ = Σⱼ wⱼ·ΔWⱼ
**exactly**, so the linear/task-arithmetic claim becomes literally true, the
encrypted payload **halves**, and the merge is stable. Confirmed head-to-head
(vote-selected accuracy, 3 seeds):

| task | both-A-B (old) | freeze-A (new) |
|---|---|---|
| AG-News | 0.68 ± 0.15 | **0.75 ± 0.09** |
| TREC | 0.57 ± 0.13 | **0.72 ± 0.05** |

Freeze-A wins on mean **and** cuts seed variance 2–3×, and the gain concentrates
exactly on the high-conflict collapse seeds (0.65 vs 0.48). This is now a clean,
true claim instead of a refutable one — and it is *cited*, not claimed as ours
(FFA-LoRA, ICLR 2024); our novelty is what it buys under one-shot encryption.

### 2.2 We turned aggregation into a new protocol contribution: encrypted multi-candidate release with client-vote selection

A blind server cannot adapt the aggregation rule to the data — encryption
removes exactly that adaptivity. We restore it **after decryption, at zero extra
HE cost**. Because every useful aggregation rule is itself linear, the server
emits **several depth-one candidate aggregates** in one pass:

- a **λ-scaling** family (θ₀ + λ·Σwⱼ·Δⱼ);
- **Fisher-** and **coverage-(class-count-)weighted** merges, computed at depth
  one via a **numerator/denominator trick** (clients upload Enc(F⊙Δ) and Enc(F);
  the server only adds; clients decrypt both and divide in plaintext);
- **leave-one-out** aggregates.

The clients jointly decrypt the candidates and **select by a sample-weighted
vote on their local holdouts**. Findings across the 39-cell program:

- **The vote picks the test-best candidate in 34/39 cells** (4 of 5 misses cost
  ≤2 points). No *single fixed* rule wins everywhere (count-head best in 28/39,
  Fisher in 10/39) — the vote, not any one rule, is the robust choice.
- Under severe skew (α=0.1) the vote-selected model beats the plain weighted
  average by **+24 (AG-News), +21 (TREC), +13 (DBpedia), +38 (Banking77)**
  points.
- We found **no prior work doing multi-candidate threshold decryption +
  post-decryption selection in HE-FL** — this is a clean, novel protocol
  element (with an explicit leakage accounting: the λ family reveals nothing
  beyond θ⋆; leave-one-out exposes per-client contributions to *participants*,
  which our threat model permits and we state).

This also reframes a result we previously believed: deep conflict-resolving
merges were thought unnecessary; under freeze-A at severe skew they **do** help,
and the vote captures that gain automatically.

### 2.3 We closed the hardest accuracy gap (coverage under extreme skew)

The single linear aggregate's known weakness is the **coverage gap**: a client
contributes signal for a class only if it holds examples of it, so under extreme
label skew + many classes the shared head is under-covered. On **Banking77 (77
classes, α=0.1)** the gap to centralized was **0.52**. With freeze-A +
coverage-weighted (count-head) aggregation + the vote, the released model reaches
**0.77 (gap 0.11)** — the gap is **cut from 0.52 to 0.11** with no extra
communication and no privacy spend. DBpedia reaches **0.94** (within 0.05 of
centralized) at K=400.

### 2.4 We fixed the vision arm (was a negative result)

Under the old both-A-B method, the vision row was *embarrassing*: on CIFAR-100
the adapter added **−0.01** over a linear probe (i.e. nothing). Under the new
method the **CIFAR-100 arm is positive**: **0.78 selected vs 0.87 centralized**,
a real lift, restoring the "works across vision and language" claim with
evidence instead of an asterisk.

### 2.5 We ran matched-setup comparisons (answering a prior-rejection complaint)

Reviewers objected that we compared our numbers at our setup against others'
numbers at their setups. We now run HE-IFD at the **published partitions** of
the comparator papers (same dataset, client count, Dirichlet α — model class is
ours, a frozen ViT + adapter, which we state):

| matched setup | our released model | their reported number |
|---|---|---|
| CIFAR-10, N=5 (DENSE, NeurIPS'22) | **0.96** | 0.50 (α=0.1) / 0.60 (α=0.3) |
| CIFAR-10, N=20, α=0.04 (FedAUXfdp, DP) | **0.94** | 0.75 (CIFAR-10, ε=0.5) |
| Tiny-ImageNet, N=10, α=0.1 (FedSD2C, NeurIPS'24) | **0.73** | (FedSD2C's reported TIN range) |

(α=0.16 FedAUXfdp cell finishing.) The comparison favors us at the matched
partition, with cryptographic — not lossy — privacy.

### 2.6 We demonstrated it at billion-parameter-class scale

The protocol carries to a frozen **Qwen2.5-0.5B** causal LM (freeze-A LoRA +
head, one-shot): DBpedia reaches **0.87–0.88** (selected) where the plain
average collapses to 0.44, AG-News **0.71–0.72**. The encrypted object stays
tiny — **26 ciphertexts (13 MiB)** — because only the adapter is encrypted, not
the 0.5B backbone. This shows the cost is set by the adapter, not the model
behind it.

### 2.7 We re-measured the real cryptographic cost (end-to-end Lattigo)

At the *actual* freeze-A payload (≈150k trainable parameters), measured in
multiparty CKKS:

- **19 ciphertexts, 9.5 MiB per client** — **half** the old both-A-B object —
  in **one** round.
- Server aggregation **76 ms** (N=10) to **0.72 s** (N=100); threshold decrypt
  **44 ms** to **0.43 s**; client encrypt **40 ms**. **No bootstrapping.**
- Decrypted result matches plaintext to relative ℓ₂ **≈10⁻⁹** (depth-one ⇒ no
  error amplification).
- Multi-candidate release costs *k* threshold decryptions, linear: a 12-candidate
  set adds ~0.5 s total.
- Contrast: encrypting the full RoBERTa backbone would move ~7.5 GiB/client/round
  over many rounds (POSEIDON-class); the closest current adapter-HE work
  (SHE-LoRA, ICLR'26) is multi-round and inherits the bilinear aggregation noise
  that freeze-A removes.

### 2.8 We grounded the privacy claim in measurement (membership inference)

The prior version *asserted* the released model leaks little. We are now
**measuring** it on the freeze-A released model with shadow-model attacks
(loss-threshold + LiRA) under both an **external** adversary and a
**fellow-client** adversary (the participant who holds its own data as a
prior — the strongest adversary our threat model admits). First scored cell
(AG-News): attack AUC **0.49–0.51** (chance) and **TPR ≈ 1% at 1% FPR** (no
better than random) for *both* adversaries. *The remaining 11 cells are in
their final scoring pass on the cluster; the full table lands shortly and will
be folded in.*

### 2.9 We re-positioned the paper against the 2026 literature

A field scan settled the claim precisely. "First one-shot federated
fine-tuning" is **taken** (one-round FM fine-tuning, arXiv:2412.04650), and
freeze-A is FFA-LoRA's — but **"the first one-shot federated *learning* protocol
under multiparty homomorphic encryption"** is open and defensible: all HE-FL is
multi-round, all one-shot FL is plaintext or DP. The co-design argument
(freeze-A makes the single encrypted aggregate exact and depth-one) and the
multi-candidate release are both unoccupied. Related-work paragraphs, the
revised claim, and the multi-candidate section are drafted
(`docs/paper/drafts/`).

**Net:** the method is now internally consistent (the central claim is true),
materially stronger (collapse seeds fixed, coverage gap cut 0.52→0.11, vision
arm positive, half the payload), broader (LLM scale, matched comparators), and
its privacy claim is measured rather than asserted.

---

## Part 3 — Where we can submit

The work sits at *federated learning × applied cryptography (HE) × efficient
fine-tuning*. Calibrated options:

### Strongest fit — security/privacy journals (HE + measured privacy)
- **IEEE TNSE** (Transactions on Network Science and Engineering) — the current
  target; in progress. Accepts FL+crypto systems work.
- **IEEE TIFS** (Transactions on Information Forensics and Security) — arguably
  the *best* fit: HE + membership-inference measurement + threat model is
  squarely its scope.
- **IEEE TDSC** (Transactions on Dependable and Secure Computing) — natural home
  for the threat model + HE protocol; note this is where v1 was rejected (shared
  reviewer pool is a risk, but the method is now substantially different).
- **PoPETs / PETS** (Proceedings on Privacy Enhancing Technologies) — excellent
  fit for the privacy-by-construction + MIA story; rolling deadlines, fast.

### Strong fit — top security conferences (higher bar, higher prestige)
- **USENIX Security**, **ACM CCS**, **NDSS**, **IEEE S&P** — the one-shot-HE
  protocol + end-to-end Lattigo + MIA is conference-shaped; these reward a clean
  novel protocol with real crypto measurement. NDSS/USENIX have the friendliest
  cadence.

### Plausible — systems / distributed
- **IEEE TPDS** (Parallel & Distributed Systems), **ACM TOPS** — if framed as an
  efficient distributed protocol.

### Possible — ML venues (crypto angle valued less, but FL+efficiency lands)
- **NeurIPS / ICML / ICLR** — the freeze-A co-design + multi-candidate
  selection + one-shot FT story is ML-publishable; the HE depth argument would
  need to be made accessible. **TMLR** is a good lower-variance option for the
  method+analysis framing.

**Recommendation.** Keep IEEE TNSE as the in-flight submission. If repositioning
is on the table, **IEEE TIFS** or **PoPETs** are the best-matched homes for the
"cryptographic privacy, measured, at one-shot cost" framing; **NDSS/USENIX** if
the group wants to aim the novel protocol at a top conference.
