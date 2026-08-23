#!/usr/bin/env python3
"""Prove that a cut deleted text and did not rewrite it.

The PIs have read the manuscript. Every new sentence is one they must read
again, so the submission is cut by deleting and moving, never by rewriting.
This script checks that claim paragraph by paragraph.

    scripts/check_subseq.py OLD.tex NEW.tex

Each surviving paragraph is classified.

  identical   byte for byte
  deletions   the new word sequence is a subsequence of the old one
  allowed     a subsequence once the three permitted substitutions are applied
  REWRITTEN   contains words in an order the old paragraph does not have

Only REWRITTEN needs a human. Exit 1 if any paragraph is REWRITTEN.

The three permitted substitutions, and no others:
  1. "the serving party" / "serving party" -> "the server" / "server"
  2. a number that changed against its record (declare with --number OLD=NEW)
  3. a cross-reference retargeted at the report (\\cref{x} -> \\trsee{x})
"""
import argparse
import difflib
import re
import sys

FLOAT = re.compile(
    r"\\begin\{(table\*?|figure\*?|functionality|algorithm|tabular)\}.*?"
    r"\\end\{\1\}", re.S)


def paragraphs(text):
    text = "\n".join(l for l in text.split("\n") if not l.lstrip().startswith("%"))
    text = FLOAT.sub(" <FLOAT> ", text)
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def words(p):
    return re.findall(r"\S+", p)


def normalise(p, subs):
    p = re.sub(r"\bthe serving party\b", "the server", p)
    p = re.sub(r"\bserving party\b", "server", p)
    p = re.sub(r"\\cref\{([^}]+)\}", r"\\trsee{\1}", p)
    for old, new in subs:
        p = p.replace(new, old)
    return p


def is_subsequence(new, old):
    it = iter(old)
    return all(w in it for w in new)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("--number", action="append", default=[],
                    metavar="OLD=NEW", help="a number that changed, with its record")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    subs = [tuple(s.split("=", 1)) for s in a.number]
    O = paragraphs(open(a.old).read())
    N = paragraphs(open(a.new).read())

    tally = {"identical": 0, "deletions": 0, "allowed": 0, "REWRITTEN": 0}
    rewritten = []
    for i, p in enumerate(N):
        if p in O:
            tally["identical"] += 1
            continue
        # the old paragraph this one most plausibly came from
        cand = difflib.get_close_matches(p, O, n=1, cutoff=0.0)
        src = cand[0] if cand else ""
        if is_subsequence(words(p), words(src)):
            tally["deletions"] += 1
            continue
        if is_subsequence(words(normalise(p, subs)), words(normalise(src, subs))):
            tally["allowed"] += 1
            continue
        tally["REWRITTEN"] += 1
        rewritten.append((i, p, src))

    print(f"{a.new}: {len(N)} paragraphs kept of {len(O)}, "
          f"{len(O) - len(N)} deleted outright")
    for k in ("identical", "deletions", "allowed", "REWRITTEN"):
        print(f"  {k:10s} {tally[k]}")
    if rewritten and not a.quiet:
        print("\nthese need a human, with the reason stated:")
        for i, p, src in rewritten:
            print(f"\n--- new paragraph {i} ---\n{p[:400]}")
            print(f"--- closest old ---\n{src[:400]}")
    return 1 if tally["REWRITTEN"] else 0


if __name__ == "__main__":
    sys.exit(main())
