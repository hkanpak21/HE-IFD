A1 — Pivot methodology to encrypted CFD
What: replace block-wise HE-IFD inmethodology.texwith PRD §4 (encrypted CFD on probe); kills the 460 GB upload number
Resolves: [AE-2], [R1-W3], [R3-2], [R3-4] (partial)
By: W13–16 (2026-08-29)

A2 — TenSEAL prototype + primitive validation
What: validate β-aggregation, λ variance, one encrypted SGD step ont4_ai; reports depth budget + throughput
Resolves: [AE-3] (partial), [R2-Q3]
By: W4 (2026-06-06)

A3 — Real-HE end-to-end single-cell run
What: portlegacy/toy_ifd_real_he.pyto CFD on MNIST α=0.3 N=10 LeNet-5; report wall-clock + rotations + memory + convergence; TenSEAL first, Lattigo only if depth fails
Resolves: [AE-3], [R2-Q2]
By: W8 (2026-07-04)

A4 — Headline grid + N-ablation
What: 5 datasets (MNIST / FMNIST / SVHN / CIFAR-10 / CIFAR-100) × 3 α × 4 variants × 3 seeds × N=10 = 180 cells (matches Co-Boosting); + 48-cell N-ablation at N ∈ {5, 10, 20, 50} on CIFAR-10 α=0.1 (mirrors Co-Boosting Table 6); three measurement columns per cell (Acc_plain_ReLU / Acc_plain_poly / Acc_cipher)
Resolves: [AE-1], [R1-W1], [R1-W2], [R1-W5]
By: W10 (2026-07-18)

A5 — γ-variant DP-DDPM
What: per-client pixel-space DP-DDPM (ε_G=10) on subset of grid; the no-public-data extension; long-pole compute item
Resolves: strengthens [R1-W4], [R2-Q5]
By: W14 (2026-08-15)

A6 — Add FedAvg / FedMD / FedDF baseline curves
What: numeric comparisons in same grid as A4
Resolves: [R2-Q1], [R3-5], [AE-7]
By: W10 (2026-07-18; piggybacks on A4)

A7 — Post-release MIA on decrypted student
What: LiRA + loss-threshold across the grid; population MIA single-cell ablation
Resolves: [AE-5], [R2-Q5], [R1-W4]
By: W11 (2026-07-25)

A8 — Formal privacy framing: binding invariant + SQ-floor
What: rewrite §threat-model + §discussion to import PRD §2; single paragraph answers [R2-Q6] via binding invariant + CT×PT observation
Resolves: [R1-W4], [R2-Q6], [AE-5]
By: W16 (2026-08-29)

A9 — Malicious-clients out-of-scope paragraph
What: one §future-work paragraph naming encrypted-feature poisoning + robust aggregation under HE; cites Viand SoK 2023 + vCKKS lines
Resolves: [AE-4], [R2-Q4]
By: W16 (2026-08-29)

A10 — Rewrite §I-A challenges + abstract incentive paragraph
What: replace 3 legacy challenges with 4 post-pivot ones (depth budget / β-λ without division / binding invariant / SQ-floor); abstract gets concrete numbers from May-5 (MNIST α=0.3: 0.965 vs 0.81)
Resolves: [AE-6], [R3-1] (advisor: "Add more explanation"), [R3-2] (advisor: "Write more directly")
By: W18 (2026-09-12)

A11 — Structural fixes: motivation move + new figures + future-directions move
What: §II-C → §I-B; new protocol-overview SVG + threat-model SVG (Client #C6A87D / Server #8B9EA8); §V-F → §VI
Resolves: [R3-3], [R3-4], [R3-6]
By: W16 (2026-08-29)

A12 — Pruning ablation [OPEN]
What: scope reading with Kerem — block-wise residue / CFD compression knob / future work mention; then execute if scoped
Resolves: [ADV-Pruning]
By: scoping W1 (2026-05-16); execution W17 (2026-09-05) only if in scope