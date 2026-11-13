#!/usr/bin/env bash
# Checks that scripts/check_json.py covers every tracked *.json file this repo
# owns, ignores the tool-installed trees and untracked files, and fails loudly
# on a JSON parse error or on an empty file set (issue #114).
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="$ROOT/scripts/check_json.py"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
fail=0
check() { if [[ "$2" == "$3" ]]; then echo "ok   $1"; else echo "FAIL $1 (got $2, want $3)"; fail=1; fi; }

# --- the committed tree -----------------------------------------------------
( cd "$ROOT" && python3 -I "$SCRIPT" ) >"$tmp/log" 2>&1
check "committed tree passes" "$?" "0"

# Every tracked *.json this repo owns gets an ok: line -- no list to keep in
# step, so the set the gate reports must equal the set git tracks.
( cd "$ROOT" && git ls-files -- '*.json' ) \
  | grep -vE '^(\.loom|\.claude|\.agents)/' | sort >"$tmp/want"
sed -n 's/^ok:  *\(.*\.json\)$/\1/p' "$tmp/log" | sort >"$tmp/got"
diff -u "$tmp/want" "$tmp/got" >"$tmp/diff" 2>&1
check "covers every tracked repo-owned *.json" "$?" "0"
[[ -s "$tmp/diff" ]] && sed -n '1,20p' "$tmp/diff"

# The bootstrap-era skip branch is gone: an unreachable path must never be
# reported as a green non-result.
grep -q '^skip:' "$tmp/log"; check "reports no skipped paths" "$?" "1"

# Tool-installed trees stay out, so a Loom or skill upgrade cannot turn the
# evidence gate red.
grep -qE '^ok:  *\.(loom|claude|agents)/' "$tmp/log"
check "excludes the tool-installed trees" "$?" "1"

# --- a scratch repo, so a parse error can be staged safely -------------------
repo="$tmp/repo"
mkdir -p "$repo/scripts" "$repo/.loom"
cp "$SCRIPT" "$repo/scripts/check_json.py"
printf '# scratch\n\nNo links here.\n' >"$repo/README.md"
printf '{"ok": true}\n' >"$repo/good.json"
git -C "$repo" init -q
git -C "$repo" add -A

python3 -I "$repo/scripts/check_json.py" >"$tmp/log2" 2>&1
check "scratch repo passes" "$?" "0"
grep -q '^ok:  *good\.json$' "$tmp/log2"; check "  parses the tracked file" "$?" "0"

# An untracked file is not evidence: the gate enumerates the index.
printf '{"truncated": \n' >"$repo/untracked.json"
python3 -I "$repo/scripts/check_json.py" >"$tmp/log3" 2>&1
check "untracked broken JSON is ignored" "$?" "0"
rm -f "$repo/untracked.json"

# A tracked tool-tree file is skipped even when it is broken.
printf '{"truncated": \n' >"$repo/.loom/config.json"
git -C "$repo" add -A
python3 -I "$repo/scripts/check_json.py" >"$tmp/log4" 2>&1
check "broken JSON in a tool tree is ignored" "$?" "0"
rm -f "$repo/.loom/config.json"; git -C "$repo" add -A

# A truncated evidence file fails the gate and is named.
printf '{"truncated": \n' >"$repo/good.json"
git -C "$repo" add -A
python3 -I "$repo/scripts/check_json.py" >"$tmp/log5" 2>&1
check "truncated tracked JSON fails" "$?" "1"
grep -q '^FAIL: good\.json' "$tmp/log5"; check "  names the file" "$?" "0"
printf '{"ok": true}\n' >"$repo/good.json"; git -C "$repo" add -A

# No tracked *.json at all is a broken gate, not a green one: that silent pass
# is what the old glob list did when a path moved.
empty="$tmp/empty"
mkdir -p "$empty/scripts"
cp "$SCRIPT" "$empty/scripts/check_json.py"
printf '# scratch\n\nNo links here.\n' >"$empty/README.md"
git -C "$empty" init -q
git -C "$empty" add -A
python3 -I "$empty/scripts/check_json.py" >"$tmp/log6" 2>&1
check "no tracked *.json fails" "$?" "1"

# Outside a git repo the gate cannot enumerate anything: fail, never pass.
nogit="$tmp/nogit"
mkdir -p "$nogit/scripts"
cp "$SCRIPT" "$nogit/scripts/check_json.py"
printf '# scratch\n\nNo links here.\n' >"$nogit/README.md"
printf '{"ok": true}\n' >"$nogit/good.json"
python3 -I "$nogit/scripts/check_json.py" >"$tmp/log7" 2>&1
check "outside a git repo fails" "$?" "1"

exit "$fail"
