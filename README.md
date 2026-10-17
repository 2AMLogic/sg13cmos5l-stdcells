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

**Status: just opened, specification phase.** Nothing is designed yet,
nothing has been taped out, and nothing has been measured.

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

## Target specification (DRAFT — engineering to ratify, see issue #2)

Port parity: the rows below mirror the sg13g2-stdcells draft. Ratification
must confirm each against SG13CMOS5L's own rules and metal stack; where the
PDK makes a row wrong rather than merely harder, it changes through a decision
record that says why.

| Parameter | Target | Fallback | Stretch |
|---|---|---|---|
| Row height | 3.36 µm (8 tracks), as origin — confirm against SG13CMOS5L rules | as `sg13cmos5l_stdcell` | — |
| Routing grid | 0.42 µm × 0.42 µm, as origin — confirm | — | — |
| Intra-cell routing | Metal1 only | — | — |
| Pin access | every pin on a routing-grid point | — | — |
| Combinational cells | 40 | 20 | 120 |
| Sequential cells | 0 (deferred, as origin) | — | 8 |
| DRC | clean, `klt drc`, SG13CMOS5L deck | — | — |
| LVS | layout-vs-schematic match, `klt lvs` | — | — |
| Liberty corners | TT / nominal supply / 25 °C | — | + FF/−40 °C, SS/125 °C |
| Benchmark cell area vs `sg13cmos5l_stdcell` | ≤ 1.00× | ≤ 1.20× | ≤ 0.80× |
| Benchmark clock period vs `sg13cmos5l_stdcell` | within 10% | within 20% | within 5% |

All benchmark rows compare like with like: same PDK, same open flow, same
benchmark designs. No cross-library or cross-PDK comparison is a result of
this repo.

Maturity ladder: spec ratified → generator retargeted → cells DRC/LVS-clean →
views characterized → synthesis benchmark recorded → shuttle seat → measured
silicon. **Current position: pre-spec.**

## Repo layout

```
spec/          ratified spec + decision records
design/        per-cell schematics (xschem)
rtl/           functional Verilog models of each cell
sim/           per-cell SPICE characterization + PVT corner results (ngspice)
verification/  cocotb checks of the functional models and the benchmark
layout/        generated GDS + DRC/LVS reports (klayout-tools driven)
measurements/  silicon characterization (empty until tape-out)
```

## Reproduce

Every recorded result appends the exact commands that regenerate it here.

Repo checks (JSON/evidence formats, README links, graded signoff record):

```
npm run check:ci
```

## License

Apache License 2.0 — see [LICENSE](LICENSE).
