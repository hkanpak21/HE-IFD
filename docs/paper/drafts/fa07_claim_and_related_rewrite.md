# fa07 draft — claim + related-work rewrite (for HITL review, not yet in .tex)

Everything below is PROPOSED text/structure grounded in the fa-series results
and the 2026-06-10 field scan. Numbers marked ⏳ await fa02 (MIA) / fa05
(matched comparators).

## 1. Contributions (replaces the current four bullets)

1. **The first one-shot federated learning protocol under (multiparty)
   homomorphic encryption.** One upload and one download per client; the
   server's only operation is a multiplicative-depth-one linear combination
   under multiparty CKKS with threshold decryption. All prior HE federated
   learning is multi-round (POSEIDON; BatchCrypt/FedML-HE/FedSHE; SHE-LoRA,
   FedShield-LLM for adapters), and all prior one-shot federated learning is
   plaintext or differentially private.
2. **A co-design that makes one-shot encryption cheap.** Freezing the LoRA
   down-projection (following FFA-LoRA) makes the encrypted aggregate *exact*
   task arithmetic on the weight updates — no bilinear cross-terms under
   encryption, no per-round re-encryption — so the entire cryptographic cost
   is 19 ciphertexts (9.5 MiB) per client, once. Measured end-to-end in
   Lattigo at relative L2 ~1e-9.
3. **Encrypted multi-candidate release with client-vote selection.** The
   server emits several depth-one candidate aggregates (λ-scaled, Fisher- and
   coverage-weighted via numerator/denominator decryption, leave-one-out);
   clients jointly decrypt all candidates and select by a sample-weighted vote
   on local holdouts. The vote picks the test-best candidate in 34/39
   experiment cells, lifts the released model by +15 to +38 points over the
   plain average under severe heterogeneity, and yields a measured
   Byzantine-lite defense (the vote excluded a poisoning client in ⏳/18
   attack cells, recovering oracle accuracy). No precedent in MHE-FL.
4. **Privacy by cryptography alone, with the release surface measured.**
   Contributions are never exposed (simulation argument, Prop. 1); the only
   plaintext object is the released model, whose residual leakage we measure
   with threshold and LiRA attacks under both an external and a
   fellow-client adversary (⏳ fa02 numbers).

## 2. The claim sentence (abstract + intro)

> "We present, to our knowledge, the first one-shot federated learning
> protocol whose contributions are protected by homomorphic encryption: a
> single round, a single encrypted linear aggregation at multiplicative depth
> one, and a threshold decryption — made possible by fine-tuning frozen
> pretrained backbones with frozen-projection low-rank adapters, for which
> the linear aggregate is exact task arithmetic."

Never claim: "first one-shot federated fine-tuning" (arXiv:2412.04650),
"first federated LoRA under HE" (SHE-LoRA, FedShield-LLM), or freeze-A as
ours (FFA-LoRA, ICLR 2024).

## 3. Related work — two NEW paragraphs + one rewrite

### 3a. Federated fine-tuning with adapters (insert after the HE-aggregation paragraph)

Key content: parameter-efficient federated fine-tuning emerged with FedIT
(arXiv:2305.05644); naive per-factor averaging of LoRA is biased because
Σ(BᵢAᵢ) ≠ (ΣBᵢ)(ΣAᵢ) — formalized as "aggregation noise" by FLoRA
(arXiv:2409.05976, NeurIPS 2024), addressed by full-product averaging + SVD
redistribution (FlexLoRA, arXiv:2402.11505), stacking (FLoRA), rank
self-pruning (HetLoRA, arXiv:2401.06432), server-side correction (LoRA-FAIR,
arXiv:2411.14961), selective A-sharing (FedSA-LoRA, arXiv:2410.01463), and —
the fix we adopt — freezing the down-projection so only B trains: FFA-LoRA
(arXiv:2403.12313, ICLR 2024), motivated there by DP-noise linearity in
multi-round FL. **Our point of departure**: under encryption the bilinearity
is not merely a bias but a cost cliff (resolving it server-side needs
ciphertext×ciphertext products); freeze-A makes the one-shot encrypted
aggregate exact at depth one, which none of these multi-round plaintext/DP
works exploit.

