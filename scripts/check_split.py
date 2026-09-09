#!/usr/bin/env python3
"""Check the invariant that makes \\trsee sound.

The paper cites the technical report by section number, using its own \\ref on
a shared label. That is only correct while every section label carries the same
number in both documents. This script compiles nothing. It reads the two .aux
files and compares.

    scripts/check_split.py docs/paper

Exit 1 if any shared label disagrees, or if a label the paper points at with
\\trsee is missing from the report.
"""
import re
import budget
import sys
from pathlib import Path


def labels(aux):
    """label -> printed number, from \\newlabel{name}{{number}{page}...}."""
    out = {}
    for m in re.finditer(r"\\newlabel\{([^}]+)\}\{\{([^}]*)\}", aux):
        out[m.group(1)] = m.group(2)
    return out


def main(root):
    root = Path(root)
    a, b = root / "main.aux", root / "main-tr.aux"
    for f in (a, b):
        if not f.exists():
            print(f"{f} missing. Compile both drivers first.", file=sys.stderr)
            return 1
    pa, pb = labels(a.read_text()), labels(b.read_text())

    shared = sorted(k for k in pa if k in pb and k.startswith("sec:"))
    bad = [(k, pa[k], pb[k]) for k in shared if pa[k] != pb[k]]

    # every \trsee target must exist in the report
    tex = "\n".join(p.read_text() for p in (root / "sections").glob("*.tex"))
    targets = sorted(set(re.findall(r"\\trsee\{([^}]+)\}", tex)))
    missing = [t for t in targets if t not in pb]

    print(f"section labels shared by both documents: {len(shared)}")
    print(f"\\trsee targets: {len(targets)}")

    for k, x, y in bad:
        print(f"  MISMATCH {k}: paper says {x}, report says {y}")
    for t in missing:
        print(f"  MISSING  {t} is a \\trsee target and the report has no such label")

    # a \trsee target that is not a section is a pointer we cannot keep stable
    notsec = [t for t in targets if not t.startswith("sec:")]
    for t in notsec:
        print(f"  SCOPE    {t} is not a section label. Point at a section, never a subsection")

    # a subsection with exactly one run-in prints a lone "a)" in IEEEtran, which
    # reads as a heading with nothing to distinguish itself from. It happens when
    # a subsection's other run-ins are conditional, so it must be checked per
    # document rather than on the source.
    lone = []
    for view, drop, keep in (("submission", "tronly", "paperonly"),
                             ("report", "paperonly", "tronly")):
        for f in sorted((root / "sections").glob("*.tex")):
            if f.name in ("preamble.tex", "body.tex"):
                continue
            t = budget.strip_conditional(f.read_text(), drop)
            t = budget.unwrap(t, keep)
            t = "\n".join(l for l in t.split("\n") if not l.lstrip().startswith("%"))
            cur, seen = None, {}
            for m in re.finditer(r"\\subsection\{([^}]*)\}|\\paragraph\{([^}]*)\}", t):
                if m.group(1):
                    cur = m.group(1)
                    seen.setdefault(cur, [])
                elif cur:
                    seen[cur].append(m.group(2))
            lone += [(view, k, v[0]) for k, v in seen.items() if len(v) == 1]
    for view, sub, run in lone:
        print(f"  LONE     {view}: \"{sub}\" has one run-in, \"{run}\". "
              f"Drop it or give the subsection a second one")

    n = len(bad) + len(missing) + len(notsec) + len(lone)
    print("OK" if n == 0 else f"{n} problem(s)")
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "docs/paper"))
