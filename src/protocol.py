"""End-to-end protocol composition: one (dataset, backbone, N, α, K, method, seed)
cell -> CellResult.

``run_cell`` is the deep-module that wires the whole pipeline:

    data        reserve labelled probe + Dirichlet-partition the pool
      -> teacher    train one teacher per client (+ a centralised oracle reference)
      -> phase0     build the alignment probe and warm θ₀ for the chosen strategy
      -> distill    each client runs the bounded K-step trajectory -> Δ_i
      -> aggregate  server computes θ = θ₀ + Σ_i w_i·Δ_i  (linear, sample-weighted)
      -> evaluate   IID test accuracy of the aggregated student
      (-> report    handled by the caller / sweep)

It faithfully reproduces the notebook's two task runners — ``run_section_A_task``
(from-scratch MNIST/MLP) and ``run_pretrained_protocol_task`` (linear head on
cached pretrained features) — behind one signature parameterised by ``backbone``.
All seeding matches the notebook so a ported cell reproduces the colab logic
(numeric bit-match is NOT a goal — the notebook carries the GPT-2 bug fixed in
issue 002; the gate is the qualitative sanity check in 001).

Method panel (``method`` -> (phase0 strategy)):
  no_phase0             -> none        (distil from fresh random init θ₀)
  warmup_only_labelled  -> warmup_only (warm on labelled probe, NO distillation)
  labelled_probe_warmup -> labelled    (warm θ₀ on labelled probe, then distil)
  raw_union_K{K}        -> raw_union   (K_per_class kwarg)
  dp_avg_eps{E}_K{K}    -> dp_avg      (K_per_class + eps kwargs)
  synthetic_K{K}        -> synthetic   (issue 016+ — per-(client, class)
                                        Gaussian-around-mean synthetic
                                        samples; same byte budget as
                                        raw_union_K, no raw records crossing
                                        the P2P boundary; no DP)
  synthetic_dp_eps{E}_K{K}
                        -> synthetic_dp (issue 016+ — DP-protected μ release
                                         on the synthetic path; same averaging-
                                         variant accounting as dp_avg)
  synthetic_logit_K{K}  -> synthetic_logit (issue 016+ NOVEL — synthetic-
                                            sample payload composed with per-
                                            class teacher-logit prototypes;
                                            warmup uses KL against the soft-
                                            label prototypes rather than CE
                                            against one-hot labels)
  noprobe_raw_union_K{K}
                        -> noprobe_raw_union (issue 017 — NO labelled public
                                              probe; the raw-union per-(client,
                                              class) prototypes themselves are
                                              the supervised warmup set, giving
                                              a WEAK θ₀)
  noprobe_dp_avg_eps{E}_K{K}
                        -> noprobe_dp_avg (issue 017 — NO labelled public probe;
                                           the DP-noisy per-(client, class)
                                           prototypes themselves are the
                                           supervised warmup set; same averaging-
                                           variant DP accounting as dp_avg)
"""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional, Sequence


# ---------------------------------------------------------------------------
# Backbone registry: maps a backbone label to its loader + per-role hyperparams.
# From-scratch backbones train on raw inputs; "head" backbones train a linear
# head on cached pretrained features. Hyperparameters mirror notebook Section 0.2.
# ---------------------------------------------------------------------------
@dataclass
class BackboneSpec:
    label: str
    kind: str                 # "scratch" | "head"
    num_classes: int
    labelled_probe_default: int
    teacher_epochs: int
    teacher_lr: float
    oracle_epochs: int
    warmup_epochs: int
    bs: int
    feature_loader: str       # which backbones.* loader to call ("mnist"/cifar/text)
    # Default trainable-layer scope for this backbone (issue 011). Per-cell
    # overrides flow through ``run_cell(..., trainable_scope=...)`` via the
    # sweep CLI's ``--scopes`` flag; the BackboneSpec default applies when no
    # override is given so every pre-issue-011 entrypoint stays byte-identical.
    # Valid tokens: ``"head_only"`` (default), ``"lora_<rank>"``,
    # ``"last_block"``, ``"last_n_blocks_<n>"``. See ``backbones.parse_scope``.
    trainable_scope: str = "head_only"
    # Optional LR schedule for the supervised SGD trainer (teacher / oracle /
    # Phase-0 warmup — all three go through ``teacher.train_supervised_model``).
    # ``None`` (the legacy default) keeps the constant-LR behaviour byte-identical
    # for every pre-issue-011-Part-3-round-2 backbone. ``"cosine"`` enables
    # ``CosineAnnealingLR`` with ``T_max=epochs``, ``eta_min=teacher_lr/100``,
    # stepping at the end of each epoch — useful when the budget is large
    # enough (e.g. CNN-5/CIFAR-10 at teacher_epochs=60) that a constant LR
    # over-shoots late in training. Opt-in: only the backbone that sets this
    # field will hit the scheduler path; every other backbone keeps the
    # SGD-with-constant-LR loop. See ``teacher.train_supervised_model``.
    teacher_lr_schedule: Optional[str] = None
    # Per-backbone feature standardization applied to the cached features once at
    # load (issue 019 warmup-collapse fix). Some strong frozen text encoders
    # (RoBERTa-base, all-mpnet-base-v2) emit mean-pooled features whose raw
    # magnitude/distribution the small-LR warmup head cannot fit at extreme
    # heterogeneity (α=0.05), pinning θ₀ at chance even though the centralised
    # linear-probe oracle is strong (~0.90). The standard linear-probing remedy
    # is to standardize the frozen features before the head. Values:
    #   * ``"none"``   (default) — NO normalization; byte-identical to the
    #                  pre-019 path for every existing backbone (the gate is a
    #                  pure no-op when "none", see ``_load_features``).
    #   * ``"zscore"`` — per-feature (x − μ)/(σ + eps), with μ/σ fit on the TRAIN
    #                  features ONLY (no test leakage) and applied to BOTH train
    #                  and test. eps=1e-6.
    #   * ``"l2"``     — per-sample L2 normalization x / (‖x‖₂ + eps).
    # Applied once to the X tensors at load, so warmup, teachers, distillation,
    # and oracle all see the SAME standardized features (consistent downstream).
    normalize_features: str = "none"


# Notebook Section 0.2 constants
_TEACHER_MOMENTUM = 0.9
_STUDENT_LR = 0.01
_TAU = 4.0
_WARMUP_EPOCHS = 5

