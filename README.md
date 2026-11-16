# sg13cmos5l-stdcells

An 8-track standard-cell library on
[IHP SG13CMOS5L](https://github.com/IHP-GmbH/IHP-Open-PDK/tree/dev/ihp-sg13cmos5l),
the CMOS-only member of IHP's open 130 nm family, with a reduced metal stack —
designed by AI agents driving
[klayout-tools](https://github.com/2AMLogic/klayout-tools) and the open-source
flow: xschem + ngspice for per-cell device-level characterization, cocotb +
Icarus and Yosys/OpenROAD for the functional models and the synthesis
benchmark.

It is the set of small logic gates — inverters, NANDs, NORs, AOIs, adders —
that a synthesis tool builds a digital chip from, produced by cell generators
at a fixed row height and characterized into the abstract views (LEF,
Liberty) that every downstream tool reads.

**Status: specification ratified, tier 1 in progress.** The spec is ratified
(decision record 0001) and the block kind is declared digital (decision record
0004). The committed signoff record
([`manifests/sg13cmos5l-stdcells.signoff.json`](manifests/sg13cmos5l-stdcells.signoff.json))
grades 3 of 11 tier-1 items met: design sources (1), testbenches shipped (9)
and repo hygiene (10). For the unmet items, what is committed and which open
issue each waits on:

- **Layout, DRC and LVS (item 2, issue #24):** the origin's cell generators
  are pinned in [`reuse.lock.json`](reuse.lock.json) and the SG13CMOS5L
  generator configuration plus a one-cell retarget probe are committed under
  [`layout/`](layout/README.md); the generator currently places 3 of the 40
  cells (census on issue #24), and item 2 waits on an operator ruling on how
  it proceeds.
- **Corner verification (item 5, issue #27):** Liberty for all 40 cells at
  TT, FF and SS is committed under
  [`sim/characterize/records/`](sim/characterize/records), and the
  three-corner limit-checked functional sweep is recorded in
  [`verification/functional/records/corners.report.json`](verification/functional/records/corners.report.json) —
  status `fail`, 2 of 3 corners pass. Item 5 waits on #87 (cite the report as
  item-5 evidence and regenerate the verdict of record) and #129 (the ruling
  on the five SS rise arcs over the bound ratified by
  [decision record 0005](spec/decision-records/0005-timing-margin-spec-row.md)).
- **Monte Carlo (item 6, issue #28):** the not_applicable statement covering
  every ratified row is committed
  ([`verification/item6-not-applicable.md`](verification/item6-not-applicable.md)),
  and item 6 waits on a ruling about a `Status:` line in the ratified
  [`spec/target-spec.md`](spec/target-spec.md).

Nothing has been taped out
and nothing has been measured; every number from the smoke benches is
simulated, not measured.

**Built agent-native.** Every specification, decision record, testbench, and
line of documentation here is produced by AI agents working from a ratified
spec and an append-only evidence trail — not human-authored work that agents
merely assisted with. Verification is the product: every claim traces to a
recorded result under PVT corners. Where the agents hit friction with the
open-source tooling — most often
[klayout-tools](https://github.com/2AMLogic/klayout-tools) — that friction is
filed as a public issue against the tool itself, so the fix benefits everyone
using SG13CMOS5L, not just this repo.

## Why this block, on this PDK

This is a **port, not a new design**. Its origin is
[sg13g2-stdcells](https://github.com/2AMLogic/sg13g2-stdcells), the program's
8-track library on IHP SG13G2, and this repo inherits that repo's spec
structure and its geometry decisions rather than re-deciding them. The
experimental design is the one every port in this program uses: **the PDK is
the variable, not the design.**

What makes it a worthwhile variable is the back end. SG13CMOS5L is a
CMOS-only process — no SiGe bipolar devices — with a shorter metal stack than
SG13G2. How much of the front end and the Metal1 rules the two share is the
first thing ratification establishes, from the PDK's own documentation rather
than from assumption. A standard-cell library is where the metal stack shows up
first: pin access, the routing grid, the power-rail strategy, and the routing
resources the synthesis benchmark has to place and route on. A cell generator
that was written well should retarget with rule and stack changes, not with
redrawn cells — and where it cannot, that is a finding about the generator,
recorded once and fixed upstream in sg13g2-stdcells.

The PDK ships its own reference library (`sg13cmos5l_stdcell`), which is the
benchmark baseline here exactly as `sg13g2_stdcell` is for the origin repo.

## Scope

- **In scope**: the combinational cell set, its generator configuration for
  SG13CMOS5L, DRC/LVS-clean layouts, LEF and Liberty views, and a synthesis
  benchmark against `sg13cmos5l_stdcell`.
- **Not in scope**: the cell generators themselves. They are designed once,
  in sg13g2-stdcells, and taken from there by a pinned reference. Fixes go
  upstream first.
- **Deferred with the origin repo**: sequential cells, which wait on the same
  setup/hold characterization machinery sg13g2-stdcells waits on.

## Target specification (ratified — see [spec/](spec/target-spec.md))

Ratified by [decision record 0001](spec/decision-records/0001-ratify-target-spec.md)
from the [PDK comparison](spec/pdk-comparison.md). The rows mirror the
sg13g2-stdcells draft; each is confirmed against SG13CMOS5L's own rules and
metal stack, and the spec records the risks that confirmation does not remove
(row-height feasibility, pin access onto the Metal2/4 tracks, `klt` deck
coverage). A row changes only through a new decision record.

| Parameter | Target | Fallback | Stretch |
|---|---|---|---|
| Row height | 3.36 µm (8 tracks of 0.42 µm) | 3.78 µm (9 tracks), the `sg13cmos5l_stdcell` site height | — |
| Routing grid | 0.42 µm × 0.42 µm | — | — |
| Intra-cell routing | Metal1 only | — | — |
| Pin access | every pin on a routing-grid point | — | — |
| Combinational cells | 40 | 20 | 120 |
| Sequential cells | 0 (deferred) | — | 8 |
| DRC | clean, `klt drc`, SG13CMOS5L deck | — | — |
| LVS | layout-vs-schematic match, `klt lvs` | — | — |
| Core supply | 1.20 V (`sg13_lv` devices) | — | — |
| Liberty corners | TT / 1.20 V / 25 °C | — | + FF / 1.32 V / −40 °C, SS / 1.08 V / 125 °C |
| Characterization grid | input slew 0.0186–2.5074 ns, output load 0.001–0.3 pF (7 × 7, the baseline's index set) | — | — |
| Benchmark cell area vs `sg13cmos5l_stdcell` | ≤ 1.00× | ≤ 1.20× | ≤ 0.80× |
| Benchmark energy vs `sg13cmos5l_stdcell` | ≤ 1.00× | — | ≤ 0.80× |
| Benchmark clock period vs `sg13cmos5l_stdcell` | within 10 % | within 20 % | within 5 % |

All benchmark rows compare like with like: same PDK, same open flow, same
benchmark designs. No cross-library or cross-PDK comparison is a result of
this repo.

Maturity ladder: spec ratified → generator retargeted → cells DRC/LVS-clean →
views characterized → synthesis benchmark recorded → shuttle seat → measured
silicon. **Current position: spec ratified.**

## Repo layout

```
spec/          ratified spec + decision records
design/        cell catalog (cells.json), the netlist generator, the 40 generated SPICE netlists
rtl/           functional Verilog models of each cell (model tests in rtl/tests/)
sim/           per-cell SPICE characterization + PVT corner results (ngspice)
verification/  committed verification records: netlist-vs-RTL functional and three-corner sweeps, tier evidence
layout/        SG13CMOS5L generator config + vendored origin generators, generated GDS, DRC/LVS smoke
manifests/     evidence-tier definitions + the graded signoff record
scripts/       bring-up (setup-env.sh) + the check:ci gate scripts
measurements/  silicon characterization (empty until tape-out)
```

## Bring-up

A fresh clone reaches a runnable state with one script and no manual PDK step:

```
scripts/setup-env.sh        # fetch + build into pdks/, .cache/, .venv/ (all gitignored)
source .cache/env.sh        # PDK_ROOT, PDK=ihp-sg13cmos5l, PATH
```

It fetches the SG13G2 sibling and the pinned SG13CMOS5L subtree of
IHP-Open-PDK (the CMOS5L models are symlinks into the sibling), builds ngspice
47 (the host ngspice-42 cannot load the OSDI models), compiles the Verilog-A
models to OSDI, and installs `klt` and `cocotb` at their pins in `.venv`. It
needs `curl`, `tar`, `make`, `gcc`, `bison`, `flex`, `python3` >= 3.10 and `uv`,
about 1 GB of disk and several minutes (`SETUP_JOBS`, default 2, sets the ngspice
`make -j`). It installs nothing host-wide and fails closed on any checksum
mismatch. Pins: [`sim/pdk.json`](sim/pdk.json), [`sim/toolchain.json`](sim/toolchain.json),
[`layout/toolchain.json`](layout/toolchain.json), [`rtl/toolchain.json`](rtl/toolchain.json).
`scripts/test_setup_env.sh` checks the fail-closed behaviour without the large
downloads; CI runs it (`npm run check:setup-env`), so the claim is gated rather
than advertised.

This is the only recipe that builds `.venv`, and it installs everything `npm run
check:ci` needs in it — the RTL gate's cocotb included. Icarus (`iverilog`) is
the one tool it does not provide: install it from the distro.

Smoke evidence: [`sim/smoke`](sim/smoke/README.md) (inverter simulation;
single-corner probe plus the five-corner transient and DC records, simulated)
and [`layout/smoke`](layout/smoke/README.md) (`klt drc` clean; `klt lvs`
mismatch in the committed klt-`0.7.1.dev`-build envelope and `match` in the
later klt-`0.9.2`-build envelope, both on the PDK's own reference inverter).

## Reproduce

Every recorded result appends the exact commands that regenerate it here.

Repo checks (JSON/evidence formats, README links, `setup-env.sh` fail-closed
behaviour, graded signoff record, and the PDK-free design/RTL gate: catalog,
generator freshness, unit tests and the netlist-vs-RTL functional compare):

```
npm run check:ci
```

`npm test` is an alias for `npm run check:ci` — one entry-point list, so the
next gate added to `check:ci` needs no second edit.

## License

Apache License 2.0 — see [LICENSE](LICENSE).
