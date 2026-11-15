#!/usr/bin/env bash
# Self-test for the checks scripts/check_signoff.sh can run without klt:
# check_attest_pins, which refuses an item-9 attestation inventory whose
# hand-copied pins have drifted from this repo's pins of record (issue #131),
# attest_envelopes, which derives the list of attestation envelopes to
# re-check from the manifest rather than hand-copying a block per item (issue
# #133), and check_netlist_identities, which recomputes each functional
# record's environment.netlist_identity from the tree so a netlist change that
# moves electrical content cannot silently stale the item-5 evidence (issue
# #170). No network, no uvx and no klt: sources the script with
# CHECK_SIGNOFF_SOURCE_ONLY=1 and exercises each against doctored copies of the
# pin files, records and netlists, plus `--help`, which also runs klt-free.
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

# --- attest_envelopes: the re-checked list is derived from the manifest -------
# Issue #133: items 9 and 10 each had a hand-copied `--attest N --check` block
# in check_signoff.sh and item 1, cited by the manifest since issue #36, had
# none -- so the one cited envelope no gate re-checked was the one that had
# drifted. These check that the list the gate re-checks is derived from the
# manifest (so it cannot omit a citation) and that anything the derivation
# cannot resolve fails loudly instead of dropping a row.

# The committed manifest, read in place: every attestation envelope it cites,
# item-sorted, one `<item><TAB><inventory><TAB><envelope>` row each.
want="$(printf '1\tdesign/item1-inventory.json\tverification/item1-attest.json\n9\tsim/attest/item9.inventory.json\tsim/attest/item9.envelope.json\n10\tmanifests/item-10-inventory.json\tmanifests/evidence/item-10-repo-hygiene.json')"
got="$(attest_envelopes "$ROOT" "$MANIFEST" 2>"$tmp/log")"
check "the committed manifest's attestation envelopes are derived" "$?" "0"
check "every cited envelope is a row, item 1 included" "$got" "$want"

# A synthetic manifest + evidence tree, so the failure modes below need no
# doctored copy of the repo's own evidence.
AE="$tmp/ae"
mkdir -p "$AE"
# write <path-under-$AE> <json>
write() { printf '%s\n' "$2" >"$AE/$1"; }
ENVELOPE='{"t1_item": 1, "source": "inv1.json", "attestation": {"producer": "klt signoff --attest"}}'
SYNTH_MANIFEST='{"block": "b", "kind": "digital", "evidence": {"1": {"file": "e1.json"}, "5": {"file": "r5.json"}}}'

write m.json "$SYNTH_MANIFEST"
write e1.json "$ENVELOPE"
write r5.json '{"status": "pass", "checks": []}'
got="$(attest_envelopes "$AE" m.json 2>"$tmp/log")"
check "a synthetic manifest yields its one envelope" "$?" "0"
check "a cited non-attestation report is not a row" "$got" "$(printf '1\tinv1.json\te1.json')"

write e1.json '{"source": "inv1.json", "attestation": {"producer": "klt signoff --attest"}}'
( attest_envelopes "$AE" m.json ) >/dev/null 2>"$tmp/log"
check "an envelope naming no t1_item exits non-zero" "$?" "1"
grep -q "e1.json" "$tmp/log"; check "that failure names the envelope" "$?" "0"

write e1.json '{"t1_item": 1, "attestation": {"producer": "klt signoff --attest"}}'
( attest_envelopes "$AE" m.json ) >/dev/null 2>"$tmp/log"
check "an envelope naming no source inventory exits non-zero" "$?" "1"

write e1.json "$ENVELOPE"
rm -f "$AE/r5.json"
( attest_envelopes "$AE" m.json ) >/dev/null 2>"$tmp/log"
check "a cited evidence file that is missing exits non-zero" "$?" "1"
grep -q "r5.json" "$tmp/log"; check "that failure names the missing citation" "$?" "0"

write r5.json 'not json'
( attest_envelopes "$AE" m.json ) >/dev/null 2>"$tmp/log"
check "a cited evidence file that is not JSON exits non-zero" "$?" "1"

write m.json '{"block": "b", "kind": "digital", "evidence": {"5": {"file": "r5.json"}}}'
write r5.json '{"status": "pass", "checks": []}'
( attest_envelopes "$AE" m.json ) >/dev/null 2>"$tmp/log"
check "a manifest citing no attestation envelope exits non-zero" "$?" "1"

write m.json '{"block": "b", "kind": "digital", "evidence": {"1": {"hash": "x"}}}'
( attest_envelopes "$AE" m.json ) >/dev/null 2>"$tmp/log"
check "an evidence entry naming no file exits non-zero" "$?" "1"

( attest_envelopes "$AE" absent.json ) >/dev/null 2>"$tmp/log"
check "a manifest that cannot be read exits non-zero" "$?" "1"
grep -q "Traceback" "$tmp/log"; check "a derivation failure is reported, not crashed on" "$?" "1"

# --- check_netlist_identities: the item-5 records' netlist_identity gate -----
# Issue #170: the manifest's item-5 citation pins only the top deck (its
# content_hash is netlist_sha256); the 40 cell netlists are pinned by each
# functional record's environment.netlist_closure, summarized in
# environment.netlist_identity -- and nothing resolved either against the
# tree. The gate recomputes the identity from the working tree over each
# record's own closure. It needs the same read-only clone treatment as
# check_attest_pins: the records, the top decks and the netlists, no klt.

