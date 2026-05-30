# heifd_021_mia

Membership-inference study (issue 021) of the HE-IFD released global model θ⋆ and
the Phase-0 prototype channel. Three attacks — Yeom et al. 2018 loss/confidence
threshold, Carlini et al. 2022 LiRA (likelihood-ratio shadow-model attack), and
Galichin et al. 2025 GLiRA (distillation-guided black-box LiRA) — are run across
three adversary surfaces: external (black-box query on θ⋆), fellow-client (a
participant with its own data + the shared Phase-0 prototypes as a stronger
prior), and the prototype channel (membership inference directly on the per-class
prototype release, at raw and ε∈{2,8}). Scored by TPR@0.1%FPR and ROC/AUC.

**Placeholder.** This README is auto-overwritten by `mia.report.write_report`
once `mia.run` produces results. Cells: `mnist_mlp` and `vit_b32_cifar100`,
N=10, α∈{0.05, 1.0}, ~64 shadow models per target. See `mia/README.md` for the
suite design, attack citations, and how to run the wrappers
(`jobs/heifd_021_mia_*.sh`).

The suite reuses `src/` to build every target and shadow model — the protocol is
not reimplemented. Per-cell JSONs (`cell_*.json`) carry full ROC arrays for the
paper's log-log figure; `summary.json` carries the flat records the §VI table
reads.

## COLLECTED RESULTS — 028 both backbones (Colab run, 2026-05-30) ✅

ViT/CIFAR-100 (vision) + RoBERTa/AG-News (language), N=10, α∈{0.05,1.0}, 64 shadows,
3 attacks × 3 surfaces. AUC is the headline (TPR@fixed-FPR alongside). External and
fellow surfaces are identical here (same θ⋆ confidences), so listed once.

### RoBERTa / AG-News (language)

| α | surface | attack | TPR@0.1%FPR | TPR@1%FPR | AUC |
|---|---------|--------|-------------|-----------|-----|
| 0.05 | external/fellow | threshold | 0.0024 | 0.0118 | 0.4946 |
| 0.05 | external/fellow | lira | 0.0012 | 0.0078 | 0.5137 |
| 0.05 | external | glira | 0.0008 | 0.0147 | 0.4954 |
| 0.05 | prototype | raw | 0.0735 | 0.0824 | 0.5287 |
| 0.05 | prototype | eps8 | 0.0016 | 0.0098 | 0.4906 |
| 0.05 | prototype | eps2 | 0.0033 | 0.0122 | 0.4933 |
| 1.0 | external/fellow | threshold | 0.0045 | 0.0186 | 0.4960 |
| 1.0 | external/fellow | lira | 0.0057 | 0.0216 | 0.5300 |
| 1.0 | external | glira | 0.0008 | 0.0110 | 0.4999 |
| 1.0 | prototype | raw | 0.2886 | 0.2906 | 0.6421 |
| 1.0 | prototype | eps8 | 0.0012 | 0.0090 | 0.4915 |
| 1.0 | prototype | eps2 | 0.0016 | 0.0078 | 0.4904 |

### ViT / CIFAR-100 (vision)

| α | surface | attack | TPR@0.1%FPR | TPR@1%FPR | AUC |
|---|---------|--------|-------------|-----------|-----|
| 0.05 | external/fellow | threshold | 0.0049 | 0.0220 | 0.6684 |
| 0.05 | external/fellow | **lira** | **0.1282** | 0.2518 | **0.8518** |
| 0.05 | external | glira | 0.0033 | 0.0204 | 0.5332 |
| 0.05 | prototype | raw | 0.9359 | 0.9367 | 0.9671 |
| 0.05 | prototype | eps8 | 0.0094 | 0.0371 | 0.5677 |
| 0.05 | prototype | eps2 | 0.0037 | 0.0184 | 0.5271 |
| 1.0 | external/fellow | threshold | 0.0020 | 0.0229 | 0.6759 |
| 1.0 | external/fellow | **lira** | **0.1645** | 0.2686 | **0.8597** |
| 1.0 | external | glira | 0.0045 | 0.0229 | 0.5364 |
| 1.0 | prototype | raw | 1.0000 | 1.0000 | 1.0000 |
| 1.0 | prototype | eps8 | 0.0029 | 0.0261 | 0.6000 |
| 1.0 | prototype | eps2 | 0.0053 | 0.0220 | 0.5620 |

### Cross-modality reading (vision + language)

- **RoBERTa/language — the MNIST dual story HOLDS cleanly.** Released θ⋆ is
  **near-chance under every attack** (AUC 0.49–0.53, incl. LiRA). The prototype
  channel barely leaks even raw (AUC 0.53 @ α=0.05, 0.64 @ α=1.0) and DP ε≤8
  drives it to ~0.49. Text sentence-embedding prototypes are far less
  identifiable than image features.
- **ViT/vision — prototype story HOLDS, released-model story DEVIATES.** Prototype
  raw leaks hard (0.97 / 1.00) and DP collapses it (ε8 → 0.57/0.60, ε2 →
  0.53/0.56) ✅. But **LiRA on the released θ⋆ reaches AUC 0.85** (TPR@0.1%FPR
  0.13–0.16) while threshold/GLiRA stay low (0.53–0.68) — the "released model
  near-chance" headline does **not** hold for ViT/CIFAR-100 under the strongest
  shadow attack.
- **Net:** prototype-channel DP-collapse is universal (both modalities). The
  near-chance released-model claim is solid for language but needs a caveat for
  the pretrained vision backbone under LiRA — flag for the paper / analysis
  (separable CIFAR-100 features + α heterogeneity → more memorization).

Full ROC arrays (for the log-log figure) live in the per-cell `cell_*.json` on the
Colab VM; pull them via the notebook's EXPORT cell when convenient.
