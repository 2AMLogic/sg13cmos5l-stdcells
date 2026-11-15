"""Tests for design/gen_netlists.py and the committed design/netlists/*.spice.

design/gen_netlists.py is the SG13CMOS5L adapter (decision record 0006): it
merges design/cells.json with the `process` sizing block of
layout/sg13cmos5l-cells.config.json and delegates to the pinned upstream
generator (layout/vendor/sg13g2-stdcells/design/gen_netlists.py,
reuse.lock.json). The engine tests here pin that delegation -- the vendored
file by hash, the parser by identity -- and the committed netlists are parsed
independently of the generator: a switch-level truth-table check runs on all
40 cells, and a few cells (plus a load of all 40) also go through ngspice
with logic-level stub models (design/tests/stub_models.inc, not the PDK
models).
"""
import contextlib
import hashlib
import io
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
REPO = DESIGN.parent
sys.path.insert(0, str(DESIGN))
import gen_netlists as gn  # noqa: E402

CAT = json.load(open(DESIGN / "cells.json"))
NETLISTS = DESIGN / "netlists"
STUB = pathlib.Path(__file__).resolve().parent / "stub_models.inc"
NGSPICE = shutil.which("ngspice")
VENDORED = REPO / "layout" / "vendor" / "sg13g2-stdcells" / "design" / "gen_netlists.py"


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


def row_fit_layout(row_height_nm=3360, rail_width_nm=440):
    """A minimal layout dict shaped like sg13cmos5l-cells.config.json."""
    return {"layout": {"row_height_nm": row_height_nm, "rules": {"rail_width_nm": rail_width_nm}}}


class EngineTest(unittest.TestCase):
    """The adapter must run the pinned vendored engine, never a second copy."""

    def test_engine_is_the_pinned_vendored_file(self):
        self.assertEqual(pathlib.Path(gn.engine.__file__).resolve(), VENDORED.resolve())

    def test_vendored_engine_matches_the_reuse_pin(self):
        """sha256 of the vendored file equals the reuse.lock.json entry, so a
        hand-edit of the vendored copy fails here instead of drifting from the
        pin of record."""
        lock = json.load(open(REPO / "reuse.lock.json"))
        entries = [
            f
            for imp in lock["imports"]
            for f in imp["files"]
            if f["local"] == "layout/vendor/sg13g2-stdcells/design/gen_netlists.py"
        ]
        self.assertEqual(len(entries), 1)
        want = entries[0]["sha256"]
        got = hashlib.sha256(VENDORED.read_bytes()).hexdigest()
        self.assertEqual(got, want)

    def test_parser_is_the_engine_single_parser(self):
        """`parse`/`evaluate` are re-exports, so there is exactly one parser."""
        self.assertIs(gn.parse, gn.engine.parse)
        self.assertIs(gn.evaluate, gn.engine.evaluate)

    def test_config_is_catalog_plus_process(self):
        config = gn.build_config()
        self.assertEqual(config["cells"], CAT["cells"])
        proc = config["process"]
        self.assertEqual(proc["supply_v"], 1.2)
        self.assertEqual(proc["l_nm"], 130)
        self.assertEqual((proc["unit_n_nm"], proc["unit_p_nm"]), (740, 1120))
        self.assertEqual((proc["finger_max_n"], proc["finger_max_p"]), (1000, 1200))
        self.assertEqual((proc["nmos_model"], proc["pmos_model"]), ("sg13_lv_nmos", "sg13_lv_pmos"))
        self.assertEqual((proc["vdd_net"], proc["vss_net"]), ("VDD", "VSS"))


