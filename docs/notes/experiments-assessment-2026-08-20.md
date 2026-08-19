# Assessment of the experiments, 2026-08-20

Written for item T21 of `docs/plan/paper-todo-2026-08-19.md`, which came from the
CryptoKU meeting of 2026-08-07. This is a note, not paper text. Nothing under
`docs/paper/` was edited.

Scope of the audit. Every number printed in `docs/paper/sections/experiments.tex`
was recomputed from the files under `results/`. The code that produced each table
was read under `jobs/` and `src/`. No job was submitted and no training ran.

Summary. The accuracy tables reproduce exactly. Two rows of Table III have no
record at all. One row of Table V disagrees with the record. One sentence about
the naive argmax quotes the wrong cell. Three numbers in Section 5.4 and 5.4's
communication paragraph have no record. The sampling that produced every accuracy
figure is undisclosed, and it is larger than the CIFAR-10 subsample already known.

---

## 1. Verification

### 1.1 The two known items, both confirmed

**Table II is the three-seed mean of the two stratified records, with the mode
mapping stated in the brief.** Confirmed. Every one of the nineteen filled cells
reproduces to the printed precision from
`results/personal_adapter/stratified/results.csv`,
`results/personal_adapter_vision/stratified/results.csv` and
`results/centralised_ceiling/results.csv`.

| task | shared head, record | paper | adapter, record | paper | alone, record | paper | disclosed, record | paper | pooled, record | paper |
|---|---|---|---|---|---|---|---|---|---|---|
| AG-News | 0.6487 | 0.649 | 0.4789 | 0.479 | 0.4749 | 0.475 | 0.7391 | 0.739 | 0.9209 | 0.921 |
| TREC | 0.6067 | 0.607 | 0.4288 | 0.429 | 0.3995 | 0.400 | 0.7107 | 0.711 | 0.9673 | 0.967 |
| DBpedia | 0.7888 | 0.789 | 0.7536 | 0.754 | 0.4505 | 0.451 | 0.9247 | 0.925 | 0.9878 | 0.988 |
| Banking77 | 0.2061 | 0.206 | 0.6857 | 0.686 | 0.2489 | 0.249 | 0.7603 | 0.760 | 0.9229 | 0.923 |
| CIFAR-100 | 0.7477 | 0.748 | 0.7744 | 0.774 | 0.1974 | 0.197 | 0.7845 | 0.784 | none | dash |

The pooled column comes from the `matched_total` rows of
`results/centralised_ceiling/results.csv`, which are 2,000 steps.

**The per-task charge in Section 5.7 is `current` minus `sel_gp_rarefill` and
reads 0.071, 0.104, 0.136, 0.075, 0.029.** Confirmed. The three-seed means of the
difference are 0.0706, 0.1040, 0.1359, 0.0746 and 0.0287, from the same two
stratified files. The four partition differences in the same paragraph also
reproduce, at 0.1817, 0.2567, 0.0631 and 0.1626 against the printed 0.182, 0.257,
0.063 and 0.163.

### 1.2 Mismatches

**M1. Table V, both baseline rows.** The paper prints 6/15 correct cells and a
regret of 0.383 for the sample-weighted majority and for its class-balanced
variant. The record gives **7/15** and **0.403** for both rows.

The `sel_federated` rule picks the personal adapter in all fifteen cells of
`results/personal_adapter/stratified/results.csv` and
`results/personal_adapter_vision/stratified/results.csv`, and the personal
adapter is genuinely better in seven of them, which are AG-News seed 44 (0.4614
against 0.4018), all three Banking77 seeds and all three CIFAR-100 seeds. The
`sel_fed_balanced` rule picks identically in every cell, so its row must carry the
same two numbers.

The regret definition that reproduces the paper's two estimator rows exactly is
the sum over the five tasks of the per-task mean of `max(A, B)` minus the selected
accuracy. Under that definition the zero fill gives 0.0268 and the rare-class fill
gives 0.0186, which round to the printed 0.027 and 0.019. The same definition
gives 0.4027 for both baseline rows, not 0.383. For reference, the per-client vote
gives 0.3788 under the same definition, so 0.383 may have been transcribed from a
third rule.

The caption also says the regret is "averaged over tasks". The quantity printed is
a **sum** over tasks. A true average over the five tasks would print 0.005 and
0.004 for the estimator rows.

**M2. The naive argmax at a hundred classes.** Section 5.4 says the sequential
fold takes "roughly twenty minutes at a hundred classes". The record
`results/fhe_serve/argmax_cost.csv` gives 1,587,433.7 ms at C=100, which is
**26.5 minutes**. The 20.4 minute figure in that file is the C=77 row
(1,225,902.9 ms). The fourteenfold reduction quoted alongside is correct, at
1,587,433.7 over 112,969.6 in `results/fhe_serve/argmax_tournament.csv`.

