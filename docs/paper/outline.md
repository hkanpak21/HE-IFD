# TNSE paper — storyline and section plan (2026-07-03 flow pass)

Supersedes the distillation-era skeleton. Bar for every paragraph (unchanged):
preempt a reviewer concern · be clear · deliver the result. Written to address the
PI's flow notes; each note maps to a numbered item below.

## The storyline (one causal chain, every section answers one question)

> Organizations build models by **fine-tuning** pretrained backbones on private
> data. When several parties want one jointly adapted model, the artifacts they
> exchange **while training runs** are the dominant leak — training-time attacks
> (gradient inversion, update-level membership inference) are far stronger than
> anything an adversary can do with the released model afterwards. HE-IFD
> **eliminates the training-time surface entirely** instead of perturbing it:
> the exchange is one-shot (one artifact, not hundreds) and that one artifact is
> encrypted (zero plaintext exposure). This is affordable precisely **because**
> the task is fine-tuning: the frozen backbone supplies the shared frame a
> one-shot linear aggregation needs, and freezing the adapter's down-projection
> makes the encrypted aggregate exact at multiplicative depth one. What remains
> exposed is only the released model — the inference-time floor no shared-model
> protocol can remove — and we measure it at or near chance.

Chain: **why secure fine-tuning as a service** → **the threat is training-time**
→ **remove it: one-shot × encryption** → **fine-tuning is what makes that
affordable** → **blind server → multi-candidate vote** → **measure the remaining
inference-time floor** → **positioning: nobody else occupies the intersection**.

## PI notes → changes

1. *"Plan intro and other sections; simpler, flow-following narration."*
   → Introduction rebuilt as the 6-paragraph chain above; shorter sentences;
   every section opens by stating which question of the chain it answers.
2. *"Prior-work comparison: HETAL et al. experimental, others at least
   theoretical."* → HETAL added to the encrypted-schemes comparison
   (tab:hecomm + prose in sec:fhe-cost) with its own reported times/accuracies
   verbatim beside ours; the structural (theoretical) axes comparison covers
   the rest (rounds × what-is-encrypted × depth × parties).
3. *"Simplify; settle on one storyline."* → the chain above; de-duplicate
   repeated arguments (lossy-vs-lossless appears once, in related work;
   basin/frame argument once, in method).
4. *"Explain Table XI in a paragraph; use as related-work motivation."*
   → tab:positioning (Table XI) deleted from experiments; its content becomes
   the closing positioning paragraph of related work (the "empty intersection"
   paragraph, now carrying the table's axes in prose).
5. *"Why secure fine-tuning as a service — motivation must be well built."*
   → Intro P1: fine-tuning is the dominant adaptation workflow; parties cannot
   pool data; the service they need is aggregation of adaptations by a server
   that learns nothing.
6. *"State that our focus is training-time attacks."* → named explicitly in
   intro P2, threat model (sec:threat), and the MIA section opener
   (released model = the inference-time surface, the one we cannot remove).
7. *"Show training-time > inference-time via prior work/experiments."*
   → related-work subsection A with verbatim numbers (DLG/Geiping gradient
   inversion; Nasr passive/active federated white-box MIA vs black-box final
   model; malicious-server harvesting), closed by our own Table X (released
   model at/near chance) as the measured inference-time floor.

## Section skeleton (post-pass)

1. **Abstract** — follows the chain: FTaaS motivation → training-time surface
   → one-shot × HE → fine-tuning co-design → vote → results + measured floor.
2. **Introduction** — P1 why secure fine-tuning as a service; P2 the threat is
   training time (quantitative); P3 remove the surface: one-shot × encryption;
   P4 why affordable: frozen backbone + freeze-A ⇒ exact depth-one; P5 blind
   server ⇒ candidates + client vote; P6 what remains + results; contributions.
3. **Related work** (subsections; was continuous prose)
   - A. *Leakage in federated learning: training time vs inference time* — the
     motivation evidence (PI notes 6–7).
   - B. *Protecting training cryptographically* — SecAgg, encrypted training
     (POSEIDON), encrypted aggregation (BatchCrypt/FedML-HE/FedSHE, SHE-LoRA),
     encrypted transfer learning (HETAL line, Priv-FedTL) — all multi-round,
     single-party, or optimizer-under-encryption.
   - C. *One-shot federated learning* — plaintext line; DP line; DP transfer
     learning as the lossy counterpart of our setting.
   - D. *Federated fine-tuning and task arithmetic* — PEFT aggregation bias,
     FFA-LoRA freeze, task-vector merging: the plaintext ingredients we
     compose under encryption.
   - E. *Positioning* — the former Table XI as one paragraph (PI note 4).
4. **Method** — unchanged structure; threat model names the training-time /
   inference-time split explicitly.
5. **Experiments** — unchanged except: sec:positioning (Table XI) removed,
   its "two informative comparisons" folded into related-work E and
   sec:fhe-cost; HETAL row + paragraph in sec:fhe-cost; sec:mia reframed as
   "the inference-time floor, measured".
6. **Conclusion** — one-paragraph restatement of the chain.
