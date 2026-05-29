#!/usr/bin/env python3
"""Build trajectories.png: test-acc vs step per scheme, faceted by alpha, at
N=10, for the probe (top row) and no-probe (bottom row) basins. Uses seed 42
cell JSONs. Run after run_probe.py."""
import glob
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
SEED = 42
N = 10
ALPHAS = [0.05, 0.1, 0.5, 1.0]
BASINS = ["probe", "no-probe"]

SCHEME_STYLE = {
    "weight_avg":   ("#d62728", "-",  "A weight_avg (one-shot)"),
    "stepsum":      ("#ff9896", "--", "B stepsum (telescoping ctrl)"),
    "sync_sgd":     ("#1f77b4", "-",  "C sync_sgd (synchronized)"),
    "fedavg_Estep": ("#2ca02c", "-.", "D fedavg E=5"),
    "centralized":  ("#7f7f7f", ":",  "E centralized (oracle)"),
}


def load_cell(basin, alpha):
    path = os.path.join(OUT_DIR, f"cell_{basin}_N{N}_a{alpha}_s{SEED}.json")
    with open(path) as f:
        return json.load(f)


fig, axes = plt.subplots(len(BASINS), len(ALPHAS), figsize=(17, 8), sharey=True)
for r, basin in enumerate(BASINS):
    for c, alpha in enumerate(ALPHAS):
        ax = axes[r][c]
        cell = load_cell(basin, alpha)
        for scheme, (color, ls, label) in SCHEME_STYLE.items():
            sc = cell["schemes"][scheme]
            xs = sc["eval_steps"]
            ys = [100.0 * v for v in sc["acc_traj"]]
            ax.plot(xs, ys, color=color, linestyle=ls, marker="o", markersize=2.5,
                    linewidth=1.8, label=label if (r == 0 and c == 0) else None)
        th0 = 100.0 * cell["theta0_acc"]
        ax.axhline(th0, color="black", linestyle=(0, (1, 3)), linewidth=0.9, alpha=0.6)
        ax.set_title(f"{basin}  |  alpha={alpha}", fontsize=10)
        ax.set_xlabel("step (local / synchronized)")
        if c == 0:
            ax.set_ylabel("test accuracy (%)")
        ax.grid(True, alpha=0.25)
        ax.set_ylim(0, 100)
        # annotate the final WA-vs-SYNC gap
        wa = 100.0 * cell["schemes"]["weight_avg"]["final_acc"]
        ss = 100.0 * cell["schemes"]["sync_sgd"]["final_acc"]
        ax.text(0.97, 0.05, f"SYNC-WA = +{ss-wa:.1f} pt", transform=ax.transAxes,
                ha="right", va="bottom", fontsize=8,
                bbox=dict(boxstyle="round,pad=0.25", fc="#fff7e6", ec="#d0a040", alpha=0.9))

handles, labels = axes[0][0].get_legend_handles_labels()
handles.append(plt.Line2D([0], [0], color="black", linestyle=(0, (1, 3)), linewidth=0.9))
labels.append("theta0 (basin start)")
fig.legend(handles, labels, loc="upper center", ncol=6, fontsize=9,
           bbox_to_anchor=(0.5, 1.0), frameon=False)
fig.suptitle("Aggregation schemes on MNIST MLP — test acc vs step  (N=10, seed 42)\n"
             "synchronized trajectory (C) vs telescoping weight-average (A/B), "
             "by label-Dirichlet alpha and basin", y=1.07, fontsize=12)
fig.tight_layout(rect=[0, 0, 1, 0.97])
out = os.path.join(OUT_DIR, "trajectories.png")
fig.savefig(out, dpi=130, bbox_inches="tight")
print(f"wrote {out}")
