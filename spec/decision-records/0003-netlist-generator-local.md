# 0003 — Netlist generator lives locally until upstreamed

- **Status**: accepted
- **Date**: 2026-10-27
- **Issue**: #34 (part of #23)

## Context

CLAUDE.md makes `sg13g2-stdcells` the master of PDK-independent generators,
taken by pinned reference. At `f450813` and on its `main` the origin has no
netlist generator (`design/` is a README only), so there is nothing to pin.
Netlists for the 40-cell catalog (decision record 0002) are needed now.

## Decision

Land `design/gen_netlists.py` here as a **recorded local divergence**: one
generator for all 40 cells (topology from the boolean function in
`design/cells.json`, SG13CMOS5L sizing in constants at the top of the file),
deterministic output, `--check` as the freshness check. The PDK-independent
part is filed upstream as `2AMLogic/sg13g2-stdcells#5`. When it lands, pin it
in `reuse.lock.json` and reduce this file to the sizing configuration.

## Consequences

- The topology code is temporarily not under the pinned-reference rule.
- Sizing assumes `w` is the total width split over `ng` fingers; this is
  unverified against the PDK `sg13_lv_*` wrappers (no PDK in the build
  environment). The ngspice tests use logic-level stub models, not PDK models.
- Row fit is a finger-width constraint, not a layout claim; the row height
  stays the 3.36 µm target with the 3.78 µm fallback.

## Addendum (#46): one Liberty-function parser

`design/gen_netlists.py:parse` is the single parser for catalog output
expressions; `rtl/gen_models.py` imports it and only adds the pin-name check
and the Verilog rendering. The grammar is the strict one the Verilog view
already enforced: `*`, `+`, `^` may not be mixed at one nesting level without
parentheses. No new module and no new divergence: the parser stays inside the
file this record already keeps local. When `2AMLogic/sg13g2-stdcells#5` lands,
the parser moves upstream with the topology code, and `rtl/gen_models.py`
follows the pin.
