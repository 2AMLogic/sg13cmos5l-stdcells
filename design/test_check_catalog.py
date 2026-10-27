import copy
import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import check_catalog as cc

CAT = json.load(open(pathlib.Path(__file__).parent / "cells.json"))


class CatalogTest(unittest.TestCase):
    def test_committed_catalog_passes(self):
        self.assertEqual(cc.check(CAT), [])

    def test_missing_cell_fails(self):
        c = copy.deepcopy(CAT)
        c["cells"].pop()
        self.assertTrue(any("expected 40" in e for e in cc.check(c)))

    def test_duplicate_name_fails(self):
        c = copy.deepcopy(CAT)
        c["cells"][1] = copy.deepcopy(c["cells"][0])
        self.assertTrue(any("duplicate name" in e for e in cc.check(c)))

    def test_sequential_fails(self):
        c = copy.deepcopy(CAT)
        c["cells"][0]["name"] = "s5l_dfrbp_1"
        self.assertTrue(any("not counted" in e for e in cc.check(c)))

    def test_undeclared_pin_fails(self):
        c = copy.deepcopy(CAT)
        c["cells"][0]["outputs"] = {"X": "(Q*B1)"}
        self.assertTrue(any("undeclared" in e for e in cc.check(c)))

    def test_unknown_pdk_cell_fails(self):
        self.assertTrue(any("not in PDK" in e for e in cc.check(CAT, {"x"})))


if __name__ == "__main__":
    unittest.main()
