# personal_adapter — federate only the head, keep the adapter local

Serve forbids a *shared* internal adapter: its aggregate would have to be
decrypted, and an (N-1) coalition could subtract its own contributions to
recover the last honest client's displacement exactly.

This tests never aggregating the adapter at all: each client keeps its own
adapter private (nothing to subtract -> collusion-safe), and only the HEAD is
federated under HE and served encrypted. Rationale: the adapter improves the
representation, which a client can do alone; the head is where coverage bites.

Modes (all on the GLOBAL test set):
  local       adapter_j + head_j        client alone
  B_personal  adapter_j + agg_head      <-- the proposed design
  current     agg_adapter + agg_head    current HE-OFT (not servable)
  no_adapter  theta0 + agg_head         head trained with an adapter, served without
  A_headonly  r=0 head-only, federated  the true floor
