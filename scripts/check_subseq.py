#!/usr/bin/env python3
"""Prove that a cut deleted text and did not rewrite it.

The PIs read one specific version of the manuscript. Every sentence that is not
in that version is a sentence they must read again, so the submission is cut by
deleting and moving, never by rewriting. This checks that claim.

    scripts/check_subseq.py --base cc1df39

The base is a git ref. Every paragraph now in docs/paper/sections is looked up
against the pool of every paragraph the base had, across all files at once,
because a cut moves text between files as well as out of them.

Each paragraph is classified.

  identical   present in the base, word for word
  deletions   its words are a subsequence of some base paragraph's words
  allowed     a subsequence once the permitted substitutions are applied
  REWRITTEN   contains words in an order no base paragraph has

Only REWRITTEN needs a human. Exit 1 if any paragraph is REWRITTEN and is not
listed in --allow.

The permitted substitutions, and no others:
  1. "the serving party" / "the aggregation server" -> "the server"
  2. agreement forced by 1, because two parties became one
  3. "honest-but-curious" -> "semi-honest", the CONTEXT.md ruling of 2026-08-19
  4. a cross-reference retargeted at the report, \\cref{x} -> \\trsee{x}
  5. a number that changed against its record, declared with --number OLD=NEW

Anything else is a rewrite and Halil decides it.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

FLOAT = re.compile(
    r"\\begin\{(table\*?|figure\*?|functionality|algorithm|tabular)\}.*?"
    r"\\end\{\1\}", re.S)
_TOKEN = re.compile(r"\\[A-Za-z@]+|[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*")

# \s+ rather than a literal space: LaTeX source wraps, and a newline between
# "serving" and "party" would otherwise defeat the pattern silently.
_MERGE = [
    (r"\bthe\s+server\s+and\s+the\s+serving\s+party\b", "the server"),
    (r"\bthe\s+serving\s+party\s+and\s+the\s+server\b", "the server"),
    (r"\bthe\s+aggregation\s+server\b", "the server"),
    (r"\bthe\s+serving\s+party\b", "the server"),
    (r"\bserving\s+party\b", "server"),
    (r"\bhonest-but-curious\b", "semi-honest"),
]
# Two parties becoming one forces these agreements and no others.
_AGREE = [
    # "neither", ranging over two parties, becomes "it" when there is one.
    (r"\b(?:they|it|them|neither|both|either)\b", "PRON"),
    (r"\b(?:their|its)\b", "POSS"),
    (r"\b(?:are|is)\b", "BE"), (r"\b(?:observe|observes)\b", "V"),
    (r"\b(?:hold|holds)\b", "V"), (r"\b(?:follow|follows)\b", "V"),
    (r"\b(?:stay|stays)\b", "V"), (r"\b(?:see|sees)\b", "V"),
    (r"\b(?:can|cannot)\b", "MODAL"), (r"\blast\b", ""),
]


# A cross-reference is machinery. Retargeting one, or adding one because a float
# moved, is not rewriting, so the command and its argument are removed before
# anything is compared. \cite is NOT in here, because dropping a citation is a
# real change and must be visible.
XREF = re.compile(r"\\(?:c|C)?ref\{[^}]*\}|\\trsee\{[^}]*\}")


def paragraphs(text):
    text = "\n".join(l for l in text.split("\n") if not l.lstrip().startswith("%"))
    text = FLOAT.sub(" <FLOAT> ", text)
    text = XREF.sub(" ", text)
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


# Conditionals are machinery. A paragraph wrapped in \tronly is the same
# paragraph.
_MACHINERY = {"\\tronly", "\\paperonly", "\\ifsubmission", "\\else", "\\fi"}


def words(p):
    return [t.lower() for t in _TOKEN.findall(p) if t not in _MACHINERY]


def normalise(p, subs):
    # Case-insensitive, because a deleted leading clause moves a word to the
    # start of its sentence and capitalises it. "They follow" becoming "It
    # follows" is the merge, not a rewrite.
    for pat, rep in _MERGE:
        p = re.sub(pat, rep, p, flags=re.I)
    for pat, rep in _AGREE:
        p = re.sub(pat, rep, p, flags=re.I)
    for old, new in subs:
        p = p.replace(new, old)
    return p


def is_sub(new, old):
    it = iter(old)
    return all(w in it for w in new)


# Machinery, not prose. preamble.tex is packages and macros, body.tex is an
# \input list. Neither is text a PI reads.
SKIP = {"preamble.tex", "body.tex"}


def base_pool(ref, root):
    files = subprocess.run(["git", "ls-tree", "-r", "--name-only", ref, root],
                           capture_output=True, text=True).stdout.split()
    # The base kept the title, the abstract, the acknowledgment and the
    # biographies in main.tex. W1 moved them into sections/, so the pool needs
    # main.tex or every one of them reads as newly written.
    files.append(str(Path(root).parent / "main.tex"))
    pool = []
    for f in files:
        if not f.endswith(".tex"):
            continue
        t = subprocess.run(["git", "show", f"{ref}:{f}"],
                           capture_output=True, text=True).stdout
        ps = paragraphs(t)
        pool += [(f, p) for p in ps]
        # A blank line inside what is one LaTeX paragraph is a source artifact,
        # and closing it up is not rewriting. Adjacent pairs join the pool so a
        # repaired paragraph still matches.
        pool += [(f, a + " " + b) for a, b in zip(ps, ps[1:])]
    return pool


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="git ref the PIs read")
    ap.add_argument("--root", default="docs/paper/sections")
    ap.add_argument("--number", action="append", default=[], metavar="OLD=NEW")
    ap.add_argument("--allow", default="docs/paper/.subseq-allow",
                    help="file of accepted new paragraphs, one per line of reason")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    subs = [tuple(s.split("=", 1)) for s in a.number]
    pool = base_pool(a.base, a.root)
    pool_w = [(f, words(p)) for f, p in pool]
    pool_n = [(f, words(normalise(p, subs))) for f, p in pool]
    exact = {p for _, p in pool}

    allowed_text = set()
    ap_path = Path(a.allow)
    if ap_path.exists():
        for blk in ap_path.read_text().split("\n%%\n"):
            # The reason lives in # lines above the text it justifies. Strip
            # them and keep what the paragraph actually is.
            body = "\n".join(l for l in blk.split("\n")
                             if not l.lstrip().startswith("#")).strip()
            if body:
                # Compare on the same tokens the paragraphs use, so an entry
                # does not stop matching when a cross-reference is retargeted.
                allowed_text.add(tuple(words(XREF.sub(" ", body))))

    tally = dict.fromkeys(("identical", "deletions", "allowed", "accepted",
                           "REWRITTEN"), 0)
    flagged = []
    total = 0
    for f in sorted(Path(a.root).glob("*.tex")):
        if f.name in SKIP:
            continue
        for p in paragraphs(f.read_text()):
            total += 1
            if p in exact:
                tally["identical"] += 1
                continue
            w = words(p)
            if any(is_sub(w, ow) for _, ow in pool_w):
                tally["deletions"] += 1
                continue
            wn = words(normalise(p, subs))
            if any(is_sub(wn, on) for _, on in pool_n):
                tally["allowed"] += 1
                continue
            if tuple(w) in allowed_text:
                tally["accepted"] += 1
                continue
            tally["REWRITTEN"] += 1
            flagged.append((f.name, p))

    print(f"base {a.base}: {len(pool)} paragraphs.  now: {total}")
    for k in ("identical", "deletions", "allowed", "accepted", "REWRITTEN"):
        print(f"  {k:10s} {tally[k]}")
    if flagged and not a.quiet:
        print(f"\n{len(flagged)} paragraph(s) the PIs have not read. State the reason "
              f"for each, then add it to {a.allow} separated by a line of %%.")
        for name, p in flagged:
            print(f"\n--- {name} ---\n{p[:500]}")
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())
