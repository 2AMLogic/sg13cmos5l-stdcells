# verification/functional — netlist vs RTL truth tables (issue #82, part of #27)

T1 item 5 functional evidence. Everything here is **simulated**, never measured.

- `gen_functional.py` — generates `tb_all.cir`, `tt.request.json` (one TT
  single-corner `klt sim` request, runs local; all 40 cells, every input vector,
  from `design/cells.json`), `tb_rtl.v` (exhaustive RTL truth tables),
  `tb_corners.cir` + `corners.request.json` (the three-corner timing-arc sweep
  below), and `tb_corner_states.cir` + `corner_states.request.json` (the same
  sweep widened to every propagating side-input state, below that). `--check`
  fails if stale; `--arcs` lists every derived arc and the side-input state
  that propagates it, `--arc-states` lists every (arc, state) pair.
- `compare.py` — RTL tables (iverilog) vs the sim report, bit-exact on
  thresholded levels (<0.1·VDD → 0, >0.9·VDD → 1, otherwise fail).
  `--negative-control` flips one RTL bit and must fail. Two forms, and the
  distinction matters (issue #138):
  - `--report R --out P` **regenerates** `P` — the deliberate step after a new
    `klt sim` run, and the only thing here that writes the record.
  - `--report R --out P --check` is the **gate**: it compares the committed
    record at `P` against the freshly computed result in memory and never
    writes it, so a stale or hand-edited record is reported instead of
    silently repaired. Exit 1 = the netlist and RTL disagree (a broken
    library), exit 3 = the record is stale (out-of-date bookkeeping); the two
    verdicts are separate on purpose so a red log needs no guessing. Refused
    with `--negative-control`, which computes a deliberately wrong table.
- `test_functional.sh` — freshness (`gen_functional.py --check` **and**
  `compare.py --check`), all-40-cells coverage, real pass, the wrong-truth-table
  negative control, a stale-record negative control for the gate itself, then
  `test_arcs.py`. It only reads the records; a passing or failing run leaves
  `git status` clean.
- `test_arcs.py` — cross-checks the derived arc list two ways: the evaluator
  that derives it (`design/gen_netlists.py`'s `evaluate`, behind the one shared
  Liberty-function parser the RTL models are generated from too) must reproduce
  the iverilog RTL truth tables on every one of the 356 vectors, and the arc
  count must equal the number of `timing ()` groups in the recorded TT Liberty
  (106). Then, if the corner report exists, that every arc is measured, limited
  and spec-row tagged at every ratified corner. Pass/fail of the arcs themselves
  is printed, not asserted — a recorded overshoot is evidence, not a broken test.
  It applies the same two checks to the all-state sweep: that `arc_states()`
  reproduces, for every arc, the state list **and each state's output
  direction** that the iverilog RTL truth tables give — an independent oracle,
  not the enumeration's own `out_on_rise` field, because checking that field
  against itself silently accepts a non-unate arc flattened to unate (an
  earlier draft did, and a negative control caught it) — that it agrees with
  `arcs()` about which arcs exist and about each arc's first state, that its
  416 delay names are unique, that every arc the oracle calls non-unate
  measures each output edge from **both** input-edge directions, and that the
  all-state report covers every (arc, state, output edge) at all three
  corners.
  It also prints the per-corner comparison below — the state spread, and the
  run-to-run spread on the single-state arcs that bounds it — so those numbers
  are re-derived on every run rather than transcribed here.
- `records/tt.report.json` — `klt sim` report (klt 0.9.1, ngspice 46 per `environment.engine_version`, TT 1.20 V 25 C). The repo pin (`sim/toolchain.json`) is ngspice 47, so this record was not produced at the pin.
- `records/functional.tt.json` — per-cell, per-vector pass/fail (356 checks, 40/40 pass).

Reproduce: `source .cache/env.sh; klt sim verification/functional/tt.request.json --backend local -o <out> --report-out verification/functional/records/tt.report.json; python3 verification/functional/compare.py --report verification/functional/records/tt.report.json --out verification/functional/records/functional.tt.json; verification/functional/test_functional.sh`
— the `compare.py` call is the regeneration step for the new report, and
`test_functional.sh` then verifies what it wrote. To check the committed
records without a new sim, run `test_functional.sh` alone.

## Corner-matrix timing-arc sweep (issue #120)

The limit-checked half of T1 item 5. `tt.report.json` above applies no
`limits` at all, so the grader reads it as `no_limits_checked`; this sweep is
the one that bounds something.

- **What is measured.** Every timing arc of all 40 cells — one arc per
  `timing ()` group of the characterized Liberty, 106 of them, 0 declared
  gaps — as two delays each (rising and falling output edge, 212 total),
  50 %-of-rail to 50 %-of-rail, at each of the three ratified Liberty
  corners. **Each arc in one side-input state**: the first assignment of its
  non-switching inputs that propagates it. 30 of the 106 arcs have more than
  one propagating state, so for those this sweep bounds the one state it
  measured and not the arc (issue #124). The all-state sweep in the next
  section measures all 208 (arc, state) pairs and is what carries the
  worst-over-states claim; everything in *this* section is scoped to the
  single state named in `--arcs`.
- **Where.** One grid point: the ratified characterization grid's worst
  point, input slew 2.5074 ns and output load 0.3 pF. Stage delay is
  monotonic in both, so a pass there carries the bound over the whole 7 × 7
  grid — which is what `margin.py`'s all-points definition asserts.
- **Against what.** `limits.max` = 2.5074 ns, `sim/characterize/margin.py`'s
  `LIMIT_NS`, ratified as spec row `t_stage_delay_grid_bound` by
  [decision record 0005](../../spec/decision-records/0005-timing-margin-spec-row.md).
  A grid-validity bound, **not** a timing-closure budget.
- **How the deck handles three rails.** `.meas` thresholds are literals in
  the netlist, but 50 % of the rail differs per corner. So the stimulus is a
  unitless PWL shape (peak 1.0) scaled by the rail
  (`Bin vin 0 V = v(vdd)*v(vshape)`), giving an exactly rail-to-rail ramp of
  the grid's slew at every corner, and each output is mirrored through
  `V = v(out)/v(vdd)` — so the single literal `VAL=0.5` is 50 % of the
  actual rail in all three. Only `Vdd` is swept, as a plain DC source.
  Each arc gets its own cell instance, with its non-switching inputs tied
  straight to the rail or ground in a propagating state, so arcs cannot
  interact.
- `records/corners.report.json` — the recorded three-corner `klt sim` report
  (klt 0.9.1 client, fleet runner 0.9.0 — `major.minor` match — ngspice 47,
  batch job `klt-sim-6030b9203673`, 28 s). 212 arc delays per corner, all 212
  carrying `limits`, so the `no_limits_checked` refusal that `tt.report.json`
  draws no longer applies.

### Recorded result (one state per arc) — `fail`, 5 of 636 arc delays over the bound

**SIMULATED, never measured.** TT and FF pass with every arc inside the bound,
in the state measured.
SS / 1.08 V / 125 C fails on five rise arcs, all at the grid's extreme point:

| arc | delay | margin |
|---|---|---|
| `s5l_nand4_1` `Y<-D` rise | 2.5622 ns | **−0.0548 ns** |
| `s5l_nand4_1` `Y<-C` rise | 2.5393 ns | −0.0319 ns |
| `s5l_nand3_1` `Y<-C` rise | 2.5190 ns | −0.0116 ns |
| `s5l_nand3b_1` `Y<-C` rise | 2.5190 ns | −0.0116 ns |
| `s5l_nand4_1` `Y<-B` rise | 2.5151 ns | −0.0077 ns |

These are **the same five arcs, in the same order, with the same least margin
(−0.0548 ns)** that `margin.py` already records over the characterized Liberty
(`sim/characterize/README.md`, "Timing-margin metric"). That is an independent
reproduction: a hand-generated arc deck through `klt sim` on the batch fleet,
against NLDM tables produced by `klt characterize`, agreeing to four decimals
on the binding point. It corroborates both the deck here and the
characterization there.

Every one is a stacked-NMOS rise arc at the grid's largest slew *and* largest
load, at the slow **stretch** corner, missing by 0.3–2.2 % of the bound. As
`sim/characterize/README.md` already states, the bound is a grid-validity
bound and not a ratified delay budget, so this is a recorded property of the
slow corner at the grid's extreme, not a spec violation — and it is left as
it is. Nothing here is retuned to make it pass.

Graded with the pinned klt against a scratch manifest citing this report
(`spec_rows: {"5": [{"id": "t_stage_delay_grid_bound", "timing_margin":
true}]}`), T1 item 5 is **`unmet` / `check_failed`**, blocker
`sim__corner__failed_count: 1`, with `uncovered_rows: []`,
`declared_gaps: []` and `unratified_rows: []` — i.e. the timing-margin rule
itself is satisfied and only the measurement verdict blocks the item.
Re-pointing the committed manifest is [#87](https://github.com/2AMLogic/sg13cmos5l-stdcells/issues/87), not this record.

Two things #87 will need, found while grading:

- a `sim` citation's `content_hash` is checked against the report's
  **`provenance.input.content_hash`** (the netlist's hash), not the sha256 of
  the report file; citing the file hash grades `stale_evidence`;
- with the five arcs still over the bound, item 5 cannot reach `met` from this
  report. Narrowing the gap needs either a ratified delay budget or a grid
  change — both decision records, and neither is this issue's to make.

Reproduce (multi-corner ⇒ batch fleet, never a hand-launched local grid):

```
source .cache/env.sh
klt sim verification/functional/corners.request.json --backend batch \
    --wait-for-capacity 600 \
    --report-out verification/functional/records/corners.report.json
python3 verification/functional/test_arcs.py
```

## All-state arc sweep (issue #124)

The sweep above measures each arc in **one** propagating side-input state.
This one measures it in **every** one. Same 106 arcs, same grid point, same
three corners, same `limits.max` = 2.5074 ns, same spec row
`t_stage_delay_grid_bound` — only the measured population widens, from 106
arcs to the **208 propagating (arc, state) pairs**, i.e. 416 delays per
corner against 212. Recorded separately, because recorded results are
append-only: `corners.*` is byte-for-byte unchanged by this work.

- **Why.** Decision record 0005 section 3 bounds "every timing arc"; the
  single-state deck evidences that in one admissible state per arc. For the
  30 multi-state arcs (8 of them non-unate) a different state could be
  slower, and no state other than the first had been simulated. See the
  [0005 addendum of 2026-11-14](../../spec/decision-records/0005-timing-margin-spec-row.md),
  which reads the row as the worst delay over every propagating state.
- **What is measured.** For every (arc, state) pair, the rising and the
  falling output-edge delay, 50 %-of-rail to 50 %-of-rail, at TT / FF / SS.
  Covering every state is also what gives each **non-unate** arc both
  input-edge directions per output edge, which the single-state deck cannot
  have: `test_arcs.py` asserts that it does rather than assuming it.
- **How it is named.** Each measurement name carries its state —
  `d_s5l_a21o_1_x_a1_s_a2_1_b1_0_r` is A1→X rise with A2 held high and B1
  low. `_s_` separates arc from state, and the level is its own `_` field
  because every pin name already ends in a digit (`a2_1`, not `a21`). All
  416 names are unique, asserted.
- **Same deck, longer list.** `tb_corner_states.cir` is `tb_corners.cir`'s
  generator over `arc_states()` instead of `arcs()`, and both enumerations
  read one shared `propagating_states()` helper, so they cannot disagree
  about what propagates. One self-contained job keeps every per-arc
  state comparison inside a single deck, environment and solver run.
- `records/corner_states.report.json` — the recorded three-corner `klt sim`
  report (klt 0.9.1 client — the `layout/toolchain.json` pin, run via
  `uvx --from klayout-tools==0.9.1` — fleet runner 0.9.0, `major.minor`
  match, ngspice 47, batch job `klt-sim-5a89364ff41a`, 73 s, 64.4–64.6 s per
  corner). 416 delays per corner, all 416 carrying `limits` and the spec row.

### Recorded result — `fail`, the same 5 of 1248 delays over the bound

**SIMULATED, never measured.** The verdict does not move, but the margins do.

| corner | delays | over the bound | tightest passing margin |
|---|--:|---|--:|
| TT / 1.20 V / 25 °C | 416 | 0 | +0.5038 ns (`s5l_nand4_1` `Y<-D` rise) |
| FF / 1.32 V / −40 °C | 416 | 0 | +0.9596 ns (`s5l_nand4_1` `Y<-D` rise) |
| SS / 1.08 V / 125 °C | 416 | 5 | **+0.0009 ns** (`s5l_mux4_1` `X<-A3` rise) |

**No arc that passed in its first state fails in another.** SS is over the
bound on exactly the five stacked-NMOS rise arcs the single-state record
already names (`s5l_nand3_1` `Y<-C`, `s5l_nand3b_1` `Y<-C`, `s5l_nand4_1`
`Y<-{B,C,D}`), at the same values; all five are single-state arcs, so
widening the state coverage could not have changed them. TT and FF pass all
416.

**The headline finding is a margin, not a failure.** At SS the worst state is
slower than the first on **41 of the 60 multi-state arc edges**, by up to
**+0.3610 ns** — 14.4 % of the bound (39 of 60 at TT, 38 of 60 at FF). The
library's tightest *passing* margin at SS therefore drops from the +6.55 ps
that prompted this issue to **+0.86 ps**, 0.03 % under the bound, on
`s5l_mux4_1` `X<-A3` rise holding `A0=1 A1=1 A2=1 S0=1 S1=1`. That arc has
eight propagating states spanning 2.43480–2.50654 ns, and `arcs()` happened
to pick the **fastest** of them (+72.60 ps). 16 of the 416 passing delays sit
within 50 ps of the bound at SS, where the single-state record had 9 of 212.

The arc the issue was filed about is **exonerated**: `s5l_o21ai_1` `Y<-B1`
rise is slowest in the state already measured — 2.50085 ns, against
2.49603 ns and 2.50083 ns for its other two states.

**What bounds those numbers.** The 152 *single*-state arc edges have one
state each, so any difference between this record and `corners.report.json`
is numerical — a 208-instance deck gives a different matrix and a different
adaptive timestep. That spread is **≤ 0.2 ps** across all three corners
(worst: `s5l_and4_1` `X<-B` fall at FF). The state spreads above are up to
1800× that, so they are an effect and not solver noise. `test_arcs.py` prints
both spreads side by side on every run for exactly this reason.

### Every multi-state arc edge, per corner

Complete: all 30 multi-state arcs × 2 output edges, sorted by SS state
spread. "single" is the state `corners.report.json` measured; "worst" is the
worst over all of the arc's states in this run (**bold** where they differ).
All values in ns, SIMULATED.

| arc | edge | states | TT single → worst | FF single → worst | SS single → worst | SS worst state | SS margin |
|---|---|--:|---|---|---|---|--:|
| `s5l_mux4_1` `X<-S0` | fall | 16 | 1.1884 → **1.5038** | 0.7542 → **1.0346** | 1.9338 → **2.2948** | `A0=1 A1=1 A2=1 A3=0 S1=1` | +0.2126 |
| `s5l_a221oi_1` `Y<-C1` | rise | 9 | 1.3429 → **1.5247** | 0.8991 → **0.9968** | 1.8563 → **2.1874** | `A1=1 A2=0 B1=1 B2=0` | +0.3200 |
| `s5l_a22oi_1` `Y<-A2` | rise | 3 | 1.6085 → **1.8294** | 1.1736 → **1.3412** | 2.0886 → **2.4010** | `A1=1 B1=1 B2=0` | +0.1064 |
| `s5l_mux4_1` `X<-S1` | fall | 16 | 1.2049 → **1.4828** | 0.7760 → **1.0227** | 1.9503 → **2.2601** | `A0=1 A1=1 A2=1 A3=0 S0=1` | +0.2473 |
| `s5l_a22oi_1` `Y<-A1` | rise | 3 | 1.5993 → **1.8186** | 1.1641 → **1.3308** | 2.0783 → **2.3870** | `A2=1 B1=1 B2=0` | +0.1204 |
| `s5l_mux4_1` `X<-A0` | fall | 8 | 0.9755 → **1.2010** | 0.6359 → **0.8242** | 1.5662 → **1.8568** | `A1=1 A2=1 A3=1 S0=0 S1=0` | +0.6506 |
| `s5l_mux4_1` `X<-A1` | fall | 8 | 1.0825 → **1.2585** | 0.7069 → **0.8487** | 1.7255 → **1.9615** | `A0=1 A2=1 A3=1 S0=1 S1=0` | +0.5459 |
| `s5l_a22oi_1` `Y<-B2` | rise | 3 | 1.5754 → **1.6942** | 1.1260 → **1.1925** | 2.0959 → **2.3152** | `A1=1 A2=0 B1=1` | +0.1922 |
| `s5l_a221oi_1` `Y<-A2` | rise | 3 | 1.5956 → **1.7496** | 1.1386 → **1.2550** | 2.1132 → **2.3310** | `A1=1 B1=1 B2=0 C1=0` | +0.1764 |
| `s5l_a22oi_1` `Y<-B1` | rise | 3 | 1.5663 → **1.6837** | 1.1172 → **1.1830** | 2.0850 → **2.3011** | `A1=1 A2=0 B2=1` | +0.2063 |
| `s5l_a221oi_1` `Y<-A1` | rise | 3 | 1.5856 → **1.7385** | 1.1281 → **1.2439** | 2.1016 → **2.3168** | `A2=1 B1=1 B2=0 C1=0` | +0.1906 |
| `s5l_a21oi_1` `Y<-B1` | rise | 3 | 1.5565 → **1.6722** | 1.0970 → **1.1611** | 2.0764 → **2.2900** | `A1=1 A2=0` | +0.2174 |
| `s5l_xor2_1` `X<-A` | fall | 2 | 0.9525 → **1.0900** | 0.6547 → **0.7457** | 1.5059 → **1.7149** | `B=1` | +0.7925 |
| `s5l_mux4_1` `X<-A2` | fall | 8 | 1.1596 → **1.3099** | 0.7528 → **0.8694** | 1.8527 → **2.0578** | `A0=1 A1=1 A3=1 S0=0 S1=1` | +0.4496 |
| `s5l_mux4_1` `X<-A0` | rise | 8 | 1.2861 → **1.4288** | 0.9194 → **1.0104** | 1.9142 → **2.1154** | `A1=1 A2=1 A3=1 S0=0 S1=0` | +0.3920 |
| `s5l_mux4_1` `X<-A3` | fall | 8 | 1.1965 → **1.2955** | 0.7617 → **0.8314** | 1.9233 → **2.0725** | `A0=1 A1=1 A2=1 S0=1 S1=1` | +0.4349 |
| `s5l_mux2_1` `X<-S` | fall | 2 | 0.9649 → **1.0707** | 0.6493 → **0.7347** | 1.5388 → **1.6864** | `A0=1 A1=0` | +0.8210 |
| `s5l_a221oi_1` `Y<-B2` | rise | 3 | 1.6024 → **1.6772** | 1.1287 → **1.1700** | 2.1582 → **2.3041** | `A1=1 A2=0 B1=1 C1=0` | +0.2033 |
| `s5l_xor2_1` `X<-A` | rise | 2 | 1.1315 → **1.2155** | 0.7737 → **0.7865** | 1.7171 → **1.8616** | `B=1` | +0.6458 |
| `s5l_a221oi_1` `Y<-B1` | rise | 3 | 1.5926 → **1.6664** | 1.1190 → **1.1599** | 2.1460 → **2.2898** | `A1=1 A2=0 B2=1 C1=0` | +0.2176 |
| `s5l_mux4_1` `X<-A1` | rise | 8 | 1.4392 → **1.5390** | 1.0299 → **1.0950** | 2.1276 → **2.2656** | `A0=1 A2=1 A3=1 S0=1 S1=0` | +0.2418 |
| `s5l_mux2_2` `X<-S` | fall | 2 | 0.6741 → **0.7576** | 0.4492 → **0.5268** | 1.0420 → **1.1565** | `A0=1 A1=0` | +1.3509 |
| `s5l_mux4_1` `X<-A2` | rise | 8 | 1.5737 → **1.6434** | 1.1331 → **1.1767** | 2.3036 → **2.4017** | `A0=1 A1=1 A3=1 S0=0 S1=1` | +0.1057 |
| `s5l_mux4_1` `X<-S1` | rise | 16 | 1.5266 → **1.5886** | 1.0499 → **1.0562** | 2.2848 → **2.3821** | `A0=1 A1=1 A2=1 A3=0 S0=1` | +0.1253 |
| `s5l_a21oi_2` `Y<-B1` | rise | 3 | 1.0708 → **1.1269** | 0.7146 → **0.7507** | 1.4649 → **1.5604** | `A1=1 A2=0` | +0.9471 |
| `s5l_mux4_1` `X<-S0` | rise | 16 | 1.5860 → **1.6218** | 1.1192 → **1.1294** | 2.3425 → **2.4364** | `A0=1 A1=1 A2=1 A3=0 S1=1` | +0.0710 |
| `s5l_xor2_1` `X<-B` | fall | 2 | 1.0152 → **1.0775** | 0.6923 → **0.7388** | 1.6109 → **1.6947** | `A=1` | +0.8127 |
| `s5l_mux4_1` `X<-A3` | rise | 8 | 1.6753 → **1.7261** | 1.2144 → **1.2475** | 2.4348 → **2.5065** | `A0=1 A1=1 A2=1 S0=1 S1=1` | +0.0009 |
| `s5l_mux2_2` `X<-A0` | fall | 2 | 0.6990 → **0.7435** | 0.4857 → **0.5311** | 1.0647 → **1.1145** | `A1=1 S=0` | +1.3929 |
| `s5l_a21o_1` `X<-B1` | fall | 3 | 0.9428 → **0.9765** | 0.5891 → **0.6146** | 1.5491 → **1.5983** | `A1=1 A2=0` | +0.9091 |
| `s5l_a21o_2` `X<-B1` | fall | 3 | 0.6539 → **0.6872** | 0.3941 → **0.4191** | 1.0516 → **1.0999** | `A1=1 A2=0` | +1.4075 |
| `s5l_mux2_1` `X<-S` | rise | 2 | 1.1821 → **1.1982** | 0.8172 → **0.8172** | 1.7878 → **1.8356** | `A0=1 A1=0` | +0.6718 |
| `s5l_mux2_1` `X<-A0` | fall | 2 | 0.9882 → **1.0295** | 0.6811 → **0.7239** | 1.5625 → **1.6082** | `A1=1 S=0` | +0.8992 |
| `s5l_a21o_1` `X<-B1` | rise | 3 | 1.3820 → **1.4070** | 0.9828 → **0.9988** | 2.0293 → **2.0649** | `A1=1 A2=0` | +0.4425 |
| `s5l_a21o_2` `X<-B1` | rise | 3 | 1.0087 → **1.0311** | 0.7485 → **0.7630** | 1.4326 → **1.4648** | `A1=1 A2=0` | +1.0426 |
| `s5l_mux2_2` `X<-S` | rise | 2 | 0.8066 → **0.8066** | 0.5797 → **0.5797** | 1.1895 → **1.2040** | `A0=1 A1=0` | +1.3034 |
| `s5l_xor2_1` `X<-B` | rise | 2 | 1.2094 → 1.2094 | 0.8110 → **0.8110** | 1.8420 → **1.8477** | `A=1` | +0.6597 |
| `s5l_a22oi_1` `Y<-A2` | fall | 3 | 1.5021 → **1.5048** | 1.1194 → **1.1207** | 2.0352 → **2.0382** | `A1=1 B1=1 B2=0` | +0.4692 |
| `s5l_a221oi_1` `Y<-A2` | fall | 3 | 1.5134 → **1.5161** | 1.1350 → **1.1366** | 2.0482 → **2.0513** | `A1=1 B1=1 B2=0 C1=0` | +0.4561 |
| `s5l_a22oi_1` `Y<-A1` | fall | 3 | 1.5875 → **1.5902** | 1.2295 → **1.2309** | 2.0845 → **2.0873** | `A2=1 B1=1 B2=0` | +0.4201 |
| `s5l_a221oi_1` `Y<-A1` | fall | 3 | 1.5999 → **1.6027** | 1.2467 → **1.2483** | 2.0978 → **2.1006** | `A2=1 B1=1 B2=0 C1=0` | +0.4068 |
| `s5l_xnor2_1` `Y<-B` | rise | 2 | 1.6731 → 1.6731 | 1.1767 → **1.1767** | 2.2865 → 2.2865 | `A=0` | +0.2209 |
| `s5l_xnor2_1` `Y<-B` | fall | 2 | 1.5122 → 1.5122 | 1.1269 → 1.1269 | 2.0504 → 2.0504 | `A=0` | +0.4570 |
| `s5l_xnor2_1` `Y<-A` | rise | 2 | 1.7896 → 1.7896 | 1.3030 → 1.3030 | 2.3512 → 2.3512 | `B=0` | +0.1562 |
| `s5l_xnor2_1` `Y<-A` | fall | 2 | 1.5834 → 1.5834 | 1.2241 → 1.2241 | 2.0805 → 2.0805 | `B=0` | +0.4269 |
| `s5l_o21ai_1` `Y<-B1` | rise | 3 | 1.9563 → 1.9563 | 1.4948 → 1.4948 | 2.5009 → 2.5009 | `A1=0 A2=1` | +0.0066 |
| `s5l_o21ai_1` `Y<-B1` | fall | 3 | 1.5087 → 1.5087 | 1.1118 → 1.1118 | 2.0491 → 2.0491 | `A1=0 A2=1` | +0.4583 |
| `s5l_mux2_2` `X<-A1` | rise | 2 | 0.8757 → 0.8757 | 0.6050 → **0.6050** | 1.2978 → 1.2978 | `A0=0 S=1` | +1.2096 |
| `s5l_mux2_2` `X<-A1` | fall | 2 | 0.7542 → 0.7542 | 0.5125 → 0.5125 | 1.1512 → 1.1512 | `A0=0 S=1` | +1.3562 |
| `s5l_mux2_2` `X<-A0` | rise | 2 | 0.7896 → 0.7896 | 0.5412 → **0.5412** | 1.1767 → 1.1767 | `A1=0 S=0` | +1.3307 |
| `s5l_mux2_1` `X<-A1` | rise | 2 | 1.2598 → 1.2598 | 0.8486 → **0.8486** | 1.9075 → 1.9075 | `A0=0 S=1` | +0.6000 |
| `s5l_mux2_1` `X<-A1` | fall | 2 | 1.0498 → 1.0498 | 0.7121 → 0.7121 | 1.6574 → 1.6574 | `A0=0 S=1` | +0.8500 |
| `s5l_mux2_1` `X<-A0` | rise | 2 | 1.1678 → 1.1678 | 0.7840 → **0.7840** | 1.7765 → 1.7765 | `A1=0 S=0` | +0.7309 |
| `s5l_a22oi_1` `Y<-B2` | fall | 3 | 1.5246 → 1.5246 | 1.1388 → 1.1388 | 2.0651 → 2.0651 | `A1=0 A2=0 B1=1` | +0.4423 |
| `s5l_a22oi_1` `Y<-B1` | fall | 3 | 1.6110 → 1.6110 | 1.2508 → 1.2508 | 2.1135 → 2.1135 | `A1=0 A2=0 B2=1` | +0.3939 |
| `s5l_a221oi_1` `Y<-C1` | fall | 9 | 1.8759 → 1.8759 | 1.4950 → 1.4950 | 2.4080 → 2.4080 | `A1=0 A2=0 B1=0 B2=0` | +0.0994 |
| `s5l_a221oi_1` `Y<-B2` | fall | 3 | 1.5458 → 1.5458 | 1.1620 → 1.1620 | 2.0915 → 2.0915 | `A1=0 A2=0 B1=1 C1=0` | +0.4160 |
| `s5l_a221oi_1` `Y<-B1` | fall | 3 | 1.6338 → 1.6338 | 1.2765 → 1.2765 | 2.1398 → 2.1398 | `A1=0 A2=0 B2=1 C1=0` | +0.3676 |
| `s5l_a21oi_2` `Y<-B1` | fall | 3 | 1.3553 → 1.3553 | 1.0498 → 1.0498 | 1.7513 → 1.7513 | `A1=0 A2=0` | +0.7561 |
| `s5l_a21oi_1` `Y<-B1` | fall | 3 | 1.8247 → 1.8247 | 1.4429 → 1.4429 | 2.3392 → 2.3392 | `A1=0 A2=0` | +0.1682 |

The 76 single-state arcs are unchanged by construction and are not listed;
their values are `corners.report.json`'s, inside the ≤ 0.2 ps numerical
spread above.

Reproduce (multi-corner ⇒ batch fleet, never a hand-launched local grid):

```
source .cache/env.sh
klt sim verification/functional/corner_states.request.json --backend batch \
    --wait-for-capacity 600 \
    --report-out verification/functional/records/corner_states.report.json
python3 verification/functional/test_arcs.py
```

Note: the RTL side runs iverilog directly rather than `klt functional-verification`
because cocotb is not installed on the build host (host tools are not modified);
the exhaustive-vector comparison is equivalent for combinational cells.
