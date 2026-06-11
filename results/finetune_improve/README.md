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

---

## Decision memo (fa01 — program complete, 2026-06-11)

**Winning configuration: freeze-A LoRA r=8 + head, sem_init OFF, candidate set
{plain λ grid, fisher, count_head} + client-vote selection.** K=200 default;
K=400 is accuracy-optimal where client budget allows (DBpedia sel 0.937 vs
0.928, monotone in K; lr 1e-3 ≥ 5e-4). Rank: r=8 beats 16/32 on banking77.

| task (sel = vote-selected acc, 3 seeds) | plain λ=1 | selected | central |
|---|---|---|---|
| ag_news  freeze-A           | 0.51 | **0.75 ± 0.09** | 0.91 |
| trec     freeze-A           | 0.51 | **0.72 ± 0.05** | 0.96 |
| dbpedia  freeze-A K400      | 0.84 | **0.94 ± 0.00** | 0.99 |
| banking77 freeze-A          | 0.39 | **0.77 ± 0.02** | 0.88 |
| cifar/llm: see s6 / results/llm_scale (count_head 0.87–0.88 dbpedia@qwen) | | | |

- **Freeze-A confirmed** vs both-A-B: +7pp/+15pp (ag/trec) on selected, 2–3×
  lower seed std, advantage concentrated on collapse seeds (0.65 vs 0.48,
  0.66 vs 0.49). Plus halved payload.
- **The candidate set + vote is the headline mechanism**: plain λ=1 alone
  still collapses on bad seeds; count_head is the modal winner (28/39),
  fisher second (10/39). Vote picks the exact test-best candidate in 34/39
  cells; 4 of 5 misses are ≤2pp or on sem_init cells, worst case TREC −9.8pp
  (small holdouts).
- **Semantic init: DROP from the method, keep as ablation.** Zero-shot A0
  stays at chance; banking77 0.724 vs 0.769 without it; trec 0.425 vs 0.716.
  Only effect: variance↓ on ag_news at equal mean.
- **Banking77 coverage gap: 0.52 → 0.11** (0.77 vs central 0.88) from
  freeze-A + count_head + vote alone.
- s3 (SWA/prox/calib) not run: the candidate set already absorbs the
  instability plain averaging suffers; revisit only if a reviewer asks.
- fa02 MIA target set accordingly: count_head aggregate, sem_init off.
