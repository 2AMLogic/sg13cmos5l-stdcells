#!/usr/bin/env python3
"""Coverage check for a characterized corner (issue #85).

For every cell in design/cells.json: the cell must appear in the library and
every timing arc must carry both a rise and a fall delay table of the full
7 x 7 grid. Cells absent from the library are reported, never dropped, so a
partial corner shows up as a non-zero exit. Values are SIMULATED.

A corner may be recorded as SEVERAL `.lib` files. Recorded results are
append-only, and a cell whose grid outruns the fleet job ceiling has to be
characterized on its own (klayout-tools#5410), so the FF corner is one
39-cell file plus one `s5l_mux4_1` file rather than a rewritten library.
Pass every file of the corner and they are checked as ONE record:

    python3 -I sim/characterize/check_lib_coverage.py records/<corner>.lib [more.lib ...]

A combined record must be a partition of one corner, so two guards hold it
honest: a cell appearing in more than one file is reported
(`duplicate_cells`) instead of being silently unioned, and files that do not
all declare the same corner are refused (`corner_mismatch`) -- coverage can
never be manufactured by pairing two different corners.

Exit 0 only if all cells in design/cells.json are present with both edges.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import margin as m

ROOT = pathlib.Path(__file__).resolve().parents[2]
GRID = 7


def check(lib_texts, expected):
    """Check one corner, recorded as one Liberty text or a list of them."""
    if isinstance(lib_texts, str):
        lib_texts = [lib_texts]
    pts, missing, corners = [], [], []
    first_file, duplicate = {}, set()
    for i, text in enumerate(lib_texts):
        lib = m.parse_liberty(text)
        corners.append(m.corner_name(lib))
        p, miss = m.compute(lib)
        for cell in sorted({x.cell for x in p}):
            if cell in first_file:
                duplicate.add(cell)
            else:
                first_file[cell] = i
        pts += p
        missing += miss
    cells = {p.cell for p in pts}
    absent = sorted(set(expected) - cells)
    per_arc = {}
    for p in pts:
        k = (p.cell, p.out_pin, p.related_pin, p.when, p.edge)
        per_arc[k] = per_arc.get(k, 0) + 1
    short = sorted(k for k, n in per_arc.items() if n != GRID * GRID)
    cells_without_both = sorted(
        c for c in cells
        if {"rise", "fall"} - {k[4] for k in per_arc if k[0] == c})
    return {"present": sorted(cells & set(expected)), "absent": absent,
            "missing_tables": missing, "short_tables": short,
            "cells_without_both_edges": cells_without_both,
            "unexpected": sorted(cells - set(expected)),
            "duplicate_cells": sorted(duplicate),
            "corner_mismatch": sorted(set(corners)) if len(set(corners)) > 1 else [],
            "corner": corners[0] if len(set(corners)) == 1 else None}


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    expected = [c["name"] for c in json.load(open(ROOT / "design/cells.json"))["cells"]]
    paths = [pathlib.Path(a) for a in argv[1:]]
    r = check([p.read_text() for p in paths], expected)
    print(f"corner {r['corner']}; record of {len(paths)} file(s): "
          + ", ".join(p.name for p in paths))
    print(f"cells present {len(r['present'])}/{len(expected)}; absent {r['absent']}")
    print(f"arc tables missing {len(r['missing_tables'])}; not {GRID}x{GRID} {len(r['short_tables'])}; "
          f"cells lacking rise/fall {r['cells_without_both_edges']}; unexpected {r['unexpected']}")
    if r["duplicate_cells"]:
        print(f"ERROR cells recorded in more than one file: {r['duplicate_cells']}")
    if r["corner_mismatch"]:
        print(f"ERROR files do not all declare one corner: {r['corner_mismatch']}")
    ok = not (r["absent"] or r["missing_tables"] or r["short_tables"]
              or r["cells_without_both_edges"] or r["unexpected"]
              or r["duplicate_cells"] or r["corner_mismatch"])
    print("COVERAGE COMPLETE" if ok else "COVERAGE INCOMPLETE")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
