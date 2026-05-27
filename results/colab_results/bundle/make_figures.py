"""
Generate paper headline figures from the parsed long-form data.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")

BASE = "/home/claude/he_ifd_parsed"
df = pd.read_csv(f"{BASE}/raw_all_results.csv")
import os
os.makedirs(f"{BASE}/figures", exist_ok=True)

# ============================================================================
# Figure 1 (Section A): Probe-size sweep with protocol contribution
# ============================================================================
df_A = df[df["section"] == "A"].copy()
agg = (df_A.groupby(["alpha", "probe_size", "method"])["acc"]
            .agg(["mean", "std"]).reset_index())

method_order = ["no_phase0", "warmup_only_labelled", "labelled_probe_warmup",
                 "raw_union_K20", "dp_avg_eps2_K20", "dp_avg_eps8_K20"]
method_labels = {
    "no_phase0":              "no Phase 0",
    "warmup_only_labelled":   "warmup only (no protocol)",
    "labelled_probe_warmup":  "labelled probe + protocol",
    "raw_union_K20":          "raw align K=20 + protocol",
    "dp_avg_eps2_K20":        "DP align ε=2, K=20 + protocol",
    "dp_avg_eps8_K20":        "DP align ε=8, K=20 + protocol",
}
method_colors = {
    "no_phase0": "#1f77b4",
    "warmup_only_labelled": "#ff7f0e",
    "labelled_probe_warmup": "#2ca02c",
    "raw_union_K20": "#d62728",
    "dp_avg_eps2_K20": "#9467bd",
    "dp_avg_eps8_K20": "#8c564b",
}

ALPHAS = sorted(df_A["alpha"].unique())
fig, axes = plt.subplots(1, len(ALPHAS), figsize=(4.5 * len(ALPHAS), 4.2), sharey=True)
for ax, alpha in zip(axes, ALPHAS):
    sub = agg[agg["alpha"] == alpha]
    for m in method_order:
        ms = sub[sub["method"] == m].sort_values("probe_size")
        if len(ms) == 0:
            continue
        ax.errorbar(ms["probe_size"], ms["mean"], yerr=ms["std"], marker="o",
                      label=method_labels[m], capsize=3, color=method_colors[m])
    ax.set_xlabel("Probe size P")
    ax.set_xscale("log")
    ax.set_title(f"α = {alpha}")
    ax.grid(alpha=0.3)
    ax.set_ylim([0.1, 1.0])
    if ax is axes[0]:
        ax.set_ylabel("Test accuracy")
axes[-1].legend(loc="lower right", fontsize=7, framealpha=0.95)
fig.suptitle("Figure 1. MNIST MLP from scratch: protocol contribution across α and probe size P (mean ± std, 3 seeds)")
fig.tight_layout()
fig.savefig(f"{BASE}/figures/figure_1_section_A_protocol_surface.png",
              dpi=140, bbox_inches="tight")
plt.close(fig)
print("Wrote figure_1_section_A_protocol_surface.png")

# ============================================================================
# Figure 2 (Section B): Pretrained vision backbones
# ============================================================================
df_B = df[df["section"] == "B"].copy()
agg_B = (df_B.groupby(["backbone", "alpha", "method"])["acc"]
              .agg(["mean", "std"]).reset_index())

method_order_BC = ["no_phase0", "labelled_probe_warmup", "raw_union_K20",
                    "dp_avg_eps2_K20", "dp_avg_eps8_K20"]
method_labels_BC = {
    "no_phase0":              "no Phase 0",
    "labelled_probe_warmup":  "labelled probe (P=100)",
    "raw_union_K20":          "raw align K=20",
    "dp_avg_eps2_K20":        "DP align ε=2, K=20",
    "dp_avg_eps8_K20":        "DP align ε=8, K=20",
}
colors_BC = ["#1f77b4", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]

backbones = ["resnet18", "vit_b32"]
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
for ax, bb in zip(axes, backbones):
    sub = agg_B[agg_B["backbone"] == bb]
    alphas_here = sorted(sub["alpha"].unique())
    x = np.arange(len(alphas_here))
    width = 0.8 / len(method_order_BC)
    for i, m in enumerate(method_order_BC):
        vals, errs = [], []
        for a in alphas_here:
            row = sub[(sub["alpha"] == a) & (sub["method"] == m)]
            vals.append(row["mean"].iloc[0] if len(row) else np.nan)
            errs.append(row["std"].iloc[0] if len(row) else 0)
        ax.bar(x + i*width, vals, width, yerr=errs, color=colors_BC[i],
                label=method_labels_BC[m], capsize=3, alpha=0.85, edgecolor="k")
    ax.set_xticks(x + 2*width)
    ax.set_xticklabels([f"α={a}" for a in alphas_here])
    ax.set_title(f"{bb} on CIFAR-10")
    ax.set_ylim([0, 1.0])
    ax.grid(alpha=0.3, axis="y")
    if ax is axes[0]:
        ax.set_ylabel("Test accuracy")
axes[-1].legend(loc="lower right", fontsize=8, framealpha=0.95)
fig.suptitle("Figure 2. Pretrained vision backbones on CIFAR-10 (mean ± std, 3 seeds)")
fig.tight_layout()
fig.savefig(f"{BASE}/figures/figure_2_section_B_vision.png",
              dpi=140, bbox_inches="tight")
plt.close(fig)
print("Wrote figure_2_section_B_vision.png")

# ============================================================================
# Figure 3 (Section C): Pretrained text backbones
# ============================================================================
df_C = df[df["section"] == "C"].copy()
agg_C = (df_C.groupby(["backbone", "alpha", "method"])["acc"]
              .agg(["mean", "std"]).reset_index())

backbones = ["distilbert", "gpt2_small"]
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
for ax, bb in zip(axes, backbones):
    sub = agg_C[agg_C["backbone"] == bb]
    alphas_here = sorted(sub["alpha"].unique())
    x = np.arange(len(alphas_here))
    width = 0.8 / len(method_order_BC)
    for i, m in enumerate(method_order_BC):
        vals, errs = [], []
        for a in alphas_here:
            row = sub[(sub["alpha"] == a) & (sub["method"] == m)]
            vals.append(row["mean"].iloc[0] if len(row) else np.nan)
            errs.append(row["std"].iloc[0] if len(row) else 0)
        ax.bar(x + i*width, vals, width, yerr=errs, color=colors_BC[i],
                label=method_labels_BC[m], capsize=3, alpha=0.85, edgecolor="k")
    ax.set_xticks(x + 2*width)
    ax.set_xticklabels([f"α={a}" for a in alphas_here])
    ax.set_title(f"{bb} on AG News")
    ax.set_ylim([0, 1.0])
    ax.grid(alpha=0.3, axis="y")
    if ax is axes[0]:
        ax.set_ylabel("Test accuracy")
axes[-1].legend(loc="lower right", fontsize=8, framealpha=0.95)
fig.suptitle("Figure 3. Pretrained text backbones on AG News (mean ± std, 3 seeds)")
fig.tight_layout()
fig.savefig(f"{BASE}/figures/figure_3_section_C_text.png",
              dpi=140, bbox_inches="tight")
plt.close(fig)
print("Wrote figure_3_section_C_text.png")

# ============================================================================
# Figure 4 (Section D): DP privacy/utility frontier
# ============================================================================
df_D = df[df["section"] == "D"].copy()
# Map eps for display (inf as a categorical point at the right)
EPS_DISPLAY_ORDER = [0.5, 2.0, 8.0, 32.0, np.inf]
EPS_LABELS = ["0.5", "2", "8", "32", "∞"]
EPS_X = list(range(len(EPS_DISPLAY_ORDER)))

agg_D = (df_D.groupby(["setup", "alpha", "eps", "K_per_class"])["acc"]
              .agg(["mean", "std"]).reset_index())

setups = ["cifar10_vit_b32", "ag_news_distilbert", "ag_news_gpt2_small"]
ALPHAS_D = sorted(df_D["alpha"].unique())
K_ORDER = [1, 5, 20]
K_COLORS = {1: "#1f77b4", 5: "#ff7f0e", 20: "#2ca02c"}

fig, axes = plt.subplots(len(setups), len(ALPHAS_D),
                          figsize=(4 * len(ALPHAS_D), 3 * len(setups)),
                          squeeze=False, sharey="row")
for i, setup in enumerate(setups):
    for j, alpha in enumerate(ALPHAS_D):
        ax = axes[i][j]
        sub = agg_D[(agg_D["setup"] == setup) & (agg_D["alpha"] == alpha)]
        for K_pc in K_ORDER:
            ys = []
            errs = []
            for eps in EPS_DISPLAY_ORDER:
                row = sub[(sub["eps"] == eps) & (sub["K_per_class"] == K_pc)]
                ys.append(row["mean"].iloc[0] if len(row) else np.nan)
                errs.append(row["std"].iloc[0] if len(row) else 0)
            ax.errorbar(EPS_X, ys, yerr=errs, marker="o", capsize=3,
                          color=K_COLORS[K_pc], label=f"K={K_pc}")
        ax.set_xticks(EPS_X)
        ax.set_xticklabels(EPS_LABELS)
        ax.set_title(f"{setup}, α={alpha}", fontsize=9)
        ax.grid(alpha=0.3)
        ax.set_ylim([0.1, 1.0])
        if j == 0:
            ax.set_ylabel("Test accuracy")
        if i == len(setups) - 1:
            ax.set_xlabel("ε (per client)")
        if i == 0 and j == 0:
            ax.legend(fontsize=8, loc="lower right")
fig.suptitle("Figure 4. DP privacy/utility frontier (averaging variant; δ=1e-5; 3 seeds)")
fig.tight_layout()
fig.savefig(f"{BASE}/figures/figure_4_section_D_dp_frontier.png",
              dpi=140, bbox_inches="tight")
plt.close(fig)
print("Wrote figure_4_section_D_dp_frontier.png")

print("\nAll figures done.")
