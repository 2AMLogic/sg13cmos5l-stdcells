#!/usr/bin/env python3
"""Validate committed JSON config/evidence files and README relative links.

Run from anywhere: `python3 -I scripts/check_json.py`. Globs that match nothing
are skipped with a note (the files land with later issues), so this is green on
a repo that has none of them yet. Exit 1 on any parse error or broken link.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

JSON_GLOBS = [
    "package.json",
    "reuse.lock.json",
    "sim/*.json",
    "layout/toolchain.json",
    "manifests/*.json",
]

LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")


def check_json():
    failures = 0
    for pattern in JSON_GLOBS:
        paths = sorted(glob.glob(os.path.join(ROOT, pattern)))
        if not paths:
            print(f"skip: {pattern} (no matching file yet)")
            continue
        for path in paths:
            rel = os.path.relpath(path, ROOT)
            try:
                with open(path, encoding="utf-8") as fh:
                    json.load(fh)
            except (OSError, ValueError) as exc:
                print(f"FAIL: {rel}: {exc}")
                failures += 1
            else:
                print(f"ok:   {rel}")
    return failures


def check_links(readme="README.md"):
    failures = 0
    path = os.path.join(ROOT, readme)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    in_fence = False
    for lineno, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for target in LINK_RE.findall(line):
            if re.match(r"^[a-z][a-z0-9+.-]*:", target) or target.startswith("#"):
                continue
            file_part = target.split("#", 1)[0]
            if file_part and not os.path.exists(os.path.join(ROOT, file_part)):
                print(f"FAIL: {readme}:{lineno}: broken relative link {target}")
                failures += 1
    if not failures:
        print(f"ok:   {readme} relative links")
    return failures


def main():
    failures = check_json() + check_links()
    if failures:
        print(f"{failures} check(s) failed")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
