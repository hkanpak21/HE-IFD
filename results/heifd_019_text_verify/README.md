# heifd_019_text_verify

Verify run for issue 019 — stronger frozen TEXT backbones. Exercises the new
frozen encoders `roberta_base_agnews` and `mpnet_st_agnews` (both bidirectional
→ masked mean-pool; backbone FROZEN, only the linear head displacement enters
the HE combine) on N=10 × α∈{0.05, 1.0} × {no_phase0, raw_union_K20} × seed 42,
K=100/τ=1/lr=0.001. Optional DBpedia-14 cells (`roberta_base_dbpedia`,
`mpnet_st_dbpedia`, 14 classes) when submitted with
`HEIFD_019_INCLUDE_DBPEDIA=1`.

## The question

Does a stronger frozen text encoder bring the text deployment story up to the
ViT/CIFAR-100 vision level? The text half is the weak link: DistilBERT works at
IID (0.864) but collapses at α=0.05.

**The bar to beat — current DistilBERT, AG-News, α=0.05:**

| backbone | α=0.05 acc | θ₀ | mean_teacher | oracle | m4_ood |
|---|---:|---:|---:|---:|---:|
| distilbert_agnews | 0.437 | 0.410 | 0.293 | 0.904 | 0.363 |
| gpt2_agnews | 0.333 | 0.266 | 0.274 | 0.666 | 0.337 |

**Acceptance target (issue 019):** the new backbone's α=0.05 `raw_union_K20`
acc ≥ 0.6 and m4_ood ≥ 0.5 (toward the ViT/CIFAR-100 level: acc 0.811, m4 0.807),
with oracle ≥ 0.93. Expected frozen linear-probe ceilings: RoBERTa ~0.92+,
MPNet ≥0.93.

## Verdict

_(to be filled by the auto-writer + the orchestrator's read of the cells: does a
stronger frozen text encoder beat DistilBERT at α=0.05, and is the full headline
grid (`jobs/heifd_019_text_headline.sh`) cleared for submission?)_

<!-- results table auto-populated below by src.report -->
