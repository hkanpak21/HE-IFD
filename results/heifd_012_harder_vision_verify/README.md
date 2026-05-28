# heifd_012_harder_vision_verify

Issue 012 — verify wrapper for the harder-vision-dataset extension (CIFAR-100,
optionally Tiny-ImageNet). HE-IFD plaintext simulation of the one-shot federated
distillation protocol: each client distils its own teacher into a student over a
bounded K-step trajectory from a shared, Phase-0-aligned init θ₀, then uploads
the cumulative trainable-parameter displacement Δ_i = θ_i^(K) − θ₀; the server's
only operation is the sample-weighted linear combine θ₀ + Σ_i w_i·Δ_i. ViT-B/32
on CIFAR-10 saturates at 0.97 IID (issue 008 STATUS) — no headroom to
demonstrate distillation value. This case exercises the new BACKBONES entries
(`vit_b32_cifar100`, `resnet18_cifar100`, plus the Tiny-ImageNet pair if
included) on the minimal 4-cell grid that establishes whether the protocol
now has measurable headroom on CIFAR-100's ~0.75-0.80 ViT linear-probe ceiling.

## Status — pending VALAR submission

The orchestrator will populate this README with verify-cell results after the
`heifd_012_harder_vision_verify.sh` job lands. Acceptance gates (per issue 012):

- ViT/CIFAR-100 IID linear-probe headline (θ₀ or oracle) ≥ 0.60 (expected
  0.75-0.80 from the literature on ImageNet-pretrained ViT linear probes).
- ViT/CIFAR-100 raw_union_K20 > θ₀ at α=0.05 — the headline question issue
  012 was created to answer. If yes, ViT saturation explained CIFAR-10's
  lack of headroom in issue 008.
- ResNet/CIFAR-100 raw_union_K20 in a sensible 0.50-0.65 range with θ₀
  comparable (the harder dataset should also relax the issue-008 finding
  that ResNet-18/CIFAR-10 had θ₀=0.74 vs final=0.48 at α=0.05).
- (Optional, if Tiny-ImageNet included) ViT IID 0.55-0.65, ResNet 0.45-0.55.

## Sweep configuration

- Backbones: `vit_b32_cifar100,resnet18_cifar100` (CIFAR-100 always);
  `vit_b32_tiny_imagenet,resnet18_tiny_imagenet` added when
  `HEIFD_012_INCLUDE_TINY=1` is set in the submit env.
- N: 16 · Dirichlet α: 0.05 · Methods: `no_phase0,raw_union_K20`
- Seed: 42 (single seed; this is a verify, not the headline grid)
- KD hparams: K=100, τ=1, lr=0.001 (issue 010's best defaults for the
  pretrained-head regime; issue 011 confirmed `head_only` scope is sufficient).
- Labelled-probe size: backbone-default (`labelled_probe_default=300` for the
  CIFAR-100 entries, `=600` for the Tiny-ImageNet entries — ~3 samples/class).

## Triggering

```sh
# CIFAR-100 + Tiny-ImageNet must be pre-fetched on the login node first.
ssh valar 'cd /scratch/hkanpak21/HE_IFD && source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh && conda activate he_ofl && python jobs/prefetch_login.py --include-cifar100 --include-tiny-imagenet'

# Then submit the verify (CIFAR-100 only):
sbatch jobs/heifd_012_harder_vision_verify.sh
# Or include Tiny-ImageNet:
sbatch --export=ALL,HEIFD_012_INCLUDE_TINY=1 jobs/heifd_012_harder_vision_verify.sh
```

## Reading the results

Once the job lands, per-cell JSONs (`cell_<bb>_N16_a0.05_<method>_s42_K100_*.json`)
contain `acc`, `theta0_acc`, `mean_teacher`, `oracle`, and the M3/M4 diagnostic
fields. The auto-writer fills in the results table below.
