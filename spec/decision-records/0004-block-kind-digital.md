# 0004 — Block kind is `digital` (full-custom sub-case)

- **Status**: accepted
- **Date**: 2026-10-29
- **Issue**: #36 (part of #23)

## Context

`manifests/sg13cmos5l-stdcells.json` carried `kind: "mixed-signal"` as a
placeholder (`manifests/README.md`), pending a revision by decision record. The
ratified spec (0001) states no block kind. The block is a standard-cell
library: its deliverables are digital views (Verilog models, Liberty, LEF,
GDS) of cells that are generated at transistor level, with no RTL and no
synthesis step in the block's own design flow.

## Decision

Declare `kind: "digital"`. T1 item 1 takes the full-custom digital sub-case of
the evidence-tiers doc: the generators (`design/gen_netlists.py`,
`rtl/gen_models.py`) plus the netlists and models derived from them,
regenerated on design change. Item 1 is attested by
`klt signoff --attest 1 --inventory design/item1-inventory.json`, committed as
`verification/item1-attest.json` and cited from the manifest.

## Consequences

- The kind-split T1 items grade against their digital column. Items that were
  not yet evidenced stay `unmet`; nothing is relaxed.
- `manifests/sg13cmos5l-stdcells.signoff.json` is regenerated in the same PR,
  as `manifests/README.md` requires.
- If the analog characterization work later needs the `mixed-signal` partition
  claim, that is a new decision record, not an edit of this one.
