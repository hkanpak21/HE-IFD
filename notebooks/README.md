# Colab notebooks — run issues 026 / 027 / 028 without VALAR

These reproduce the three verify jobs on a Google Colab GPU instead of the VALAR
queue. Each is **self-contained**: it clones this (public) repo, installs deps,
pre-downloads the datasets (the repo loaders use `download=False` for VALAR's
offline compute nodes — Colab has internet, so the notebooks download first),
then runs the **same `python -m …` entrypoints** as the sbatch wrappers.

**Requirements:** set the runtime to **GPU** (T4 is fine). No GitHub token needed
(public repo). No TenSEAL needed for these three.

### Running from VS Code (Colab remote kernel)
These are tuned for driving a **Colab GPU runtime from VS Code**:
- Open the `.ipynb` in VS Code and select the **Colab runtime** as the kernel.
- Code executes on the Colab VM; files live under `/content/HE-IFD`. View and
  download results from the **VS Code remote Explorer** (right-click ▸ Download) —
  the notebooks don't rely on the `files.download` browser widget.
- `drive.mount` (optional persistence cell) uses the **auth-code paste flow** in
  this frontend.
- `!`, `%cd`, `%pip` magics work (the kernel is IPython on the Colab VM).

| Notebook | Mirrors | What it runs | ~time on a T4 |
|---|---|---|---|
| [`colab_026_lambda_verify.ipynb`](colab_026_lambda_verify.ipynb) | `jobs/heifd_026_lambda_verify.sh` | λ-scaling eval-only verify, 4 cells, λ∈{0…2} | ~5–15 min |
| [`colab_027_merf_verify.ipynb`](colab_027_merf_verify.ipynb) | `jobs/heifd_027_merf_verify.sh` | DP-MERF soundness `pytest` **then** 2-cell re-verify (5 methods) | ~20–60 min |
| [`colab_028_mia.ipynb`](colab_028_mia.ipynb) | `jobs/heifd_021_mia_vit_cifar100.sh` + `jobs/heifd_028_mia_roberta_agnews.sh` | MIA on ViT/CIFAR-100 **and** RoBERTa/AG-News, ~64 shadows each | ~1–2 h |

### Open in Colab (one click)
- 026 — https://colab.research.google.com/github/hkanpak21/HE-IFD/blob/master/notebooks/colab_026_lambda_verify.ipynb
- 027 — https://colab.research.google.com/github/hkanpak21/HE-IFD/blob/master/notebooks/colab_027_merf_verify.ipynb
- 028 — https://colab.research.google.com/github/hkanpak21/HE-IFD/blob/master/notebooks/colab_028_mia.ipynb

### Notes
- **Gates are preserved** (the notebooks run only the verify cells, the same as the
  VALAR chain): 026 reports the acc-vs-λ curve + λ⋆ + lift (no λ grid); 027 reports
  the Mode-A-before/after at ε=2 (no full-022 rerun); 028 reports released-model AUC
  + prototype DP-collapse on both backbones.
- **027 runs the soundness `pytest` first** — the re-verify only matters if the
  DP-soundness invariant (no released sample equals a raw record) holds.
- **028 is heavy and Colab sessions disconnect.** Uncomment the **Drive persistence**
  cell to point `cache/` + `results/` at Google Drive — the MIA suite resumes from
  `shadows/<cell>/` checkpoints, so a dropped session continues instead of
  restarting. Set `N_SHADOWS = 8` for a quick smoke run before the full 64.
- Each notebook ends by zipping `results/<case>/` for download (or copy it out of
  Drive) so the numbers can come back into the repo / paper.
- These do **not** replace the queued VALAR chain — they're a faster path while the
  `t4_ai` queue is backed up. Run whichever is convenient; results are identical
  (GPU type doesn't affect correctness).
