#!/usr/bin/env bash
# Checks that scripts/check_roadmap_now.py passes on the committed ROADMAP.md
# and fails loudly on a reintroduced work-item issue reference, an absent
# `## Now` heading, and a section that parses to zero rows (issue #180).
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
fail=0
check() { if [[ "$2" == "$3" ]]; then echo "ok   $1"; else echo "FAIL $1 (got $2, want $3)"; fail=1; fi; }
run() { python3 -I "$ROOT/scripts/check_roadmap_now.py" --file "$1" >"$tmp/log" 2>&1; }
ROADMAP="$ROOT/ROADMAP.md"

run "$ROADMAP"; check "committed ROADMAP.md passes" "$?" "0"
grep -q "^ok " "$tmp/log"; check "  reports ok" "$?" "0"

# cwd independence and no token: the check must be hermetic (defect #172's shape)
( cd /tmp && env -u GH_TOKEN -u GITHUB_TOKEN \
  python3 -I "$ROOT/scripts/check_roadmap_now.py" >/dev/null 2>&1 )
check "passes from any working directory with no token" "$?" "0"

# a reintroduced work-item reference fails, naming the section and the line
sed 's/the record\*\*\./the record** (#152)./' "$ROADMAP" >"$tmp/roadmap_ref.md"
run "$tmp/roadmap_ref.md"; check "reintroduced (#152) in a Now row fails" "$?" "1"
want_line="$(grep -n 'Bring the README status' "$tmp/roadmap_ref.md" | cut -d: -f1)"
grep -q "line $want_line:" "$tmp/log"; check "  names the line ($want_line)" "$?" "0"
grep -q "## Now" "$tmp/log"; check "  names the section" "$?" "0"

# prose references are not work-item references and must keep passing
sed 's/pending the #129 decision/pending the (#129) decision/' "$ROADMAP" >"$tmp/roadmap_prose.md"
run "$tmp/roadmap_prose.md"; check "prose (#129) on a continuation line passes" "$?" "0"
sed 's/Done when the Status paragraph/Done when the (#129) Status paragraph/' "$ROADMAP" >"$tmp/roadmap_prose2.md"
run "$tmp/roadmap_prose2.md"; check "prose (#129) on the row's first line passes" "$?" "0"

# a `#N` inside a markdown link target on a row line is not a work-item reference
sed 's/Done when the Status/Done when [x](#152-anchor) Status/' "$ROADMAP" >"$tmp/roadmap_link.md"
run "$tmp/roadmap_link.md"; check "link-target anchor on a row line passes" "$?" "0"

# renamed or absent `## Now` fails loudly rather than passing vacuously
sed 's/^## Now$/## Starting today/' "$ROADMAP" >"$tmp/roadmap_nonow.md"
run "$tmp/roadmap_nonow.md"; check "absent ## Now fails" "$?" "1"
grep -q "no \`## Now\` heading" "$tmp/log"; check "  names the missing heading" "$?" "0"

# a section that parses to zero rows fails loudly
printf '# Roadmap\n\n## Now\n\nNothing startable today.\n\n## Next\n\n- something\n' >"$tmp/roadmap_empty.md"
run "$tmp/roadmap_empty.md"; check "zero-row ## Now fails" "$?" "1"
grep -q "zero rows" "$tmp/log"; check "  names the emptiness" "$?" "0"

exit "$fail"
