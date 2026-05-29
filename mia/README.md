# `mia/` — Membership-inference suite (issue 021)

A self-contained suite that measures the **residual leakage** of the HE-IFD
protocol's *released* artefacts. The protocol protects client contributions
cryptographically, but after threshold decryption every party holds the global
model θ⋆ in the clear, and the Phase-0 prototypes travel over the P2P channel
before encryption. §VI of the paper (`docs/paper/sections/mia.tex`) must
*measure* what those released objects leak. This suite produces that measurement
— TPR@0.1%FPR + ROC/AUC — for three attacks across three adversary surfaces.

It **reuses `src/`** to build every target and shadow model. The protocol is not
reimplemented: `mia.target` composes `src.teacher`, `src.phase0`, `src.distill`,
`src.aggregate` in the exact order `src.protocol.run_cell` does, on resampled
data splits. (See "src/ reuse" below for the one read-only hook.)

## The three attacks (`mia/attacks.py`)

| attack | citation | what it does |
|---|---|---|
| **threshold** | Yeom et al. 2018, *Privacy Risk in Machine Learning* (`yeom2018privacy`) | The interpretable floor. Membership score = −loss of the target on the example (members are trained-on ⇒ lower loss). No shadow models. |
| **LiRA** | Carlini et al. 2022, *Membership Inference Attacks From First Principles* (`carlini2022membership`) | Likelihood-ratio shadow-model attack. Per example, fit Gaussians to the LiRA logit-scaled confidences φ = log(p/(1−p)) of the shadow models that did vs did not train on it, and score by the IN/OUT likelihood ratio. Algorithm ported from the TensorFlow-Privacy reference `research/mi_lira_2021` (`score.py`/`plot.py`), including its pooled-variance (`fix_variance=True`) stabilisation and the offline fallback when no IN-shadows exist for an example. |
| **GLiRA** | Galichin et al. 2025, *GLiRA: Black-Box Membership Inference Attack via Knowledge Distillation* (`galichin2025glira`) | Distillation-guided **black-box** LiRA — the natural fit for the external adversary on θ⋆. Identical likelihood-ratio test, but every φ is computed on a *surrogate* knowledge-distilled from the model's **query outputs** (never its weights). Implemented from the paper (no public repo found). |

All three reduce a model to one real-valued membership score per attack example;
`mia/metrics.py` turns (scores, labels) into ROC arrays, AUC, and TPR at fixed
FPR (default targets 0.1%, 1%, 10% — **0.1% is the headline**).

## The three adversary surfaces (`mia/surfaces.py`, scored in `mia/run.py`)

| surface | observes | attacks run | reading |
|---|---|---|---|
| **external** | black-box query access to θ⋆ | threshold, LiRA, **GLiRA** | LiRA here reads θ⋆'s own confidences (an upper reading of the released-model leakage); GLiRA is the query-only fit; threshold is the Yeom floor. |
| **fellow** | θ⋆ + the participant's own labelled data + the shared Phase-0 prototypes | threshold, LiRA (class-conditionally calibrated) | A participant has a stronger prior than the external adversary. Modelled concretely by subtracting a per-class OUT-population φ baseline (the prior a participant can reconstruct from public task knowledge) before the LiRA test. Reported separately so the fellow's advantage is visible; expect ≥ external. |
| **prototype** | the Phase-0 per-class prototype release itself, at **raw** and **ε∈{2,8}** | distance-to-nearest-prototype | Membership inference directly on the released summaries. An averaged-in example sits closer to its class prototype. AUC/TPR should be large at raw release and **collapse toward chance as ε tightens** — the empirical validation of the paper's averaging-variant DP accounting (`docs/paper/sections/method.tex` §Security Analysis). |

## Cells

Per issue 021: `mnist_mlp` and `vit_b32_cifar100`, **N=10**, **α∈{0.05, 1.0}**,
**~64 shadow models** per target. The attacked Phase-0 method defaults to
`raw_union_K20` (the headline protocol configuration); override with
`--methods`. The prototype surface additionally sweeps ε∈{∞(raw),8,2} internally.

## Metrics & outputs

