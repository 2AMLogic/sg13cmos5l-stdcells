#!/usr/bin/env python3
"""Generate design/item1-inventory.json from design/cells.json.

Usage: gen_item1_inventory.py [--check] [--catalog PATH] [--out PATH]

The inventory is the input to `klt signoff --attest 1` (decision record 0004).
Its `derived` array is two entries per catalog cell -- the SG13CMOS5L netlist
and the functional Verilog model -- each declaring its own generator's `--check`
as the freshness check. That is 100% derivable from the catalog, so it is
generated here rather than hand-maintained: a cell added to design/cells.json
without regenerating this file would otherwise leave CI green while the item-1
envelope attested one cell fewer than the library has (issue #144).

With --check, writes nothing and exits 1 if the committed inventory is missing
or stale, naming the paths that differ.

The generator emits the committed bytes exactly (`json.dumps(..., indent=2)`
plus a trailing newline), so regenerating does not move item 1's
`content_hash` and re-attests nothing. If a plain run leaves a diff, the
generator is wrong -- fix it rather than re-attesting over the diff.

The scalar fields and `sources` below are this file's own content, not derived:
they describe the attestation, and revising them -- including the ratified cell
count quoted in `description` -- is a decision-record change
(spec/decision-records/0004-block-kind-digital.md), not a catalog change. So
--check reports an added cell as missing `derived` paths, and ratifying the
larger catalog is the separate step that updates `description`.
"""
import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent

# Non-derived fields, verbatim from the ratified inventory.
HEAD = {
    "schema_version": 1,
    "kind": "t1-attestation-inventory",
    "t1_item": 1,
    "description": "T1 item 1 (design sources), full-custom digital sub-case: the ratified 40-cell catalog (design/cells.json) and the two generators that derive from it (design/gen_netlists.py for the SG13CMOS5L transistor-level netlists; rtl/gen_models.py for the functional Verilog models, which imports the shared Liberty-function parser from gen_netlists.py), plus every derived file. Each derived entry declares its generator's own --check as the freshness check (it rewrites nothing). No schematic capture and no synthesis step: the cells are generated, not hand-drawn."
}

SOURCES = [
    "design/cells.json",
    "design/gen_netlists.py",
    "rtl/gen_models.py"
]

# One (repo-relative path template, generator) per derived view. Each view
# contributes its cells sorted by path, in this order -- the committed order.
VIEWS = [
    ("design/netlists/{name}.spice", "design/gen_netlists.py"),
    ("rtl/{name}.v", "rtl/gen_models.py"),
]


def render(cells):
    """The inventory's exact bytes for `cells` (a list of catalog cell dicts)."""
    derived = []
    for template, generator in VIEWS:
        paths = sorted(template.format(name=c["name"]) for c in cells)
        derived += [
            {
                "path": path,
                "generator": generator,
                "check": {"argv": ["python3", "-I", generator, "--check"]},
            }
            for path in paths
        ]
    doc = dict(HEAD, sources=list(SOURCES), derived=derived)
    return json.dumps(doc, indent=2) + "\n"


def stale_reason(committed, want):
    """Why `committed` (text, or None if missing) is not `want`, or None."""
    if committed is None:
        return "missing"
    if committed == want:
        return None
    try:
        have_paths = [e["path"] for e in json.loads(committed)["derived"]]
    except (ValueError, KeyError, TypeError):
        return "not a readable inventory with a `derived` array"
    want_paths = [e["path"] for e in json.loads(want)["derived"]]
    if have_paths == want_paths:
        return (f"the same {len(want_paths)} path(s), but an entry or a "
                "non-derived field differs")
    missing = [p for p in want_paths if p not in set(have_paths)]
    extra = [p for p in have_paths if p not in set(want_paths)]
    parts = []
    if missing:
        parts.append("absent from the inventory: " + ", ".join(missing))
    if extra:
        parts.append("no catalog cell: " + ", ".join(extra))
    if not parts:
        parts.append("the same paths in a different order")
    return "; ".join(parts)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true",
                    help="verify the committed inventory is fresh; write nothing")
    ap.add_argument("--catalog", type=pathlib.Path, default=HERE / "cells.json")
    ap.add_argument("--out", type=pathlib.Path, default=HERE / "item1-inventory.json")
    args = ap.parse_args(argv)

    cells = json.loads(args.catalog.read_text())["cells"]
    want = render(cells)

    if args.check:
        committed = args.out.read_text() if args.out.is_file() else None
        reason = stale_reason(committed, want)
        if reason is not None:
            print(f"gen_item1_inventory: {args.out}: {reason}", file=sys.stderr)
            print("gen_item1_inventory: regenerate with "
                  "`python3 -I design/gen_item1_inventory.py` and re-attest item 1 "
                  "if the bytes move (see manifests/README.md)", file=sys.stderr)
            return 1
        print(f"gen_item1_inventory: inventory fresh "
              f"({len(json.loads(want)['derived'])} derived entries, {len(cells)} cells)")
        return 0

    args.out.write_text(want)
    print(f"gen_item1_inventory: wrote {args.out} "
          f"({len(json.loads(want)['derived'])} derived entries, {len(cells)} cells)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
