# HE-OFT — submission venues

Method: one-shot federated fine-tuning; server aggregates encrypted LoRA
displacements under multiparty CKKS at depth one; threshold decryption.
Positioning axes reviewers will weigh: (a) systems/networking vs. security vs.
ML, (b) crypto novelty (we reuse MHE — engineering, not new primitives) vs.
protocol/systems novelty, (c) fit of "generic FL + HE" to the venue's scope.

## Currently targeted

| Venue | Type | Fit | Notes |
|---|---|---|---|
| IEEE TNSE | Journal | medium | Current target. Networked-systems angle fits; "generic FL+crypto" scope risk flagged by us before. Shares reviewer pool with the rejected TDSC submission. |

## Journals — primary alternatives

| Venue | Type | Fit | Notes |
|---|---|---|---|
| IEEE TIFS | Journal | high | Security/forensics home for privacy-preserving ML; strong fit for the crypto+MIA framing. Competitive, slow. |
| IEEE TDSC | Journal | — | Where it was rejected. Do not resubmit without addressing that panel; shared pool with TNSE. |
| PoPETs / PETS | Journal (rolling) | high | Privacy-tech venue; values the DP-vs-crypto contrast and the MIA measurement. Four deadlines/year, fast. |
| IEEE TPDS | Journal | medium | Parallel/distributed-systems angle; would need the systems/scaling story foregrounded. |
| IEEE TNNLS | Journal | low-med | ML-heavy; crypto would read as secondary. |
| ACM TOPS | Journal | medium | Security/privacy; smaller readership. |

## Conferences — security

| Venue | Fit | Notes |
|---|---|---|
| USENIX Security | high | Strong for the training-time-attack storyline + MIA; systems-security readers. Very competitive. |
| ACM CCS | high | Same fit; crypto-literate panel will scrutinize the depth-one framing. |
| IEEE S&P (Oakland) | high | Same; hardest bar. |
| NDSS | high | Systems-security; often kinder to applied protocol work. |
| PoPETs (as conf track) | high | Best scope match; multiple cycles. |
| ESORICS | medium-high | European security; good applied-crypto fit, lower bar than the big four. |
| ACSAC | medium | Applied security; welcomes systems + measurement. |

## Conferences — ML / systems

| Venue | Fit | Notes |
|---|---|---|
| NeurIPS / ICML / ICLR | medium | Would need the ML contribution (task-arithmetic-under-HE, one-shot) foregrounded; crypto as enabler. Privacy workshops are a faster path. |
| MLSys | medium-high | Systems-for-ML; the cost/communication story and Lattigo implementation fit well. |
| AISTATS | low-med | Theory-leaning. |

## Recommendation (plain)

1. If staying journal: **PoPETs** (best scope fit, fast cycles) or **IEEE TIFS**
   (prestige, security home). Keep TNSE only if the PIs want the networking framing.
2. If moving to a conference: **NDSS** or **USENIX Security** for the
   training-time-attack narrative; **ESORICS/ACSAC** as lower-bar applied fallbacks.
3. Avoid TDSC (shared reviewer pool with the rejection) unless the rebuttal is airtight.

## Open decision (PIs)

Venue is a PI call. The scope-fit risk (generic FL+crypto) is smallest at
PoPETs/TIFS/USENIX-Security and largest at the ML venues.
