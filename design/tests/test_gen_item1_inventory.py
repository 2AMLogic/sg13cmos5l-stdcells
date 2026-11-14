"""Tests for design/gen_item1_inventory.py and design/item1-inventory.json.

The byte-identity test is the load-bearing one: item 1's attestation
`content_hash` covers the inventory, so a generator that reformats it would
silently invalidate `verification/item1-attest.json`. The drift test is the
regression this generator closes -- a catalog edit that every other
`check:design-rtl` gate passes clean while the inventory still names the old
cell (issue #144).
"""
import copy
import json
import pathlib
import sys
import tempfile
import unittest

DESIGN = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DESIGN))
import gen_item1_inventory as gi  # noqa: E402

INVENTORY = DESIGN / "item1-inventory.json"
CATALOG = json.loads((DESIGN / "cells.json").read_text())
COMMITTED = json.loads(INVENTORY.read_text())


def write_catalog(directory, catalog):
    path = pathlib.Path(directory) / "cells.json"
    path.write_text(json.dumps(catalog, indent=2) + "\n")
    return path


class RenderTest(unittest.TestCase):
    def test_committed_inventory_is_byte_identical(self):
        """A plain run must not move a single byte: item 1 is attested on these
        bytes, so a reformat would invalidate the committed envelope."""
        self.assertEqual(gi.render(CATALOG["cells"]), INVENTORY.read_text())

    def test_non_derived_fields_match_the_ratified_inventory(self):
        """description/sources/kind/t1_item are decision-record content
        (0004), not catalog-derived -- the generator must not rewrite them."""
        fresh = json.loads(gi.render(CATALOG["cells"]))
        for key in ("schema_version", "kind", "t1_item", "description", "sources"):
            self.assertEqual(fresh[key], COMMITTED[key], key)

    def test_two_entries_per_cell_each_citing_its_generator(self):
        derived = json.loads(gi.render(CATALOG["cells"]))["derived"]
        self.assertEqual(len(derived), 2 * len(CATALOG["cells"]))
        for entry in derived:
            self.assertEqual(sorted(entry), ["check", "generator", "path"])
            self.assertEqual(
                entry["check"]["argv"],
                ["python3", "-I", entry["generator"], "--check"],
            )
        names = [c["name"] for c in CATALOG["cells"]]
        paths = [e["path"] for e in derived]
        self.assertEqual(
            paths,
            sorted(f"design/netlists/{n}.spice" for n in names)
            + sorted(f"rtl/{n}.v" for n in names),
        )


class CheckTest(unittest.TestCase):
    def test_committed_inventory_fresh(self):
        self.assertEqual(gi.main(["--check"]), 0)

    def test_missing_inventory_fails(self):
        with tempfile.TemporaryDirectory() as d:
            out = pathlib.Path(d) / "item1-inventory.json"
            self.assertEqual(gi.main(["--check", "--out", str(out)]), 1)
            self.assertEqual(gi.main(["--out", str(out)]), 0)
            self.assertEqual(gi.main(["--check", "--out", str(out)]), 0)

    def test_renamed_cell_is_named_as_drift(self):
        """The gap this closes: renaming a cell keeps the catalog at 40 and
        both derived views fresh, so check_catalog / gen_netlists --check /
        gen_models --check all pass -- only this check sees the stale
        inventory, and it must name both sides of the drift."""
        catalog = copy.deepcopy(CATALOG)
        cell = next(c for c in catalog["cells"] if c["name"] == "s5l_xor2_1")
        cell["name"] = "s5l_xnor2_9"
        with tempfile.TemporaryDirectory() as d:
            path = write_catalog(d, catalog)
            self.assertEqual(
                gi.main(["--check", "--catalog", str(path), "--out", str(INVENTORY)]), 1
            )
            reason = gi.stale_reason(INVENTORY.read_text(), gi.render(catalog["cells"]))
            for expected in ("design/netlists/s5l_xnor2_9.spice", "rtl/s5l_xnor2_9.v"):
                self.assertIn(expected, reason)
            for orphan in ("design/netlists/s5l_xor2_1.spice", "rtl/s5l_xor2_1.v"):
                self.assertIn(orphan, reason)

    def test_edited_non_derived_field_is_named_without_blaming_the_paths(self):
        want = gi.render(CATALOG["cells"])
        edited = json.loads(want)
        edited["description"] = "hand-edited"
        reason = gi.stale_reason(json.dumps(edited, indent=2) + "\n", want)
        self.assertIn("non-derived field", reason)

    def test_unreadable_inventory_is_named_not_raised(self):
        self.assertIn("readable", gi.stale_reason("{not json", gi.render(CATALOG["cells"])))

    def test_fresh_inventory_reports_no_reason(self):
        want = gi.render(CATALOG["cells"])
        self.assertIsNone(gi.stale_reason(want, want))


if __name__ == "__main__":
    unittest.main()
