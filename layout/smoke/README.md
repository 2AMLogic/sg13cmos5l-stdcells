# layout/smoke -- physical-verification smoke (issue #4)

`klt drc` and `klt lvs` run on one cell of the PDK's own reference library,
`sg13cmos5l_inv_1` from `libs.ref/sg13cmos5l_stdcell` at the IHP-Open-PDK
commit pinned in [`sim/pdk.json`](../../sim/pdk.json) (`f7bca326...`). This is
toolchain bring-up: it shows the tools run end to end on this PDK and says
precisely what they did and did not check. It is not a verification claim
about any cell this repo designs, and nothing here is a measurement.

| file | what |
|---|---|
| `sg13cmos5l_inv_1.gds` | `klt clip --cell` of the reference cell (PDK data, Apache-2.0) |
| `sg13cmos5l_inv_1.spice` | the cell's `.subckt` copied verbatim from the PDK's `sg13cmos5l_stdcell.spice` |
| `lvs_request.json` | the `klt lvs` request |
| `reports/drc_sg13cmos5l_inv_1.json` | `klt drc --deck sg13cmos5l --top sg13cmos5l_inv_1` envelope |
| `reports/lvs_sg13cmos5l_inv_1.json` | `klt lvs lvs_request.json` envelope |

Reproduce (after `scripts/setup-env.sh` and `source .cache/env.sh`), from this
directory: `klt drc --deck sg13cmos5l --top sg13cmos5l_inv_1 sg13cmos5l_inv_1.gds --format json`
and `klt lvs lvs_request.json --format json`. klt is pinned in
[`layout/toolchain.json`](../toolchain.json): `"0.8.0"`,
klayout `0.30.12`. The deck is the curated
`sg13cmos5l` deck, content hash `sha256:f31d94eb2324a5db7b20b286760312e0835eb1dbaae4a46fc05699c4a52619d3`,
`released: false`.

## DRC: `clean`, 0 violations

Quoted verbatim from the envelope's `coverage` block. "Clean" means clean
against the rules the curated deck models, and only those:

- `layers_in_stream_without_rules`: `["8/2", "8/25", "189/4"]`
- `rules_skipped`: `["metal1.enclosing.via1.1", "metal2.enclosing.via1.1", "metal2.enclosing.via2.1", "metal2.space.1", "metal2.width.1", "metal3.enclosing.via2.1", "metal3.enclosing.via3.1", "metal3.space.1", "metal3.width.1", "metal4.enclosing.topvia1.1", "metal4.enclosing.via3.1", "metal4.space.1", "metal4.width.1", "nwell.enclosing.nactiv.1", "nwell.enclosing.nactiv.dig.1", "nwell.enclosing.nactiv.hv.1", "nwell.space.nactiv.1", "nwell.space.nactiv.dig.1", "nwell.space.nactiv.hv.1", "topmetal1.enclosing.topvia1.1", "topmetal1.space.1", "topmetal1.width.1", "topvia1.space.1", "topvia1.width.1", "via1.space.1", "via1.width.1", "via2.space.1", "via2.width.1", "via3.space.1", "via3.width.1"]`
- `deck_scope`: `["5.1 NWell", "5.16 Metal1", "5.17 Metaln", "5.19 Via1", "5.20 Vian", "5.21 TopVia1", "5.22 TopMetal1", "5.5 Activ", "5.8 GatPoly", "Via1 upper-landing containment (curated)", "Via2 upper-landing containment (curated)", "Via3 upper-landing containment (curated)"]`

The envelope also reports `layers_checked` `["1/0", "5/0", "6/0", "8/0", "14/0", "31/0"]` and
`rules_checked` of 15 rules. Every id in `rules_skipped`
is listed in `coverage.inapplicable` with reason `no_applicable_geometry`
(`coverage.skipped` is `[]`): a one-metal inverter has no Metal2+/Via
geometry for those rules to act on. What `deck_scope` omits is the real
limit: it names the NWell, Activ, GatPoly, Metal1-n and Via rule families and
three curated via-landing checks, so the deck is a subset of the PDK's own DRC
deck (`libs.tech/klayout/tech/drc/ihp-sg13cmos5l.drc`), not a replacement for
it. The shapes on `8/2`, `8/25` (Metal1 pin/text purposes) and `189/4` carry no
rules.

## LVS: `mismatch` -- NOT clean

`6` entries, `4` errors: {"device.body_unverified": 2, "device.unmatched": 1, "net.merged": 1, "net.split": 2}.
Nets {"layout": 5, "reference": 4, "matched": 1}, devices {"layout": 2, "reference": 2, "matched": 1}, pins
{"layout": 1, "reference": 4, "matched": 4}. The envelope is committed unedited because a failing
result on the PDK's own reference cell is itself the finding: against a
reference netlist taken from the same PDK, the curated `sg13cmos5l` extraction
sees one device pair unmatched, the reference `VDD` merged with another net, and
no promoted pin (`pins.layout` is 1, the reference has 4). Re-pointing the label
purpose with `layout.label_layers` (`metal1: [8, 25]`) gave the identical
result. The `device.body_unverified` warnings say no tap geometry resolved the
bodies. Which of these is the cell, the extraction deck, or the extraction of a
cell clipped out of its library is not established here and is not claimed.

The PDK's own LVS runset was also tried
(`klt lvs` with `"engine": "klayout-runset"` and
`--deck-file libs.tech/klayout/tech/lvs/sg13cmos5l.lvs`) and cannot run at this
pin: klayout stops with `Unable to open file: .../rule_decks//cap_cmomi_derivations.lvs`.
Six of the runset's rule-deck includes are relative symlinks into the
`ihp-sg13g2` sibling that the sibling release does not contain (see
`known_incomplete` in `sim/pdk.json`). That run produced no verdict and no
envelope is committed for it.

## Gaps for klayout-tools

Filed on 2AMLogic/klayout-tools, worded generically:

- [#3831](https://github.com/2AMLogic/klayout-tools/issues/3831): the curated
  `sg13cmos5l` LVS does not match the PDK's own reference inverter.
- [#3832](https://github.com/2AMLogic/klayout-tools/issues/3832): dangling
  sibling links leave the PDK-native LVS runset unrunnable.
- [#2727](https://github.com/2AMLogic/klayout-tools/issues/2727) (existing,
  commented): the batch backend refuses `ihp-sg13cmos5l` (see `sim/smoke/README.md`).
