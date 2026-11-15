#!/usr/bin/env python3
"""Generate the 40 transistor-level SPICE netlists with the pinned upstream generator.

Usage: gen_netlists.py [--check] [--out design/netlists]

This file is the SG13CMOS5L adapter (decision record 0006, superseding 0003).
It merges the ratified catalog (design/cells.json) with this PDK's sizing --
the `process` block of layout/sg13cmos5l-cells.config.json, which carries the
citation for every value -- into the config the pinned generator consumes, and
delegates everything else to the vendored upstream copy
(layout/vendor/sg13g2-stdcells/design/gen_netlists.py, byte-identical to
2AMLogic/sg13g2-stdcells at the `reuse.lock.json` pin). The topology code and
the Liberty-function parser live upstream now; this repo keeps no second copy.

Sizing rule (all numbers in the `process` block; the only PDK-specific part):
the finger caps (1000 nm N / 1200 nm P) split each device into fingers that
keep the N and P diffusion rows (1000 + 1200 nm) plus the 440 nm rail and a
700 nm N-P diffusion-spacing reserve inside the 3360 nm row target
(spec/target-spec.md, 8 tracks of 0.42 um; fallback 3.78 um only through a new
decision record). The assert below is that rule, checked against the config
so the two files cannot drift apart.

Default mode (re)writes one `<cell>.spice` per catalog cell under --out.
`--check` regenerates in memory and exits 1 on any difference against the
files on disk (changed, missing, or stray `.spice` files); this is the
declared freshness check for `klt signoff --attest 1`. Output is
deterministic (sorted, no timestamps), so the check is a byte compare.

`parse` and `evaluate` are re-exported from the pinned engine: this module is
still the one shared Liberty-function parser home for the digital views
(rtl/gen_models.py imports it and, through it,
verification/functional/gen_functional.py's arc derivation), but the grammar
has exactly one implementation -- the pinned one.
"""
import argparse
import importlib.util
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
VENDOR = REPO / "layout" / "vendor" / "sg13g2-stdcells" / "design" / "gen_netlists.py"
PROCESS_CONFIG = REPO / "layout" / "sg13cmos5l-cells.config.json"

# Row-fit reserve for the N-P diffusion spacing, nm: part of the sizing rule
# above, not a PDK rule, so it lives here and only here.
DIFF_RESERVE_NM = 700

# Header line 1 names the catalog the netlists derive from; passing the repo
# path keeps that line byte-identical to the pre-pin output.
CONFIG_NAME = "design/cells.json"


def _load_engine():
    """The pinned upstream generator, loaded by path under its own module name.

    Both this adapter and the engine are named `gen_netlists.py`, so a plain
    `import gen_netlists` here could resolve back to this file; the explicit
    spec makes the delegation unambiguous.
    """
    spec = importlib.util.spec_from_file_location("sg13g2_stdcells_gen_netlists", VENDOR)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


engine = _load_engine()

# The one shared Liberty-function parser, from the pinned copy.
parse = engine.parse
evaluate = engine.evaluate

_LAYOUT = json.loads(PROCESS_CONFIG.read_text())
_PROCESS = _LAYOUT["process"]
assert (
    _PROCESS["finger_max_n"] + _PROCESS["finger_max_p"]
    <= _LAYOUT["layout"]["row_height_nm"] - _LAYOUT["layout"]["rules"]["rail_width_nm"] - DIFF_RESERVE_NM
), "finger caps do not fit the ratified row: revisit the sizing (decision record)"


def process():
    """The SG13CMOS5L sizing block (the only PDK-specific part)."""
    return dict(_PROCESS)


def build_config():
    """The config the pinned engine consumes: catalog cells + process sizing."""
    return dict(json.loads((HERE / "cells.json").read_text()), process=process())


def generate():
    """{cell.spice: text} exactly as committed under the pinned engine."""
    return engine.generate(build_config(), config_name=CONFIG_NAME)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="fail if committed netlists differ from regenerated ones")
    ap.add_argument("--out", default=str(HERE / "netlists"))
    a = ap.parse_args(argv)
    outdir = pathlib.Path(a.out)
    try:
        files = generate()
    except ValueError as e:
        print(f"gen_netlists: invalid config: {e}", file=sys.stderr)
        return 2
    return engine.sync_outputs(
        files, outdir, "*.spice", check=a.check, tool="gen_netlists",
        script="design/gen_netlists.py", plural="netlists",
        out_of_date="netlist(s)", describe_stale=engine.describe_text_diff,
    )


if __name__ == "__main__":
    sys.exit(main())
