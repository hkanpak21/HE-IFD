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

## COLLECTED RESULTS — 028 ViT/CIFAR-100 (Colab run, 2026-05-30)

ViT/CIFAR-100 MIA landed (64 shadows). **RoBERTa/AG-News did NOT** — its `mia.run`
hit the pre-fix `ag_news` loader (the Colab VM repo was stale); re-run after
`git pull` of the `fancyzhx/ag_news` fix (commit `d8b2847`). Full ROC arrays in
`heifd_021_mia_results.zip`.

| backbone | α | surface | attack | TPR@0.1%FPR | TPR@1%FPR | AUC |
|---|---|---------|--------|-------------|-----------|-----|
| vit_b32_cifar100 | 0.05 | external/fellow | threshold | 0.0049 | 0.0220 | 0.6684 |
| vit_b32_cifar100 | 0.05 | external/fellow | **lira** | **0.1282** | 0.2518 | **0.8518** |
| vit_b32_cifar100 | 0.05 | external | glira | 0.0033 | 0.0204 | 0.5332 |
| vit_b32_cifar100 | 0.05 | prototype | raw | 0.9359 | 0.9367 | 0.9671 |
| vit_b32_cifar100 | 0.05 | prototype | eps8 | 0.0094 | 0.0371 | 0.5677 |
| vit_b32_cifar100 | 0.05 | prototype | eps2 | 0.0037 | 0.0184 | 0.5271 |
| vit_b32_cifar100 | 1.0 | external/fellow | threshold | 0.0020 | 0.0229 | 0.6759 |
| vit_b32_cifar100 | 1.0 | external/fellow | **lira** | **0.1645** | 0.2686 | **0.8597** |
| vit_b32_cifar100 | 1.0 | external | glira | 0.0045 | 0.0229 | 0.5364 |
| vit_b32_cifar100 | 1.0 | prototype | raw | 1.0000 | 1.0000 | 1.0000 |
| vit_b32_cifar100 | 1.0 | prototype | eps8 | 0.0029 | 0.0261 | 0.6000 |
| vit_b32_cifar100 | 1.0 | prototype | eps2 | 0.0053 | 0.0220 | 0.5620 |

**Prototype-channel story HOLDS:** raw release leaks hard (AUC 0.97 / 1.00), DP
collapses it toward chance (ε8 → 0.57/0.60, ε2 → 0.53/0.56).

**⚠️ Released-model story DEVIATES from MNIST:** on MNIST the released θ⋆ was
near-chance (AUC 0.49–0.57). On ViT/CIFAR-100 the threshold/GLiRA attacks stay
low (0.67 / 0.53) but **LiRA reaches AUC 0.85 (TPR@0.1%FPR ≈ 0.13–0.16)** — the
released pretrained-vision model leaks materially under the strongest shadow
attack. The "released model near-chance" headline does **not** replicate on
ViT/CIFAR-100 under LiRA — flag for the paper / further analysis.