BACKBONES: Dict[str, BackboneSpec] = {
    # From-scratch MNIST MLP (Section A): teacher_epochs=5, lr=0.05, oracle=10, bs=64.
    "mlp_mnist": BackboneSpec(
        label="mlp_mnist", kind="scratch", num_classes=10,
        labelled_probe_default=100, teacher_epochs=5, teacher_lr=0.05,
        oracle_epochs=10, warmup_epochs=_WARMUP_EPOCHS, bs=64, feature_loader="mnist",
    ),
    # From-scratch FashionMNIST LeNet-5 (issue 007): same from-scratch training
    # regime as mlp_mnist (teacher_epochs=5, lr=0.05, oracle=10, warmup=5, bs=64),
    # the notebook Section-0.2 from-scratch convention. Conv net on 1x28x28 raw
    # images — Co-Boosting/FedLPA "LeNet-5 for FMNIST" peer setup.
    "lenet_fmnist": BackboneSpec(
        label="lenet_fmnist", kind="scratch", num_classes=10,
        labelled_probe_default=100, teacher_epochs=5, teacher_lr=0.05,
        oracle_epochs=10, warmup_epochs=_WARMUP_EPOCHS, bs=64, feature_loader="fmnist",
    ),
    # From-scratch CIFAR-10 CNN-5 (issue 007 + issue 011 Part 3 + Round 2):
    # CIFAR-10 is harder, and the original (teacher_epochs=10 / oracle_epochs=20
    # / teacher_lr=0.01 / warmup_epochs=5) hit a 27pp IID gap to oracle in
    # issue 007's verify run — raw_union IID 0.48 vs oracle 0.75 — i.e. the
    # teacher (and the warmup) were under-trained. Issue 011 Part 3's first
    # bump (teacher_epochs=30 / oracle_epochs=50 / teacher_lr=0.005 /
    # warmup_epochs=10) lifted IID raw_union to 0.5159 but still missed the
    # ≥0.60 gate; teachers at 30 epochs / constant lr=0.005 only reached
    # mean_teacher ≈ 0.46 (vs oracle 0.78 at 50 epochs), so distillation
    # bottlenecks on weak teacher signal and m4_ood at α=0.05 sat at 0.16.
    # Round 2 doubles the teacher / oracle budget AND switches the trainer to
    # cosine LR decay (lr_max=0.01 → lr_min=1e-4 over T=teacher_epochs / or
    # oracle_epochs / warmup_epochs respectively): higher starting LR + cosine
    # tail tends to land better than a constant low LR with the same step
    # count. Sanity gate: CIFAR-10 IID raw_union ≥ 0.60 at α=1.0 AND m4_ood ≥
    # 0.40 at α=0.05 after refit. Conv net on RAW 3x32x32 images (NOT
    # pretrained feats). Co-Boosting/FedLPA "CNN-5 for CIFAR-10" peer setup.
    "cnn5_cifar10": BackboneSpec(
        label="cnn5_cifar10", kind="scratch", num_classes=10,
        labelled_probe_default=100, teacher_epochs=60, teacher_lr=0.01,
        oracle_epochs=100, warmup_epochs=10, bs=64, feature_loader="cifar10_raw",
        teacher_lr_schedule="cosine",
    ),
    # Pretrained vision heads (Section B): head training is faster/smaller-LR.
    "resnet18_cifar10": BackboneSpec(
        label="resnet18_cifar10", kind="head", num_classes=10,
        labelled_probe_default=100, teacher_epochs=3, teacher_lr=0.01,
        oracle_epochs=5, warmup_epochs=_WARMUP_EPOCHS, bs=128, feature_loader="cifar10:resnet18",
    ),
    "vit_b32_cifar10": BackboneSpec(
        label="vit_b32_cifar10", kind="head", num_classes=10,
        labelled_probe_default=100, teacher_epochs=3, teacher_lr=0.01,
        oracle_epochs=5, warmup_epochs=_WARMUP_EPOCHS, bs=128, feature_loader="cifar10:vit_b32",
    ),
    # Pretrained vision heads on CIFAR-100 (issue 012; harder regime to escape
    # ViT-on-CIFAR-10's 0.97 saturation). 100 classes ⇒ probe ≥ 1 sample per
    # class is the floor; we set 300 so each class sees ~3 examples on
    # average (still small enough that the linear-head probe remains an
    # honest "small-labelled-public" baseline, large enough that warmup
    # doesn't collapse the way a 100-sample probe over 100 classes would).
    # Hyperparams otherwise mirror the CIFAR-10 head cells (per issue 011's
    # finding that head_only/(K=100, τ=1, lr=0.001) is the right pretrained
    # default; per-cell KD hparams come through the sweep CLI). Issue 011
    # also showed last_block harms via warmup-underfit on a 100-sample probe;
    # the 300-sample probe used here gives last_block a fairer test on harder
    # data if the orchestrator later sweeps scopes (issue 012 itself stays
    # head_only per the brief).
    "resnet18_cifar100": BackboneSpec(
        label="resnet18_cifar100", kind="head", num_classes=100,
        labelled_probe_default=300, teacher_epochs=3, teacher_lr=0.01,
        oracle_epochs=5, warmup_epochs=_WARMUP_EPOCHS, bs=128,
        feature_loader="cifar100:resnet18",
    ),
    "vit_b32_cifar100": BackboneSpec(
        label="vit_b32_cifar100", kind="head", num_classes=100,
        labelled_probe_default=300, teacher_epochs=3, teacher_lr=0.01,
        oracle_epochs=5, warmup_epochs=_WARMUP_EPOCHS, bs=128,
        feature_loader="cifar100:vit_b32",
    ),
    # Pretrained vision heads on Tiny-ImageNet (issue 012; 200 classes, 64×64).
    # Probe set to 600 so every class sees ~3 examples on average — the same
    # per-class probe density as the CIFAR-100 entries (300/100=3). The
    # ResNet/ViT backbones are ImageNet-trained and Tiny-ImageNet's classes
    # overlap ImageNet, so the frozen features are informative; the linear-
    # probe ceiling is ~0.55-0.65 (ViT) / 0.45-0.55 (ResNet) per the issue
    # 012 brief — substantial headroom for distillation to add value.
    "resnet18_tiny_imagenet": BackboneSpec(
        label="resnet18_tiny_imagenet", kind="head", num_classes=200,
        labelled_probe_default=600, teacher_epochs=3, teacher_lr=0.01,
        oracle_epochs=5, warmup_epochs=_WARMUP_EPOCHS, bs=128,
        feature_loader="tiny_imagenet:resnet18",
    ),
    "vit_b32_tiny_imagenet": BackboneSpec(
        label="vit_b32_tiny_imagenet", kind="head", num_classes=200,
        labelled_probe_default=600, teacher_epochs=3, teacher_lr=0.01,
        oracle_epochs=5, warmup_epochs=_WARMUP_EPOCHS, bs=128,
        feature_loader="tiny_imagenet:vit_b32",
    ),
    # Pretrained text heads (Section C) on AG News (4 classes).
    "distilbert_agnews": BackboneSpec(
        label="distilbert_agnews", kind="head", num_classes=4,
        labelled_probe_default=100, teacher_epochs=3, teacher_lr=0.01,
        oracle_epochs=5, warmup_epochs=_WARMUP_EPOCHS, bs=128, feature_loader="text:distilbert",
    ),
    "gpt2_agnews": BackboneSpec(
        label="gpt2_agnews", kind="head", num_classes=4,
        labelled_probe_default=100, teacher_epochs=3, teacher_lr=0.01,
        oracle_epochs=5, warmup_epochs=_WARMUP_EPOCHS, bs=128, feature_loader="text:gpt2_small",
    ),
    # ------------------------------------------------------------------------
    # Big pretrained backbones (issue 018). Head-on-cached-features pattern is
    # identical to the existing pretrained entries — only the frozen extractor
    # is the Large model variant (1024-d features for all three vs 768-d for
    # the base models). ``head_only`` scope per issue 011's finding (the linear
    # head suffices; LoRA is the deferred Part-B capacity lever reserved for the
    # big backbones if head_only under-capacitates). Part A's sanity-check
    # reuses the centralised ``oracle`` field (a supervised head trained on the
    # full training pool, evaluated on held-out test) that ``run_cell`` already
    # computes — no protocol run on a big backbone is authorised until the HITL
    # review of Part A passes.
    # ViT-L/16 on CIFAR-100 (the harder dataset from issue 012; CIFAR-10
    # saturates). Probe=300 mirrors vit_b32_cifar100 (≈3 labelled samples/class).
    "vit_l_cifar100": BackboneSpec(
        label="vit_l_cifar100", kind="head", num_classes=100,
        labelled_probe_default=300, teacher_epochs=3, teacher_lr=0.01,
        oracle_epochs=5, warmup_epochs=_WARMUP_EPOCHS, bs=128,
        feature_loader="cifar100:vit_l",
    ),
    # BERT-large-uncased on AG-News (4 classes). Bidirectional encoder — masked
    # mean-pool, like distilbert_agnews. Mirrors the AG-News head hyperparams.
    "bert_large_agnews": BackboneSpec(
        label="bert_large_agnews", kind="head", num_classes=4,
        labelled_probe_default=100, teacher_epochs=3, teacher_lr=0.01,
        oracle_epochs=5, warmup_epochs=_WARMUP_EPOCHS, bs=128,
        feature_loader="text:bert_large",
    ),
    # GPT-2-medium on AG-News (4 classes). Causal LM — inherits the issue-002
    # left-pad + last-token pooling fix (NOT mean-pool) via the gpt2_medium
    # branch in extract_text_features. GPT-2 family is deferred per issue 002;
    # its Part-A gate (IID ≥ 0.50) is informational only — a failure here does
    # NOT block Part B.
    "gpt2_medium_agnews": BackboneSpec(
        label="gpt2_medium_agnews", kind="head", num_classes=4,
        labelled_probe_default=100, teacher_epochs=3, teacher_lr=0.01,
        oracle_epochs=5, warmup_epochs=_WARMUP_EPOCHS, bs=128,
        feature_loader="text:gpt2_medium",
    ),
    # ------------------------------------------------------------------------
    # Strong frozen TEXT backbones (issue 019) — the text analogue of the
    # issue-018/012 vision improvement. The backbone is FROZEN: it never enters
    # the HE combine; only the linear head displacement Δᵢ is aligned/aggregated.
    # So any strong frozen encoder is fair game. Both are *bidirectional*
    # encoders → masked mean-pool over real tokens (right-pad), like
    # distilbert_agnews — NOT the GPT-2 causal last-token path. AG-News head
    # hyperparams mirror distilbert_agnews exactly (pretrained-head regime).
    # RoBERTa-base on AG-News (4 classes). 125M params, 768-d. Expected frozen
    # linear-probe ~0.92+ vs DistilBERT's 0.864 — lifting the heterogeneous
    # α=0.05 regime (DistilBERT collapses to 0.437 there).
    "roberta_base_agnews": BackboneSpec(
        label="roberta_base_agnews", kind="head", num_classes=4,
        labelled_probe_default=100, teacher_epochs=3, teacher_lr=0.01,
        oracle_epochs=5, warmup_epochs=_WARMUP_EPOCHS, bs=128,
        feature_loader="text:roberta_base", normalize_features="zscore",
    ),
    # all-mpnet-base-v2 on AG-News (4 classes). 768-d sentence-embedding model;
    # mean-pool is its training-time pooling — the strongest frozen linear-probe
    # candidate (expected ≥0.93). Loaded via plain transformers AutoModel (no
    # sentence-transformers package dependency); the existing manual mean-pool
    # reproduces its embedding.
    "mpnet_st_agnews": BackboneSpec(
        label="mpnet_st_agnews", kind="head", num_classes=4,
        labelled_probe_default=100, teacher_epochs=3, teacher_lr=0.01,
        oracle_epochs=5, warmup_epochs=_WARMUP_EPOCHS, bs=128,
        feature_loader="text:mpnet_st", normalize_features="zscore",
    ),
    # ------------------------------------------------------------------------
    # DBpedia-14 (issue 019 Part 2) — the text analogue of CIFAR-100. 14 topic
    # classes give a meaningful α=0.05 heterogeneity + 13 OOD classes for m4
    # (AG-News's 4 classes cap both). Same frozen backbones / head hyperparams
    # as the AG-News entries; only num_classes (14) and the dataset segment of
    # the feature_loader (``:dbpedia_14``) differ. Probe=300 mirrors the
    # CIFAR-100 head entries (~3 labelled samples/class over 14 classes is
    # ample; kept at the CIFAR-100 value for a fair "small labelled public"
    # baseline on the richer label space).
    "roberta_base_dbpedia": BackboneSpec(
        label="roberta_base_dbpedia", kind="head", num_classes=14,
        labelled_probe_default=300, teacher_epochs=3, teacher_lr=0.01,
        oracle_epochs=5, warmup_epochs=_WARMUP_EPOCHS, bs=128,
        feature_loader="text:roberta_base:dbpedia_14", normalize_features="zscore",
    ),
    "mpnet_st_dbpedia": BackboneSpec(
        label="mpnet_st_dbpedia", kind="head", num_classes=14,
        labelled_probe_default=300, teacher_epochs=3, teacher_lr=0.01,
        oracle_epochs=5, warmup_epochs=_WARMUP_EPOCHS, bs=128,
        feature_loader="text:mpnet_st:dbpedia_14", normalize_features="zscore",
    ),
}


