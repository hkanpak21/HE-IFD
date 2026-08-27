# Privacy analysis for the technical report, and what else the paper can shed

Written 2026-08-27, answering the request to plan a comprehensive privacy
analysis for the technical report, ground the membership work in prior work,
separate the server-to-client channel from the client-to-client channel, and
find what else the paper can delegate. Literature sweep of 2026-08-27 is folded
in. The plan this serves is `docs/notes/plan-submission-2026-08-23.md`, work
item W12, which this note expands.

## Verdict

The membership work already in the repo measures a threat model the serve-only
pivot deleted, so none of it can be cited as it stands. Cases `heifd_021_mia`,
its 028 extension, and `heifd_mia_freeze_a` all attack a plaintext released head
$\thstar$ and a Phase-0 prototype channel. The current method releases no model
and builds no prototype channel, so both objects are gone, and every attack in
`mia/attacks.py` consumes a per-example loss or confidence that the label-only
interface never emits. The correct analysis has one empirical target, the
client-to-client channel, because the server-to-client channel is closed by
proof already in `security.tex` and needs no experiment. Client-to-client
inference under this interface is not blocked by the label restriction. It is
made expensive by it. A multiclass softmax head over public features is
reconstructible from labels alone to above 99.9 per cent agreement in $100C(d+1)$
queries (Tramer et al., USENIX Security 2016, Section 6.2, empirical), after which
the white-box membership attacks apply to the reconstruction. The
report therefore measures how much a coalition of $\tc-1$ clients learns about an
honest client at the real budget $(\tc-1)Q$, which is the quantity $\delta$ that
Theorem 2 leaves abstract and that `sec:exp-leak` promises to measure.

Superseded in part on 2026-08-27, and the supersession is an improvement.
Proposition 2 of `security.tex` now shows $\delta(Q_{\mathrm{tot}})$ is capped at
every budget by $\delta_{\mathrm{wb}}$, the advantage of an adversary holding the
head. Theorem 2 is therefore no longer vacuous without the measurement, and the
measurement's job is to put a number on the ceiling rather than to rescue the
theorem. It also becomes a white-box attack on the true head instead of an
extract-then-attack pipeline.

## 1. The existing membership suite measures a deleted threat model

`mia/target.py` composes `src.teacher`, `src.phase0`, `src.distill` and
`src.aggregate`, the retired distillation pipeline. It trains a released global
model $\thstar$ on a data subset, then attacks it. The three surfaces in
`mia/surfaces.py` are the released model in the clear (external and fellow) and
the Phase-0 prototype release (prototype). The four attacks in `mia/attacks.py`
are the Yeom loss threshold, LiRA, GLiRA, and prototype distance. Every one of
them reads a real-valued signal off a model the adversary holds, a loss, a
confidence, or a distance to a released prototype.

The current method exposes none of that. No party holds $\thstar$ in plaintext
at any point. There is no Phase-0 prototype release. The only adversary-facing
object is the served head under a label-only oracle, and a client that queries
it receives $\arg\max_c(\thstar\,\phi(x))_c$ and nothing else. Consequences:

- The prototype surface has no referent. Delete it.
- The external and fellow surfaces as written assume plaintext confidences.
  Under the real interface the adversary has argmax labels, so LiRA, GLiRA and
  the Yeom threshold cannot run directly. They run only against a copy the
  adversary reconstructs first, which is Strategy B below.
- The numbers in `results/heifd_021_mia/README.md` (external LiRA AUC up to
  0.86 on ViT/CIFAR-100, prototype AUC up to 1.0 at raw release) describe the
  leakage of the disclosed-model protocol this construction declines to build.
  They are a correct measurement of the wrong object. They belong in the report
  only as the counterfactual "what disclosure would have leaked", clearly
  labelled, never as this method's leakage.

Epistemic status: this is a reading of `mia/` against `method.tex` and the
serve-only design, not a measurement. It is a claim about what the code targets,
and it is checkable by reading the two files. The rewire is W12 and is unstarted.

## 2. The two channels, and why only one needs an experiment

### 2.1 Server to client is proof-only

Against a semi-honest server the channel is closed by Theorem 1. The server's
view is ciphertexts under the collective key, public sample counts, and
evaluation keys, and the simulator reproduces it from the leakage $\Leak$ under
IND-CPA against $\tc-1$ shares. No membership experiment is possible, because the
server holds no plaintext to score. Proven, `thm:semihonest`.