**M3. The optimism of the local holdout.** Section 5.3 says the personal
arrangement's measured accuracy "exceeds its true global accuracy by 0.29 on
average". Recomputed from the `sel_federated` notes and the `B_personal` rows of
the two stratified files, the mean is **0.2848**, which rounds to 0.28. The range
runs from 0.0199 on CIFAR-100 seed 42 to 0.5715 on TREC seed 43.

**M4. Table III has two rows with no record anywhere.** The label-skew row
(0.812, 0.789, 0.914, 0.971) and the local-steps row (0.718, 0.803, 0.870) are not
in any file under `results/`. Only the alpha=0.10 cell (0.789, from the stratified
file) and the whole client-count row (0.803, 0.826, 0.882, from
`results/personal_adapter/nsweep.csv`) trace to a record. The commit that landed
those two rows, `7937e95`, touched only `docs/paper/main.pdf` and
`docs/paper/sections/experiments.tex`. The supporting prose is unrecorded too,
which covers the seed spread of 0.769 to 0.861 at alpha=0.05 and the gains of 0.27
against 0.06 across the local-steps range. The numbers in
`results/finetune_improve/` cover the same axes but do not match, because that is
the pre-pivot pipeline. Its DBpedia alpha=1.0 mean is 0.9791 against the paper's
0.971, and its alpha=0.3 mean is 0.9609 against the paper's 0.914. Ground rule 6
of the TODO says no number enters the paper without a record. These seven numbers
break it.

**M5. The bootstrapping key material has no record.** The 15.5 MiB at ring degree
2^16 and the 49 s to generate it appear nowhere under `results/`. The code path
exists at `fhe/protocol_cost.go:493` behind the `-btp-keys` flag, and it prints
`bootstrapping_key_bytes` and `bootstrapping_key_gen_ms`, but the output was never
committed. Already flagged as item 3 of Part 6 in
`docs/notes/PI_notes/pastes/T22-T23-cost-comparables.md`.

**M6. The GPU microbenchmarks have no record and no citation.** Section 5.4 states
that a CUDA implementation of CKKS puts the product at 30 ms and the rotation at
29.5 ms at ring degree 2^16. Neither number is under `results/`, and the sentence
carries no reference. `results/fhe_gpu/ring_sweep.json` is our own CPU sweep, not a
GPU measurement, and its ring degree 2^16 rows read 166.7472 ms for the product and
144.11215 ms for the rotation. The ratios the paper computes are arithmetically
right against our own `results/fhe_serve/cost_grid.json` figures of 174.8859 ms and
149.66695 ms, which give 5.83 and 5.07 against the printed "about 6" and "about 5".
The external half of the ratio is unsourced. Commit `0de13c5` removed the source
attribution and never replaced it.

**M7. Table VI mixes two runs that disagree with each other.** Six of the nine rows
come from `results/fhe_serve/cost_grid.json` at N=10 and log N=14, which are
39.0123, 5.38215, 0.71105, 33.1246, 1.1495 and 197.663 ms against the printed 39.0,
5.4, 0.7, 33.1, 1.1 and 198 ms. The reciprocal row of 4.21 s comes from
`results/fhe_serve/protocol_cost.json`, because `cost_grid.json` records
`encrypted_reciprocal_ms` as 0 in every one of its nine entries. The two runs
disagree on the primitives they share. `protocol_cost.json` reads 35.0177 ms for
the product against 39.0123, and 181.094 ms for the key switch against 197.663.
`CLAUDE.md` already warns that these two single-run measurements do not agree. The
paper takes one figure from each and does not say so, and the source-of-truth table
in `CLAUDE.md` maps Table VI to `cost_grid.json` alone.

**M8. Table VI's caption states one ring degree and the table carries two.** The
caption says "at the default setting, N=10 and ring degree 2^14". The three argmax
rows and the reciprocal row were measured at log N=15, per
`results/fhe_serve/argmax_tournament.csv` and the header of
`results/fhe_serve/README.md`. The prose above the table does say that the deep
circuits use 2^15, so the fact is disclosed, but the caption contradicts it.

**M9. The query allowance rounds the wrong way.** Section 5.6 says holding a
coalition of nine clients below fidelity 0.90 requires Q below "roughly
1.4 times 10^3" per client on AG-News. The AG-News curve in
`results/extraction_budget/results.csv` crosses 0.90 at about 1.2 times 10^4
queries, between the 10,000 point at 0.8892 and the 20,000 point at 0.9360.
Divided by nine that is 1.3 times 10^3, so the printed bound is looser than the
record supports. The Banking77 figure is right, at 2.0 times 10^5 over nine equal
to 2.2 times 10^4.

