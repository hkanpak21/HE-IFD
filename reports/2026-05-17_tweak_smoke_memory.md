# Tweak — TenSEAL smoke memory budget 16G → 64G (2026-05-17)

*Motivation.* Slurm job 1079639 (issue 04, `jobs/smoke_tenseal.sh`) was killed with `oom_kill event in StepId=1079639.0` after 4 min wall-clock. The job survived `create_context` (the log shows `context built in 2.02s; coeff chain [60, 40, 40, 40, 40, 40, 40, 60], levels=6`) and was killed during the encryption phase. At logN=14 the public-key + galois rotation key + relinearisation key set already consumes several hundred megabytes, and the per-ciphertext multiplication intermediates for the β-aggregation pass over $N{=}10$ teacher logit tensors of shape $(5000, 10)$ push working-set far past the 16 GB allocation.

*Tweak.* `jobs/smoke_tenseal.sh` `#SBATCH --mem` row, peripheral per PRD §9.5.2 ("sbatch chunking"), old value `16G` → new value `64G`. No change to logN, scale, $N$, $|\mathcal P|$, $\beta$, or the protocol primitives being smoked.

*Expected effect.* Job 1079640 (resubmission with the new budget) should complete in well under the 30 min wall-clock cap and emit `results/smoke_tenseal_<job_id>.json` with the three measurement outputs (divergence, wall-clock per phase, ctxt bytes per phase) and pass the three correctness assertions (β-aggregation < $10^{-3}$, λ-variance < $10^{-3}$, gradient cosine-sim > 0.99).

*Fallback.* If the next run also OOMs, the next peripheral adjustment is to reduce $|\mathcal P|$ from 5000 to 1000 (also a §9.5.2 peripheral — probe size). That would shrink ciphertext counts by 5×. Logged as a follow-on tweak if needed; the linear-accumulator depth audit does not depend on the probe size, only on the depth-per-step count.

*Cross-references.* Issue 04 (`issues/04-a2-tenseal-smoke.md`). Action plan A2 (lines 201–208). PRD §8 (lines 245–256). Failed job 1079639 logs at `results/smoke_tenseal_1079639.{log,err}`.
