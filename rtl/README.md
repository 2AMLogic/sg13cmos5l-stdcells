# rtl

Functional Verilog models, one per cell in `design/cells.json` (40 files,
`s5l_<family>_<drive>.v`). Generated, never hand-edited; no timing, no power
pins.

    python3 rtl/gen_models.py            # regenerate rtl/*.v from the catalog
    python3 rtl/gen_models.py --check    # exit 1 if any model is missing or stale

Tests (`rtl/tests/`) need cocotb and Icarus. cocotb comes from the checkout's
`.venv/` (gitignored, never a host-wide install), built by the one bring-up
recipe at the one pin of record — there is no second recipe here to drift, and
no version to type by hand (issue #119):

    scripts/setup-env.sh                                        # builds .venv at the pins
    .venv/bin/python rtl/tests/run_tests.py                     # exhaustive, one job
    python3 -m unittest rtl/tests/test_gen_models.py            # generator unit tests

The cocotb pin is [`toolchain.json`](toolchain.json) (`cocotb.install_spec`),
read by both `scripts/setup-env.sh` and the `design-rtl` CI job. Icarus
(`iverilog`) is not installed by the bring-up script: it comes from the distro
(`apt-get install iverilog`), as it does on the CI runner. The exhaustive run is
also the last step of `npm run check:design-rtl`, so a `.venv` built by
`scripts/setup-env.sh` is all that local gate needs.

`run_tests.py` drives every input row of every cell (at most 64, for
`s5l_mux4_*`) and compares against the catalog expression evaluated
independently in Python. Cocotb checks of the models live here, in
`rtl/tests/`; `verification/` holds the benchmark checks.
