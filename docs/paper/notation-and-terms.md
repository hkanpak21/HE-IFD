# Notation & terminology contract (the paper obeys this)

Two rules: **(1)** every symbol below is defined at first use and collected in a notation table in the
Preliminaries; **(2)** the "reader-friendly name" column is what appears in prose — the "banned
development artifact" column never appears in the paper.

## Notation table (goes in Preliminaries)

| Symbol | Meaning |
|---|---|
| `N` | number of participating clients (parties) |
| `D_j` | client *j*'s local labelled dataset; `n_j = |D_j|` its size |
| `C` | number of classes |
| `α` | Dirichlet concentration controlling label heterogeneity (smaller = more heterogeneous) |
| `φ` | frozen feature extractor (pretrained backbone) — never trained, never encrypted |
| `h_ψ` | the small trainable classifier head, parameters `ψ` — the only trained/encrypted object |
| `f_θ = h_ψ ∘ φ` | the student model; `θ` denotes its trainable parameters |
| `θ₀` | the **shared loss basin**: a common initialization produced in Phase 0 |
| `t_j` | client *j*'s local teacher |
| `K` | number of bounded local distillation steps (trajectory length) |
| `τ` | distillation temperature |
| `Δ_j = θ_j^{(K)} − θ₀` | client *j*'s cumulative parameter displacement after its K-step trajectory |
| `w_j = n_j / Σ_i n_i` | client *j*'s sample weight in aggregation |
| `θ⋆ = θ₀ + Σ_j w_j Δ_j` | the aggregated global model (the only quantity computed under encryption) |
| `(ε, δ)` | differential-privacy budget on the Phase-0 prototypes (averaging variant) |
| `K_pc` | samples per class per client averaged into a prototype; sensitivity ∝ `clip / K_pc` |
| `σ` | calibrated Gaussian noise scale for the DP prototypes |

## Reader-friendly name contract (prose) — kills development artifacts

| Reader-friendly name (use this) | What it is | Banned artifact (never write) |
|---|---|---|
| **shared loss basin** / "the shared initialization θ₀" | the common, aligned (not necessarily strong) init | "warmed init", "theta0_acc" raw |
| **coverage of locally-unseen classes** | a client's accuracy on classes it held zero local examples of | `M4`, `M4_ood_acc` |
| **global-vs-local gain on a client's own data** | the global model's accuracy minus the client's own local model, on that client's data (often negative — owned, see incentive discussion) | `M3`, `M3_mean_gap` |
| **centralized reference** | model trained on the pooled data — an upper-bound, not a competitor | `oracle` |
| **average / best local teacher** | mean (resp. max) accuracy of the per-client teachers | `mean_teacher`, `best_teacher` |
| **no-alignment baseline** | distillation with no shared basin (random init) | `no_phase0` |
| **raw-prototype alignment** | basin built from raw per-class feature prototypes over P2P channels | `raw_union_K20` |
| **DP-prototype alignment** | basin from differentially-private averaged prototypes | `dp_avg_eps2_K20` |
| **client-synthetic alignment** | basin from per-client synthetic samples | `synthetic_K20` |
| **no-probe basin** | basin formed with no labelled public data at all | `noprobe` |
| **global model test accuracy** | top-line accuracy of θ⋆ | `acc` |
| **distillation lift** | (global model accuracy − shared-basin accuracy) — what distillation adds on top of the basin | `acc − θ₀` raw |
| **client's local training samples** `D_j` / `n_j` | — | `train_samples_local_client` |

## Phase names (the method)

- **Phase 0 — shared loss basin construction:** over peer-to-peer secure channels (the server is
  excluded); clients exchange per-class prototypes (raw, DP, or synthetic) to agree on θ₀.
- **Local bounded-trajectory distillation:** each client distils its teacher into the student for K
  bounded steps from θ₀, yielding the displacement `Δ_j`.
- **Encrypted linear aggregation:** the server's only crypto operation — `θ⋆ = θ₀ + Σ_j w_j Δ_j`
  (plaintext-scalar × ciphertext and ciphertext + ciphertext only; multiplicative depth ≈ 1), under a
  joint CKKS key with threshold decryption (no single party decrypts).
