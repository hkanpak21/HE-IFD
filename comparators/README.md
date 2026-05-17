# Vendored comparator clones

This directory holds vendored clones of comparator methods used by the A4.1 headline grid (and adjacent ablations). The clones themselves are **not** committed — `.gitignore` ignores `comparators/*/*` except for each `COMMIT.txt` audit file, an optional `PATCH-NOTES.md` per vendor, and this README. The full trees can run to 100+ MB per clone (datasets, model checkpoints, upstream `.git` history), so committing them would balloon the repo for no reproducibility benefit a pinned SHA could not give.

## Audit trail

Each `comparators/<vendor>/COMMIT.txt` pins:

- The upstream URL.
- The clone date.
- The HEAD SHA at clone time.

To rehydrate a vendor:

```sh
cd comparators
URL=$(grep -oE 'https://[^ ]+' <vendor>/COMMIT.txt | head -1)
SHA=$(grep -oE '[a-f0-9]{40}' <vendor>/COMMIT.txt | head -1)
git clone "$URL" <vendor>-fresh
( cd <vendor>-fresh && git checkout "$SHA" )
# preserve COMMIT.txt / PATCH-NOTES.md and overlay the upstream tree
mv <vendor>/COMMIT.txt <vendor>-fresh/
[ -f <vendor>/PATCH-NOTES.md ] && mv <vendor>/PATCH-NOTES.md <vendor>-fresh/
rm -rf <vendor> && mv <vendor>-fresh <vendor>
```

If the vendor has a `PATCH-NOTES.md`, apply the documented patches by hand after rehydration. We avoid carrying patches as `.patch` files because the diffs against upstream are typically small and the `PATCH-NOTES.md` rationale is what matters for reproducibility.

## Current comparators

| Vendor | Upstream | Privacy | Tier | sbatch wrapper |
|---|---|---|---|---|
| `coboosting/` | `github.com/rong-dai/Co-Boosting` (Dai et al. ICLR 2024, `dai2024coboosting`) — note: the issue spec's `yuanyuanyuan/Co-Boosting` was a 404; corrected during issue 06. | no-DP, plaintext | tier-1 | `jobs/cfd_v2_comp_coboost.sh` |
| `fedmd/` | `github.com/diogenes0319/FedMD_clean` (Li & Wang 2019, `li2019fedmd`) | no-DP, plaintext | tier-1 | `jobs/cfd_v2_comp_fedmd.sh` |
| `feddiff/` | `github.com/mmendiet/FedDiff` (Mendieta–Sun–Chen WACV 2025, `feddiff2024`) — note: the issue spec's `mendieta/FedDiff` was a 404; corrected during issue 08. **Upstream is currently a placeholder (LICENSE + 1-line README); wrapper hard-fails with a clear `upstream_not_populated` status until the authors release code.** | DP via Opacus, ε ∈ {1, 10} | tier-1, primary γ-variant comparator | `jobs/cfd_v2_comp_feddiff.sh` |
| `fedkt/` | `github.com/QinbinLi/FedKT` (Li et al. 2021, `li2021fedkt`) | PATE-style DP, ε ∈ {1, 10} via upstream's moments accountant (not Opacus) | tier-1 | `jobs/cfd_v2_comp_fedkt.sh` |
| `dpdm_upstream/` | `github.com/nv-tlabs/DPDM` (Dockhorn et al. TMLR 2022, `dockhorn2022dpdm`) | DP-SGD generator, ε = 10 headline | scaffolded for γ-variant generator (issue 22 profile + issue 23 per-client trainers) | `jobs/dpdm_profile.sh` |

Tier-2 comparators (FedDF, DENSE, FuseFL, FedMD-NFDP, FedDM) per issue 10 will land in the same convention.

## Running a smoke

All wrappers expect conda env `he_ifd_comparators` to exist. Construction recipe is per-vendor — typically `conda create -n he_ifd_comparators python=3.10` plus the upstream's `requirements.txt`. Wrappers run on `t4_ai` (account `comx29`); QoS for longer runs is gated on the resolution of issue 03 (HITL admin ticket).