@dataclass
class CellResult:
    """One protocol cell's outcome (serialised to results/<case>/cell_*.json)."""
    # identity
    backbone: str
    dataset: str
    N: int
    alpha: float
    seed: int
    K: int
    tau: float
    method: str
    phase0_kind: str
    probe_size_actual: int
    sigma: float
    # Server-combine selector (issue 025). DEFAULTS to "weight_avg" (the linear
    # production aggregate) so every pre-025 cell JSON — which omits this field —
    # reloads as the linear baseline, and a weight_avg cell is identity-identical
    # to the pre-025 path. ``agg_depth`` is the HE multiplicative-depth annotation
    # for the chosen combine (depth-1 / depth-2 / deep; see
    # aggregate.NONLINEAR_DEPTH). Recorded here, in the CSV, and in the report.
    agg_method: str = "weight_avg"
    agg_depth: str = "depth-1"
    # headline metric + references
    acc: Optional[float] = None
    mean_teacher: Optional[float] = None
    best_teacher: Optional[float] = None
    oracle: Optional[float] = None
    per_teacher_acc: List[float] = field(default_factory=list)
    # standalone θ₀: test accuracy of the aligned init clients receive, BEFORE
    # any local distillation (for no_phase0 this is the fresh random init).
    theta0_acc: Optional[float] = None
    # M3 — per-client teacher-vs-aggregate gap on each client's own data D_i:
    #   acc(final_student, D_i) − acc(teacher_i, D_i). Positive ⇒ federation
    #   helped client i. (See evaluate.per_client_gap.)
    m3_student_acc_on_Di: List[Optional[float]] = field(default_factory=list)
    m3_teacher_acc_on_Di: List[Optional[float]] = field(default_factory=list)
    m3_gap: List[Optional[float]] = field(default_factory=list)
    m3_mean_gap: Optional[float] = None
    m3_clients_helped: Optional[int] = None
    m3_clients_evaluated: Optional[int] = None
    # M4 — per-client OOD-class accuracy: final student's accuracy on TEST
    #   examples from classes client i held ZERO local examples of. All-None /
    #   m4_mean=None when vacuous (every client saw every class, e.g. α=1.0).
    m4_ood_acc: List[Optional[float]] = field(default_factory=list)
    m4_mean: Optional[float] = None
    m4_clients_evaluated: Optional[int] = None
    # partition diagnostics
    per_client_total: List[int] = field(default_factory=list)
    per_client_per_class: List[List[int]] = field(default_factory=list)
    sample_weights: List[float] = field(default_factory=list)
    # timing
    wall_clock_sec: float = 0.0
    phase_teacher_sec: float = 0.0
    phase_phase0_sec: float = 0.0
    phase_distill_sec: float = 0.0
    phase_aggregate_sec: float = 0.0
    phase_eval_sec: float = 0.0
    # provenance
    job_id: Optional[str] = None
    node: Optional[str] = None
    status: str = "success"
    error: Optional[str] = None
    notes: str = ""
    # KD-dynamics diagnostics (issue 013). ``None`` (the default) means this
    # cell was run WITHOUT diagnostics — the default for every sweep — and the
    # field is simply absent from the JSON's information content (still
    # serialised so the schema is stable). When populated, this dict carries
    # teacher entropy / per-step Δ norms / pairwise cosine / per-class θ₀-vs-
    # final accuracy. JSON-serialisable plain types only. See src.diagnostics.
    diagnostics: Optional[Dict] = None
    # Task-arithmetic λ-scaling curve (issue 026). ``None`` (the default) means
    # the cell was run WITHOUT the λ-sweep — the default for every sweep — and the
    # field is simply absent from the JSON's information content (still serialised
    # so the schema is stable, and ``asdict`` emits ``null``). When populated (only
    # when ``run_cell(..., lambda_scales=[...])`` is given AND agg_method is the
    # linear ``weight_avg``), it is the eval-only acc-vs-λ curve along the line
    # θ⋆(λ) = (1−λ)·θ₀ + λ·θ⋆(1): a list of ``{"lambda": float, "acc": float}``
    # dicts, one per requested λ. λ=0 reproduces standalone θ₀ acc, λ=1 reproduces
    # ``acc``. No retraining — each point reuses the SAME trajectory's {Δ_i}.
    lambda_curve: Optional[List[Dict]] = None
    # Client-side optimizer axis (TIER-1 aggregation study, Axis A). ``None``
    # (the default) means the field is absent from older JSON — those cells ran
    # the historical SGD trajectory; ``run_cell`` sets this to the actual
    # optimizer name (default ``"sgd"``) so every newly-written cell records it.
    optimizer: Optional[str] = None
    # Δ-drift diagnostics over the per-client cumulative displacements {Δ_i}.
    # Populated only in the success path (cheap, CPU). ``delta_norms`` = the list
    # of ‖Δ_i‖₂; ``delta_norm_spread`` = std/mean of those norms (0 if mean 0);
    # ``delta_pairwise_cosine_mean`` = mean over i<j of cosine(Δ_i, Δ_j) (None if
    # N<2). They quantify how the choice of client optimizer spreads / rotates
    # the deltas the server linearly combines. ``None`` on any older JSON / FAIL.
    delta_norms: Optional[List[float]] = None
    delta_norm_spread: Optional[float] = None
    delta_pairwise_cosine_mean: Optional[float] = None

    def to_dict(self) -> Dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Method-name parsing (notebook panel) -> (phase0_kind, kwargs)
