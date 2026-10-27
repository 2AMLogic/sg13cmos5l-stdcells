# rtl

Functional Verilog models, one per cell in `design/cells.json` (40 files,
`s5l_<family>_<drive>.v`). Generated, never hand-edited; no timing, no power
pins.

    python3 rtl/gen_models.py            # regenerate rtl/*.v from the catalog
    python3 rtl/gen_models.py --check    # exit 1 if any model is missing or stale

Tests (`rtl/tests/`) need cocotb and Icarus. Use a venv inside the checkout
(`.venv/` is gitignored), not a host-wide install:

    python3 -m venv .venv && .venv/bin/pip install cocotb
    PATH=$PWD/.venv/bin:$PATH python rtl/tests/run_tests.py     # exhaustive, one job
    python3 -m unittest rtl/tests/test_gen_models.py            # generator unit tests

`run_tests.py` drives every input row of every cell (at most 64, for
`s5l_mux4_*`) and compares against the catalog expression evaluated
independently in Python. Cocotb checks of the models live here, in
`rtl/tests/`; `verification/` holds the benchmark checks.
