# 23. A5 DP-DDPM generator training (per-client)

Status: ready-for-agent
Label: AFK
Priority: P4 (conditional path determined by issue 22)
Action-plan: A5 generator-training pass
PRD-section: §3.2 (γ-variant)

## Parent

Action plan A5 (lines 317–341). Scope depends on issue 22's profiling result:
- h ≤ 3 h → full grid: 15 (dataset, α) pairs × 10 clients each.
- 3 h < h ≤ 8 h → subset: 5 (dataset, α) pairs × 10 clients.
- h > 8 h → narrow subset: 3 (dataset, α) pairs × 10 clients (drop SVHN + CIFAR-100).

## What to build

For each (dataset, α) in scope, train per-client DP-DDPMs:

- **Architecture:** Pixel-space U-Net (~2–3M params), Dockhorn et al. TMLR 2022 reference implementation (`github.com/nv-tlabs/DPDM`).
- **DP budget:** (ε_G, δ_G) = (10, 10⁻⁵) headline + (1, 10⁻⁵) ablation per PRD §3.2 and Appendix A.
- **Per-client sample volume:** $|\mathcal P|/N = 500$ synthetic samples per client at N=10 (PRD §3.2 line 109). Generated locally; never uploaded in plaintext.
- **Seeds:** Generator trained *once per (dataset, α)* and reused across all 3 distillation seeds per action plan A5 line 322.

**Output per (dataset, α, client_id):**
- `comparators/dpdm/checkpoints/<dataset>_<alpha>_client<id>_eps<eps>.pt` — generator weights.
- `comparators/dpdm/synthetic/<dataset>_<alpha>_client<id>_eps<eps>.pt` — 500 synthetic samples (kept on-device; only the encrypted-pooled probe goes to the server per PRD §3.2).
- DP accountant log line proving (ε_G, δ_G) achieved.

**Compute** is dominant per action plan A5 line 322: 150 × h GPU-hours for the full grid, 50 × h for the subset, 30 × h for the narrow subset. Tweak protocol per §9.5.3 if compute pressure forces a scope reduction.

## Acceptance criteria

- [ ] All in-scope (dataset, α, client, ε) combinations have a generator checkpoint and a synthetic-sample tensor.
- [ ] DP accountant verified for every checkpoint.
- [ ] Synthetic FID reasonable for each (dataset, ε) pair (publication-comparable to Dockhorn et al.'s downstream classifier numbers at MNIST: 98.1 % at ε=10, 83.2 % at ε=1).
- [ ] Each per-client run respects the 8-hour wallclock cap (checkpoint-resume per memory `valar`).
- [ ] Compute pressure tweaks (if any) logged per §9.5.3 / §9.5.6.
- [ ] No login-node execution.

## Blocked by

- Issue 03 (QoS escalation; per-client jobs run in parallel under `t4_ai` QoS).
- Issue 22 (γ-scope conditional path chosen).

## References

- Action plan A5 (lines 317–341).
- PRD §3.2 (lines 107–119), Appendix A (locked items, line 406).
- Upstream: `https://github.com/nv-tlabs/DPDM`.
- Bibkey: `dockhorn2022dpdm`.

## Comments

(none yet)
