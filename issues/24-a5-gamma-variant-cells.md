# 24. A5 γ-variant cells (encrypted synthetic probe protocol)

Status: ready-for-agent
Label: AFK
Priority: P4 (downstream of 14, 18, 23)
Action-plan: A5 + A4.1 γ-method-row
PRD-section: §3.2, §4 (γ-specific phase notes)

## Parent

Action plan A5 + A4.1 γ-method-row (lines 257–265).

## What to build

Per (dataset, α, seed) cell in γ-scope (per issue 22's chosen conditional path), run the full γ-variant CFD protocol:

- **Phase 0:** DKG (multiparty CKKS).
- **Phase 1g:** each client encrypts its 500 DP-DDPM synthetic samples (from issue 23) under $\mathsf{pk}$ and uploads. Server pools to form encrypted probe $\langle\mathcal P_{\text{syn}}\rangle$ of total size $|\mathcal P| = 5000$.
- **Phase 1t:** each client computes $T_i(\mathcal P_{\text{syn}})$ on its **encrypted** probe (depth-many ctxt-ctxt multiplications per the γ-variant cost note in PRD §3.2 line 117) and uploads $\langle T_i(\mathcal P_{\text{syn}})\rangle$. **The synthetic probe is never decrypted at any point** (PRD §3.2 critical design point).
- **Phase 2:** β-aggregation + λ variance (PRD §4.2).
- **Phase 2c:** encrypted SGD on $\langle\theta\rangle$ against $\widetilde Y$ on encrypted probe inputs. Linear-accumulator construction per memory `project-linear-accumulator`; per-step depth ≤ 3 still holds for the *student update*, but the *forward pass over encrypted inputs* doubles the per-step depth per PRD §4.3 (post-issue-01 patch).
- **Phase 4:** collective key-switch on $\langle\theta_E\rangle$.
- **Phase 5 (optional):** per-client cheap last-layer fine-tuning per PRD Appendix A Provisional item "Phase 5 personalisation: F2".

**No warm-start** in γ — shared random $\theta_0$ from a deterministic seed (PRD §6.4).

**Compute** is HE-cost-heavier than α (PRD §3.2 line 117). Per-cell wall-clock ~ 2× α-variant.

**Privacy budget composition** per PRD §3.2 line 118: released student leakage bounded by $(\varepsilon_G + \varepsilon_P, \delta_G + \delta_P)$ via post-processing. No $\varepsilon_T$ (teachers non-DP per headline). Record the composed (ε, δ) for each cell in the per-cell JSON.

## Acceptance criteria

- [ ] γ-variant runs on every (dataset, α, seed) in scope.
- [ ] `results/grid/<dataset>_gamma_<alpha>_<seed>.json` per cell, with composed (ε, δ).
- [ ] Synthetic probe never decrypted at any phase (assertion in code).
- [ ] Per-step depth ≤ 6 (3 for student update + 3 for encrypted forward) — bootstrap-free.
- [ ] Per-cell wall-clock ≤ 2× α-variant wall-clock (sanity bound).
- [ ] No login-node execution.

## Blocked by

- Issue 14 (A3 establishes the encrypted-forward depth budget for γ).
- Issue 18 (grid scaffold exists; γ slots into A4.1's 4th method-column).
- Issue 23 (per-client DP-DDPM checkpoints + synthetic samples ready).

## References

- Action plan A5 (lines 317–341), A4.1 γ-method-row (lines 257–265).
- PRD §3.2 (lines 107–119), §4 (lines 131–168), §6.4 (line 206), Appendix A "Provisional" Phase 5 F2.
- Memory: `project-linear-accumulator`.

## Comments

(none yet)
