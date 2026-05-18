"""
HE-IFD prototype library.

Module map:
    partitions          -- deterministic Dirichlet partition of a torch dataset.
    teachers            -- per-client teacher CNN train/load with resume.
    encrypted_ensemble  -- probe-pass + beta-aggregation + lambda variance under TenSEAL CKKS.
    linear_accumulator  -- depth-<=-3 encrypted SGD against the ensemble target.
    evaluation          -- decrypt, eval student/teachers/oracle on the test set.

All modules are import-safe at module-scope (no CKKS context creation at
import time, no synthetic data generation). Heavy work is gated behind
function calls so syntax-checking on the login node remains cheap.
"""
