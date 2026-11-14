# design

- `cells.json`: ratified 40-cell combinational catalog (spec/decision-records/0002).
- `check_catalog.py`: count/shape check (`python3 -I design/check_catalog.py`; `--celllist` also checks PDK counterparts).
- `test_check_catalog.py`: unit tests for the check.
- `gen_netlists.py`: also the one shared Liberty-function parser (used by `rtl/gen_models.py` and, through it, by `verification/functional/gen_functional.py`'s arc derivation); generator for `netlists/*.spice` (sizing rule in its docstring; local divergence, decision record 0003). `python3 -I design/gen_netlists.py` rewrites; `--check` is the freshness check.
- `netlists/`: 40 derived `sg13_lv` subcircuits. Do not edit by hand.
- `item1-inventory.json`: derived T1 item-1 attestation inventory (the input to `klt signoff --attest 1`; see `verification/README.md`). Do not edit by hand.
- `gen_item1_inventory.py`: generator for `item1-inventory.json` — two derived entries per catalog cell (netlist + Verilog model), each citing its own generator's `--check`. `python3 -I design/gen_item1_inventory.py` rewrites; `--check` is the freshness check. It emits the attested bytes exactly, so a plain run leaves no diff and re-attests nothing; if it does leave one, the generator is the bug (issue #144). The non-derived `description`/`sources` fields are decision-record content (0004), not catalog-derived.
- `tests/`: freshness, switch-level truth tables (all 40), ngspice load and truth-table checks (logic-level stub models, not PDK models).
