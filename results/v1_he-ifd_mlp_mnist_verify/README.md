# v1_he-ifd_mlp_mnist_verify

M1 consolidation verification cell (issue 001). From-scratch MNIST / MLP
(784->128->64->10). Runs the consolidated `src/` protocol end-to-end on a tiny
grid that exercises the qualitative sanity gate: at alpha=0.05 `raw_union_K20`
must beat `no_phase0` (alignment beats no-alignment under heterogeneity), and at
alpha=1.0 (IID) the aggregated student must land near the single-model ceiling
(mean teacher / oracle). This is a LOGIC port check, not a colab bit-match.

The table below is auto-populated by `src.report` when the sweep runs on VALAR.
