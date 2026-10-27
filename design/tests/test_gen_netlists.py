"""Tests for design/gen_netlists.py and the committed design/netlists/*.spice.

The committed netlists are parsed independently of the generator: a switch-
level truth-table check runs on all 40 cells, and a few cells (plus a load of
all 40) also go through ngspice with logic-level stub models
(design/tests/stub_models.inc, not the PDK models).
"""
import itertools
import json
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
STUB = pathlib.Path(__file__).resolve().parent / "stub_models.inc"
NGSPICE = shutil.which("ngspice")


def parse_netlist(text):
    devs, ports = [], None
    for line in text.splitlines():
        if line.startswith(".subckt"):
            ports = line.split()[2:]
        elif line.startswith("XM"):
            t = line.split()
            params = dict(p.split("=") for p in t[6:])
            devs.append((t[5], t[1], t[2], t[3], params))
    return ports, devs


def switch_level(ports, devs, vec):
    val = dict(vec, VDD=1, VSS=0)
    for _ in range(len(devs) + 2):
        parent = {}

        def find(x):
            parent.setdefault(x, x)
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for model, d, g, s, _ in devs:
            gv = val.get(g)
            if gv is None:
                continue
            if (model == "sg13_lv_nmos" and gv == 1) or (model == "sg13_lv_pmos" and gv == 0):
                parent[find(d)] = find(s)
        new = dict(vec, VDD=1, VSS=0)
        nodes = {n for _, d, _, s, _ in devs for n in (d, s)}
        for n in nodes:
            hi, lo = find(n) == find("VDD"), find(n) == find("VSS")
            if hi and lo:
                raise AssertionError(f"short between VDD and VSS via {n}")
            if hi or lo:
                new[n] = int(hi)
        if new == val:
            return val
        val = new
    return val


class GeneratorTest(unittest.TestCase):
    def test_freshness_check_passes_on_committed(self):
        self.assertEqual(gn.check(gn.generate(CAT), NETLISTS), [])

    def test_forty_netlists_committed(self):
        self.assertEqual(len(list(NETLISTS.glob("*.spice"))), 40)

    def test_check_detects_stale_missing_and_stray(self):
        files = gn.generate(CAT)
        with tempfile.TemporaryDirectory() as td:
            out = pathlib.Path(td)
            for n, t in files.items():
                (out / n).write_text(t)
            self.assertEqual(gn.check(files, out), [])
            (out / "s5l_inv_1.spice").write_text("x\n")
            (out / "s5l_inv_2.spice").unlink()
            (out / "s5l_extra_1.spice").write_text("x\n")
            errs = " ".join(gn.check(files, out))
            self.assertIn("stale", errs)
            self.assertIn("missing", errs)
            self.assertIn("stray", errs)

    def test_cli_check_exit_codes(self):
        self.assertEqual(gn.main(["--check"]), 0)
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(gn.main(["--check", "--out", td]), 1)

    def test_sizing_fits_row(self):
        for p in NETLISTS.glob("*.spice"):
            _, devs = parse_netlist(p.read_text())
            for model, _, _, _, prm in devs:
                w, ng = int(prm["w"][:-1]), int(prm["ng"])
                cap = gn.FINGER_MAX_N if model == "sg13_lv_nmos" else gn.FINGER_MAX_P
                self.assertLessEqual(w / ng, cap, p.name)
                self.assertEqual(w % ng, 0, p.name)

    def test_widest_stacks_present(self):
        for name in ("s5l_nor4_1", "s5l_nand4_1", "s5l_mux4_1", "s5l_xor2_1", "s5l_xnor2_1"):
            self.assertTrue((NETLISTS / f"{name}.spice").exists())

    def test_truth_tables_switch_level_all_cells(self):
        for cell in CAT["cells"]:
            ports, devs = parse_netlist((NETLISTS / f"{cell['name']}.spice").read_text())
            self.assertEqual(ports, cell["inputs"] + sorted(cell["outputs"]) + ["VDD", "VSS"])
            for bits in itertools.product((0, 1), repeat=len(cell["inputs"])):
                vec = dict(zip(cell["inputs"], bits))
                got = switch_level(ports, devs, vec)
                for pin, fn in cell["outputs"].items():
                    want = gn.evaluate(gn.parse(fn), vec)
                    self.assertEqual(got.get(pin), want, f"{cell['name']} {vec} {pin}")


@unittest.skipUnless(NGSPICE, "ngspice not installed")
class NgspiceTest(unittest.TestCase):
    def run_ngspice(self, deck):
        with tempfile.TemporaryDirectory() as td:
            f = pathlib.Path(td) / "d.cir"
            f.write_text(deck)
            r = subprocess.run([NGSPICE, "-b", str(f)], capture_output=True, text=True, timeout=300)
        return r.stdout + r.stderr

    def test_all_40_load(self):
        lines = ["load test", f'.include "{STUB}"']
        for c in CAT["cells"]:
            lines.append(f'.include "{NETLISTS / (c["name"] + ".spice")}"')
        lines.append("Vdd vdd 0 1.2")
        for i, c in enumerate(CAT["cells"]):
            nets = [f"i{i}_{p}" for p in c["inputs"]] + [f"o{i}_{p}" for p in sorted(c["outputs"])]
            for p in c["inputs"]:
                lines.append(f"Vs{i}_{p} i{i}_{p} 0 0")
            lines.append(f"X{i} {' '.join(nets)} vdd 0 {c['name']}")
        lines += [".op", ".end"]
        out = self.run_ngspice("\n".join(lines))
        self.assertNotIn("Error", out)
        self.assertNotIn("unknown subckt", out.lower())
        self.assertIn("No. of Data Rows", out)

    def truth_table(self, name):
        cell = next(c for c in CAT["cells"] if c["name"] == name)
        ins, outs = cell["inputs"], sorted(cell["outputs"])
        lines = [name, f'.include "{STUB}"', f'.include "{NETLISTS / (name + ".spice")}"', "Vdd vdd 0 1.2"]
        lines += [f"V{p} {p} 0 0" for p in ins]
        lines += [f"X1 {' '.join(ins + outs)} vdd 0 {name}", ".control", "set noaskquit"]
        combos = list(itertools.product((0, 1), repeat=len(ins)))
        for bits in combos:
            lines += [f"alter V{p} dc = {1.2 * b}" for p, b in zip(ins, bits)]
            lines += ["op"] + [f'echo "RES $&v({o})"' for o in outs]
        lines += ["quit", ".endc", ".end"]
        out = self.run_ngspice("\n".join(lines))
        res = [float(x) for x in re.findall(r"RES\s+(\S+)", out)]
        self.assertEqual(len(res), len(combos) * len(outs), out[-500:])
        k = 0
        for bits in combos:
            vec = dict(zip(ins, bits))
            for o in outs:
                want = gn.evaluate(gn.parse(cell["outputs"][o]), vec)
                self.assertAlmostEqual(res[k], 1.2 * want, delta=0.05, msg=f"{name} {vec}")
                k += 1

    def test_truth_tables_spot_check(self):
        for name in ("s5l_inv_1", "s5l_nand2_1", "s5l_nor2b_1", "s5l_a21oi_1", "s5l_xor2_1", "s5l_xnor2_1", "s5l_mux2_1", "s5l_mux4_1"):
            with self.subTest(cell=name):
                self.truth_table(name)


if __name__ == "__main__":
    unittest.main()