**M10. "To within 0.02" is a mean, not a bound.** Section 5.3 says pooled held-out
measurements estimate the shared arrangement's global accuracy "to within 0.02".
The mean absolute error over the fifteen cells is 0.0194 and the **worst cell is
0.1148**, on TREC seed 44. The same applies to the estimator's own calibration,
where the paper says "within 0.019 on average" and states the average, which is
right at 0.0185, while the worst cell is 0.1227. The first sentence reads as a
bound and the second reads as an average, and only the second is accurate.

**M11. Two different figures for the key-switching traffic.** Table VII gives ten
key-switching shares totalling 2.5 MiB, which is
`key_switch_share_bytes_level_1` of 262,168 bytes each from
`results/fhe_serve/comm_cost.json`. The paragraph under Figure 4 says traffic runs
at "2.0 MiB per participating client", which is
`key_switch_share_bytes_total` of 20,975,820 divided by ten from
`results/fhe_serve/cost_grid.json`. Both are sourced and the level-1 choice is the
right one for a label ciphertext, but a reader who compares the two passages sees a
factor of eight and no explanation. Already raised as item 2 of Part 6 in
`docs/notes/PI_notes/pastes/T22-T23-cost-comparables.md`.

### 1.3 What checks out

Everything below reproduces from its record and needs no change.

- **Table IV**, all twenty-four cells, from
  `results/personal_adapter_vision/cifar10_matched.csv`. The negative charge at
  N=20 and alpha=0.04 is real, at 0.943 disclosed against 0.9478 selected, and the
  paper's account of it is right. Two seeds show the gap and the third shows none,
  at 0.943 against 0.9315, 0.9495 against 0.9495 and 0.951 against 0.948. The
  effective federation of 17 to 19 is in the `n` column.
- **Selection on the matched partitions**, 11 of 12, from the same file. The one
  failure is N=5 and alpha=0.3 on seed 42, where `sel_gp_rarefill` takes 0.9445
  and the other arrangement holds 0.9530.
- **The two estimator rows of Table V**, 12/15 and 13/15, and the regrets 0.027 and
  0.019 under the sum-over-tasks definition.
- **Table VI's six shallow rows and both argmax rows**, listed under M7 and M8.
  The tournament at C=4 is 31,243.5 ms and at C=100 is 112,969.6 ms, so the totals
  of 31.5 s and 113.2 s are right once the 0.237 s of arithmetic and key switch are
  added, and the argmax is 99.2 per cent of the first.
- **The reciprocal**, 4.21 s, 3.16 s, 6.30 s, two refreshes and a relative error of
  1.9 times 10^-8, all from `results/fhe_serve/protocol_cost.json`.
- **The ring-degree and client-count scaling in Section 5.4**, 38.4, 39.0 and
  39.2 ms for the product across client counts, 39.0, 82.5 and 174.9 ms across ring
  degrees, 33.1, 71.6 and 149.7 ms for the rotation, and 103 ms to 1.73 s for the
  key switch, all from `results/fhe_serve/cost_grid.json`. The Figure 4 caption's
  spans of 0.0007 to 0.18 s and 0.10 to 1.7 s are right.
- **Table VII**, every row, from `results/fhe_serve/comm_cost.json`. The 510 MiB
  alternative also reproduces, at 34 refreshes from
  `results/fhe_serve/argmax_tournament.csv` times ten clients times 1,573,253 bytes,
  which is 510.1 MiB.
- **Table VIII**, all eighteen cells, as the mean over three seeds and both
  arrangements from `results/extraction_budget/results.csv`. The boundary variant
  loses in 13 of 15 cells and wins twice by 0.003, as stated. The 0.675 against
  0.755 on Banking77 at 50,000 queries reproduces. The logit solve reaches fidelity
  1.000 at 769 queries.
- **The peer numbers.** DENSE at 50.26 and FedDF at 40.58 on CIFAR-10 at
  alpha=0.1, and DENSE's default of five clients, all from
  `comparators/REPORTED_RESULTS.md` section 4. FedAUXfdp's 75.2 undefended, 74.6 at
  eps=1.0, 72.3 at eps=0.5, 33.9 at eps=0.1 and 12.6 at eps=0.01, all read from the
  alpha=0.16 ShuffleNet column of the tables quoted in section 12 of the same file.
  The four differences of 0.006, 0.029, 0.413 and 0.626 are right.
