# sim/characterize

Issue #27 (T1 item 5): NLDM characterization of the 40 combinational cells.
Everything here is **simulated**, never measured. **Status: TT, FF and SS
complete (40/40 cells each).**

| path | what |
|---|---|
| `gen_requests.py` | writes `requests/{tt,ff,ss}.request.json` from `design/cells.json`; `--check` exits 1 if they are stale |
| `requests/` | one `klt characterize` request per Liberty corner in `spec/target-spec.md` (TT target; FF, SS stretch), 40 cells, the spec's 7 x 7 grid |
| `margin.py`, `test_margin.py` | the timing-margin metric (defined in `margin.py`'s docstring, the one place): `margin = LIMIT_NS - delay` per (cell, arc, slew, load, corner); table + per-arc pass/fail + binding corner from any `records/*.lib` |
| `check_lib_coverage.py`, `test_check_lib_coverage.py` | every cell in `design/cells.json` present with rise+fall 7 x 7 tables; exits 1 on a partial corner. Takes **several `.lib` files** when a corner is recorded as more than one file, and checks them as one record; a cell in two files, or files from two corners, is an error, so coverage cannot be manufactured by pairing corners |
| `records/s5l_ff_1p32v_m40c.lib` (+ `.provenance.json`) | FF / 1.32 V / -40 C, **39 of 40 cells, SIMULATED** (issue #85): the 40th, `s5l_mux4_1`, is the separate file below. FF `s5l_nand2_1` delays average 0.71x the TT probe's over the 196 points, so the corner took effect |
| `records/s5l_mux4_1.ff_1p32v_m40c.lib` (+ `.provenance.json`) | FF / 1.32 V / -40 C, `s5l_mux4_1` only, **SIMULATED** (issue #85). Additive: it does not rewrite the file above. Unsplit, this cell's grid is one `tran` run that outruns the fleet's 3600 s whole-job ceiling, so it ran with `--split-grid 7` (klayout-tools#5410), one fleet job per input-slew row, 7/7 `pass`. 588 points, 0 negative delays; FF/TT ratio mean 0.686. **Caveat:** these legs ran on fleet ngspice-47, the other 39 cells on ngspice-46, so the combined FF record is not single-engine |
| `records/s5l_tt_1p20v_25c.lib` (+ `.provenance.json`) | TT / 1.20 V / 25 C, the ratified target corner, **all 40 cells, SIMULATED** (issue #84): coverage check `COVERAGE COMPLETE` (40/40, rise+fall 7 x 7); fleet job ids per cell in the provenance. `s5l_nand2_1` agrees with the local probe below at all 196 points (max |delta| 2.9e-5 ns) |
| `records/s5l_ss_1p08v_125c.lib` (+ `.provenance.json`) | SS / 1.08 V / 125 C, **39 of 40 cells, SIMULATED** (issue #86): the 40th, `s5l_mux4_1`, is the separate file below. Single-engine (fleet ngspice-47 for every cell), unlike the FF record. SS/TT delay ratio mean 1.482 over the 10350 common points whose TT delay is at least 25 ps, so the corner took effect. **This corner is the one where the margin metric records FAILs:** 5 of 10388 points, all at the grid's largest slew *and* largest load on a stacked-NMOS rise arc, least margin -0.0548 ns (`s5l_nand4_1` `Y<-D`) |
| `records/s5l_mux4_1.ss_1p08v_125c.lib` (+ `.provenance.json`) | SS / 1.08 V / 125 C, `s5l_mux4_1` only, **SIMULATED** (issue #86). Additive: it does not rewrite the file above. Same reason as the FF split -- unsplit, this cell's grid is one `tran` run that outruns the fleet's 3600 s whole-job ceiling (it is also the cell that aborted the first SS attempt on the then-default 900 s ngspice timeout) -- so it ran with `--split-grid 7`, one fleet job per input-slew row, 7/7 `pass`. 588 points, 0 negative delays, 0 margin FAILs |
| `records/probe.s5l_nand2_1.tt_1p20v_25c.lib` | probe: `s5l_nand2_1` alone, TT / 1.20 V / 25 C, local run |

Run a corner (the requests set `output.lib` into `records/`):

```
source .cache/env.sh
python3 sim/characterize/gen_requests.py
klt characterize sim/characterize/requests/tt.request.json --backend batch \
    --wait-for-capacity 600 --timeout-s 3000 --resume --keep-going
```

`--wait-for-capacity` is not only a capacity knob: it is what lets
`klt characterize` run cells **concurrently** on the `batch` backend
(klayout-tools#5351, 4 at a time), because without a capacity wait a burst of
submits would just be refused. Without it the run is serial, roughly 4.7 h for
one corner. `--timeout-s` raises the per-sim ngspice timeout above the default
(klayout-tools#5380); at the 900 s default the `s5l_mux4_1` grid does not finish, which is what aborted the first SS attempt.

A client killed mid-run loses nothing: re-run the same command with the same
`-o` and `--resume` and it re-attaches to the fleet jobs already submitted.
One case does not recover on its own -- a job the fleet leaves Spot-`interrupted`
without re-launching, which `--resume` re-attaches to forever
(klayout-tools#5515); until that is fixed, delete that unit's
`<outdir>/cells/<cell>/sim/batch-receipt.json` so the next `--resume`
resubmits it.

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

Over all three recorded corners the binding corner is now `ss_1p08v_125c`,
and it is the only corner with failing points: **5 of its 10388 points are
recorded FAILs**, least margin -0.0548 ns (`s5l_nand4_1` `Y<-D` rise),
then `s5l_nand4_1` `Y<-C`, `s5l_nand3_1` `Y<-C`, `s5l_nand3b_1` `Y<-C`,
`s5l_nand4_1` `Y<-B`. Every one is at the grid's largest input slew
(2.5074 ns) *and* largest load (0.3 pF) on a stacked-NMOS rise arc, and
misses by 0.3-2.2 % of `LIMIT_NS`. `LIMIT_NS` is a grid-validity bound, not
a ratified delay budget, and SS is a stretch corner, so this is a recorded
property of the slow corner at the grid's extreme -- not a spec violation.
It is left as it is: the metric is not retuned to make it pass, and
`margin.py` therefore exits 1 over `records/*.lib`. Narrowing it needs
either a ratified delay budget or a grid change, both decision records.

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

- All three corners of `spec/target-spec.md` are now recorded. What is not
  recorded is any **post-layout** corner (#29) and any corner outside that
  ratified set.
- `klt characterize --backend batch` runs **4 cells at a time** when a
  capacity wait is set (klayout-tools#5351, closed), which is what brings a
  corner down from roughly 4.7 h to roughly 1.5 h. `--wait-for-capacity`,
  `--resume`/re-attach (klayout-tools#5348), `--timeout-s`
  (klayout-tools#5380) and `--split-grid` (klayout-tools#5410) have all
  landed, so an interrupted or capacity-refused run is recoverable rather
  than lost -- except a Spot-`interrupted` job, which `--resume` re-attaches
  to indefinitely (klayout-tools#5515, open; see the recipe above).
- The FF corner is not single-engine: the fleet moved from ngspice-46 to
  ngspice-47 between the 39-cell run and the `s5l_mux4_1` run. Re-running the
  39 cells on ngspice-47 would make it uniform; recorded results are
  append-only, so that would be a new file, not an edit.
- Not done: the functional check against `rtl/`, the
  CI validator and the manifest entry for item 5.
