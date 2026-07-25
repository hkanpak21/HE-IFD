# personal_adapter_vision — experiment B on a frozen ViT-B/16

Vision arm of jobs/personal_adapter_test.py. Each client trains its OWN LoRA
adapter locally and never shares it (no adapter aggregate -> nothing for an
(N-1) coalition to subtract); only the HEAD is federated under HE and kept
encrypted, answering queries via encrypted argmax.

Modes: current (agg adapter + agg head, NOT servable) | local | B_personal
(own adapter + agg head) | A_headonly (r=0 floor) | selected (per-client vote).