- **Banking77 selection margins of 0.13 to 0.24.** These are the zero-fill margins
  of 0.1296, 0.1790 and 0.2368 in the notes of
  `results/personal_adapter/stratified/results.csv`. The rare-class fill, which is
  the rule the table sets in bold, gives 0.4554, 0.5347 and 0.5188. The paper does
  not say which variant it quotes.
- **The 0.402 unlucky AG-News seed** and the 0.48 cost of choosing wrongly on
  Banking77, both from the stratified file.

---

## 2. Undisclosed methodology

Each item below is something a reviewer would want stated and the paper does not
state.

**U1. Every text number uses a 20,000-example training subsample and a
5,000-example test subsample.** `load_text` at `jobs/finetune_improve.py:100`
defaults to `max_train=20000, max_test=5000`, and `_data` at line 329 calls it
without overrides. AG-News has 120,000 training and 7,600 test examples and DBpedia
has 560,000 and 70,000, so both are cut. TREC and Banking77 are smaller than the
caps and survive whole. Table II's AG-News and DBpedia accuracies therefore rest on
5,000 test examples, and the whole federation at N=10 shares 20,000 training
examples, so a client holds about 2,000. This is the same defect as the known
CIFAR-10 one and it is larger, because it touches four of the five tasks in the
headline table.

**U2. Every vision number uses a 10,000-example training subsample and a
2,000-example test subsample.** `load_vision` at `jobs/vision_matched.py:62`
defaults to `max_train=10000, max_test=2000`, and `jobs/personal_adapter_vision.py:209`
calls it with the seed only. This is the known Table IV item, and it also applies to
**Table II's CIFAR-100 row**, which the brief did not mention. A 2,000-image test
set over a hundred classes is about twenty images per class. It also sets the
resolution of Table IV. At an accuracy near 0.95 on 2,000 test images the binomial
standard error is about 0.005, which is exactly the size of the negative charge the
paper reports at N=20 and alpha=0.04 and defends at length in its own paragraph.

**U3. Clients are dropped, and not only in the cell where the paper says so.**
`MIN_SHARD = 20` at `jobs/personal_adapter_test.py:83` drops any client whose
Dirichlet shard holds fewer than twenty examples. The `n` column of
`results/personal_adapter/stratified/results.csv` shows **AG-News seed 44 ran with
seven clients and TREC seed 44 ran with nine**, while Table II's caption says
N=10 without qualification. AG-News seed 44 is also the outlier that drags the
shared-head mean from about 0.77 to 0.649, and the paper attributes it to "an
unlucky partition" without saying that three clients were removed.

**U4. The seed changes the data, not only the split.** `load_text` and
`load_vision` both key their subsampling generator on the seed, so seed 42, 43 and
44 train and test on different subsets of the corpus as well as on different
partitions and different adapter initialisations. The three-seed spread therefore
mixes three sources of variation, and the paper reads as if it varies the partition
alone.

**U5. Every client in every run draws the same minibatch index sequence.**
`train_steps` at `jobs/finetune_improve.py:203` sets
`torch.Generator().manual_seed(0)` and never reseeds it. The sampling stream is
therefore identical across clients, seeds and tasks.

**U6. Two hundred steps means different numbers of epochs for different clients.**
The sampler draws with replacement, so 200 steps at batch 32 is 6,400 draws. A
client holding 2,000 examples sees about three epochs and a client holding 200 sees
about thirty-two. The paper calls it a bounded trajectory of 200 steps and leaves
the reader to assume the exposure is comparable.

**U7. The optimiser and the adapter geometry are unstated.** AdamW, learning rate
5 times 10^-4, batch 32, LoRA alpha equal to twice the rank, dropout 0, and the
adapter attached to the query and value projections only, from
`jobs/personal_adapter_test.py:71` and `jobs/finetune_improve.py:74`. Text inputs
are truncated to 128 tokens at `jobs/finetune_improve.py:115`.

**U8. The vision backbone is `google/vit-base-patch16-224-in21k`**, at
`jobs/vision_matched.py:50`. The paper says ViT-B/16 and cites the architecture
paper. A reviewer will want the pretraining corpus named, because ImageNet-21k
covers the CIFAR label space and that is most of why the CIFAR-10 numbers sit at
0.95.

**U9. The pooled reference sees more data than the federation.**
`jobs/centralised_ceiling.py` trains on the whole 20,000-example subsample. The
federated runs carve about ten per cent of every shard into a holdout and drop
short clients, so they train on less. The pooled run also spends N times K equal to
2,000 steps even in the AG-News seed 44 cell where the effective N was seven. Both
choices inflate the pooled column, which is the column the paper uses to argue that
the partition costs more than the disclosure does.

