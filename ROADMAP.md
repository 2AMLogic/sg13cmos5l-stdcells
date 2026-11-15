# Roadmap

sg13cmos5l-stdcells is a port of the 8-track `sg13g2-stdcells` library to IHP
SG13CMOS5L: 40 generated combinational cells, their views, and the evidence
that they meet the ratified spec.

Status as of 2026-11-15, `main` @ `8eb4dfc`; the Now list was re-read against
the tracker at the same commit.

Tracker for the gap to tier 1 (T1): #6. Verdict of record:
[`manifests/sg13cmos5l-stdcells.signoff.json`](manifests/sg13cmos5l-stdcells.signoff.json).
[`WORK_PLAN.md`](WORK_PLAN.md) is the generated label view; this file is the
sequence and its reasons. Every number below is simulated; nothing is measured.

## Where it stands

On the README's maturity ladder the position still reads **spec ratified**,
even though the retarget has begun: the first generated cell is on `main`.

The signoff record grades **3 of 11 T1 items met** (klt 0.9.1):

| # | Item | Verdict of record | Evidence on `main` | Open issue |
|---|---|---|---|---|
| 1 | Design sources | met | `design/cells.json`, `design/gen_netlists.py`, 40 netlists, 40 `rtl/` models, `verification/item1-attest.json` | — |
| 2 | Layout | unmet (`no_evidence`) | first generated cell `layout/gds/s5l_inv_1.gds` on `main`; no item-2 evidence in the manifest yet | #24 |
| 3 | DRC clean | unmet (`no_evidence`) | smoke: `klt drc` clean on the reference inverter | #25 |
| 4 | LVS clean | unmet (`no_evidence`) | smoke: `klt lvs` mismatch on the reference inverter | #26 |
| 5 | Corner verification | unmet (`check_failed`) | Liberty at TT, FF and SS for all 40 cells (`sim/characterize/records/`), 356-vector functional record, three-corner limit-checked sweeps — one propagating state per arc (`verification/functional/records/corners.report.json`) and every propagating state (`verification/functional/records/corner_states.report.json`) — both recorded **fail**: 2 of 3 corners pass | #27, #87, #129 |
| 6 | Monte Carlo | unmet (`no_evidence`) | `verification/item6-not-applicable.{md,json}`, drift-checked in CI, not yet cited | #28 |
| 7 | Post-layout verification | unmet (`no_evidence`) | none | #29 |
| 8 | Characterization report | unmet (`no_evidence`) | none | #30 |
| 9 | Testbenches shipped | met | `sim/attest/item9.envelope.json` | — |
| 10 | Repo hygiene | met | `manifests/evidence/item-10-repo-hygiene.json` | — |
| 11 | Power delivery | unmet (`no_evidence`) | none | #32 |

Two facts shape everything below.

