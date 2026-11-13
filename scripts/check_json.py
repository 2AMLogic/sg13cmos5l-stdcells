#!/usr/bin/env python3
"""Validate committed JSON config/evidence files and README relative links.

Run from anywhere: `python3 -I scripts/check_json.py`. Every tracked `*.json`
file is parsed, except the tool-installed trees listed in TOOL_TREES. There is
no path list to keep in step with the evidence: a record is covered as soon as
it is tracked. An empty file set is a failure, not a green run. Exit 1 on any
parse error or broken link.
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Installed and refreshed by tooling (Loom, agent skills), so their JSON is not
# this repo's evidence and a tool upgrade must not be able to turn this gate
# red. Everything else tracked in the repo is in scope.
TOOL_TREES = (".loom/", ".claude/", ".agents/")

LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")


def tracked_json_paths():
    """Repo-relative paths of every tracked *.json file outside TOOL_TREES.

    Raises subprocess.CalledProcessError if `git ls-files` cannot run (no git,
    or not a repository): the caller turns that into a failure, so a gate that
    cannot enumerate its inputs never reports success.
    """
    listing = subprocess.run(
        ["git", "ls-files", "-z", "--", "*.json"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return sorted(
        rel
        for rel in listing.split("\0")
        if rel and not rel.startswith(TOOL_TREES)
    )


def check_json():
    try:
        paths = tracked_json_paths()
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"FAIL: cannot list tracked *.json files with git: {exc}")
        return 1
    if not paths:
        print("FAIL: git tracks no *.json file outside " + ", ".join(TOOL_TREES))
        return 1
    failures = 0
    for rel in paths:
        try:
            with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
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
