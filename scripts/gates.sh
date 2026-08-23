#!/usr/bin/env bash
# Every gate the plan sets, in one command. Run from the repo root.
#   scripts/gates.sh
set -uo pipefail
P=docs/paper

# Numbers that changed against a record, declared so the subsequence checker
# does not read a corrected measurement as a rewrite. Table IV moved to the
# whole CIFAR-10 test set on 2026-08-23, jobs 1593568 to 1593571.
NUM=(--number 0.948=0.949 --number 0.962=0.963 --number 0.569=0.570
     --number 0.950=0.952 --number 0.964=0.966 --number 0.014=0.015
     --number 0.943=0.947 --number=-0.005=-0.003 --number 0.399=0.397
     --number 0.952=0.953 --number 0.959=0.961 --number 0.005=0.003)

pages () { python3 -c "
import subprocess,sys
print(len([p for p in subprocess.run(['pdftotext',sys.argv[1],'-'],capture_output=True,text=True).stdout.split(chr(12)) if p.strip()]))" "$1"; }

echo "1  length"
echo "     submission $(pages $P/main.pdf) pages, target 10"
echo "     report     $(pages $P/main-tr.pdf) pages, no limit"
echo "2  prose budget"; python3 scripts/budget.py | tail -1 | sed 's/^/     /'
echo "3  nothing rewritten, submission"
python3 scripts/check_subseq.py --base cc1df39 "${NUM[@]}" --quiet | sed 's/^/     /'
echo "3b nothing rewritten, report"
python3 scripts/check_subseq.py --base cc1df39 --view report "${NUM[@]}" --quiet | sed 's/^/     /'
echo "4  the two documents agree"; python3 scripts/check_split.py $P | sed 's/^/     /'
echo "5  bibliography"
echo "     submission $(grep -c '^\\bibitem' $P/main.bbl) keys, report $(grep -c '^\\bibitem' $P/main-tr.bbl)"
echo "6  both compile"
for d in main main-tr; do
  echo "     $d cite=$(grep -c 'Citation.*undefined' $P/$d.log) ref=$(grep -c 'Reference.*undefined' $P/$d.log) overfull=$(grep -c Overfull $P/$d.log) err=$(grep -c '^!' $P/$d.log)"
done
echo "7  voice, on the resolved submission view"
python3 scripts/lint_view.py 2>&1 | grep -E "error\(s\)" | sed 's/^/     /'
echo "8  figure text at the caption size"
for f in fig_protocol fig_trends; do
  echo "     $f $(python3 $P/figures/figfont.py check $P/figures/$f.pdf --target 8 2>&1 | grep -o '[0-9]* of [0-9]* spans outside tolerance')"
done
echo "9  the arXiv placeholder is still there and must not be submitted"
echo "     $(grep -c 'XXXX.XXXXX' $P/refs.bib) occurrence in refs.bib"