# ---------------------------------------------------------------------------
def parse_method(method: str) -> tuple:
    """Map a method name to (phase0_kind, kwargs) following the notebook panel."""
    if method in ("no_phase0",):
        return "none", {}
    if method in ("warmup_only_labelled", "warmup_only"):
        return "warmup_only", {}
    if method in ("labelled_probe_warmup", "labelled"):
        return "labelled", {}
    # Issue 022 — DP-MERF synthetic-basin family (Harder et al. 2021). Checked
    # BEFORE the dp_avg / raw_union / synthetic prefixes: ``merf_basin_…`` and
    # ``dp_synth_all_…`` are distinct tokens (``dp_synth_all`` does NOT match the
    # ``dp_avg`` prefix), but keeping them first makes the two new branches
    # self-evidently separate.
    #   * Mode B — ``merf_basin_eps{E}_K{K}``: DP-MERF on K_per_class samples
    #     builds θ₀; the normal bounded distillation + HE aggregate runs on top
    #     (phase0_kind ``merf``; see phase0.build_probe_merf).
    #   * Mode A — ``dp_synth_all_eps{E}``: DP-MERF on ALL local data; the
    #     student is trained one-shot directly on the synthetic set — no basin,
    #     no distillation, no HE (phase0_kind ``dp_synth_all`` — a SEPARATE
    #     short-circuit branch in run_cell, NOT a basin warmup).
    if method.startswith("merf_basin"):
        # merf_basin_eps2_K20 / merf_basin_eps8_K20 / merf_basin_epsinf_K20
        k = _extract_int_after(method, "K", default=20)
        eps = _extract_eps(method)
        return "merf", {"K_per_class": k, "eps": eps}
    if method.startswith("dp_synth_all"):
        # dp_synth_all_eps2 / dp_synth_all_eps8 / dp_synth_all_epsinf.
        # No K — Mode A uses ALL local data per class (full-data DP one-shot).
        eps = _extract_eps(method)
        return "dp_synth_all", {"eps": eps}
    # Issue 017 — no-probe alignment family. Checked BEFORE the bare
    # raw_union / dp_avg prefixes: the no-probe tokens start with ``noprobe_``
    # so they would never collide, but keeping them first makes the no-probe
    # branch self-evidently distinct. No labelled public probe is consumed; the
    # (raw-union or DP-noisy) per-(client, class) prototypes ARE the supervised
    # warmup set (see phase0.build_noprobe_*).
    if method.startswith("noprobe_raw_union"):
        # noprobe_raw_union_K20 -> K_per_class=20 ; bare -> default 20
        k = _extract_int_after(method, "K", default=20)
        return "noprobe_raw_union", {"K_per_class": k}
    if method.startswith("noprobe_dp_avg"):
        # noprobe_dp_avg_eps2_K20 / noprobe_dp_avg_eps8_K20
        k = _extract_int_after(method, "K", default=20)
        eps = _extract_eps(method)
        return "noprobe_dp_avg", {"K_per_class": k, "eps": eps}
    if method.startswith("raw_union"):
        # raw_union_K20 -> K_per_class=20 ; bare raw_union -> default 20
        k = _extract_int_after(method, "K", default=20)
        return "raw_union", {"K_per_class": k}
    if method.startswith("dp_avg"):
        # dp_avg_eps2_K20 / dp_avg_epsinf_K5
        k = _extract_int_after(method, "K", default=20)
        eps = _extract_eps(method)
        return "dp_avg", {"K_per_class": k, "eps": eps}
    # Issue 016+: synthetic-sample alignment family. Order matters — the more-
    # specific prefixes (synthetic_logit, synthetic_dp) must be checked before
    # the bare ``synthetic_`` prefix.
    if method.startswith("synthetic_logit"):
        # synthetic_logit_K100 -> K_per_class=100 ; bare -> default 20.
        # No DP for this MVP (see build_logit_prototypes' DP-extensibility note).
        k = _extract_int_after(method, "K", default=20)
        return "synthetic_logit", {"K_per_class": k}
    if method.startswith("synthetic_dp"):
        # synthetic_dp_eps2_K100 — DP-protected μ release on the synthetic path.
        k = _extract_int_after(method, "K", default=20)
        eps = _extract_eps(method)
        return "synthetic_dp", {"K_per_class": k, "eps": eps}
    if method.startswith("synthetic"):
        # synthetic_K100 -> K_per_class=100 ; bare synthetic -> default 20.
        k = _extract_int_after(method, "K", default=20)
        return "synthetic", {"K_per_class": k}
    raise ValueError(f"unknown method {method!r}")


def _extract_int_after(s: str, marker: str, default: int) -> int:
    import re

    m = re.search(rf"{marker}(\d+)", s)
    return int(m.group(1)) if m else default


def _extract_eps(s: str) -> float:
    import re

    m = re.search(r"eps([0-9.]+|inf)", s)
    if not m:
        return float("inf")
    tok = m.group(1)
    return float("inf") if tok == "inf" else float(tok)


# ---------------------------------------------------------------------------
# Feature standardization (issue 019 warmup-collapse fix)
# ---------------------------------------------------------------------------
def _apply_feature_normalization(Xtr, Xte, mode: str):
    """Standardize cached features per ``BackboneSpec.normalize_features``.

    ``mode == "none"`` (the default for every pre-019 backbone) is a strict
    no-op: ``Xtr``/``Xte`` are returned UNCHANGED, so the load path is
    byte-identical to the legacy behaviour for resnet18 / vit_b32 / distilbert /
    the from-scratch nets — they never reach this helper with anything but
    "none".

    ``mode == "zscore"`` fits per-feature mean/std on the TRAIN features ONLY
    (``Xtr``) and applies (x − μ)/(σ + eps) to BOTH ``Xtr`` and ``Xte``. Fitting
    on train alone means the test statistics never influence the transform — no
    test→train leakage — while still giving every downstream consumer (warmup
    head, teachers, distillation students, oracle) the SAME standardized inputs.

    ``mode == "l2"`` divides each sample's feature vector by its own L2 norm
    (+eps); this is purely per-sample so there is no fit step and no leakage by
    construction.

    eps = 1e-6 in both standardizing modes.
    """
    if mode == "none":
        return Xtr, Xte
    import torch

    eps = 1e-6
    if mode == "zscore":
        # Fit per-feature statistics on TRAIN ONLY (dim 0), then apply to both.
        mean = Xtr.mean(dim=0, keepdim=True)
        std = Xtr.std(dim=0, unbiased=False, keepdim=True)
        denom = std + eps
        return (Xtr - mean) / denom, (Xte - mean) / denom
    if mode == "l2":
        # Per-sample L2 normalization (no fitted statistics).
        ntr = Xtr.norm(dim=1, keepdim=True) + eps
        nte = Xte.norm(dim=1, keepdim=True) + eps
        return Xtr / ntr, Xte / nte
    raise ValueError(
        f"unknown normalize_features {mode!r}; expected 'none' | 'zscore' | 'l2'"
    )