NI="$tmp/ni"
mkdir -p "$NI"
cp -r "$ROOT/design" "$ROOT/verification" "$NI/"

( check_netlist_identities "$NI" ) >"$tmp/log" 2>&1
check "the committed records' netlist identities recompute" "$?" "0"
grep -q "corners.report.json" "$tmp/log"
check "the ok line names a record it re-checked" "$?" "0"

# A record whose environment carries no netlist_identity is skipped, never
# failed or counted. functional.tt.json, the committed record of that shape,
# is not under the *.report.json glob, so the branch is exercised with a
# synthetic record the glob does select.
printf '%s\n' '{"environment": {"ngspice": "44"}}' >"$NI/verification/functional/records/noident.report.json"
( check_netlist_identities "$NI" ) >"$tmp/log" 2>&1
check "a record with no netlist_identity is skipped, not failed" "$?" "0"
grep -q "noident.report.json" "$tmp/log"
check "the skipped record is not named as checked" "$?" "1"
grep -q "3 functional records" "$tmp/log"
check "the skipped record is not counted as checked" "$?" "0"
rm "$NI/verification/functional/records/noident.report.json"

# s5l_a21o_1.spice is in all three closures; doctoring it exercises the gate.
NET="$NI/design/netlists/s5l_a21o_1.spice"

sed -i 's/w=1480n/w=1500n/' "$NET"
( check_netlist_identities "$NI" ) >/dev/null 2>"$tmp/log"
check "an electrical netlist change exits non-zero" "$?" "1"
grep -q "corners.report.json" "$tmp/log"
check "that failure names a record" "$?" "0"
grep -q "sha256:" "$tmp/log"
check "that failure names both hashes" "$?" "0"

# A comment-only regeneration (the PR #168 shape) must stay green: the
# identity drops `*` lines, so the raw byte pins go stale with no signal.
# Back to the committed netlist first -- the electrical change above is still
# in the clone.
cp "$ROOT/design/netlists/s5l_a21o_1.spice" "$NET"
sed -i '2s/./* header regenerated, comment-only change./' "$NET"
( check_netlist_identities "$NI" ) >"$tmp/log" 2>&1
check "a comment-only netlist change stays green" "$?" "0"

# A closure entry whose file is gone is a failure, never a silent pass.
rm "$NET"
( check_netlist_identities "$NI" ) >/dev/null 2>"$tmp/log"
check "a missing closure file exits non-zero" "$?" "1"
grep -q "s5l_a21o_1.spice" "$tmp/log"
check "that failure names the missing file" "$?" "0"

# Back to the committed tree: the cases below must trip their own branches,
# not this one's missing-file failure still standing in the clone.
cp "$ROOT/design/netlists/s5l_a21o_1.spice" "$NET"

# Zero records under the glob would make the re-check cover nothing; the
# attest_envelopes precedent says that is a failure, not a pass.
mv "$NI/verification/functional/records" "$NI/verification/functional/records.away"
( check_netlist_identities "$NI" ) >/dev/null 2>"$tmp/log"
check "a glob selecting zero records exits non-zero" "$?" "1"
grep -q "selected no record" "$tmp/log"; check "that failure is loud, not silent" "$?" "0"
mv "$NI/verification/functional/records.away" "$NI/verification/functional/records"

# A record whose identity klt could not compute (netlist_identity_error, set
# whenever a closure cannot be fully read) must fail, never falsely match.
cp "$NI/verification/functional/records/corners.report.json" "$tmp/corners.pristine"
python3 -I - "$NI/verification/functional/records/corners.report.json" <<'PY'
import json, sys

with open(sys.argv[1], "rb") as handle:
    report = json.loads(handle.read().decode("utf-8"))
env = report["environment"]
env["netlist_identity"] = None
env["netlist_identity_error"] = "include(s) resolved by the executing host are not hashable: models.cir"
with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump(report, handle)
PY
( check_netlist_identities "$NI" ) >/dev/null 2>"$tmp/log"
check "a record with netlist_identity_error exits non-zero" "$?" "1"
grep -q "could not compute its netlist_identity" "$tmp/log"
check "that failure is the identity-error branch, not the missing-file one" "$?" "0"
cp "$tmp/corners.pristine" "$NI/verification/functional/records/corners.report.json"

# Discovery is by rule, not a hand-kept list, so a fourth record is covered
# automatically -- including a broken one, which fails rather than passes.
printf 'not json\n' >"$NI/verification/functional/records/bogus.report.json"
( check_netlist_identities "$NI" ) >/dev/null 2>"$tmp/log"
check "an unreadable fourth record exits non-zero" "$?" "1"
grep -q "bogus.report.json" "$tmp/log"
check "that failure names the broken record" "$?" "0"
rm "$NI/verification/functional/records/bogus.report.json"

# --- usage(): --help is the whole header comment -----------------------------
# The help text was a hardcoded `sed -n '2,13p'` line range, so it silently
# dropped the last Usage line the moment the header grew by one (issue #133).
# --help exits before any klt or network use, so this needs neither.
help="$("$ROOT/scripts/check_signoff.sh" --help 2>"$tmp/log")"
check "--help exits 0" "$?" "0"
grep -q -- "--regenerate   rewrite the committed signoff record" <<<"$help"
check "--help reaches the last Usage line" "$?" "0"
grep -q "^set -uo pipefail" <<<"$help"
check "--help stops at the first non-comment line" "$?" "1"

exit $fail
