#!/usr/bin/env python3
"""Generate the paper's data figures from the landed results.csv files.

Reproducible: reads results/<case>/results.csv, writes <fig>.pdf next to this script.
Run:  /tmp/figvenv/bin/python docs/paper/figures/make_figures.py
Palette is deliberately restrained (one blue ramp + one neutral + one amber accent),
fonts are >= body text, output is vector PDF.
"""
import csv, collections, statistics as s, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.dirname(__file__)

# ---- SANZO palette (FL_TDSC/figures/sanzo.md) ----
BLUE      = "#5B7FA6"   # SANZO primary blue: our method / final
BLUE_LT   = "#A9BDD3"   # light blue: basin / theta0
BLUE_RAMP = ["#A9BDD3", "#7B9BBF", "#5B7FA6"]  # 3 blue tints for alpha
NEUTRAL   = "#5B7B6E"   # SANZO dark sage: centralized reference
NEUTRAL_LT= "#D4C5A9"   # SANZO light tan: teacher / random floor
AMBER     = "#D4826A"   # SANZO terracotta: contrast accent

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 13, "axes.titlesize": 13, "axes.labelsize": 13,
    "xtick.labelsize": 12, "ytick.labelsize": 12, "legend.fontsize": 11,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 150, "savefig.bbox": "tight", "pdf.fonttype": 42,
})

def load(case):
    p = os.path.join(ROOT, "results", case, "results.csv")
    return [r for r in csv.DictReader(open(p)) if r["status"] == "success"]

def avg(rows, key):
    v = []
    for r in rows:
        try:
            x = float(r[key])
            if x == x: v.append(x)
        except (ValueError, KeyError, TypeError): pass
    return s.mean(v) if v else float("nan")

def cells(rows, N="10", method=None, backbone=None):
    g = collections.defaultdict(list)
    for r in rows:
        if N and r["N"] != N: continue
        if method and r["method"] != method: continue
        if backbone and r["backbone"] != backbone: continue
        g[r["alpha"]].append(r)
    return g

# ======================================================================
# FIG. scaling — the contribution showcase: a common SUPERIOR model.
# avg local teacher  vs  our global model  vs  centralized reference.
# ======================================================================
def fig_scaling():
    vit = cells(load("heifd_012_harder_vision_headline"), method="raw_union_K20", backbone="vit_b32_cifar100")["0.05"]
    txt = load("heifd_019_text_headline")
    rob = cells(txt, method="raw_union_K20", backbone="roberta_base_agnews")["0.05"]
    mpn = cells(txt, method="raw_union_K20", backbone="mpnet_st_agnews")["0.05"]
    groups = [("ViT-B/32\nCIFAR-100", vit), ("RoBERTa\nAG-News", rob), ("MPNet\nAG-News", mpn)]
    labels = [g[0] for g in groups]
    teacher = [avg(g[1], "mean_teacher") for g in groups]
    ours    = [avg(g[1], "acc")          for g in groups]
    oracle  = [avg(g[1], "oracle")       for g in groups]

    import numpy as np
    x = np.arange(len(groups)); w = 0.26
    fig, ax = plt.subplots(figsize=(7.6, 3.4))
    ax.bar(x - w, teacher, w, label="average local teacher", color=NEUTRAL_LT)
    ax.bar(x,     ours,    w, label="our global model",      color=BLUE)
    ax.bar(x + w, oracle,  w, label="centralized reference",  color=NEUTRAL)
    for xi, v in zip(x, ours):
        ax.text(xi, v + 0.015, f"{v:.2f}", ha="center", va="bottom", fontsize=11, color=BLUE)
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_ylabel("test accuracy"); ax.set_ylim(0, 1.0)
    ax.legend(loc="upper left", frameon=False, bbox_to_anchor=(1.0, 1.0))
    fig.savefig(os.path.join(OUT, "fig_scaling.pdf")); plt.close(fig)
    print("scaling:", {l: round(o,3) for l,o in zip(labels, ours)}, "teacher", [round(t,3) for t in teacher])

