# PRD — Freeze-A era: method-improvement program + claim-calibrated TNSE resubmission

**Status:** active — `needs-triage`
**Created:** 2026-06-10 (grilling session; extends, does not replace, `he-ifd-finetuning.md`)
**Source of truth:** `results/finetune_increment/results.csv` (E1, both-A-B era — superseded for
method config, still valid as the both-A-B baseline), `results/finetune_improve/` (the program this
PRD defines), `docs/paper/SUBMISSION_TODO.md` ("Decisions locked 2026-06-10" block).
**Origin:** the 2026-06-10 grilling on paper quality. The session memory is
`improvement-program-2026-06-10` in the agent memory directory.

---

## Problem Statement

The paper pivoted to one-shot federated fine-tuning (LoRA + head under multiparty CKKS), but as
written it cannot survive review, and the author cannot yet write honest headline claims:

1. **The central mathematical claim is false.** The paper's spine — aggregation is *linear in the
   encrypted quantities*, i.e. task arithmetic on fine-tuning deltas — does not hold for standard
   LoRA where both A and B train: averaging A's and B's separately does not average the weight
   updates BᵢAᵢ (the merge is bilinear). The symptom is visible in the data: catastrophic seed
   collapses at α=0.1 (AG-News seed 44 lands at 0.27 vs 0.78; TREC seed 43 at 0.23 vs 0.71),
   making reported means meaningless.
2. **The coverage gap is unaddressed.** The shared initialization's head encodes nothing about any
   class, so accuracy on a class is bounded by client coverage. On Banking77 (77 classes, α=0.1)
   the federated model sits ~52 points below centralized. The paper currently says "close to
   centralized" — a claim the data contradicts in this regime.
3. **The modality claim has no data.** "Across vision and language" is asserted; every real number
   is RoBERTa/text. The one vision attempt (FGVC) failed.
4. **Residual-leakage and comparison claims repeat the rejection shape.** The TDSC reviewers (same
   pool as TNSE) dinged asserted-not-measured privacy claims and comparisons against other papers'
   numbers at other papers' setups. The current draft does both again.
5. **The threat model is under-leveraged.** The protocol's actual position — clients receive the
   decrypted model by design, so inter-client inference via the released model is *permitted*;
   protection targets the server and sub-threshold coalitions — is the paper's differentiator
   against DP one-shot work, and it also unlocks method improvements DP papers cannot use. Neither
   point is currently made.
6. The repo accumulated a week of pivot debris: deleted-but-unstaged CSVs, untracked results and
   notebooks, LaTeX build intermediates under version control.

## Solution

Run a structured **method-improvement program** on the corrected configuration before fixing any
claim wording ("improve the method as much as possible and claim accordingly"), then rewrite the
gated paper sections from the winning configuration's numbers.

The program (all levers HE-legal: the server stays a depth-1 linear combiner; client-side work is
pre-encryption, candidate selection is post-decryption among clients):

- **Freeze-A (FFA) LoRA** becomes the method: A frozen at the shared public init, only B (+ head)
  trains, so the encrypted combine is *exact* task arithmetic. Expected side effect: kills the
  seed collapses. S1 A/B-tests this against both-A-B on the unstable tasks.
- **Semantic head initialization**: head row c = centered, normalized embedding of class c's *name*
  under the same public backbone. Public by construction (no client data), gives never-seen-class
  rows a zero-shot starting point — the direct attack on the coverage gap. S2.
- **Depth-1 aggregation candidates ride along in every cell**: plain λ-grid, Fisher-weighted and
  count-head (coverage-aware) merges via the **numerator/denominator trick** (clients send
  Enc(F⊙Δ) and Enc(F); the server only adds; clients decrypt both aggregates and divide in
  plaintext), plus **client-vote selection** (every client scores every decrypted candidate on a
  local holdout; sample-weighted vote picks the release). If plain λ=1 wins everywhere, that is
  the *measured* ablation justifying depth-1 averaging — publishable either way.
- **Client-side flags** (SWA over the trajectory tail, FedProx pull, FedLC logit calibration) held
  in reserve for residual variance. S3, conditional on S1.
- **K × lr re-tune** and **rank compensation** (r ∈ {8,16,32} — freezing A halves capacity) for the
  new configuration. S4/S5.
- **One vision arm** (CIFAR-100, frozen ViT-B/16) in the same wave; the modality claim is kept only
  if the data supports it. S6.

