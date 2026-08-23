#!/usr/bin/env python3
"""Make draw.io figure text land at an exact point size in the compiled paper.

The problem this solves: draw.io does not export text at its declared size.
Measured on macOS draw.io desktop, a label declared `fontSize=8` arrives in the
exported PDF at 5.77 pt, a 28% shortfall. Nobody catches that by eye, and the
result is a figure whose labels are smaller than every caption around it.

The mapping is linear:  rendered_pt = K * declared_size * s
where K is a per-install constant (about 0.7216) and s is any scale LaTeX
applies at include time.

Subcommands
-----------
  calibrate                  derive K on this machine and cache it
  plan --target PT           declared fontSize to use in draw.io
  check FIG.pdf --target PT  measure an exported figure
  audit PAPER.pdf            font size histogram of a compiled paper

Requires: PyMuPDF (`import fitz`) and the draw.io desktop app.
"""
import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

CACHE = pathlib.Path(__file__).with_name(".calibration.json")
DEFAULT_K = 0.721625  # measured, macOS draw.io desktop, 2026-08

DRAWIO_CANDIDATES = [
    "/Applications/draw.io.app/Contents/MacOS/draw.io",
    "/opt/draw.io/drawio",
]


def drawio_bin():
    for name in ("drawio", "draw.io"):
        p = shutil.which(name)
        if p:
            return p
    for p in DRAWIO_CANDIDATES:
        if pathlib.Path(p).exists():
            return p
    sys.exit("draw.io desktop not found. Install it, or add it to PATH.")


def need_fitz():
    try:
        import fitz  # noqa: F401
        return fitz
    except ImportError:
        sys.exit("PyMuPDF missing. Install with: python3 -m pip install pymupdf")


def spans(pdf_path):
    """Every text span in a PDF, as (text, rendered_pt, font, page)."""
    fitz = need_fitz()
    out = []
    with fitz.open(pdf_path) as doc:
        for pno, page in enumerate(doc, 1):
            for blk in page.get_text("dict")["blocks"]:
                for line in blk.get("lines", []):
                    for sp in line["spans"]:
                        if sp["text"].strip():
                            out.append((sp["text"], sp["size"], sp["font"], pno))
    return out


def page_width_pt(pdf_path):
    fitz = need_fitz()
    with fitz.open(pdf_path) as doc:
        return doc[0].rect.width


CAL_TEMPLATE = """<mxfile host="app.diagrams.net"><diagram name="c" id="c">
<mxGraphModel dx="800" dy="600" grid="0" page="1" pageScale="1"
 pageWidth="850" pageHeight="1100" math="0"><root>
<mxCell id="0"/><mxCell id="1" parent="0"/>
{cells}
</root></mxGraphModel></diagram></mxfile>"""

CAL_CELL = ('<mxCell id="n{i}" value="CAL{i}" style="text;html=1;fontSize={sz};'
            'fontFamily=Times New Roman;align=left;verticalAlign=top;" vertex="1"'
            ' parent="1"><mxGeometry x="20" y="{y}" width="400" height="{h}"'
            ' as="geometry"/></mxCell>')


def cmd_calibrate(_args):
    probes = [8, 12, 16, 24, 32]
    cells, y = [], 20
    for i, sz in enumerate(probes):
        cells.append(CAL_CELL.format(i=i, sz=sz, y=y, h=sz * 2))
        y += sz * 2 + 20
    with tempfile.TemporaryDirectory() as td:
        src = pathlib.Path(td, "cal.drawio")
        out = pathlib.Path(td, "cal.pdf")
        src.write_text(CAL_TEMPLATE.format(cells="\n".join(cells)))
        subprocess.run([drawio_bin(), "--no-sandbox", "-x", "-f", "pdf",
                        "--crop", "-o", str(out), str(src)],
                       check=True, capture_output=True)
        measured = {}
        for text, size, _font, _pg in spans(out):
            if text.startswith("CAL"):
                measured[probes[int(text[3:])]] = size

    if not measured:
        sys.exit("calibration produced no measurable text")
    ratios = [m / d for d, m in measured.items()]
    k = sum(ratios) / len(ratios)
    spread = max(ratios) - min(ratios)

    print("declared -> rendered")
    for d in sorted(measured):
        print(f"  {d:>3} -> {measured[d]:6.3f} pt   ratio {measured[d]/d:.5f}")
    print(f"\nK = {k:.6f}   (spread {spread:.5f})")
    if spread > 0.01:
        print("WARNING: ratio is not constant. The mapping may not be linear "
              "on this install. Rely on `check`, not `plan`.")
    CACHE.write_text(json.dumps({"K": k, "probes": measured}, indent=2))
    print(f"cached to {CACHE}")