# ======================================================================
# FIG. continuum — supporting defense: distillation lift vs basin strength.
# x = basin strength (theta0 acc), y = final acc; diagonal = no lift.
# ======================================================================
def fig_continuum():
    rows = load("heifd_017_noprobe_mlp") + load("heifd_mlp_mnist_headline")
    methods = ["noprobe_raw_union_K20", "noprobe_dp_avg_eps8_K20", "noprobe_dp_avg_eps2_K20",
               "dp_avg_eps2_K20", "raw_union_K20"]
    alphas = ["0.05", "0.3", "1.0"]
    fig, ax = plt.subplots(figsize=(5.0, 4.4))
    ax.plot([0, 1], [0, 1], ls="--", color=NEUTRAL_LT, lw=1.2, zorder=0)
    ax.text(0.62, 0.55, "no lift", color=NEUTRAL, fontsize=11, rotation=37)
    for ai, a in enumerate(alphas):
        xs, ys = [], []
        for m in methods:
            g = collections.defaultdict(list)
            for r in rows:
                if r["N"] == "10" and r["method"] == m and r["alpha"] == a:
                    g[m].append(r)
            if g[m]:
                xs.append(avg(g[m], "theta0_acc")); ys.append(avg(g[m], "acc"))
        ax.scatter(xs, ys, s=55, color=BLUE_RAMP[ai], edgecolor="white", linewidth=0.6,
                   zorder=3, label=f"$\\alpha={a}$")
    ax.set_xlabel("shared-basin accuracy ($\\theta_0$ alone)")
    ax.set_ylabel("global model accuracy")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.legend(loc="lower right", frameon=False)
    fig.savefig(os.path.join(OUT, "fig_continuum.pdf")); plt.close(fig)

