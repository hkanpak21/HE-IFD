# linearize_test — can internal-layer LoRA survive Serve?

Serve keeps the aggregate encrypted, so the client must run the backbone in
plaintext. Internal-layer LoRA makes the features depend on the secret adapter,
which is impossible under encryption at depth 1-2. The only rescue is to feed
BASE-model activations at every LoRA site and add all LoRA contributions once at
the logits — a first-order (linearized) approximation of the true model.

This measures, in plaintext, what that approximation costs.
`eps=1.0` rows are an exactness self-test (`acc_lin` must equal `acc_true`).

Decision: `acc_lin ≈ acc_true` → internal LoRA is rescuable, no 0.93→0.78 cliff.
`acc_lin` collapses → servable architecture is head-side, cliff stands.
