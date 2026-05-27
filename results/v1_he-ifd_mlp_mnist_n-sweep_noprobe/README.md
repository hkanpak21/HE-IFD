# v1 HE-IFD N-sweep — MNIST MLP

HE-IFD v1 simulation (plaintext): clients locally distil from their teachers into a shared random init via KL with temperature, ship per-layer cumulative deltas, the server averages them linearly (FHE-compatible). Tests whether the protocol learns and whether accuracy scales with N. Architecture MLP 784->128->32->10 on MNIST, Dirichlet alpha=0.1 partition; no real FHE in v1 -- server-side operations are restricted to linear ops (addition + plaintext-scalar multiplication) so the simulation upper-bounds what the encrypted version produces. Default distillation set is the client's local data D_i only (no public probe); see `use_probe` flag.

## Sweep configuration

- N values swept: `10`
- Seeds: `42`
- Dirichlet alpha: `0.1`
- K (client distill epochs): `5`
- tau (distill temperature): `4.0`
- use_probe: `False`
- Probe size (only if use_probe): `5000`
- Teacher epochs: `30`

## Results

| N | seed | student_acc | mean_teacher_acc | best_teacher_acc | worst_teacher_acc | wall_clock (s) | status |
|---|------|-------------|------------------|------------------|-------------------|----------------|--------|
| 10 | 42 | 0.6209 | 0.4636 | 0.6818 | 0.2984 | 677.3 | success |

Raw per-cell JSONs live in this directory as `cell_N<n>_s<seed>_<job_id>.json`.
Partition diagnostic (per-client per-class sample counts) at `partition_diagnostic.jsonl`.
Slurm stdout/stderr at `runs/`.
