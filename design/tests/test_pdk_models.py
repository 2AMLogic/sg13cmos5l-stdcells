"""Truth tables for all 40 generated netlists against the REAL PDK models.

Counterpart of test_gen_netlists.py, which uses logic-level stubs. One
`ngspice -b` per cell, serial, tt corner / 27 C only (PSP103 OSDI preloaded,
`mos_tt` of cornerMOSlv.lib). Skipped when the PDK or an OSDI-capable ngspice
is absent (CI without `scripts/setup-env.sh` stays green). Results are
SIMULATED. Run: `source .cache/env.sh && python3 -m unittest design.tests.test_pdk_models`
or `python3 design/tests/test_pdk_models.py [--record out.json]`.
"""
import itertools
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

DESIGN = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DESIGN))
import gen_netlists as gn  # noqa: E402

CAT = json.load(open(DESIGN / "cells.json"))
NETLISTS = DESIGN / "netlists"
PDK_ROOT = os.environ.get("PDK_ROOT", "")
MODELS = pathlib.Path(PDK_ROOT) / "ihp-sg13cmos5l/libs.tech/ngspice/models/cornerMOSlv.lib"
OSDI = pathlib.Path(PDK_ROOT) / "ihp-sg13cmos5l/libs.tech/ngspice/osdi/psp103.osdi"
NGSPICE = shutil.which("ngspice")
HAVE_PDK = bool(PDK_ROOT) and MODELS.exists() and OSDI.exists() and NGSPICE
VDD = 1.2
TOL_V = 0.1


def run_cell(cell):
    """Return a list of (vector, pin, volts) for every input combination."""
    name, ins, outs = cell["name"], cell["inputs"], sorted(cell["outputs"])
    lines = [
        name,
        f".lib {MODELS} mos_tt",
        f'.include "{NETLISTS / (name + ".spice")}"',
        f"Vdd vdd 0 {VDD}",
    ]
    lines += [f"V{p} {p} 0 0" for p in ins]
    lines += [f"X1 {' '.join(ins + outs)} vdd 0 {name}", ".control", f"pre_osdi {OSDI}"]
    combos = list(itertools.product((0, 1), repeat=len(ins)))
    for bits in combos:
        lines += [f"alter V{p} dc = {VDD * b}" for p, b in zip(ins, bits)]
        lines += ["op"] + [f'echo "RES $&v({o})"' for o in outs]
    lines += [".endc", ".end"]
    with tempfile.TemporaryDirectory() as td:
        deck = pathlib.Path(td) / "d.cir"
        deck.write_text("\n".join(lines) + "\n")
        r = subprocess.run([NGSPICE, "-b", str(deck)], capture_output=True, text=True, timeout=300)
    out = r.stdout + r.stderr
    res = [float(x) for x in re.findall(r"RES\s+(\S+)", out)]
    if len(res) != len(combos) * len(outs):
        raise AssertionError(f"{name}: ngspice produced {len(res)} results\n{out[-800:]}")
    errs = [l for l in out.splitlines() if re.match(r"\s*(Error|.*unknown subckt)", l, re.I)]
    if errs:
        raise AssertionError(f"{name}: ngspice errors: {errs[:3]}")
    k, rows = 0, []
    for bits in combos:
        vec = dict(zip(ins, bits))
        for o in outs:
            rows.append((vec, o, res[k]))
            k += 1
    return rows


def check_cell(cell):
    """Return (n_checks, worst_logic_error_V, failures)."""
    fails, worst, n = [], 0.0, 0
    for vec, pin, v in run_cell(cell):
        want = gn.evaluate(gn.parse(cell["outputs"][pin]), vec) * VDD
        worst = max(worst, abs(v - want))
        n += 1
        if abs(v - want) > TOL_V:
            fails.append(f"{cell['name']} {vec} {pin}: got {v:.4f} V want {want:.1f} V")
    return n, worst, fails


@unittest.skipUnless(HAVE_PDK, "PDK / OSDI ngspice not installed (scripts/setup-env.sh)")
class PdkModelTruthTables(unittest.TestCase):
    def test_all_40_truth_tables_real_models(self):
        self.assertEqual(len(CAT["cells"]), 40)
        for cell in CAT["cells"]:
            with self.subTest(cell=cell["name"]):
                _, _, fails = check_cell(cell)
                self.assertEqual(fails, [])


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--record":
        if not HAVE_PDK:
            sys.exit("PDK not installed; source .cache/env.sh")
        rows, bad = [], 0
        for cell in CAT["cells"]:
            n, worst, fails = check_cell(cell)
            bad += len(fails)
            rows.append({"cell": cell["name"], "vectors_x_outputs": n, "worst_logic_error_v": round(worst, 6), "failures": fails})
        json.dump({"corner": "tt", "temp_c": 27, "vdd_v": VDD, "tol_v": TOL_V, "status": "simulated", "cells": rows}, open(sys.argv[2], "w"), indent=1)
        print(f"{len(rows)} cells, {sum(r['vectors_x_outputs'] for r in rows)} checks, {bad} failures")
        sys.exit(1 if bad else 0)
    unittest.main()
