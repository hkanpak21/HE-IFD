"""HE-IFD membership-inference suite (issue 021).

A self-contained suite that measures how much the *released* artefacts of the
HE-IFD protocol leak about a client's training data. Three attacks are run
across three adversary surfaces, scored by TPR@0.1%FPR and ROC/AUC.

Attacks (``mia.attacks``)
-------------------------
* ``threshold``  — Yeom et al. 2018 loss/confidence threshold attack
  (``yeom2018privacy``). The cheap, interpretable floor: a sample is predicted
  IN if the target's loss on it is below a threshold.
* ``lira``       — Carlini et al. 2022 LiRA, the offline/online likelihood-ratio
  shadow-model attack (``carlini2022membership``; algorithm ported from
  ``github.com/tensorflow/privacy`` ``research/mi_lira_2021``).
* ``glira``      — Galichin et al. 2025 GLiRA, distillation-guided black-box LiRA
  (``galichin2025glira``). Implemented from the paper (no public repo): the
  adversary distils a *surrogate* of the black-box target and runs the LiRA
  likelihood-ratio on the surrogate's confidences.

Surfaces (``mia.surfaces``)
---------------------------
* ``external``    — black-box query access to the released global model θ⋆.
* ``fellow``      — an honest-but-curious participant; same θ⋆ access PLUS its
  own data and the shared Phase-0 prototypes as a stronger auxiliary prior.
* ``prototype``   — membership inference directly on the Phase-0 per-class
  prototype release (raw and at ε∈{2,8}); empirically validates the
  averaging-variant DP accounting of the paper's §Security Analysis.

The suite reuses ``src/`` to build every target and shadow model (it does NOT
reimplement the protocol): see ``mia.target``.
"""
