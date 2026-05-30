#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --qos=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --job-name=heifd_027_merf_verify
#SBATCH --output=/scratch/hkanpak21/HE_IFD/results/heifd_027_merf_verify/runs/merf_verify_%j.out
#SBATCH --error=/scratch/hkanpak21/HE_IFD/results/heifd_027_merf_verify/runs/merf_verify_%j.err
#
# Issue 027 — re-verify the DP-MERF generator after making it DP-SOUND.
#
# THE BUG (issue 027). The old _merf_generate_class privatized the φ-space mean
# embedding but then RELEASED RAW RECORDS (base = X_c[pick]) + cosmetic jitter,
# so the "synthetic" set literally contained real data → NO sample-level DP.
# Mode A (dp_synth_all) therefore reached an implausible 0.97 @ ε=2 on MNIST
# because the DP never bit — the 022 verify's inverted contrast (Mode A > Mode B)
# was an ARTIFACT, not a finding.
#
# THE FIX. _merf_generate_class now (a) privatizes the per-class RFF mean
# embedding μ̂^priv via the repo's averaging-variant dp_sigma(clip=1, m, eps), then
# (b) TRAINS a small neural generator G (2-layer MLP, latent=16) to match μ̂^priv
# under the random-feature MMD, and (c) SAMPLES n_gen FRESH points from G. The
# released set is draws from G — never X_c. A runtime guard + tests/test_merf_
# dpsound.py assert no released sample equals a raw record. ε=∞ ⇒ σ=0 (raw-MERF
# ceiling) is preserved. Both builders (Mode A build_dp_synth_all, Mode B
# build_probe_merf) call the SAME fixed function.
#
# EXPECTED TELL (what "fixed" looks like).
#   * Mode A (dp_synth_all_eps2): accuracy must now DROP at ε=2 — the 0.97 MNIST
#     artifact is GONE, because the DP finally bites (the student trains one-shot
#     on genuinely private synthetic data, not raw records). dp_synth_all_eps8
#     should sit ABOVE eps2 (looser ε ⇒ less noise) but still well below the old
#     bogus 0.97.
#   * Mode B (merf_basin_eps{2,8}_K20): the DP-MERF basin θ₀ need only ALIGN
#     clients, so the student stays competitive (≈ raw_union_K20 ceiling) because
#     the bulk flows through the HE-protected bounded distillation. So the
#     corrected contrast is  merf_basin ≈ raw_union  >>  dp_synth_all  at ε=2.
#   * raw_union_K20 is the no-DP alignment ceiling reference row.
#
# Grid: backbones{mlp_mnist, vit_b32_cifar100}                                   (2)
#       × methods{dp_synth_all_eps2, dp_synth_all_eps8,                          (Mode A)
#                 merf_basin_eps2_K20, merf_basin_eps8_K20,                      (Mode B)
#                 raw_union_K20}                                                 (ref)  (5)
#       × α{0.05}                                                                (1)
#       × N{10}                                                                  (1)
#       × seeds{42}                                                              (1)
#       = 2 × 5 × 1 × 1 × 1 = 10 cells (small — no job array needed).
#
# NOTE backbone key: the registered BackboneSpec key is "mlp_mnist" (see
# src/protocol.py BACKBONES). The vit_b32_cifar100 Mode-A cell (DP-MERF over ALL
# local data, 100 classes, now with per-class generator training) is the heaviest
# but still well inside the 3h VALAR cap at this 10-cell scale. Resumable:
# re-submitting skips any cell whose JSON already records status=success.
#
# PREFETCH (login node, internet — compute nodes are offline):
#   python jobs/prefetch_login.py --include-cifar100
# puts ViT-B/32 weights + CIFAR-100 in the HF/torch cache (reuse the issue-012
# caches if already populated). MNIST is pre-cached under data/ (download=False).
#
# Run this AFTER the soundness test passes on VALAR:
#   pytest tests/test_merf_dpsound.py -q
# Only after this verify shows the DP biting does 022's full grid get re-run.

set -euo pipefail
REPO=/scratch/hkanpak21/HE_IFD
CASE=heifd_027_merf_verify
mkdir -p "${REPO}/results/${CASE}/runs"
source /opt/ohpc/pub/compiler/conda3/latest/etc/profile.d/conda.sh
conda activate he_ofl
export HF_HUB_OFFLINE=1           # ViT-B/32 weights + CIFAR-100 pre-fetched on the login node
cd "${REPO}"
echo "[027 merf_verify] job ${SLURM_JOB_ID:-?} on $(hostname)"

exec srun python -u -m src.sweep \
    --backbones mlp_mnist,vit_b32_cifar100 \
    --Ns 10 \
    --alphas 0.05 \
    --methods dp_synth_all_eps2,dp_synth_all_eps8,merf_basin_eps2_K20,merf_basin_eps8_K20,raw_union_K20 \
    --seeds 42 \
    --K "${HEIFD_K:-300}" \
    --case "${CASE}" \
    --results-root "${REPO}/results" \
    --data-root "${REPO}/data" \
    --cache-root "${REPO}/cache"
