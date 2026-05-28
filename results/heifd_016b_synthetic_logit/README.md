# heifd_016b_synthetic_logit

Re-runs the `synthetic_logit_K100` arm after the conv2d shape-bug fix. In issue
016 every `synthetic_logit_K100` cell on CNN-5 crashed with
`RuntimeError: Expected 3D/4D input to conv2d`: the synthetic_logit Phase-0 path
fed FLATTENED (n_i, 3072) per-client tensors to `build_logit_prototypes`, which
runs them through the conv teachers (`teacher(X_i)`) — conv2d rejects flat
input. Plain `synthetic_K100` survived because it only samples in flat feature
space (no teacher forward pass). The fix (src/protocol.py + src/phase0.py) feeds
the synthetic-sample path flat tensors and the logit-prototype path native-shape
tensors; it is a no-op for pretrained-feature backbones (native IS flat).

## The run

Two backbones, two KD configs, one case:

- **`cnn5_cifar10`** (from-scratch conv — the case that failed): K=300 / τ=4 /
  lr=0.01, the legacy from-scratch defaults, to match the ORIGINAL failing
  config and confirm the shape fix works.
- **`resnet18_cifar10`** (pretrained linear head — synthetic samples live in
  smooth cached-feature space, not pixel space, so should behave far better):
  K=100 / τ=1 / lr=0.001, the issue-010 resnet18 best.

Methods on both: `synthetic_logit_K100` (the fixed novel arm) +
`synthetic_K100` (plain synthetic, isolates the logit modality) +
`raw_union_K20` (minimal-leak baseline).

## Read-out

- Primary: confirm `synthetic_logit_K100` RUNS (no conv2d crash) on cnn5.
- Compare `synthetic_logit_K100` vs `synthetic_K100` vs `raw_union_K20` on
  `theta0_acc` + `acc` + `m4_ood` — does the orthogonal teacher-logit modality
  lift the aligned init / OOD acc over plain feature prototypes?
- Cross-backbone: synthetic samples in resnet18 feature space should behave far
  better than in cnn5 pixel space.

## Sweep configuration

- Backbones: `cnn5_cifar10` (K=300, τ=4, lr=0.01) + `resnet18_cifar10`
  (K=100, τ=1, lr=0.001)
- N: `16`; seed: `42`
- Dirichlet α: `0.05, 1.0`
- Methods: `synthetic_logit_K100, synthetic_K100, raw_union_K20`
- Grid: 3 methods × 2 backbones × 2 α = **12 cells**

## Results

<!-- auto-populated by src/report.py on the VALAR side after the run -->

Raw per-cell JSONs live here as
`cell_<backbone>_N<n>_a<α>_<method>_s<seed>_K<k>_<hash>.json`.
