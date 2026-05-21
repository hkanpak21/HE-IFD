# HE-IFD

Homomorphic-encryption federated knowledge distillation. One-shot protocol where clients distil locally against their own teachers, ship per-layer encrypted parameter deltas to a server, server does a single linear aggregation, jointly decrypt the released student.

## v1 status (2026-05-21)

Plaintext simulation only. No real FHE — server-side operations are restricted to linear primitives so the simulation upper-bounds what the encrypted version would produce. Single dataset (MNIST), single architecture (MLP 784→128→32→10), single seed, one client-side distillation hyperparameter setting (`K=5` epochs, `τ=4`, KL distillation, `α=0.1` Dirichlet). Six N values: 1, 2, 4, 8, 16, 32.

Headline result: the student exceeds the mean per-client teacher at every N≥2, and the gap **widens monotonically** as N grows — from +8 pp at N=2 to +35 pp at N=32. Full numbers in `results/v1_he-ifd_mlp_mnist_n-sweep/README.md`.

## Layout

```
src/v1/             # v1 source (clean rewrite, no legacy reuse)
  data.py            # MNIST loader, Dirichlet partition, probe extraction
  model.py           # MLP 784->128->32->10 with named per-layer state I/O
  teacher.py         # per-client teacher training (cached)
  distill.py         # client-side KL-distillation, end-of-K cumulative deltas
  aggregate.py       # server-side linear aggregator (FHE-compatible by construction)
  evaluation.py      # student / teacher / oracle accuracy helpers
  cell.py            # single (N, seed) cell driver -> CellResult JSON
  sweep.py           # CLI: sweep over N values + seeds, calls report at end
  report.py          # writes results/<case>/{README.md, results.csv, partition_diagnostic.jsonl}
jobs/
  v1_sweep.sh        # sbatch wrapper -- the only entrypoint that runs python
data/                # datasets (MNIST/, FashionMNIST/, cifar-10-batches-py/)
cache/teachers/      # teacher checkpoints, keyed (dataset, N, alpha, seed)
results/
  v1_he-ifd_mlp_mnist_n-sweep/   # experimental case: see its README for the table
FL_TDSC/             # paper sources + CHANGES.md (Overleaf replay log)
```

## Running v1

```sh
sbatch jobs/v1_sweep.sh
```

Defaults: `Ns=1,2,4,8,16,32`, `seeds=42`, `alpha=0.1`, `K=5`, `tau=4.0`, `probe_size=5000`, `teacher_epochs=30`. Override via env vars (`V1_NS`, `V1_SEEDS`, ...) — see the sbatch script header.

The job emits per-cell `cell_N<n>_s<seed>_<job_id>.json` plus a Slurm `runs/sweep_<job_id>.{out,err}`, then the aggregator overwrites `results/v1_he-ifd_mlp_mnist_n-sweep/README.md` with the populated table.

## Cluster notes

- Conda env: `he_ofl` (has `torch`, `torchvision`, `tenseal`). No new env needed for v1.
- Partition `t4_ai`, account `comx29`. Never run `python` on the login node.
- Datasets live under `data/`; torchvision loaders pass `download=False`.
