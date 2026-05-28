# heifd_012_harder_vision_verify

Issue 012 verify — does the protocol show measurable distillation value on CIFAR-100 where ViT-B/32 has actual headroom (linear-probe ceiling ~0.85 vs CIFAR-10's saturated 0.97)? 4 cells × seed 42 at N=16, α=0.05, K=100, τ=1, lr=0.001 (issue-010 best defaults), `head_only` scope (issue-011 finding).

## Verdict — **CIFAR-100 unlocks the protocol's defensibility on the pretrained-vision deployment story**

Every defensibility criterion passes. **ViT-B/32 / CIFAR-100 / α=0.05 / N=16 is the strongest paper-defensible cell we have so far.**

| Backbone | Method | acc | θ₀ | mean_t | best_t | oracle | m3_gap | m4_ood | acc / oracle |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **ViT-B/32** | raw_union_K20 | **0.8305** | 0.8252 | 0.184 | 0.289 | 0.8692 | −0.130 | **0.828** | **95.5%** |
| ViT-B/32 | no_phase0 | 0.0248 | 0.0121 | 0.184 | 0.289 | 0.8692 | −0.954 | 0.023 | 2.9% |
| **ResNet-18** | raw_union_K20 | **0.5385** | 0.5237 | 0.111 | 0.166 | 0.6661 | −0.296 | **0.532** | 80.8% |
| ResNet-18 | no_phase0 | 0.0172 | 0.0161 | 0.111 | 0.166 | 0.6661 | −0.837 | 0.016 | 2.6% |

### Defensibility-bar checks (Phase II PRD)

- **raw_union > no_phase0**: ViT 33×, ResNet 32× — alignment is the structural lever.
- **raw_union ≥ θ₀**: ✓ both (+0.005 ViT, +0.015 ResNet).
- **raw_union → oracle**: 95.5% (ViT), 80.8% (ResNet) at α=0.05 alone. α=1.0 cell will run in the headline grid.
- **M4 > 0 at low α**: ✓ ViT m4=**0.828**, ResNet m4=0.532 — strong on both.

### Participation-incentive picture (M4 is the headline)

- ViT m4_ood **0.828**: federation gives every client 82.8% acc on classes they hold ZERO local samples of. The teacher trained on 1-2 classes cannot classify any of the other 98; the aggregate inherits broad knowledge. ~∞-fold lift on OOD vs local teacher.
- Aggregate beats mean_teacher 4–5× on overall acc.
- m3_gap = −0.13 (ViT) is the same in-distribution-slice math artifact — at α=0.05 each client's data is 1–2 classes where its specialised teacher peaks. The M4 story measures the cross-class gain explicitly.

### Comparison vs the resnet18/CIFAR-10 cell (issues 010 + 011)

| Cell | acc | θ₀ | oracle | acc / oracle | m4_ood |
|---|---:|---:|---:|---:|---:|
| **ViT/CIFAR-100 (012)** | **0.830** | 0.825 | 0.869 | **95.5%** | **0.828** |
| ResNet/CIFAR-100 (012) | 0.538 | 0.524 | 0.666 | 80.8% | 0.532 |
| ResNet/CIFAR-10 (010 best) | 0.762 | 0.740 | 0.870 | 87.6% | 0.750 |

**ViT/CIFAR-100 is the new pretrained-vision headline.** ResNet/CIFAR-10 retained as a comparable point; ViT/CIFAR-10 dropped from headline due to 0.97 saturation. ResNet/CIFAR-100 adds breadth.

## Sweep configuration

- Backbones: `vit_b32_cifar100`, `resnet18_cifar100` (Tiny-ImageNet gated by `HEIFD_012_INCLUDE_TINY=1`)
- N=16, α=0.05, methods {no_phase0, raw_union_K20}, seed 42, K=100, τ=1, lr=0.001, scope head_only.
- Job 1115633, 4m15s wall-clock (the second cell per backbone reuses the first's teacher + feature caches).
- Labelled probe: 300 (CIFAR-100), 600 (Tiny-ImageNet).

## Next — full grid

`jobs/heifd_012_harder_vision_headline.sh` (already in repo) runs the full N+α grid on ViT-B/32/CIFAR-100 + ResNet-18/CIFAR-100. The orchestrator submits this once the verify is acknowledged at the HITL touchpoint.
