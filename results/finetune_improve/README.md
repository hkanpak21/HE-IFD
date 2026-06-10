# finetune_improve — the method-improvement program (freeze-A era)

Decisions locked 2026-06-10: switch to **freeze-A (FFA) LoRA** so the encrypted
aggregation is exact task arithmetic; test **semantic head init** (zero-shot
public θ₀ from class-name embeddings) against the coverage gap; compare the
depth-1 **aggregation candidates** (plain λ grid, Fisher and count-head
num/denom merges, client-vote selection) which ride along in every cell.

Stages (Colab: `notebooks/improve_program.ipynb`; VALAR: `sbatch
jobs/finetune_improve.sh`, array index = stage):

- **s1** freeze-A vs both-A-B on the seed-unstable tasks (ag_news, trec)
- **s2** semantic head init across ag_news/trec/dbpedia_14/banking77
- **s3** client-side flags (SWA / prox / logit calibration) — only if s1 still unstable
- **s4** K × lr mini-grid for the freeze-A config
- **s5** rank compensation (r ∈ {8,16,32}) on banking77
- **s6** vision arm CIFAR-100 / ViT-B/16 (notebook only)

Per-cell JSONs land here; paste each notebook section's CSV block into
`<section>.csv` (e.g. `s1_freeze_a.csv`). Schema:

```
task,backbone,N,alpha,seed,K,r,freeze_a,sem_init,swa,prox_mu,calib_tau,n_trainable,A0,Astar,acc_fisher,acc_counthead,lam_best,acc_lam_best,selected,acc_selected,A_central,increment,gap
```
