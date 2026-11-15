#!/usr/bin/env bash
# Checks that scripts/check_reuse_lock.py verifies every vendored file named in
# reuse.lock.json against its recorded sha256, and fails closed on a mismatch,
# a missing vendored file or a broken lock (issue #159).
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="$ROOT/scripts/check_reuse_lock.py"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
fail=0
check() { if [[ "$2" == "$3" ]]; then echo "ok   $1"; else echo "FAIL $1 (got $2, want $3)"; fail=1; fi; }
sha() { python3 -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$1"; }

# --- the committed tree ------------------------------------------------------
( cd "$ROOT" && python3 -I "$SCRIPT" ) >"$tmp/log" 2>&1
check "committed tree passes" "$?" "0"

# No list to keep in step: the set of ok: lines the gate prints must equal the
# set of local paths the lock lists.
python3 -c 'import json; [print(f["local"]) for e in json.load(open("reuse.lock.json"))["imports"] for f in e["files"]]' \
  | ( cd "$ROOT" && sort ) >"$tmp/want"
sed -n 's/^ok:  *\(.*\)$/\1/p' "$tmp/log" | sort >"$tmp/got"
diff -u "$tmp/want" "$tmp/got" >"$tmp/diff" 2>&1
check "covers every local path the lock lists" "$?" "0"
[[ -s "$tmp/diff" ]] && sed -n '1,20p' "$tmp/diff"

# ROOT comes from __file__, so the gate runs from a subdirectory.
( cd "$ROOT/sim" && python3 -I "../scripts/check_reuse_lock.py" ) >"$tmp/log_sub" 2>&1
check "runs from a subdirectory" "$?" "0"

# --- a scratch repo, so a vendored edit can be staged safely ------------------
repo="$tmp/repo"
mkdir -p "$repo/scripts" "$repo/vendored"
cp "$SCRIPT" "$repo/scripts/check_reuse_lock.py"
printf 'vendored line one\n' >"$repo/vendored/gen.py"
printf 'scratch readme\n' >"$repo/vendored/README.md"
# A binary fixture with NUL bytes and a CRLF: a text-mode read would translate
# the CRLF and hash different bytes, so a pass here proves byte-mode hashing.
printf 'M\000\001\002\r\nend' >"$repo/vendored/blob.gds"
h_gen="$(sha "$repo/vendored/gen.py")"
h_readme="$(sha "$repo/vendored/README.md")"
h_blob="$(sha "$repo/vendored/blob.gds")"
cat >"$repo/reuse.lock.json" <<EOF
{
  "schema": 1,
  "imports": [
    {
      "from": "example/upstream",
      "commit": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "mode": "vendored",
      "files": [
        {"upstream": "src/gen.py", "local": "vendored/gen.py", "sha256": "$h_gen"},
        {"upstream": "src/README.md", "local": "vendored/README.md", "sha256": "$h_readme"}
      ]
    },
    {
      "from": "example/upstream2",
      "commit": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "mode": "vendored",
      "files": [
        {"upstream": "art/blob.gds", "local": "vendored/blob.gds", "sha256": "$h_blob"}
      ]
    }
  ]
}
EOF
git -C "$repo" init -q
git -C "$repo" add -A

python3 -I "$repo/scripts/check_reuse_lock.py" >"$tmp/log2" 2>&1
check "scratch repo passes (two elements, binary file)" "$?" "0"
grep -q '^ok:  *vendored/gen\.py$' "$tmp/log2"; check "  names gen.py" "$?" "0"
grep -q '^ok:  *vendored/blob\.gds$' "$tmp/log2"; check "  names blob.gds" "$?" "0"

# One flipped byte in a vendored file fails and names the file and both hashes.
printf '\n' >>"$repo/vendored/gen.py"
h_actual="$(sha "$repo/vendored/gen.py")"
python3 -I "$repo/scripts/check_reuse_lock.py" >"$tmp/log3" 2>&1
check "flipped vendored byte fails" "$?" "1"
grep -qF "FAIL: vendored/gen.py: sha256 mismatch (recorded $h_gen, actual $h_actual)" "$tmp/log3"
check "  names the file and both hashes" "$?" "0"

# Restoring the byte goes green again: the gate tracks the tree, not history.
printf 'vendored line one\n' >"$repo/vendored/gen.py"
python3 -I "$repo/scripts/check_reuse_lock.py" >"$tmp/log4" 2>&1
check "restored tree passes again" "$?" "0"

# A listed-but-absent local path is a failure, not a skip: a silently deleted
# vendored file is an undisclosed divergence, same class as an edited one.
rm "$repo/vendored/README.md"
python3 -I "$repo/scripts/check_reuse_lock.py" >"$tmp/log5" 2>&1
check "deleted vendored file fails" "$?" "1"
grep -q '^FAIL: vendored/README\.md' "$tmp/log5"; check "  names the missing file" "$?" "0"
printf 'scratch readme\n' >"$repo/vendored/README.md"

# --- the lock itself must be usable, or the gate is not green -----------------
printf '{"schema": 1, "imports": []}\n' >"$repo/reuse.lock.json"
python3 -I "$repo/scripts/check_reuse_lock.py" >"$tmp/log6" 2>&1
check "empty imports[] fails" "$?" "1"

printf '{"schema": 1, "imports": [{"files": []}]}\n' >"$repo/reuse.lock.json"
python3 -I "$repo/scripts/check_reuse_lock.py" >"$tmp/log7" 2>&1
check "empty files[] fails" "$?" "1"

printf '{"imports": [\n' >"$repo/reuse.lock.json"
python3 -I "$repo/scripts/check_reuse_lock.py" >"$tmp/log8" 2>&1
check "unparseable lock fails" "$?" "1"

rm "$repo/reuse.lock.json"
python3 -I "$repo/scripts/check_reuse_lock.py" >"$tmp/log9" 2>&1
check "missing lock fails" "$?" "1"

cat >"$repo/reuse.lock.json" <<EOF
{"schema": 1, "imports": [{"files": [{"upstream": "src/gen.py", "local": "vendored/gen.py", "sha256": "deadbeef"}]}]}
EOF
python3 -I "$repo/scripts/check_reuse_lock.py" >"$tmp/log10" 2>&1
check "non-64-hex recorded sha256 fails" "$?" "1"
grep -q '^FAIL: vendored/gen\.py' "$tmp/log10"; check "  names the file" "$?" "0"

exit "$fail"
