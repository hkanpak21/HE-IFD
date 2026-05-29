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
