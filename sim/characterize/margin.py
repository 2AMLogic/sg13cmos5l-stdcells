#!/usr/bin/env python3
"""Per-point timing-margin metric for characterized Liberty libraries (issue #83).

Definition (the single place it is defined; sim/characterize/README.md points here)::

    margin(cell, arc, slew, load, corner) = LIMIT_NS - measured_delay_ns

* A *point* is one entry of a ``cell_rise`` / ``cell_fall`` table, i.e. one
  (input slew, output load) grid pair of one timing arc of one cell in one
  corner's ``.lib``.
* An *arc* is (cell, output pin, related pin, ``when`` condition, edge), edge
  being ``rise`` or ``fall`` (the output edge).
* ``measured_delay_ns`` is the table value, converted to ns by the library's
  ``time_unit``. It is a SIMULATED delay, never a measurement.
* A point passes iff ``margin >= 0``. A negative margin is a recorded FAIL; no
  point is ever dropped. A missing arc table is reported, not skipped.
* The *binding corner* is the corner whose worst point has the least margin
  (ties go to the corner named first alphabetically).

``LIMIT_NS`` derivation. The ratified spec states no delay budget (spec/
target-spec.md, "Characterization grid" row; a combinational-only library has
no clock period). The one stated number that bounds a stage delay is the
ratified grid itself: the slew axis tops out at 2.5074 ns, and a stage whose
delay exceeds that is driving downstream pins outside the characterized slew
domain, where the tables extrapolate. ``LIMIT_NS`` is therefore the grid's
largest input slew, 2.5074 ns. It is a constant set before any result was
looked at; it must not be edited to make a result pass. It is a grid-validity
bound, not a timing-closure target; a real delay budget needs a decision
record (see the PR for #83).

    python3 sim/characterize/margin.py [LIB ...]      # default: records/*.lib
    python3 sim/characterize/margin.py --csv out.csv LIB ...

Exit status: 0 all points pass, 1 any point fails or an arc table is missing,
2 usage/parse error.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent

# spec/target-spec.md "Characterization grid": largest input slew, ns.
GRID_MAX_SLEW_NS = 2.5074
LIMIT_NS = GRID_MAX_SLEW_NS

_UNIT_NS = {"1ns": 1.0, "1ps": 1e-3, "1us": 1e3, "10ps": 1e-2, "100ps": 1e-1}


# --------------------------------------------------------------- Liberty parse
@dataclass
class Group:
    name: str
    args: list
    attrs: dict = field(default_factory=dict)
    children: list = field(default_factory=list)


_TOKEN = re.compile(r'"[^"]*"|[A-Za-z_][\w.$\[\]]*|[-+0-9.eE]+|[(){}:;,]')


def _strip(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    text = re.sub(r"//[^\n]*", " ", text)
    return text.replace("\\\n", " ")


def parse_liberty(text: str) -> Group:
    toks = _TOKEN.findall(_strip(text))
    pos = 0

    def parse_args():
        nonlocal pos
        args, cur = [], []
        pos += 1  # (
        while toks[pos] != ")":
            if toks[pos] == ",":
                args.append(" ".join(cur)); cur = []
            else:
                cur.append(toks[pos].strip('"'))
            pos += 1
        if cur:
            args.append(" ".join(cur))
        pos += 1  # )
        return args

    def parse_body(g: Group):
        nonlocal pos
        while pos < len(toks) and toks[pos] != "}":
            name = toks[pos]; pos += 1
            if toks[pos] == ":":
                pos += 1
                val = []
                while toks[pos] != ";":
                    val.append(toks[pos].strip('"')); pos += 1
                pos += 1
                g.attrs[name] = " ".join(val)
            elif toks[pos] == "(":
                args = parse_args()
                if toks[pos] == "{":
                    pos += 1
                    child = Group(name, args)
                    parse_body(child)
                    pos += 1  # }
                    g.children.append(child)
                else:
                    if toks[pos] == ";":
                        pos += 1
                    g.attrs[name] = args
            else:
                raise ValueError(f"unexpected token {toks[pos]!r} after {name!r}")

    root = Group("<root>", [])
    parse_body(root)
    libs = [c for c in root.children if c.name == "library"]
    if len(libs) != 1:
        raise ValueError("expected exactly one library group")
    return libs[0]


def _floats(s) -> list:
    if isinstance(s, list):
        s = " ".join(s)
    return [float(x) for x in re.split(r"[\s,]+", s.strip()) if x]


# ---------------------------------------------------------------- the metric
@dataclass
class Point:
    corner: str
    cell: str
    out_pin: str
    related_pin: str
    when: str
    edge: str          # output edge: rise | fall
    slew_ns: float
    load_pf: float
    delay_ns: float
    margin_ns: float

    @property
    def passed(self) -> bool:
        return self.margin_ns >= 0.0


def margin(delay_ns: float, limit_ns: float = LIMIT_NS) -> float:
    """The metric. Negative means fail."""
    return limit_ns - delay_ns


def corner_name(lib: Group) -> str:
    name = lib.attrs.get("default_operating_conditions")
    return name if name else lib.args[0]


def compute(lib: Group, limit_ns: float = LIMIT_NS):
    """Return (points, missing) for one parsed library.

    ``missing`` lists (corner, cell, out_pin, related_pin, when, edge) for each
    timing arc that lacks a cell_rise or cell_fall table.
    """
    scale = _UNIT_NS.get(lib.attrs.get("time_unit", "1ns").replace(" ", ""))
    if scale is None:
        raise ValueError(f"unsupported time_unit {lib.attrs.get('time_unit')!r}")
    corner = corner_name(lib)
    points, missing = [], []
    for cell in (c for c in lib.children if c.name == "cell"):
        for pin in (c for c in cell.children if c.name == "pin"):
            for arc in (c for c in pin.children if c.name == "timing"):
                rel = arc.attrs.get("related_pin", "")
                when = arc.attrs.get("when", "")
                tables = {t.name: t for t in arc.children}
                for edge in ("rise", "fall"):
                    key = (corner, cell.args[0], pin.args[0], rel, when, edge)
                    tab = tables.get(f"cell_{edge}")
                    if tab is None:
                        missing.append(key)
                        continue
                    slews = _floats(tab.attrs["index_1"])
                    loads = _floats(tab.attrs["index_2"])
                    rows = [_floats(r) for r in tab.attrs["values"]]
                    if len(rows) != len(slews) or any(len(r) != len(loads) for r in rows):
                        raise ValueError(f"{key}: values shape does not match index_1/index_2")
                    for i, s in enumerate(slews):
                        for j, l in enumerate(loads):
                            d = rows[i][j] * scale
                            points.append(Point(*key, s * scale, l, d, margin(d, limit_ns)))
    return points, missing


def binding(points):
    """Least-margin point (the binding point); None when empty."""
    return min(points, key=lambda p: (p.margin_ns, p.corner, p.cell, p.related_pin, p.edge),
               default=None)


def binding_corner(points):
    return binding(points).corner if points else None


def load_libs(paths):
    pts, miss = [], []
    for p in paths:
        pp, mm = compute(parse_liberty(Path(p).read_text()))
        pts += pp
        miss += mm
    return pts, miss


COLS = ["corner", "cell", "out_pin", "related_pin", "when", "edge",
        "slew_ns", "load_pf", "delay_ns", "limit_ns", "margin_ns", "result"]


def write_table(points, out):
    w = csv.writer(out, lineterminator="\n")
    w.writerow(COLS)
    for p in points:
        w.writerow([p.corner, p.cell, p.out_pin, p.related_pin, p.when, p.edge,
                    p.slew_ns, p.load_pf, f"{p.delay_ns:.6g}", LIMIT_NS,
                    f"{p.margin_ns:.6g}", "pass" if p.passed else "FAIL"])


def summarize(points, missing):
    """Per-(corner, cell, arc, edge) rows: worst margin and pass/fail, then the binding corner."""
    rows = {}
    for p in points:
        k = (p.corner, p.cell, p.out_pin, p.related_pin, p.when, p.edge)
        if k not in rows or p.margin_ns < rows[k].margin_ns:
            rows[k] = p
    lines = ["# per-arc worst point (limit = %.4f ns)" % LIMIT_NS]
    for k, p in sorted(rows.items()):
        lines.append("%s %s %s<-%s%s %s worst_margin=%.4g ns @slew=%g load=%g -> %s" % (
            p.corner, p.cell, p.out_pin, p.related_pin,
            f"[{p.when}]" if p.when else "", p.edge, p.margin_ns, p.slew_ns,
            p.load_pf, "pass" if p.passed else "FAIL"))
    for k in sorted(missing):
        lines.append("MISSING arc table: " + " ".join(k))
    b = binding(points)
    if b:
        lines.append("binding corner: %s (least margin %.4g ns at %s %s<-%s %s slew=%g load=%g)" % (
            b.corner, b.margin_ns, b.cell, b.out_pin, b.related_pin, b.edge, b.slew_ns, b.load_pf))
    nfail = sum(not p.passed for p in points)
    lines.append("points=%d fail=%d missing_arcs=%d" % (len(points), nfail, len(missing)))
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("libs", nargs="*", help="Liberty files (default: records/*.lib)")
    ap.add_argument("--csv", help="write the per-point table here (default: stdout)")
    args = ap.parse_args(argv)
    paths = args.libs or sorted(str(p) for p in (HERE / "records").glob("*.lib"))
    if not paths:
        print("no .lib files", file=sys.stderr)
        return 2
    try:
        points, missing = load_libs(paths)
    except (OSError, ValueError, KeyError, IndexError) as e:
        print(f"margin.py: {e}", file=sys.stderr)
        return 2
    if args.csv:
        with open(args.csv, "w", newline="") as f:
            write_table(points, f)
    else:
        write_table(points, sys.stdout)
    print(summarize(points, missing), file=sys.stderr if not args.csv else sys.stdout)
    return 0 if points and not missing and all(p.passed for p in points) else 1


if __name__ == "__main__":
    sys.exit(main())
