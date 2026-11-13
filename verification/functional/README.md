# verification/functional — netlist vs RTL truth tables (issue #82, part of #27)

T1 item 5 functional evidence. Everything here is **simulated**, never measured.

- `gen_functional.py` — generates `tb_all.cir`, `tt.request.json` (one TT
  single-corner `klt sim` request, runs local; all 40 cells, every input vector,
  from `design/cells.json`), `tb_rtl.v` (exhaustive RTL truth tables), and
  `tb_corners.cir` + `corners.request.json` (the three-corner timing-arc sweep
  below). `--check` fails if stale; `--arcs` lists every derived arc and the
  side-input state that propagates it.
- `compare.py` — RTL tables (iverilog) vs the sim report, bit-exact on
  thresholded levels (<0.1·VDD → 0, >0.9·VDD → 1, otherwise fail).
  `--negative-control` flips one RTL bit and must fail.
- `test_functional.sh` — freshness, all-40-cells coverage, real pass, negative
  control, then `test_arcs.py`.
- `test_arcs.py` — cross-checks the derived arc list two ways: the evaluator
  that derives it (`design/gen_netlists.py`'s `evaluate`, behind the one shared
  Liberty-function parser the RTL models are generated from too) must reproduce
  the iverilog RTL truth tables on every one of the 356 vectors, and the arc
  count must equal the number of `timing ()` groups in the recorded TT Liberty
  (106). Then, if the corner report exists, that every arc is measured, limited
  and spec-row tagged at every ratified corner. Pass/fail of the arcs themselves
  is printed, not asserted — a recorded overshoot is evidence, not a broken test.
- `records/tt.report.json` — `klt sim` report (klt 0.9.1, ngspice 46 per `environment.engine_version`, TT 1.20 V 25 C). The repo pin (`sim/toolchain.json`) is ngspice 47, so this record was not produced at the pin.
- `records/functional.tt.json` — per-cell, per-vector pass/fail (356 checks, 40/40 pass).

Reproduce: `source .cache/env.sh; klt sim verification/functional/tt.request.json --backend local -o <out> --report-out verification/functional/records/tt.report.json; verification/functional/test_functional.sh`.

## Corner-matrix timing-arc sweep (issue #120)

The limit-checked half of T1 item 5. `tt.report.json` above applies no
`limits` at all, so the grader reads it as `no_limits_checked`; this sweep is
the one that bounds something.

- **What is measured.** Every timing arc of all 40 cells — one arc per
  `timing ()` group of the characterized Liberty, 106 of them, 0 declared
  gaps — as two delays each (rising and falling output edge, 212 total),
  50 %-of-rail to 50 %-of-rail, at each of the three ratified Liberty
  corners.
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

### Recorded result — `fail`, 5 of 636 arc delays over the bound

**SIMULATED, never measured.** TT and FF pass with every arc inside the bound.
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

Note: the RTL side runs iverilog directly rather than `klt functional-verification`
because cocotb is not installed on the build host (host tools are not modified);
the exhaustive-vector comparison is equivalent for combinational cells.
