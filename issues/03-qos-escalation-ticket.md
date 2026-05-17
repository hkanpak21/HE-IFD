# 03. QoS escalation ticket (P0)

Status: ready-for-human
Label: HITL
Priority: P0 (admin; blocks 18, 23, 24)
Action-plan: P0 (action plan §0 "Valar concurrency wall")
PRD-section: §9.5.2 (sbatch chunk size peripheral)

## Parent

Action plan §0 "Valar concurrency wall (2026-05-17 audit)" + memory `valar`.

## What to build

Open an admin ticket with KU Valar HPC requesting `t4_ai` QoS be added to user `hkanpak21`'s `comx29` association. Current state per audit:

- `sacctmgr show qos comx29 → gres/gpu:tesla_t4=1` — capped at 1 concurrent T4 across the cluster.
- `sacctmgr show user hkanpak21 → Qos=comx29` only — `t4_ai` QoS not in user's QoS list.
- 159 historical jobs all single-GPU.

`t4_ai` QoS would lift the cap to 16 concurrent T4s at the same billing rate. Without it, A4.1 sequential on 1 GPU at tier-1 scope (360 cells × 1–2 GPU-h) is 45–90 calendar days — the 26-week plan is infeasible.

Why this is HITL: opening an admin ticket requires a human-authored email or web form with institutional context (advisor, project ID, justification framing). Claude cannot send authenticated email.

## Acceptance criteria

- [ ] Ticket opened (record ticket ID, date opened, recipient address in this issue's Comments).
- [ ] Receipt confirmation captured.
- [ ] On QoS approval: re-run `sacctmgr show user hkanpak21` to verify `Qos=comx29,t4_ai`; record output in Comments.
- [ ] On QoS approval: update memory `valar` if any details change.
- [ ] If denied: trigger §0.1 scope-cuts contingency (A4.1 to tier-1 + 3 datasets + 2 α + 2 seeds; drop SVHN/CIFAR-100/α=0.1/3rd seed; A5 γ to MNIST+FashionMNIST only).

## Blocked by

None — open ticket immediately.

## References

- Action plan §0 "Valar concurrency wall" and §0.1 "Scope cuts if QoS escalation fails".
- Memory `valar`: t4_ai partition, account=comx29, login-node-forbidden rule.

## Comments

(none yet)