**U10. Two of Table II's columns average over clients and none reports spread.**
The `alone` and `adapter` columns are means over clients as well as over seeds. The
record carries the per-client range and the paper prints none of it. On AG-News seed
43 the personal adapter runs from 0.2446 to 0.7738 across the ten clients, and on
TREC seed 43 from 0.1300 to 0.7620, both from
`results/personal_adapter/stratified/results.csv`.

**U11. The extraction adversary queries an isotropic Gaussian, and is scored on
one.** `jobs/extraction_budget.py` draws both the queries and the 20,000 evaluation
points from `rng.normal(0, 1/sqrt(d))` over the 768-dimensional feature space. The
paper says fidelity is measured "on held-out features", which reads as features of
real held-out inputs. No real feature vector enters the attack or the evaluation.
The majority baselines in Table VIII are properties of that Gaussian, which is why
AG-News reads 0.488 rather than the 0.25 a uniform label space would give.

**U12. The rare-class fill uses an absolute threshold of two training examples.**
`RARE_Q = 2` at `jobs/personal_adapter_test.py:75`. The paper says the fill comes
from "each client's rarest classes" and never states the threshold, although the
threshold is what makes the rule work at C=4.

**U13. The scaling law behind the allowance varies C only, never d, and uses two
seeds and synthetic heads.** `jobs/extraction_scale.py` fixes `D = 768`, sweeps
`CLASSES = [4, 16, 64, 256]`, uses `SEEDS = [42, 43]`, and builds each head from
`rng.normal` rather than from training. Section 5.6 tells a deployment it can set
its allowance "from C and d". The record in
`results/extraction_scale/results.csv` supports the C half of that sentence.

**U14. Table IV's record is hand-assembled and its log is not committed.**
`results/personal_adapter_vision/cifar10_matched.csv` carries a `match` column that
`jobs/personal_adapter_vision.py` never prints, so the file was built by hand from a
slurm log. `results/personal_adapter_vision/runs/` and
`results/personal_adapter/runs/` are both empty, so the log is gone. The same is
true of the stratified files.

**U15. The CPU is never named** and every FHE timing is a single run. The paper
says "single-run wall clock on a commodity CPU" and "reported as indicative", so the
single run is disclosed. The machine is not, and `results/fhe_serve/README.md`
records only "VALAR `t4_ai`, CPU path".

**U16. Table III's client-count and local-steps rows are one seed.** The caption
says so, which is honest, and it also means the paper's blanket claim in Setup that
"every number is the mean over three seeds" is contradicted seventy lines later.

---

## 3. Gaps a TNSE reviewer will ask about

**G1. No baseline runs.** The paper compares against published numbers on a
different backbone and says clearly that the backbone accounts for the margin. That
is honest and it leaves the paper with no measured comparison of any kind. A
reviewer will ask for at least one method run under our own conditions. The cheapest
credible ones are a frozen-backbone linear probe on the pooled data, which is
already close to the `matched_total` rows of
`results/centralised_ceiling/results.csv`, and FedAvg over a handful of rounds on
the same adapter, which is the thing the introduction argues against.

**G2. No ablation of the trainable unit.** `docs/plan/paper-rewrite.md` lists a
trainable-unit ablation as planned Table 3 and it never landed. Nothing in the paper
shows that rank 8 is a reasonable choice, that freezing the down-projection helps,
or that the coverage-weighted head merge beats plain sample weighting. A pre-pivot
record answers two of the three. In `results/finetune_improve/`, Banking77 at
rank 8, 16 and 32 gives three-seed means of 0.7238, 0.7108 and 0.6932, and AG-News
and TREC with the down-projection unfrozen give 0.6833 and 0.5667 against 0.7525
and 0.7160 with it frozen. Those numbers were produced by the superseded pipeline
and cannot be quoted, but they show the ablation is cheap and will come out the
right way.

**G3. One backbone per modality.** Every text number is RoBERTa-base and every
vision number is ViT-B/16. The paper's scope paragraph claims the construction
fixes the position of the shared map and not the task. That claim rests on two
encoders.

**G4. The one regime where the design should fail is not tested.** Setup states
that the Dirichlet partition "holds the feature distribution fixed across clients".
The personal-adapter arrangement works because every client's representation stays
near a common frame. A partition that moves the feature distribution, which is the
covariate-shift case in the same taxonomy the paper cites, is exactly where a shared
head over privately adapted representations should break. Nothing measures it. A
reviewer will find this faster than any other gap, because the paper itself names the
assumption.