- **Item 5 has its evidence but cannot grade met as recorded.** Decision record
  [0005](spec/decision-records/0005-timing-margin-spec-row.md) ratified the
  grid-validity bound (stage delay ≤ 2.5074 ns) as the timing-margin row. TT and
  FF pass; at SS / 1.08 V / 125 °C five stacked-NMOS rise arcs exceed it at the
  grid's largest slew and load, by at most 0.0548 ns (`s5l_nand4_1` `Y<-D`).
  Since #124 (PR #146) the sweep covers every propagating side-input state, not
  one per arc: 208 (arc, state) pairs, 416 delays per corner, in
  `verification/functional/records/corner_states.report.json` — the same five
  arcs fail, and the library's tightest *passing* SS margin drops from +6.55 ps
  to +0.86 ps (`s5l_mux4_1` `X<-A3` rise; DR 0005's 2026-11-14 addendum). The
  manifest cites `corners.report.json` and the verdict of record reads
  `unmet` (`check_failed`); how item 5 reaches met is held for a decision
  (#129), and the citation issue #87 is itself held under `loom:operator` as
  of 2026-11-15.
- **The layout chain's first slice is done; the rest hangs off a held #24.**
  The origin ships a layout generator (`layout/gen_layouts.py`,
  config-driven, with `--check`; sg13g2-stdcells#22, closed) and the netlist
  generator that decision record
  [0003](spec/decision-records/0003-netlist-generator-local.md) was waiting
  for (sg13g2-stdcells#5, closed). `reuse.lock.json` pins both at `26935d3`
  with a sha256 per file, the SG13CMOS5L layout config is committed, and the
  first generated cell, `layout/gds/s5l_inv_1.gds`, is on `main`. Items 2, 3,
  4, 7 and 11 all hang off #24, held as of 2026-11-14 (see below).

## Now

Can start today; each is one pull request. Live issue numbers are tracked in
[`WORK_PLAN.md`](WORK_PLAN.md), not here: a Now row is built and closed within
the hour, so a row that names its issue is stale by the time it merges.

1. **Bring the README status in line with the record**. Done when the
   Status paragraph and the Repo layout block match the table above: the
   retarget has begun (first generated cell committed), item 5 is recorded
   `unmet` (`check_failed`) pending the #129 decision, item 6 waits on the
   #28 decision, and `design/` holds a catalog and a generator rather than
   xschem schematics.
2. **Reduce the local netlist generator to configuration** (decision
   record [0003](spec/decision-records/0003-netlist-generator-local.md)).
   Done when the pinned upstream generator reproduces the 40 committed
   netlists under `--check`, `design/gen_netlists.py` holds only the
   SG13CMOS5L sizing, and item 1 is re-attested.
3. **Gate and hygiene follow-ups**, one pull request each: done
   when `scripts/test_check_reuse_lock.sh` passes from any working directory
   and the item-1 inventory docstring no longer states the premise PR #147
   corrected.

## Next

Unblocked by a named item above.

- **Generate all 40 cells** (#24 — held, see below). Done when 40 GDS
  reproduce from the pinned generator with `--check` clean, the manifest
  gains item-2 evidence and the signoff record reads item 2 met. The pinned
  generator places 3 of 40 cells today (measured 2026-11-14 for #24's
  decision); the 37 that fail exit 3 wait on upstream capability gaps, to be
  filed against `sg13g2-stdcells` — never hand-drawn here.
- **DRC and LVS on every generated cell** (#25, #26, after #24): `klt drc`
  clean with coverage quoted; `klt lvs` match against the item-1 netlists. The
  smoke already records an LVS mismatch on the PDK's own inverter, so expect
  tool or deck findings first.
- **Power delivery** (#32, after #24 and #26): `klt erc` supply spec, LVS
  carrying the supplies.
- **Post-layout re-characterization** (#29, after #24, #26 and #27), then the
  **characterization report and synthesis benchmark** (#30, after #27, #29).

## Later

Direction, each with the question that comes first.

- **Synthesis benchmark against `sg13cmos5l_stdcell`.** Which designs? The spec
  leaves them to the benchmark issue and requires purely combinational designs
  while sequential cells are deferred.
- **8-track row on this metal stack.** Does a 3.36 µm row with Metal1-only
  routing give every pin a routing-grid point, or does the 3.78 µm fallback
  apply? Answered by the generated cells and the benchmark's routability.
- **Sequential cells** (stretch: 8) and the 120-cell stretch set. When does
  the origin's setup/hold characterization exist, and has the 40-cell set
  graded T1?

## Blocked and waiting

Held for a maintainer decision (`loom:operator`); agents do not edit the
ratified spec to make a result pass.

- **#24: item 2 (layout).** Held as of 2026-11-14 for a maintainer decision:
  the pinned and current upstream generators both place only 3 of 40 cells
  (37 fail exit 3 across diffusion breaks, finger folding and channel
  routing), so item 2 `met` is unreachable without upstream work.
- **#129: how item 5 reaches met.** Four options from decision record 0005
  (accept unmet at the SS stretch corner, change the grid row, add drive
  strengths, ratify a delay budget). Items 7 and 8 inherit the outcome via #27.
- **#87: item-5 citation.** Held under `loom:operator` as of 2026-11-15; the
  citation slice itself is delivered — the manifest cites the three-corner
  report — and what remains of the issue waits on that decision.
- **#28: item 6 citation.** The pinned grader needs a `Status:` line in
  `spec/target-spec.md`; adding it changes the ratified spec's hash and needs a
  decision record.
- **#105, #117, #134:** removal proposals (vendored `sim/harness`, vendored
  tiers document, cocotb harness).

Waiting on an upstream release: **#109**, the characterization klt pin. The
Liberty records were made with an unreleased host klt because `--split-grid`,
`--resume` and `--wait-for-capacity` are not in the pinned 0.9.1.

## Not planned

- Cell generators designed here (they come from `sg13g2-stdcells` by pinned
  reference), and hand-drawn cells.
- Comparisons against SG13G2, the origin's numbers or any published library;
  the only baseline is `sg13cmos5l_stdcell` through the same open flow.
- Any tier above T1 before T1 is graded.
