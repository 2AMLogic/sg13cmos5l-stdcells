# verification/functional — netlist vs RTL truth tables (issue #82, part of #27)

T1 item 5 functional evidence. Everything here is **simulated**, never measured.

- `gen_functional.py` — generates `tb_all.cir`, `tt.request.json` (one TT
  single-corner `klt sim` request, runs local; all 40 cells, every input vector,
  from `design/cells.json`) and `tb_rtl.v` (exhaustive RTL truth tables). `--check`
  fails if stale.
- `compare.py` — RTL tables (iverilog) vs the sim report, bit-exact on
  thresholded levels (<0.1·VDD → 0, >0.9·VDD → 1, otherwise fail).
  `--negative-control` flips one RTL bit and must fail.
- `test_functional.sh` — freshness, all-40-cells coverage, real pass, negative control.
- `records/tt.report.json` — `klt sim` report (klt 0.9.1, ngspice 47, TT 1.20 V 25 C).
- `records/functional.tt.json` — per-cell, per-vector pass/fail (356 checks, 40/40 pass).

Reproduce: `source .cache/env.sh; klt sim verification/functional/tt.request.json --backend local -o <out> --report-out verification/functional/records/tt.report.json; verification/functional/test_functional.sh`.

Note: the RTL side runs iverilog directly rather than `klt functional-verification`
because cocotb is not installed on the build host (host tools are not modified);
the exhaustive-vector comparison is equivalent for combinational cells.