# ---------------------------------------------------------------------------
# Feature loading per backbone
# ---------------------------------------------------------------------------
def _load_features(
    spec: BackboneSpec,
    data_root: str,
    cache_root: str,
    trainable_scope: str = "head_only",
):
    """Return (X_train, y_train, X_test, y_test, in_dim_or_None, make_model_fn_factory).

    For "scratch" backbones in_dim is None and make_model_fn is parameter-free.
    For "head" backbones in_dim is the feature dim and make_model_fn is built
    from (in_dim, num_classes).

    ``trainable_scope`` (issue 011) selects the head architecture for "head"
    backbones: ``head_only`` (default) keeps the legacy single-Linear path
    byte-identical to pre-issue-011 cells; ``lora_<rank>`` and
    ``last_block`` / ``last_n_blocks_<n>`` dispatch to the expanded-capacity
    factories in ``backbones`` (LoRA-on-head, MLP-on-cached-features). For
    "scratch" backbones a non-default scope raises ``NotImplementedError`` —
    issue 011's focused comparison and acceptance criteria target the
    pretrained-head backbones (resnet18, vit_b32, distilbert) only.
    """
    from . import backbones as bk
    from . import data as dt

    if spec.feature_loader == "mnist":
        if trainable_scope != "head_only":
            raise NotImplementedError(
                f"trainable_scope={trainable_scope!r} is only defined for "
                "head-on-cached-features backbones (issue 011); the "
                "from-scratch MLP path supports 'head_only' only."
            )
        Xtr, ytr, Xte, yte = dt.load_mnist_tensors(data_root, cache_root)
        return Xtr, ytr, Xte, yte, None, bk.make_mnist_mlp
    if spec.feature_loader == "fmnist":
        if trainable_scope != "head_only":
            raise NotImplementedError(
                f"trainable_scope={trainable_scope!r} is only defined for "
                "head-on-cached-features backbones (issue 011); the "
                "from-scratch LeNet-5 path supports 'head_only' only."
            )
        # From-scratch LeNet-5 on raw 1x28x28 FashionMNIST images.
        Xtr, ytr, Xte, yte = dt.load_fmnist_tensors(data_root, cache_root)
        return Xtr, ytr, Xte, yte, None, bk.make_fmnist_lenet5
    if spec.feature_loader == "cifar10_raw":
        if trainable_scope != "head_only":
            raise NotImplementedError(
                f"trainable_scope={trainable_scope!r} is only defined for "
                "head-on-cached-features backbones (issue 011); the "
                "from-scratch CNN-5 path supports 'head_only' only."
            )
        # From-scratch CNN-5 on RAW 3x32x32 CIFAR-10 images (pixel space — NOT the
        # pretrained-feature "cifar10:<backbone>" path below).
        Xtr, ytr, Xte, yte = dt.load_cifar10_raw_tensors(data_root, cache_root)
        return Xtr, ytr, Xte, yte, None, bk.make_cifar10_cnn5
    if spec.feature_loader.startswith("cifar10:"):
        name = spec.feature_loader.split(":", 1)[1]
        Xtr, ytr, Xte, yte, in_dim = bk.extract_cifar10_features(name, data_root, cache_root)
        # Scope-aware head dispatch. ``head_only`` returns the legacy
        # ``make_head`` factory so existing cell hashes/results are unchanged.
        def _head_factory(in_dim_, num_classes_):
            return bk.make_head_for_scope(in_dim_, num_classes_, trainable_scope)
        return Xtr, ytr, Xte, yte, in_dim, _head_factory
    if spec.feature_loader.startswith("cifar100:"):
        # Pretrained-feature path on CIFAR-100 (issue 012). Same head-on-cached-
        # features pattern as CIFAR-10, the only difference is the number of
        # classes and the harder linear-probe ceiling. Scope dispatch is shared.
        name = spec.feature_loader.split(":", 1)[1]
        Xtr, ytr, Xte, yte, in_dim = bk.extract_cifar100_features(name, data_root, cache_root)
        def _head_factory(in_dim_, num_classes_):
            return bk.make_head_for_scope(in_dim_, num_classes_, trainable_scope)
        return Xtr, ytr, Xte, yte, in_dim, _head_factory
    if spec.feature_loader.startswith("tiny_imagenet:"):
        # Pretrained-feature path on Tiny-ImageNet (issue 012). 200 classes,
        # native 64×64 (the extractor upsamples to 224 for the ImageNet
        # backbones). Same head-on-cached-features pattern; same scope
        # dispatch as the CIFAR paths.
        name = spec.feature_loader.split(":", 1)[1]
        Xtr, ytr, Xte, yte, in_dim = bk.extract_tiny_imagenet_features(
            name, data_root, cache_root)
        def _head_factory(in_dim_, num_classes_):
            return bk.make_head_for_scope(in_dim_, num_classes_, trainable_scope)
        return Xtr, ytr, Xte, yte, in_dim, _head_factory
    if spec.feature_loader.startswith("text:"):
        # ``text:<model>``            -> AG-News (legacy default), or
        # ``text:<model>:<dataset>``  -> a specific HF text dataset (issue 019
        #                                Part 2 uses ``dbpedia_14``). The bare
        #                                two-token form is byte-identical to the
        #                                pre-019 path (task_name="ag_news").
        rest = spec.feature_loader.split(":", 1)[1]
        if ":" in rest:
            name, task_name = rest.split(":", 1)
        else:
            name, task_name = rest, "ag_news"
        Xtr, ytr, Xte, yte, in_dim = bk.extract_text_features(name, task_name, data_root, cache_root)
        # Per-backbone feature standardization (issue 019). No-op for
        # ``normalize_features="none"`` (every pre-019 text backbone) so the
        # cached-feature path stays byte-identical there; "zscore"/"l2" applied
        # once here so ALL downstream consumers (warmup, teachers, distill,
        # oracle) see the same standardized X. Fit-on-train avoids test leakage.
        Xtr, Xte = _apply_feature_normalization(Xtr, Xte, spec.normalize_features)
        def _head_factory(in_dim_, num_classes_):
            return bk.make_head_for_scope(in_dim_, num_classes_, trainable_scope)
        return Xtr, ytr, Xte, yte, in_dim, _head_factory
    raise ValueError(spec.feature_loader)