Paper changes gated on the program's outcome: headline claims, the two hero figures, FHE cost
re-measurement on the real winning payload, the comparison table (HE-IFD re-run on multiple
matched published setups, selection later), the residual-leakage section grounded in prior-work
MIA studies (final shape to be discussed with the user), and a threat-model subsection stating the
inter-client-inference position explicitly and noting that DP one-shot baselines protect a
different target.

Repo hygiene: stage the intended deletions, stop tracking LaTeX intermediates, commit the pivot
work in logical units.

## User Stories

1. As the paper author, I want the encrypted-aggregation claim to be mathematically exact, so that no reviewer can falsify the paper's central equation.
2. As the paper author, I want per-seed stability on every reported task, so that means over seeds are honest summaries rather than artifacts of collapses.
3. As the paper author, I want the method improved as far as HE-legality allows before claims are worded, so that the headline is the strongest honest statement the data supports.
4. As the paper author, I want a public, data-free initialization whose head already encodes class semantics, so that the coverage gap at extreme label skew shrinks without any alignment phase or privacy spend.
5. As the paper author, I want every aggregation candidate evaluated in every experiment cell at no extra training cost, so that the choice of aggregation rule is decided by measurement, not assertion.
6. As the paper author, I want a measured answer to "would curvature-weighted merging help?", so that the depth-1 weighted average is justified by an ablation rather than by appeal to prior probes from the superseded method.
7. As the paper author, I want one vision dataset run on the corrected configuration, so that the modality-generality claim is either supported by data or removed.
8. As the paper author, I want the K, learning rate, and rank re-tuned for the freeze-A configuration, so that the new method is not handicapped by hyperparameters tuned for the old one.
9. As the paper author, I want the comparison table built from HE-IFD runs on multiple matched published setups, so that the privacy-utility comparison answers the prior rejection rather than repeating it.
10. As the paper author, I want the residual-leakage section grounded in published MIA studies of fine-tuned and released models, so that the section has a citable base while the measurement question stays open for discussion.
11. As the paper author, I want the threat model to state explicitly that clients may infer from one another via the released model, so that reviewers evaluate the protocol against its actual security target.
12. As a TNSE reviewer, I want the limitation regimes (extreme skew, large label spaces) characterized openly with their mechanism named, so that I find the boundary stated rather than discovering it myself.
13. As a federated client operator, I want everything clever to happen on my device before encryption or after decryption, so that my data and my update never leave in any form other than ciphertext.
14. As an aggregation server operator, I want my entire job to be ciphertext additions and public-scalar multiplications, so that my cost stays depth-1 and independent of how sophisticated the clients' local processing is.
15. As a client in the decryption quorum, I want to score every decrypted candidate model on my own held-out data and vote, so that the released model is chosen by the federation rather than by a fixed server rule.
16. As an AFK compute agent, I want the whole program runnable as resumable stages on both Colab and VALAR from one shared code path, so that a 3-hour wall-clock kill or a Colab disconnect costs one cell, not the program.
17. As an AFK compute agent, I want every results cell to print paste-ready single-header CSV, so that the user can land numbers into the repo from a phone screen if needed.
18. As a context-zero agent, I want the locked decisions and their rationale recorded in the submission TODO, the PRD, and memory, so that I never re-litigate the LoRA configuration or re-propose CT×CT "improvements".
19. As the paper author, I want the repo cleaned and the pivot work committed in logical units, so that the VALAR and Colab sides can pull a coherent state and the git history documents the era boundary.

## Implementation Decisions

- **One canonical runner, embedded everywhere.** The improvement program lives in a single
  self-contained job module; the Colab notebook builder embeds everything above a CLI marker
  verbatim at build time, so the notebook and the VALAR job cannot drift. Editing the job and
  rebuilding the notebook is the only update path.
- **The cell runner is the deep module.** One call — (task, backbone, N, α, seed, K, lr, r,
  freeze_a, sem_init, flags) → a flat result row — encapsulates partitioning, local trajectories,
  Fisher estimation, all aggregation candidates, client-vote selection, and the centralized
  reference. Its interface is the row schema; everything inside can change without touching
  callers.
- **Aggregation candidates are pure state-dict functions**, modality-agnostic (the vision arm
  reuses them unchanged), and independent of transformers/GPUs — deliberately extracted so they
  are testable in isolation with tiny tensors.
- **Freeze-A semantics**: the A matrices are generated from the public seed and frozen; only B and
  the head enter the trainable state, the displacement, and the ciphertexts. Payload roughly
  halves relative to both-A-B at equal rank.
