# 0008 — Item-5 margin gap: close it by widening the failing stack cells' PMOS pull-up

- **Status**: proposed (awaiting the repo's ratification path; the operator's
  ruling decides the option, not this record's wording of it)
- **Date**: 2026-11-19
- **Issue**: #129 (part of #27, T1 item 5)
- **Ruling**: operator rjwalters, 2026-11-18, `/fleet:decide` round
  20261118-r16, q144 — "fix the design. Add drive strengths for the failing
  stacked cells; do not change the grid row, do not ratify a delay budget,
  and do not record item 5 as accepted-unmet."

## Context

[0005](0005-timing-margin-spec-row.md) ratifies the item-5 timing-margin row:
every timing arc of every cell, at every ratified corner, at the grid's worst
point (input slew 2.5074 ns, load 0.3 pF), against the grid-validity bound
`stage_delay <= 2.5074 ns`. The recorded corner sweep
(`verification/functional/records/corners.report.json`) fails it at SS /
1.08 V / 125 C on five stacked-NMOS rise arcs, all on `_1` cells:

| arc | delay (ns) | margin (ns) |
|---|---|---|
| `s5l_nand4_1` `Y<-D` rise | 2.56217 | −0.0548 |
| `s5l_nand4_1` `Y<-C` rise | 2.53934 | −0.0319 |
| `s5l_nand3_1` `Y<-C` rise | 2.51898 | −0.0116 |
| `s5l_nand3b_1` `Y<-C` rise | 2.51896 | −0.0116 |
| `s5l_nand4_1` `Y<-B` rise | 2.51506 | −0.0077 |

0005's Consequences name the ways forward and say each is a change to the
ratified spec needing its own decision record; #129 asked which one. The
ruling chose **drive-strengths** and asked one question to be answered by
simulation before any layout: can added higher-drive variants bring item 5 to
`met`, or do the `_1` cells themselves need a sizing change?

## Decision

### 1. The choice, and how it is realized

**Option `drive-strengths`, realized as a sizing change of the three failing
`_1` cells, not as new cells.** The row is stated "for every timing arc of
every cell" (0005 §1, §3), so `s5l_nand4_1`, `s5l_nand3_1` and
`s5l_nand3b_1` stay in `design/cells.json` and stay measured at the failing
point regardless of any added `_2`/`_4` variant: added variants alone can
never bring item 5 to `met`. This answers the ruling's question from the row
text, and the simulation below confirms the sizing path works. No cell is
added or removed; the 40-cell list and the spec's count stay as [0002](0002-cell-list.md)
ratified them.

### 2. The feasibility result (SIMULATED — `sim/characterize/probe_item5_sizing/`)

The probe derives variant netlists from the committed ones, instantiates all
ten arcs of the three cells exactly as `tb_corners.cir` does, and measures
them at the failing point with a single-corner local `klt sim` run per
variant (one `--backend local` run per corner; no grid). Full tables:
`sim/characterize/probe_item5_sizing/results.md`. Outcome **(i): a resized
`_1` clears the bound.**

- **Validation.** The unresized baseline reproduces the recorded SS corner to
  within 0.16 ps on all 20 arcs and finds the same five failures at the same
  values (least margin −0.0549 ns, `s5l_nand4_1` `Y<-D`) — the probe is
  comparable with the record.
- **Recommended sizing.** Output PMOS of the three cells 1120n ng=1 →
  **1680n ng=2 (840n per finger, +50 % PMOS drive)**. All 20 arcs pass at
  all three ratified corners; at the failing point the worst arc is
  `s5l_nand4_1` `Y<-D` rise at 2.09609 ns, **margin +0.4113 ns** (TT worst
  +0.8555 ns, FF worst +1.2597 ns). The finger stays under the 1200 nm PMOS
  finger cap and the row-fit rule of 0006 is untouched. At SS the fall-side
  arcs move +2.9 to +4.8 ps from the added drain capacitance on `Y`, except
  `s5l_nand3b_1` `Y<-A_N` fall at +27.4 ps: the wider output PMOS adds gate
  load to the internal `A_N_b` node driven by the cell's own inverter, which
  that arc's path crosses (it still passes with +1.0564 ns of margin).
- **Alternative probed.** Doubling the PMOS (2240n ng=2, 1120n per finger)
  clears everywhere with worst SS margin +0.5393 ns, at twice the added
  P-diffusion width.
- **Negative result.** Narrowing the NMOS stack alone (740n → 560n per
  finger) does *not* clear `s5l_nand4_1` `Y<-C`/`Y<-D` (still −0.0313 ns
  worst): the rise bottleneck is the parallel-PMOS pull-up fighting the
  partially-on stack, not the stack's own width.

The five failing arcs are single-state arcs (0005 addendum of 2026-11-14), so
covering the arc covers every propagating side-input state of it; the logic
function is unchanged by a resize, so the RTL models and the truth-table
records stay valid.

### 3. The rejected options

- **Ratify a real delay budget for item 5** — rejected by the ruling, and on
  0005's own ground: the library has no clock period to derive a budget from,
  and any budget chosen after these results existed would be post-hoc by
  construction — exactly what 0005 refused to do when it adopted the
  pre-existing constant instead.
- **Change the characterization grid row** (widen the slew axis, drop the
  worst load point) — rejected by the ruling, and it would weaken the grid to
  make a result pass: the bound exists to keep Liberty reads inside the
  characterized slew domain (0005 §1), and moving the grid point the row is
  evidenced at was already refused inside 0005's addendum of 2026-11-13 for
  being outcome-driven.
- **Accept item 5 as `unmet` at SS** — rejected by the ruling: a recorded
  stretch-corner failure is evidence, not a verdict of record for T1 item 5,
  and the graded gate needs `met` on an unchanged row and bound.

### 4. What this reopens

The resize departs from the transistor sizing of the three cells' PDK
counterparts (`sg13cmos5l_nand3_1`, `sg13cmos5l_nand3b_1`,
`sg13cmos5l_nand4_1`), so **this record reopens decision record [0002](0002-cell-list.md)
for those three cell definitions** — their names, count and counterpart
listing stay unchanged; what changes is their sizing's citation. The sizing
itself lands in the `process` block of `layout/sg13cmos5l-cells.config.json`
(0006's adapter, which carries a citation for every value); whether the
pinned upstream generator's config schema can express a per-family PMOS width
is the first question the follow-on answers — if it cannot, the schema change
is an upstream `sg13g2-stdcells` fix first, per the reuse rule.

Nothing here edits 0005, 0002, `target-spec.md`, the 2.5074 ns bound, or
`sim/characterize/margin.py`'s `LIMIT_NS`; all stay exactly as ratified.

## Consequences

- Item 5 can grade `met` with the row and bound untouched, once the resized
  cells are re-characterized and the corner sweep re-recorded.
- Follow-on work, filed as its own issues (none of it done in #129): the
  generator sizing change and regenerated netlists; re-characterization of
  the three cells at all three corners (append-only new `.lib` records); the
  re-recorded corner sweep and its README/record updates (coordinated with
  #87's manifest re-point); the layout re-fit of the three cells (wider
  P-diffusion row inside the 8-track width); the 0002 amendment this record
  proposes.
- `s5l_nand2_1` is not failing and is not resized by this record; it passes
  the failing point with +23 / +36 ps of rise margin today. If the follow-on
  expresses the sizing rule family-wide, its re-characterization will show
  whether that margin moves; until then it stays as ratified.
- If the ratification path amends the sizing, the numbers above are
  superseded by the re-characterization records; until then every value here
  is SIMULATED, never measured.
