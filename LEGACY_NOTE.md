# Legacy artefacts pointer

The previous repository, including all `.pt` checkpoints, ablation outputs, and
result `.out` files for the **deprecated block-wise HE-IFD protocol**, has
been renamed in place to:

```
/scratch/hkanpak21/HE_Distillation_legacy_2026-05-05/
```

It is preserved (not deleted) so that, if HE-IFD-v1 numbers need to be
reproduced for a rebuttal or follow-up, the original training artefacts are
still on disk.

## What is in there
- `results/` — full ablation `.pt` weights and `.out` logs from the v1 protocol
  (block-wise intermediate-feature distillation). Roughly 113 GB of trained
  students/teachers across $N \in \{4,16,32\}$, $\alpha \in \{0.05, 0.1, 1.0\}$.
- `checkpoints/` — `teacher_resnet18_cifar10.pt` and `teacher_logits_cifar10.pt`,
  the ImageNet-domain reference ResNet-18 from the v1 experiments.
- `data/`, `data_mnist/`, `data_co/`, `MNIST/` — local copies of the standard
  CIFAR-10/MNIST/Fashion-MNIST datasets used by the v1 jobs. Re-downloadable
  from `torchvision`; they live there only as a cache.
- `src/`, `demos/`, `experiments/`, `prototypes/` — v1 protocol code. Treat
  as reference only; the new CFD protocol re-implements the relevant pieces
  cleanly under this tree's `prototypes/`.

## What you should NOT do with it
- Do not import code from there into the new tree. The v1 abstractions
  (block-wise features, magnitude regularisation, bridge construction) do
  not apply to the new encrypted CFD protocol.
- Do not cite v1 numbers as "current results" anywhere — those numbers are
  for the deprecated protocol described in
  `reports/2026-05-05_methodology_pivot.md` §1 (Why the pivot).

## What you SHOULD do with it
- If you need v1 results for a rebuttal: re-run the relevant `jobs/` files
  in the legacy tree directly. They are self-contained and use absolute paths
  inside the legacy tree.
- If you need the v1 paper snapshot for diff: it is also captured in
  `/scratch/hkanpak21/archive/HE_IFD_paper_subset_2026-05-05.tar.zst`.

## A slim tarball of the paper subset (no `results/`, no datasets) lives at
```
/scratch/hkanpak21/archive/HE_IFD_paper_subset_2026-05-05.tar.zst
```
which is the canonical "this is what the project looked like at the moment
of the pivot" snapshot, suitable for sharing without the 113 GB result tree.
