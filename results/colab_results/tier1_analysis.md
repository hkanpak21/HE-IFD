# TIER-1 — aggregation strategy + client/server optimizer deep-dive (analysis)

Colab run, 2026-05-31/06-01. CSVs in this dir: `heifd_lambda.csv`, `heifd_tier1_axisB.csv`
(both 3-seed), and `heifd_tier1_{axisA,axisB_new,axisC,AxB}.csv` (Axis A/B-new/C single-seed
smoke s42 α{0.05,1.0}; A×B 3-seed α{0.05,0.3,1.0}). Backbones `mlp_mnist`, `vit_b32_cifar100`.

## One-line verdict
The only **HE-legal** accuracy lever is a **depth-1 shrink of the displacement toward θ₀**
(`λ<1` / `lambda_scaled`), and it helps **only on the pretrained backbone under heterogeneity**
(ViT/CIFAR-100 α≤0.3, ~+0.02–0.035). **Client-side adaptivity buys nothing and momentum is
actively harmful; deep server rules and client/coord selection buy nothing.** At near-IID,
plain `weight_avg` + `λ=1` + `SGD` is optimal. So the deployable default stays depth-1, and the
"we explored the full optimizer/aggregation space" claim is earned.

## Axis A — client optimizer (the hypothesized "win"): REFUTED
- **Momentum & Nesterov DESTABILIZE the bounded K-step trajectory** — they diverge at lr≥0.03
  (acc→chance 0.10, Δ-norm-spread explodes 0.2→>1.0). Momentum accumulates over K=300 steps with
  no cross-round reset → overshoot. Clean negative, specific to the one-shot bounded regime
  (contra multi-round FL, where momentum helps).
- **Adaptive (Adam/AdamW/RMSProp/Adagrad/LAMB) does NOT beat tuned SGD under heterogeneity.**
  MNIST α=0.05 best = **SGD lr=0.03 (0.8514)** > SGD 0.01 (0.8466) > all adaptive (0.82–0.84);
  ViT α=0.05 best = LAMB 0.001 (0.7785) ≈ SGD 0.01 (0.7709), within noise. At near-IID a small
  +0.01 from momentum/adaptive, but they're not needed.
- **The biggest Axis-A lever is just the SGD learning rate** (0.01→0.03 at α=0.05). The headline
  grid used 0.01; 0.03 is a free ~+0.005.
- Δ-drift diagnostic tracks stability: stable runs Δspread 0.02–0.2, diverged runs >1.0.

## Axis B — server combine: shrink-toward-θ₀ is the only lever (depth-1 captures it)
λ-axis and both server-combine sweeps agree. On the hard cell (ViT α=0.05, weight_avg=0.7709):

| rule | acc | Δ vs WA | HE depth |
|---|---|---|---|
| λ⋆=0 (basin alone) | 0.8051 | **+0.0345** | depth-1 |
| `lambda_scaled` (λ=0.5) | 0.8004 | +0.0295 | **depth-1** |
| `fedadam/fedyogi_1step` | 0.8017 | +0.0308 | deep |
| `poly_gate_d2_a/b` | ~0.805 | +0.035 | depth-2 |
| `agreement_gated` / `second_moment` | 0.799/0.799 | +0.028 | deep |
| `top_k` / `fisher` / `dare` | 0.79/0.79/0.775 | +0.017/+0.019/+0.004 | deep/deep/depth-1 |
| `ties`, `coord_median/trimmed`, `mag_weighted` | ≤ WA | ≤0 | deep |

All winners do the same thing (down-weight high-disagreement coords toward θ₀); the **depth-1
`lambda_scaled` and depth-2 poly-gate match the best deep rule** — deep rules add nothing.
At α=1.0 every combine ≤ `weight_avg`. `ties` and `fisher` consistently HURT.

## Axis C — selection: no win
`drop_topnorm_k1/k2` (drop the most-divergent clients) **loses everywhere** (MNIST −0.003/−0.019;
ViT −0.017/−0.023). The harmful displacement is distributed, not from outlier clients; dropping a
client just loses its data.

## A×B payoff — caveat: used the wrong optimizer
The A×B cell ran `BEST_OPT='sgd_momentum'` (a leftover placeholder), but Axis A shows sgd_momentum
is suboptimal/unstable — so its `weight_avg` baseline is depressed (ViT α=0.05 0.7319 vs plain-SGD
0.7709). The qualitative result still holds (`lambda_scaled` > `weight_avg` under heterogeneity:
ViT α=0.05 0.7933 vs 0.7319), but **A×B should be re-run with `BEST_OPT='sgd'`** for clean numbers.

## Deployable HE-legal winner + caveats
- **Default: SGD client optimizer (tune lr) + depth-1 `weight_avg`, with `λ<1` (lambda_scaled)
  switched in under heterogeneity** on the pretrained backbone — beats the SGD+WA+λ=1 default by
  ~+0.02–0.035 at ViT α≤0.3, neutral at near-IID.
- **Caveats:** Axis A/B-new/C are single-seed (s42) smokes — expand to 3 seeds before the paper.
  Re-run A×B with `sgd`. The λ<1 gain is partly a *symptom* (under heterogeneity the bounded
  displacement on ViT partially hurts, so the basin θ₀ alone is competitive) — frame as
  "alignment carries the load; a depth-1 shrink recovers the rest," not "our aggregation is rich."
