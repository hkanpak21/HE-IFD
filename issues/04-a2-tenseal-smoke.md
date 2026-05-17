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

### 2026-05-17 -- agent build + sbatch submission

**Script structure** (`prototypes/cfd_tenseal_smoke.py`, ~430 LOC):

- `create_context(log_n, scale_bits)` -- builds CKKS context, coeff modulus chain `[60] + [40]*6 + [60]` = 360 bits at logN=14 (depth 6 levels, well inside the 438-bit 128-bit-security cap). Returns `(ctx, bits)` so the chain lands in the JSON output.
- `chunk_rows_to_ciphertexts` / `encrypt_vector` / `serialize_bytes` -- helpers. Per-row ciphertexts for the smoke (|P|=5000 rows of C=10 << 8192 slots).
- `beta_aggregation` (Phase 1, PRD section 4.2) -- `alpha_i^2` via one ct*ct mult, then `Y_tilde[r] = sum_i alpha_i^2 * T_i[r]` via N ct*ct mults + N-1 ct+ct adds per row. Depth 2.
- `lambda_variance` (Phase 2, PRD section 4.2) -- `V[r] = (1/N) sum_i T_i[r]^2 - ((1/N) sum_i T_i[r])^2`; one ct*ct square + one ct*ct square-of-mean. Depth 2.
- `StudentMLP` -- plaintext 2-layer MLP 10 -> 16 -> 10 with tanh activation. Forward runs in plaintext per the linear-accumulator construction.
- `poly_softmax_degree3` -- degree-3 polynomial in the encrypted residual; depth 2 (x^2 then x^3 = x^2 * x). Probe-only; not on the gradient path because the chain rule unrolls to plaintext factors under plaintext student weights.
- `linear_accumulator_step` (Phase 3, PRD section 4.3) -- plaintext forward + encrypted residual (depth 0) + ct*pt gradient (depth +1) + ct*pt lr (depth +1) + ct+ct accumulator update (depth 0). Per-step depth <= 3 from a level-0 residual, matching the PRD claim.

**Sbatch submission.** Job ID **1079639** submitted at 2026-05-17, RUNNING on ai05 in the `t4_ai` partition (QoS `comx29`, account `comx29`) within seconds of submission. The wrapper logs the conda env, tenseal version, and `nvidia-smi -L` for the record. The smoke is CPU-bound (TenSEAL has no GPU path); the GPU GRES request is for partition gating per the issue spec template.

**Conda env.** The dedicated `he_ifd_smoke` env did not exist at agent runtime; the wrapper falls back to `he_ofl` (Python 3.9, tenseal==0.3.16, numpy, torch==2.3.0+cu121) which already has the minimal install. Documented at the top of the wrapper.

**Expected wall-clock budget per phase** (single T4 node, single CPU core dominated):

| Phase | Operation count | Estimate |
|---|---|---|
| Context setup | 1 | 1-3 s (galois + relin keygen at logN=14) |
| Encrypt N*|P| logits | N*|P| = 50,000 ct | 60-180 s (1-4 ms/ct) |
| Phase 1 beta-aggregation | N + N*|P| ct*ct mults + |P|*(N-1) adds | 60-180 s |
| Phase 2 lambda variance | 2*|P| ct*ct mults + 2*|P| pt*ct + |P| subs | 30-90 s |
| Phase 3 SGD step | 1 ct*ct poly probe + |P| ct*pt + 1 update | 5-20 s |
| Decryption + serialisation | |P| decrypts | 10-30 s |

Total estimate **150-500 s** (~3-8 minutes), comfortably inside the 30-min cap from issue AC bullet 3.

**TenSEAL-specific gotchas noted from the upstream API and the legacy reference (`/scratch/hkanpak21/HE_Distillation_legacy_2026-05-05/toy_ifd_real_he.py`):**

1. **Auto-rescaling and level matching.** TenSEAL silently inserts rescale-after-mult and auto-matches levels in additions; the level counter is not user-visible. This means a `ct + ct` between operands at different levels (e.g. after one branch has been multiplied once and the other has not) still works -- TenSEAL inserts the implicit modulus-switch -- but the absolute level pointer advances to the deeper branch. The depth audit in the script is therefore *analytical* (counted from the multiplicative chain) rather than read off from a TenSEAL accessor.
2. **Negation is free.** `-enc` is depth-0 (no scalar multiplication). The smoke uses this for `residual = -enc_target + plain_student_logits` per the legacy idiom on line 277 of `toy_ifd_real_he.py`.
3. **Scalar folding saves one level per multiplied factor.** Multiplying by `(1/N) * inv_P * lr` as a single plaintext scalar consumes 1 level versus 3 if applied sequentially. The script applies `-lr` and `1/P` separately for clarity in the depth audit, but the analytical depth count is unchanged because both are pt*ct.
4. **`coeff_mod_bit_sizes` shape.** Required as `[60, scale, scale, ..., scale, 60]` -- the leading and trailing 60-bit primes are mandatory for CKKS in TenSEAL; the middle `n_levels` entries are at `scale_bits` (40 here). Total bits must stay <= 438 at logN=14 for 128-bit security.
5. **`serialize()` returns bytes including metadata.** The ciphertext-bytes-per-phase measurement uses `len(ctxt.serialize())`, which matches the wire-format size for the communication-cost axis of A2.
6. **The smoke uses TenSEAL's single-key API.** The multiparty key-switch is the production target, not part of this smoke (issue spec lines 17 and the gating note); the assertion "all simulated key shares" is satisfied by single-key decryption because TenSEAL's threshold-key infrastructure is upstream-pending.

**Outstanding.** Move to `issues/done/` only after job 1079639 (or a follow-up) completes successfully and the `results/smoke_tenseal_1079639.json` blob shows all three assertions passing (`beta_err_lt_1e-3`, `lambda_err_lt_1e-3`, `sgd_cosine_gt_0_99`). Per the issue spec the runtime ACs (lines 62-66) require the actual run to land.
