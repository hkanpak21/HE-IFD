#!/usr/bin/env bash
# One command that says whether the serving re-measurement has landed, and if it
# has, what to do about it. Read-only on VALAR: squeue, sacct, and cat.
#
#   scripts/valar_result.sh            check once, print, write the memo if done
#   scripts/valar_result.sh --watch    check every 5 minutes until every job ends
#
# The decision branches are written down before the numbers arrive, so that when
# they arrive the action is already chosen and nobody argues with a result.
set -uo pipefail
cd "$(dirname "$0")/.."
JOBS="fhe_serve_index|fhe_serve_btp|fhe_serve_tournament"
MEMO="docs/notes/valar-decision-$(date +%Y-%m-%d).md"
REMOTE=/scratch/hkanpak21/HE_IFD

ssh_valar () { timeout 60 ssh -o ConnectTimeout=20 -o BatchMode=yes valar "$@" 2>/dev/null; }

check () {
  if ! ssh_valar true; then
    echo "VALAR unreachable. The Koc VPN is the usual cause and nothing here"
    echo "touches ~/.ssh in response to it."
    return 2
  fi
  RUNNING=$(ssh_valar "squeue -u hkanpak21 -h -o '%i %j %T %M'" | grep -E "$JOBS" || true)
  RECENT=$(ssh_valar "sacct -X -u hkanpak21 --starttime=\$(date -d '12 hours ago' +%FT%T) \
           -o JobID,JobName%24,State,Elapsed,ExitCode -n" | grep -E "$JOBS" || true)
  echo "== still running =="; [ -n "$RUNNING" ] && echo "$RUNNING" || echo "  none"
  echo "== last 12 hours =="; [ -n "$RECENT" ] && echo "$RECENT" || echo "  none"
  [ -n "$RUNNING" ] && return 1 || return 0
}

collect () {
  echo "collecting logs and any CSV the jobs wrote"
  mkdir -p results/fhe_serve/runs
  ssh_valar "cd $REMOTE && ls -1 results/fhe_serve/runs/*.out 2>/dev/null | tail -8" | while read -r f; do
    [ -z "$f" ] && continue
    ssh_valar "cd $REMOTE && cat '$f'" > "results/fhe_serve/runs/$(basename "$f")" 2>/dev/null \
      && echo "  pulled $(basename "$f")"
  done
  for c in argmax_index.csv argmax_btp.csv; do
    ssh_valar "cd $REMOTE && test -f results/fhe_serve/$c && cat results/fhe_serve/$c" \
      > "/tmp/$c" 2>/dev/null
    if [ -s "/tmp/$c" ]; then cp "/tmp/$c" "results/fhe_serve/$c"; echo "  pulled $c"; fi
  done
}

write_memo () {
python3 - "$MEMO" <<'PY'
import csv, os, subprocess, sys
memo = sys.argv[1]
def state(job):
    try:
        o = subprocess.run(["bash","-c",
            f"timeout 60 ssh -o ConnectTimeout=20 -o BatchMode=yes valar "
            f"\"sacct -X -u hkanpak21 --starttime=\\$(date -d '12 hours ago' +%FT%T) "
            f"-o JobName%24,State -n\" 2>/dev/null | grep {job} | tail -1"],
            capture_output=True, text=True).stdout.split()
        return o[1] if len(o) > 1 else "NOT RUN"
    except Exception:
        return "UNKNOWN"

base = {}
p = "results/fhe_serve/argmax_tournament.csv"
if os.path.exists(p):
    for r in csv.DictReader(open(p)):
        base[int(r["C"])] = (float(r["argmax_total_ms"])/1000,
                             float(r["in_refresh_ms"])/1000)

def table(path, label):
    if not os.path.exists(path): return f"No `{path}`. The job wrote no CSV.\n"
    rows = list(csv.DictReader(open(path)))
    if not rows: return f"`{path}` is empty.\n"
    out = [f"Measured, from `{path}`.\n", "| C | total | against the max-only tournament |", "|---|---|---|"]
    for r in rows:
        try:
            C = int(r.get("C", 0)); tot = float(r.get("argmax_total_ms", "nan"))/1000
        except Exception:
            continue
        old = base.get(C, (None, None))[0]
        d = f"{tot-old:+.1f} s ({100*(tot-old)/old:+.0f} %)" if old else "no baseline"
        out.append(f"| {C} | {tot:.1f} s | {d} |")
    return "\n".join(out) + "\n"

idx, btp = state("fhe_serve_index"), state("fhe_serve_btp")
L = []
L.append("# The serving re-measurement, and what it decides\n")
L.append("Written by `scripts/valar_result.sh`. The branches below were fixed")
L.append("before the numbers arrived.\n")
L.append(f"Index extraction job: **{idx}**.  Bootstrapping job: **{btp}**.\n")

L.append("## The argmax index\n")
L.append("The method reduces the logits to an argmax index. Both shipped")
L.append("benchmarks compute the maximum logit instead, so the reported latency")
L.append("omits the index step and the exactness claim is about the max.\n")
if idx == "COMPLETED":
    L.append(table("results/fhe_serve/argmax_index.csv", "index"))
    L.append("**Act on it.** The report states the index cost and stops calling the")
    L.append("figure a lower bound. If the total moved by more than a few per cent,")
    L.append("the abstract's 31.5 to 113.2 s changes, and that is submission text and")
    L.append("Halil's call. If the decoded index is not exact, the claim that the")
    L.append("encrypted argmax is exact narrows to the maximum.\n")
else:
    L.append(f"**Not measured, state {idx}.** The report says plainly that the")
    L.append("benchmark computes the maximum and that the reported latency is a lower")
    L.append("bound for the specified circuit. Nothing in the submission changes, and")
    L.append("the honest sentence is already written.\n")

L.append("## Server-side bootstrapping\n")
L.append("The reported latency was measured with collective refresh. The per-query")
L.append("traffic prices the bootstrapping-key design the protocol specifies. The")
L.append("specified design has never been timed.\n")
if btp == "COMPLETED":
    L.append(table("results/fhe_serve/argmax_btp.csv", "btp"))
    L.append("**Act on it.** Both figures now describe one design. If the new latency")
    L.append("is close to the old, the correction paragraph in Section V collapses to")
    L.append("one sentence. If it is materially slower, the abstract's number is wrong")
    L.append("for the specified protocol and must either change or be labelled, which")
    L.append("is Halil's call. Note the ring degree: the timings are at 2^15 and the")
    L.append("bootstrapping keys at 2^16, so say which was used.\n")
else:
    L.append(f"**Not measured, state {btp}.** The report already says the reported")
    L.append("latency belongs to the collective-refresh variant and is not claimed for")
    L.append("the specified one. That sentence stands and nothing else is needed.\n")

L.append("## If both failed\n")
L.append("Nothing in either document becomes wrong. Both gaps are already stated in")
L.append("the report as gaps. The cost of leaving them is one paragraph a reviewer")
L.append("may probe, not a claim that fails.\n")
open(memo, "w").write("\n".join(L) + "\n")
print(f"memo written to {memo}")
PY
}

if [ "${1:-}" = "--watch" ]; then
  while true; do
    check; rc=$?
    [ $rc -eq 2 ] && exit 2
    [ $rc -eq 0 ] && break
    echo "still running, checking again in 5 minutes"; sleep 300
  done
else
  check; rc=$?
  [ $rc -eq 2 ] && exit 2
  if [ $rc -eq 1 ]; then echo; echo "Jobs still running. No memo written."; exit 1; fi
fi
collect
write_memo
