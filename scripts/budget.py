#!/usr/bin/env python3
"""Prose words per section, for the document that is being cut.

\\tronly blocks belong to the report, so counting them tells you nothing about
the submission's length. This strips them, strips floats, strips comments, and
prints what remains against the target.

    scripts/budget.py            the submission
    scripts/budget.py --report   the report
"""
import argparse
import re
from pathlib import Path

FLOATS = ["table\\*", "table", "figure\\*", "figure", "functionality", "algorithm"]
ORDER = ["intro", "prelim", "method", "security", "experiments", "related",
         "conclusion"]
# Page targets ruled 2026-08-23, at about 900 prose words per page.
TARGET = {"intro": 810, "prelim": 540, "method": 1890, "security": 513,
          "experiments": 1000, "related": 540, "conclusion": 270}


def strip_conditional(t, name):
    """Remove \\name{...} and its balanced braces."""
    out, i = [], 0
    tag = "\\" + name + "{"
    while True:
        j = t.find(tag, i)
        if j < 0:
            out.append(t[i:])
            return "".join(out)
        out.append(t[i:j])
        d, k = 1, j + len(tag)
        while k < len(t) and d:
            d += (t[k] == "{") - (t[k] == "}")
            k += 1
        i = k


def unwrap(t, name):
    """Keep the body of \\name{...}, drop the wrapper."""
    tag = "\\" + name + "{"
    out, i = [], 0
    while True:
        j = t.find(tag, i)
        if j < 0:
            out.append(t[i:])
            return "".join(out)
        out.append(t[i:j])
        d, k = 1, j + len(tag)
        while k < len(t) and d:
            d += (t[k] == "{") - (t[k] == "}")
            k += 1
        out.append(t[j + len(tag):k - 1])
        i = k


def words(path, report):
    t = path.read_text()
    # comments render nothing, so they must not inflate the count
    t = "\n".join(l for l in t.split("\n") if not l.lstrip().startswith("%"))
    t = re.sub(r"(?<!\\)%.*", "", t)
    drop, keep = ("paperonly", "tronly") if report else ("tronly", "paperonly")
    t = strip_conditional(t, drop)
    t = unwrap(t, keep)
    for e in FLOATS:
        t = re.sub(r"\\begin\{" + e + r"\}.*?\\end\{" + e + r"\}", "", t, flags=re.S)
    return len(t.split())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--root", default="docs/paper/sections")
    a = ap.parse_args()
    root = Path(a.root)
    print(f"{'section':12s} {'words':>6s} {'target':>7s} {'to cut':>7s}")
    tot = cut = 0
    for f in ORDER:
        p = root / f"{f}.tex"
        if not p.exists():
            continue
        n = words(p, a.report)
        tot += n
        if a.report:
            print(f"{f:12s} {n:6d}")
        else:
            t = TARGET[f]
            cut += n - t
            print(f"{f:12s} {n:6d} {t:7d} {n - t:7d}")
    if a.report:
        print(f"{'TOTAL':12s} {tot:6d}")
    else:
        print(f"{'TOTAL':12s} {tot:6d} {sum(TARGET.values()):7d} {cut:7d}")


if __name__ == "__main__":
    main()
