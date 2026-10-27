import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import gen_models as gm


class GenModelsTest(unittest.TestCase):
    def test_committed_models_fresh(self):
        self.assertEqual(gm.main(["--check"]), 0)

    def test_check_detects_stale_missing_and_extra(self):
        with tempfile.TemporaryDirectory() as d:
            out = pathlib.Path(d)
            self.assertEqual(gm.main(["--outdir", d]), 0)
            self.assertEqual(gm.main(["--check", "--outdir", d]), 0)
            (out / "s5l_inv_1.v").write_text("// edited\n")
            (out / "s5l_buf_1.v").unlink()
            (out / "s5l_bogus_1.v").write_text("")
            self.assertEqual(gm.main(["--check", "--outdir", d]), 1)

    def test_operators(self):
        self.assertEqual(gm.to_verilog(gm.parse("!(A+!B_N)", {"A", "B_N"})), "~(A | ~B_N)")
        self.assertEqual(gm.to_verilog(gm.parse("(A^B)", {"A", "B"})), "(A ^ B)")

    def test_rejects_ambiguous_or_unknown(self):
        for bad in ("A^B*C", "A+B^C", "A*Z", "(A*B", "A*B)"):
            with self.assertRaises(ValueError, msg=bad):
                gm.parse(bad, {"A", "B", "C"})


if __name__ == "__main__":
    unittest.main()