Against a malicious server the channel is not closed by cryptography alone, and
the request's phrasing "the server cannot attack by any means due to
cryptography" holds only in the semi-honest model. Proposition 1
(`prop:nogate`) is precise about this. A deviating server can present a
ciphertext of its own choosing for decryption, for instance a row of $\thstar$,
and an honest client cannot refuse on the basis of content, because a predicate
that decided differently on $\mathsf{Enc}(m_0)$ and $\mathsf{Enc}(m_1)$ would be
an IND-CPA distinguisher. So input privacy against a malicious server is
recovered only by the added mechanism the report carries, recomputation of the
deterministic serving circuit and a comparison as a string, or a proof of
correct evaluation. The report states the server-to-client guarantee in exactly
these two tiers and does not let the semi-honest claim stand for the malicious
case. Proven for the semi-honest tier (`thm:semihonest`), proven as an
impossibility for the naive malicious repair (`prop:nogate`), and the
recomputation mechanism is a construction whose soundness rests on the circuit
being deterministic, which the traffic-saving key design already guarantees.

### 2.2 Client to client is the empirical work

A coalition of at most $\tc-1$ clients cannot decrypt, so it never holds
$\thstar$. Its entire window into an honest client $h$ is that $\thstar$ depends
on $h$'s head-row displacement through the coverage-weighted merge, and that the
coalition may spend $(\tc-1)Q$ label-only queries on the served head. Theorem 2
(`thm:malicious`) already bounds the coalition's advantage by
$\negl(\lambda)+\delta(Q_{\mathrm{tot}})$ with $Q_{\mathrm{tot}}=(\tc-1)Q$, where
$\delta$ is "the advantage available from $Q_{\mathrm{tot}}$ label queries to the
served model". The theorem does not say $\delta$ is small. Measuring $\delta$ is
the report's job, and it is the single number that decides whether Theorem 2
says anything.

## 3. What client-to-client inference is, as an attack

### 3.1 The channel, stated concretely

The served map is $f(x)=\arg\max_c(W\phi(x)+b)_c$, a fixed linear classifier over
the frozen public feature space $\phi$, with $\Cc$ classes and feature dimension
$d$. The querier computes $\phi$ itself, so it controls the exact vector fed to
the linear map, and it receives one label per query, metered by $Q$. The private
quantity is $W$, because $W$ is the coverage-weighted merge of client
displacements and $h$'s row carries $h$'s training signal. Membership of a record
of $h$ is a question about whether that record moved $h$'s row.

### 3.2 Strategy A, direct label-only membership inference

The published label-only attacks infer membership from the stability of the
predicted label under perturbation of the input. Choquette-Choo et al. (ICML
2021, proven threat, empirical rates) estimate the distance from a point to the
decision boundary by a boundary-search or by label agreement under
augmentations, and read membership off that distance, since trained-on points
sit farther inside their class. Li and Zhang (CCS 2021) give the concurrent
transfer-based form. The query-efficiency objection to a small $Q$ is answered
by OSLO (Peng et al., NeurIPS 2024) and YOQO (Wu et al., ICLR 2024), which mount
label-only membership inference in a single query at TPR several times the prior
art, so a small allowance is not on its own a defence against membership
inference. For a deviating coalition, Chameleon (Chaudhari et al., ICLR 2024,
label-only adaptive poisoning) is the published bridge, because a coalition that
holds training data for a class it shares with $h$ can poison that class before
the one-shot merge and raise the label-only signal.

The structural subtlety, and the reason the label restriction is a cost and not
a wall, is that when the map is linear the boundary distance is closed-form once
$W$ is known, $\lvert w_c^\top\phi(x)\rvert/\lVert w_c\rVert$, so Strategy A
collapses into Strategy B. Empirical, Tramer et al. (USENIX Security 2016,
Section 6.2): a multiclass softmax model is recovered from class labels alone to
above 99.9 per cent agreement in $100C(d+1)$ queries by adaptive retraining. The
label interface hides the confidence, not the hyperplane.

### 3.3 Strategy B, extract then attack

The coalition spends part of its budget reconstructing $W$ from labels, then runs
white-box membership inference on the reconstruction. The reconstruction cost is
already measured in the repo. `results/extraction_budget/results.csv` and
`results/extraction_scale/results.csv` give fidelity against queries and the
$\Cc d$ scaling law, three to five queries per parameter for fidelity 0.90. The
white-box attack on the copy is LiRA (Carlini et al., S&P 2022) or, at low
reference-model cost, RMIA (Zarifzadeh et al., ICML 2024), both of which train
shadow linear heads on the coalition's own feature data, which is cheap. The
published instance of this exact pipeline is Marich (Karmakar and Basu, NeurIPS
2023, empirical), which extracts a distributionally equivalent copy in one to
nine thousand queries and then attains membership accuracy of 0.84 to 0.96 on
the copy. This is what unifies the extraction study and the membership study.
They are one analysis of one channel, the query interface, not two separate
results.

