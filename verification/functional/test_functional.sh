#!/usr/bin/env bash
# Checks for issue #82: generated files fresh, all 40 cells in the record,
# the real comparison passes, and a deliberately wrong truth table fails.
# Plus issue #120: the derived timing arcs agree with the RTL models and with
# the characterized Liberty, and the recorded corner report has every arc at
# every ratified corner (test_arcs.py).
# Plus issue #138: the committed comparison record is *verified*, never
# rewritten -- `compare.py --check` below is the freshness gate, and the
# stale-record negative control at the end proves it goes red and leaves the
# record alone.
set -euo pipefail
cd "$(dirname "$0")"
REPORT=records/tt.report.json
RECORD=records/functional.tt.json
python3 gen_functional.py --check
python3 compare.py --report "$REPORT" --out "$RECORD" --check
python3 - <<'PY'
import json
r = json.load(open("records/functional.tt.json"))
cells = {c["name"] for c in json.load(open("../../design/cells.json"))["cells"]}
assert set(r["cells"]) == cells and len(cells) == 40, "report must cover all 40 cells"
assert r["pass"]
PY
# The wrong-truth-table control. Its diagnosis must read as a netlist/RTL
# mismatch (exit 1) and never as a stale record -- the two verdicts a red CI log
# must keep apart (issue #138).
NEG_ERR="$(mktemp)"
trap 'rm -f "$NEG_ERR"' EXIT INT TERM HUP
rc=0
python3 compare.py --report "$REPORT" --negative-control >/dev/null 2>"$NEG_ERR" || rc=$?
if [ "$rc" -ne 1 ]; then
  echo "FAIL: negative control exited $rc, expected 1 (netlist/RTL mismatch)" >&2
  cat "$NEG_ERR" >&2; exit 1
fi
if ! grep -q 'disagree with the RTL models' "$NEG_ERR"; then
  echo "FAIL: the negative control was not diagnosed as a netlist/RTL mismatch" >&2
  cat "$NEG_ERR" >&2; exit 1
fi
if grep -q 'stale functional record' "$NEG_ERR"; then
  echo "FAIL: a netlist/RTL mismatch was reported as a stale record" >&2
  cat "$NEG_ERR" >&2; exit 1
fi
trap - EXIT INT TERM HUP
rm -f "$NEG_ERR"
echo "ok: 40 cells compared; negative control fails as a netlist/RTL mismatch"

# Negative control for the freshness gate itself (issue #138). Doctors the
# tracked record, asserts --check reports it stale (exit 3, not the exit-1
# netlist/RTL verdict) and leaves the doctoring in place, then restores it. The
# trap restores on every exit path; the only window that could leave the record
# doctored is an uncatchable kill between the two, and the restore is verified
# by digest below.
BACKUP="$(mktemp)"
STALE_ERR="$(mktemp)"
RECORD_SHA="$(sha256sum "$RECORD" | cut -d' ' -f1)"
cp "$RECORD" "$BACKUP"
trap 'cp "$BACKUP" "$RECORD" 2>/dev/null || true; rm -f "$BACKUP" "$STALE_ERR"' EXIT INT TERM HUP
python3 - "$RECORD" <<'PY'
import json, sys
p = sys.argv[1]
r = json.loads(open(p).read())
r["cells_passed"] = 0           # doctor the record: claim every cell failed
r["pass"] = False
open(p, "w").write(json.dumps(r, indent=1) + "\n")
PY
rc=0
python3 compare.py --report "$REPORT" --out "$RECORD" --check >/dev/null 2>"$STALE_ERR" || rc=$?
if [ "$rc" -ne 3 ]; then
  echo "FAIL: --check on a doctored record exited $rc, expected 3 (stale record)" >&2
  cat "$STALE_ERR" >&2; exit 1
fi
if ! grep -q 'stale functional record' "$STALE_ERR"; then
  echo "FAIL: --check did not name the record as stale" >&2
  cat "$STALE_ERR" >&2; exit 1
fi
if grep -q 'disagree with the RTL models' "$STALE_ERR"; then
  echo "FAIL: a stale record was reported as a netlist/RTL mismatch" >&2
  cat "$STALE_ERR" >&2; exit 1
fi
if [ "$(sha256sum "$RECORD" | cut -d' ' -f1)" = "$RECORD_SHA" ]; then
  echo "FAIL: --check repaired the record it was checking" >&2; exit 1
fi
trap - EXIT INT TERM HUP
cp "$BACKUP" "$RECORD"
rm -f "$BACKUP" "$STALE_ERR"
if [ "$(sha256sum "$RECORD" | cut -d' ' -f1)" != "$RECORD_SHA" ]; then
  echo "FAIL: the record was not restored after the stale-record control" >&2; exit 1
fi
echo "ok: stale-record control goes red, names the record, and leaves it doctored"

python3 test_arcs.py
