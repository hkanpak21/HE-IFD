# Issues — Milestone 1 (Foundation + Headline)

File-based issue tracker. Each issue is a self-contained brief for a **context-zero agent** (you have no conversation history — read the linked files). Source of the plan: [`docs/prd/he-ifd-tnse-resubmission.md`](../prd/he-ifd-tnse-resubmission.md). Operations: [`../../CLAUDE.md`](../../CLAUDE.md). Authoritative implementation to port from: `results/colab_results/results_notebook.ipynb`.

**Milestone 1 only.** M2 (real-FHE, MIA) and M3 (paper) issues are deliberately **not created yet** — they are written after the M1 review gate (009), because headline numbers may shift the design.

Verification philosophy: we do **not** bit-match the colab numbers (the notebook contains a GPT-2 feature-extraction bug; matching it would reproduce the bug). The gate is a **faithful logic port + unit tests + qualitative sanity** (alignment beats no-alignment at low α; IID near the single-model ceiling; post-fix GPT-2 IID ≈ 90%).

## Dependency order

| # | Issue | Type | Blocked by |
|---|---|---|---|
| 001 | [Consolidate notebook → flat `src/` package](001-consolidate-src-package.md) | AFK | — |
| 002 | [Fix GPT-2 feature extraction](002-fix-gpt2-feature-extraction.md) | AFK | 001 |
| 003 | [Unit tests for load-bearing modules](003-unit-tests-load-bearing-modules.md) | AFK | 001 (002 for backbones test) |
| 004 | [Seed-keyed teacher cache](004-teacher-cache.md) | AFK | 001 |
| 005 | [Incentive (M3) + OOD (M4) + θ₀ + no-align metrics](005-incentive-ood-metrics.md) | AFK | 001 |
| 006 | [Aggregation-coherence ablation](006-aggregation-coherence-ablation.md) | AFK | 001, 003 |
| 007 | [From-scratch headline sweep](007-from-scratch-headline-sweep.md) | AFK | 001, 004, 005 |
| 008 | [Pretrained headline sweep](008-pretrained-headline-sweep.md) | AFK | 001, 002, 004, 005 |
| 009 | [M1 review gate](009-m1-review-gate.md) | **HITL** | 006, 007, 008 |

001 is the prerequisite for everything. 002–006 can proceed in parallel once 001 lands. 007/008 are the big VALAR sweeps. 009 stops for human review before M2.
