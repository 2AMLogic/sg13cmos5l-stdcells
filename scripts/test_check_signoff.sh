#!/usr/bin/env bash
# Checks that scripts/check_signoff.sh refuses an item-9 attestation inventory
# whose hand-copied pins have drifted from this repo's pins of record (issue
# #131). No network, no uvx and no klt: sources the script with
# CHECK_SIGNOFF_SOURCE_ONLY=1 and exercises check_attest_pins against doctored
# copies of the pin files.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
fail=0
check() { if [[ "$2" == "$3" ]]; then echo "ok   $1"; else echo "FAIL $1 (got $2, want $3)"; fail=1; fi; }

INV="sim/attest/item9.inventory.json"

# shellcheck disable=SC1091
CHECK_SIGNOFF_SOURCE_ONLY=1 source "$ROOT/scripts/check_signoff.sh" ""
set +e  # sourcing leaves no `set -e` on, but be explicit: the checks read $?

mkdir -p "$tmp/clone"
cp -r "$ROOT/sim" "$ROOT/layout" "$tmp/clone/"

# edit <dotted key under "pins"> <value|DELETE>: doctor the clone's inventory,
# starting again from the committed one each time.
edit() {
    cp "$ROOT/$INV" "$tmp/clone/$INV"
    python3 -I - "$tmp/clone/$INV" "$1" "$2" <<'PY'
import json, sys

path, key, value = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path, "rb") as handle:
    inventory = json.loads(handle.read().decode("utf-8"))
node = inventory
*head, last = ["pins", *key.split(".")] if key else ["pins"]
for step in head:
    node = node[step]
if value == "DELETE":
    del node[last]
else:
    node[last] = value
with open(path, "w", encoding="utf-8") as handle:
    json.dump(inventory, handle)
PY
}

( check_attest_pins "$tmp/clone" ) >"$tmp/log" 2>&1
check "the committed inventory matches the pins of record" "$?" "0"

edit "tools.klt" "dce956c3c39995643ff2a5c31b53c474b3c2aada"
( check_attest_pins "$tmp/clone" ) >"$tmp/log" 2>&1
check "a drifted klt pin exits non-zero" "$?" "1"
grep -q "pins.tools.klt" "$tmp/log"; check "the klt failure names the inventory key" "$?" "0"
grep -q "layout/toolchain.json" "$tmp/log"; check "the klt failure names the pin of record" "$?" "0"

edit "tools.ngspice" "44"
( check_attest_pins "$tmp/clone" ) >"$tmp/log" 2>&1
check "a drifted ngspice pin exits non-zero" "$?" "1"
grep -q "sim/toolchain.json" "$tmp/log"; check "the ngspice failure names the pin of record" "$?" "0"

edit "tools.openvaf-r" "osdi_0.3-1-gdeadbeef"
( check_attest_pins "$tmp/clone" ) >"$tmp/log" 2>&1
check "a drifted openvaf-r pin exits non-zero" "$?" "1"

edit "pdk.revision" "0000000000000000000000000000000000000000"
( check_attest_pins "$tmp/clone" ) >"$tmp/log" 2>&1
check "a drifted PDK revision exits non-zero" "$?" "1"
grep -q "sim/pdk.json" "$tmp/log"; check "the PDK failure names the pin of record" "$?" "0"

edit "" "DELETE"
( check_attest_pins "$tmp/clone" ) >"$tmp/log" 2>&1
check "an inventory with no pins block exits non-zero" "$?" "1"
grep -q "Traceback" "$tmp/log"; check "a missing pins block is reported, not crashed on" "$?" "1"

cp "$ROOT/$INV" "$tmp/clone/$INV"
python3 -I - "$tmp/clone/layout/toolchain.json" <<'PY'
import json, sys

with open(sys.argv[1], "rb") as handle:
    pins = json.loads(handle.read().decode("utf-8"))
del pins["klt"]["commit"]
with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump(pins, handle)
PY
( check_attest_pins "$tmp/clone" ) >"$tmp/log" 2>&1
check "an unreadable pin of record exits non-zero" "$?" "1"

exit $fail
