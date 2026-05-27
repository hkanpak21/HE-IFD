"""HE-IFD: consolidated, flat simulation package for the one-shot federated
distillation protocol (IEEE TNSE resubmission).

Single source of truth, ported from results/colab_results/results_notebook.ipynb.
Pipeline order: data -> backbones -> teacher -> phase0 -> distill -> aggregate
-> evaluate, composed by protocol.run_cell and driven by sweep (resumable,
chunkable) with report writing results/<case>/.

The server-side aggregation is sample-weighted (w_i = n_i/Sum_j n_j) and linear by
construction (PT x CT + CT + CT only), so it is FHE-compatible; the encrypted
object is the per-client cumulative displacement Delta_i = theta_i^(K) - theta_0.
"""
