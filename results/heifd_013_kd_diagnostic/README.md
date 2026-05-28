# heifd_013_kd_diagnostic

Issue 013 — KD-dynamics diagnostic. Two cells (one degrading: `resnet18_cifar10` / α=0.05 / N=10 / `raw_union_K20` / K=20 / seed 42; one working: `mlp_mnist` / α=0.05 / N=10 / `raw_union_K20` / K=20 / seed 42) run with `diagnose=True` via `python -m src.diagnose_cells`, emitting per-cell JSONs that carry teacher logit entropy, per-step ‖Δᵢ⁽ᵏ⁾‖₂ profiles, the N×N pairwise cosine matrix over cumulative Δ, and per-class θ₀-vs-final test accuracy. The post-run analysis interprets these numbers against three candidate hypotheses for the θ₀ ≥ final phenomenon flagged in issue 008 — **basin-cancellation** (clients' Δᵢ point in opposing directions ⇒ small/negative pairwise cosine ⇒ partial cancellation under sample-weighted summation), **teacher-overshoot** (peaky near-one-hot KL targets at low α push the student off the warmed θ₀ along high-norm trajectories), and **capacity-constraint** (a linear head over frozen pretrained features simply cannot absorb a 26-pp jump from non-IID local teachers).

## Sweep configuration

- Backbones: `resnet18_cifar10, mlp_mnist`
- N values: `10`
- Dirichlet α: `0.05`
- Methods: `raw_union_K20`
- Seeds: `42`
- K (bounded trajectory length): `20`
- τ (distill temperature): `4.0`
- Student LR: `0.01`
- Labelled-probe size P: backbone default (100)
- Diagnostics: `diagnose=True` (issue 013 only; default everywhere else is `False`)

## Hypothesis verdict

_Pending live diagnostic data._ Once both cell JSONs are written, this README is updated with the per-cell entropy summary, ‖Δ‖ distribution, off-diagonal cosine distribution, per-class accuracy delta, and the verdict the data supports. The verdict feeds into how issues 010 (KD hyperparams) and 011 (trainable-layer scope) should be parameterised.

## Results

_(populated post-run from the per-cell JSON `diagnostics` field)_

Raw per-cell JSONs live here as `cell_<backbone>_N<n>_a<α>_<method>_s<seed>_K<k>_<hash>.json`. The orchestrator runs `jobs/heifd_013_kd_diagnostic.sh` (entrypoint: `python -m src.diagnose_cells`).
