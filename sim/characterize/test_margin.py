import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import margin as m

PROBE = pathlib.Path(__file__).parent / "records" / "probe.s5l_nand2_1.tt_1p20v_25c.lib"


def lib(corner="c1", unit="1ns", rise_vals="1.0, 3.0, 2.0, 2.6", fall=True, extra=""):
    fall_tab = ('cell_fall (t) { index_1 ("0.1, 1.0"); index_2 ("0.01, 0.1");'
                ' values ( \\\n "0.5, 0.6", \\\n "0.7, 0.8" ); }') if fall else ""
    a, b, c, d = rise_vals.split(", ")
    return f"""
library (l_{corner}) {{
  time_unit : "{unit}";
  default_operating_conditions : "{corner}";
  cell (X) {{
    pin (Y) {{
      direction : "output";
      timing () {{
        related_pin : "A";
        cell_rise (t) {{ index_1 ("0.1, 1.0"); index_2 ("0.01, 0.1");
          values ( \\
            "{a}, {b}", \\
            "{c}, {d}" ); }}
        {fall_tab}
      }}
      timing () {{
        related_pin : "B";
        when : "A";
        cell_rise (t) {{ index_1 ("0.1, 1.0"); index_2 ("0.01, 0.1");
          values ("0.1, 0.1", "0.1, 0.1"); }}
        cell_fall (t) {{ index_1 ("0.1, 1.0"); index_2 ("0.01, 0.1");
          values ("0.1, 0.1", "0.1, 0.1"); }}
      }}
    }}
  }}
  {extra}
}}"""


class MarginTest(unittest.TestCase):
    def test_formula(self):
        self.assertAlmostEqual(m.margin(1.0, 2.5), 1.5)
        self.assertLess(m.margin(3.0, 2.5), 0)

    def test_limit_is_grid_max_slew(self):
        self.assertEqual(m.LIMIT_NS, 2.5074)

    def test_negative_margin_recorded_not_dropped(self):
        pts, miss = m.compute(m.parse_liberty(lib(rise_vals="1.0, 3.0, 2.0, 2.6")), limit_ns=2.5)
        a_rise = [p for p in pts if p.related_pin == "A" and p.edge == "rise"]
        self.assertEqual(len(a_rise), 4)  # nothing dropped
        fails = [p for p in a_rise if not p.passed]
        self.assertEqual(sorted(p.delay_ns for p in fails), [2.6, 3.0])
        self.assertAlmostEqual(min(p.margin_ns for p in a_rise), -0.5)
        self.assertEqual(miss, [])

    def test_rise_vs_fall_and_multi_arc(self):
        pts, _ = m.compute(m.parse_liberty(lib()), limit_ns=2.5)
        keys = {(p.related_pin, p.when, p.edge) for p in pts}
        self.assertEqual(keys, {("A", "", "rise"), ("A", "", "fall"),
                                ("B", "A", "rise"), ("B", "A", "fall")})
        p = next(p for p in pts if p.edge == "fall" and p.related_pin == "A"
                 and p.slew_ns == 1.0 and p.load_pf == 0.01)
        self.assertAlmostEqual(p.delay_ns, 0.7)

    def test_missing_arc_reported(self):
        pts, miss = m.compute(m.parse_liberty(lib(fall=False)))
        self.assertEqual(miss, [("c1", "X", "Y", "A", "", "fall")])
        self.assertEqual(len(pts), 12)

    def test_time_unit_scaled(self):
        pts, _ = m.compute(m.parse_liberty(lib(unit="1ps")), limit_ns=2.5)
        self.assertAlmostEqual(max(p.delay_ns for p in pts), 0.003)

    def test_binding_corner(self):
        a, _ = m.compute(m.parse_liberty(lib("slow", rise_vals="1.0, 3.0, 2.0, 2.6")), limit_ns=2.5)
        b, _ = m.compute(m.parse_liberty(lib("fast", rise_vals="0.2, 0.3, 0.2, 0.4")), limit_ns=2.5)
        self.assertEqual(m.binding_corner(a + b), "slow")

    def test_exit_status_fails_on_negative(self, ):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            f = pathlib.Path(d) / "x.lib"
            f.write_text(lib(rise_vals="9.0, 9.0, 9.0, 9.0"))
            self.assertEqual(m.main([str(f), "--csv", str(pathlib.Path(d) / "o.csv")]), 1)

    def test_probe_hand_computed(self):
        # hand computed from the lib: A rise at slew 2.5074, load 0.3 is 1.93426 ns
        pts, miss = m.compute(m.parse_liberty(PROBE.read_text()))
        self.assertEqual(miss, [])
        self.assertEqual(len(pts), 196)
        p = next(p for p in pts if p.related_pin == "A" and p.edge == "rise"
                 and p.slew_ns == 2.5074 and p.load_pf == 0.3)
        self.assertAlmostEqual(p.delay_ns, 1.93426)
        self.assertAlmostEqual(p.margin_ns, 2.5074 - 1.93426)
        self.assertEqual(m.binding_corner(pts), "tt_1p20v_25c")


if __name__ == "__main__":
    unittest.main()
