#!/usr/bin/env python3
"""Fail when a ROADMAP.md `## Now` row names its work item by issue number (issue #180).

A Now row is by definition startable today, so it is built and closed within
the hour; a row that carries a leading `(#N)` work-item reference is stale at
merge time. Live issue numbers belong in WORK_PLAN.md, the generated label
view. Explanatory references inside a row's prose (#129, #28) and PR
references are not work-item references and pass.

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
WORK_ITEM_REF = re.compile(r"^([0-9]+\. \*\*.*\*\* \()#([0-9]+)")


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
    rows = 0
    for offset, line in enumerate(body):
        lineno = start + offset
        if NUMBERED_ROW.match(line):
            rows += 1
        m = WORK_ITEM_REF.match(line)
        if m:
            errors.append(f"line {lineno}: ## Now row cites #{m.group(2)} as "
                          "its work item; live issue numbers belong in "
                          "WORK_PLAN.md, not ROADMAP.md ## Now")
    if rows == 0:
        errors.append("## Now parses to zero rows; the check cannot run "
                      "(restore the numbered rows or update this script)")
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
        print("ok   ROADMAP.md ## Now cites no work-item issue number")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