- **Semantic init semantics**: class-name strings (human-readable; overridden where dataset label
  codes are not words) embedded by the same frozen backbone, centered across classes,
  L2-normalized, written into the head rows of θ₀; bias zero. The zero-init LoRA keeps backbone
  outputs identical at step 0, so θ₀ is a genuine zero-shot classifier and its accuracy is itself
  a reported number.
- **Num/denom merging keeps depth 1**: per-client products are formed client-side pre-encryption;
  the server adds ciphertexts; clients jointly decrypt numerator and denominator and divide in
  plaintext. Count-head is the special case where the weights are per-class example counts applied
  to head rows only; rows nobody covers stay at θ₀.
- **Client-vote selection**: each client reserves a fraction of its shard as a local holdout
  (accepting slightly less training data, consistently within the program), scores every decrypted
  candidate, and the sample-weighted argmax is released. Post-decryption, zero HE cost, admissible
  under the threat model.
- **Threat model wording**: honest-but-curious server + sub-threshold coalitions are the protected
  surface (simulation argument unchanged); the released model is outside the protected boundary by
  construction, and inter-client inference through it is permitted. The comparison table must flag
  that DP one-shot baselines protect a different target.
- **Decision flow**: S1 fixes the LoRA configuration → S2 decides whether semantic init joins the
  headline method → candidate columns fix the aggregation rule → S4/S5 fix hyperparameters → the
  full headline grid re-runs in the existing sweep machinery with the winning configuration → only
  then are claims, figures, FHE cost numbers, and the comparison table finalized.
- **Repo hygiene**: LaTeX intermediates (aux/log/out) leave version control and enter the ignore
  list scoped to the paper directory; compiled PDFs and figures stay tracked; the pivot-week work
  is committed as paper-restructure, increment-experiments, improvement-program, and planning
  units.

## Testing Decisions

- A good test exercises **external behavior through the public interface** — the row schema, the
  aggregation identities, the θ₀ contract — never internals like parameter names or loop
  structure.
- **Aggregation candidates** are the primary test target (pure math, no GPU, no network): plain
  combine with λ=1 equals the sample-weighted average of fine-tuned states; Fisher merge with
  uniform Fisher reduces exactly to the plain combine; count-head reproduces the per-class
  weighted average on head rows and the plain combine elsewhere, and leaves uncovered rows at θ₀.
- **Freeze-A task-arithmetic identity** on a tiny synthetic linear model: the merged frozen-A LoRA
  equals the average of the clients' effective weight updates — the property the paper claims —
  and a counter-test documents that both-A-B violates it.
- **Semantic init contract**: correct shape, unit row norms, determinism, and independence from
  any client data.
- Prior art: the existing aggregate/finetune test files in the repo's test directory; same style
  (deferred imports, CPU-only, seeded).
- The heavy paths (transformers, peft, Colab cells) are validated by the VERIFY notebook cell and
  per-cell JSON outputs, not by unit tests.
- *(Module sketch and test scope chosen per the author's standing delegation; revise at triage if
  the breakdown does not match expectations.)*

## Out of Scope

- Anything requiring ciphertext×ciphertext multiplication, multi-round communication, or any
  data-derived quantity leaving a client unencrypted — these break the paper's spine and are
  permanently out of scope, not deferred.
- New MIA attacks/measurements on the new method (the residual-leakage section is prior-work-based
  for now; a measurement decision is an open discussion item, not part of this PRD).
- DP noise on the released model (the threat model deliberately does not claim record-level
  protection against fellow clients).
- A second vision dataset, CLIP-style semantic init for vision backbones, and Byzantine-robust
  leave-one-out candidate screening — noted as extensions, not commitments.
- Re-running comparator vendor code (repo rule: cite published numbers; run HE-IFD on matched
  setups).
- The final paper writing pass itself (HITL with the user, separate from this PRD's compute and
  hygiene scope).

## Further Notes

- The grilling resolved one open contradiction in the repo's memory: the earlier "deep merges are
  provably unnecessary (probes 023/024/025)" verdict was measured on the *distillation-era* method
  in its shared basin; the freeze-A LoRA setting at extreme skew re-opens the question, and the
  candidate columns answer it by measurement. The memory file records this supersession.
- Banking77 remains the designated stress case. If semantic init + count-head + rank compensation
  do not move it materially, the two-regime framing (match centralized at moderate skew; coverage-
  bounded at extreme skew, mechanism named) is the fallback headline — that fallback was discussed
  and is acceptable, but only after the levers have been tried.
- Pending compute from the previous era (VALAR increment sweep stages, both-A-B) is superseded for
  method decisions but stays as the documented baseline; do not burn further compute on both-A-B
  beyond S1's comparison arm.
