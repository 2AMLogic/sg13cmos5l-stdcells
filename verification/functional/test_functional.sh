#!/usr/bin/env bash
# Checks for issue #82: generated files fresh, all 40 cells in the record,
# the real comparison passes, and a deliberately wrong truth table fails.
set -euo pipefail
cd "$(dirname "$0")"
REPORT=records/tt.report.json
python3 gen_functional.py --check
python3 compare.py --report "$REPORT" --out records/functional.tt.json
python3 - <<'PY'
import json
r = json.load(open("records/functional.tt.json"))
cells = {c["name"] for c in json.load(open("../../design/cells.json"))["cells"]}
assert set(r["cells"]) == cells and len(cells) == 40, "report must cover all 40 cells"
assert r["pass"]
PY
if python3 compare.py --report "$REPORT" --negative-control >/dev/null; then
  echo "FAIL: negative control did not fail" >&2; exit 1
fi
echo "ok: 40 cells compared; negative control fails as required"
