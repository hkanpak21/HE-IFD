# heifd_mia_freeze_a — full MIA suite on the freeze-A released model (fa02)

Membership inference against the released θ⋆ of the freeze-A LoRA method —
target and all shadows trained through the real federated pipeline (Dirichlet
partition, bounded K-step trajectories, depth-1 aggregate). Backs the
R1-W4/R2-Q5 response promise on THE submitted method.

- Surface: released model only (contributions are covered by Proposition 1).
- Adversaries: external (Yeom threshold + LiRA, 16 shadows) and fellow-client
  (class-conditional calibrated threshold + LiRA) — the fellow is the headline,
  since our threat model permits inter-client inference.
- Cells: {ag_news, trec, dbpedia_14, banking77} × seeds {42,43,44};
  `sbatch jobs/mia_freeze_a.sh` (array index = cell), resumable per model via
  `shadows/<cell>/model_*.npz`.
- CSV schema: `backbone,N,alpha,method,seed,surface,attack,tpr_at_0.1pct,tpr_at_1pct,auc`.

Submit after the fa01 S1/S2 verdicts (pass `--sem-init` if S2 promotes the
semantic head init into the headline method).
