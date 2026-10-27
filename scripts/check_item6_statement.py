#!/usr/bin/env python3
"""Check verification/item6-not-applicable.md against spec/target-spec.md (issue #28).

Fails when the statement's recorded SHA-256 differs from the spec file, or when
the statement's row names differ from the spec's Parameters table.
"""
import argparse
import hashlib
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def table_rows(text, header):
    """First-column cells of the markdown table whose header row starts with `header`."""
    rows, in_table = [], False
    for line in text.splitlines():
        if not line.startswith("|"):
            if in_table:
                break
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not in_table:
            in_table = cells[0] == header
        elif not set(cells[0]) <= set("-: "):
            rows.append(cells[0])
    return rows


def check(spec_path, statement_path):
    spec = pathlib.Path(spec_path).read_bytes()
    statement = pathlib.Path(statement_path).read_text(encoding="utf-8")
    errors = []

    m = re.search(r"SHA-256:\s*([0-9a-f]{64})", statement)
    actual = hashlib.sha256(spec).hexdigest()
    if not m:
        errors.append("statement records no SHA-256 of the spec")
    elif m.group(1) != actual:
        errors.append(f"spec hash changed: statement has {m.group(1)}, spec is {actual}")

    want = table_rows(spec.decode("utf-8"), "Parameter")
    have = table_rows(statement, "Parameter")
    if not want:
        errors.append("no Parameters table found in the spec")
    for r in want:
        if r not in have:
            errors.append(f"spec row missing from statement: {r}")
    for r in have:
        if r not in want:
            errors.append(f"statement row not in spec: {r}")
    if len(set(have)) != len(have):
        errors.append("statement lists a row more than once")
    return errors


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--spec", default=ROOT / "spec/target-spec.md")
    p.add_argument("--statement", default=ROOT / "verification/item6-not-applicable.md")
    a = p.parse_args(argv)
    errors = check(a.spec, a.statement)
    for e in errors:
        print(f"FAIL {e}", file=sys.stderr)
    if not errors:
        print("ok   item 6 statement matches spec/target-spec.md")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
