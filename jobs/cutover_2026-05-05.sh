#!/bin/bash
#SBATCH --job-name=he_ifd_cutover
#SBATCH --partition=t4_ai
#SBATCH --qos=comx29
#SBATCH --account=comx29
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=/scratch/hkanpak21/cutover_%j.out
#SBATCH --error=/scratch/hkanpak21/cutover_%j.err

set -euo pipefail

OLD=/scratch/hkanpak21/HE_Distillation
LEGACY=/scratch/hkanpak21/HE_Distillation_legacy_2026-05-05
NEW=/scratch/hkanpak21/HE_IFD
ARCH=/scratch/hkanpak21/archive
TARBALL=$ARCH/HE_IFD_paper_subset_2026-05-05.tar.zst

echo "=== node: $(hostname) ==="
echo "=== start: $(date -Is) ==="
echo "OLD=$OLD"
echo "NEW=$NEW"
echo "ARCH=$ARCH"

# 0. sanity checks
if [[ ! -d "$OLD" ]]; then echo "ERROR: $OLD missing"; exit 1; fi
if [[ -d "$LEGACY" ]]; then echo "ERROR: $LEGACY already exists"; exit 1; fi
if [[ -d "$NEW" ]]; then echo "ERROR: $NEW already exists"; exit 1; fi

mkdir -p "$ARCH"

# 1. slim paper-subset tarball (no results, no datasets, no large zips)
#    paths inside the tarball are relative to /scratch/hkanpak21 so they unpack cleanly.
echo "=== step 1: slim tarball ==="
cd /scratch/hkanpak21
tar --use-compress-program=zstd \
    --exclude='HE_Distillation/results' \
    --exclude='HE_Distillation/data' \
    --exclude='HE_Distillation/data_co' \
    --exclude='HE_Distillation/data_mnist' \
    --exclude='HE_Distillation/MNIST' \
    --exclude='HE_Distillation/output' \
    --exclude='HE_Distillation/repo_full_archive_*.zip' \
    --exclude='HE_Distillation/FL_TDSC.zip' \
    --exclude='HE_Distillation/FL_TDSC_snapshot_*.zip' \
    --exclude='HE_Distillation/__pycache__' \
    --exclude='HE_Distillation/*/__pycache__' \
    --exclude='HE_Distillation/*/*/__pycache__' \
    -cf "$TARBALL" HE_Distillation
echo "tarball: $(ls -lh $TARBALL | awk '{print $5}') at $TARBALL"

# 2. spin up new clean tree
echo "=== step 2: create $NEW ==="
mkdir -p "$NEW"/{FL_TDSC,reports,prototypes,jobs,results}

# 3. carry over paper text verbatim (no pruning at carry-over time)
echo "=== step 3: copy FL_TDSC verbatim ==="
cp -a "$OLD"/FL_TDSC/. "$NEW"/FL_TDSC/

# 4. carry over the design PRD + may-5 results report
echo "=== step 4: copy reports ==="
cp -a "$OLD"/reports/. "$NEW"/reports/

# 5. write the LEGACY note in the new tree
cat > "$NEW"/LEGACY_NOTE.md <<'EOF'
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
EOF
echo "wrote $NEW/LEGACY_NOTE.md"

# 6. symlink legacy from inside new tree for convenience
ln -s "$LEGACY" "$NEW"/legacy

# 7. starter README in new tree
cat > "$NEW"/README.md <<'EOF'
# HE-IFD (encrypted CFD pivot, 2026-05-05)

Working tree for the HE-IFD paper after the methodology pivot of 2026-05-05.

## Authoritative design
`reports/2026-05-05_methodology_pivot.md` is the **PRD**. It supersedes
`FL_TDSC/methodology.tex` where they conflict (the .tex still contains
deprecated block-wise content at carry-over time; replacement is logged
in `FL_TDSC/CHANGES.md`).

## Layout
- `FL_TDSC/` — paper text (carried over verbatim from v1 at the cutover;
  rewrite happens in-place, logged to `FL_TDSC/CHANGES.md` for Overleaf
  replay).
- `reports/` — design docs. `2026-05-05_methodology_pivot.md` is the PRD;
  `2026-05-05_one_shot_cfd_central_vs_client_update.md` is the underlying
  results report for the May-5 grilling session.
- `prototypes/` — TenSEAL prototype (parametric on student architecture).
- `jobs/` — sbatch templates.
- `results/` — empty at carry-over; new experiments fill it.
- `legacy/` — symlink to the renamed v1 tree (see `LEGACY_NOTE.md`).

## Hardware policy
Never run anything on the login node. Always `sbatch` onto `t4_ai` per
the existing `jobs/` template. Account `comx29`, partition `t4_ai`, GPU
`tesla_t4` when needed.

## Conda env
The v1 environment `he_ofl` at `/home/hkanpak21/.conda/envs/he_ofl/bin/python`
remains usable. A v2-specific env is not needed unless DPDM training pulls
in new deps.
EOF
echo "wrote $NEW/README.md"

# 8. RENAME the old tree so it's clearly deprecated
echo "=== step 8: rename $OLD -> $LEGACY ==="
mv "$OLD" "$LEGACY"

# 9. final summary
echo "=== done: $(date -Is) ==="
echo
echo "tarball:  $TARBALL"
ls -lh "$TARBALL"
echo
echo "legacy:   $LEGACY"
echo "new:      $NEW"
ls -la "$NEW"
echo
echo "FL_TDSC inventory in new tree:"
ls "$NEW"/FL_TDSC/
echo
echo "reports inventory in new tree:"
ls "$NEW"/reports/
