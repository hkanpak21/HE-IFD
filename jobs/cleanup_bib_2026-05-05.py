"""
One-shot bib cleanup pass.

  1. Drop all entries whose key never appears in any \cite call across the .tex tree.
  2. Normalise a handful of overlong venue strings (IJCAI, ACM CCS, ICML).
  3. Append Dockhorn et al. 2022 (DPDM) and Viand et al. 2023 (vFHE SoK) which
     the rewrite per `reports/2026-05-05_methodology_pivot.md` will need.

Author lists and author-name shortening are left untouched per user instruction.
"""
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
BIB = os.path.join(ROOT, "references.bib")

# 1. Identify which keys are cited in any .tex file in this directory.
cited = set()
cite_re = re.compile(r"\\cite[a-zA-Z]*\{([^}]+)\}")
for fn in os.listdir(ROOT):
    if fn.endswith(".tex"):
        with open(os.path.join(ROOT, fn)) as f:
            for m in cite_re.finditer(f.read()):
                for key in m.group(1).split(","):
                    cited.add(key.strip())

# 2. Walk the bib, splitting into entries.
with open(BIB) as f:
    text = f.read()

# Split on top-level @ at column 0.
entry_re = re.compile(r"^@(\w+)\{([^,\s]+),", re.MULTILINE)

# Find all entry start positions, then slice between them.
starts = [m.start() for m in entry_re.finditer(text)] + [len(text)]
entries = []
for i in range(len(starts) - 1):
    chunk = text[starts[i] : starts[i + 1]]
    m = entry_re.match(chunk)
    if not m:
        continue
    typ, key = m.group(1), m.group(2)
    entries.append((typ, key, chunk))

orig_count = len(entries)
preamble = text[: starts[0]] if starts and starts[0] != 0 else ""

# 3. Filter out non-cited entries.
kept = [e for e in entries if e[1] in cited]
dropped = [e for e in entries if e[1] not in cited]

# 4. Apply venue normalisation across the surviving entries only.
VENUE_FIXES = [
    # match the multiline overlong forms our grep above found.
    (re.compile(r"booktitle\s*=\s*\{Proceedings of the \d+(?:st|nd|rd|th)? International Joint Conference on Artificial Intelligence(?:[^}]*)\}", re.DOTALL),
     "booktitle = {IJCAI}"),
    (re.compile(r"booktitle\s*=\s*\{Proceedings of the \d+(?:st|nd|rd|th)? ACM SIGSAC Conference on Computer and Communications Security(?:[^}]*)\}", re.DOTALL),
     "booktitle = {ACM CCS}"),
    (re.compile(r"booktitle\s*=\s*\{Proceedings of the \d+(?:st|nd|rd|th)? International Conference on Machine Learning(?:[^}]*)\}", re.DOTALL),
     "booktitle = {ICML}"),
    (re.compile(r"booktitle\s*=\s*\{Proceedings of the \d+(?:st|nd|rd|th)? ACM Workshop on Artificial Intelligence and Security(?:[^}]*)\}", re.DOTALL),
     "booktitle = {AISec}"),
    (re.compile(r"booktitle\s*=\s*\{Advances in Neural Information Processing Systems\s*\(NeurIPS\)\}"),
     "booktitle = {NeurIPS}"),
    (re.compile(r"journal\s*=\s*\{Proceedings on Privacy Enhancing Technologies\}"),
     "journal = {PoPETs}"),
    (re.compile(r"journal\s*=\s*\{IEEE Transactions on Information Forensics and Security\}"),
     "journal = {IEEE TIFS}"),
]

new_entries = []
fix_log = []
for typ, key, chunk in kept:
    new = chunk
    for pat, repl in VENUE_FIXES:
        if pat.search(new):
            new = pat.sub(repl, new)
            fix_log.append((key, repl))
    new_entries.append((typ, key, new))

# 5. Append Dockhorn DPDM + Viand verifiable HE SoK.
APPENDED = """
@article{dockhorn2022dpdm,
  title     = {Differentially Private Diffusion Models},
  author    = {Dockhorn, Tim and Cao, Tianshi and Vahdat, Arash and Kreis, Karsten},
  journal   = {Transactions on Machine Learning Research (TMLR)},
  year      = {2022},
  url       = {https://arxiv.org/abs/2210.09929}
}

@inproceedings{viand2023verifiable,
  title     = {{SoK}: Fully Homomorphic Encryption Compilers and Verifiable Computation},
  author    = {Viand, Alexander and Knabenhans, Christian and Hithnawi, Anwar},
  booktitle = {IEEE S\\&P},
  year      = {2023},
  url       = {https://arxiv.org/abs/2301.07041}
}
"""

# 6. Reassemble.
out = preamble + "".join(c for _, _, c in new_entries) + APPENDED
with open(BIB, "w") as f:
    f.write(out)

print(f"original entries: {orig_count}")
print(f"kept entries:     {len(kept)}")
print(f"dropped entries:  {len(dropped)}")
print(f"venue fixes applied:")
for key, repl in fix_log:
    print(f"  {key:40s} -> {repl}")
print(f"appended: dockhorn2022dpdm, viand2023verifiable")
print(f"final entry count: {len(kept) + 2}")
print()
print("dropped keys:")
for _, key, _ in dropped:
    print(f"  {key}")
