# design

- `cells.json`: ratified 40-cell combinational catalog (spec/decision-records/0002).
- `check_catalog.py`: count/shape check (`python3 -I design/check_catalog.py`; `--celllist` also checks PDK counterparts).
- `test_check_catalog.py`: unit tests for the check.
- `gen_netlists.py`: also the one shared Liberty-function parser (used by `rtl/gen_models.py`); generator for `netlists/*.spice` (sizing rule in its docstring; local divergence, decision record 0003). `python3 -I design/gen_netlists.py` rewrites; `--check` is the freshness check.
- `netlists/`: 40 derived `sg13_lv` subcircuits. Do not edit by hand.
- `tests/`: freshness, switch-level truth tables (all 40), ngspice load and truth-table checks (logic-level stub models, not PDK models).
