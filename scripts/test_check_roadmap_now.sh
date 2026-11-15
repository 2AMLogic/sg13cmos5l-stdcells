#!/usr/bin/env bash
# Checks that scripts/check_roadmap_now.py passes on the committed ROADMAP.md
# (`## Now` as a WORK_PLAN.md pointer, zero hand-written rows) and fails loudly
# on any restored hand-written work row — numbered or bulleted, whether or not
# it cites an issue — and on an absent `## Now` heading (issues #186, #192).
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
fail=0
check() { if [[ "$2" == "$3" ]]; then echo "ok   $1"; else echo "FAIL $1 (got $2, want $3)"; fail=1; fi; }
run() { python3 -I "$ROOT/scripts/check_roadmap_now.py" --file "$1" >"$tmp/log" 2>&1; }
ROADMAP="$ROOT/ROADMAP.md"
# mutate <sed-expr> <out>: build a fixture, failing loudly if the expression
# matched nothing — a no-op sed makes the following assertion vacuous (#180)
mutate() { sed "$1" "$ROADMAP" >"$2"; if cmp -s "$ROADMAP" "$2"; then echo "FAIL fixture unchanged: $1"; fail=1; fi; }

run "$ROADMAP"; check "committed ROADMAP.md passes" "$?" "0"
grep -q "^ok " "$tmp/log"; check "  reports ok" "$?" "0"

# cwd independence and no token: the check must be hermetic (defect #172's shape)
( cd /tmp && env -u GH_TOKEN -u GITHUB_TOKEN \
  python3 -I "$ROOT/scripts/check_roadmap_now.py" >/dev/null 2>&1 )
check "passes from any working directory with no token" "$?" "0"

# a restored hand-written numbered row is rejected, naming the section and line
mutate 's/^## Now$/## Now\n\n1. **Bring the README status in line with the record** (#152). Done when it matches./' "$tmp/roadmap_row.md"
run "$tmp/roadmap_row.md"; check "restored numbered row citing #152 fails" "$?" "1"
want_line="$(grep -n 'Bring the README status' "$tmp/roadmap_row.md" | cut -d: -f1)"
grep -q "line $want_line:" "$tmp/log"; check "  names the line ($want_line)" "$?" "0"
grep -q "## Now" "$tmp/log"; check "  names the section" "$?" "0"

# a row citing no issue fails too, so the old work-item-reference branch
# stays deleted (issue #186)
mutate 's/^## Now$/## Now\n\n2. **A row citing nothing in particular**. Done when it is gone./' "$tmp/roadmap_plain.md"
run "$tmp/roadmap_plain.md"; check "numbered row citing no issue fails too" "$?" "1"

# a bulleted work row is rejected too: bullets are the house list style of
# every sibling section in ROADMAP.md, so a bulleted queue is the likely
# regression shape, not an exotic one (issue #192)
mutate 's/^## Now$/## Now\n\n- **A row written as a dash bullet**. Done when it is gone./' "$tmp/roadmap_dash.md"
run "$tmp/roadmap_dash.md"; check "bulleted row (dash) fails" "$?" "1"
want_line="$(grep -n 'A row written as a dash bullet' "$tmp/roadmap_dash.md" | cut -d: -f1)"
grep -q "line $want_line:" "$tmp/log"; check "  names the line ($want_line)" "$?" "0"
grep -q "## Now" "$tmp/log"; check "  names the section" "$?" "0"

mutate 's/^## Now$/## Now\n\n* **A row written as a star bullet**. Done when it is gone./' "$tmp/roadmap_star.md"
run "$tmp/roadmap_star.md"; check "bulleted row (star) fails" "$?" "1"

mutate 's/^## Now$/## Now\n\n+ **A row written as a plus bullet**. Done when it is gone./' "$tmp/roadmap_plus.md"
run "$tmp/roadmap_plus.md"; check "bulleted row (plus) fails" "$?" "1"

# prose that merely begins with a hyphenated word is not a list row (#192)
mutate 's/^## Now$/## Now\n\nCross-cutting work lives in WORK_PLAN.md, not here.\nA well-known fact: this is prose, not a - bullet item./' "$tmp/roadmap_hyphen.md"
run "$tmp/roadmap_hyphen.md"; check "hyphenated prose words are not list rows" "$?" "0"

# prose references in the pointer text are not work rows and keep passing
mutate 's/(issue #186)/(issue (#186))/' "$tmp/roadmap_prose.md"
run "$tmp/roadmap_prose.md"; check "prose (#186) on the pointer text passes" "$?" "0"
mutate 's/(#180), applied/(#180) and #129, applied/' "$tmp/roadmap_prose2.md"
run "$tmp/roadmap_prose2.md"; check "prose #129 on the pointer text passes" "$?" "0"

# a `#N` inside a markdown link target on the pointer line is not a work row
mutate 's|](WORK_PLAN.md)|](WORK_PLAN.md#129-anchor)|' "$tmp/roadmap_link.md"
run "$tmp/roadmap_link.md"; check "link-target anchor on the pointer line passes" "$?" "0"

# renamed or absent `## Now` fails loudly rather than passing vacuously
mutate 's/^## Now$/## Starting today/' "$tmp/roadmap_nonow.md"
run "$tmp/roadmap_nonow.md"; check "absent ## Now fails" "$?" "1"
grep -q "no \`## Now\` heading" "$tmp/log"; check "  names the missing heading" "$?" "0"

# a zero-row `## Now` is the passing state — the pointer replaced the rows
printf '# Roadmap\n\n## Now\n\nNothing startable today.\n\n## Next\n\n- something\n' >"$tmp/roadmap_empty.md"
run "$tmp/roadmap_empty.md"; check "zero-row ## Now passes" "$?" "0"
grep -q "^ok " "$tmp/log"; check "  reports ok" "$?" "0"

exit "$fail"
