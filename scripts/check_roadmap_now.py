#!/usr/bin/env python3
"""Fail when ROADMAP.md `## Now` carries a hand-written numbered work row (issue #186).

`## Now` is a pointer, not a second work queue: what can start today lives
in WORK_PLAN.md, regenerated from live GitHub label state, so it cannot go
stale. A hand-written Now row is built and closed within the hour — stale
by the time it merges — so any numbered row under `## Now` is rejected,
whether or not it cites an issue number. Prose references inside the
pointer text (#129, #28) and PR references are not work rows and pass.

Hermetic by construction: reads the file, no network, no gh call.
"""
import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

NOW_HEADING = re.compile(r"^##\s+Now\s*$")
NEXT_HEADING = re.compile(r"^##\s")
NUMBERED_ROW = re.compile(r"^[0-9]+\.\s")


def now_section(text):
    """(first_line_number, body_lines) of the `## Now` section, or None."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if NOW_HEADING.match(line):
            start = i + 1
            break
    if start is None:
        return None
    body = []
    for line in lines[start:]:
        if NEXT_HEADING.match(line):
            break
        body.append(line)
    return start + 1, body


def check(text):
    errors = []
    sec = now_section(text)
    if sec is None:
        return ["ROADMAP.md has no `## Now` heading; the check cannot run "
                "(rename the section back or update this script)"]
    start, body = sec
    for offset, line in enumerate(body):
        if NUMBERED_ROW.match(line):
            lineno = start + offset
            errors.append(f"line {lineno}: ## Now carries a hand-written "
                          "numbered work row; ## Now is a pointer to "
                          "WORK_PLAN.md, not a queue — remove the row")
    return errors


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--file", default=ROOT / "ROADMAP.md",
                   help="the roadmap file to check (default: <repo>/ROADMAP.md)")
    a = p.parse_args(argv)
    text = pathlib.Path(a.file).read_text(encoding="utf-8")
    errors = check(text)
    for e in errors:
        print(f"FAIL {e}", file=sys.stderr)
    if not errors:
        print("ok   ROADMAP.md ## Now is a WORK_PLAN.md pointer with no "
              "hand-written rows")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
