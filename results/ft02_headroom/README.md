# ft02_headroom

Linear-probe **headroom check** — the dataset selection criterion for the
fine-tuning pivot (issue ft02). For each `(backbone, dataset)` a single
`nn.Linear` probe is fit on the frozen features the protocol would use, and the
task is **KEPT** only if the probe's test accuracy is below the ceiling (default
0.90) — i.e. a frozen backbone does NOT already solve it, so fine-tuning has real
headroom. CIFAR-10 on ViT-B/32 (≈0.97) would be DROPPED; CUB/Cars/Aircraft and
the harder text tasks should be KEPT.

This case is produced by `python -m src.headroom` (run via `jobs/ft02_headroom.sh`
on a compute node). It writes:

- `headroom.csv` — one row per `(backbone, dataset)`:
  `backbone,dataset,num_classes,n_train,n_test,train_acc,test_acc,headroom,verdict`
- `headroom.json` — the same rows with status/error.
- `partition_diagnostic.jsonl` — per-`(N, α)` seed-keyed Dirichlet partition
  counts on each new dataset, proving the loaders flow through the unchanged
  partition machinery.

## Datasets under test

| modality | dataset | classes | backbone(s) | fetch |
|---|---|---|---|---|
| fine-grained vision | CUB-200-2011 | 200 | vit_b32 | manual (Caltech curl; see `src/data.py`) |
| fine-grained vision | Stanford Cars | 196 | vit_b32 | manual (Kaggle/HF; torchvision URL dead) |
| fine-grained vision | FGVC-Aircraft | 100 | vit_b32 | `prefetch_login.py --include-ft02-fgvc` |
| large-label / domain-shift | Tiny-ImageNet (primary) | 200 | resnet18/vit_b32 | `--include-tiny-imagenet` (issue 012) |
| domain-shift (alt) | DomainNet-clipart | 345 | vit_b32 | manual (BU mirror; see `src/data.py`) |
| harder text | Banking77 | 77 | roberta_base/mpnet_st | `--include-ft02-text` |
| harder text | DBpedia-14 | 14 | roberta_base/mpnet_st | `--include-text019` (issue 019) |
| harder text | 20-Newsgroups | 20 | roberta_base/mpnet_st | `--include-ft02-text` |
| harder text | TREC (coarse) | 6 | roberta_base/mpnet_st | `--include-ft02-text` |

_(table auto-populated into `headroom.csv` after the job lands.)_
