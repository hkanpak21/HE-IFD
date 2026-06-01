# Checkpoint — 2026-06-01 — state saved before the federated-fine-tuning pivot

This marks the repository state immediately **before** the paper is refactored from
"one-shot federated distillation (from-scratch + pretrained)" toward
**federated fine-tuning of pretrained models under HE**, a direction decided with the PIs.

## What this checkpoint captures (the pre-pivot state)

- **Paper** (`docs/paper/`): one-shot federated distillation framing; experiments with
  from-scratch (MNIST/FMNIST) + pretrained (ViT-B/32 CIFAR-100, RoBERTa/MPNet AG-News);
  λ scaling-coefficient (drift-regularizer) subsection; MIA section reframed as
  attack-surface + leak-minimization; basin-choice incl. the DP-MERF negative.
- **Results**: headline grids (3 seeds 42/43/44); FHE PoC (Lattigo, depth-1, validated +
  cost sweep just landed); MIA (021/028); λ (026); DP-MERF DP-soundness fix (027).
- **Tracker**: `docs/prd/he-ifd-tnse-resubmission.md` (Phases I–III) + `docs/issues/` 001–028.

## Why we are pivoting (decided 2026-06-01)

- Reframe to **federated fine-tuning for pretrained models** → extend to more pretrained
  backbones + harder/more datasets.
- **ViT/CIFAR is too easy** → the pretrained model saturates, hiding the method's contribution.
- **Figure 4 (distillation lift vs basin)** currently shows distillation adds ~nothing on top
  of the basin — must be fixed (harder tasks), reframed, or cut.
- Add a **comprehensive CKKS communication/computation section** + prior-work comparison.
- Add a **"why fine-tuning, not from-scratch" section**: the necessity of a shared loss basin,
  and the lack of programmability in HE (computation on obfuscated ciphertexts → fixed
  low-depth circuit only).

The previous PRD/issues will be archived and a new PRD + issue set cut for the fine-tuning paper.
