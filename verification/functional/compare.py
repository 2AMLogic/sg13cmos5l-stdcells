#!/usr/bin/env python3
"""Compare simulated netlist truth tables to the rtl/ models bit-exactly (issue #82).

RTL side: iverilog/vvp over tb_rtl.v + rtl/s5l_*.v (exhaustive vectors).
Netlist side: the `klt sim` report of tt.request.json (TT, SIMULATED). Output
voltages are thresholded: < 0.1*VDD -> 0, > 0.9*VDD -> 1, anything between is
a failure (indeterminate level), never rounded.

    compare.py --report records/tt.report.json --out records/functional.tt.json
    compare.py --report ... --negative-control   # flip one RTL bit; must FAIL
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
VDD = 1.2
sys.path.insert(0, str(HERE))
import gen_functional as g  # noqa: E402


def rtl_tables() -> dict[tuple[str, str, int], int]:
    with tempfile.TemporaryDirectory() as td:
        vvp = Path(td) / "tb.vvp"
        srcs = sorted(str(p) for p in (ROOT / "rtl").glob("s5l_*.v"))
        subprocess.run(["iverilog", "-g2012", "-o", str(vvp), str(HERE / "tb_rtl.v"), *srcs], check=True)
        out = subprocess.run(["vvp", str(vvp)], check=True, capture_output=True, text=True).stdout
    t = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 4 and parts[0].startswith("s5l_"):
            t[(parts[0], parts[1], int(parts[2]))] = int(parts[3])
    return t


def netlist_levels(report: dict) -> dict[str, float]:
    (corner,) = report["corners"]
    return {m["name"]: m["value"] for m in corner["measurements"]}


def level(v: float | None) -> int | None:
    if v is None:
        return None
    return 0 if v < 0.1 * VDD else 1 if v > 0.9 * VDD else None


def compare(rtl: dict, volts: dict[str, float]) -> dict:
    cells = {}
    for c in g.cells():
        tests = []
        for o in c["outputs"]:
            for k in range(1 << len(c["inputs"])):
                want = rtl.get((c["name"], o, k))
                v = volts.get(g.meas_name(c["name"], o, k))
                got = level(v)
                tests.append({"output": o, "vector": k, "rtl": want, "netlist_v": v,
                              "netlist": got, "pass": want is not None and got == want})
        cells[c["name"]] = {"pass": all(t["pass"] for t in tests), "tests": tests}
    return {"label": "SIMULATED (ngspice, TT 1.20 V 25 C), never measured",
            "pass": all(c["pass"] for c in cells.values()),
            "cells_total": len(cells), "cells_passed": sum(c["pass"] for c in cells.values()),
            "cells": cells}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True, type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--negative-control", action="store_true")
    args = ap.parse_args()
    rtl = rtl_tables()
    if args.negative_control:
        key = next(iter(rtl))
        rtl[key] ^= 1  # deliberately wrong truth table
    res = compare(rtl, netlist_levels(json.loads(args.report.read_text())))
    if args.out and not args.negative_control:
        args.out.write_text(json.dumps(res, indent=1) + "\n")
    print(f"{res['cells_passed']}/{res['cells_total']} cells pass ({'PASS' if res['pass'] else 'FAIL'})")
    for n, c in res["cells"].items():
        if not c["pass"]:
            print(f"  FAIL {n}: " + ", ".join(f"{t['output']}[{t['vector']}]" for t in c["tests"] if not t["pass"]))
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
