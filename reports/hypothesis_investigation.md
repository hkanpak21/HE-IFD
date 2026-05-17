# HE-IFD Methodology Investigation
## Variance Reduction & Accuracy Improvement Analysis

---

## 1. Motivation and Problem Framing

### Current Best Results (Improved Protocol v3 — teacher-input + trainable bridges + server refinement)

| Config | N | α | Mean Teacher | Best Teacher | Student | vs Mean | vs Best |
|--------|---|---|-------------|-------------|---------|---------|---------|
| n4_a05 | 4 | 0.5 | 69.3% | 81.9% | **79.65%** | +10.3% | −2.3% |
| n4_a10 | 4 | 1.0 | 78.0% | 86.5% | **79.93%** | +1.9% | −6.6% |
| n16_a05 | 16 | 0.5 | 43.3% | 54.8% | **60.13%** | +16.8% | **+5.3%** |
| n16_a10 | 16 | 1.0 | 50.3% | 66.1% | **60.05%** | +9.8% | −6.0% |

**Key observation**: The student *already surpasses the best teacher* for N=16 α=0.5 (+5.3%). For N=4 and N=16 α=1.0, it falls short by 2-7%. The pattern shows the student benefits most from ensembling when teachers are weak and diverse — but struggles when there's a single strong teacher dominating.

### The Variance Problem

In non-IID Dirichlet partitioning, teacher quality varies significantly:

| Config | Teacher Accs | Std |
|--------|-------------|-----|
| n4 α=0.5 | [81.9, 60.5, 64.7, 70.3] | 8.1 |
| n4 α=1.0 | [81.1, 86.5, 83.1, 61.4] | 11.3 |
| n16 α=0.5 | [36-55%] spread | 4.8 |
| n16 α=1.0 | [36-66%] spread | 9.7 |

**Current protocol**: uniform aggregation — each teacher's features have equal weight regardless of accuracy. A teacher with 60% accuracy contributes the same signal as one with 86%.

---

## 2. Why We Cannot Match Plaintext Distillation — Fundamental Bottlenecks

### B1: Polynomial Activation Expressiveness Gap
**LearnablePolyAct**: `f(x) = ax² + bx + c` (degree 2, 3 parameters per activation)

ReLU is not polynomial-approximable efficiently with degree 2. The quadratic can approximate ReLU locally but fails at the tails — it grows unboundedly, causing the "escaping activation problem" (Garimella et al., SISYPHUS). The degree-2 approximation introduces systematic bias in feature representations.

**Gap estimate**: IBM PolyKD (arXiv 2111.03362) reports 0.32–5.3% accuracy drop from ReLU→degree-2 poly on ResNet-18, under ideal training conditions (not federated/distillation).

### B2: ChannelScale vs BatchNorm
**BatchNorm** adapts dynamically to batch statistics, normalising internal activations and effectively increasing the effective learning rate. **ChannelScale** is a static per-channel scale/shift — it cannot normalise away covariate shift during training.

In our multi-client setting, this is especially severe: teacher features from different clients have different distributions, and ChannelScale cannot compensate for this dynamically.

### B3: Block-Independent Training — Sub-Optimal Global Objective
Each block is trained to minimise its local feature reconstruction loss (NormMSE). This does not minimise the final classification loss. A block may learn a locally-optimal feature representation that prevents the downstream block from achieving its best output.

Refinement (Phase 2b) partially fixes this by adapting blocks to the actual chain, but it only runs for 30 epochs per block and cannot fully undo the suboptimal initial representations.

### B4: Feature-Space vs Prediction-Space Supervision
We supervise at intermediate feature layers (block outputs), not at the final prediction (logit/softmax). Features are the teacher's *internal* representation, not its decision boundary. The student learns to mimic teacher *representations*, but the relationship between representations and final accuracy is indirect.

In contrast, soft-label distillation (e.g., FedDF) directly trains on teacher predictions — the signal is closer to the actual objective. However, soft labels expose private information (as documented in background.tex, sections 3.3 and 3.4), making them unsuitable in our privacy model.

### B5: Ensemble Quality Ceiling
In the current protocol, the distillation target at each layer is the **concatenation** of all teacher features. If teachers are heterogeneous (non-IID), this mixture contains contradictory feature representations for the same input patterns.

