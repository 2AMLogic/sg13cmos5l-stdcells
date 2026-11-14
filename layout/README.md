# layout

Physical-verification toolchain pin ([`toolchain.json`](toolchain.json)) and the
DRC/LVS smoke on a PDK reference cell ([`smoke/`](smoke/README.md)).

Generated cell layouts come from the origin's cell layout generator, taken by
pinned reference and driven by this repo's SG13CMOS5L configuration:

| Path | What it is | Owner |
|---|---|---|
| [`vendor/sg13g2-stdcells/`](vendor/sg13g2-stdcells) | the origin's `gen_layouts.py` + `gen_netlists.py`, vendored byte-identical at the commit in [`/reuse.lock.json`](../reuse.lock.json) | `2AMLogic/sg13g2-stdcells` — **never edited here** |
| [`sg13cmos5l-cells.config.json`](sg13cmos5l-cells.config.json) | the SG13CMOS5L configuration: row geometry, layer map, 15 rule values, cell list | this repo |
| [`gds/`](gds) | the generated GDS, one per config cell | generator output |

```bash
# regenerate
python3 -I layout/vendor/sg13g2-stdcells/layout/gen_layouts.py \
    --config layout/sg13cmos5l-cells.config.json --out layout/gds
# freshness gate (also run by `npm run check:ci` as `check:layout`)
npm run check:layout
```

Exit codes: `0` wrote/fresh, `1` stale, `2` invalid config, `3` a cell cannot be
placed (the reason is named, and no partial GDS is written for any cell).

## Why the generator is vendored under `vendor/`, not in place

`gen_layouts.py` imports the netlist generator through a `sys.path.insert`
resolved **relative to its own grandparent**, so the two files have to keep the
upstream `…/layout/gen_layouts.py` + `…/design/gen_netlists.py` shape under one
root. That root cannot be the repo root: `/design/gen_netlists.py` here is this
repo's recorded local divergence (decision record 0003 — it is not
config-driven and has no `validate`/`PROCESS_KEYS`), and `rtl/gen_models.py`
imports it for the Liberty-function parser. The vendor subtree keeps both, with
no edit to either file.

## What the retarget probe established (issue #151, one cell)

The generator **retargets to SG13CMOS5L by configuration alone**, and
`s5l_inv_1` **places on the ratified 3.36 µm row**. Measured on this host at the
pinned generator commit and the PDK pin in [`/sim/pdk.json`](../sim/pdk.json)
(`f7bca32694fe3d58be0cc7d9df4b9f5db7161a14`):

- `--out layout/gds` exits `0`; `--check` exits `0` and prints `1 GDS fresh`.
- Byte-deterministic: three independent runs give
  `sha256 8a50b81ec2fbb5fe64ca4c6887918067944c474cbdc78376570ae78ddd08ca0b`.
- Cell is **0.84 µm × 3.36 µm**; rails are Metal1 0.44 µm centred on the row
  boundary; NMOS strip 740 nm tall at y = 350 nm, PMOS strip 1120 nm topping at
  y = 3030 nm; one well tap and one substrate tap, 300 nm tall, under their rails.
- Devices agree with the committed netlist: the generator's `build()` returns
  `('n','Y','A','VSS',740,1)` and `('p','Y','A','VDD',1120,1)`, and its rendered
  device lines are identical to those in
  [`/design/netlists/s5l_inv_1.spice`](../design/netlists/s5l_inv_1.spice).

**None of this is a DRC, LVS or manufacturability claim.** It is generator
output checked against generator input; no rule deck has been run on it. DRC is
issue #25 and LVS is issue #26, and until those land no generated cell is called
clean. A simulated or generated number is never called measured.

### The margin budget — the two free parameters

`n_diff_y0_nm` and `p_diff_top_margin_nm` are the only free values in the
config, and they decide whether the 3.36 µm row places. The feasible region for
`s5l_inv_1`, measured by sweeping each boundary to the 5 nm grid:

| Constraint | Bound | What fails past it (exit 3) |
|---|---|---|
| `n_diff_y0_nm` | **≥ 280** | `VSS tap Metal1 is not 180 nm clear of Y` |
| `p_diff_top_margin_nm` | **≥ 260** | `VDD tap Metal1 is not 180 nm clear of Y` |
| sum of the two | **≤ 750** | `channel too short for track 1 of net Y` |

Confirmed at each edge: `275/300` and `340/255` fail, `280/300` and `340/260`
pass; `340/410` (sum 750) passes and `340/415` (sum 755) fails.

The config uses **350 / 330**, the maximin point of that region — 70 nm of slack
on each of the three constraints. The two lower bounds are new with the tap
bands; the sum bound is the one that moves, because wider devices shrink the
channel. **That sum is the number issue #24 will have to re-derive** for the
widest of the 40 cells, since the config carries one value for all of them.

`row_height_nm` is **not** relaxed here. `spec/target-spec.md` leaves 3.36 µm as
a target "not claimed achievable" and permits the 3.78 µm fallback only through
a new decision record citing generator evidence; that record belongs to #24. On
this cell the fallback is not needed.

### `nsd` (7/0) is required, and that reverses issue #151's AC8

AC8 asked for `layout.layers.nsd` to be **omitted**, on the evidence that the
PDK's own `sg13cmos5l_stdcell` cells draw no `7/0` and the generator listed
`nsd` in `OPTIONAL_LAYERS`. **That premise is false at the pinned commit.** The
generator now draws a well tap and a substrate tap per cell so extraction puts
the device bodies on VDD/VSS instead of synthesized well/substrate nets
(origin issue #73), and it refuses to place without `nsd`:

```
layout.layers.nsd is missing, so the n-well tap cannot be drawn as a well tie
(the deck derives the tie as activ & nsd); give the config an nsd layer
```

Reproduced here: dropping `nsd` from the config exits `3` with exactly that
message. `nsd` is `7/0` in this PDK (`layers_def.drc:131`,
`nsd_drw = get_polygons(7, 0)`), so the config carries it. The implants abut
rather than overlap — `psd` runs −380…170 nm and `nsd` 170…1270 nm on the VSS
side — because `psd` over `nsd` is not a mask either tool can resolve.

`OPTIONAL_LAYERS` still lists `nsd`, so the *validator* accepts a config without
it and the *placer* then rejects it — exit 3 (`cannot place`) where exit 2
(`invalid config`) is the honest code. Filed upstream as
[`2AMLogic/sg13g2-stdcells#80`](https://github.com/2AMLogic/sg13g2-stdcells/issues/80);
the vendored copy stays byte-identical to the pin until upstream fixes it.

### Four cited rules are not implemented in the default deck

Each of the 15 rule values carries its citation in the config's
`layout._citations`. Eleven resolve to a rule implemented in the default deck's
`feol/`/`beol/` rule files. Four — `Gat.c` (poly end cap), `NW.c`, `NW.e`
(the well-tie enclosure the tap needs) and `pSD.c` — have values in
`sg13cmos5l_tech_default.json` and rule text in `sg13cmos5l_maximal.drc`, but no
implementation in the default deck's rule files. The config uses the documented
values; which rules the deck does not cover on a real cell is the open question
`spec/target-spec.md` already defers to the DRC run, and this is one more
datapoint for it — expected, on a PDK where the deck is least exercised.
