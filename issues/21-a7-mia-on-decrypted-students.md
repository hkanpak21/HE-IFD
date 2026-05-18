# 21. A7 post-release MIA against the decrypted student

Status: ready-for-agent
Label: AFK
Priority: P4 (security check; downstream of grid)
Action-plan: A7
PRD-section: §2.4 (SQ-floor on released student)

## Parent

Action plan A7 (lines 376–390) — locked 2026-05-10.

## What to build

Per cell of issue 18's headline grid (360+ cells) + the 48-cell N-ablation, run two membership inference attacks on the decrypted student and report AUC:

- **LiRA** (Carlini et al. 2022, `carlini2022membership`) — the field-standard individual-record attack.
- **Loss-threshold** (Yeom et al. 2018, `yeom2018privacy`) — the simplest baseline.

This pair was canonical in the rejected paper's training-time MIA; applying it post-decryption keeps the methodology internally consistent.

**Population MIA** (Ye et al., arXiv:2111.09679) as a single-cell ablation on CIFAR-10 α=0.1 N=10. Add to `references.bib` if not present.

**Output:**
- `jobs/mia_lira.sh`, `jobs/mia_loss_threshold.sh` sbatch wrappers.
- `results/mia/<dataset>_<variant>_<alpha>_<seed>_lira.json` and `_lossthr.json` per cell.
- Consolidated `results/A7_mia_auc_table.csv` and `.tex`.
- New §V subsection in `experiments.tex` reporting AUC.

**Compute** per action plan A7 line 387: ≈ 1 day on top of A4.

## Acceptance criteria

- [ ] LiRA + loss-threshold AUC measured per cell of issue 18's scope.
- [ ] Population MIA single-cell ablation on CIFAR-10 α=0.1 N=10.
- [ ] `references.bib` has all three MIA references.
- [ ] §V MIA subsection added to `experiments.tex`.
- [ ] `FL_TDSC/CHANGES.md` logged.
- [ ] No login-node execution.

## Blocked by

- Issue 18 (need decrypted students from grid cells).

## References

- Action plan A7 (lines 376–390).
- PRD §2.4 (SQ-floor framing, lines 53–63).
- Bibkeys: `carlini2022membership`, `yeom2018privacy`.

## Comments

### 2026-05-18 (wave-7 agent) -- scaffold landed

Owned files now exist (syntax-clean, `bash -n` clean):

- `prototypes/mia_lib/__init__.py` -- defines `MIAResult` dataclass.
- `prototypes/mia_lib/shadow_models.py` -- shadow training + cache (LeNet-5 for
  MNIST/FashionMNIST, ResNet-8 (3 BasicBlocks) for CIFAR-10).
- `prototypes/mia_lib/lira.py` -- offline LiRA scoring + numpy-only ROC AUC.
- `prototypes/mia_lib/loss_threshold.py` -- Yeom et al. 2018 cross-entropy baseline.
- `prototypes/mia_lira.py` -- end-to-end driver.
- `jobs/mia_lira.sh` -- sbatch wrapper, partition=t4_ai, 4 h cap.

Per the wave-7 brief I did NOT create `jobs/mia_loss_threshold.sh`, the
aggregated CSV/TeX, the `experiments.tex` subsection, or the bib edits --
those are out of scope for this scaffold pass; the issue's full acceptance
criteria above remain open for follow-up waves.

#### Invocation pattern

One sbatch per (student_ckpt, dataset, alpha, seed, variant):

```
sbatch jobs/mia_lira.sh <student_ckpt_path> MNIST 0.3 42 warmstart
```

The driver runs *both* attacks (LiRA + loss-threshold) in a single
invocation and writes one `MIAResult` JSON per cell to
`results/mia/lira_<dataset>_a<alpha>_s<seed>_<variant>_<job_id>.json`.
Failures of one MIA job do not affect others; the aggregator picks up
whatever lands and the `status` field disambiguates ok vs error.

For live runs the driver also accepts `--cell-result <CellResult.json>`,
which is how it learns the (members, non-members) partition of the
shadow training pool. Without it the driver falls back to a sentinel
first-half/second-half split (only useful for dry-run / smoke testing).

#### Shadow-cache contract

- Cache root: `results/shadows/<dataset>_<seed>/`.
- Keyed only on (dataset, seed) -- *not* on the student. The shadow
  population is student-independent (LiRA threat model: adversary knows
  the data distribution, not the membership mask).
- Contents per cache dir:
  - `manifest.json` -- {dataset, seed, n_shadows, victim_size,
    n_train_pool, epochs, batch_size, lr, arch}.
  - `masks.npy` -- `(n_shadows, n_train_pool)` bool in/out matrix.
  - `shadow_000.pt` ... `shadow_063.pt` -- per-shadow state_dicts.
- Cache-hit rule: bundle is reused iff manifest exists, masks file
  exists, and `n_shadows` cached is >= requested. Implication: bumping
  `--n-shadows` invalidates the cache.

#### Wall-clock budget (estimates pending live calibration)

- 64 shadow models per (dataset, seed). Per-shadow cost on a single T4
  (16 GB):
  - LeNet-5 on MNIST/FMNIST (60k train, 20 epochs, batch 128): ~2-3 min
    per shadow => ~2-3 h total.
  - ResNet-8 on CIFAR-10 (50k train, 20 epochs, batch 128): ~3-4 min per
    shadow => ~3-4 h total -- this is the tight constraint that drives
    the sbatch `--time=04:00:00`.
- Scoring (LiRA + loss-threshold) on `--n-candidates 4000`: <5 min
  (forward passes only).
- **First MIA job per (dataset, seed) pays the full shadow-training
  cost; every subsequent job for the same (dataset, seed) is scoring-
  only (~5 min wall-clock) thanks to the cache.**
- LiRA shadow training therefore dominates the total A7 budget; the
  per-cell marginal cost amortises to near zero once the shadow
  population is in place for each (dataset, seed) used by issue 18's
  grid.

#### Design decisions

- **Offline LiRA** (not online) per Carlini et al. 2022: half the
  shadow-evaluation cost, comparable AUC at n_shadows=64. The fixed-
  variance trick is enabled by default for stability at the chosen
  shadow count.
- **AUC computation in numpy** (rank-based Mann-Whitney U) to avoid a
  hard sklearn dep at scoring time.
- **CellResult coupling is loose** -- import is lazy and the schema is
  documented above (`member_indices`, `nonmember_indices`); issue 14
  owns the canonical definition.