**G5. The client-count sweep stops before it gets interesting.** It runs
N in {10, 20, 50} on one task and one seed, and the selected accuracy rises
monotonically from 0.8026 to 0.8822 in `results/personal_adapter/nsweep.csv`. The
curve never turns over, so the paper reports a trend and not a limit. Federated
learning reviewers ask about a hundred clients and more, and the coverage argument
that carries the whole shared-head story predicts that the shared head keeps
improving while each client's own adapter gets worse. That is a prediction the paper
could test and does not.

**G6. The headline selection result is one cell wide.** The rare-class fill wins
13/15 against the zero fill's 12/15, on the same fifteen cells. The paper sets the
first in bold. `docs/plan/paper-rewrite.md` already records the fix, which is to fold
the twelve CIFAR-10 cells of
`results/personal_adapter_vision/cifar10_matched.csv` into Table V and report 24/27.
That costs no compute and it also removes the oddity that selection is reported
twice in two places at two rates.

**G7. All of the estimator's regret comes from one task.** Under the definition
that reproduces the printed 0.027 and 0.019, AG-News, TREC, DBpedia and Banking77
each contribute zero and CIFAR-100 contributes everything. The estimator is never
wrong on a text task in the record. A reviewer who notices will read the regret
column as a CIFAR-100 statistic wearing a five-task label.

**G8. The malicious-client limitation carries no number.** Section 5.8 says a
client that uploads a crafted head displacement can bias the shared head and that
the server cannot inspect it. `results/finetune_improve/robust_cell_*.json` holds
eighteen sign-flip, label-flip and Gaussian attack cells on AG-News and DBpedia
which show how far. On DBpedia seed 42 a single sign-flipping client holding 26.8
per cent of the weight drives the plain merge from 0.6932 to 0.0662. Those cells
were produced by the superseded leave-one-out selection that the plan dropped, so
they cannot be quoted, but they show that one sentence of the limitations section
could carry a measured number for a few hours of compute.

**G9. The paper declines to answer the obvious alternative, and the repo has the
answer.** Section 5.8 offers calibrated noise on the returned labels as the
mechanism for high-volume deployments, says it "composes with the protocol without
modification", and states that we do not evaluate it. We did.
`results/extraction_defence/results.csv` shows the mechanism costs the task at every
budget that slows the attack. On AG-News the task accuracy falls from 0.649 at
eps equal to infinity to 0.620 at eps=4, 0.494 at eps=2 and 0.372 at eps=1, while
the copy still reaches fidelity 0.954 at 100,000 queries at eps=4. On Banking77 the
task accuracy falls from 0.206 to 0.092 at eps=4. Presenting the mechanism as
available without stating its price is the kind of thing a reviewer treats as
selective reporting once they find the record.

**G10. Membership inference is dismissed in one sentence and measured in the
repo.** `results/mia_vit_cifar100/results.csv` holds an external LiRA and a fellow
threshold attack on the released surface at AUC 0.6348, 0.6064 and 0.6299 across
three seeds. The paper's argument that the surface does not exist is correct, and
one sentence citing the measurement is stronger than one sentence asserting it.

**G11. The argmax correctness claim rests on five runs.** Section 5.4 says the
encrypted argmax "returns the same index as the plaintext argmax in every case
tested". `results/fhe_serve/argmax_tournament.csv` holds five rows, one per label
space, at N=10 and log N=15, on synthetic inputs. A CKKS reviewer will point out
immediately that the approximate sign function fails on near-ties and that five
synthetic runs are unlikely to have produced one. The claim needs either a failure
rate over many draws or a much narrower wording.

**G12. Nothing runs the protocol end to end.** The accuracies come out of PyTorch
and the costs come out of Lattigo, and no experiment connects them. The paper's
statement that the cryptography costs no accuracy rests on the reciprocal's relative
error of 1.9 times 10^-8 from `results/fhe_serve/protocol_cost.json` and on the
argmax exactness above, not on a single query answered through the real merge, the
real argmax and the real key switch. This is the most quotable weakness in the
submission, because it is the one a reviewer can state in a single sentence.

**G13. Every measurement is at threshold equal to the federation size.** The paper
says so in the limitations, and the query allowance of Section 5.6 scales with the
largest coalition that cannot decrypt, so the entire allowance analysis is
conditional on a setting the paper never varies.

**G14. No dispersion is reported anywhere.** Three seeds, five tasks, and not one
interval. The shared head on AG-News runs 0.809, 0.736 and 0.402 across seeds and on
TREC runs 0.594, 0.540 and 0.686, both from
`results/personal_adapter/stratified/results.csv`. A reviewer will not accept a
three-seed mean over that spread without a range, and printing the range costs no
compute and almost no space.

