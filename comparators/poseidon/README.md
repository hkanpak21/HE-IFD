# POSEIDON (Sav et al., NDSS 2021)

POSEIDON does **not** have a standalone GitHub repository; its implementation lives inside Lattigo's examples (`tuneinsight/lattigo`).

- **Paper:** Sav, Pyrgelis, Troncoso-Pastoriza, Froelicher, Bossuat, Troncoso-Pastoriza, Hubaux. *POSEIDON: Privacy-Preserving Federated Neural Network Learning*. NDSS 2021. arXiv:2009.00349.
- **Implementation reference:** `https://github.com/tuneinsight/lattigo` — same authors and group. The multiparty-CKKS primitives (CKG / RKG / RTG / CKS) that POSEIDON describes are what Lattigo implements; the NN training loop on top is sketched in the paper's §5 and §6.

We do not vendor Lattigo here (it is ~1 GB with all its tests and examples). When we need to actually instantiate the encrypted protocol we install it as a Go dependency and call from Python via subprocess, as documented in the future v2 plan.

This subdirectory exists so the comparator-results table (REPORTED_RESULTS.md) can reference a stable filesystem path; the meaningful artefact is the paper.
