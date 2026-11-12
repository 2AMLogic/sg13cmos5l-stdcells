# sim/characterize

Issue #27 (T1 item 5): NLDM characterization of the 40 combinational cells.
Everything here is **simulated**, never measured. **Status: partial.** The
requests are generated and one cell has been run at TT; the 40-cell,
three-corner run has not been completed (see below).

| path | what |
|---|---|
| `gen_requests.py` | writes `requests/{tt,ff,ss}.request.json` from `design/cells.json`; `--check` exits 1 if they are stale |
| `requests/` | one `klt characterize` request per Liberty corner in `spec/target-spec.md` (TT target; FF, SS stretch), 40 cells, the spec's 7 x 7 grid |
| `margin.py`, `test_margin.py` | the timing-margin metric (defined in `margin.py`'s docstring, the one place): `margin = LIMIT_NS - delay` per (cell, arc, slew, load, corner); table + per-arc pass/fail + binding corner from any `records/*.lib` |
| `records/probe.s5l_nand2_1.tt_1p20v_25c.lib` | probe: `s5l_nand2_1` alone, TT / 1.20 V / 25 C, local run |

Run a corner (the requests set `output.lib` into `records/`):

```
source .cache/env.sh
python3 sim/characterize/gen_requests.py
klt characterize sim/characterize/requests/tt.request.json --backend batch
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

## Why the full run is not here

- `klt characterize --backend batch` submits **one fleet job per cell,
  serially**. Four cells (a21o_1 .. a21oi_2) took about 28 min, i.e. roughly
  7 min per cell, so one corner is about 4.7 h and three corners about 14 h.
  Run locally a cell costs 13 CPU-minutes, which this host may not spend.
- `klt characterize` has no `--wait-for-capacity` and does not forward a
  `batch` block to the sim request, so a `batch_no_capacity` burst cannot be
  waited out. It also has no `--attach`: when the client is stopped the
  remote job (`klt-sim-96215636a0f7`) keeps running and its result is
  unreachable.
- Not done: the functional check against `rtl/`, the
  CI validator and the manifest entry for item 5.