**G15. The peer partitions are cherry-picked in one direction.** FedAUXfdp reports
four alpha values and the paper adopts two, leaving out alpha=0.01, which is where
FedAUXfdp is strongest at 75.2 per `comparators/REPORTED_RESULTS.md`. DENSE reports
three and the paper adopts two. Neither omission changes the conclusion, and both
are the kind of thing a hostile reviewer names.

**G16. The setting the paper is sold on is never instantiated.** The motivation is a
regulated or proprietary model that cannot be handed to participants. Every
experiment is a public benchmark cut by a Dirichlet draw. Nothing in the evaluation
distinguishes this design from any other federated fine-tuning paper's setup.

---

## 4. What to run next

Ranked by what each buys against what it costs. Timings use the recorded wall
clocks. A single-pass text cell at N=10 costs 17 to 26 minutes on a T4 across the
`results/finetune_improve/cell_*.json` files, N=20 costs 35 to 43 minutes and N=50
costs 93 to 97 minutes. `jobs/personal_adapter_test.py` runs two passes, one at rank
8 and one at rank 0, so a text cell costs about twice those figures. `CLAUDE.md`
records 22 minutes per CIFAR-10 cell and 43 minutes per CIFAR-100 cell for
`jobs/personal_adapter_vision.py`.

### R1. Put a record under Table III. Highest priority.

Run `jobs/personal_adapter_test.py` on `dbpedia_14` with `PA_ALPHA` in
{0.05, 0.3, 1.0} at three seeds, and with `PA_K` in {100, 400} at seeds 43 and 44
plus the K=200 pair that is missing. That is nine cells for the skew row at about
45 minutes each and six for the local-steps row, so **about eleven hours of T4 time**
in four chunks of three hours. Commit the printed CSV block, which is what
`results/personal_adapter/nsweep.csv` already is.

This is the only place where the paper prints a number that traces to nothing. It
also lets the Table III caption drop its single-seed admission for the steps row and
lets Section 5.2 keep its crossover argument, which is the sharpest reading in the
whole experiments section and currently rests on unrecorded numbers. Without it, the
honest alternative is to delete the two rows, which would cost the paper the claim
that the crossover is about coverage and not about label-space size.

### R2. Measure CIFAR-10 and CIFAR-100 on their whole test sets.

Raise `max_test` in `jobs/vision_matched.py:62` from 2,000 to 10,000 and rerun the
evaluation only. Training is unchanged, so the cost is inference over four
partitions times three seeds for CIFAR-10 plus three seeds for CIFAR-100, which is
**under two hours** and possibly under one. Keep `max_train` where it is and
disclose it in the caption, which is the cheap half of item T21.

This lets Table IV's negative charge of 0.005 at N=20 and alpha=0.04 survive
contact with a reviewer who computes the standard error of a 2,000-sample estimate.
Today that paragraph argues at length from a difference the test set cannot resolve.
It also fixes Table II's CIFAR-100 row, which currently rests on twenty test images
per class.

### R3. Answer one real query end to end under encryption.

Load one trained head from `results/personal_adapter/artifacts/`, encrypt it under
the collective public key, take 200 real test feature vectors, and run them through
the real coverage-weighted merge, the real tournament argmax in
`fhe/serve_tournament.go` and the real key switch. Report the agreement with the
PyTorch argmax and the wall clock. The Go code already does the argmax and the key
switch, so the work is loading a real head and real features rather than synthetic
ones. CPU only, so it needs no GPU slot and runs beside a training job, and the
compute is **under an hour**. The engineering is a day.

This is the highest-value single item in the list. It retires G11 and G12 together,
it turns "the encrypted argmax is exact" from five synthetic runs into a measured
agreement rate on real logits including near-ties, and it lets the paper write the
sentence "the protocol was executed end to end", which today it cannot. It adds no
table, because the result is two numbers in the correctness paragraph.

### R4. Fold the twelve CIFAR-10 cells into Table V. No compute.

Already in `docs/plan/paper-rewrite.md`. Selection goes from 13/15 in one table and
11/12 in a separate paragraph to 24/27 in one place. It also removes a paragraph
from Section 5.2, which helps the page count.

### R5. Report the label-noise defence. No compute.

`results/extraction_defence/results.csv` is landed and covers both label and
probability access at six budgets and three tasks. Two sentences replace the current
"we do not evaluate it" in Section 5.8 and answer the reviewer's obvious question
with our own measurement, at the cost of conceding that the fallback is expensive.
Conceding it is better than being caught not having looked.

### R6. Pooled reference on CIFAR-100.