# ---------------------------------------------------------------------------
# The deep module: run_cell
# ---------------------------------------------------------------------------
def run_cell(
    *,
    backbone: str,
    N: int,
    alpha: float,
    seed: int,
    method: str,
    K: int = 300,
    tau: float = _TAU,
    student_lr: float = _STUDENT_LR,
    probe_size: Optional[int] = None,
    data_root: str = "data",
    cache_root: str = "cache",
    job_id: Optional[str] = None,
    node: Optional[str] = None,
    diagnose: bool = False,
    trainable_scope: Optional[str] = None,
    agg_method: str = "weight_avg",
    lambda_scales: Optional[Sequence[float]] = None,
    optimizer: str = "sgd",
) -> CellResult:
    """Run one protocol cell end-to-end and return a CellResult.

    Faithful composition of the notebook task runners. ``K`` is the bounded
    trajectory length (swept hyperparameter; notebook default 300). Aggregation
    is always sample-weighted. ``warmup_only`` short-circuits before distillation
    (its "result" is the warmed model, not a protocol output) — this is the
    probe-only baseline used to isolate what the K-step trajectory adds.

    ``diagnose`` (default ``False``) — when ``False`` this function is
    byte-identical to its pre-issue-013 behaviour (no new code paths execute).
    When ``True`` the distill loop additionally retains per-step deltas, and
    after aggregation the issue-013 diagnostics (teacher entropy / Δ-norm
    profile / pairwise cosine / per-class θ₀-vs-final acc) are computed once
    and stuffed into ``res.diagnostics``. The flag is opt-in and reserved for
    diagnostic cells; sweeps that omit it see zero behaviour change.

    ``trainable_scope`` (default ``None`` -> use the backbone's BackboneSpec
    default, which is ``"head_only"`` everywhere) is the issue-011 lever. When
    set to ``"lora_<rank>"`` / ``"last_block"`` / ``"last_n_blocks_<n>"`` the
    head factory dispatches to the expanded-capacity variants in
    ``backbones`` (LoRA-on-head residual, MLP-on-cached-features). The
    aggregate remains element-wise linear regardless — every trainable tensor
    flows through the same FHE-compatible PT×CT + CT+CT combine — see
    ``aggregate.aggregate`` and ``tests/test_aggregate.py`` for the invariant.

    ``agg_method`` (default ``"weight_avg"``) is the issue-025 server-combine
    selector. The DEFAULT routes the aggregation through the EXISTING linear
    ``aggregate.aggregate(theta0, deltas, weights)`` — byte-identical to the
    pre-025 path — so every sweep that does not opt in sees zero behaviour change.
    Any other value (``mag_weighted`` / ``poly_gate_d2_a`` / … see
    ``aggregate.NONLINEAR_DEPTH``) instead calls ``aggregate.aggregate_nonlinear``
    over the SAME one-shot ``deltas``; the combine's HE depth is recorded in
    ``res.agg_depth``. This is an INVESTIGATION axis (does any non-linear one-shot
    combine beat the flat weighted average under heterogeneity?), NOT a change to
    the production aggregator — distillation semantics are untouched.

    ``lambda_scales`` (default ``None``) is the issue-026 task-arithmetic λ-sweep
    hook. When ``None`` (every existing caller) NO new code runs and this function
    is BYTE-IDENTICAL to its pre-026 behaviour. When a list of floats is supplied
    AND ``agg_method == "weight_avg"`` (the linear aggregate), then AFTER the λ=1
    aggregate is scored, the EVAL-ONLY interpolation θ⋆(λ) = θ₀ + λ·Σ_i w_i·Δ_i is
    additionally scored for each λ using the SAME in-process test eval — no
    retraining, the trajectory's {Δ_i} are reused — and stored in
    ``res.lambda_curve`` as ``[{"lambda": λ, "acc": acc}, …]``. λ stays a public
    scalar so the combine remains depth-1 under CKKS. The hook is a no-op for any
    non-linear ``agg_method`` (the interpolation identity is a linear-aggregate
    property).
    """
    import numpy as np
    import torch

    from . import aggregate as agg
    from . import phase0 as p0
    from .backbones import get_params
    from .data import partition_pool, per_client_per_class_counts, reserve_probe_and_pool
    from .distill import distill_all_clients
    from .evaluate import accuracy_on, ood_accuracy, per_client_gap
    from .teacher import train_supervised_model

    spec = BACKBONES[backbone]
    # Resolve the effective trainable-layer scope (issue 011). ``None`` falls
    # back to the BackboneSpec default, which is ``"head_only"`` for every
    # registered backbone today — so cells written before issue 011 reproduce
    # exactly under the same descriptor/hash.
    effective_scope = (
        trainable_scope if trainable_scope is not None else spec.trainable_scope
    )
    phase0_kind, kwargs = parse_method(method)
    probe_size = spec.labelled_probe_default if probe_size is None else probe_size
    momentum = _TEACHER_MOMENTUM
    nc = spec.num_classes
    # Human-readable dataset label from the feature_loader. Keyed on the prefix
    # so both the from-scratch loaders ("mnist"/"fmnist"/"cifar10_raw") and the
    # pretrained ones ("cifar10:<bb>"/"cifar100:<bb>"/"tiny_imagenet:<bb>"/
    # "text:<bb>") resolve correctly.
    _loader_prefix = spec.feature_loader.split(":")[0]
    # For text backbones the dataset is the optional 3rd ``text:<model>:<ds>``
    # segment (issue 019 Part 2); bare ``text:<model>`` defaults to AG-News so
    # every pre-019 text cell keeps the "AGNews" label byte-identical.
    if _loader_prefix == "text":
        _text_parts = spec.feature_loader.split(":")
        _text_ds = _text_parts[2] if len(_text_parts) > 2 else "ag_news"
        dataset = {"ag_news": "AGNews", "dbpedia_14": "DBpedia14"}.get(
            _text_ds, _text_ds)
    else:
        dataset = {
            "mnist": "MNIST",
            "fmnist": "FashionMNIST",
            "cifar10_raw": "CIFAR10",
            "cifar10": "CIFAR10",
            "cifar100": "CIFAR100",
            "tiny_imagenet": "TinyImageNet",
        }.get(_loader_prefix, "CIFAR10" if "cifar" in spec.feature_loader else "AGNews")

    res = CellResult(
        backbone=backbone, dataset=dataset, N=N, alpha=alpha, seed=seed,
        K=K, tau=tau, method=method, phase0_kind=phase0_kind,
        probe_size_actual=0, sigma=0.0, job_id=job_id, node=node,
        notes=("HE-IFD plaintext simulation: sample-weighted linear aggregate "
               "θ₀+Σ w_i·Δ_i of bounded K-step cumulative displacements; "
               "server op is PT×CT + CT+CT only (FHE-compatible)."),
    )
    # Record the issue-025 server-combine selector + its HE depth up front so
    # even the short-circuit branches (warmup_only / dp_synth_all, which never
    # reach the aggregate step) carry the chosen agg_method through to the JSON.
    # ``weight_avg`` (the default) is depth-1 and routes to the linear aggregate.
    from .aggregate import NONLINEAR_DEPTH as _NL_DEPTH
    res.agg_method = agg_method
    res.agg_depth = _NL_DEPTH.get(agg_method, "depth-1")
    # Client-optimizer axis (default "sgd" → byte-identical trajectory). Recorded
    # up front so even short-circuit branches carry it through to the JSON.
    res.optimizer = optimizer
    t_start = time.time()
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"

        # --- data: load features, reserve labelled probe, partition the pool ---
        # Scope plumbed through so "head" backbones can swap make_head ->
        # make_lora_head / make_mlp_head per issue 011 without touching the
        # feature-cache logic. From-scratch backbones ignore the scope (they
        # accept only "head_only"; non-trivial scopes raise NotImplementedError
        # one level down).
        Xtr, ytr, Xte, yte, in_dim, model_fn_src = _load_features(
            spec, data_root, cache_root, trainable_scope=effective_scope,
        )
        Xte_dev = Xte.to(device)
        yte_dev = yte.to(device)

        make_model_fn = model_fn_src() if spec.kind == "scratch" else model_fn_src(in_dim, nc)

        # Per-sample shape (everything after dim 0). For the MLP / pretrained
        # heads this is (D,) — already flat. For the conv backbones it is
        # (C, H, W). The dp_avg Phase-0 mechanism is defined in FLAT feature
        # space (it L2-clips, averages and Gaussian-noises per-feature), so for
        # image-shaped data we flatten into it and reshape its probe back to the
        # image shape before warmup. raw_union/none/labelled/warmup_only need no
        # such bridge — they index/concat along dim 0 only and so flow with the
        # native shape straight into the conv net. (See data.py shape contract.)
        sample_shape = tuple(Xtr.shape[1:])
        is_image = len(sample_shape) > 1

        flat_dim = 1
        for _d in sample_shape:
            flat_dim *= int(_d)

        def _flatten_clients(xs):
            """Flatten a list of per-client tensors to (n_i, prod(sample_shape)).

            At extreme heterogeneity (N=50, α=0.01) the Dirichlet partition can
            hand a client ZERO samples — its tensor is (0, C, H, W), 0 elements.
            ``x.reshape(0, -1)`` then raises because ``-1`` is ambiguous on an
            empty tensor. We use the explicit trailing dim ``flat_dim`` so the
            inferred axis is never the size-0 one; for a non-empty client this is
            identical to ``reshape(n_i, -1)`` (flat_dim == prod(sample_shape)),
            so the non-pathological path is byte-identical. raw_union never hits
            this bridge (it keeps native shape), which is why only dp_avg /
            synthetic / synthetic_dp failed at the corner."""
            return [x.reshape(x.shape[0], flat_dim) for x in xs]

        def _reshape_probe_to_image(probe_X_flat):
            """Reshape a flat dp_avg probe (P, prod(sample_shape)) back to images
            (P, C, H, W) so the conv warmup consumes the same shape as training.

            Guard the all-empty pathological case (every class had zero
            contributors -> P == 0): ``reshape(0, *sample_shape)`` is well-defined
            (no ambiguous ``-1``), but we build the empty tensor explicitly to be
            unambiguous and dtype/-device-stable. For P > 0 this is identical to
            the original reshape."""
            if probe_X_flat.shape[0] == 0:
                import torch as _torch
                return _torch.empty(
                    (0, *sample_shape),
                    dtype=probe_X_flat.dtype, device=probe_X_flat.device,
                )
            return probe_X_flat.reshape(probe_X_flat.shape[0], *sample_shape)

        probe_X, probe_y, pool_X, pool_y = reserve_probe_and_pool(Xtr, ytr, probe_size, seed)
        client_X_list, client_y_list, sample_sizes = partition_pool(
            pool_X, pool_y, N, alpha, seed, nc)
        res.per_client_total = [int(s) for s in sample_sizes]
        res.per_client_per_class = per_client_per_class_counts(client_y_list, nc)

        def eval_model(m):
            return accuracy_on(m, Xte_dev, yte_dev)

        def theta0_test_acc(params):
            """Standalone θ₀ accuracy: build a model from the aligned init params
            and evaluate it on the test set, BEFORE any local distillation."""
            m = make_model_fn()
            m.load_state_dict(params)
            return float(eval_model(m))

        def populate_incentive_ood(final_student):
            """Populate M3 (per-client gap on D_i) and M4 (OOD-class acc) on the
            CellResult. Reuses the already-trained ``teachers`` and the
            per-client partition tensors — trains nothing, decodes nothing."""
            m3 = per_client_gap(final_student, teachers, client_X_list, client_y_list)
            res.m3_student_acc_on_Di = m3["student_acc"]
            res.m3_teacher_acc_on_Di = m3["teacher_acc"]
            res.m3_gap = m3["gap"]
            res.m3_mean_gap = m3["mean_gap"]
            res.m3_clients_helped = m3["n_clients_helped"]
            res.m3_clients_evaluated = m3["n_clients_evaluated"]
            m4 = ood_accuracy(final_student, Xte_dev, yte_dev, res.per_client_per_class)
            res.m4_ood_acc = m4["per_client"]
            res.m4_mean = m4["mean"]
            res.m4_clients_evaluated = m4["n_clients_evaluated"]

        # --- teachers (one per client) + oracle reference ---
        t0 = time.time()
        teachers, t_accs = [], []
        for i in range(N):
            if sample_sizes[i] == 0:
                teachers.append(make_model_fn())
                t_accs.append(1.0 / nc)
                continue
            t = train_supervised_model(
                make_model_fn, client_X_list[i], client_y_list[i],
                epochs=spec.teacher_epochs, lr=spec.teacher_lr,
                momentum=momentum, bs=spec.bs, seed=seed * 1000 + i,
                lr_schedule=spec.teacher_lr_schedule)
            teachers.append(t)
            t_accs.append(eval_model(t))
        res.per_teacher_acc = [float(a) for a in t_accs]
        res.mean_teacher = float(np.mean(t_accs))
        res.best_teacher = float(np.max(t_accs))

        oracle_m = train_supervised_model(
            make_model_fn, pool_X, pool_y, epochs=spec.oracle_epochs,
            lr=spec.teacher_lr, momentum=momentum, bs=spec.bs, seed=seed * 7919,
            lr_schedule=spec.teacher_lr_schedule)
        res.oracle = float(eval_model(oracle_m))
        res.phase_teacher_sec = time.time() - t0

        # --- Phase 0: build θ₀ for the chosen strategy ---
        t0 = time.time()
        torch.manual_seed(seed)
        init_params = get_params(make_model_fn())  # fresh random init

        # The augmented-probe tensors the warmup actually consumes. Tracked
        # purely so issue-013 diagnostics (when ``diagnose=True``) can compute
        # teacher entropy on the same tensor that warmed θ₀. ``None`` for
        # ``no_phase0`` and ``warmup_only`` (the latter returns before
        # distillation anyway). Not used unless ``diagnose=True``.
        align_X = None

        clip = None
        if phase0_kind in ("dp_avg", "synthetic_dp", "noprobe_dp_avg"):
            # Percentile feature-norm clip in flat space (image data -> flatten).
            # Shared between dp_avg, synthetic_dp and noprobe_dp_avg because all
            # three apply the averaging-variant Gaussian mechanism to the
            # per-(client, class) mean μ_ic; sensitivity = clip / K_per_class is
            # identical.
            clip = p0.compute_feature_norms_percentile(
                pool_X.reshape(pool_X.shape[0], -1) if is_image else pool_X)

        if phase0_kind == "none":
            theta0 = init_params  # no alignment: θ₀ is the fresh random init
            res.probe_size_actual = 0
            res.sigma = 0.0
            res.theta0_acc = theta0_test_acc(theta0)

        elif phase0_kind == "warmup_only":
            # Probe-only baseline: warm on the labelled probe, NO distillation.
            theta0 = p0.warmup_init(
                make_model_fn, probe_X, probe_y, init_params,
                epochs=spec.warmup_epochs, lr=spec.teacher_lr,
                momentum=momentum, bs=spec.bs,
                lr_schedule=spec.teacher_lr_schedule)
            res.phase_phase0_sec = time.time() - t0
            warmed = make_model_fn()
            warmed.load_state_dict(theta0)
            t0e = time.time()
            res.acc = float(eval_model(warmed))
            # θ₀ IS the output here (no distillation), so standalone-θ₀ acc == acc;
            # M3/M4 are reported against the warmed model so the probe-only
            # baseline row is complete rather than empty.
            res.theta0_acc = res.acc
            populate_incentive_ood(warmed)
            res.phase_eval_sec = time.time() - t0e
            res.probe_size_actual = int(probe_size)
            res.sigma = 0.0
            res.sample_weights = agg.sample_weights(sample_sizes)
            res.wall_clock_sec = time.time() - t_start
            res.status = "success"
            return res

        elif phase0_kind == "dp_synth_all":
            # Issue 022 — Mode A: DP-synthesize-EVERYTHING (the naive DP-one-shot
            # baseline, cf. FedDiff). Each client fits DP-MERF to ALL of its
            # local data; the union of synthetic sets carries the whole
            # contribution and the student is trained ONE-SHOT directly on it.
            # NO shared basin, NO bounded distillation, NO HE benefit — this is a
            # SEPARATE short-circuit branch (like warmup_only), deliberately
            # distinct from the basin+distill+aggregate path. Covering every
            # sample at meaningful ε forces large DP noise, so accuracy is
            # expected to drop and the released model stays MIA-vulnerable — the
            # contrast against Mode B (merf_basin_*). The synthetic set lives in
            # FLAT feature space (RFF map per flat dim); for conv backbones we
            # flatten the per-client tensors going in and reshape the synthetic
            # set back to images for the from-scratch trainer — reusing the SAME
            # bridge as the synthetic path.
            flat_image = is_image
            synth_clients = (
                _flatten_clients(client_X_list) if flat_image else client_X_list)
            synth_X, synth_y, info = p0.build_dp_synth_all(
                synth_clients, client_y_list, num_classes=nc,
                seed=seed * 100003, eps=kwargs.get("eps"))
            if flat_image:
                synth_X = _reshape_probe_to_image(synth_X)
            res.phase_phase0_sec = time.time() - t0
            # Train the student one-shot directly on the synthetic union, from a
            # fresh init, with the oracle's epoch/LR budget (the natural "train
            # a classifier on the released synthetic data" recipe — more epochs
            # than a 5-epoch warmup so the baseline gets a fair shot).
            t0d = time.time()
            student = train_supervised_model(
                make_model_fn, synth_X, synth_y,
                epochs=spec.oracle_epochs, lr=spec.teacher_lr,
                momentum=momentum, bs=spec.bs, seed=seed * 100019,
                init_params=init_params,
                lr_schedule=spec.teacher_lr_schedule)
            res.phase_distill_sec = time.time() - t0d
            final_params = get_params(student)
            t0e = time.time()
            res.acc = float(eval_model(student))
            # No basin here, so there is no separate θ₀: report the fresh-init
            # accuracy as theta0_acc for column parity with the basin methods.
            res.theta0_acc = theta0_test_acc(init_params)
            populate_incentive_ood(student)
            res.phase_eval_sec = time.time() - t0e
            res.probe_size_actual = int(info["synth_size"])
            res.sigma = float(info["sigma"])
            res.notes += (
                " | Mode-A DP-MERF synthesize-everything (no basin/distill/HE): "
                f"{info.get('dp_note', '')}")
            res.sample_weights = agg.sample_weights(sample_sizes)
            res.wall_clock_sec = time.time() - t_start
            res.status = "success"
            return res

        elif phase0_kind == "labelled":
            theta0 = p0.warmup_init(
                make_model_fn, probe_X, probe_y, init_params,
                epochs=spec.warmup_epochs, lr=spec.teacher_lr,
                momentum=momentum, bs=spec.bs,
                lr_schedule=spec.teacher_lr_schedule)
            align_X = probe_X       # for issue-013 entropy (no-op unless diagnose=True)
            res.probe_size_actual = int(probe_size)
            res.sigma = 0.0
            res.theta0_acc = theta0_test_acc(theta0)

        elif phase0_kind in ("raw_union", "dp_avg", "synthetic", "synthetic_dp", "merf"):
            probe_seed = seed * 100003
            # raw_union selects raw samples (preserves the native image shape).
            # dp_avg / synthetic / synthetic_dp / merf work in flat feature space
            # (the μ/σ² / RFF statistics are defined per-feature-dim), so for
            # image data we flatten the per-client tensors going in and reshape
            # the returned (P, C*H*W) probe back to (P, C, H, W) coming out —
            # keeping phase0.py and the conv warmup input shape-consistent
            # without touching aggregation/distill. ``merf`` (issue 022, Mode B)
            # is a DP-MERF basin source: it is treated identically to
            # ``synthetic`` from run_cell's perspective — build a flat probe,
            # warm θ₀ on it, then run the SAME bounded distillation + HE
            # aggregate below (the bulk is HE-protected). The DP noise on the
            # released RFF mean embedding is calibrated inside build_probe_merf
            # via the repo's dp_sigma, so no external ``clip`` is needed.
            flat_image = is_image and phase0_kind in (
                "dp_avg", "synthetic", "synthetic_dp", "merf")
            probe_clients = _flatten_clients(client_X_list) if flat_image else client_X_list
            align_X, align_y, info = p0.build_probe(
                phase0_kind, client_X_list=probe_clients, client_y_list=client_y_list,
                num_classes=nc, K_per_class=kwargs.get("K_per_class"),
                eps=kwargs.get("eps"), clip=clip, seed=probe_seed)
            if flat_image:
                align_X = _reshape_probe_to_image(align_X)
            theta0 = p0.warmup_init(
                make_model_fn, align_X, align_y, init_params,
                epochs=spec.warmup_epochs, lr=spec.teacher_lr,
                momentum=momentum, bs=spec.bs,
                lr_schedule=spec.teacher_lr_schedule)
            res.probe_size_actual = int(info["probe_size"])
            res.sigma = float(info["sigma"])
            res.theta0_acc = theta0_test_acc(theta0)

        elif phase0_kind in ("noprobe_raw_union", "noprobe_dp_avg"):
            # Issue 017 — NO labelled public probe. The (raw-union or DP-noisy)
            # per-(client, class) prototypes ARE the supervised warmup set: each
            # prototype is one feature-space sample with its class as the label
            # (~num_classes × N_contributors points). θ₀ is therefore warmed on a
            # deliberately WEAK, possibly-noisy set; the K-step distillation must
            # carry the learning above it. probe_X (the held-out labelled probe)
            # is NEVER touched on this path.
            #
            # The no-probe builders always emit FLAT-space prototypes (the
            # per-feature μ statistics are defined per flat dim), so for image
            # backbones we flatten the per-client tensors going in and reshape
            # the returned (P, C*H*W) prototype set back to (P, C, H, W) for the
            # conv warmup — reusing the SAME flatten/reshape bridge as the
            # dp_avg path (``_flatten_clients`` / ``_reshape_probe_to_image``),
            # not a duplicate.
            probe_seed = seed * 100003
            flat_image = is_image
            probe_clients = _flatten_clients(client_X_list) if flat_image else client_X_list
            align_X, align_y, info = p0.build_probe(
                phase0_kind, client_X_list=probe_clients, client_y_list=client_y_list,
                num_classes=nc, K_per_class=kwargs.get("K_per_class"),
                eps=kwargs.get("eps"), clip=clip, seed=probe_seed)
            if flat_image:
                align_X = _reshape_probe_to_image(align_X)
            theta0 = p0.warmup_init(
                make_model_fn, align_X, align_y, init_params,
                epochs=spec.warmup_epochs, lr=spec.teacher_lr,
                momentum=momentum, bs=spec.bs,
                lr_schedule=spec.teacher_lr_schedule)
            res.probe_size_actual = int(info["probe_size"])
            res.sigma = float(info["sigma"])
            res.theta0_acc = theta0_test_acc(theta0)

        elif phase0_kind == "synthetic_logit":
            # Issue 016+ NOVEL — synthetic-sample payload composed with per-
            # class teacher-logit prototypes. The synthetic samples flow
            # through the same flat → reshape bridge as ``synthetic`` (they
            # are also Gaussian-around-mean in flat feature space). The logit
            # prototypes are computed on the NATIVE-shape per-client tensors
            # because they pass through the trained teachers, which were
            # trained on the native shape.
            probe_seed = seed * 100003
            flat_image = is_image
            # Synthetic-sample generation (Gaussian-around-mean) is defined in
            # FLAT feature space, so it consumes the flattened per-client
            # tensors — same bridge as the ``synthetic`` path. But the logit
            # prototypes run the per-client tensors THROUGH the teachers, which
            # were trained on the NATIVE shape; feeding them flat tensors was
            # the conv2d-shape bug (issue 016b). So we hand the synthetic path
            # the flattened list and the teacher path the native-shape list.
            # For non-image (pretrained-feature) backbones native IS flat, so
            # both lists are identical and this split is a no-op.
            probe_clients = _flatten_clients(client_X_list) if flat_image else client_X_list
            align_X, align_y, soft_labels, info = (
                p0.build_probe_synthetic_with_logits(
                    client_X_list=probe_clients,           # flat: synthetic-sample path
                    client_y_list=client_y_list,
                    teachers=teachers,                     # native-shape teachers
                    K_per_class=kwargs.get("K_per_class"),
                    num_classes=nc,
                    seed=probe_seed,
                    teacher_client_X_list=client_X_list,   # native: logit-prototype path
                )
            )
            if flat_image:
                align_X = _reshape_probe_to_image(align_X)
            theta0 = p0.warmup_init(
                make_model_fn, align_X, align_y, init_params,
                epochs=spec.warmup_epochs, lr=spec.teacher_lr,
                momentum=momentum, bs=spec.bs,
                lr_schedule=spec.teacher_lr_schedule,
                soft_targets=soft_labels,
            )
            res.probe_size_actual = int(info["probe_size"])
            res.sigma = float(info.get("sigma", 0.0))
            res.theta0_acc = theta0_test_acc(theta0)
        else:
            raise ValueError(phase0_kind)
        res.phase_phase0_sec = time.time() - t0

        # --- distillation: each client runs the bounded K-step trajectory -> Δ_i ---
        # ``diagnose=False`` (the sweep default) takes the byte-identical path
        # — distill_all_clients returns only the cumulative Δ list. With
        # ``diagnose=True`` the per-step trajectories are additionally collected
        # so src.diagnostics can compute the per-step ‖Δ⁽ᵏ⁾‖₂ profile (issue 013).
        t0 = time.time()
        if diagnose:
            deltas, step_deltas_per_client = distill_all_clients(
                teachers, theta0, make_model_fn, client_X_list,
                K_steps=K, lr=student_lr, momentum=0.0, tau=tau, bs=spec.bs,
                diagnose=True, optimizer=optimizer,
            )
        else:
            deltas = distill_all_clients(
                teachers, theta0, make_model_fn, client_X_list,
                K_steps=K, lr=student_lr, momentum=0.0, tau=tau, bs=spec.bs,
                optimizer=optimizer)
            step_deltas_per_client = None
        res.phase_distill_sec = time.time() - t0

        # --- Δ-drift diagnostics over the per-client cumulative {Δ_i} ---
        # Cheap, CPU-side. Each Δ_i is flattened to a single vector; we record
        # the per-client L2 norms, their std/mean spread, and the mean pairwise
        # cosine. These quantify how the client-optimizer choice (Axis A)
        # disperses / rotates the deltas the server linearly combines.
        _flat = [
            torch.cat([t.detach().reshape(-1).float().cpu() for t in d.values()])
            for d in deltas
        ]
        _norms = [float(v.norm()) for v in _flat]
        res.delta_norms = _norms
        if _norms:
            _mean = sum(_norms) / len(_norms)
            if _mean != 0.0:
                _var = sum((x - _mean) ** 2 for x in _norms) / len(_norms)
                res.delta_norm_spread = float((_var ** 0.5) / _mean)
            else:
                res.delta_norm_spread = 0.0
        if len(_flat) >= 2:
            _cos = []
            for _i in range(len(_flat)):
                for _j in range(_i + 1, len(_flat)):
                    _ni, _nj = _norms[_i], _norms[_j]
                    if _ni > 0 and _nj > 0:
                        _cos.append(float(torch.dot(_flat[_i], _flat[_j])) / (_ni * _nj))
                    else:
                        _cos.append(0.0)
            res.delta_pairwise_cosine_mean = float(sum(_cos) / len(_cos)) if _cos else None

        # --- aggregate: θ = θ₀ + Σ_i w_i·Δ_i (sample-weighted, linear-only) ---
        # ``agg_method == "weight_avg"`` (the default) takes the EXACT pre-025
        # linear path: agg.aggregate(theta0, deltas, weights) — byte-identical.
        # A non-default agg_method (issue 025) instead applies the chosen one-shot
        # combine over the SAME ``deltas`` via agg.aggregate_nonlinear; the
        # distillation that produced ``deltas`` is unchanged regardless.
        t0 = time.time()
        weights = agg.sample_weights(sample_sizes)
        res.sample_weights = weights
        if agg_method == "weight_avg":
            final_params = agg.aggregate(theta0, deltas, weights)
        else:
            final_params = agg.aggregate_nonlinear(
                theta0, deltas, weights, method=agg_method)
        res.phase_aggregate_sec = time.time() - t0

        # --- evaluate: IID acc + M3 (per-client gap) + M4 (OOD-class acc) ---
        # θ₀_acc was recorded above right after warmup (before distill); M3/M4
        # reuse the trained teachers + per-client tensors, so no retraining here.
        t0 = time.time()
        model = make_model_fn()
        model.load_state_dict(final_params)
        res.acc = float(eval_model(model))
        populate_incentive_ood(model)

        # --- (optional) issue-026 task-arithmetic λ-sweep (EVAL-ONLY) ---
        # Strictly opt-in: only fires when ``lambda_scales`` is provided AND the
        # combine is the linear ``weight_avg`` (the interpolation identity
        # θ⋆(λ) = θ₀ + λ·Σ w_iΔ_i = (1−λ)θ₀ + λθ⋆(1) is a linear-aggregate
        # property). When ``lambda_scales is None`` — every existing caller —
        # this block does not execute and the CellResult is byte-identical to
        # the pre-026 path (``res.lambda_curve`` stays ``None``). Each λ reuses
        # the SAME {deltas}: no distillation, no retraining — one ``aggregate``
        # call (a public-scalar reweight, still depth-1) + one test eval per λ.
        if lambda_scales is not None and agg_method == "weight_avg":
            curve = []
            for lam in lambda_scales:
                lam = float(lam)
                theta_lam = agg.aggregate(theta0, deltas, weights, lambda_scale=lam)
                m_lam = make_model_fn()
                m_lam.load_state_dict(theta_lam)
                curve.append({"lambda": lam, "acc": float(eval_model(m_lam))})
            res.lambda_curve = curve

        res.phase_eval_sec = time.time() - t0

        # --- (optional) issue-013 KD-dynamics diagnostics ---
        # Strictly opt-in. When ``diagnose=False`` this block does not run and
        # ``res.diagnostics`` stays ``None`` (the default) — so the produced
        # CellResult is unchanged from the pre-issue-013 sweep behaviour.
        if diagnose:
            from .diagnostics import build_diagnostics

            res.diagnostics = build_diagnostics(
                teachers=teachers,
                align_X=align_X,
                align_y=None,
                client_X_list=client_X_list,
                deltas=deltas,
                step_deltas_per_client=step_deltas_per_client,
                theta0_params=theta0,
                final_params=final_params,
                make_model_fn=make_model_fn,
                X_test=Xte_dev,
                y_test=yte_dev,
                num_classes=nc,
                bs=spec.bs,
            )

        res.status = "success"
    except Exception as exc:  # noqa: BLE001 — record failure, keep sweep alive
        import traceback

        res.status = "FAIL"
        res.error = "".join(traceback.format_exception_only(type(exc), exc)).strip()
        res.notes += f" | traceback: {traceback.format_exc()[-800:]}"
    res.wall_clock_sec = time.time() - t_start
    return res
