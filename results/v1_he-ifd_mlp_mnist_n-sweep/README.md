# v1 HE-IFD N-sweep — MNIST MLP

HE-IFD v1 simulation (plaintext): clients locally distil from their teachers into a shared random init via KL with temperature, ship per-layer cumulative deltas, the server averages them linearly (FHE-compatible). Tests whether the protocol learns and whether accuracy scales with N. Architecture MLP 784->128->32->10 on MNIST, Dirichlet alpha=0.1 partition; no real FHE in v1 -- server-side operations are restricted to linear ops (addition + plaintext-scalar multiplication) so the simulation upper-bounds what the encrypted version produces.

## Sweep configuration

- N values swept: `1,2,4,8,16,32`
- Seeds: `42`
- Dirichlet alpha: `0.1`
- K (client distill epochs): `5`
- tau (distill temperature): `4.0`
- Probe size: `5000`
- Teacher epochs: `30`

## Results

| N | seed | student_acc | mean_teacher_acc | wall_clock (s) | status |
|---|------|-------------|------------------|----------------|--------|
| 1 | 42 | 0.9806 | 0.9834 | 427.7 | success |
| 2 | 42 | 0.6744 | 0.5932 | 361.4 | success |
| 4 | 42 | 0.6212 | 0.4870 | 370.2 | success |
| 8 | 42 | 0.5318 | 0.4506 | 390.3 | success |
| 16 | 42 | 0.6662 | 0.4314 | 437.4 | success |
| 32 | 42 | 0.7120 | 0.3634 | 515.7 | success |

Raw per-cell JSONs live in this directory as `cell_N<n>_s<seed>_<job_id>.json`.
Partition diagnostic (per-client per-class sample counts) at `partition_diagnostic.jsonl`.
Slurm stdout/stderr at `runs/`.