`jobs/centralised_ceiling.py` is text only, so this needs a small vision arm that
trains the same rank-8 ViT adapter on the pooled 10,000 images for 2,000 steps at
three seeds. At the recorded 43 minutes per CIFAR-100 cell the pooled runs are
shorter than a federated cell, so **about two hours**. It removes the dash in Table
II, which item T21 already flags and which reviewers ask about because a dash in a
table reads as an experiment that failed.

### R7. Extend the client-count sweep to 100, on a second task.

`jobs/personal_adapter_test.py` already checkpoints per client under
`results/personal_adapter/ckpt/`, which is what makes this reachable. At the
recorded 95 minutes per pass at N=50, N=100 is about three hours per pass, so a
three-seed cell is about eighteen hours split across chunks. It costs no table space
if it extends the existing row.

This buys the answer to the most predictable question a federated learning reviewer
asks, and the coverage argument predicts the answer, so the risk of an unhelpful
result is low.

### R8. Rank and freeze ablation under the current pipeline.

Run `jobs/personal_adapter_test.py` on `banking77` at ranks 16 and 32, three seeds
each, which is six cells at about 45 minutes, so **about five hours**. The pre-pivot
record in `results/finetune_improve/` already indicates rank 8 wins, so this
converts an unjustified hyperparameter into three numbers in the setup paragraph. It
adds no table.

### R9. Repeat the extraction budget on real features.

Change the query and evaluation distributions in `jobs/extraction_budget.py` from
`rng.normal` to a sample of the cached test features. The attack is a linear fit, so
this is **CPU only and under an hour**. It closes U11 before a reviewer opens it, and
it either confirms the allowance or changes it, and either outcome is better than the
current position where the paper's most operational recommendation rests on a
distribution it does not name.

### R10. A feature-skew partition.

Split CIFAR-10 by a corruption or a rotation applied per client rather than by
label, and rerun the two arrangements at three seeds. About two hours of compute at
22 minutes per cell, plus half a day to write the partitioner. This is the one
experiment on the list that may produce a bad result, which is the point. It gives
the paper a limitation it states itself instead of one a reviewer finds, and three
numbers in Section 5.8 carry it without a table.

---

## 5. What not to run

**More seeds on Table II.** Three seeds already reproduce every printed cell, and
the conclusion that matters, which arrangement wins at which label-space size, holds
in sign on fourteen of fifteen cells in
`results/personal_adapter/stratified/results.csv` and
`results/personal_adapter_vision/stratified/results.csv`. More seeds would shrink an
interval the paper does not print. Print the range instead, which costs nothing.

**More points in the cryptographic cost grid.**
`results/fhe_serve/cost_grid.json` already covers three ring degrees times three
client counts, and the paper's own analysis shows the argmax is more than 99 per cent
of a query at 31.2 s out of 31.5 s. Adding ring degree 2^17 or N=50 moves a term
that is already two orders of magnitude below the one that decides the answer.

**A GPU implementation of the argmax.** The paper deliberately stops at a
primitive ratio and gives a good reason, which is that reported bootstrapping times
on GPUs span more than two orders of magnitude. Building a CUDA CKKS argmax is
months of work and would change one paragraph.

**More membership inference.** There is no released model and the only interface
returns a label. `results/mia_vit_cifar100/results.csv` already shows AUC between
0.6064 and 0.6348 against the released surface, which is the surface this protocol
does not expose. Running more of it answers a question the threat model has already
answered.

**More budgets for the boundary-search extraction variant.** It loses in 13 of the
15 cells already measured in `results/extraction_budget/results.csv` and wins twice
by 0.003. The reason is structural, since a bisection chain returns nearly identical
points and a linear fit gains little from them. More budgets will not reverse a
structural result.

**Differential privacy on the local adapter.** The contribution is protected
cryptographically and the adapter never leaves the client, so DP-SGD would cost
accuracy and protect a surface that does not exist. The only DP question this paper
faces is on the answers, and `results/extraction_defence/results.csv` has already
answered it.

**Autoregressive perplexity.** `docs/plan/paper-rewrite.md` already records the
blocker, which is that GPT-2 ties the vocabulary projection to the input embedding,
so untying it to federate costs perplexity on its own and confounds the federation
effect. The scope paragraph already says the paper evaluates classification only. A
weak perplexity number is worse than an honest scope statement.

**Re-running any vendor comparator.** `CLAUDE.md` records that many vendored
comparators have stale APIs, and the paper's own argument is that absolute accuracy
across papers measures the backbone. Running DENSE on our backbone produces a number
its authors never chose and settles nothing that
`comparators/REPORTED_RESULTS.md` does not already settle.

**A learning-rate or batch-size sweep.** Nothing in the paper's argument depends on
the local optimiser being tuned, and every arrangement in every table shares the
same one, so the comparison is internally matched. Disclose the values and move on.
