"""Generate the two results figures from the landed sweep CSV.

Reads results/finetune_increment/results.csv and writes:
  docs/paper/figures/fig_increment.pdf   (headline: head vs HE-IFD per task)
  docs/paper/figures/fig_robust.pdf      (left: A* vs alpha; right: A* vs N)

SANZO palette, no chartjunk, vector PDF for LaTeX. Re-run whenever the CSV
changes (e.g. after the freeze-A re-run). Tasks/configs absent from the CSV are
skipped, so it works on partial data.

Run:  python docs/paper/figures/make_results_figs.py
"""
import csv
import statistics as st
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
CSV = ROOT / "results" / "finetune_increment" / "results.csv"
OUT = Path(__file__).resolve().parent

# SANZO palette (mirrors main.tex)
TAN, BLUE, SAGE, GREY, TERRA = "#C6A87D", "#5B7FA6", "#5B7B6E", "#8B9EA8", "#D4826A"

plt.rcParams.update({
    "font.size": 9, "axes.titlesize": 9, "axes.labelsize": 9,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 150, "savefig.bbox": "tight", "pdf.fonttype": 42,
})

TASKS = [  # slug -> (label, n_classes); plotted in this order if present
    ("ag_news", "AG-News (4)"), ("trec", "TREC (6)"),
    ("dbpedia_14", "DBpedia (14)"), ("banking77", "Banking77 (77)"),
    ("cifar100", "CIFAR-100 (100)"),
]


def load():
    rows = list(csv.DictReader(open(CSV)))
    for r in rows:
        for k in ("N", "K", "r"):
            r[k] = int(r[k])
        for k in ("alpha", "Astar", "A_central"):
            r[k] = float(r[k])
    return rows


def mean(rows, **f):
    sel = [r for r in rows if all(r[k] == v for k, v in f.items())]
    return (st.mean(x["Astar"] for x in sel),
            st.mean(x["A_central"] for x in sel)) if sel else (None, None)


# Headline numbers, mirroring Table~\ref{tab:headline} (freeze-A, vote-selected,
# three seeds): per task -> (naive sample-weighted average, HE-IFD, centralized).
HEADLINE = {
    "ag_news":    (0.51, 0.75, 0.91),
    "trec":       (0.51, 0.72, 0.95),
    "dbpedia_14": (0.80, 0.93, 0.99),
    "banking77":  (0.39, 0.77, 0.88),
    "cifar100":   (0.47, 0.78, 0.87),
}

FIG_W = 3.4  # shared figure width (in): both paper figures use this so that,
             # included at the same \columnwidth, their text renders at one size.


def fig_increment(_rows=None):
    labels, naive, heifd, ceil = [], [], [], []
    for slug, lab in TASKS:
        if slug not in HEADLINE:
            continue
        n, a, c = HEADLINE[slug]
        labels.append(lab); naive.append(n); heifd.append(a); ceil.append(c)

    x = range(len(labels)); w = 0.38
    fig, ax = plt.subplots(figsize=(FIG_W, 2.6))
    ax.bar([i - w / 2 for i in x], naive, w, label="naive average", color=TAN)
    ax.bar([i + w / 2 for i in x], heifd, w, label="HE-IFD", color=BLUE)
    for i, c in enumerate(ceil):  # centralized reference as a dashed cap per group
        ax.plot([i - w, i + w], [c, c], ls="--", lw=1.1, color=SAGE,
                label="centralized" if i == 0 else None)
    ax.set_xticks(list(x)); ax.set_xticklabels(labels, rotation=28, ha="right")
    ax.set_ylabel("accuracy"); ax.set_ylim(0, 1.0)
    ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.18))
    ax.grid(axis="y", lw=0.4, alpha=0.4)
    fig.savefig(OUT / "fig_increment.pdf")
    print("wrote fig_increment.pdf  tasks:", [l.split("\n")[0] for l in labels])


