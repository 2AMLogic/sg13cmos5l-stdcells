# sim/characterize

Issue #27 (T1 item 5): NLDM characterization of the 40 combinational cells.
Everything here is **simulated**, never measured. **Status: TT and FF
complete (40/40 cells each), SS not run.**

| path | what |
|---|---|
| `gen_requests.py` | writes `requests/{tt,ff,ss}.request.json` from `design/cells.json`; `--check` exits 1 if they are stale |
| `requests/` | one `klt characterize` request per Liberty corner in `spec/target-spec.md` (TT target; FF, SS stretch), 40 cells, the spec's 7 x 7 grid |
| `margin.py`, `test_margin.py` | the timing-margin metric (defined in `margin.py`'s docstring, the one place): `margin = LIMIT_NS - delay` per (cell, arc, slew, load, corner); table + per-arc pass/fail + binding corner from any `records/*.lib` |
| `check_lib_coverage.py`, `test_check_lib_coverage.py` | every cell in `design/cells.json` present with rise+fall 7 x 7 tables; exits 1 on a partial corner. Takes **several `.lib` files** when a corner is recorded as more than one file, and checks them as one record; a cell in two files, or files from two corners, is an error, so coverage cannot be manufactured by pairing corners |
| `records/s5l_ff_1p32v_m40c.lib` (+ `.provenance.json`) | FF / 1.32 V / -40 C, **39 of 40 cells, SIMULATED** (issue #85): the 40th, `s5l_mux4_1`, is the separate file below. FF `s5l_nand2_1` delays average 0.71x the TT probe's over the 196 points, so the corner took effect |
| `records/s5l_mux4_1.ff_1p32v_m40c.lib` (+ `.provenance.json`) | FF / 1.32 V / -40 C, `s5l_mux4_1` only, **SIMULATED** (issue #85). Additive: it does not rewrite the file above. Unsplit, this cell's grid is one `tran` run that outruns the fleet's 3600 s whole-job ceiling, so it ran with `--split-grid 7` (klayout-tools#5410), one fleet job per input-slew row, 7/7 `pass`. 588 points, 0 negative delays; FF/TT ratio mean 0.686. **Caveat:** these legs ran on fleet ngspice-47, the other 39 cells on ngspice-46, so the combined FF record is not single-engine |
| `records/s5l_tt_1p20v_25c.lib` (+ `.provenance.json`) | TT / 1.20 V / 25 C, the ratified target corner, **all 40 cells, SIMULATED** (issue #84): coverage check `COVERAGE COMPLETE` (40/40, rise+fall 7 x 7); fleet job ids per cell in the provenance. `s5l_nand2_1` agrees with the local probe below at all 196 points (max |delta| 2.9e-5 ns) |
| `records/probe.s5l_nand2_1.tt_1p20v_25c.lib` | probe: `s5l_nand2_1` alone, TT / 1.20 V / 25 C, local run |

Run a corner (the requests set `output.lib` into `records/`):

```
source .cache/env.sh
python3 sim/characterize/gen_requests.py
klt characterize sim/characterize/requests/tt.request.json --backend batch \
    --wait-for-capacity 600 --resume --keep-going
```

Check a corner. A corner recorded as several files is checked as one record,
so pass every file of it:

```
python3 -I sim/characterize/check_lib_coverage.py \
    sim/characterize/records/s5l_ff_1p32v_m40c.lib \
    sim/characterize/records/s5l_mux4_1.ff_1p32v_m40c.lib
```

A cell whose whole grid outruns the fleet's 3600 s whole-job ceiling needs
`--split-grid N` (one fleet job per input-slew row, merged into one table):

```
klt characterize sim/characterize/requests/ff.request.json --cell s5l_mux4_1 \
    --backend batch --wait-for-capacity 600 --split-grid 7 --timeout-s 3000 \
    --resume --lib sim/characterize/records/s5l_mux4_1.ff_1p32v_m40c.lib
```

## Timing-margin metric

```
python3 -I sim/characterize/margin.py [--csv out.csv] [records/*.lib ...]
python3 -I sim/characterize/test_margin.py
```

`margin = LIMIT_NS - measured_delay` for every `cell_rise`/`cell_fall` table
point; negative is a recorded FAIL, never dropped; a missing arc table is
reported. `LIMIT_NS` = 2.5074 ns, the ratified grid's largest input slew (the
spec states no delay budget, so this is a grid-validity bound, not a
closure target; a real budget needs a decision record). Values are
SIMULATED. Probe result: 196 points, 0 fail, binding corner
`tt_1p20v_25c` (least margin 0.5632 ns, `Y<-B` rise at slew 2.5074 / load 0.3).

## `klt sta` `netlist_estimate` on a per-cell wrapper (checked)

Run once, locally (single unit), 2026-11-12, `klt 0.9.2.dev768`, OpenROAD
26Q3-1510: a combinational-only wrapper (`module wrap(A, B, Y)` holding one
`s5l_nand2_1`) with `geometry_source: netlist_estimate`. Result: **it can
be timed.** `status: ok`, `constraint_completeness: complete`, worst setup
path `output_setup B -> Y`, worst hold path `A -> Y`. A single-corner
request needs:

- `constraints.clock_port`/`clock_period_ns` (required by `klt sta`) with
  `input_delay_ns`/`output_delay_ns` set, so the combinational paths are
  constrained against that clock; the wrapper itself has no register.
- the cell as a `macros[]` entry: its LEF, and its Liberty per corner
  (the probe `.lib` here). The repo has no LEF for the cell yet, so the
  run used a hand-written stub LEF (pins only, not a real abstract);
  timing comes from the Liberty alone.

No klayout-tools gap found, so none filed. Caveat: OpenSTA could not read
the PDK's own Liberty from `~/share/pdk` on this host (`cannot read file`,
while a copy under `/tmp` loaded); it is a host access problem, not shown
to be a `klt` fault, so the run used a `/tmp` mirror of the PDK `lib/` and
`lef/`. The margin metric stays `margin.py` over the characterized `.lib`;
`klt sta` is a cross-check, not a replacement. Not done here: comparing
`klt sta`'s path delay with the table value at the same slew/load.

## Probe provenance

- request: `requests/tt.request.json` filtered to `s5l_nand2_1`, netlist
  `design/netlists/s5l_nand2_1.spice`, absolute paths, output to a scratch dir
- PDK: `sim/pdk.json` pin (`f7bca32694fe3d58be0cc7d9df4b9f5db7161a14`),
  `cornerMOSlv.lib` section `mos_tt`
- tools: `klt characterize` from klayout-tools 0.9.2.dev683 (host `klt`),
  ngspice-46 on the host; the repo pin is klt 0.9.1 / ngspice 47
- run: one local single-unit run, 49 points, 2 arcs; about 100 s wall, 13 min CPU

## What is not here yet

- **SS / 1.08 V / 125 C has not been run.** `requests/ss.request.json` is
  generated but never executed.
- `klt characterize --backend batch` submits **one fleet job per cell,
  serially** (concurrent per-cell runs: klayout-tools#5351, open), so one
  corner is roughly 4.7 h of wall time. `--wait-for-capacity`,
  `--resume`/re-attach (klayout-tools#5348) and `--split-grid`
  (klayout-tools#5410) have all landed, so an interrupted or
  capacity-refused run is recoverable rather than lost.
- The FF corner is not single-engine: the fleet moved from ngspice-46 to
  ngspice-47 between the 39-cell run and the `s5l_mux4_1` run. Re-running the
  39 cells on ngspice-47 would make it uniform; recorded results are
  append-only, so that would be a new file, not an edit.
- Not done: the functional check against `rtl/`, the
  CI validator and the manifest entry for item 5.
