# Target specification

Ratified by [decision record 0001](decision-records/0001-ratify-target-spec.md).
Evidence for every PDK statement is in [`pdk-comparison.md`](pdk-comparison.md).
The README target table is a copy of the Parameter rows below and must match
them.

**Origin read.** `2AMLogic/sg13g2-stdcells` at
`f450813c6a5eecf3cf67aaf899db90d11f4ee68c` (2026-10-17). Its `spec/` is a
placeholder and its own target table is still marked DRAFT (its issue #1), so
there are no origin decision records to inherit: the only origin input is that
README table. "Inherited" below means that table. Where the origin later
ratifies or changes a row, the matching row here is re-checked (a new decision
record), not silently followed.

**Status vocabulary.** *confirmed* — the inherited value stands and the PDK
evidence does not contradict it. *changed* — the value differs from the
inherited one; the reason is given. A confirmed row can still carry a *risk*:
a thing the spec does not claim to have verified.

## Parameters

| Parameter | Target | Fallback | Stretch | vs origin |
|---|---|---|---|---|
| Row height | 3.36 µm (8 tracks of 0.42 µm) | 3.78 µm (9 tracks), the `sg13cmos5l_stdcell` site height | — | confirmed (fallback made concrete) |
| Routing grid | 0.42 µm × 0.42 µm | — | — | confirmed |
| Intra-cell routing | Metal1 only | — | — | confirmed |
| Pin access | every pin on a routing-grid point | — | — | confirmed |
| Combinational cells | 40 | 20 | 120 | confirmed |
| Sequential cells | 0 (deferred) | — | 8 | confirmed |
| DRC | clean, `klt drc`, SG13CMOS5L deck | — | — | confirmed |
| LVS | layout-vs-schematic match, `klt lvs` | — | — | confirmed |
| Core supply | 1.20 V (`sg13_lv` devices) | — | — | confirmed |
| Liberty corners | TT / 1.20 V / 25 °C | — | + FF / 1.32 V / −40 °C, SS / 1.08 V / 125 °C | confirmed (supplies stated) |
| Characterization grid | input slew 0.0186, 0.0966, 0.174, 0.3294, 0.6408, 1.263, 2.5074 ns; output load 0.001, 0.0234, 0.039, 0.0648, 0.108, 0.18, 0.3 pF (7 × 7) | — | — | new (origin states none) |
| Benchmark cell area vs `sg13cmos5l_stdcell` | ≤ 1.00× | ≤ 1.20× | ≤ 0.80× | confirmed |
| Benchmark energy vs `sg13cmos5l_stdcell` | ≤ 1.00× | — | ≤ 0.80× | confirmed (carried from origin) |
| Benchmark clock period vs `sg13cmos5l_stdcell` | within 10 % | within 20 % | within 5 % | confirmed |

Benchmark rows compare like with like: same PDK, same open flow, same designs.
No cross-library or cross-PDK number is a result of this repo.

## Row reasoning

**Row height — confirmed, with a risk and a concrete fallback.**
The origin target is 3.36 µm. The PDK's own library uses a 0.48 × 3.78 µm site
(9 tracks), so the 8-track target is *smaller than the baseline*, and nothing
in the PDK documents says 3.36 µm is reachable: neither rule document states a
minimum row height, and it follows from the generated layout. The rules a
generator reads for the cell body are identical in the two PDKs (pdk-comparison,
"What the two PDKs share"), so any feasibility finding upstream carries over;
the metal stack does not enter the row height because intra-cell routing is
Metal1 only. Row height is therefore left as the target, **not claimed
achievable**, and the fallback is fixed at 3.78 µm. A row height falling back
to 3.78 µm is the only permitted relaxation, and only through a new decision
record that cites the generator evidence for why 3.36 µm failed.

**Routing grid — confirmed, with a risk.**
The PDK's own track file puts Metal1 and Metal3 on a 0.42 µm pitch and Metal2
and Metal4 on 0.48 µm; the baseline site is 0.48 µm wide. A library on a
0.42 µm pin grid therefore does not align with the Metal2/Metal4 tracks the
router will use. This is the same relation as in the origin PDK's library
(its LEF is identical), so the origin decision carries over, but whether
OpenROAD reaches every pin on this stack is exactly what the benchmark
measures. Success criterion, not relaxed: the benchmark designs route with no
pin-access failures and no DRC violations.

**Intra-cell routing — confirmed.** Metal1 rules (M1.a–M1.k) are identical in
the two PDKs; the stack difference is above Metal1.

**Pin access — confirmed; stack consequence recorded.** Pins are on Metal1 on
the 0.42 µm grid. Signal routing above the cells has Metal2–Metal4 (three
layers, one fewer than SG13G2) and the thick layer is TopMetal1 only,
horizontal; there is no TopMetal2. The rail is the baseline's: Metal1, 0.44 µm
wide, centered on the cell boundary. A different power-rail or pin-access
scheme is **not** adopted — the reduced stack does not break port parity at the
cell level; it reduces routing resources for the benchmark. If the benchmark
shows the stack cannot route the designs, that is a finding recorded in a new
decision record, not a reason to edit this row.

**Combinational cells — confirmed.** 40 / 20 / 120 are cell-count targets and
do not depend on the PDK. The baseline has 84 macros including sequential,
fill, decap and tie cells; the count is not a target for this library.
The 40-cell list is ratified by [decision record 0002](decision-records/0002-cell-list.md)
(catalog: [`design/cells.json`](../design/cells.json)).

**Sequential cells — confirmed deferred.** Same deferral as the origin: the
setup/hold characterization machinery does not exist yet. The 8-cell stretch is
unchanged.

**DRC / LVS — confirmed; coverage not verified.** `klt` has a built-in
`sg13cmos5l` deck (`released: False`) with device classes nfet, pfet,
cap_cmomi, cap_cmomf and resistor; it has no `dantenna`/`dpantenna` class,
which the `sg13g2` deck does. Which rules the deck does not yet cover on a real
cell is **deferred to issue #4** (its `klt` smoke run). Until that run lands,
no cell is called DRC/LVS clean.

**Core supply and Liberty corners — confirmed, 1.20 V stated.** Reference cells
use only `sg13_lv_nmos`/`sg13_lv_pmos`. The baseline Liberty set has a 1.20 V
family (1.08 / 1.20 / 1.32 V) matching the origin's TT/FF/SS corners, and a
second 1.50 V family (1.35 / 1.50 / 1.65 V). The 1.5 V family is **out of
scope**: the origin has no such row, and adding it would be a spec change
made without a need. Supply excursions per corner: TT 1.20 V, FF 1.32 V
(+10 %), SS 1.08 V (−10 %), as the baseline's own corners.

**Characterization grid — new.** The origin states none. The grid is the
baseline's own `TIMING_DELAY_7x7ds1` index set, so that tables are comparable
point-for-point; constraint tables (sequential) are deferred with them.

**Benchmark energy — carried.** The origin lists an energy row. This repo's
earlier README omitted it; it is carried to keep the port at parity, measured
by the same power report on both libraries. No fallback is set because the
origin has none.

**Benchmark designs and flow.** The origin names no benchmark designs. Flow:
the open flow the PDK ships for the baseline — Yosys synthesis and OpenROAD
place-and-route through the LibreLane configuration in
`libs.tech/librelane/` (corners nom_typ_1p20V_25C, nom_fast_1p32V_m40C,
nom_slow_1p08V_125C) — run once with `sg13cmos5l_stdcell` and once with this
library, with the same designs, constraints and floorplan rules. Design set:
chosen by the benchmark issue, subject to the constraint that follows from the
sequential deferral — **this library has no flip-flops, so a design that needs
them cannot be mapped to it alone.** Until sequential cells exist, the
benchmark either uses purely combinational designs or is not run; mixing
baseline flip-flops into this library's result is not permitted because it
makes the comparison unlike. The benchmark also depends on Liberty writing
(below).

## Open questions, answered

1. *Does the reduced stack force a different power-rail or pin-access scheme,
   and does that break port parity?* No at the cell level (above). The risk
   moves to benchmark routability, where it is measured, not assumed.
2. *Does `klt` resolve SG13CMOS5L for DRC and LVS of individual cells, and which
   rules does its deck not yet cover?* The deck exists and is unreleased; its
   coverage on cells is **deferred to #4**.
3. *Which of the origin's deferrals apply here unchanged?* Both: sequential
   cells, and writing Liberty from characterization (the origin cites
   `2AMLogic/klayout-tools#2498`: `klt` reads NLDM Liberty but no verb writes
   it). Neither is resolved here; both gate the benchmark.

## Reuse from `sg13g2-stdcells` and how it is pinned

PDK-independent material is taken from `2AMLogic/sg13g2-stdcells`, never forked:
cell generators, characterization-harness mechanics, benchmark scripts. It is
taken by a pinned reference recorded in `reuse.lock.json` at the repo root
(commit SHA of the origin; file mechanics are issue #3's). The pin is advanced
deliberately, by a commit that names the origin SHA.

At the SHA read above the origin holds a harness, `flow/`, `views/` and a
placeholder `spec/`, and **no cell generators**. This repo owns: the
SG13CMOS5L configuration of the generators, the cells it produces, their views
and their evidence. A rule the origin's generators cannot express is fixed
upstream first; a local divergence needs a decision record. No generator gap is
known today (none can be, with no generator); none is filed. This is re-checked
when the first generator is pinned.

## Not decided here

PDK and toolchain pin, `klt` smoke runs (#4); `reuse.lock.json` and harness
vendoring (#3); CI and the signoff manifest (#5); any cell or generator.
