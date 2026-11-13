# 0005 — Adopt the grid-validity bound as the item-5 timing-margin spec row

- **Status**: accepted
- **Date**: 2026-11-13
- **Issue**: #120 (part of #27, T1 item 5)

## Context

[`target-spec.md`](../target-spec.md) states no delay budget. The library is
combinational-only, so it has no clock period to derive one from, and the
"Characterization grid" row is the only ratified row that bounds a stage
delay at all.

T1 item 5 takes this block's full-custom digital sub-case (decision record
[0004](0004-block-kind-digital.md)): PVT corner-matrix SPICE simulation plus
"an explicit per-corner timing-margin metric measured directly in that same
sweep". The pinned grader (`klayout-tools==0.9.1`, `layout/toolchain.json`)
implements that as a manifest `spec_rows` row carrying
`"timing_margin": true`, evidenced by a passing, `limits`-bearing `klt sim`
measurement tagged with the row id in the rollup and present in every corner
(`klayout_tools/signoff.py`, `_missing_timing_margin` /
`_row_margin_lacking_corners`; `docs/cli/signoff.md`, "Full-custom digital
needs a measured timing margin"). Without such a row the item grades `unmet`
/ `timing_margin_missing`, and a row declared `"ratified": false` never
grades `met`.

So item 5 needs a *ratified* limit. The one candidate that is not chosen
after the fact is the bound already in `sim/characterize/margin.py`:

    LIMIT_NS = GRID_MAX_SLEW_NS = 2.5074

`margin.py` was written for issue #83, before any Liberty was characterized,
and says of that constant: "It is a constant set before any result was
looked at; it must not be edited to make a result pass. It is a
grid-validity bound, not a timing-closure target; a real delay budget needs
a decision record." This is that decision record. It ratifies the bound as
the item-5 timing-margin row and nothing more.

## Decision

### 1. The row

Declare one item-5 spec row:

| field | value |
|---|---|
| `id` | `t_stage_delay_grid_bound` |
| `timing_margin` | `true` |
| `ratified` | `true` (default) |

**Statement of the row.** For every timing arc of every cell, at every
ratified Liberty corner, the stage delay must not exceed the largest input
slew of the ratified characterization grid:

    stage_delay <= 2.5074 ns

**What the bound means, and does not mean.** It is a *grid-validity* bound,
identical in definition to `sim/characterize/margin.py`'s
`margin = LIMIT_NS - delay`, and it is adopted unchanged from it. A stage
whose delay exceeds the grid's largest characterized input slew drives its
downstream pin outside the slew domain the tables cover, where the NLDM
tables extrapolate rather than interpolate — the Liberty is then being read
outside its own characterized range. **It is not a timing-closure target,
not a performance budget, and not a claim that the library is fast enough
for any design.** A real delay budget remains unstated by the ratified spec
and would need its own decision record.

### 2. The point it is measured at

The row is evidenced at **one** grid point per corner: the grid's own worst
point,

| axis | value | source |
|---|---|---|
| input slew | **2.5074 ns** | `target-spec.md` "Characterization grid", largest value on the slew axis |
| output load | **0.3 pF** | same row, largest value on the load axis |

Reason: `margin.py` applies the bound at *every* one of the 49 grid points of
every arc, and takes the binding point to be the worst one. Stage delay is
monotonically increasing in both input slew and output load, so the grid's
(max slew, max load) corner is that worst point. A measurement that passes
there carries the bound over the whole grid; a measurement at any gentler
point would claim strictly less than `margin.py`'s definition. Measuring at
the worst point is therefore the only single-point choice that is equivalent
to the row as stated, and it keeps the `klt sim` evidence and `margin.py`
consistent by construction rather than by coincidence.

Per-grid-point margin over the full 7 × 7 tables stays with `margin.py` over
the recorded Liberty; this row does not replace it.

### 3. Arc coverage and the measured quantity

Every timing arc of all 40 cells of `design/cells.json` is measured at each
of the three ratified corners (TT / 1.20 V / 25 °C, FF / 1.32 V / −40 °C,
SS / 1.08 V / 125 °C — `target-spec.md` "Liberty corners"), as two
measurements per arc:

- `cell_rise` — delay to the **rising** output edge;
- `cell_fall` — delay to the **falling** output edge;

each defined, as in the Liberty tables, as the 50 %-of-rail crossing of the
switching input to the 50 %-of-rail crossing of the output, with the arc's
non-switching inputs held in a state that propagates the arc. Both carry
`limits: {"max": 2.5074e-9}` (seconds, as ngspice reports) and
`spec_row: "t_stage_delay_grid_bound"`.

Only `max` is bounded. A 50 %-to-50 % delay may legitimately be small or
negative for a fast cell driven by a slow input ramp, so no `min` is
declared: a lower bound would fail a physically correct measurement.

## Consequences

- `manifests/` may declare `spec_rows` for item 5 with this row. This record
  ratifies the row; **re-pointing the committed manifest citation and
  regenerating the verdict of record is #87**, not this record.
- The bound is now ratified, so it must not be edited to make a result pass —
  the same rule `margin.py` already stated for itself. A result that exceeds
  it is recorded as a failure and reported.
- A failing arc is a real finding about the ratified grid, not about the
  cell: it says the slew axis does not reach far enough to cover that arc at
  that load and corner. Acting on such a finding (widening the grid row,
  dropping the worst load point, or adding drive strengths) is a change to
  `target-spec.md` and needs its own decision record.
- Adopting the existing constant, rather than choosing a new number now,
  is deliberate: all three corners' Liberty is already recorded, so any
  freshly chosen limit would be post-hoc by construction.
