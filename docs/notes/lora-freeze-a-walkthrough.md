# Walkthrough — LoRA & Freeze-A (FFA-LoRA) in HE-IFD

A running learning doc. Checkboxes get ticked once you've *demonstrated* understanding
(restated it / answered a quiz), not just been told. High-level (why) **and** low-level
(mechanics, edge cases) both count.

## Learning arc

### Part 1 — The problem
- [ ] 1.1 What "fine-tuning" normally costs (full FT updates *all* backbone weights)
- [ ] 1.2 Why that cost is fatal in *our* setting (federated + HE: communication, ciphertext budget, depth-1 limit)
- [ ] 1.3 The branches we could have taken (head-only, last-N layers, full FT, LoRA) and their trade-offs

### Part 2 — LoRA, the solution
- [ ] 2.1 Core idea: freeze W, learn a low-rank update ΔW = B·A
- [ ] 2.2 *Why* low rank is enough (intrinsic dimension of fine-tuning)
- [ ] 2.3 Mechanics: rank r, alpha scaling, target_modules, B zero-init (step-0 == base model)
- [ ] 2.4 The parameter / communication win

### Part 3 — Freeze-A (FFA-LoRA), our specific twist
- [ ] 3.1 What freeze-A *is*: A frozen at a shared public seed-keyed random init; only B (+head) trains
- [ ] 3.2 *Why* we need it: aggregation is task arithmetic (linear combine of deltas); B·A is **bilinear** → breaks linearity → seed collapses
- [ ] 3.3 How freezing A restores linearity → valid depth-1 HE combine
- [ ] 3.4 Edge cases / decisions: A identical across clients, B zero-init, head trained, FFA-LoRA is *prior work* (cite, don't claim)

### Part 4 — Broader context
- [ ] 4.1 HE has no programmability → server can only do a depth-1 linear combine → learning must be client-side
- [ ] 4.2 How freeze-A LoRA is what makes the whole one-shot HE-FL pipeline legal
- [ ] 4.3 Impact: the "first one-shot federated learning under multiparty HE" claim, tiny uploads, threat-model knock-ons

## Covered
(entries appended as we go)

## Open questions
(yours — surfaced every session)
