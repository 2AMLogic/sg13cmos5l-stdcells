#!/usr/bin/env python3
"""Coverage check for a characterized corner `.lib` (issue #85).

For every cell in design/cells.json: the cell must appear in the library and
every timing arc must carry both a rise and a fall delay table of the full
7 x 7 grid. Cells absent from the library are reported, never dropped, so a
partial corner shows up as a non-zero exit. Values are SIMULATED.

    python3 -I sim/characterize/check_lib_coverage.py records/<corner>.lib

Exit 0 only if all cells in design/cells.json are present with both edges.
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import margin as m

ROOT = pathlib.Path(__file__).resolve().parents[2]
GRID = 7


def check(lib_text, expected):
    lib = m.parse_liberty(lib_text)
    pts, missing = m.compute(lib)
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
            "unexpected": sorted(cells - set(expected))}


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    expected = [c["name"] for c in json.load(open(ROOT / "design/cells.json"))["cells"]]
    r = check(pathlib.Path(argv[1]).read_text(), expected)
    print(f"cells present {len(r['present'])}/{len(expected)}; absent {r['absent']}")
    print(f"arc tables missing {len(r['missing_tables'])}; not {GRID}x{GRID} {len(r['short_tables'])}; "
          f"cells lacking rise/fall {r['cells_without_both_edges']}; unexpected {r['unexpected']}")
    ok = not (r["absent"] or r["missing_tables"] or r["short_tables"]
              or r["cells_without_both_edges"] or r["unexpected"])
    print("COVERAGE COMPLETE" if ok else "COVERAGE INCOMPLETE")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
