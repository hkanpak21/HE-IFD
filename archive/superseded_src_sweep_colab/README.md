# Superseded src/phase0 sweep results (archived 2026-06-02)

`colab_cell_1.csv` and `colab_cell_2_1..2_5.csv` are Colab paste-dumps from the
**pre-pivot `src/` sweep** — the distillation + Phase-0-alignment method, not the
current one.

**Schema (old method):** `backbone,dataset,N,alpha,seed,K,tau,method,phase0_kind,
...,acc,mean_teacher,best_teacher,oracle,theta0_acc,m3_*,m4_*,...` with
`method ∈ {no_phase0, raw_union_K300}`, `phase0_kind`, `tau=4.0`, per-client
teachers, and an oracle column. Backbones `roberta_base_banking77`,
`roberta_base_dbpedia`, `roberta_base_trec`, `vit_b32_cifar100`,
`vit_b32_fgvc_aircraft` (FGVC failed — not prefetched).

**Why archived, not used:** these informed the coverage-gap analysis
(`no_phase0` collapses at extreme skew on many-class tasks while `raw_union`
holds; gap scales with #classes × skew) — see memory `no-alignment-gap-accepted`.
That analysis led to the **2026-06-01 pivot** to one-shot federated **fine-tuning**
(frozen backbone + LoRA, no public data, the increment story). The current paper's
experiment tables fill from the *new* `finetune_increment` runs (Colab E1 +
VALAR `finetune_increment_{e3,sweep}`), **not** from these. Kept for provenance
only.

The matching raw E1 fine-tuning log is at
`archive/finetune_increment_e1_rawlog.txt` (extracted to
`results/finetune_increment_e1/e1_partial.csv` by `tools/extract_increment.py`).
