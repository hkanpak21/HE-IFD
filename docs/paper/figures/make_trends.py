#!/usr/bin/env python3
"""Figure 2 of the paper. Four panels, full width, one record behind each.

    python3 docs/paper/figures/make_trends.py

  (a) accuracy against the number of clients   results/personal_adapter/nsweep.csv
  (b) accuracy against label skew              results/personal_adapter/sensitivity.csv
  (c) accuracy against local steps             results/personal_adapter/sensitivity.csv
  (d) argmax cost against the label space      results/fhe_serve/argmax_tournament.csv
                                               results/fhe_serve/argmax_cost.csv

Panels (a) to (c) replace the sensitivity table. Panel (d) replaces fig_cost.
Both of those move to the technical report.
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import heoft_plot as hp  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
SEL, LOC, DIS = "sel_gp_rarefill", "local", "current"


def rows(p):
    return list(csv.DictReader(open(REPO / p)))


def mean_by(rs, key, mode):
    """mean accuracy over seeds, keyed by one axis, for one mode"""
    acc = defaultdict(list)
    for r in rs:
        if r["mode"] == mode:
            acc[float(r[key])].append(float(r["acc_mean"]))
    return sorted((k, sum(v) / len(v)) for k, v in acc.items())


def line(ax, pts, name, marker):
    x, y = zip(*pts)
    ax.plot(x, y, marker=marker, color=hp.SERIES[name], label=name)


def main():
    ns = rows("results/personal_adapter/nsweep.csv")
    sn = rows("results/personal_adapter/sensitivity.csv")

    fig, ax = hp.panels(4, ratio=0.78, width="text")

    # (a) federation size. One seed, which the table already states.
    for m, name, mk in ((SEL, "selected", "o"), (DIS, "disclosed", "s"),
                        (LOC, "alone", "^")):
        line(ax[0], mean_by(ns, "N", m), name, mk)
    ax[0].set_xscale("log")
    ax[0].set_xticks([10, 20, 50])
    ax[0].set_xticklabels(["10", "20", "50"])
    ax[0].minorticks_off()   # a log axis labels minor ticks as 2x10^1
    ax[0].set_xlabel(r"clients $N$")
    ax[0].set_ylabel("accuracy")
    hp.label(ax[0], "a")

    # (b) label skew, at the default K. Mean over three seeds.
    #
    # sensitivity.csv holds the skew axis at alpha 0.05, 0.30 and 1.00 only. The
    # default cell, alpha = 0.10, is the headline run and lives in
    # stratified/results.csv, three seeds, which is where Table III's 0.789 also
    # comes from. Panel (b) is therefore three-seed means throughout, and panels
    # (a) and (c) are seed 42 throughout, which is the split the old caption
    # already declared.
    hl = [r for r in rows("results/personal_adapter/stratified/results.csv")
          if r["task"] == "dbpedia_14"]
    sk = [r for r in sn if r["K"] == "200"]
    sk += [dict(r, alpha="0.1") for r in hl]
    for m, name, mk in ((SEL, "selected", "o"), (DIS, "disclosed", "s"),
                        (LOC, "alone", "^")):
        line(ax[1], mean_by(sk, "alpha", m), name, mk)
    ax[1].set_xscale("log")
    ax[1].set_xticks([0.05, 0.1, 0.3, 1.0])
    ax[1].set_xticklabels(["0.05", "0.1", "0.3", "1"])
    ax[1].minorticks_off()
    ax[1].set_xlabel(r"label skew $\alpha$")
    hp.label(ax[1], "b")

    # (c) local steps, at the default skew. Seed 42, and its default cell is
    # that seed's value, which is the N=10 row of the client sweep.
    st = [r for r in sn if r["alpha"] == "0.1"]
    st += [dict(r, K="200") for r in ns if r["N"] == "10"]
    for m, name, mk in ((SEL, "selected", "o"), (DIS, "disclosed", "s"),
                        (LOC, "alone", "^")):
        line(ax[2], mean_by(st, "K", m), name, mk)
    ax[2].set_xticks([100, 200, 400])
    ax[2].set_xlabel(r"local steps $K$")
    hp.label(ax[2], "c")

    # (d) what one query costs, against the label space. Both curves are
    # measured, at the label-space sizes of the five tasks. The fold at a
    # hundred classes is 1587 s against the tournament's 113, a factor of 14.
    trn = sorted(rows("results/fhe_serve/argmax_tournament.csv"),
                 key=lambda r: int(r["C"]))
    seq = sorted(rows("results/fhe_serve/argmax_cost.csv"),
                 key=lambda r: int(r["C"]))
    # Distinct colours, because panel (d) measures seconds and the other three
    # measure accuracy. One name for one thing extends to colour.
    for rs, name, mk, lab in ((seq, "pooled", "s", "sequential"),
                              (trn, "cost", "o", "tournament")):
        ax[3].plot([int(r["C"]) for r in rs],
                   [float(r["argmax_total_ms"]) / 1000 for r in rs],
                   marker=mk, color=hp.SERIES[name], label=lab)
    ax[3].set_xscale("log")
    ax[3].set_yscale("log")
    ax[3].set_xticks([4, 14, 100])
    ax[3].set_xticklabels(["4", "14", "100"])
    ax[3].set_yticks([30, 100, 300, 1000])
    ax[3].set_yticklabels(["30", "100", "300", "1000"])
    ax[3].minorticks_off()
    ax[3].set_ylim(18, 2600)   # room at the foot for the legend
    ax[3].set_xlabel("classes")
    ax[3].set_ylabel("seconds per query")
    hp.label(ax[3], "d")

    # Panels (a) to (c) draw the same three series, so they share one legend
    # above the row. Inside any panel it covers data. Panel (d) draws different
    # series and keeps its own, in the corner its curves leave empty.
    h, l = ax[0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", ncol=3, frameon=False,
               bbox_to_anchor=(0.40, 1.17), columnspacing=1.4)
    # Panel (d)'s curves both rise across the panel and leave no free corner, so
    # its legend sits above it, on the same line as the shared one.
    h4, l4 = ax[3].get_legend_handles_labels()
    fig.legend(h4, l4, loc="upper center", ncol=2, frameon=False,
               bbox_to_anchor=(0.86, 1.17), columnspacing=1.2)
    hp.save(fig, "fig_trends.pdf")

    # the numbers the caption and the prose must agree with
    print("\nselected, by axis")
    print("  N     ", [(int(k), round(v, 3)) for k, v in mean_by(ns, "N", SEL)])
    print("  alpha ", [(k, round(v, 3)) for k, v in mean_by(sk, "alpha", SEL)])
    print("  K     ", [(int(k), round(v, 3)) for k, v in mean_by(st, "K", SEL)])


if __name__ == "__main__":
    main()