# ======================================================================
# FIG. 2x2 — supporting: both ingredients necessary.
# ======================================================================
def fig_necessity():
    import numpy as np
    vit = load("heifd_012_harder_vision_headline")
    mnist = load("heifd_mlp_mnist_headline")
    def corners(rows, C):
        a = "0.05"
        noalign = avg([r for r in rows if r["N"]=="10" and r["method"]=="no_phase0" and r["alpha"]==a], "acc")
        basin   = avg([r for r in rows if r["N"]=="10" and r["method"]=="raw_union_K20" and r["alpha"]==a], "theta0_acc")
        full    = avg([r for r in rows if r["N"]=="10" and r["method"]=="raw_union_K20" and r["alpha"]==a], "acc")
        orc     = avg([r for r in rows if r["N"]=="10" and r["method"]=="raw_union_K20" and r["alpha"]==a], "oracle")
        return [noalign, basin, full], orc
    names = ["no\nalignment", "basin\nonly", "full\nmethod"]
    cols  = [AMBER, BLUE_LT, BLUE]
    fig, axes = plt.subplots(2, 1, figsize=(3.35, 5.1))
    for ax, (rows, C, title) in zip(axes, [(vit,100,"ViT-B/32 $\\cdot$ CIFAR-100"), (mnist,10,"MLP $\\cdot$ MNIST")]):
        vals, orc = corners(rows, C)
        ax.bar(range(3), vals, color=cols, width=0.6)
        ax.axhline(orc, ls="--", color=NEUTRAL, lw=1.2)
        ax.text(2.45, orc, "centralized", color=NEUTRAL, fontsize=9, va="bottom", ha="right")
        for i, v in enumerate(vals):
            ax.text(i, v + 0.02, f"{v:.2f}", ha="center", va="bottom", fontsize=9)
        ax.set_xticks(range(3)); ax.set_xticklabels(names, fontsize=10)
        ax.set_ylim(0, 1.05); ax.set_ylabel("test accuracy"); ax.set_title(title, fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_necessity.pdf")); plt.close(fig)

# ======================================================================
# FIG. dp frontier — supporting: accuracy flat as the budget tightens to eps=2.
# ======================================================================
def fig_dpfrontier():
    rows = load("heifd_015_dp_frontier_mlp") + load("heifd_mlp_mnist_headline")
    eps_methods = [("0.5","dp_avg_eps0.5_K20"), ("2","dp_avg_eps2_K20"), ("8","dp_avg_eps8_K20"),
                   ("32","dp_avg_eps32_K20"), ("∞","dp_avg_epsinf_K20")]
    alphas = ["0.05", "0.3", "1.0"]
    fig, ax = plt.subplots(figsize=(5.4, 3.6))
    xticks = list(range(len(eps_methods)))
    for ai, a in enumerate(alphas):
        ys = []
        for _, m in eps_methods:
            g = [r for r in rows if r["N"]=="10" and r["method"]==m and r["alpha"]==a]
            ys.append(avg(g, "acc"))
        ax.plot(xticks, ys, marker="o", color=BLUE_RAMP[ai], lw=1.8, label=f"$\\alpha={a}$")
    ax.axvline(1, ls=":", color=NEUTRAL_LT, lw=1.2)
    ax.text(1.05, 0.12, "$\\varepsilon=2$", fontsize=10, color=NEUTRAL)
    ax.set_xticks(xticks); ax.set_xticklabels([e for e,_ in eps_methods])
    ax.set_xlabel("privacy budget $\\varepsilon$ (smaller = more private)")
    ax.set_ylabel("global model accuracy"); ax.set_ylim(0, 1.0)
    ax.legend(loc="center right", frameon=False)
    fig.savefig(os.path.join(OUT, "fig_dpfrontier.pdf")); plt.close(fig)

# ======================================================================
# FIG. nscaling — graceful scaling in the number of clients.
# ======================================================================
def fig_nscaling():
    rows = load("heifd_012_harder_vision_headline")
    Ns = ["5", "10", "20", "50"]; alphas = ["0.05", "0.3", "1.0"]
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    for ai, a in enumerate(alphas):
        ys = []
        for N in Ns:
            g = [r for r in rows if r["N"]==N and r["method"]=="raw_union_K20" and r["alpha"]==a]
            ys.append(avg(g, "acc"))
        ax.plot(range(len(Ns)), ys, marker="o", color=BLUE_RAMP[ai], lw=1.8, label=f"$\\alpha={a}$")
    ax.set_xticks(range(len(Ns))); ax.set_xticklabels(Ns)
    ax.set_xlabel("number of clients $N$"); ax.set_ylabel("global model accuracy")
    ax.set_ylim(0, 1.0)
    ax.legend(loc="lower left", frameon=False)
    fig.savefig(os.path.join(OUT, "fig_nscaling.pdf")); plt.close(fig)

# ======================================================================
# FIG. ksweep — bounded trajectory: short is better; long drifts down.
# ======================================================================
def fig_ksweep():
    rows = load("heifd_010_kd_hparams_resnet18")
    Ks = ["30", "100", "300", "1000"]
    th0 = avg([r for r in rows if r["tau"]=="1.0"], "theta0_acc")
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    for tau, col, lab in [("1.0", BLUE, "$\\tau=1$"), ("4.0", AMBER, "$\\tau=4$")]:
        ys = [avg([r for r in rows if r["K"]==K and r["tau"]==tau], "acc") for K in Ks]
        ax.plot(range(len(Ks)), ys, marker="o", color=col, lw=1.8, label=lab)
    ax.axhline(th0, ls="--", color=NEUTRAL, lw=1.2)
    ax.text(0.05, th0+0.01, "shared basin $\\theta_0$", color=NEUTRAL, fontsize=10)
    ax.set_xticks(range(len(Ks))); ax.set_xticklabels(Ks)
    ax.set_xlabel("distillation steps $K$"); ax.set_ylabel("global model accuracy")
    ax.set_ylim(0.4, 0.85)
    ax.legend(loc="lower left", frameon=False)
    fig.savefig(os.path.join(OUT, "fig_ksweep.pdf")); plt.close(fig)

# ======================================================================
# FIG. alignment — basin source spectrum at fixed heterogeneity.
# ======================================================================
def fig_alignment():
    rows = load("heifd_017_noprobe_mlp") + load("heifd_mlp_mnist_headline")
    items = [("no_phase0", "no\nalignment"), ("noprobe_raw_union_K20", "no-probe\n(raw)"),
             ("noprobe_dp_avg_eps2_K20", "no-probe\n(DP)"), ("dp_avg_eps2_K20", "DP\nprototypes"),
             ("raw_union_K20", "raw\nprototypes")]
    a = "0.05"
    vals = [avg([r for r in rows if r["N"]=="10" and r["method"]==m and r["alpha"]==a], "acc") for m,_ in items]
    cols = [AMBER, BLUE_RAMP[0], BLUE_RAMP[1], BLUE_RAMP[1], BLUE]
    fig, ax = plt.subplots(figsize=(5.6, 3.6))
    ax.bar(range(len(items)), vals, color=cols, width=0.66)
    for i, v in enumerate(vals):
        ax.text(i, v+0.015, f"{v:.2f}", ha="center", va="bottom", fontsize=10)
    ax.set_xticks(range(len(items))); ax.set_xticklabels([l for _,l in items], fontsize=10)
    ax.set_ylim(0, 1.0); ax.set_ylabel("global model accuracy")
    fig.savefig(os.path.join(OUT, "fig_alignment.pdf")); plt.close(fig)

if __name__ == "__main__":
    fig_scaling(); fig_continuum(); fig_necessity(); fig_dpfrontier()
    fig_nscaling(); fig_ksweep(); fig_alignment()
    print("wrote:", sorted(f for f in os.listdir(OUT) if f.endswith(".pdf")))
