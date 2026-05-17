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