class RowFitRuleTest(unittest.TestCase):
    """The row-fit rule (decision record 0006) as an exercised rule, not a
    value pin: check_row_fit must reject any finger-cap sum over the row
    budget -- including a coordinated re-size that moves the config caps and
    every value pin together -- and it must raise, not assert, so `python -O`
    keeps the guard."""

    def test_ratified_config_fits_the_row(self):
        # Reads the committed config with no cap literals: a deliberate
        # re-size that moves only finger_max_* (and any value pin elsewhere)
        # fails here, because the budget still comes from the ratified row.
        layout = json.loads(gn.PROCESS_CONFIG.read_text())
        gn.check_row_fit(layout, layout["process"])

    def test_rejects_out_of_row_sum_with_the_rule_message(self):
        proc = {"finger_max_n": 1000, "finger_max_p": 1225}
        with self.assertRaises(ValueError) as raised:
            gn.check_row_fit(row_fit_layout(), proc)
        msg = str(raised.exception)
        self.assertIn("finger caps do not fit the ratified row", msg)
        self.assertIn("decision record", msg)

    def test_boundary_equality_accepted_one_nm_over_rejected(self):
        budget = 3360 - 440 - gn.DIFF_RESERVE_NM  # 2220 at the ratified geometry
        at = {"finger_max_n": budget - 1200, "finger_max_p": 1200}
        gn.check_row_fit(row_fit_layout(), at)
        over = dict(at, finger_max_n=at["finger_max_n"] + 1)
        with self.assertRaises(ValueError):
            gn.check_row_fit(row_fit_layout(), over)

    def test_row_height_and_rail_width_participate(self):
        caps = {"finger_max_n": 1000, "finger_max_p": 1220}  # sum == 2220
        gn.check_row_fit(row_fit_layout(3361), caps)  # taller row: room to spare
        with self.assertRaises(ValueError):
            gn.check_row_fit(row_fit_layout(3359), caps)  # shorter row: over
        gn.check_row_fit(row_fit_layout(3360, 439), caps)  # narrower rail: fits
        with self.assertRaises(ValueError):
            gn.check_row_fit(row_fit_layout(3360, 441), caps)  # wider rail: over

    def test_out_of_row_config_breaks_the_adapter_under_O(self):
        """End-to-end where the assert sat: a config over the row budget must
        break the adapter itself -- a fresh run of gen_netlists.py, not just
        the function -- under plain python3 and under -O alike. This is what
        the old bare assert could not provide: stripped by -O, and deletable
        with the whole suite staying green."""
        bad = json.loads(gn.PROCESS_CONFIG.read_text())
        bad["process"]["finger_max_p"] = 1225
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            (root / "design").mkdir()
            (root / "layout").mkdir()
            # The script resolves REPO from its own __file__, so the shadow
            # tree carries a copy of the script (symlinks would resolve back
            # to the real config) and symlinks for the pinned engine inputs.
            shutil.copy(DESIGN / "gen_netlists.py", root / "design" / "gen_netlists.py")
            shutil.copy(DESIGN / "cells.json", root / "design" / "cells.json")
            (root / "layout" / "vendor").symlink_to(REPO / "layout" / "vendor")
            (root / "layout" / "sg13cmos5l-cells.config.json").write_text(json.dumps(bad))
            for opt in ([], ["-O"]):
                r = subprocess.run(
                    [sys.executable, *opt, str(root / "design" / "gen_netlists.py"),
                     "--check", "--out", str(NETLISTS)],
                    capture_output=True, text=True, timeout=300, cwd=str(root),
                )
                self.assertNotEqual(r.returncode, 0, f"guard did not fire under {opt or 'python3'}")
                self.assertIn("finger caps do not fit the ratified row", r.stderr)


class GeneratorTest(unittest.TestCase):
    def test_freshness_check_passes_on_committed(self):
        for name, text in gn.generate().items():
            self.assertEqual((NETLISTS / name).read_text(), text)

    def test_forty_netlists_committed(self):
        self.assertEqual(len(list(NETLISTS.glob("*.spice"))), 40)

    def test_check_detects_stale_missing_and_stray(self):
        with tempfile.TemporaryDirectory() as td:
            out = pathlib.Path(td)
            self.assertEqual(gn.main(["--out", str(out)]), 0)
            (out / "s5l_inv_1.spice").write_text("x\n")
            (out / "s5l_inv_2.spice").unlink()
            (out / "s5l_extra_1.spice").write_text("x\n")
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                rc = gn.main(["--check", "--out", str(out)])
            self.assertEqual(rc, 1)
            errs = err.getvalue()
            self.assertIn("stale", errs)
            self.assertIn("missing", errs)
            self.assertIn("stray", errs)

    def test_cli_check_exit_codes(self):
        self.assertEqual(gn.main(["--check"]), 0)
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(gn.main(["--check", "--out", td]), 1)

    def test_sizing_fits_row(self):
        proc = gn.process()
        for p in NETLISTS.glob("*.spice"):
            _, devs = parse_netlist(p.read_text())
            for model, _, _, _, prm in devs:
                w, ng = int(prm["w"][:-1]), int(prm["ng"])
                cap = proc["finger_max_n"] if model == "sg13_lv_nmos" else proc["finger_max_p"]
                self.assertLessEqual(w / ng, cap, p.name)
                self.assertEqual(w % ng, 0, p.name)

    def test_rejects_mixed_operators_like_the_verilog_view(self):
        sys.path.insert(0, str(REPO / "rtl"))
        import gen_models as gm

        for bad in ("A^B*C", "A+B^C", "A*B+C", "!(A*B+C)"):
            with self.assertRaises(ValueError, msg=bad):
                gn.parse(bad)
            with self.assertRaises(ValueError, msg=bad):
                gm.parse(bad, {"A", "B", "C"})
        self.assertEqual(gn.evaluate(gn.parse("A^B^C"), {"A": 1, "B": 1, "C": 1}), 1)

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
