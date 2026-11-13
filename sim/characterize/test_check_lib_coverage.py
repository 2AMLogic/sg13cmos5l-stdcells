import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import check_lib_coverage as c

REC = pathlib.Path(__file__).parent / "records"
CELLS = [x["name"] for x in json.load(open(c.ROOT / "design/cells.json"))["cells"]]


class CoverageTest(unittest.TestCase):
    def test_ff_record_is_partial_and_says_which_cell(self):
        r = c.check((REC / "s5l_ff_1p32v_m40c.lib").read_text(), CELLS)
        self.assertEqual(r["absent"], ["s5l_mux4_1"])
        self.assertEqual(len(r["present"]), 39)
        self.assertEqual(r["missing_tables"], [])
        self.assertEqual(r["short_tables"], [])

    def test_probe_reports_other_cells_absent(self):
        r = c.check((REC / "probe.s5l_nand2_1.tt_1p20v_25c.lib").read_text(), CELLS)
        self.assertEqual(r["present"], ["s5l_nand2_1"])
        self.assertEqual(len(r["absent"]), 39)

    def test_corner_took_effect(self):
        import margin as m
        def d(p):
            l = m.parse_liberty((REC / p).read_text())
            return {(x.related_pin, x.when, x.edge, x.slew_ns, x.load_pf): x.delay_ns
                    for x in m.compute(l)[0] if x.cell == "s5l_nand2_1"}
        ff, tt = d("s5l_ff_1p32v_m40c.lib"), d("probe.s5l_nand2_1.tt_1p20v_25c.lib")
        ratios = [ff[k] / tt[k] for k in tt]
        self.assertEqual(len(ratios), 196)
        self.assertLess(sum(ratios) / len(ratios), 0.9)  # FF faster than TT


if __name__ == "__main__":
    unittest.main()
