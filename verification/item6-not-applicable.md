# T1 item 6 (Monte Carlo / yield) — `not_applicable` statement

Digital partition. `klt yield` evidence is required only where the ratified spec
carries a statistical row: a sigma, yield, offset or matching bound. This
statement accounts for every row of the Parameters table in
`spec/target-spec.md` and shows none is statistical, so item 6 is
`not_applicable` for this block.

Written against `spec/target-spec.md` with
`SHA-256: cf2688fb8414feb158a8f0b11c67a2d79026a9b3343c64b5d5cf98f8c5d817b0`.

`scripts/check_item6_statement.py` fails when that hash no longer matches the
spec, or when the first column of the table below differs from the spec's
Parameter column (a row added, removed or renamed). A failure means the spec
changed: re-read the changed rows, then update this statement and the hash.

## Classes

- **geometry** — a drawn dimension; fixed by construction, checked by DRC/LVS.
- **count** — a number of cells in the library.
- **corner-bounded** — a deterministic characterization at named PVT corners;
  one simulation per corner and grid point, no random parameter.
- **tool-pass** — a pass/fail verdict of a deterministic tool run.
- **benchmark ratio** — a ratio from one deterministic run of the open flow.

## Row accounting

| Parameter | Class | Why it is not statistical |
|---|---|---|
| Row height | geometry | A drawn dimension (8 tracks of 0.42 µm); no device variation enters it. |
| Routing grid | geometry | A pitch the layout snaps to; no variation. |
| Intra-cell routing | geometry | A layer-usage rule (Metal1 only), checked by DRC. |
| Pin access | geometry | Pins sit on grid points; a layout property, checked on the drawn cell. |
| Combinational cells | count | A cell-count target; no distribution. |
| Sequential cells | count | A cell-count target (0, deferred); no distribution. |
| DRC | tool-pass | A deterministic rule check on drawn geometry. |
| LVS | tool-pass | A deterministic netlist comparison. |
| Core supply | corner-bounded | A nominal voltage (1.20 V); the ±10 % excursions are named corners, not a distribution. |
| Liberty corners | corner-bounded | Named PVT points (TT; stretch FF, SS), each simulated once; no sigma or yield bound. |
| Characterization grid | corner-bounded | A fixed 7 × 7 slew/load index set; a deterministic sweep with no spread claim. |
| Benchmark cell area vs `sg13cmos5l_stdcell` | benchmark ratio | One deterministic flow run per library; a ratio with no tolerance band. |
| Benchmark energy vs `sg13cmos5l_stdcell` | benchmark ratio | One deterministic power report per library; no spread claim. |
| Benchmark clock period vs `sg13cmos5l_stdcell` | benchmark ratio | One deterministic timing result per library; the "within 10 %" is a comparison threshold, not a variation bound. |

## The soft spot

The benchmark ratios and the 7 × 7 grid are single deterministic runs. The
statement holds because the spec makes **no spread claim** for them: no sigma,
yield or matching bound, and no Monte Carlo requirement. If any later spec row
adds a tolerance or variation claim (a sigma bound, a yield target, an offset or
matching limit, or a spread on a benchmark ratio or table value), this statement
no longer applies and that row needs `klt yield` evidence.

## Re-verification log

- Hash re-recorded after the spec gained a prose pointer to decision record 0002
  under the Combinational cells rationale (PR #39). The Parameters table rows
  are unchanged, so the accounting above is unchanged.

## Pending

The block manifest does not yet cite this file as item 6's `not_applicable`
evidence, and `klt signoff` does not yet report item 6 from it. The pinned
`klt` 0.7.0 has no `not_applicable` grading, and 0.8.0's form takes a JSON
ratified spec and a JSON statement, not this markdown pair. The citation waits
on that tool gap (issue #28 stays open).
