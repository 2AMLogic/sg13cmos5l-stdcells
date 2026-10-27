#!/usr/bin/env python3
"""Run the exhaustive cocotb + Icarus test over every generated model.

Usage: .venv/bin/python rtl/tests/run_tests.py [cell ...]

Needs cocotb and iverilog/vvp on PATH. Cells run one after another (one job).
Build products go to sim/build/rtl-<cell>, which is gitignored. Exit 0 only if
every selected cell passes and all 40 catalog cells were covered.
"""
import json
import os
import pathlib
import sys

from cocotb_tools.runner import get_runner

HERE = pathlib.Path(__file__).resolve().parent
RTL = HERE.parent
ROOT = RTL.parent
EXPECTED_CELLS = 40


def main(argv):
    names = [c["name"] for c in json.loads((ROOT / "design" / "cells.json").read_text())["cells"]]
    if not argv and len(names) != EXPECTED_CELLS:
        print(f"expected {EXPECTED_CELLS} catalog cells, found {len(names)}", file=sys.stderr)
        return 1
    unknown = [a for a in argv if a not in names]
    if unknown:
        print(f"not catalog cells: {unknown}", file=sys.stderr)
        return 1
    failed = []
    for name in argv or names:
        build = ROOT / "sim" / "build" / f"rtl-{name}"
        os.environ["CELL"] = name
        os.environ["PYTHONPATH"] = str(HERE)
        runner = get_runner("icarus")
        runner.build(sources=[RTL / f"{name}.v"], hdl_toplevel=name, build_dir=build, always=True, timescale=("1ns", "1ps"))
        results = runner.test(hdl_toplevel=name, test_module="test_exhaustive", build_dir=build)
        _, ntests, nfail = _count(results)
        if nfail or ntests != 1:
            failed.append(name)
    if failed:
        print(f"FAILED: {failed}", file=sys.stderr)
        return 1
    print(f"all {len(argv or names)} cells passed exhaustively")
    return 0


def _count(results_xml):
    import xml.etree.ElementTree as ET

    cases = list(ET.parse(results_xml).getroot().iter("testcase"))
    bad = [c for c in cases if c.find("failure") is not None or c.find("error") is not None]
    return results_xml, len(cases), len(bad)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
