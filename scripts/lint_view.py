#!/usr/bin/env python3
"""Run the writing linter on what each document actually prints.

lint.py cannot see past \\tronly, so it lints report-only text as if it were in
the submission and reports orphan labels for floats that moved. This writes the
resolved view of every section to a scratch directory and lints that.

    scripts/lint_view.py            the submission
    scripts/lint_view.py --report   the report
"""
import argparse
import re
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("budget", HERE / "budget.py")
budget = importlib.util.module_from_spec(spec)
spec.loader.exec_module(budget)

LINT = Path.home() / ".claude/skills/research/scripts/lint.py"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--root", default="docs/paper/sections")
    a = ap.parse_args()
    drop, keep = ("paperonly", "tronly") if a.report else ("tronly", "paperonly")
    out = Path(tempfile.mkdtemp(prefix="lintview-"))
    files = []
    for f in sorted(Path(a.root).glob("*.tex")):
        if f.name in ("preamble.tex", "body.tex", "frontmatter.tex", "backmatter.tex"):
            continue
        t = budget.strip_conditional(f.read_text(), drop)
        t = budget.unwrap(t, keep)
        (out / f.name).write_text(t)
        files.append(str(out / f.name))
    print(f"linting the {'report' if a.report else 'submission'} view\n")
    rc = subprocess.run([sys.executable, str(LINT), "--paper", *files]).returncode
    return rc + house(files)


# Words the PIs have asked us to stop using in this paper. The global linter
# does not know them, and every Overleaf round trip has reinstated some of
# them, so they are checked here rather than remembered.
HOUSE = [
    (r"\bsits?\b(?!\s+at\s+the\s+bottom)", "a location, not a verb. placed, comes after, is within"),
    (r"\bbuys?\b", "name the price. costs, is the price of, pays for"),
    (r"\bwhich is why\b", "two sentences, or therefore"),
    (r"\bat chance\b", "random guessing"),
    (r"\badds nothing\b", "say what it does not add"),
    (r"(?<!e)\bvery\b", "banned intensifier"),
    (r"\bdoes no better\b", "obtains no greater advantage"),
]


def house(files):
    n = 0
    for path in files:
        for i, line in enumerate(Path(path).read_text().split("\n"), 1):
            if line.lstrip().startswith("%"):
                continue
            for pat, fix in HOUSE:
                if re.search(pat, line):
                    print(f"  {Path(path).name}:{i}  HOUSE  "
                          f"{re.search(pat, line).group(0)!r}: {fix}")
                    n += 1
    if n:
        print(f"\n{n} house-style hit(s)")
    return n


if __name__ == "__main__":
    sys.exit(main())
