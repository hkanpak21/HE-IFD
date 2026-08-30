# mia_extracted

How much membership signal survives extraction of the served head. Measures the
cap delta_wb that Proposition 2 introduces and nobody had measured. Three attack
surfaces per cell: the head handed over in plaintext (the ceiling), a copy fitted
from Q label-only queries (what the protocol admits), and the free gap baseline.

Reported as true-positive rate at 0.1 and 1 per cent false-positive rate, the
convention Carlini et al. (IEEE S&P 2022) require.

Produced by `jobs/mia_extracted_head.py`, submitted with `jobs/mia_extracted_head.sh`.
