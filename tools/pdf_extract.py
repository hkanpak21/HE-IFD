"""Extract text from a PDF + search for paragraphs containing given keywords.

Usage:
    python tools/pdf_extract.py <PDF_PATH> "<KEYWORDS_COMMA_SEPARATED>" [--context N]

Prints, for each keyword, every paragraph (line) that contains it, with N lines
of context before/after (default 1). Pure text dump, no paraphrasing.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pypdf


def extract_text(path: Path) -> str:
    reader = pypdf.PdfReader(str(path))
    return "\n\f\n".join(page.extract_text() or "" for page in reader.pages)


def search(text: str, keywords: list[str], context: int = 1) -> None:
    lines = text.splitlines()
    for kw in keywords:
        kw_lc = kw.lower()
        hits = [i for i, ln in enumerate(lines) if kw_lc in ln.lower()]
        print(f"\n========== KEYWORD: {kw}  ({len(hits)} hit(s)) ==========")
        last = -context - 1
        for i in hits:
            if i - context > last + context + 1:
                print("---")
            start = max(0, i - context)
            end = min(len(lines), i + context + 1)
            for j in range(start, end):
                marker = ">>" if j == i else "  "
                print(f"{marker} L{j:5d}: {lines[j]}")
            last = i


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("pdf")
    p.add_argument("keywords", help="comma-separated keywords")
    p.add_argument("--context", type=int, default=1)
    p.add_argument("--dump", action="store_true", help="dump full text and exit")
    args = p.parse_args()
    text = extract_text(Path(args.pdf))
    if args.dump:
        sys.stdout.write(text)
        return
    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    search(text, keywords, context=args.context)


if __name__ == "__main__":
    main()
