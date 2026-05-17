# 04. A2 TenSEAL smoke prototype

Status: ready-for-agent
Label: AFK
Priority: P2 (validates linear-accumulator depth ≤ 3; unblocks 14, 15, 25)
Action-plan: A2
PRD-section: §8

## Parent

Action plan A2 (lines 201–208) + PRD §8 (lines 245–256).

## What to build

`prototypes/cfd_tenseal_smoke.py` — a standalone Python prototype that runs the §4.2 β-aggregation + λ variance + one linear-accumulator SGD step under real TenSEAL CKKS, validating that the depth-≤-3 claim holds. Plus `jobs/smoke_tenseal.sh` to launch on `t4_ai` (never login-node per memory `valar`).

**Contents per PRD §8 + linear-accumulator clarification:**

1. **TenSEAL CKKS context** at logN=14 minimum, scale=2^40, polynomial modulus ring degree configured to support depth ≥ 6 levels (per memory `project-linear-accumulator`, depth ≤ 3 needed; depth 6 leaves headroom).
2. **Mock teacher logits**: encrypt $N=10$ mock teacher logit tensors of shape $(|\mathcal{P}|, C) = (5000, 10)$ + mock $\alpha_i$ scalars.
3. **β-aggregation per PRD §4.2:**
   - Compute $\alpha_i^\beta$ for $\beta = 2$ via one ctxt-ctxt multiplication (depth +1).
   - Linear sum $\widetilde Y = \sum_i \langle\alpha_i^\beta\rangle \cdot \langle T_i(\mathcal P)\rangle$ (depth +1).
   - Decrypt with all simulated key shares; assert max element-wise error < $10^{-3}$ vs the plaintext-equivalent computation.
4. **λ per-row variance per PRD §4.2:**
   - $V_k = \tfrac{1}{N}\sum_i \langle T_{i,k}\rangle^2 - (\tfrac{1}{N}\sum_i \langle T_{i,k}\rangle)^2$, one ctxt-ctxt square (depth +1), one ctxt-ctxt square of the mean (depth +1).
   - Decrypt and compare.
5. **One linear-accumulator SGD step:**
   - 2-layer MLP student starting from plaintext $\theta_0$.
   - Forward pass on plaintext $\theta_0$ against plaintext probe.
   - Compute encrypted KL loss against $\widetilde Y$ with polynomial-softmax approximation.
   - Encrypted gradient $\langle g_t\rangle$ via backprop on the encrypted loss (depth ≤ 3 per memory `project-linear-accumulator`).
   - Update encrypted accumulator $\langle\Delta\rangle = \langle\Delta\rangle + \eta \cdot \langle g_t\rangle$ (depth +1 scalar-ctxt; depth +1 addition).
   - Decrypt $\langle\Delta\rangle$; assert gradient direction matches plaintext.
6. **Three measured outputs** per A2 spec:
   - Per-step plaintext-vs-HE divergence (correctness): max-norm of $\langle\Delta\rangle - \Delta_{\text{plain}}$.
   - Wall-clock per phase (compute).
   - Ciphertext bytes per phase (communication).

**Forgetting points per PRD §8:**
- TenSEAL auto-rescales after each multiplication; depth ≤ 3 fits TenSEAL's level chain at logN=14. **No bootstrapping needed under the linear-accumulator construction** (memory `project-linear-accumulator`); the smoke test stays entirely in TenSEAL.
- Per-row Gaussian noise (P2) must be added to **plaintext** logits before encryption.
- Plaintext baseline must use the same finite-precision arithmetic as CKKS scale=$2^{40}$ (≈12 decimal digits) for a fair comparison.

**sbatch wrapper** `jobs/smoke_tenseal.sh`:
```
#!/bin/bash
#SBATCH --partition=t4_ai
#SBATCH --account=comx29
#SBATCH --gres=gpu:tesla_t4:1
#SBATCH --time=00:30:00
#SBATCH --output=results/smoke_tenseal_%j.log
srun python prototypes/cfd_tenseal_smoke.py --logn 14 --scale 40 --N 10 --probe 5000
```

**Golden rule:** never `python prototypes/cfd_tenseal_smoke.py` on the login node; always via `sbatch jobs/smoke_tenseal.sh`.

## Acceptance criteria

- [ ] `prototypes/cfd_tenseal_smoke.py` exists.
- [ ] `jobs/smoke_tenseal.sh` exists, executable, `t4_ai`-partition-gated.
- [ ] Smoke run completes in < 30 min wall-clock on a single T4.
- [ ] Decrypted β-aggregation: max element-wise error < $10^{-3}$.
- [ ] Decrypted λ variance: max element-wise error < $10^{-3}$.
- [ ] Linear-accumulator SGD step: gradient direction matches plaintext (cosine similarity > 0.99).
- [ ] Three measurement outputs (divergence, wall-clock, bytes) printed to stdout and persisted to `results/smoke_tenseal_<job_id>.json`.
- [ ] No login-node execution attempted.

## Blocked by

- Issue 01 (PRD §4.3 + §8 cleaned up so this prototype reflects the actual protocol).
- Issue 02 (Ralph scaffold + decision log infrastructure ready).

## References

- PRD §4.2 (lines 150–168), §8 (lines 245–256).
- Action plan A2 (lines 201–208), A3 §"Depth budget clarification" (lines 32–34).
- Memory: `project-linear-accumulator`, `valar`.
- Legacy code: `legacy/toy_ifd_real_he.py` (already-working TenSEAL ops in this codebase).

## Comments

(none yet)
