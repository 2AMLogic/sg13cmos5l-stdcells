# Roadmap

sg13cmos5l-stdcells is a port of the 8-track `sg13g2-stdcells` library to IHP
SG13CMOS5L: 40 generated combinational cells, their views, and the evidence
that they meet the ratified spec.

Status as of 2026-11-13, `main` @ `e167b52`.

Tracker for the gap to tier 1 (T1): #6. Verdict of record:
[`manifests/sg13cmos5l-stdcells.signoff.json`](manifests/sg13cmos5l-stdcells.signoff.json).
[`WORK_PLAN.md`](WORK_PLAN.md) is the generated label view; this file is the
sequence and its reasons. Every number below is simulated; nothing is measured.

## Where it stands

On the README's maturity ladder the position is still **spec ratified**: the
generator has not been retargeted, so no cell layout exists.

The signoff record grades **3 of 11 T1 items met** (klt 0.9.1):

| # | Item | Verdict of record | Evidence on `main` | Open issue |
|---|---|---|---|---|
| 1 | Design sources | met | `design/cells.json`, `design/gen_netlists.py`, 40 netlists, 40 `rtl/` models, `verification/item1-attest.json` | — |
| 2 | Layout | unmet (`no_evidence`) | only the PDK reference inverter in `layout/smoke/` | #24 |
| 3 | DRC clean | unmet (`no_evidence`) | smoke: `klt drc` clean on the reference inverter | #25 |
| 4 | LVS clean | unmet (`no_evidence`) | smoke: `klt lvs` mismatch on the reference inverter | #26 |
| 5 | Corner verification | unmet (`no_limits_checked`) | Liberty at TT, FF and SS for all 40 cells (`sim/characterize/records/`), 356-vector functional record, three-corner limit-checked sweep `verification/functional/records/corners.report.json` (recorded **fail**: 2 of 3 corners pass) | #27, #87, #129, #124 |
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
  The committed manifest still cites the TT-only report; re-pointing it is #87.
- **The layout chain is no longer waiting on the origin.** #24 was parked
  because `sg13g2-stdcells` had no layout generator. It now ships one
  (`layout/gen_layouts.py`, config-driven, with `--check`;
  sg13g2-stdcells#22, closed) and the netlist generator that decision record
  [0003](spec/decision-records/0003-netlist-generator-local.md) was waiting
  for (sg13g2-stdcells#5, closed). `reuse.lock.json` here still pins the origin
  at `f450813`, which predates both. Items 2, 3, 4, 7 and 11 all hang off #24.

## Now

Can start today; each is one pull request.

1. **Pin the origin's generators and record a one-cell retarget probe** (first
   slice of #24; no issue of its own yet). Done when `reuse.lock.json` carries
   the origin's `design/gen_netlists.py` and `layout/gen_layouts.py` at one
   full commit with a sha256 per file, an SG13CMOS5L layout config is
   committed, and `layout/` holds either the generated `s5l_inv_1` GDS with a
   clean `--check`, or a record of the generator's named failure and the
   upstream issue filed for it. Blocked by: nothing in the tree; #24 itself
   still carries `loom:blocked` and `loom:operator`.
2. **Measure every propagating side-input state in the corner arc sweep**
   (#124, ready). Done when `corners.report.json` covers all propagating
   states for the 30 multi-state arcs with the worst one carrying the limit,
   or `verification/functional/README.md` states the single-state scope with
   a measurement showing the other states are not slower.
3. **Cite the three-corner report for item 5 and regenerate the verdict**
   (#87, PR #136 open with changes requested and a merge conflict). Done when
   the manifest cites `corners.report.json` and the signoff record reads
   item 5 as graded on it (expected `unmet` / `check_failed`, per
   `verification/functional/README.md`).
4. **Bring the README status in line with the record** (no issue yet). Done
   when the Status paragraph and the Repo layout block match the table above:
   the per-corner characterization exists, item 5 waits on #87 and #129,
   item 6 waits on the #28 decision, and `design/` holds a catalog and a
   generator rather than xschem schematics.
5. **Gate hygiene in flight:** #138 (PR #139, approved), #116 (PR #130,
   changes requested), #142 (triage), #141 (being evaluated).

## Next

Unblocked by a named item above.

- **Generate all 40 cells** (#24, after Now 1). Done when 40 GDS reproduce from
  the pinned generator with `--check` clean, the manifest gains item-2
  evidence and the signoff record reads item 2 met. A cell the generator cannot
  place is filed against `sg13g2-stdcells`, never hand-drawn here.
- **Reduce the local netlist generator to configuration** (decision record
  0003, after Now 1). Done when the pinned upstream generator reproduces the 40
  committed netlists under `--check`, `design/gen_netlists.py` holds only the
  SG13CMOS5L sizing, and item 1 is re-attested.
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

- **#129: how item 5 reaches met.** Four options from decision record 0005
  (accept unmet at the SS stretch corner, change the grid row, add drive
  strengths, ratify a delay budget). Items 7 and 8 inherit the outcome via #27.
- **#28: item 6 citation.** The pinned grader needs a `Status:` line in
  `spec/target-spec.md`; adding it changes the ratified spec's hash and needs a
  decision record.
- **#24: re-curation.** Its park reason (no upstream generator) is resolved;
  the labels have not been lifted.
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
