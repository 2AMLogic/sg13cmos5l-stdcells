#!/usr/bin/env bash
# Checks that scripts/setup-env.sh fails closed (issue #4). No network, no
# large downloads: exercises fetch_verified against a local file:// URL.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
fail=0
check() { if [[ "$2" == "$3" ]]; then echo "ok   $1"; else echo "FAIL $1 (got $2, want $3)"; fail=1; fi; }

printf 'stub payload\n' >"$tmp/payload"
good="$(sha256sum "$tmp/payload" | awk '{print $1}')"
bad="0000000000000000000000000000000000000000000000000000000000000000"

# shellcheck disable=SC1091
SETUP_ENV_SOURCE_ONLY=1 source "$ROOT/scripts/setup-env.sh"
set +e  # sourcing leaves `set -e` on; the checks below read $? themselves

( fetch_verified "file://$tmp/payload" "$bad" "$tmp/out" ) >"$tmp/log" 2>&1
check "wrong sha256 exits non-zero" "$?" "1"
[[ ! -e "$tmp/out" ]]; check "wrong sha256 leaves no file at dest" "$?" "0"
grep -q "checksum mismatch" "$tmp/log"; check "mismatch message names the cause" "$?" "0"

( fetch_verified "file://$tmp/payload" "$good" "$tmp/out" ) >"$tmp/log" 2>&1
check "right sha256 exits zero" "$?" "0"
cmp -s "$tmp/payload" "$tmp/out"; check "right sha256 installs the file" "$?" "0"

( fetch_verified "file://$tmp/missing" "$good" "$tmp/out2" ) >"$tmp/log" 2>&1
check "failed download exits non-zero" "$?" "1"

# The pins in sim/ must agree with the checksummed scripts: a doctored pin is refused
# before any large download. Run the real script with a corrupted copy of the pin file.
mkdir -p "$tmp/clone" && cp -r "$ROOT/sim" "$ROOT/layout" "$ROOT/scripts" "$tmp/clone/"
python3 -I - "$tmp/clone/sim/pdk.json" <<'PY'
import json, sys
p = json.load(open(sys.argv[1])); p["tarball_sha256"] = "0" * 64
json.dump(p, open(sys.argv[1], "w"))
PY
(cd "$tmp/clone" && bash scripts/setup-env.sh) >"$tmp/log" 2>&1
rc=$?
check "doctored PDK pin makes setup-env.sh exit non-zero" "$([[ $rc -ne 0 ]] && echo 1 || echo 0)" "1"
grep -q "disagrees with fetch-ihp-sg13cmos5l.sh" "$tmp/log"; check "doctored pin reported as a pin/script disagreement" "$?" "0"

exit $fail
