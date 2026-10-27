#!/usr/bin/env bash
# Checks that scripts/check_item6_statement.py passes on the committed pair and
# fails on a changed spec byte, a deleted statement row, and a renamed/added spec row (issue #28).
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
fail=0
check() { if [[ "$2" == "$3" ]]; then echo "ok   $1"; else echo "FAIL $1 (got $2, want $3)"; fail=1; fi; }
run() { python3 -I "$ROOT/scripts/check_item6_statement.py" --spec "$1" --statement "$2" >"$tmp/log" 2>&1; }
SPEC="$ROOT/spec/target-spec.md"; STMT="$ROOT/verification/item6-not-applicable.md"

run "$SPEC" "$STMT"; check "committed pair passes" "$?" "0"

sed 's/^Core supply/Core supply /;s/3\.36 µm (8 tracks/3.36 µm (8 tracks /' "$SPEC" >"$tmp/spec_byte.md"
run "$tmp/spec_byte.md" "$STMT"; check "edited spec byte fails" "$?" "1"
grep -q "spec hash changed" "$tmp/log"; check "  names the hash" "$?" "0"

grep -v '^| Pin access |' "$STMT" >"$tmp/stmt_missing.md"
run "$SPEC" "$tmp/stmt_missing.md"; check "deleted statement row fails" "$?" "1"
grep -q "missing from statement: Pin access" "$tmp/log"; check "  names the row" "$?" "0"

# a spec edit with the hash re-recorded still fails on rows
sed 's/^| Pin access |/| Pin access (renamed) |/' "$SPEC" >"$tmp/spec_row.md"
sed "s/SHA-256: [0-9a-f]\{64\}/SHA-256: $(sha256sum "$tmp/spec_row.md" | awk '{print $1}')/" "$STMT" >"$tmp/stmt_rehash.md"
run "$tmp/spec_row.md" "$tmp/stmt_rehash.md"; check "renamed spec row fails despite fresh hash" "$?" "1"

exit "$fail"