def load_k():
    if CACHE.exists():
        return json.loads(CACHE.read_text())["K"]
    print(f"note: no calibration cache, using default K={DEFAULT_K}. "
          "Run `figfont.py calibrate` for this machine.", file=sys.stderr)
    return DEFAULT_K


def cmd_plan(args):
    k = load_k()
    s = 1.0
    if args.pdf and args.latex_width_pt:
        w = page_width_pt(args.pdf)
        s = args.latex_width_pt / w
        print(f"exported width {w:.2f} pt, LaTeX target {args.latex_width_pt:.2f} pt")
        print(f"LaTeX will scale by s = {s:.4f}")
        if abs(s - 1.0) > 0.001:
            print("  (this is why width=\\columnwidth silently shrinks labels)")
    declared = args.target / (k * s)
    print(f"\ntarget {args.target} pt in the paper")
    print(f"  -> set fontSize={declared:.2f} in draw.io")
    if abs(s - 1.0) < 1e-9:
        print(f"  -> include with \\includegraphics{{...}}, no width option")
    else:
        print(f"  -> include with \\includegraphics[width={args.latex_width_pt:.2f}pt]{{...}}")
    print("\nVerify after export:")
    print(f"  figfont.py check <fig>.pdf --target {args.target}"
          + (f" --latex-width-pt {args.latex_width_pt}" if args.latex_width_pt else ""))


def cmd_check(args):
    s = 1.0
    w = page_width_pt(args.pdf)
    if args.latex_width_pt:
        s = args.latex_width_pt / w
    found = spans(args.pdf)
    if not found:
        sys.exit("no text found in the figure PDF")

    print(f"figure width {w:.2f} pt, LaTeX scale s = {s:.4f}")
    print(f"target {args.target} pt, tolerance {args.tol*100:.0f}%\n")
    bad = 0
    seen = {}
    for text, size, font, _pg in found:
        eff = size * s
        key = round(eff, 2)
        seen.setdefault(key, []).append(text.strip()[:28])
        if abs(eff - args.target) / args.target > args.tol:
            bad += 1
    for eff in sorted(seen):
        off = (eff - args.target) / args.target * 100
        mark = "ok " if abs(off) <= args.tol * 100 else "OFF"
        sample = ", ".join(seen[eff][:3])
        print(f"  {mark} {eff:6.2f} pt  ({off:+5.1f}%)  {len(seen[eff]):>3} span(s)  {sample}")
    print(f"\n{bad} of {len(found)} spans outside tolerance.")
    if bad:
        k = load_k()
        print(f"Fix: multiply every fontSize by {args.target/ (max(seen)*1.0):.4f} "
              f"or re-plan with `figfont.py plan --target {args.target}`.")
        print(f"Do NOT fix this by changing the \\includegraphics width.")
    return 1 if bad else 0


def cmd_audit(args):
    found = spans(args.pdf)
    hist = {}
    for _t, size, _f, _p in found:
        hist[round(size, 1)] = hist.get(round(size, 1), 0) + 1
    print(f"{args.pdf}: {len(found)} spans\n")
    print("  pt     count  bar")
    for size in sorted(hist):
        n = hist[size]
        print(f"  {size:5.1f}  {n:>5}  {'#' * min(60, n // max(1, len(found)//200 or 1))}")
    print("\nBody text is the tallest bar. Figure labels should sit at the")
    print("caption size. Any lone small cluster is a figure with wrong fonts.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("calibrate", help="derive K on this machine").set_defaults(fn=cmd_calibrate)

    p = sub.add_parser("plan", help="declared fontSize for a target point size")
    p.add_argument("--target", type=float, required=True, help="wanted pt in the paper")
    p.add_argument("--pdf", help="already-exported figure, to compute the LaTeX scale")
    p.add_argument("--latex-width-pt", type=float, help="width you will include at")
    p.set_defaults(fn=cmd_plan)

    p = sub.add_parser("check", help="measure an exported figure")
    p.add_argument("pdf")
    p.add_argument("--target", type=float, required=True)
    p.add_argument("--latex-width-pt", type=float)
    p.add_argument("--tol", type=float, default=0.05)
    p.set_defaults(fn=cmd_check)

    p = sub.add_parser("audit", help="font size histogram of a compiled paper")
    p.add_argument("pdf")
    p.set_defaults(fn=cmd_audit)

    a = ap.parse_args()
    sys.exit(a.fn(a) or 0)


if __name__ == "__main__":
    main()