### 3.4 Why $\delta$ is expected small, and what is open

The head is a coverage-weighted average across clients, and each row is itself an
average of the contributing records' displacements through bounded $K$-step
distillation over a frozen backbone. Averaging attenuates the per-record signal
that membership inference needs, and the field's own separation supports this,
attacks that see only a final generalising model identify few members and only at
low false-positive rates (Carlini et al., S&P 2022), the point `related.tex`
already makes. The nearest quantitative support is Tobaben et al. (NeurIPS 2025,
empirical), a fitted power law in which membership vulnerability of a fine-tuned
model falls with examples-per-class. The claim that the cross-client merge
lowers membership leakage on a linear head has no direct citation, so it is open
and the report supports it with the measurement, not with a reference. State it
as open.

One honest caveat for the two-arrangement design. When the served head sits over
a client's own adapter, querying it can leak about the frozen base and about that
client, which is the fine-tuned-model membership setting of TMI (Abascal et al.,
2023, arXiv:2306.01181, venue unconfirmed) and the transfer-learning MIA of the
TIFS 2024 work. The report notes this for the personal-adapter arrangement and
confines the strong near-chance claim to the shared arrangement, where the merge
attenuation applies.

## 4. The measurement to run

The rewire of `mia/`, W12, in one pass.

1. Retarget `mia/target.py` to the current pipeline. The object under attack is
   the served head produced by the frozen backbone, the local adapter, the
   encrypted head displacement, and the coverage-weighted merge. Drop the
   `src.phase0`/`src.distill`/`src.aggregate` composition. The adapter is local
   and never enters the adversary's view.
2. Replace the oracle. The adversary sees $\arg\max$ labels at chosen feature
   vectors, under a per-client allowance. Add a label-only attack module, the
   boundary-distance and single-query attacks of Section 3.2, and the
   extract-then-attack pipeline of Section 3.3 reusing the existing extraction
   code in `fhe/` and `results/extraction_*`.
3. Fix the adversary as the fellow coalition of $\tc-1$ clients at budget
   $(\tc-1)Q$, not an unmetered external querier. The server-to-client surface
   produces no experiment, only the citation to the proof.
4. Keep the plaintext white-box LiRA and RMIA on the reconstructed head as the
   headline. Proposition 2 makes this the ceiling on every budget, so the
   white-box attack on the true head is the measurement and the extraction
   pipeline does not have to be built to obtain a bound.
   Report TPR at 0.1 and 1 percent FPR and AUC, the metric LiRA and RMIA fix.
5. Sweep the budget, so the output is a curve of membership advantage against
   spent queries, which is $\delta$ as a function of $Q_{\mathrm{tot}}$ and is
   what Theorem 2 needs. Overlay the extraction-fidelity curve, so one figure
   shows both halves of the channel.

Compute is AFK on VALAR, resumable per shadow model as the suite already is. New
case slug `heifd_mia_served` under `results/`. Cite `choquettechoo2021labelonly`,
already in `refs.bib` and cited nowhere.

## 5. Grounding, the citations the analysis stands on

Essential and load-bearing:

- Tramer et al., USENIX Security 2016, Section 6.2. Label-only extraction of a
  multiclass softmax model at $100C(d+1)$ queries. The reason the label interface
  is a cost, not a guarantee. Already cited by the paper, and verified against the
  USENIX proceedings on 2026-08-27 as supporting exactly the sentence
  `experiments.tex` attributes to it. Lowd and Meek, KDD 2005, is *not* the right
  citation here and was withdrawn, because their result is for the binary case.
- Choquette-Choo et al., ICML 2021, and Li and Zhang, CCS 2021. The label-only
  membership threat class.
- OSLO, NeurIPS 2024, or YOQO, ICLR 2024. Single-query label-only membership
  inference, which answers the small-$Q$ objection.
- LiRA, S&P 2022, and RMIA, ICML 2024. The white-box attack on the reconstructed
  head and the low-FPR metric.
- Marich, NeurIPS 2023. The published extract-then-infer pipeline.
- Nasr et al., S&P 2019, and Melis et al., S&P 2019. The federated-learning
  channels this construction denies by never sending an update.
- Ngo et al., ECML PKDD 2024, secure aggregation is not private against
  membership inference. Preempts the reviewer who equates this design with
  secure aggregation, by letting the report state the sharper claim that no
  plaintext aggregate is formed at all.
- Ghazi et al., NeurIPS 2021, label differential privacy. The reference point
  for the noise-on-labels defence and its utility cost.
- PRADA, EuroS&P 2019. The extraction-detection lineage the query allowance sits
  in.

