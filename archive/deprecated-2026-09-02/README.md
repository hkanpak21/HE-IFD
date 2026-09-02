# Deprecated, 2026-09-02

Moved out of the working tree on 2026-09-02. Provenance only. Nothing here is
methodology and nothing here should be mined for it.

## mia/ and jobs/*mia*

The membership-inference suite written for the released-model protocol. Its
target composed `src.phase0`, `src.distill` and `src.aggregate` and attacked a
model this protocol never produces, so it could not be pointed at the current
construction without being rewritten.

It was superseded rather than repaired. The attacks the paper reports now live in
`jobs/mia_extracted_head.py`, `jobs/row_leakage.py` and `jobs/oslo_serving.py`,
and they attack what the protocol actually exposes: a head reachable only by
extraction from label-only answers. Records in `results/mia_extracted/`,
`results/row_leakage/` and `results/oslo_serving/`.

The four job wrappers came with it because they import the package.

## FL_TDSC/

The rejected TDSC submission. Encrypted intermediate-feature distillation,
polynomial activations, server-side encrypted SGD. None of that is the current
method. Kept because the figure palette and some prose predate the pivot.

## REJECTED_PAPER/

The decision letter and the submitted PDF for the same rejection.
