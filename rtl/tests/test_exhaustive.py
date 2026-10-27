"""cocotb test: one generated model against its catalog function, every row.

Run through run_tests.py, which sets CELL to the catalog cell under test. The
expected value comes from evaluating the catalog expression here in Python, not
from the generated Verilog text, so the two views stay independent.
"""
import itertools
import json
import os
import pathlib
import re

import cocotb
from cocotb.triggers import Timer

CATALOG = pathlib.Path(__file__).resolve().parents[2] / "design" / "cells.json"
PY_OP = {"!": "~", "*": "&", "+": "|", "^": "^"}


def expected(expr, env):
    """Evaluate a Liberty-style expression over 0/1 ints; bit 0 of the result."""
    py = re.sub(r"[!*+^]", lambda m: PY_OP[m.group(0)], expr)
    return eval(py, {"__builtins__": {}}, env) & 1


@cocotb.test()
async def exhaustive(dut):
    cell = next(c for c in json.loads(CATALOG.read_text())["cells"] if c["name"] == os.environ["CELL"])
    pins = cell["inputs"]
    assert len(pins) <= 6, "exhaustive sweep assumes at most 6 inputs"
    rows = 0
    for bits in itertools.product((0, 1), repeat=len(pins)):
        env = dict(zip(pins, bits))
        for p, v in env.items():
            getattr(dut, p).value = v
        await Timer(1, unit="ns")
        for out, expr in cell["outputs"].items():
            got, want = int(getattr(dut, out).value), expected(expr, env)
            assert got == want, f"{cell['name']} {env}: {out}={got}, catalog {expr} gives {want}"
        rows += 1
    assert rows == 2 ** len(pins)
    dut._log.info("%s: %d rows checked", cell["name"], rows)
