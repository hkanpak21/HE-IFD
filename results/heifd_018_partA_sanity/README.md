# heifd_018_partA_sanity

Issue 018 **Part A** — standalone centralised linear-probe sanity-check on the
three big pretrained backbones (ViT-L/16 on CIFAR-100, BERT-large-uncased on
AG-News, GPT-2-medium on AG-News), run **before** the protocol so we never
apply the protocol to a backbone we cannot even linear-probe. This case holds
ONLY Part A; **Part B (the protocol + LoRA on the big backbones) is HITL-gated**
— the orchestrator routes the numbers below to the user, who must authorise the
bigger compute before any Part-B wrapper is written or submitted.

## What the metric is

`jobs/heifd_018_partA_sanity.sh` runs one cheap cell per backbone (N=1, α=1.0,
method=`no_phase0`, K=1). The headline number is the cell's **`oracle`** field:
`protocol.run_cell` trains a centralised supervised head on the full training
pool and evaluates it on held-out test — at N=1/α=1.0 that pool is the whole
training set (minus the small labelled probe), so `oracle` is exactly the
standalone centralised linear-probe / supervised-head IID accuracy. The gate
reads `oracle`, not `acc` (the protocol output is irrelevant here).

## Sanity gates

| Backbone | Dataset | Gate (IID `oracle`) | Type |
|---|---|---:|---|
| `vit_l_cifar100` | CIFAR-100 | ≥ **0.78** | **BLOCKING** — fail ⇒ STOP, report, do not enter Part B |
| `bert_large_agnews` | AG-News | ≥ **0.92** | **BLOCKING** — fail ⇒ STOP, report |
| `gpt2_medium_agnews` | AG-News | ≥ **0.50** | **INFORMATIONAL** — GPT-2 family deferred (issue 002); failure is NOT a block |

If `vit_l_cifar100` or `bert_large_agnews` misses its gate: clean abort, report
which backbone + expected-vs-observed IID + what hparam tuning would be needed
(per issue 018 acceptance). Do not proceed to Part B with a backbone we cannot
linear-probe properly.

## Results

_(Auto-populated by `src.report.write_report` once the job lands. Until then this
section is a placeholder.)_

| Backbone | IID (`oracle`) | Gate | PASS/FAIL |
|---|---:|---:|---|
| vit_l_cifar100 | — | 0.78 | — |
| bert_large_agnews | — | 0.92 | — |
| gpt2_medium_agnews | — | 0.50 (info) | — |

## Run configuration

- Backbones (one per job via `HEIFD_018_BACKBONE`): `vit_l_cifar100`,
  `bert_large_agnews`, `gpt2_medium_agnews`.
- N=1, α=1.0, method=`no_phase0`, seed=42, K=1, τ=1, lr=0.001, scope `head_only`.
- Memory 64G, ≤3h, single T4. Big-model feature extraction (ViT-L/16 ~304M,
  BERT-large ~335M over the full train+test sets) is the heavy part; per-backbone
  isolation keeps each job under the 3h cap and avoids concurrent-extraction OOM.
- Prefetch prerequisite (login node):
  `python jobs/prefetch_login.py --include-cifar100 --include-big-backbones`.

## Next — Part B (HITL-gated, NOT in this case)

After the user reviews the gates above and authorises it: head-only sweep on
(at least) ViT-L/CIFAR-100, then issue-011's LoRA recipe applied to ≥1 big
backbone if head-only reproduces the θ₀≥final under-capacity pattern. No Part-B
wrapper exists yet by design.