Written to `results/heifd_021_mia/` (the repo's `results/<case>/` convention):

- `cell_<backbone>_N<n>_a<α>_<method>_s<seed>.json` — per-cell results: every
  surface × attack with `auc`, `tpr_at_fpr_0.001` / `_0.01` / `_0.1`, member
  counts, and the **full ROC arrays** (`roc_fpr`/`roc_tpr`) so §VI's log-log ROC
  figure is drawn straight from the JSON.
- `summary.json` — the same numbers flattened to records the paper table reads.
- `README.md` — auto-populated headline table (TPR@FPR + AUC per row).
- `shadows/<cell>/model_XXXX.npz` — per-model attack vectors (resume support;
  gitignored, regenerable from seed).
- `runs/` — Slurm stdout/stderr.

## src/ reuse and the read-only hook

`mia.target.load_features` calls `src.protocol._load_features` (an existing
module-level function) + the `src.protocol.BACKBONES` registry to obtain, for any
backbone, the same `(X_train, y_train, X_test, y_test, in_dim, make_model_fn)`
the protocol's own models consume. This is a **read-only** use of an existing
function — **no `src/` file was modified**, and no training/aggregation
semantics changed. Target and shadow models are then built by composing
`src.teacher.train_supervised_model`, `src.phase0` builders + `warmup_init`,
`src.distill.distill_all_clients`, and `src.aggregate.aggregate` — the exact
pipeline of `src.protocol.run_cell`, on the designated training subset.

The GLiRA surrogate distillation (`mia.surfaces.distill_surrogate`) reuses the
identical temperatured-KL objective of `src.distill.local_distill_trajectory`
(it trains the protocol's own head to match a black-box model's query logits), so
no new training semantics are introduced.

## How shadow training is chunked under the 3h cap

Shadow-model training dominates wall-clock and is embarrassingly parallel, so the
**chunk unit is the MODEL** (target = model 0, then 64 shadows = 65 models per
(α, seed)). `mia/run.py` is resumable and chunkable exactly like `src/sweep.py`:

- **Per-model checkpoint** — after training each model, its attack contribution
  (IN-mask + φ/loss/surrogate-φ over the attack pool, a few floats per pool
  example) is written to `shadows/<cell>/model_XXXX.npz`. A job that dies mid-run
  resumes by skipping models whose checkpoint already exists.
- **Model-level chunking** — `--num-chunks` / `--chunk-index` (or env
  `NUM_CHUNKS` / `CHUNK_INDEX`) split the 65 models round-robin across jobs. A
  SLURM job-array sets these from `SLURM_ARRAY_TASK_COUNT` / `SLURM_ARRAY_TASK_ID`.
- **Scoring** — a cell is scored (per-cell JSON written) only once **all 65**
  checkpoints are present, so partial chunks defer cleanly; `--score-only` does a
  cheap report-only pass that scores every complete cell and rewrites the table.

### Running (on VALAR; never `python` on the login node)

MNIST (cheap — one job; chunk only if a node is slow):
```sh
sbatch jobs/heifd_021_mia_mnist.sh
# optional chunking, then a score pass:
sbatch --array=0-4 --export=ALL,NUM_CHUNKS=5 jobs/heifd_021_mia_mnist.sh
sbatch --export=ALL,SCORE_ONLY=1            jobs/heifd_021_mia_mnist.sh
```

ViT-B/32 / CIFAR-100 (warm the feature cache once, then fan out, then score):
```sh
python jobs/prefetch_login.py --include-cifar100        # login node, once
sbatch --export=ALL,NUM_CHUNKS=8,CHUNK_INDEX=0 jobs/heifd_021_mia_vit_cifar100.sh
sbatch --array=1-7 --export=ALL,NUM_CHUNKS=8   jobs/heifd_021_mia_vit_cifar100.sh
sbatch --export=ALL,SCORE_ONLY=1              jobs/heifd_021_mia_vit_cifar100.sh
```

Useful env knobs (both wrappers): `HEIFD_SEEDS`, `HEIFD_NSHADOWS`, `HEIFD_POOL`,
`HEIFD_METHOD`.

## Expected comparison (acceptance)

HE-IFD's released-model leakage should be **≤ a matched DP one-shot baseline**,
because DP perturbs the model that is *shipped* whereas HE-IFD ships an
unperturbed θ⋆ and confines perturbation to the Phase-0 summaries. The headline
falsifiable predictions §VI will state:

1. **External / fellow on θ⋆** — low TPR@0.1%FPR and AUC near 0.5 (the bounded
   K-step distillation from a shared basin over many clients limits per-example
   memorisation), comparable to or below a DP one-shot FL baseline at matched
   accuracy.
2. **Prototype channel** — AUC/TPR high at raw release and collapsing toward
   chance (AUC→0.5, TPR@0.1%FPR→0.001) at ε=8 then ε=2, confirming the
   averaging-variant DP accounting empirically.

## Module map

```
mia/
  metrics.py    ROC / AUC / TPR@fixedFPR  (pure NumPy; the scoring foundation)
  attacks.py    threshold (Yeom) · LiRA (Carlini) · GLiRA (Galichin) · prototype-distance
  target.py     reuse src/ to build target + shadow global models; confidence/φ extraction
  surfaces.py   external / fellow array-scorers · GLiRA surrogate distillation · prototype surface
  run.py        resumable, chunkable CLI: train+checkpoint models → score → write results
  report.py     results/heifd_021_mia/ writer (README + summary.json the paper table reads)
```