### 3b. One-shot fine-tuning ≡ task arithmetic (insert before the one-shot-FL paragraph)

Key content: one round suffices for fine-tuning foundation models
(arXiv:2412.04650, with LoRA dominating full FT in the one-shot regime);
task-arithmetic model merging is formally equivalent to one-shot FedAvg
(arXiv:2411.18607). These establish our learning-side premise; what they do
not provide is any protection of the contributions — both operate in
plaintext. Cite Ilharco task vectors as the origin of the framing.

### 3c. Rewrite of the HE-FL paragraph (existing ¶3)

Add the adapter-era crypto works: SHE-LoRA (arXiv:2505.21051, ICLR 2026)
encrypts a sensitivity-selected subset of LoRA parameters per round;
FedShield-LLM (arXiv:2506.05640) runs FHE over LoRA updates with pruning;
PrivTuner (arXiv:2410.00433) is outsourced (non-federated) FHE LoRA. All
multi-round (or non-federated): per-round encryption cost × R rounds, and the
LoRA aggregation-noise problem persists under their encryption. Contrast
table row: ours = 1 round × 19 ct; theirs = R rounds × (their per-round
object). [⏳ quote their per-round MB verbatim for tab:hecomm.]

### 3d. Semantic-init lineage (ablation paragraph only — the method dropped it)

Dataless classification (Chang et al., AAAI 2008) → DeViSE (NeurIPS 2013) →
BERT-embedding classifier init (arXiv:2203.05676); in FL, label-name
anchoring is multi-round (FedAlign, KDD 2023; FedTSP, CVPR 2026). Our
one-shot variant is reported as a *negative* ablation: the zero-shot floor
does not materialize with mean-pooled encoder label embeddings, and final
accuracy is unchanged or worse (banking77 0.72 vs 0.77 without).

## 4. Experiments section — numbers replacing `% PROVISIONAL`

| spot | old (both-A-B) | new (freeze-A + candidates + vote) |
|---|---|---|
| tab:headline ag_news | 0.53 ± 0.21 | 0.75 ± 0.09 |
| tab:headline trec | 0.52 ± 0.21 | 0.72 ± 0.05 |
| tab:headline dbpedia | 0.79 ± 0.02 | 0.93 ± 0.01 (K200) / 0.94 (K400) |
| tab:headline banking77 | 0.38 ± 0.01 | 0.77 ± 0.02 (gap 0.11, was 0.52) |
| tab:headline cifar100 | 0.53 ± 0.02 (NEGATIVE increment) | ⏳ fa05 s6 |
| tab:robust / tab:traj | both-A-B plain | rebuild from fa01 JSONs (sel column) |
| tab:cost-comm headline | 38 ct / 19 MiB | **19 ct / 9.5 MiB** |
| tab:cost-time | old rates | fhe_freeze_a/README.md table (enc 40 ms, agg 76→717 ms, dec 44→430 ms) |
| LLM row (new) | — | Qwen2.5-0.5B: count-head 0.87–0.88 dbpedia, 26 ct / 13 MiB |
| §Residual Leakage | old-method MIA | ⏳ fa02 |
| λ-subsection promise | dangling | replaced by the multi-candidate subsection (fa08 draft) |

## 5. Threat-model insert (one paragraph, §Threat Model)

> "Every participant obtains the released model θ⋆ in the clear after
> threshold decryption; inference a participant performs on θ⋆ against
> another participant's data is therefore not an attack on the protocol but a
> property of releasing a shared model, and we measure it directly (§MIA,
> fellow-client adversary). The protocol's cryptographic guarantee concerns
> the contributions: the server and any sub-threshold coalition observe only
> ciphertexts (Prop. 1). Differentially private one-shot methods protect a
> different target — the released artifact itself, against all parties
> including participants — at a utility cost; the comparison tables flag
> this difference."

## 6. Terminology sweep checklist

- intro l.16 "one-shot federated distillation" → "one-shot federated learning
  protected cryptographically"
- related l.41 "single distillation displacement" → "single fine-tuning
  displacement"; l.95 same.
- conclusion: aligned with the new claim sentence.
- Title typo "Fine-Tuningß" (SUBMISSION_TODO Tier 3).
