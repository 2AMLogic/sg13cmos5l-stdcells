#!/usr/bin/env python3
"""Checks for the corner-matrix timing-arc evidence (issue #120).

The arc list decides what the corner sweep measures, so it is checked against
two things it must not be allowed to drift from:

  * the **RTL models** -- `gen_functional.logic()` parses the boolean
    expressions in `design/cells.json` by itself, and the arcs it derives are
    only as good as that parse. Every cell's every vector is compared against
    the exhaustive truth tables `rtl/<cell>.v` prints through iverilog (the
    same oracle `compare.py` uses), so a mis-parsed expression fails here
    rather than silently mis-measuring the library.
  * the **characterized Liberty** -- the arc count must equal the number of
    `timing ()` groups in the recorded TT `.lib`, so an arc the
    characterization found but this sweep does not measure (or vice versa) is
    a failure.

Then, if `records/corners.report.json` exists, the recorded report is checked
for shape: every arc measured at every ratified corner, every measurement
limited and spec-row tagged. Whether those measurements *passed* is the
report's own verdict and is printed, not asserted -- a recorded failure is
evidence, not a broken test (spec/decision-records/0005).

    python3 verification/functional/test_arcs.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))

import gen_functional as g  # noqa: E402

TT_LIB = ROOT / "sim" / "characterize" / "records" / "s5l_tt_1p20v_25c.lib"
REPORT = HERE / "records" / "corners.report.json"


def check_logic_against_rtl() -> int:
    """`logic()` must reproduce the RTL truth tables exactly, every vector."""
    import compare

    rtl = compare.rtl_tables()
    if not rtl:
        raise SystemExit("no RTL truth tables; iverilog/vvp produced nothing")
    checked = 0
    for c in g.cells():
        ins = c["inputs"]
        for o, expr in c["outputs"].items():
            f = g.logic(expr, ins)
            for k, vec in enumerate(g.vectors(len(ins))):
                want = rtl.get((c["name"], o, k))
                if want is None:
                    raise SystemExit(f"no RTL table for {c['name']}.{o}[{k}]")
                got = int(f({p: bool(vec[i]) for i, p in enumerate(ins)}))
                if got != want:
                    raise SystemExit(
                        f"logic({expr!r}) disagrees with rtl/{c['name']}.v at "
                        f"vector {k} ({dict(zip(ins, vec))}): {got} != {want}")
                checked += 1
    return checked


def check_arcs_against_liberty(arcs: list[dict]) -> None:
    """One arc per `timing ()` group of the recorded TT Liberty, no gaps."""
    gaps = [a for a in arcs if a["side"] is None]
    if gaps:
        raise SystemExit("arcs with no propagating state (declared gaps): "
                         + ", ".join(f"{a['cell']}.{a['pin']}->{a['output']}"
                                     for a in gaps))
    cells = {c["name"] for c in g.cells()}
    covered = {a["cell"] for a in arcs}
    if covered != cells:
        raise SystemExit(f"arcs cover {len(covered)} cells, not all {len(cells)}: "
                         f"missing {sorted(cells - covered)}")
    groups = len(re.findall(r"^\s*timing \(\)", TT_LIB.read_text(), re.M))
    if groups != len(arcs):
        raise SystemExit(
            f"{len(arcs)} derived arcs but {groups} `timing ()` groups in "
            f"{TT_LIB.relative_to(ROOT)}: the sweep and the characterized "
            "Liberty disagree about which arcs exist")


def check_report(arcs: list[dict]) -> None:
    """Shape of the recorded corner report. Verdict is printed, not asserted."""
    report = json.loads(REPORT.read_text())
    want = {g.arc_meas_name(a, e) for a in arcs for e in ("r", "f")}
    rollup = {m["name"]: m for m in report["measurements"]}
    if set(rollup) != want:
        raise SystemExit(f"report measures {len(rollup)} names, expected "
                         f"{len(want)}: missing {sorted(want - set(rollup))[:5]}")
    for name, m in rollup.items():
        if not m.get("limits", {}).get("max"):
            raise SystemExit(f"{name} carries no limits.max")
        if m.get("spec_row") != g.SPEC_ROW:
            raise SystemExit(f"{name} is not tagged spec_row {g.SPEC_ROW!r}")

    corner_ids = [c["corner_id"] for c in report["corners"]]
    if len(corner_ids) != len(g.char.CORNERS):
        raise SystemExit(f"report has corners {corner_ids}, expected one per "
                         f"ratified corner ({list(g.char.CORNERS)})")
    for corner in report["corners"]:
        names = {m["name"] for m in corner["measurements"]}
        if names != want:
            raise SystemExit(f"corner {corner['corner_id']} measures "
                             f"{len(names)} of {len(want)} arcs: missing "
                             f"{sorted(want - names)[:5]}")

    limit_s = g.LIMIT_NS * 1e-9
    worst = max(
        ((m["value"], m["name"], c["corner_id"])
         for c in report["corners"] for m in c["measurements"]
         if m.get("value") is not None),
        default=None)
    print(f"report: status {report['status']}, {len(corner_ids)} corners "
          f"({', '.join(corner_ids)}), {len(want)} arc delays each, "
          f"limit {g.LIMIT_NS} ns")
    if worst:
        print(f"  worst arc: {worst[1]} at {worst[2]} = {worst[0] * 1e9:.4f} ns "
              f"(margin {(limit_s - worst[0]) * 1e9:+.4f} ns)")
    for corner in report["corners"]:
        bad = [m["name"] for m in corner["measurements"] if m["status"] != "pass"]
        print(f"  {corner['corner_id']}: {corner['status']}, "
              f"{len(corner['measurements']) - len(bad)}/{len(want)} arcs pass"
              + (f"; over the bound: {', '.join(bad)}" if bad else ""))


def main() -> int:
    arcs = g.arcs()
    checked = check_logic_against_rtl()
    print(f"ok: logic() matches the RTL truth tables on {checked} vectors")
    check_arcs_against_liberty(arcs)
    print(f"ok: {len(arcs)} arcs, 0 gaps, all {len(g.cells())} cells, one per "
          f"`timing ()` group of the recorded TT Liberty")
    if REPORT.exists():
        check_report(arcs)
    else:
        print(f"skip: {REPORT.relative_to(ROOT)} not recorded yet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