Example: for the class "automobile", client A (who saw many automobiles) has highly discriminative automobile features at layer3. Client B (who saw few automobiles) has generic/confused automobile features at layer3. Training the student on both simultaneously introduces contradictory supervision for automobile-related samples.

---

## 3. Hypotheses and Experimental Design

### H1: Quality-Weighted Loss (QWL)
**Hypothesis**: Weighting each sample's training loss by its teacher's overall accuracy reduces noise from weak teachers.

**Motivation**: Teacher k with accuracy $a_k$ contributes noisy features for classes it rarely saw. Upweighting strong teachers' samples (weight ∝ $a_k$) concentrates the distillation signal on reliable feature representations.

**Implementation**: `w_i = acc_{teacher(i)} / Σ_k acc_k` (linear quality weights)

**Expected gain**: +1-2% for N=4, +3-5% for N=16 α=1.0 (high variance), modest for N=16 α=0.5 (lower variance).

**Privacy implication**: Weights require knowing teacher accuracy, which can be computed server-side using a small validation set (no additional client communication).

---

### H2: Per-Class Weighted Distillation (PCWD)
**Hypothesis**: In non-IID settings, each teacher specialises in its dominant classes. Per-class weighting extracts this specialist knowledge, enabling the student to **surpass the best individual teacher**.

**Insight**: The "oracle ceiling" — combining the best teacher's performance for each class separately — always exceeds the best single teacher's overall accuracy. In our N=4 α=0.5 setting:
- Best single teacher: 81.9%
- Oracle ceiling (best per-class combination): TBD from experiment

**Implementation**: `w_i = per_class_acc[teacher(i)][true_label_i]`

For class "cat", use the features from whichever teacher is best at recognising cats (even if its overall accuracy is lower).

**Expected gain**: This is the only strategy that could systematically surpass the best teacher. If the oracle ceiling is >85% (vs best teacher 81.9%), PCWD should get close to this.

