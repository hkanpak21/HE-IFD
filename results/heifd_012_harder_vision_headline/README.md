# heifd_012_harder_vision_headline

Issue 012 — full-grid headline sweep on the harder-vision-dataset extension.
Mirrors `heifd_pretrained_headline` (issue 008) but on CIFAR-100 (and
optionally Tiny-ImageNet) rather than the saturated CIFAR-10 / ViT pair.

HE-IFD plaintext simulation of the one-shot federated distillation protocol:
each client distils its own teacher into a student over a bounded K-step
trajectory from a shared, Phase-0-aligned init θ₀, then uploads the cumulative
trainable-parameter displacement Δ_i = θ_i^(K) − θ₀; the server's only
operation is the sample-weighted linear combine θ₀ + Σ_i w_i·Δ_i (w_i =
n_i/Σ_j n_j), which uses PT×CT and CT+CT only and is thus FHE-compatible by
construction. IID test accuracy is the lead metric, with mean/best teacher
and a centralised oracle as references, plus the standalone accuracy of the
aligned init θ₀, M3 (per-client teacher-vs-aggregate gap), and M4 (per-client
accuracy on classes a client held zero local examples of).

## Status — pending verify gate

This job runs **only after** `heifd_012_harder_vision_verify.sh` produces
sensible numbers (ViT/CIFAR-100 IID ≥ 0.60 + `raw_union > θ₀` at α=0.05). The
orchestrator handles the gate.

## Sweep configuration (per backbone)

- Backbones: one of `vit_b32_cifar100` (highest-value cell — the cell issue
  012 was created to enable), `resnet18_cifar100`, `vit_b32_tiny_imagenet`,
  `resnet18_tiny_imagenet`. ONE per job (set via `HEIFD_BACKBONE`).
- N: `1,5,10,20,50` (Phase II N-grid per `docs/prd/he-ifd-tnse-resubmission.md`)
- Dirichlet α: `0.01,0.05,0.1,0.3,1.0`
- Methods: `no_phase0,warmup_only_labelled,labelled_probe_warmup,raw_union_K20,dp_avg_eps2_K20,dp_avg_eps8_K20`
- Seeds: `42,43,44` (3-seed replication for mean ± std)
- KD: K=100, τ=1, lr=0.001 (issue 010 best defaults for the pretrained-head regime)
- Scope: `head_only` (issue 011 confirmed sufficient)
- Per-backbone cell count: 5 × 5 × 6 × 3 = **450 cells**
- Chunking: SLURM job-array (`--array=0-7 --export=ALL,NUM_CHUNKS=8`) so each
  chunk lands well under the 3h VALAR cap.

## Triggering

```sh
# Verify gate first (see results/heifd_012_harder_vision_verify/README.md).

# Then submit the full grid for the headline cell (ViT/CIFAR-100):
sbatch --array=0-7 --export=ALL,HEIFD_BACKBONE=vit_b32_cifar100,NUM_CHUNKS=8 \
       jobs/heifd_012_harder_vision_headline.sh

# Optionally extend to ResNet/CIFAR-100 + Tiny-ImageNet backbones:
sbatch --array=0-7 --export=ALL,HEIFD_BACKBONE=resnet18_cifar100,NUM_CHUNKS=8 \
       jobs/heifd_012_harder_vision_headline.sh
sbatch --array=0-7 --export=ALL,HEIFD_BACKBONE=vit_b32_tiny_imagenet,NUM_CHUNKS=8 \
       jobs/heifd_012_harder_vision_headline.sh
sbatch --array=0-7 --export=ALL,HEIFD_BACKBONE=resnet18_tiny_imagenet,NUM_CHUNKS=8 \
       jobs/heifd_012_harder_vision_headline.sh
```

## Acceptance (issue 012)

- Each (backbone, dataset) cell hits the defensibility criteria from the
  Phase II PRD section: `raw_union > no_phase0`, `raw_union ≥ θ₀` in *most*
  regimes, `raw_union → oracle` as α → 1.0, `M4 > 0` at low α.
- The full grid lands resumably within the 3h-per-chunk wall-clock budget
  (otherwise we tune `NUM_CHUNKS`).

The auto-writer will fill the results table below as the per-cell JSONs land.
