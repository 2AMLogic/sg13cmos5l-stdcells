# 0002 — Ratify the 40-cell combinational list

- **Status**: accepted
- **Date**: 2026-10-27
- **Issue**: #33 (part of #23)

## Context

[`target-spec.md`](../target-spec.md) fixes the combinational cell *count* (40)
but no list existed; the origin `sg13g2-stdcells` has none to take by pinned
reference. Netlists, models, layout, LVS and Liberty (#23, #24, #26, #27) need
one authoritative list. Benchmarks compare against the PDK's own
`sg13cmos5l_stdcell`, so the list is drawn from that library, not from SG13G2.

## Decision

Ratify [`design/cells.json`](../../design/cells.json) as the single source: 40
combinational cells, every one with a counterpart in the PDK
`sg13cmos5l_stdcell` cell list.

**Naming.** `s5l_<function>_<drive>`, mirroring the PDK's `<function>_<drive>`
suffix, with the PDK counterpart recorded per cell in `pdk_counterpart`. The
prefix differs from `sg13cmos5l_` so both libraries can be loaded in one flow
without cell-name collisions. Pin names are the PDK's.

**Selection.** The PDK library has 49 single-output combinational cells
excluding sequential, latch, clock-gate, fill, decap, tie, antenna, `sighold`,
delay (`dlygate*`) and tri-state (`ebufn`/`einvn`) cells. Nine are left out to
reach 40:

- `inv_8`, `inv_16`, `buf_8`, `buf_16`: very high drives are the hardest to fit
  in an 8-track row, and the 8-track fit is unproven (target-spec, row height).
- `and4_2`, `or4_2`, `nor4_2`: 4-deep stacks at double width, same reason.
- `nand2b_2`, `nor2b_2`: second drive of the inverted-input variants adds
  little mapping value.

Delay and tri-state cells are excluded because they need a different
characterization (non-logic or three-state outputs). Sequential, fill, decap
and tie cells are not counted by the spec. This is a ratification of scope,
not a relaxation: the count stays 40.

## Cells

| Cell | PDK counterpart | Inclusion reason |
|---|---|---|
| `s5l_a21o_1` | `sg13cmos5l_a21o_1` | AND-OR complex gate |
| `s5l_a21o_2` | `sg13cmos5l_a21o_2` | AND-OR complex gate |
| `s5l_a21oi_1` | `sg13cmos5l_a21oi_1` | AND-OR-invert complex gate |
| `s5l_a21oi_2` | `sg13cmos5l_a21oi_2` | AND-OR-invert complex gate |
| `s5l_a22oi_1` | `sg13cmos5l_a22oi_1` | two-pair AND-OR-invert |
| `s5l_a221oi_1` | `sg13cmos5l_a221oi_1` | largest AOI; mapping density |
| `s5l_and2_1` | `sg13cmos5l_and2_1` | non-inverting mapping target |
| `s5l_and2_2` | `sg13cmos5l_and2_2` | non-inverting mapping target |
| `s5l_and3_1` | `sg13cmos5l_and3_1` | non-inverting mapping target |
| `s5l_and3_2` | `sg13cmos5l_and3_2` | non-inverting mapping target |
| `s5l_and4_1` | `sg13cmos5l_and4_1` | non-inverting mapping target |
| `s5l_buf_1` | `sg13cmos5l_buf_1` | non-inverting buffer for fan-out and timing repair |
| `s5l_buf_2` | `sg13cmos5l_buf_2` | non-inverting buffer for fan-out and timing repair |
| `s5l_buf_4` | `sg13cmos5l_buf_4` | non-inverting buffer for fan-out and timing repair |
| `s5l_inv_1` | `sg13cmos5l_inv_1` | universal inverter; three drives (1/2/4) span the load range the 7x7 grid covers |
| `s5l_inv_2` | `sg13cmos5l_inv_2` | universal inverter; three drives (1/2/4) span the load range the 7x7 grid covers |
| `s5l_inv_4` | `sg13cmos5l_inv_4` | universal inverter; three drives (1/2/4) span the load range the 7x7 grid covers |
| `s5l_mux2_1` | `sg13cmos5l_mux2_1` | 2:1 select |
| `s5l_mux2_2` | `sg13cmos5l_mux2_2` | 2:1 select |
| `s5l_mux4_1` | `sg13cmos5l_mux4_1` | 4:1 select |
| `s5l_nand2_1` | `sg13cmos5l_nand2_1` | basic universal gate |
| `s5l_nand2_2` | `sg13cmos5l_nand2_2` | basic universal gate |
| `s5l_nand2b_1` | `sg13cmos5l_nand2b_1` | NAND with one inverted input (saves an inverter) |
| `s5l_nand3_1` | `sg13cmos5l_nand3_1` | 3-input NAND for mapping depth |
| `s5l_nand3b_1` | `sg13cmos5l_nand3b_1` | NAND3 with one inverted input |
| `s5l_nand4_1` | `sg13cmos5l_nand4_1` | 4-input NAND; widest series stack kept |
| `s5l_nor2_1` | `sg13cmos5l_nor2_1` | basic universal gate |
| `s5l_nor2_2` | `sg13cmos5l_nor2_2` | basic universal gate |
| `s5l_nor2b_1` | `sg13cmos5l_nor2b_1` | NOR with one inverted input |
| `s5l_nor3_1` | `sg13cmos5l_nor3_1` | 3-input NOR |
| `s5l_nor3_2` | `sg13cmos5l_nor3_2` | 3-input NOR |
| `s5l_nor4_1` | `sg13cmos5l_nor4_1` | 4-input NOR; single drive, 4 series PMOS |
| `s5l_o21ai_1` | `sg13cmos5l_o21ai_1` | OR-AND-invert complex gate |
| `s5l_or2_1` | `sg13cmos5l_or2_1` | non-inverting mapping target |
| `s5l_or2_2` | `sg13cmos5l_or2_2` | non-inverting mapping target |
| `s5l_or3_1` | `sg13cmos5l_or3_1` | non-inverting mapping target |
| `s5l_or3_2` | `sg13cmos5l_or3_2` | non-inverting mapping target |
| `s5l_or4_1` | `sg13cmos5l_or4_1` | non-inverting mapping target |
| `s5l_xnor2_1` | `sg13cmos5l_xnor2_1` | arithmetic / equality |
| `s5l_xor2_1` | `sg13cmos5l_xor2_1` | arithmetic / parity |

## Consequences

- Cells beyond drive 4 are absent, so a benchmark mapping may use larger
  baseline cells that this library lacks; that is measured, not hidden.
- Adding or removing a cell needs a new decision record and a count change in
  the spec. `design/check_catalog.py` enforces exactly 40 distinct entries.
