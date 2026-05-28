# heifd_010_kd_hparams_resnet18

Focused KD-hyperparameter sweep on the regime issue 008 flagged broken: resnet18 / CIFAR-10 / α=0.05 / N=10 / raw_union_K20, where the bounded-trajectory student lands at 0.48 IID acc while the warmed init θ₀ alone reaches 0.74 — distillation actively degrades a strong aligned init by 26 pp. This case crosses K ∈ {30, 100, 300, 1000} × τ ∈ {1, 4} × student-LR ∈ {0.001, 0.01} over 3 seeds (48 cells) to test whether the gap closes by KD hyperparams alone (orthogonal to issue 011's trainable-layer-scope test and issue 013's KD-dynamics diagnostic). Verdict — gap closed / partial / not closed — will be filled in once the run lands; if no config beats θ₀ = 0.74 by ≥3 pp, the issue 011 (capacity) + 013 (diagnostic) escalation path applies and the headline ResNet-18 row stays unfixed by this axis alone.

## Sweep configuration

- Backbone: `resnet18_cifar10` (frozen ImageNet ResNet-18 features + trainable linear head)
- N: `10`
- Dirichlet α: `0.05`
- Method: `raw_union_K20` (Phase-0 alignment via raw per-class prototypes, K_per_class=20; held fixed to isolate KD axes)
- Seeds: `42, 43, 44`
- K (bounded trajectory length): swept `{30, 100, 300, 1000}`
- τ (KD softmax temperature): swept `{1, 4}`
- Student LR (SGD): swept `{0.001, 0.01}`
- Labelled-probe size P: backbone default (100)
- Reference numbers from issue 008 at the legacy default cell (K=300, τ=4, lr=0.01): raw_union mean acc 0.48 vs θ₀ 0.74.

## Sweep mechanics

- Submitted as a 4-task SLURM array (`--array=0-3`). Each task runs 12 of the 48 cells via the resumable `--num-chunks` / `--chunk-index` mechanism in `src/sweep.py`. Round-robin striping spreads slow K=1000 cells across all chunks, keeping wall-clock balanced.
- The 48 cells use the new `--Ks` / `--taus` / `--student-lrs` multi-axis flags in `src/sweep.py` (additive — single-value `--K` / `--tau` / `--student-lr` flags keep their legacy contract for all other sweeps).
- Per-cell filenames now record non-default (τ, lr) so they don't collide with legacy `K=300 / τ=4.0 / lr=0.01` cells from issue 008.

## Results

_To be populated by the auto-writer when the sweep lands. Expected columns: backbone, N, α, method, seed, K, τ, lr, acc, mean_teacher, best_teacher, oracle, θ₀_acc, M3_mean_gap, M3_helped, M4_ood_acc, σ, status._