Two structural gaps, stated as the report's own claims and not as received
results. No prior work runs the full pipeline against a never-released federated
head behind an encrypted serving interface, so the composition of extraction and
membership inference here is the report's contribution and carries no single
citation. No prior work shows a cross-client merge lowers membership leakage on a
linear head, so that claim is open and rests on the measurement.

Which of these enter the submission is a citation-budget question, Section 7.

## 6. What else the paper can delegate to the report

The membership work is one of several fragments the paper carries that have a
full record and deserve a full treatment the ten pages cannot hold. Grouped so
the report gains chapters, not orphans.

**A unified empirical-privacy chapter.** Membership inference (Section 4 here),
the extraction cost table `results/extraction_budget`, the extraction scaling law
`results/extraction_scale`, the noise-on-labels defence
`results/extraction_defence`, and the comparison with model disclosure
`sec:exp-release`. These five answer one question end to end, what an adversary
with a query budget learns, and today they are scattered across the paper, the
report-only blocks, and the deleted membership suite. The noise defence alone is
thirty runs over three tasks and five budgets, and it is the argument that the
query allowance is the right control rather than label noise, since label noise
at $\varepsilon=1$ takes AG-News from 0.649 to 0.310 accuracy
(`results/extraction_defence/results.csv`). The paper keeps one corrected clause.
The report gives the measurement. This is the natural home for the request's
"what else like MIA".

**The malicious-server and integrity material.** Proposition 1, recomputation of
the deterministic circuit, and verifiable homomorphic evaluation. Already routed
to the report by W6, and the sentence "we implement neither" is deleted from the
paper by the PI's instruction of 2026-08-21. The report states recomputation and
spot-checking as a design the traffic-saving key choice already permits.

**The selection machinery.** The global-prior estimator derivation, the
inadequacy of the held-out vote, and the selection-accuracy table, which the PI
asked removed from the paper (note of 2026-08-21, item 8). Folding the twelve
CIFAR-10 cells in turns the selection result from 13/15 to 24/27 at no compute
cost, and the table is report-only now, so this is free report work.

**The full cost and communication material.** The cost grid over ring degree and
client count, the communication model with its scenarios in
`docs/notes/archive/communication-model-2026-08-20.md`, and the CUDA
microbenchmarks once attributed to `yang2024phantom` or dropped. Routed by W11.

## 7. How the paper improves, within the constraints

The submission is under the subsequence rule and the least-change discipline, so
improvements are surgical and every one of them is a deletion, a pointer, or the
single membership paragraph W12 already budgets.

1. The membership paragraph and pointer. The paper today argues privacy only
   through extraction cost. It states what a copy costs and never states what the
   copy leaks about a record. A reviewer from the shared TDSC pool will ask
   exactly that. The one paragraph states that the coalition's membership
   advantage is bounded by the allowance and measured near-chance at the real
   budget on the shared arrangement, and points at the report. This is the
   largest single strengthening available and it costs one paragraph.

2. Anchor Theorem 2's $\delta$. The submission carries $\delta(Q_{\mathrm{tot}})$
   as an abstract quantity, which a reviewer can call vacuous. One clause tying
   $\delta$ to the report's measurement makes the bound non-empty. This is a
   retarget of a cross-reference, which the subsequence rule permits.

3. One grounding citation in the submission, the label-only threat class, so the
   membership paragraph is not an unsupported assertion. `choquettechoo2021labelonly`
   is already in `refs.bib`. The rest of the citations in Section 5 ride in the
   report, which carries all 110 keys, so the submission's budget of about 55 is
   untouched.

4. The precise server framing. The submission must not let "the server learns
   nothing" stand unqualified, because Proposition 1 shows the malicious case
   needs recomputation. The security section already tiers this correctly. The
   check is that the abstract and introduction do not overreach past what
   `security.tex` proves.

Every one of these is proposed text, not applied. Paper writing is HITL, and the
membership paragraph in particular is a new paragraph, which `check_subseq.py`
will flag and which is the user's decision to accept.

## 8. Risks and what is open

- The rewire and the served-head membership sweep are real AFK compute, not a
  writing task. Budget a VALAR session for W12 before the report is complete.
- The near-chance membership claim is a prediction, not yet a result. If the
  measured $\delta$ is not small at $(\tc-1)Q$, the operational story stands, the
  allowance still bounds it, but the paragraph in Section 7 item 1 changes from
  "near chance" to a bound. Do not write the paragraph before the measurement.
- The malicious-server tier depends on the circuit being deterministic. This is
  true under the current bootstrapping-key design and would fail if the design
  moved to collective refresh, so the report states the dependency.
- Two literature items are unverified, the TMI venue and the exact arXiv numbers
  for Nasr 2019 and Jagielski 2020. Verify before they enter `refs.bib`.