def fig_robust(rows):
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(5.4, 2.4))

    alphas = sorted({r["alpha"] for r in rows
                     if r["task"] == "dbpedia_14" and r["r"] == 8 and r["N"] == 10})
    ya = [mean(rows, task="dbpedia_14", r=8, N=10, alpha=a)[0] for a in alphas]
    ca = mean(rows, task="dbpedia_14", r=8, N=10, alpha=alphas[-1])[1]
    axL.plot(alphas, ya, "-o", color=BLUE, label="HE-IFD")
    axL.axhline(ca, ls="--", lw=1.1, color=SAGE, label="centralized")
    axL.set_xscale("log"); axL.set_xlabel(r"heterogeneity $\alpha$")
    axL.set_ylabel("accuracy"); axL.set_ylim(0.4, 1.0)
    axL.legend(frameon=False, loc="lower right"); axL.grid(lw=0.4, alpha=0.4)

    Ns = sorted({r["N"] for r in rows
                 if r["task"] == "dbpedia_14" and r["r"] == 8 and r["alpha"] == 0.1})
    yn = [mean(rows, task="dbpedia_14", r=8, N=N, alpha=0.1)[0] for N in Ns]
    cn = mean(rows, task="dbpedia_14", r=8, N=10, alpha=0.1)[1]
    axR.plot(Ns, yn, "-o", color=BLUE, label="HE-IFD")
    axR.axhline(cn, ls="--", lw=1.1, color=SAGE, label="centralized")
    axR.set_xscale("log"); axR.set_xticks(Ns); axR.set_xticklabels(Ns)
    axR.set_xlabel(r"clients $N$"); axR.set_ylim(0.4, 1.0)
    axR.legend(frameon=False, loc="lower right"); axR.grid(lw=0.4, alpha=0.4)

    fig.tight_layout()
    fig.savefig(OUT / "fig_robust.pdf")
    print(f"wrote fig_robust.pdf  alphas={alphas}  Ns={Ns}")


def fig_comm():
    # calculated, not measured: CKKS ring 2^14 -> 8192 slots/ct, 0.5 MiB/ct.
    SLOTS, CT, ROUNDS = 8192, 0.5, 50
    def cts(p):
        return -(-p // SLOTS)                        # ceil
    heifd_ct = cts(150_532)                           # freeze-A adapter + head (RoBERTa)
    full_ct = cts(125_000_000)                        # full RoBERTa-base backbone
    Ns = [10, 50, 100]
    heifd = [n * heifd_ct * CT for n in Ns]           # one round (whole protocol)
    fm_round = [n * full_ct * CT for n in Ns]         # full model, per round
    fm_total = [v * ROUNDS for v in fm_round]         # full model, R rounds (training)
    x = range(len(Ns)); w = 0.27
    fig, ax = plt.subplots(figsize=(FIG_W, 2.6))
    ax.bar([i - w for i in x], fm_total, w, color=TERRA,
           label="full model, %d rounds" % ROUNDS)
    ax.bar(list(x), fm_round, w, color=GREY,
           label="full model, per round")
    ax.bar([i + w for i in x], heifd, w, color=BLUE,
           label="HE-IFD, one round")
    ax.set_yscale("log")
    ax.set_xticks(list(x)); ax.set_xticklabels([f"$N={n}$" for n in Ns])
    ax.set_ylabel("total communication (MiB, log)")
    ax.legend(frameon=False, loc="upper left", ncol=1)
    ax.grid(axis="y", lw=0.4, alpha=0.4)
    fig.savefig(OUT / "fig_comm.pdf")
    print(f"wrote fig_comm.pdf  HE-IFD={heifd[0]:.0f}-{heifd[-1]:.0f}MiB  "
          f"fm/round={fm_round[0]/1024:.0f}-{fm_round[-1]/1024:.0f}GiB  "
          f"fm/{ROUNDS}r={fm_total[0]/1024/1024:.1f}-{fm_total[-1]/1024/1024:.1f}TiB")


if __name__ == "__main__":
    # The two figures used in the paper. fig_increment uses the committed
    # headline numbers (HEADLINE, mirroring tab:headline); fig_comm is computed
    # from the freeze-A ciphertext count. Both share FIG_W so their text renders
    # at one size when included at the same \columnwidth. (fig_robust is retained
    # below but no longer included in the paper.)
    fig_increment()
    fig_comm()
