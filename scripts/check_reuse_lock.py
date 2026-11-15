#!/usr/bin/env python3
"""Verify every vendored file named in reuse.lock.json against its sha256.

Run from anywhere: `python3 -I scripts/check_reuse_lock.py`. The lock is the
contract: for every `imports[].files[]` entry the `local` path is hashed --
bytes, never text, so line endings cannot silently become part of the hash --
and compared to the recorded `sha256`. The working tree is hashed, not the
index, so an uncommitted local edit is caught too. A listed-but-absent file is
a failure, not a skip: a silently deleted vendored file is an undisclosed
divergence, the same class of problem as an edited one. Fail-closed on a gate
that cannot do its job: a missing or unparseable lock, an empty `imports[]`,
an element with an empty `files[]`, an absent `local` path, or a `sha256` that
is not 64 lowercase hex is a failure, not a green run. No network: verifying
that the recorded hash still matches the upstream blob at the pinned commit
stays a manual step (spec/porting-plan.md). Exit 1 on any mismatch or
structural failure.
"""
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCK = "reuse.lock.json"

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ESCAPES_RE = re.compile(r"(^|/)\.\.(/|$)")


def load_imports():
    """Return (imports_list, None), or (None, detail) on any structural problem.

    Structural failures keep the gate green-proof: an empty imports[] or an
    element with no files means nothing would be checked, and a check that
    checks nothing must not report success.
    """
    try:
        with open(os.path.join(ROOT, LOCK), encoding="utf-8") as fh:
            lock = json.load(fh)
    except (OSError, ValueError) as exc:
        return None, str(exc)
    if not isinstance(lock, dict) or "imports" not in lock:
        return None, "no 'imports' key"
    imports = lock["imports"]
    if not isinstance(imports, list) or not imports:
        return None, "'imports' is empty or not a list"
    for idx, element in enumerate(imports):
        if not isinstance(element, dict):
            return None, f"imports[{idx}] is not an object"
        files = element.get("files")
        if not isinstance(files, list) or not files:
            return None, f"imports[{idx}] has an empty or missing 'files' list"
    return imports, None


def check_entry(rel, recorded):
    """Hash ROOT/rel in binary mode, compare, print and return 0 or 1."""
    if not isinstance(rel, str) or not rel:
        print(f"FAIL: {LOCK}: file entry with a missing or non-string 'local'")
        return 1
    if rel.startswith("/") or ESCAPES_RE.search(rel):
        print(f"FAIL: {rel}: 'local' path escapes the repository")
        return 1
    if not isinstance(recorded, str) or not SHA256_RE.match(recorded):
        print(f"FAIL: {rel}: recorded 'sha256' is not 64 lowercase hex")
        return 1
    try:
        with open(os.path.join(ROOT, rel), "rb") as fh:
            actual = hashlib.sha256(fh.read()).hexdigest()
    except OSError as exc:
        print(f"FAIL: {rel}: {exc}")
        return 1
    if actual != recorded:
        print(f"FAIL: {rel}: sha256 mismatch (recorded {recorded}, actual {actual})")
        return 1
    print(f"ok:   {rel}")
    return 0


def check_lock():
    imports, detail = load_imports()
    if imports is None:
        print(f"FAIL: {LOCK}: {detail}")
        return 1
    failures = 0
    for element in imports:
        for entry in element["files"]:
            if not isinstance(entry, dict):
                print(f"FAIL: {LOCK}: file entry is not an object")
                failures += 1
                continue
            failures += check_entry(entry.get("local"), entry.get("sha256"))
    return failures


def main():
    failures = check_lock()
    if failures:
        print(f"{failures} check(s) failed")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