**Privacy implication**: Per-class accuracy can be shared by clients without revealing individual samples (it's a class-level aggregate statistic).

---

### H3: Confidence-Weighted Distillation (CWD)
**Hypothesis**: High teacher confidence on a sample indicates the teacher is certain about that sample's features — use it more for training.

**Implementation**: `w_i = max(softmax(teacher_logit_i))`

**Expected gain**: Moderate. Filters out borderline cases where the teacher is confused, producing a cleaner feature signal.

**Note**: This is computed purely from teacher logits (already uploaded), no additional privacy cost.

---

### H4: Top-K Teacher Selection (TOPK)
**Hypothesis**: Discarding the bottom 50% of teachers (below median accuracy) removes the noisiest feature contributions. Even though we lose half the samples, signal quality improves enough to compensate.

**Implementation**: Zero weight for teachers with `acc < median(teacher_accs)`.

**Expected gain**: For N=16 α=1.0, removing 8 weakest teachers (36-50% accuracy) keeps only 8 stronger ones (50-66%). This raises effective mean teacher quality from 50.3% to 58.9%.

**Risk**: Halving the sample count may hurt data diversity.

---

### H5: Soft Temperature Weighting (SOFTW)
**Hypothesis**: Linear quality weighting (H1) is too smooth. Sharper weighting via `softmax(acc/T)` with small T concentrates learning on top teachers.

**Implementation**: `w_i = softmax(teacher_accs / T)[teacher(i)]` with T=0.1

With T=0.1 for N=4 teachers [81.9, 60.5, 64.7, 70.3]:
- softmax(0.1) → weights ≈ [0.78, 0.01, 0.05, 0.16]
- Teacher 0 (81.9%) dominates: ~78% of the effective signal

**Risk**: May underfit for classes dominated by non-top teacher.

---

## 4. Per-Class Accuracy Analysis Framework

For each config and strategy, we track per-class accuracy of:
1. Student (our model)
2. Best teacher (for each class independently)
3. Mean teacher (average per-class across all teachers)
4. Oracle ceiling (max per-class across teachers)

**CIFAR-10 Classes**: airplane, automobile, bird, cat, deer, dog, frog, horse, ship, truck

**Expected pattern in non-IID settings**:
- High-α (α=1.0): balanced distribution → teachers have moderate accuracy across all classes → student should roughly track mean teacher per class
- Low-α (α=0.5): unbalanced → each teacher dominates 2-3 classes → student should exceed mean teacher but miss best teacher on rare classes

**Key diagnostic**: If the student scores HIGHER than the best teacher on some classes → ensemble effect is working (H2 confirmed). If student scores LOWER than mean teacher on some classes → those are underserved classes where variance dominates (H1/H3 motivation confirmed).

---

## 5. Limits of HE-Compatible Architecture

Beyond the training protocol, the HE-compatible student has inherent capacity limits:

### Activation Function Depth Cost
Each LearnablePolyAct costs 1 CKKS multiplicative level. ResNet-18 with 2 blocks per layer = 4 layers × 2 blocks × 2 activations/block = 16 activation levels + overhead = ~20 levels total. This exhausts a typical CKKS budget (poly degree 2^14 supports ~20 levels).

A degree-4 activation (better approximation to ReLU, from Softplus family) costs 2 levels per activation → doubles the depth requirement → would exceed CKKS budget for ResNet-18 depth.

**Conclusion**: For ResNet-18 scale, degree-2 polynomial is the maximum we can use without reducing network depth or introducing bootstrapping.

### Channel Scale vs Batch Norm
Batch normalisation requires computing per-channel means and variances — these are polynomial operations (mean = sum/n) but variance requires squaring, which costs 1 CKKS level. At inference on encrypted data, BN can be folded into the preceding linear layer (BN folding). However, during training on the server with encrypted features, the server cannot compute the statistics of ciphertexts without decrypting.

ChannelScale (static γ, β) can be learned during training and applied at inference on encrypted data with no multiplicative cost.

**Gap**: ChannelScale cannot perform the adaptive normalisation that makes BatchNorm so effective during training, especially under distribution shift between clients.

---

## 6. Results (to be filled after experiments complete)

### 6.1 Strategy Comparison — N=4, α=0.5
(mean_teacher=69.3%, best_teacher=81.9%, oracle_ceiling=94.3%)

| Strategy | Phase 2a | Round 1 | Round 3 | **Final** | vs Baseline | vs Best Teacher |
|----------|----------|---------|---------|-----------|-------------|----------------|
| baseline | 15.7% | 79.7% | 79.3% | **79.30%** | — | −2.62% |
| quality_weighted | 12.2% | 79.6% | 79.2% | **79.21%** | −0.09% | −2.71% |
| perclass_weighted | 17.7% | 79.7% | 79.5% | **79.45%** | +0.15% | −2.47% |
| confidence_weighted | 18.4% | 79.6% | 79.5% | **79.45%** | +0.15% | −2.47% |
| topk_teachers | 29.2% | 80.8% | 80.1% | **80.06%** | +0.76% | −1.86% |
| soft_temperature | **52.9%** | **81.6%** | 80.5% | **80.55%** | **+1.25%** | **−1.37%** |

### 6.2 Strategy Comparison — N=16, α=1.0
(mean_teacher=50.3%, best_teacher=66.0%, oracle_ceiling=83.3%)

| Strategy | Phase 2a | Round 1 | Final | vs Baseline | vs Best Teacher |
|----------|----------|---------|-------|-------------|----------------|
| baseline | 11.7% | 60.5% | **59.96%** | — | −6.09% |
| quality_weighted | 12.3% | 60.7% | **60.50%** | +0.54% | −5.55% |
| perclass_weighted | 11.5% | 60.6% | **60.03%** | +0.07% | −6.02% |
| confidence_weighted | 11.3% | 60.6% | **60.00%** | +0.04% | −6.05% |
| topk_teachers | 15.0% | 60.9% | **59.94%** | −0.02% | −6.11% |
| soft_temperature | 26.7% | **61.1%** | **60.25%** | +0.29% | −5.80% |

### 6.3 Per-Class Accuracy — N=4, α=0.5, Best Strategy (soft_temperature)
Teachers: T0=81.9% (dominates frog/horse/ship), T2=64.7% (dominates airplane/bird), T3=70.3% (dominates automobile/cat)

| Class | Student | Best Teacher | Mean Teacher | Oracle | Δ(Student−BestT) |
|-------|---------|-------------|-------------|--------|-----------------|
| airplane | 86.3% | 96.8% (T2) | 73.5% | 96.8% | −10.5% |
| automobile | 91.7% | 98.7% (T3) | 75.7% | 98.7% | −7.0% |
| bird | 72.1% | 90.7% (T2) | 71.6% | 90.7% | −18.6% |
| cat | 69.6% | 89.3% (T3) | 54.4% | 89.3% | −19.7% |
| deer | 79.2% | 92.7% (T1) | 85.1% | 92.7% | −13.5% |
| dog | 73.8% | 91.5% (T0) | 57.5% | 91.5% | −17.7% |
| frog | 86.3% | 95.7% (T0) | 67.7% | 95.7% | −9.4% |
| horse | 79.8% | 96.4% (T0) | 81.3% | 96.4% | −16.6% |
| ship | 86.1% | 96.2% (T0) | 58.7% | 96.2% | −10.1% |
| truck | 80.6% | 95.4% (T0) | 67.9% | 95.4% | −14.8% |

**0/10 classes beat the per-class best teacher.** The student produces a blended average.

---

## 7. Root-Cause Analysis: Why Variance Reduction Has Minimal Effect

### The Refinement Convergence Basin Problem

This is the central finding. Phase 2a accuracy varies dramatically across strategies:

| Strategy | Phase 2a (N=4) | Phase 2a (N=16) |
|----------|---------------|----------------|
| baseline | 15.7% | 11.7% |
| soft_temperature (= top-1 teacher) | **52.9%** | **26.7%** |

Yet final accuracy after 3 refinement rounds is nearly identical across all strategies (79.3–80.6% for N=4). **Refinement erases ~75% of the Phase 2a advantage.**

**Reason**: Phase 2b refinement uses **uniform sample weights** and trains on the **full pooled teacher feature set**. Regardless of how the student was initialised in Phase 2a, it converges to the same attractor — the one determined by the quality of the unweighted pooled teacher features. The only lasting benefit of a better initialisation is a slightly higher convergence plateau (the basin is slightly better), accounting for the residual +1.25%.

**Key fix**: Apply the same quality weighting during refinement. This would maintain the variance-reduction signal throughout all training phases. The experiment as designed applies weights only to Phase 2a.

### Why Per-Class Weighting (H2) Failed to Surpass Best Teacher

Per-class weighting requires the student to learn **class-selective** feature representations — using teacher T2's features for "airplane" class even though T2 has low overall accuracy. This requires that:

1. Early blocks (stem, layer1) produce class-discriminative features → **not true**: early layers detect edges/textures, not classes
2. The student can route class-specific supervision to class-specific blocks → **not possible**: features are processed uniformly regardless of class label during training

Per-class weighting effectively downweights clean samples from good teachers on their non-dominant classes and upweights noisy samples from specialist teachers. Since blocks learn class-agnostic features, this introduces noise rather than class-specific signal.

**The right approach**: Apply per-class weighting only at the **final block (FC head)** where features are class-discriminative, and use standard weighting for early blocks.

### Soft Temperature as Implicit Teacher Selection

T=0.1 effectively selects the single best teacher (soft weights → [1, 0, 0, 0]). This produces a cleaner Phase 2a but **sacrifices the ensemble benefit** — the diversity of class knowledge across teachers is lost. The best teacher (T0, 81.9% for N=4) is weak at airplane (34.6%) and mediocre at bird/cat/dog. Training only on T0 makes the student strong where T0 is strong, but does not exceed T0.

### Path to Surpassing Best Teacher

To achieve this, the student must combine class-specialist knowledge from multiple teachers. The oracle ceiling (94.3% for N=4, 83.3% for N=16) is far above the best single teacher, confirming the potential. But realising it requires:

1. **Weighted refinement**: Apply quality weights in Phase 2b too (not just Phase 2a)
2. **Selective per-layer weighting**: uniform for early blocks, per-class for FC head only
3. **Logit-level distillation with weighted ensemble**: at the FC level, use `Σ_k w_k(class) · teacher_k_logit` as the training target — this is per-class teacher combination at the prediction level where it's most meaningful
4. **Knowledge distillation temperature**: soft teacher logits with temperature T=4 carry more inter-class information than hard features

---

## 8. Next Experiments — Round 2 Results (6 modes × 2 configs)

Jobs 822271–822282. Goal: test weighted refinement, single-teacher upper bound, soft-KD,
and extended 6-round convergence curves.

### 8.1 Results — N=4, α=0.5
(best_teacher=81.92%, oracle=94.34%)

| Mode | Ph2a | R1 | R2 | R3 | R4 | R5 | R6 | Final | vs Best |
|------|------|----|----|----|----|----|-------|-------|---------|
| **weighted_both_soft** (soft_temp Phase2a+2b) | 52.8% | 75.4% | 74.9% | 74.7% | 74.2% | 74.1% | 73.9% | **73.9%** | −8.0% |
| weighted_both_qw (quality_w Phase2a+2b) | 11.9% | 80.1% | **80.5%** | 80.4% | 79.7% | 79.2% | 78.9% | **78.9%** | −3.0% |
| single_teacher (best teacher only) | 52.8% | 75.3% | 74.6% | 74.4% | 74.4% | 73.8% | 74.1% | **74.1%** | −7.8% |
| no_refinement_soft (Ph2a only) | 52.8% | — | — | — | — | — | — | **52.8%** | −29.1% |
| soft_kd (quality_w + T=4 KD head) | 12.2% | 78.8% | 79.8% | **79.8%** | 79.0% | 78.2% | 77.7% | **77.7%** | −4.2% |
| **weighted_refine_only** (uniform Ph2a + qw Ph2b) | 15.8% | **81.0%** | 80.7% | 79.9% | 79.8% | 79.1% | 78.9% | **78.9%** | −3.1% |

**PREVIOUS BEST** (variance_reduction soft_temperature, 3 rounds): R1=81.6%, Final=**80.55%** | −1.37%

### 8.2 Results — N=16, α=1.0
(best_teacher=66.05%, oracle=83.33%)

| Mode | Ph2a | R1 | R2 | R3 | R4 | R5 | R6 | Final | vs Best |
|------|------|----|----|----|----|----|-------|-------|---------|
| weighted_both_soft | 26.4% | 58.6% | 58.8% | 59.3% | 59.1% | 58.8% | 58.4% | **58.4%** | −7.7% |
| weighted_both_qw | 13.3% | 61.7% | 61.2% | 60.5% | 60.2% | 60.2% | 60.2% | **60.2%** | −5.9% |
| single_teacher | 25.1% | 58.8% | 58.5% | 59.0% | 58.7% | 58.6% | 58.1% | **58.1%** | −8.0% |
| no_refinement_soft | 25.1% | — | — | — | — | — | — | **25.1%** | −40.9% |
| soft_kd | 12.6% | 52.8% | 59.6% | 60.4% | **60.4%** | 60.4% | 60.2% | **60.2%** | −5.8% |
| **weighted_refine_only** | 11.6% | **61.6%** | 61.4% | 61.0% | 61.0% | 61.0% | 60.6% | **60.6%** | −5.5% |

**PREVIOUS BEST** (variance_reduction soft_temperature, 3 rounds): R1=61.1%, Final=**60.25%** | −5.80%

### 8.3 Per-Class Accuracy — N=4, α=0.5

| Class | BestT | weighted_both_soft | single_teacher | soft_kd |
|-------|-------|--------------------|----------------|---------|
| airplane | **96.8%** | 37.4% (−59.4) | 40.6% (−56.2) | 80.8% (−16.0) |
| automobile | **98.7%** | 78.1% (−20.6) | 78.3% (−20.4) | 82.3% (−16.4) |
| bird | **90.7%** | 46.5% (−44.2) | 45.4% (−45.3) | 69.3% (−21.4) |
| cat | **89.3%** | 52.1% (−37.2) | 52.7% (−36.6) | 77.5% (−11.8) |
| deer | **92.7%** | 68.5% (−24.2) | 68.0% (−24.7) | 71.1% (−21.6) |
| dog | **91.5%** | 85.7% (−5.8) | 86.6% (−4.9) | 70.5% (−21.0) |
| frog | **95.7%** | 92.9% (−2.8) | 92.8% (−2.9) | 84.7% (−11.0) |
| horse | **96.4%** | 93.5% (−2.9) | 93.2% (−3.2) | 76.4% (−20.0) |
| ship | **96.2%** | 93.4% (−2.8) | 92.6% (−3.6) | 83.2% (−13.0) |
| truck | **95.4%** | 90.9% (−4.5) | 90.9% (−4.5) | 81.5% (−13.9) |
| **Mean** | **94.3%** (oracle) | **73.9%** | **74.1%** | **77.7%** |

### 8.4 Critical Finding: Refinement Always Diverges

**The central discovery across all experiments**: Refinement accuracy peaks at R1 and monotonically
declines with each subsequent round. This holds for ALL modes in BOTH configs.

| Mode (n4_a05) | R1 | R6 | Drop |
|---------------|----|----|------|
| weighted_both_soft | 75.4% | 73.9% | −1.5% |
| weighted_both_qw | 80.1% | 78.9% | −1.2% |
| weighted_refine_only | **81.0%** | 78.9% | −2.1% |
| soft_kd | 78.8% | 77.7% | −1.1% |
| soft_temperature (Exp1) | **81.6%** | 80.6% (R3) | −1.1% |

**Root cause**: Only 5,000 uploaded samples with 30 epochs/block/round = ~900 effective passes by R6.
The model severely overfits the small uploaded feature set. Early stopping at R1 would recover most of the lost accuracy.

### 8.5 Why weighted_both_soft Failed Catastrophically (−8% vs best teacher)

Soft temperature (T=0.1, N=4) collapses to: T0 weight ≈ 78%, T1-3 ≈ 22% combined.

Teacher 0 (best overall, 81.92%) has a critical blind spot: **airplane accuracy = 34.6%** (near random!).
This propagates through both phases:
- Phase 2a: focuses 78% of gradient signal on T0's features → student inherits airplane blindspot
- Phase 2b: weighted refinement continues amplifying T0's biases → airplane stays at 37.4%

**Contrast with uniform refinement**: When Phase 2a (soft_temp) is followed by *uniform* refinement,
all classes are served equally in Phase 2b → airplane recovers to 86.3% (variance_reduction exp).
The key lesson: soft_temp Phase 2a *can* work, but it requires **un-biased refinement** to recover
classes that the dominant teacher missed.

Similarly in N=16, soft_temp concentrates on teacher 8 (66.05%) which has **dog accuracy ≈ 0-2%**.
Result: student dog accuracy = 1.2% (catastrophically bad).

---

## 9. Comprehensive Summary — All Experiments

### 9.1 Full Result History — N=4, α=0.5 (best_teacher=81.92%, oracle=94.34%)

| Protocol | Strategy | Final Acc | vs Best Teacher | Status |
|----------|----------|-----------|----------------|--------|
| Improved (v3) | baseline uniform | 79.65% | −2.27% | Best baseline |
| Variance Reduction | soft_temperature | **80.55%** | **−1.37%** | **Previous best** |
| Variance Reduction | topk_teachers | 80.06% | −1.86% | |
| Variance Reduction | quality_weighted | 79.21% | −2.71% | |
| Next Exp (6 rnd) | weighted_refine_only R1 | **80.99%** | **−0.93%** | **Best at R1** |
| Next Exp (6 rnd) | weighted_both_qw R2 | 80.51% | −1.41% | |
| Next Exp (6 rnd) | weighted_both_soft | 73.90% | −8.02% | Worst — biased refinement |
| Next Exp (6 rnd) | single_teacher | 74.11% | −7.81% | = soft_temp: same teacher |
| Next Exp (6 rnd) | no_refinement_soft | 52.78% | −29.14% | Phase 2a alone catastrophic |

### 9.2 Full Result History — N=16, α=1.0 (best_teacher=66.05%, oracle=83.33%)

| Protocol | Strategy | Final Acc | vs Best Teacher | Status |
|----------|----------|-----------|----------------|--------|
| Improved (v3) | baseline uniform | 60.05% | −6.00% | Best baseline |
| Variance Reduction | soft_temperature | 60.25% | −5.80% | |
| Variance Reduction | quality_weighted | 60.50% | −5.55% | |
| Next Exp (6 rnd) | **weighted_refine_only** | **60.55%** | **−5.50%** | **New best final** |
| Next Exp (6 rnd) | weighted_refine_only R1 | **61.63%** | **−4.42%** | **New best at R1** |
| Next Exp (6 rnd) | weighted_both_soft | 58.39% | −7.66% | Biased refinement |
| Next Exp (6 rnd) | no_refinement_soft | 25.14% | −40.91% | Phase 2a alone catastrophic |

---

## 10. Proposed Next Experiments (Priority Order)

### Exp α: Early Stopping at R1 with Optimal Setup
**Observation**: R1 always beats the final result. The best-ever R1 = 81.61% (soft_temp Phase2a + uniform refinement).
**New experiment**: Run the **variance_reduction soft_temperature** setup but stop after exactly 1 refinement round.
**Expected result**: ~81.6% for n4_a05 (vs best teacher 81.92% — within 0.3%!)
**Goal**: Establish tightest possible upper bound under current protocol.

### Exp β: Mixed Phase Weighting (soft_temp Ph2a + quality_w Ph2b)
**Observation**: soft_temp Phase 2a gives best initialization (52.9%) but biased refinement hurts.
Uniform refinement after soft_temp Ph2a gives R1=81.6%.
Quality-weighted refinement after uniform Ph2a gives R1=81.0%.
**New experiment**: soft_temp Phase 2a + quality_weighted Phase 2b (1 round only).
**Expected result**: 81.6%–82.5% — potentially the first mode to beat the best teacher.

### Exp γ: Lower Refinement LR (prevent divergence)
**Observation**: Refinement with lr=5e-4 + 30 epochs/block diverges over 6 rounds.
**New experiment**: lr=1e-4 for Phase 2b (5× lower), keep 30 epochs/block.
**Expected result**: Slower divergence → stable improvement up to R3–R4 instead of crashing.

### Exp δ: Logit-Level Ensemble Target (HE-compatible)
**Observation**: Feature-level distillation (B4) is indirect supervision. Soft labels carry richer signal.
**New approach**: Average teacher logits (sent alongside features) with quality weights as the FC target.
`target = Σ_k w_k · softmax(logit_k / T=4)` (weighted ensemble prediction as soft label).
No additional client communication (logits already uploaded with features).
**Expected result**: FC head learning improves significantly; overall may beat best teacher for n4.

---

## 8. Connection to Background Literature

From `background.tex` — leveraging prior work for improvements:

- **§2.5 (HE Networks)**: "learnable polynomial activations paired with distillation from ReLU teachers" [Baruch et al.] — we use this, but their work is centralised. Our federated variant must account for heterogeneous teacher quality.

- **§2.5 "escaping activation problem"** [Garimella, SISYPHUS]: Polynomial activations amplify distributional noise. Our bridge fix addresses the cascade failure, but the fundamental amplification at each block remains a bottleneck.

- **§2.5 "boundary losses and selective gradient clipping"** [Al-Hossain, StablePolynomial]: Their approach for stable training of deep ResNets with polynomial activations could be adapted — specifically their boundary loss that prevents activation magnitudes from growing too large. Currently we use gradient clipping (norm=1.0) but not explicit activation boundary losses.

  **Future work**: Add activation magnitude penalty to the Phase 2a loss.

- **§2.3 "feature inversion can recover private images with SSIM≈0.997"** [Beitollahi]: Confirms why we must use CKKS — plaintext features are not safe even without gradients.

- **§2.1 "exact image reconstruction for batches up to b≤25"** [Dimitrov, SPEAR]: Justifies block-level feature distillation rather than gradient sharing — our protocol never shares gradients.

- **§2.2 "soft-label distillation channels can transfer memorised data"** [Behrens]: Justifies using feature-level (not logit-level) distillation. However, as B4 above shows, this is also a limitation.

**Open question**: Could we do logit-level distillation (richer signal) while maintaining privacy? One approach: encrypt logits with CKKS, compute cross-entropy loss on ciphertexts server-side. The softmax operation costs ~3 CKKS levels (polynomial approximation of exp). This is feasible for 10-class classification but adds significant overhead.

**Resolved by Exp γ results**: Logits are already uploaded with the features (no extra communication). Quality-weighted ensemble of logits as FC target is already tested in `soft_kd` mode (T=4). It gives 79.8% for n4_a05 — better than soft/single_teacher but worse than weighted_refine_only. The feature-level distillation for blocks 0-4 combined with logit distillation at the FC head is a valid hybrid approach worth pursuing more aggressively.
