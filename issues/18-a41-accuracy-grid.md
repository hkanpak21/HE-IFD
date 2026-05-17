# 18. A4.1 accuracy grid execution — THE HEADLINE DELIVERABLE

Status: ready-for-agent
Label: AFK
Priority: P3 (the single critical-path artefact for the resubmission)
Action-plan: A4.1
PRD-section: §7 (experimental grid)

## Parent

Action plan A4.1 (lines 244–279). User's stated priority (2026-05-17): *"show our method does not degrade in accuracy compared to prior work"*.

## What to build

Execute the headline accuracy grid: 5 datasets × 3 α × 3 seeds × 8–14 method-rows on `t4_ai` (sbatch only; never login-node).

**Grid dimensions per action plan A4.1 lines 257–267:**

- **Datasets:** MNIST, FashionMNIST, SVHN, CIFAR-10, CIFAR-100.
- **Dirichlet α:** 0.05, 0.1, 0.3.
- **N:** 10 (headline; N-ablation is a separate sub-table).
- **Seeds:** 3.
- **Method-rows (tier-1 minimum, 8–9 rows):**
  - *Ours:* α-warmstart, α-warmstart-no-ensemble (A4-sanity continuation), γ (conditional on issue 22's profile gate).
  - *No-DP one-shot tier-1:* FedMD, Co-Boosting (issues 06, 07).
  - *DP one-shot tier-1:* FedDiff, FedKT (issues 08, 09) × ε ∈ {1, 10} = 4 rows.
- **Method-rows (tier-1+tier-2, 14–18 rows):** add FedDF, DENSE, FuseFL, FedMD-NFDP, FedDM (issue 10).
- **Total cells:**
  - Tier-1 minimum: 8–9 rows × 45 cells = **360–405 cells**.
  - Tier-1+tier-2 maximum: 14–18 rows × 45 = **630–810 cells**.

**Compute estimate** (action plan A4.1 line 69): 1–2 GPU-h plaintext comparators; 2–4 GPU-h ours-rows at 100-epoch teachers. Tier-1 minimum ≈ 720–1 600 GPU-h. On 16-GPU concurrent (post-QoS-escalation): tier-1 in 2–4 days wall-clock.

**On 1-GPU current QoS, tier-1 alone is 30–67 days.** Hence the hard block on issue 03.

**Per-cell artefacts:**
- `jobs/cfd_v2_<dataset>_<variant>_<alpha>_<seed>.sh` sbatch wrapper.
- `results/grid/<dataset>_<variant>_<alpha>_<seed>.json` with per-cell student accuracy + per-phase wall-clock + bytes (for A4.2 / A4.3 reuse).

**Operator-replacement triple** measured on the ours-rows only: `Acc_plain_ReLU`, `Acc_plain_poly`, `Acc_cipher`. Resolves [R1-W2].

**N-ablation sub-table** (separate from headline): CIFAR-10, α=0.1, N ∈ {5, 10, 20, 50}, 4 variants × 3 seeds = 48 cells (ours only).

**Checkpoint-resume** per action plan §0: every cell writes `state.ckpt` every 30 min; `scontrol requeue $SLURM_JOB_ID` on `SIGUSR1`. 8-hour wallclock cap applies; cells > 8h must auto-requeue per memory `valar`.

**Tweak protocol per PRD §9.5.3:** if compute pressure forces a peripheral adjustment (drop CIFAR-100, drop α=0.1, drop 3rd seed), each tweak → `reports/2026-MM-DD_tweak_<slug>.md` + ledger line per §9.5.6. **Escalation per §9.5.4:** compute overrun > 50 % → halt.

## Acceptance criteria

- [ ] `jobs/cfd_v2_*.sh` sbatch wrappers generated for every cell of the active scope.
- [ ] Cell results in `results/grid/*.json` cover the locked-tier-1 minimum scope.
- [ ] Consolidated accuracy table at `results/grid/A4_1_accuracy_table.csv` (or `.tex`) with per-(dataset, α, seed, method-row) cell.
- [ ] Operator-replacement triple measured on ours-rows.
- [ ] No login-node execution.
- [ ] Any peripheral tweak (per PRD §9.5.2) logged per §9.5.3 + §9.5.6.
- [ ] On compute-overrun > 50 % or A4-sanity gap < 2 pp re-trigger (issue 15): halt + escalate per §9.5.4.

## Blocked by

- Issue 03 (QoS escalation; without `t4_ai` QoS the grid is infeasible at full scope — fallback per action plan §0.1).
- Issues 06–10 (all tier-1 + tier-2 comparators vendored).
- Issue 15 (A4-sanity preflight cleared the gap ≥ 2 pp threshold).

## References

- Action plan A4.1 (lines 244–279), §0 priority order, §0.1 scope-cuts contingency.
- PRD §7 (lines 211–242), §9.5.2 (peripherals), §9.5.4 (escalation), §9.5.6 (decision log).
- User directive 2026-05-17: "show our method does not degrade in accuracy compared to prior work".

## Comments

(none yet)
