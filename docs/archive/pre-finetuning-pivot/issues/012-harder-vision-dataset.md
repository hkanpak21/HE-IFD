# 012 — Harder vision dataset (CIFAR-100 / Tiny-ImageNet) for ViT  [AFK]

> **STATUS: ✅ DONE** (2026-05-29) — **client-benefit win**. ViT-B/32 / CIFAR-100 (full 450-cell grid): α=0.05 acc 0.81, θ₀ 0.81, **m4_ood 0.81**, oracle 0.87, global model **3.6× mean_teacher**; → oracle at IID. Confirms the 008 ViT/CIFAR-10 saturation hypothesis (CIFAR-10 had no headroom; CIFAR-100 unlocks the protocol). ResNet-18/CIFAR-100 also passes (m4 0.53). CIFAR-100 prefetched; Tiny-ImageNet plumbed but not run. Verdict: `results/heifd_012_harder_vision_headline/README.md` (+ `_verify`).

**Phase:** M1.5 / α (address ViT saturation on CIFAR-10) · **Blocked by:** none · **Blocks:** nothing critical

**Required reading:**
1. `docs/prd/he-ifd-tnse-resubmission.md` (Phase II section).
2. `CLAUDE.md` — especially the login-node prefetch rule.
3. `docs/issues/008-pretrained-headline-sweep.md` STATUS — ViT/CIFAR-10 saturation.
4. `src/backbones.py` (`extract_cifar10_features`, `build_vit_extractor`).
5. `src/data.py`. `jobs/prefetch_login.py`.

## Why

ViT-B/32 on CIFAR-10 IID = 0.97 — saturated. There's no headroom to show distillation adds value. CIFAR-100 (ViT-B/32 linear-probe ceiling ~0.75–0.80) and Tiny-ImageNet (ceiling ~0.60–0.65) give the protocol real room.

## What to build

1. Add data loaders to `src/data.py`:
   - `load_cifar100_tensors` (torchvision, `download=False`, cache `cache/features/cifar100.pt`).
   - `load_tiny_imagenet_tensors` (Stanford CS231n source; **login-node prefetch only** — the script downloads + extracts).
2. Add feature extractors to `src/backbones.py`:
   - `extract_cifar100_features(name, ...)` and `extract_tiny_imagenet_features(name, ...)` mirroring `extract_cifar10_features`, supporting `resnet18` and `vit_b32`.
3. New `BACKBONES` entries in `src/protocol.py`:
   - `vit_b32_cifar100`, `vit_b32_tiny_imagenet`, `resnet18_cifar100`, `resnet18_tiny_imagenet`. Pretrained head; `kind="head"`.
4. Extend `jobs/prefetch_login.py` to include CIFAR-100 + Tiny-ImageNet download triggers.
5. New verify wrapper `jobs/heifd_012_harder_vision_verify.sh` (4 cells: ViT+ResNet × {no_phase0, raw_union_K20} × α=0.05, N=16, seed 42, case `heifd_012_harder_vision_verify`).
6. After verify passes: a full-grid wrapper `jobs/heifd_012_harder_vision_headline.sh` mirroring `heifd_headline_pretrained.sh` for at least ViT on CIFAR-100 (the highest-value cell).

## Acceptance

- [ ] CIFAR-100 + Tiny-ImageNet data cached on VALAR via the login-node prefetch.
- [ ] Verify cells produce sensible numbers: ViT IID on CIFAR-100 ≥ 0.60, on Tiny-ImageNet ≥ 0.40.
- [ ] **Key check:** distillation adds value over θ₀ on the harder dataset at α=0.05 (raw_union > θ₀ — if yes, ViT saturation explained CIFAR-10's lack of headroom).
- [ ] Full grid runnable for at least ViT on CIFAR-100.

## Hard boundaries

- Touch `src/backbones.py`, `src/data.py`, `src/protocol.py`, `jobs/prefetch_login.py`, new wrappers.
- **Permitted login-node `ssh`** ONLY to run the extended prefetch (documented sanctioned exception per CLAUDE.md).
- No `git push`/`git commit`/`sbatch` from your worktree. ast.parse only.

## Report

1. Datasets prefetched (sizes).
2. Verify-cell results table.
3. Whether distillation adds value on the harder dataset(s).
4. Full-grid status (queued / running / pending orchestrator).
5. Files touched.
